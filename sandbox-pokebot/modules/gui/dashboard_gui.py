"""
Fork addition: the native dashboard GUI.

This is the fork's default emulator window (see pokebot.py; launch with
`--classic-gui` for upstream's original window). It mirrors the layout of
the web dashboard (modules/web/static/custom-ui/): the emulator video is
prominent and freely resizable on the left, and every tool lives in a
column on the right — bot mode, speed, video/audio, KPI tiles, party list
and an event log. A "handheld mode" (built for the ROG Ally X) makes the
video fill the whole window and collapses the tool column into an overlay
drawer toggled by a Pokéball button.

Hotkeys (on top of the stock key bindings from keys.yml):
  H   — enter handheld mode / toggle the tool drawer while in it
  F11 — toggle handheld mode
  Esc — close the drawer; if it is already closed, leave handheld mode
"""

import json
import time
import tkinter
import tkinter.font
from datetime import datetime
from tkinter import Canvas, Menu, ttk
from typing import TYPE_CHECKING, Callable

import PIL.Image
import PIL.ImageTk

from modules.context import context
from modules.gui import PokebotGui
from modules.memory import get_game_state
from modules.plugin_interface import BotPlugin
from modules.pokemon import StatusCondition
from modules.version import pokebot_name, pokebot_version

if TYPE_CHECKING:
    from modules.encounter import EncounterInfo
    from modules.pokemon import Pokemon

# Palette — mirrors the web dashboard (custom-ui/style.css), which follows
# the project's validated dataviz reference palette.
COLOR_PAGE = "#0d0d0d"
COLOR_SURFACE = "#1a1a19"
COLOR_CARD = "#232322"
COLOR_INK = "#ffffff"
COLOR_INK_2 = "#c3c2b7"
COLOR_MUTED = "#898781"
COLOR_HAIRLINE = "#2c2c2a"
COLOR_ACCENT = "#3987e5"
COLOR_GOOD = "#0ca30c"
COLOR_WARNING = "#fab219"
COLOR_CRITICAL = "#d03b3b"
COLOR_SHINY = "#c98500"

TOOL_COLUMN_WIDTH = 360
SIDEBAR_REFRESH_FRAMES = 30  # refresh party/labels every N rendered frames
KPI_REFRESH_SECONDS = 5.0  # stats DB reads are not free — refresh sparsely
UI_STATE_FILE = "dashboard_ui.json"

GBA_ASPECT = 240 / 160


class _DashboardEventsPlugin(BotPlugin):
    """Feeds bot events (encounters etc.) into the dashboard's event log."""

    def __init__(self, on_encounter: Callable[["EncounterInfo"], None]):
        self._on_encounter = on_encounter

    def on_logging_encounter(self, encounter: "EncounterInfo") -> None:
        self._on_encounter(encounter)


class DashboardScreen:
    """
    Replacement for modules.gui.emulator_screen.EmulatorScreen with the
    dashboard layout. Implements the same interface the rest of the bot
    expects from the emulator screen (enable/disable/update/
    on_settings_updated/scale/toggle_stepping_mode).
    """

    def __init__(self, window: tkinter.Tk):
        self.window = window
        self.frame: ttk.Frame | None = None
        self.canvas: Canvas | None = None

        self._video_size: tuple[int, int] = (480, 320)
        self._current_canvas_image: PIL.ImageTk.PhotoImage | None = None
        self._current_canvas_image_id: int | None = None
        self._frame_counter = 0
        self._last_kpi_refresh = 0.0
        self._plugin_registered = False

        self._handheld = False
        self._drawer_open = False

        # Widgets that get updated live
        self._mode_button: tkinter.Button | None = None
        self._speed_buttons: dict[int, tkinter.Button] = {}
        self._video_button: tkinter.Button | None = None
        self._audio_button: tkinter.Button | None = None
        self._kpi_values: dict[str, tkinter.Label] = {}
        self._party_rows: list[dict] = []
        self._event_list: tkinter.Listbox | None = None
        self._message_label: tkinter.Label | None = None
        self._state_label: tkinter.Label | None = None
        self._fps_label: tkinter.Label | None = None
        self._pokeball_button: Canvas | None = None

        # Debug support (stock debug tabs in a separate window)
        self._debug_window: tkinter.Toplevel | None = None
        self._debug_notebook: ttk.Notebook | None = None
        self._debug_tabs: list = []

    # ------------------------------------------------------------------
    # Interface expected by PokebotGui / the rest of the bot
    # ------------------------------------------------------------------

    @property
    def scale(self) -> int:
        # Kept for compatibility with the zoom_in/zoom_out key bindings and
        # the debug tabs' click handling: report the video's current
        # integer scale relative to the native 240x160.
        return max(1, round(self._video_size[0] / 240))

    @scale.setter
    def scale(self, _value: int) -> None:
        # The dashboard resizes with the window; zoom keys are meaningless.
        pass

    def toggle_stepping_mode(self) -> None:
        context.message = "Frame-stepping mode is only available in the classic GUI (--classic-gui)."

    def enable(self) -> None:
        self.window.title(f"{context.profile.path.name} | {pokebot_name} {pokebot_version} — Dashboard")
        self.window.configure(background=COLOR_PAGE)
        self.window.resizable(True, True)
        self.window.minsize(760, 480)
        # Clamp the initial size to the (logical) screen so the tool column
        # can never start off-screen on small or heavily DPI-scaled displays.
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = min(1280, screen_width - 40)
        height = min(720, screen_height - 100)
        x = max(0, (screen_width - width) // 2 - 20)
        y = max(0, (screen_height - height) // 2 - 40)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        # Some window managers ignore the position on the initial map —
        # re-assert it once the window exists so the tool column is never
        # pushed off-screen.
        self.window.after(250, lambda: self.window.geometry(f"+{x}+{y}"))

        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)
        self.window.columnconfigure(1, weight=0)

        self._build_menu_bar()
        self._build_video_area()
        self._build_tool_column()
        self._build_pokeball_button()

        if context.debug:
            self._build_debug_window()

        if not self._plugin_registered:
            from modules.plugins import plugins

            plugins.append(_DashboardEventsPlugin(self._on_encounter_logged))
            self._plugin_registered = True

        self._log_event("Dashboard GUI ready.")
        self._refresh_controls()
        self._restore_ui_state()

    def disable(self) -> None:
        if self.frame is not None:
            self.frame.destroy()
            self.frame = None
        if self._debug_window is not None:
            self._debug_window.destroy()
            self._debug_window = None

    def on_settings_updated(self) -> None:
        self._refresh_controls()

    def update(self) -> None:
        """Called by the emulator once per emulated frame."""
        if context.emulator._performance_tracker.time_since_last_render() >= (1 / 60) * 1_000_000_000:
            if context.emulator.get_video_enabled():
                self._update_video(context.emulator.get_current_screen_image())

            self._frame_counter += 1
            if self._frame_counter % SIDEBAR_REFRESH_FRAMES == 0:
                self._refresh_sidebar()
            if self._debug_window is not None:
                self._update_debug_tabs()

            self.window.update_idletasks()
            self.window.update()
            context.emulator._performance_tracker.track_render()

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------

    def _build_menu_bar(self) -> None:
        # Same menus as the stock GUI (emulator_controls.py) so no stock
        # functionality is lost.
        import webbrowser

        from showinfm import show_in_file_manager

        from modules.gui.load_state_window import LoadStateWindow

        menu_bar = Menu(self.window)

        emulator_menu = Menu(self.window, tearoff=0)
        emulator_menu.add_command(label="Load Save State", command=lambda: LoadStateWindow(self.window))
        emulator_menu.add_command(label="New Save State", command=lambda: context.emulator.create_save_state("Manual"))
        emulator_menu.add_command(label="Take Screenshot", command=lambda: context.emulator.take_screenshot("manual"))
        emulator_menu.add_separator()
        emulator_menu.add_command(label="Reset", command=lambda: context.emulator.reset())

        profile_menu = Menu(self.window, tearoff=0)
        profile_menu.add_command(
            label="Open Profile Folder", command=lambda: show_in_file_manager(str(context.profile.path))
        )

        view_menu = Menu(self.window, tearoff=0)
        view_menu.add_command(label="Handheld Mode (F11)", command=self.toggle_handheld)
        view_menu.add_command(label="Classic GUI", command=self._explain_classic_gui)

        help_menu = Menu(self.window, tearoff=0)
        help_menu.add_command(
            label=f"{pokebot_name} Wiki",
            command=lambda: webbrowser.open_new_tab("https://github.com/40Cakes/pokebot-gen3/tree/main/wiki"),
        )

        menu_bar.add_cascade(label="Emulator", menu=emulator_menu)
        menu_bar.add_cascade(label="Profile", menu=profile_menu)
        menu_bar.add_cascade(label="View", menu=view_menu)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        if context.debug:
            from modules.gui.debug_menu import DebugMenu

            menu_bar.add_cascade(label="Debug", menu=DebugMenu(self.window))

        self.window.config(menu=menu_bar)

    def _explain_classic_gui(self) -> None:
        context.message = "Restart the bot with --classic-gui to use the original interface."

    def _build_video_area(self) -> None:
        self.canvas = Canvas(self.window, background="#000000", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="NSWE")
        self.canvas.bind("<Configure>", self._on_video_resized)
        self.canvas.bind("<Double-Button-1>", lambda _event: self.toggle_handheld())

        if context.debug:

            def handle_click_on_video_output(event):
                if context.video:
                    offset_x, offset_y, size = self._video_draw_rect()
                    scale = max(1, size[0] // 240)
                    position = ((event.x - offset_x) // scale, (event.y - offset_y) // scale)
                    if 0 <= position[0] < 240 and 0 <= position[1] < 160:
                        for tab in self._debug_tabs:
                            tab.on_video_output_click(position, scale)

            self.canvas.bind("<Button-1>", handle_click_on_video_output)

    def _build_tool_column(self) -> None:
        self.frame = ttk.Frame(self.window, width=TOOL_COLUMN_WIDTH)
        self.frame.grid(row=0, column=1, sticky="NSE")
        self.frame.grid_propagate(False)

        tools = tkinter.Frame(self.frame, background=COLOR_SURFACE, width=TOOL_COLUMN_WIDTH)
        tools.pack(fill="both", expand=True)
        tools.pack_propagate(False)
        self._tools_container = tools

        # --- drawer header (only visible in handheld mode) ---
        self._drawer_header = tkinter.Frame(tools, background=COLOR_SURFACE)
        tkinter.Label(
            self._drawer_header, text="TOOLS", background=COLOR_SURFACE, foreground=COLOR_INK_2, font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=10, pady=6)
        tkinter.Button(
            self._drawer_header,
            text="Hide",
            command=lambda: self._set_drawer(False),
            background=COLOR_CARD,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            padx=10,
        ).pack(side="right", padx=10, pady=4)
        # (packed on demand in _apply_handheld_layout)

        # --- controls card ---
        controls = self._card(tools, "CONTROLS")

        mode_row = tkinter.Frame(controls, background=COLOR_CARD)
        mode_row.pack(fill="x", pady=(2, 6))
        tkinter.Label(mode_row, text="Bot mode", width=9, anchor="w", background=COLOR_CARD, foreground=COLOR_INK_2).pack(
            side="left"
        )
        self._mode_button = tkinter.Button(
            mode_row,
            text=f"{context.bot_mode} ▾",
            command=self._open_mode_menu,
            background=COLOR_SURFACE,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            anchor="w",
            padx=8,
        )
        self._mode_button.pack(side="left", fill="x", expand=True)

        speed_row = tkinter.Frame(controls, background=COLOR_CARD)
        speed_row.pack(fill="x", pady=(0, 6))
        tkinter.Label(speed_row, text="Speed", width=9, anchor="w", background=COLOR_CARD, foreground=COLOR_INK_2).pack(
            side="left"
        )
        for speed in (1, 2, 3, 4, 8, 16, 32, 0):
            label = "∞" if speed == 0 else f"{speed}×"
            button = tkinter.Button(
                speed_row,
                text=label,
                command=lambda s=speed: self._set_speed(s),
                background=COLOR_SURFACE,
                foreground=COLOR_INK,
                activebackground=COLOR_ACCENT,
                activeforeground=COLOR_INK,
                relief="flat",
                font=("Segoe UI", 8),
                padx=3,
            )
            button.pack(side="left", padx=1)
            self._speed_buttons[speed] = button

        output_row = tkinter.Frame(controls, background=COLOR_CARD)
        output_row.pack(fill="x", pady=(0, 4))
        tkinter.Label(output_row, text="Output", width=9, anchor="w", background=COLOR_CARD, foreground=COLOR_INK_2).pack(
            side="left"
        )
        self._video_button = tkinter.Button(
            output_row,
            text="Video",
            command=context.toggle_video,
            background=COLOR_SURFACE,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            padx=8,
        )
        self._video_button.pack(side="left", padx=1)
        self._audio_button = tkinter.Button(
            output_row,
            text="Audio",
            command=context.toggle_audio,
            background=COLOR_SURFACE,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            padx=8,
        )
        self._audio_button.pack(side="left", padx=1)

        handheld_row = tkinter.Frame(controls, background=COLOR_CARD)
        handheld_row.pack(fill="x", pady=(4, 2))
        tkinter.Button(
            handheld_row,
            text="Handheld mode  (F11)",
            command=self.toggle_handheld,
            background=COLOR_SURFACE,
            foreground=COLOR_INK_2,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            padx=8,
        ).pack(fill="x")

        # --- KPI card ---
        kpis = self._card(tools, "STATS")
        kpi_grid = tkinter.Frame(kpis, background=COLOR_CARD)
        kpi_grid.pack(fill="x")
        kpi_grid.columnconfigure((0, 1), weight=1, uniform="kpi")
        definitions = [
            ("total", "TOTAL ENCOUNTERS"),
            ("shinies", "SHINIES ✨"),
            ("phase", "PHASE ENCOUNTERS"),
            ("rate", "ENCOUNTERS / HR"),
        ]
        for index, (key, label) in enumerate(definitions):
            cell = tkinter.Frame(kpi_grid, background=COLOR_SURFACE, padx=8, pady=6)
            cell.grid(row=index // 2, column=index % 2, sticky="NSWE", padx=2, pady=2)
            tkinter.Label(
                cell, text=label, background=COLOR_SURFACE, foreground=COLOR_INK_2, font=("Segoe UI", 7, "bold"), anchor="w"
            ).pack(fill="x")
            value_label = tkinter.Label(
                cell, text="—", background=COLOR_SURFACE, foreground=COLOR_INK, font=("Segoe UI", 16, "bold"), anchor="w"
            )
            value_label.pack(fill="x")
            self._kpi_values[key] = value_label

        # --- party card ---
        party_card = self._card(tools, "PARTY")
        self._party_container = tkinter.Frame(party_card, background=COLOR_CARD)
        self._party_container.pack(fill="x")

        # --- status line + message ---
        status_card = self._card(tools, "STATUS")
        self._state_label = tkinter.Label(
            status_card, text="—", background=COLOR_CARD, foreground=COLOR_INK_2, anchor="w"
        )
        self._state_label.pack(fill="x")
        self._fps_label = tkinter.Label(status_card, text="", background=COLOR_CARD, foreground=COLOR_MUTED, anchor="w")
        self._fps_label.pack(fill="x")
        self._message_label = tkinter.Label(
            status_card,
            text="",
            background=COLOR_CARD,
            foreground=COLOR_INK_2,
            anchor="w",
            wraplength=TOOL_COLUMN_WIDTH - 40,
            justify="left",
        )
        self._message_label.pack(fill="x")

        # --- backups card (sandbox A1) ---
        backup_card = self._card(tools, "BACKUPS")
        self._backup_label = tkinter.Label(
            backup_card, text="No backups yet.", background=COLOR_CARD, foreground=COLOR_MUTED, anchor="w",
            font=("Segoe UI", 8),
        )
        self._backup_label.pack(fill="x")
        backup_buttons = tkinter.Frame(backup_card, background=COLOR_CARD)
        backup_buttons.pack(fill="x", pady=(4, 2))
        tkinter.Button(
            backup_buttons,
            text="Back up now",
            command=self._backup_now,
            background=COLOR_SURFACE,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            padx=8,
        ).pack(side="left", padx=(0, 4))
        tkinter.Button(
            backup_buttons,
            text="Restore…",
            command=self._open_restore_dialog,
            background=COLOR_SURFACE,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            padx=8,
        ).pack(side="left")

        # --- event log ---
        log_card = self._card(tools, "EVENT LOG", expand=True)
        self._event_list = tkinter.Listbox(
            log_card,
            background=COLOR_CARD,
            foreground=COLOR_INK_2,
            selectbackground=COLOR_ACCENT,
            highlightthickness=0,
            borderwidth=0,
            font=("Segoe UI", 8),
        )
        self._event_list.pack(fill="both", expand=True)

    def _card(self, parent: tkinter.Widget, title: str, expand: bool = False) -> tkinter.Frame:
        outer = tkinter.Frame(parent, background=COLOR_SURFACE)
        outer.pack(fill="both" if expand else "x", expand=expand, padx=8, pady=(8, 0))
        card = tkinter.Frame(outer, background=COLOR_CARD, padx=8, pady=6)
        card.pack(fill="both", expand=True)
        tkinter.Label(
            card, text=title, background=COLOR_CARD, foreground=COLOR_INK_2, font=("Segoe UI", 8, "bold"), anchor="w"
        ).pack(fill="x", pady=(0, 4))
        return card

    def _build_pokeball_button(self) -> None:
        size = 46
        ball = Canvas(self.window, width=size, height=size, background="#000000", highlightthickness=0)
        pad = 3
        # bottom half (white), top half (red), band, center button
        ball.create_oval(pad, pad, size - pad, size - pad, fill="#f4f4f2", outline="#1c1c1c", width=3)
        ball.create_arc(pad, pad, size - pad, size - pad, start=0, extent=180, fill="#e34948", outline="#1c1c1c", width=3)
        band = size // 2
        ball.create_rectangle(pad, band - 2, size - pad, band + 2, fill="#1c1c1c", outline="#1c1c1c")
        ball.create_oval(band - 7, band - 7, band + 7, band + 7, fill="#1c1c1c", outline="#1c1c1c")
        ball.create_oval(band - 5, band - 5, band + 5, band + 5, fill="#f4f4f2", outline="#1c1c1c")
        ball.bind("<Button-1>", lambda _event: self._set_drawer(True))
        ball.configure(cursor="hand2")
        self._pokeball_button = ball
        # placed/hidden by _apply_handheld_layout

    # ------------------------------------------------------------------
    # Handheld mode
    # ------------------------------------------------------------------

    def toggle_handheld(self) -> None:
        self._handheld = not self._handheld
        self._drawer_open = False
        self._apply_handheld_layout()
        self._persist_ui_state()

    def handle_hotkey(self, keysym: str) -> bool:
        """Called by PokebotDashboardGui's key handler. Returns True if handled."""
        key = keysym.lower()
        if key == "f11":
            self.toggle_handheld()
            return True
        if key == "h":
            if self._handheld:
                self._set_drawer(not self._drawer_open)
            else:
                self.toggle_handheld()
            return True
        if key == "escape":
            if self._handheld and self._drawer_open:
                self._set_drawer(False)
                return True
            if self._handheld:
                self.toggle_handheld()
                return True
        return False

    def _set_drawer(self, open_: bool) -> None:
        self._drawer_open = open_
        self._apply_handheld_layout()

    def _apply_handheld_layout(self) -> None:
        try:
            self.window.attributes("-fullscreen", self._handheld)
        except tkinter.TclError:
            pass

        if self._handheld:
            self.frame.grid_remove()
            self._drawer_header.pack_forget()
            if self._drawer_open:
                self._drawer_header.pack(in_=self._tools_container, fill="x", before=self._tools_container.winfo_children()[1])
                self.frame.place(relx=1.0, rely=0.0, relheight=1.0, anchor="ne", width=TOOL_COLUMN_WIDTH)
                self._pokeball_button.place_forget()
            else:
                self.frame.place_forget()
                self._pokeball_button.place(relx=1.0, x=-12, y=12, anchor="ne")
        else:
            self.frame.place_forget()
            self._pokeball_button.place_forget()
            self._drawer_header.pack_forget()
            self.frame.grid(row=0, column=1, sticky="NSE")

    def _persist_ui_state(self) -> None:
        try:
            state_file = context.profile.path / UI_STATE_FILE
            state_file.write_text(json.dumps({"handheld": self._handheld}), encoding="utf-8")
        except Exception:
            pass

    def _restore_ui_state(self) -> None:
        try:
            state_file = context.profile.path / UI_STATE_FILE
            if state_file.is_file():
                state = json.loads(state_file.read_text(encoding="utf-8"))
                if state.get("handheld"):
                    self._handheld = True
                    self._apply_handheld_layout()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Video rendering
    # ------------------------------------------------------------------

    def _on_video_resized(self, _event=None) -> None:
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        if width / height > GBA_ASPECT:
            new_height = height
            new_width = int(height * GBA_ASPECT)
        else:
            new_width = width
            new_height = int(width / GBA_ASPECT)
        self._video_size = (max(240, new_width), max(160, new_height))

    def _video_draw_rect(self) -> tuple[int, int, tuple[int, int]]:
        canvas_width = max(1, self.canvas.winfo_width())
        canvas_height = max(1, self.canvas.winfo_height())
        offset_x = (canvas_width - self._video_size[0]) // 2
        offset_y = (canvas_height - self._video_size[1]) // 2
        return offset_x, offset_y, self._video_size

    def _update_video(self, image: PIL.Image.Image) -> None:
        offset_x, offset_y, size = self._video_draw_rect()
        if self._current_canvas_image_id:
            self.canvas.delete(self._current_canvas_image_id)
        self._current_canvas_image = PIL.ImageTk.PhotoImage(image=image.resize(size, resample=PIL.Image.NEAREST))
        self._current_canvas_image_id = self.canvas.create_image(
            offset_x + size[0] // 2, offset_y + size[1] // 2, image=self._current_canvas_image, state="normal"
        )

    # ------------------------------------------------------------------
    # Sidebar data
    # ------------------------------------------------------------------

    def _refresh_sidebar(self) -> None:
        self._refresh_controls()
        self._refresh_status_line()
        self._refresh_party()
        if time.monotonic() - self._last_kpi_refresh >= KPI_REFRESH_SECONDS:
            self._refresh_kpis()
            self._refresh_backup_label()

    def _refresh_controls(self) -> None:
        if self._mode_button is None:
            return
        self._mode_button.config(text=f"{context.bot_mode} ▾")
        for speed, button in self._speed_buttons.items():
            active = context.emulation_speed == speed
            button.config(background=COLOR_ACCENT if active else COLOR_SURFACE)
        self._video_button.config(background=COLOR_ACCENT if context.video else COLOR_SURFACE)
        self._audio_button.config(background=COLOR_ACCENT if context.audio else COLOR_SURFACE)

    def _refresh_status_line(self) -> None:
        try:
            state_name = get_game_state().name
        except Exception:
            state_name = "—"
        self._state_label.config(text=f"State: {state_name}")

        stats = []
        current_fps = context.emulator.get_current_fps()
        if current_fps:
            stats.append(f"{current_fps:,} fps ({current_fps / 59.727500569606:0.1f}×)")
        self._fps_label.config(text=" | ".join(stats))
        self._message_label.config(text=context.message or "")

    def _refresh_kpis(self) -> None:
        self._last_kpi_refresh = time.monotonic()
        try:
            global_stats = context.stats.get_global_stats()
            totals = global_stats.totals
            self._kpi_values["total"].config(text=f"{totals.total_encounters:,}")
            self._kpi_values["shinies"].config(text=f"{totals.shiny_encounters:,}")
            phase = global_stats.current_shiny_phase
            self._kpi_values["phase"].config(text=f"{phase.encounters:,}" if phase is not None else "0")
            self._kpi_values["rate"].config(text=f"{context.stats.encounter_rate:,}")
        except Exception:
            pass

    def _refresh_party(self) -> None:
        try:
            from modules.pokemon_party import get_party

            party = list(get_party())
        except Exception:
            party = []

        # Rebuild rows only when the party size changes; otherwise update in place.
        if len(party) != len(self._party_rows):
            for row in self._party_rows:
                row["frame"].destroy()
            self._party_rows = []
            for _ in party:
                row_frame = tkinter.Frame(self._party_container, background=COLOR_SURFACE, padx=6, pady=4)
                row_frame.pack(fill="x", pady=2)
                top = tkinter.Frame(row_frame, background=COLOR_SURFACE)
                top.pack(fill="x")
                name = tkinter.Label(
                    top, text="", background=COLOR_SURFACE, foreground=COLOR_INK, font=("Segoe UI", 9, "bold"), anchor="w"
                )
                name.pack(side="left")
                level = tkinter.Label(top, text="", background=COLOR_SURFACE, foreground=COLOR_INK_2, anchor="e")
                level.pack(side="right")
                bar_row = tkinter.Frame(row_frame, background=COLOR_SURFACE)
                bar_row.pack(fill="x", pady=(2, 0))
                bar_bg = tkinter.Frame(bar_row, background=COLOR_HAIRLINE, height=4)
                bar_bg.pack(side="left", fill="x", expand=True)
                bar_bg.pack_propagate(False)
                bar_fill = tkinter.Frame(bar_bg, background=COLOR_GOOD, height=4)
                bar_fill.place(x=0, y=0, relheight=1.0, relwidth=0.0)
                hp_text = tkinter.Label(
                    bar_row, text="", background=COLOR_SURFACE, foreground=COLOR_INK_2, font=("Segoe UI", 8), anchor="e"
                )
                hp_text.pack(side="right", padx=(6, 0))
                self._party_rows.append(
                    {
                        "frame": row_frame,
                        "name": name,
                        "level": level,
                        "bar_fill": bar_fill,
                        "hp_text": hp_text,
                    }
                )

        for pokemon, row in zip(party, self._party_rows):
            self._update_party_row(pokemon, row)

    def _update_party_row(self, pokemon: "Pokemon", row: dict) -> None:
        if pokemon.is_egg:
            row["name"].config(text="Egg", foreground=COLOR_MUTED)
            row["level"].config(text="")
            row["bar_fill"].place_configure(relwidth=0.0)
            row["hp_text"].config(text="")
            return

        name = pokemon.name
        if pokemon.is_shiny:
            name += "  ✨"
        row["name"].config(text=name, foreground=COLOR_SHINY if pokemon.is_shiny else COLOR_INK)
        row["level"].config(text=f"Lv {pokemon.level}")

        total_hp = pokemon.total_hp or 0
        current_hp = pokemon.current_hp or 0
        fraction = (current_hp / total_hp) if total_hp else 0.0
        if fraction <= 0.2:
            color = COLOR_CRITICAL
        elif fraction <= 0.5:
            color = COLOR_WARNING
        else:
            color = COLOR_GOOD
        row["bar_fill"].configure(background=color)
        row["bar_fill"].place_configure(relwidth=max(0.0, min(1.0, fraction)))

        status = pokemon.status_condition
        status_text = f"  {status.name}" if status is not StatusCondition.Healthy else ""
        row["hp_text"].config(
            text=f"{current_hp}/{total_hp}{status_text}",
            foreground=COLOR_CRITICAL if status_text else COLOR_INK_2,
        )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _on_encounter_logged(self, encounter: "EncounterInfo") -> None:
        try:
            pokemon = encounter.pokemon
            text = f"Encounter: {pokemon.name}"
            shiny = bool(pokemon.is_shiny)
            if shiny:
                text += "  — ✨ SHINY! ✨"
            self._log_event(text, highlight=shiny)
            self._last_kpi_refresh = 0.0  # force KPI refresh on next tick
        except Exception:
            pass

    def _log_event(self, text: str, highlight: bool = False) -> None:
        if self._event_list is None:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._event_list.insert(0, f"{timestamp}  {text}")
        self._event_list.itemconfig(0, foreground=COLOR_SHINY if highlight else COLOR_INK_2)
        if self._event_list.size() > 100:
            self._event_list.delete(100, "end")

    # ------------------------------------------------------------------
    # Backups (sandbox A1)
    # ------------------------------------------------------------------

    def _refresh_backup_label(self) -> None:
        if getattr(self, "_backup_label", None) is None or context.profile is None:
            return
        try:
            from modules import backup_manager

            elapsed = backup_manager.seconds_since_last_backup(context.profile.path.name)
            if elapsed is None:
                self._backup_label.config(text="No backups yet.")
            elif elapsed < 90:
                self._backup_label.config(text="Last backup: just now")
            elif elapsed < 5400:
                self._backup_label.config(text=f"Last backup: {int(elapsed // 60)} min ago")
            else:
                self._backup_label.config(text=f"Last backup: {elapsed / 3600:.1f} h ago")
        except Exception:
            pass

    def _backup_now(self) -> None:
        if context.profile is None:
            return
        try:
            from modules import backup_manager

            result = backup_manager.create_backup(context.profile.path, reason="manual")
            if result is not None:
                self._log_event(f"Backup created: {result.name}")
            else:
                self._log_event("Backup skipped/failed — see logs/backup.log", highlight=True)
            self._refresh_backup_label()
        except Exception as error:
            self._log_event(f"Backup error: {error}", highlight=True)

    def _open_restore_dialog(self) -> None:
        if context.profile is None:
            return
        from modules import backup_manager

        backups = backup_manager.list_backups(context.profile.path.name)

        dialog = tkinter.Toplevel(self.window)
        dialog.title("Restore a backup")
        dialog.configure(background=COLOR_SURFACE)
        dialog.geometry("460x360")
        dialog.transient(self.window)

        tkinter.Label(
            dialog,
            text="Restores create a NEW profile — the current one stays untouched.",
            background=COLOR_SURFACE,
            foreground=COLOR_INK_2,
            anchor="w",
            wraplength=430,
            justify="left",
        ).pack(fill="x", padx=10, pady=(10, 4))

        listbox = tkinter.Listbox(
            dialog,
            background=COLOR_CARD,
            foreground=COLOR_INK_2,
            selectbackground=COLOR_ACCENT,
            highlightthickness=0,
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        listbox.pack(fill="both", expand=True, padx=10, pady=4)
        if backups:
            for entry in backups:
                listbox.insert("end", entry["label"])
        else:
            listbox.insert("end", "(no backups for this profile yet)")

        name_row = tkinter.Frame(dialog, background=COLOR_SURFACE)
        name_row.pack(fill="x", padx=10, pady=4)
        tkinter.Label(
            name_row, text="New profile name:", background=COLOR_SURFACE, foreground=COLOR_INK_2
        ).pack(side="left")
        name_variable = tkinter.StringVar(value=f"{context.profile.path.name}-restored")
        tkinter.Entry(
            name_row, textvariable=name_variable, background=COLOR_CARD, foreground=COLOR_INK,
            insertbackground=COLOR_INK, relief="flat",
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

        feedback = tkinter.Label(
            dialog, text="", background=COLOR_SURFACE, foreground=COLOR_WARNING, anchor="w", wraplength=430,
            justify="left",
        )
        feedback.pack(fill="x", padx=10)

        def do_restore() -> None:
            selection = listbox.curselection()
            if not backups or not selection:
                feedback.config(text="Select a backup from the list first.")
                return
            entry = backups[selection[0]]
            try:
                target = backup_manager.restore_backup(entry["path"], name_variable.get().strip())
            except ValueError as error:
                feedback.config(text=str(error))
                return
            feedback.config(
                text=f"Restored to '{target.name}'. Close the bot and relaunch with that profile to use it.",
                foreground=COLOR_GOOD,
            )
            self._log_event(f"Backup restored into new profile '{target.name}'")

        tkinter.Button(
            dialog,
            text="Restore into new profile",
            command=do_restore,
            background=COLOR_ACCENT,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            padx=10,
        ).pack(pady=(2, 10))

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def _set_speed(self, speed: int) -> None:
        context.emulation_speed = speed
        self._refresh_controls()

    def _open_mode_menu(self) -> None:
        # Same behaviour as the stock bot-mode picker (emulator_controls.py):
        # modes report is_selectable() and get greyed out otherwise.
        from modules.console import console
        from modules.memory import GameState
        from modules.modes import get_bot_modes

        bold_font = tkinter.font.Font(self.window, weight="bold", size=10)
        menu = tkinter.Menu(self.window, tearoff=0)

        def select_bot_mode(mode_name: str):
            if mode_name == "Manual":
                context.set_manual_mode(enable_video_and_slow_down=False)
            else:
                context.bot_mode = mode_name
            self._log_event(f"Bot mode set to {mode_name}")
            self._refresh_controls()

        if context.bot_mode == "Manual":
            menu.add_command(label="Manual", font=bold_font)
        else:
            menu.add_command(label="Manual", command=lambda: select_bot_mode("Manual"))
        menu.add_separator()
        disabled_modes = []
        for mode in get_bot_modes():
            if mode.name() == context.bot_mode:
                menu.add_command(label=mode.name(), font=bold_font)
                continue
            try:
                game_state = get_game_state()
            except Exception:
                game_state = None
            if game_state not in (GameState.TITLE_SCREEN, GameState.MAIN_MENU, None):
                try:
                    is_selectable = mode.is_selectable()
                except Exception:
                    if context.debug:
                        console.print_exception()
                    is_selectable = False
            else:
                is_selectable = False
            if is_selectable:
                menu.add_command(label=mode.name(), command=lambda m=mode: select_bot_mode(m.name()))
            else:
                disabled_modes.append(mode.name())
        if disabled_modes:
            menu.add_separator()
            for mode_name in disabled_modes:
                menu.add_command(label=mode_name, state="disabled")
        menu.tk_popup(
            self._mode_button.winfo_rootx(), self._mode_button.winfo_rooty() + self._mode_button.winfo_height()
        )

    # ------------------------------------------------------------------
    # Debug support
    # ------------------------------------------------------------------

    def _build_debug_window(self) -> None:
        from modules.gui.debug_tabs import (
            BattleTab,
            EmulatorTab,
            EventFlagsTab,
            EventVarsTab,
            MapTab,
            MiscTab,
            PlayerTab,
            SymbolsTab,
            TasksTab,
        )

        self._debug_window = tkinter.Toplevel(self.window)
        self._debug_window.title("Debug")
        self._debug_window.geometry("560x640")
        self._debug_window.protocol("WM_DELETE_WINDOW", self._debug_window.withdraw)
        self._debug_notebook = ttk.Notebook(self._debug_window)
        self._debug_tabs = [
            TasksTab(),
            BattleTab(),
            PlayerTab(),
            MapTab(self.canvas),
            MiscTab(),
            SymbolsTab(),
            EventFlagsTab(),
            EventVarsTab(),
            EmulatorTab(),
        ]
        for tab in self._debug_tabs:
            tab.draw(self._debug_notebook)
        self._debug_notebook.pack(fill="both", expand=True)

    def _update_debug_tabs(self) -> None:
        try:
            if self._debug_window.state() == "withdrawn":
                return
            index = self._debug_notebook.index("current")
            self._debug_tabs[index].update(context.emulator)
        except Exception:
            pass


class PokebotDashboardGui(PokebotGui):
    """The fork's default GUI: stock plumbing + the dashboard screen."""

    def __init__(self, main_loop: callable, on_exit: callable, no_theme: bool = False, use_opengl: bool = False):
        # use_opengl is not supported by the dashboard screen; the stock GUI
        # remains available for that via --classic-gui.
        super().__init__(main_loop, on_exit, no_theme=no_theme, use_opengl=False)
        self._emulator_screen = DashboardScreen(self.window)

    def _handle_key_down_event(self, event):
        if (
            self._current_screen is self._emulator_screen
            and self.inputs_enabled
            and self._emulator_screen.handle_hotkey(event.keysym)
        ):
            return "break"
        return super()._handle_key_down_event(event)
