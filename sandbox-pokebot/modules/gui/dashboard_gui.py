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

Dialogs vs. emulation: there is no Tk mainloop — the Tk event queue is
pumped from `update()`, which the emulator calls once per frame. The
Restore dialog is therefore deliberately non-modal (no grab/wait_window):
emulation keeps running while it is open. The macro name prompt
(simpledialog.askstring) IS modal — wait_window runs a nested event loop
inside the frame callback, so emulation pauses until it is closed. That is
harmless by design: recording has already stopped before the prompt opens.
"""

import json
import os
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
        self._mousewheel_bound = False

        self._handheld = False
        self._drawer_open = False

        # Widgets that get updated live
        self._mode_button: tkinter.Button | None = None
        self._speed_buttons: dict[int, tkinter.Button] = {}
        self._video_button: tkinter.Button | None = None
        self._audio_button: tkinter.Button | None = None
        self._kpi_values: dict[str, tkinter.Label] = {}
        self._party_rows: list[dict] = []
        self._sprite_cache: dict = {}  # Tk needs live references to PhotoImages
        self._shiny_log_label: tkinter.Label | None = None
        self._event_list: tkinter.Listbox | None = None
        self._message_label: tkinter.Label | None = None
        self._state_label: tkinter.Label | None = None
        self._fps_label: tkinter.Label | None = None
        self._controller_label: tkinter.Label | None = None
        self._update_label: tkinter.Label | None = None
        self._update_notice_logged = False
        self._pokeball_button: Canvas | None = None
        self._menu_bar: Menu | None = None

        # Debug support (stock debug tabs in a separate window)
        self._debug_window: tkinter.Toplevel | None = None
        self._debug_notebook: ttk.Notebook | None = None
        self._debug_tabs: list = []

        # Sandbox #18: once-per-launch update check in a daemon thread; the
        # result is polled from the sidebar refresh (Tk stays on this thread).
        try:
            from modules.runtime import get_base_path
            from modules.update_check import start_background_check

            start_background_check(get_base_path())
        except Exception:
            pass  # the notice is best-effort; launch must never be affected

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
        # 860: tall enough for every tool card (incl. Backups + Macros) with
        # some event log visible; still clamped to small screens.
        height = min(860, screen_height - 100)
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
        # The video canvas and the Pokéball overlay are children of the root
        # window (not of `frame`), so they must be destroyed explicitly or
        # they would linger over whatever screen comes next.
        if self.canvas is not None:
            self.canvas.destroy()
            self.canvas = None
        if self._pokeball_button is not None:
            self._pokeball_button.destroy()
            self._pokeball_button = None
        if self._debug_window is not None:
            self._debug_window.destroy()
            self._debug_window = None
        # Drop references to destroyed widgets so refresh paths (guarded by
        # `self.frame is None`) can never .config() a dead widget, and so a
        # later enable() starts from a clean slate.
        self._current_canvas_image = None
        self._current_canvas_image_id = None
        self._mode_button = None
        self._speed_buttons = {}
        self._video_button = None
        self._audio_button = None
        self._kpi_values = {}
        self._party_rows = []
        self._sprite_cache = {}
        self._shiny_log_label = None
        self._event_list = None
        self._message_label = None
        self._state_label = None
        self._fps_label = None
        self._controller_label = None
        self._update_label = None
        self._update_notice_logged = False  # re-show the notice if re-enabled
        self._sync_label = None
        self._sync_import_button = None
        self._sync_status_logged = False
        self._menu_bar = None
        self._debug_tabs = []

    def on_settings_updated(self) -> None:
        self._refresh_controls()

    def update(self) -> None:
        """Called by the emulator once per emulated frame."""
        if self.frame is None:
            # Screen is disabled — never touch destroyed widgets.
            return
        if context.emulator._performance_tracker.time_since_last_render() >= (1 / 60) * 1_000_000_000:
            if context.emulator.get_video_enabled():
                self._update_video(context.emulator.get_current_screen_image())

            self._frame_counter += 1
            if self._frame_counter % SIDEBAR_REFRESH_FRAMES == 0:
                try:
                    self._refresh_sidebar()
                except Exception:
                    # A transient stats/party/memory read failure must never
                    # kill the emulator frame loop; the next cycle retries.
                    if context.debug:
                        from modules.console import console

                        console.print_exception()
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

        self._menu_bar = menu_bar
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

        column = tkinter.Frame(self.frame, background=COLOR_SURFACE, width=TOOL_COLUMN_WIDTH)
        column.pack(fill="both", expand=True)
        column.pack_propagate(False)
        self._tools_container = column

        # --- drawer header (only visible in handheld mode) ---
        self._drawer_header = tkinter.Frame(column, background=COLOR_SURFACE)
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

        # --- scrollable card area (A4): all cards live inside `tools`, which
        # sits in a canvas window so the column can never clip off-screen at
        # small window heights or high DPI — desktop and handheld drawer alike.
        self._scroll_area = tkinter.Frame(column, background=COLOR_SURFACE)
        self._scroll_area.pack(fill="both", expand=True)
        self._cards_canvas = Canvas(
            self._scroll_area, background=COLOR_SURFACE, highlightthickness=0, borderwidth=0
        )
        scrollbar = tkinter.Scrollbar(
            self._scroll_area, orient="vertical", command=self._cards_canvas.yview, width=10
        )
        scrollbar.pack(side="right", fill="y")
        self._cards_canvas.pack(side="left", fill="both", expand=True)
        tools = tkinter.Frame(self._cards_canvas, background=COLOR_SURFACE)
        self._cards_window = self._cards_canvas.create_window((0, 0), window=tools, anchor="nw")
        self._cards_canvas.configure(yscrollcommand=scrollbar.set)
        tools.bind(
            "<Configure>",
            lambda _event: self._cards_canvas.configure(scrollregion=self._cards_canvas.bbox("all")),
        )
        self._cards_canvas.bind(
            "<Configure>",
            lambda event: self._cards_canvas.itemconfigure(self._cards_window, width=event.width),
        )
        # Bind exactly once for the lifetime of the process: enable() may run
        # again after a disable(), and stacking bind_all handlers would make
        # each wheel notch scroll multiple units.
        if not self._mousewheel_bound:
            self.window.bind_all("<MouseWheel>", self._on_tool_mousewheel, add="+")
            self._mousewheel_bound = True

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

        # --- macros card (sandbox A2; kept right under Controls so the
        # interactive cards never get clipped on short windows) ---
        macro_card = self._card(tools, "MACROS")
        macro_row = tkinter.Frame(macro_card, background=COLOR_CARD)
        macro_row.pack(fill="x", pady=(0, 2))
        self._macro_record_button = tkinter.Button(
            macro_row,
            text="● Rec",
            command=self._toggle_macro_recording,
            background=COLOR_SURFACE,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            font=("Segoe UI", 8),
            padx=6,
        )
        self._macro_record_button.pack(side="left", padx=(0, 4))
        self._macro_variable = tkinter.StringVar(self.window, value="(no macros)")
        self._macro_menu = tkinter.OptionMenu(macro_row, self._macro_variable, "(no macros)")
        self._macro_menu.config(
            background=COLOR_SURFACE,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            highlightthickness=0,
            font=("Segoe UI", 8),
            anchor="w",
        )
        self._macro_menu["menu"].config(background=COLOR_SURFACE, foreground=COLOR_INK)
        self._macro_menu.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._macro_loop_variable = tkinter.BooleanVar(self.window, value=True)
        tkinter.Checkbutton(
            macro_row,
            text="Loop",
            variable=self._macro_loop_variable,
            background=COLOR_CARD,
            foreground=COLOR_INK_2,
            activebackground=COLOR_CARD,
            activeforeground=COLOR_INK,
            selectcolor=COLOR_SURFACE,
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(0, 4))
        tkinter.Button(
            macro_row,
            text="▶",
            command=self._play_selected_macro,
            background=COLOR_SURFACE,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            font=("Segoe UI", 8),
            padx=8,
        ).pack(side="left")
        self._refresh_macro_menu()

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

        # --- shiny log card (sandbox A4) ---
        shiny_card = self._card(tools, "SHINY LOG")
        self._shiny_log_label = tkinter.Label(
            shiny_card,
            text="No shinies yet — keep hunting!",
            background=COLOR_CARD,
            foreground=COLOR_MUTED,
            anchor="w",
            justify="left",
            font=("Segoe UI", 8),
        )
        self._shiny_log_label.pack(fill="x")

        # --- backups card (sandbox A1) ---
        backup_card = self._card(tools, "BACKUPS")
        self._backup_label = tkinter.Label(
            backup_card, text="No backups yet.", background=COLOR_CARD, foreground=COLOR_MUTED, anchor="w",
            font=("Segoe UI", 8),
        )
        self._backup_label.pack(fill="x")
        # A8 cloud sync status + (conflict-only) import button
        self._sync_label = tkinter.Label(
            backup_card, text="", background=COLOR_CARD, foreground=COLOR_MUTED, anchor="w",
            font=("Segoe UI", 8),
        )
        self._sync_label.pack(fill="x")
        self._sync_import_button = tkinter.Button(
            backup_card,
            text="Import cloud save as new profile…",
            command=self._import_cloud_conflict,
            background=COLOR_SURFACE,
            foreground=COLOR_WARNING,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            padx=8,
        )
        # packed on demand by _refresh_sync_line when a conflict exists
        self._sync_status_logged = False
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

        # --- status line + message ---
        status_card = self._card(tools, "STATUS")
        self._state_label = tkinter.Label(
            status_card, text="—", background=COLOR_CARD, foreground=COLOR_INK_2, anchor="w"
        )
        self._state_label.pack(fill="x")
        self._fps_label = tkinter.Label(status_card, text="", background=COLOR_CARD, foreground=COLOR_MUTED, anchor="w")
        self._fps_label.pack(fill="x")
        self._controller_label = tkinter.Label(
            status_card, text="", background=COLOR_CARD, foreground=COLOR_MUTED, anchor="w", font=("Segoe UI", 8)
        )
        self._controller_label.pack(fill="x")
        self._update_label = tkinter.Label(
            status_card, text="", background=COLOR_CARD, foreground=COLOR_ACCENT, anchor="w", font=("Segoe UI", 8, "bold")
        )
        # Packed on demand when the update check reports something.
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

        # --- event log ---
        # Fixed height: inside the scrollable column the card cannot expand
        # to fill leftover space; a bounded list keeps the scrollregion sane.
        log_card = self._card(tools, "EVENT LOG")
        self._event_list = tkinter.Listbox(
            log_card,
            background=COLOR_CARD,
            foreground=COLOR_INK_2,
            selectbackground=COLOR_ACCENT,
            highlightthickness=0,
            borderwidth=0,
            font=("Segoe UI", 8),
            height=9,
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
        self._apply_menu_visibility()

        if self._handheld:
            self.frame.grid_remove()
            self._drawer_header.pack_forget()
            if self._drawer_open:
                self._drawer_header.pack(in_=self._tools_container, fill="x", before=self._scroll_area)
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

    def _apply_menu_visibility(self) -> None:
        """Handheld fullscreen hides the Tk menu bar for a truly clean
        screen; opening the tool drawer (Pokéball/H) brings it back, and
        leaving handheld mode restores it permanently. Applied AFTER the
        fullscreen attribute change — on Windows, toggling fullscreen
        recreates the native window, so the menu must be (re)asserted on
        the new hwnd."""
        if self._menu_bar is None:
            return
        show_menu = (not self._handheld) or self._drawer_open
        try:
            self.window.config(menu=self._menu_bar if show_menu else "")
        except tkinter.TclError:
            pass

    def _prepare_dialog(self, dialog: tkinter.Toplevel) -> None:
        """Force a popup ABOVE the emulator and center it over the window.

        In handheld fullscreen the main window sits at the top of the Windows
        z-order, so a plain Toplevel opens *behind* the emulator video and
        looks like nothing happened. `-topmost` + `lift` + `focus_force`
        float it above even the fullscreen window; `grab_set` makes it modal;
        centering keeps it thumb-reachable on a handheld."""
        dialog.transient(self.window)
        try:
            dialog.attributes("-topmost", True)
        except tkinter.TclError:
            pass
        dialog.update_idletasks()
        try:
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            pos_x = self.window.winfo_rootx() + max(0, (self.window.winfo_width() - width) // 2)
            pos_y = self.window.winfo_rooty() + max(0, (self.window.winfo_height() - height) // 2)
            dialog.geometry(f"+{pos_x}+{pos_y}")
        except tkinter.TclError:
            pass
        dialog.lift()
        dialog.focus_force()
        try:
            dialog.grab_set()
        except tkinter.TclError:
            pass

    def _ask_text(self, title: str, prompt: str, initial: str = "") -> "str | None":
        """Touch-friendly, always-on-top replacement for
        simpledialog.askstring (which sinks behind the emulator in handheld
        fullscreen). Modal; returns the entered string, or None if cancelled.
        Like the stock prompt, this pauses emulation while it is open."""
        dialog = tkinter.Toplevel(self.window)
        dialog.title(title)
        dialog.configure(background=COLOR_SURFACE)
        result: dict = {"value": None}

        tkinter.Label(
            dialog, text=prompt, background=COLOR_SURFACE, foreground=COLOR_INK_2,
            justify="left", anchor="w", wraplength=420, font=("Segoe UI", 11),
        ).pack(fill="x", padx=16, pady=(16, 8))

        variable = tkinter.StringVar(value=initial)
        entry = tkinter.Entry(
            dialog, textvariable=variable, background=COLOR_CARD, foreground=COLOR_INK,
            insertbackground=COLOR_INK, relief="flat", font=("Segoe UI", 14),
        )
        entry.pack(fill="x", padx=16, ipady=6)

        def _accept() -> None:
            result["value"] = variable.get()
            dialog.destroy()

        def _cancel() -> None:
            result["value"] = None
            dialog.destroy()

        button_row = tkinter.Frame(dialog, background=COLOR_SURFACE)
        button_row.pack(fill="x", padx=16, pady=16)
        tkinter.Button(
            button_row, text="Cancel", command=_cancel, background=COLOR_CARD,
            foreground=COLOR_INK, relief="flat", font=("Segoe UI", 12), padx=16, pady=8,
        ).pack(side="right", padx=(8, 0))
        tkinter.Button(
            button_row, text="OK", command=_accept, background=COLOR_ACCENT,
            foreground="#ffffff", relief="flat", font=("Segoe UI", 12, "bold"), padx=20, pady=8,
        ).pack(side="right")

        entry.bind("<Return>", lambda _event: _accept())
        dialog.bind("<Escape>", lambda _event: _cancel())
        dialog.protocol("WM_DELETE_WINDOW", _cancel)
        dialog.geometry("460x210")
        entry.focus_set()
        entry.select_range(0, "end")
        self._prepare_dialog(dialog)
        self.window.wait_window(dialog)
        return result["value"]

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
            self._refresh_shiny_log()

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

        if self._controller_label is not None:
            try:
                from modules.gamepad import get_status_text

                self._controller_label.config(text=get_status_text())
            except Exception:
                pass

        # Sandbox #18: surface the async update-check result exactly once.
        if not self._update_notice_logged and self._update_label is not None:
            try:
                from modules.update_check import get_pending_update_count

                behind = get_pending_update_count()
                if behind:
                    self._update_notice_logged = True
                    notice = f"⬆ {behind} update(s) available — run install.py"
                    self._update_label.config(text=notice)
                    self._update_label.pack(fill="x")
                    self._log_event(notice, highlight=True)
            except Exception:
                pass

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
                sprite = tkinter.Label(top, background=COLOR_SURFACE)
                sprite.pack(side="left", padx=(0, 6))
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
                # XP bar — a thinner accent bar directly under the HP bar,
                # showing progress toward the next level.
                xp_row = tkinter.Frame(row_frame, background=COLOR_SURFACE)
                xp_row.pack(fill="x", pady=(2, 0))
                xp_bg = tkinter.Frame(xp_row, background=COLOR_HAIRLINE, height=3)
                xp_bg.pack(side="left", fill="x", expand=True)
                xp_bg.pack_propagate(False)
                xp_fill = tkinter.Frame(xp_bg, background=COLOR_ACCENT, height=3)
                xp_fill.place(x=0, y=0, relheight=1.0, relwidth=0.0)
                xp_text = tkinter.Label(
                    xp_row, text="", background=COLOR_SURFACE, foreground=COLOR_MUTED, font=("Segoe UI", 8), anchor="e"
                )
                xp_text.pack(side="right", padx=(6, 0))
                self._party_rows.append(
                    {
                        "frame": row_frame,
                        "sprite": sprite,
                        "sprite_key": None,
                        "name": name,
                        "level": level,
                        "bar_fill": bar_fill,
                        "hp_text": hp_text,
                        "xp_fill": xp_fill,
                        "xp_text": xp_text,
                    }
                )

        for pokemon, row in zip(party, self._party_rows):
            self._update_party_row(pokemon, row)

    def _update_party_row(self, pokemon: "Pokemon", row: dict) -> None:
        self._set_row_sprite(pokemon, row)
        if pokemon.is_egg:
            row["name"].config(text="Egg", foreground=COLOR_MUTED)
            row["level"].config(text="")
            row["bar_fill"].place_configure(relwidth=0.0)
            row["hp_text"].config(text="")
            row["xp_fill"].place_configure(relwidth=0.0)
            row["xp_text"].config(text="")
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

        try:
            xp_fraction = float(pokemon.exp_fraction_to_next_level)
        except Exception:
            xp_fraction = 0.0
        row["xp_fill"].place_configure(relwidth=max(0.0, min(1.0, xp_fraction)))
        row["xp_text"].config(text=f"XP {int(round(xp_fraction * 100))}%")

    # ------------------------------------------------------------------
    # Sprites & shiny log (sandbox A4)
    # ------------------------------------------------------------------

    def _set_row_sprite(self, pokemon: "Pokemon", row: dict) -> None:
        key = "egg" if pokemon.is_egg else f"{pokemon.species_name_for_stats}|{pokemon.is_shiny}|{pokemon.is_anti_shiny}"
        if row.get("sprite_key") == key:
            return
        image = self._get_sprite_image(pokemon, key)
        row["sprite"].config(image=image if image is not None else "")
        row["sprite_key"] = key

    def _get_sprite_image(self, pokemon: "Pokemon", cache_key: str) -> "PIL.ImageTk.PhotoImage | None":
        if cache_key in self._sprite_cache:
            return self._sprite_cache[cache_key]
        try:
            from modules.runtime import get_sprites_path
            from modules.sprites import get_sprite

            path = get_sprites_path() / "pokemon" / "Egg.png" if pokemon.is_egg else get_sprite(pokemon)
            if not path.is_file():
                self._sprite_cache[cache_key] = None
                return None
            image = PIL.Image.open(path)
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            image.thumbnail((32, 32), PIL.Image.NEAREST)
            photo = PIL.ImageTk.PhotoImage(image)
        except Exception:
            self._sprite_cache[cache_key] = None
            return None
        self._sprite_cache[cache_key] = photo
        return photo

    def _refresh_shiny_log(self) -> None:
        if self._shiny_log_label is None:
            return
        try:
            phases = context.stats.get_shiny_log()[:5]
            lines = []
            for phase in phases:
                encounter = phase.shiny_encounter
                species = encounter.pokemon.species_name_for_stats if encounter is not None else "?"
                lines.append(f"✨ {species} — {phase.encounters:,} enc")
        except Exception:
            return
        if lines:
            self._shiny_log_label.config(text="\n".join(lines), foreground=COLOR_SHINY)
        else:
            self._shiny_log_label.config(text="No shinies yet — keep hunting!", foreground=COLOR_MUTED)

    def _on_tool_mousewheel(self, event) -> None:
        if not event.delta or self.frame is None:
            return
        try:
            widget = self.window.winfo_containing(event.x_root, event.y_root)
        except (KeyError, tkinter.TclError):
            return
        while widget is not None:
            if isinstance(widget, tkinter.Listbox):
                return  # the event log scrolls itself
            if widget is self._tools_container:
                self._cards_canvas.yview_scroll(int(-event.delta / 120), "units")
                return
            widget = widget.master

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
        self._refresh_sync_line()

    def _refresh_sync_line(self) -> None:
        """A8: reflect the launch-sync outcome in the Backups card (once per
        enable for the event log; label refreshed on the normal cycle)."""
        if getattr(self, "_sync_label", None) is None or context.profile is None:
            return
        try:
            from modules import cloud_sync

            status = cloud_sync.get_status(context.profile.path.name)
            if status is None or status["state"] == "disabled":
                self._sync_label.config(text="Sync: off (enable in backup.yml)", foreground=COLOR_MUTED)
                return
            state = status["state"]
            if state == "up-to-date":
                self._sync_label.config(text="Sync: up to date with the cloud", foreground=COLOR_MUTED)
            elif state == "applied":
                self._sync_label.config(text=f"Sync: cloud save applied {status['detail']}", foreground=COLOR_GOOD)
            elif state == "conflict":
                self._sync_label.config(
                    text=f"Sync CONFLICT: local kept ({status['detail']})", foreground=COLOR_WARNING
                )
                if self._sync_import_button is not None and not self._sync_import_button.winfo_ismapped():
                    self._sync_import_button.pack(fill="x", pady=(2, 2))
            elif state == "offline":
                self._sync_label.config(text="Sync: cloud unreachable (offline?)", foreground=COLOR_MUTED)
            elif state == "no-cloud":
                self._sync_label.config(text="Sync: on — first push happens when you close the bot", foreground=COLOR_MUTED)
            else:
                self._sync_label.config(text=f"Sync: {state} {status['detail']}", foreground=COLOR_WARNING)
            if not self._sync_status_logged and state in ("applied", "conflict"):
                self._sync_status_logged = True
                if state == "applied":
                    self._log_event(f"Cloud sync: newest save applied ({status['detail']})")
                else:
                    self._log_event("Cloud sync CONFLICT — local save kept; import available in Backups", highlight=True)
        except Exception:
            pass

    def _import_cloud_conflict(self) -> None:
        """A8 conflict escape hatch: cloud version -> brand-new profile."""
        if context.profile is None:
            return

        name = self._ask_text(
            "Import cloud save",
            "Name for the NEW profile that will hold the cloud version:",
        )
        if not name:
            return
        try:
            from modules import cloud_sync

            target = cloud_sync.import_cloud_as_new_profile(context.profile.path.name, name.strip())
            self._log_event(f"Cloud save imported as new profile '{target.name}' — restart to play it.")
        except Exception as error:
            self._log_event(f"Cloud import failed: {error}", highlight=True)

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
                feedback.config(text="Select a backup from the list first.", foreground=COLOR_WARNING)
                return
            entry = backups[selection[0]]
            try:
                target = backup_manager.restore_backup(entry["path"], name_variable.get().strip())
            except Exception as error:
                # ValueError carries a user-readable refusal; anything else
                # (corrupt zip, disk error) must surface here too instead of
                # dying silently in Tk's callback handler.
                feedback.config(text=str(error) or error.__class__.__name__, foreground=COLOR_WARNING)
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

        # Float above the emulator (critical in handheld fullscreen) + center.
        self._prepare_dialog(dialog)

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

    # ------------------------------------------------------------------
    # Macros (sandbox A2)
    # ------------------------------------------------------------------
    def _refresh_macro_menu(self) -> None:
        from modules.macros import list_macros

        if context.profile is None:
            return
        names = list_macros(context.profile.path)
        menu = self._macro_menu["menu"]
        menu.delete(0, "end")
        if not names:
            self._macro_variable.set("(no macros)")
            menu.add_command(label="(no macros)", command=lambda: None)
            return
        for name in names:
            menu.add_command(label=name, command=lambda n=name: self._macro_variable.set(n))
        if self._macro_variable.get() not in names:
            self._macro_variable.set(names[0])

    def _toggle_macro_recording(self) -> None:
        from modules.macros import MacroError, recorder, save_macro

        if not recorder.armed:
            if context.bot_mode != "Manual":
                self._log_event("Switch to Manual mode to record a macro.", highlight=True)
                return
            recorder.start()
            self._macro_record_button.config(text="■ Stop", foreground=COLOR_CRITICAL)
            self._log_event("Recording macro — play in Manual, then press Stop.")
            return

        macro = recorder.stop()
        self._macro_record_button.config(text="● Rec", foreground=COLOR_INK)
        if macro is None:
            self._log_event("Recording stopped — no button presses captured, nothing saved.")
            return
        name = self._ask_text(
            "Save macro",
            f"Recorded {len(macro.steps)} step(s) / {macro.total_frames} frames.\nMacro name:",
        )
        if not name:
            self._log_event("Recording discarded (no name given).")
            return
        macro.name = name
        try:
            file_path = save_macro(context.profile.path, macro)
        except MacroError as error:
            self._log_event(f"Could not save macro: {error}", highlight=True)
            return
        self._refresh_macro_menu()
        self._macro_variable.set(file_path.stem)
        self._log_event(f"Macro `{file_path.stem}` saved ({macro.total_frames} frames).")

    def _play_selected_macro(self) -> None:
        from modules.macros import list_macros, save_selection

        if context.profile is None:
            return
        selected = self._macro_variable.get()
        if selected not in list_macros(context.profile.path):
            self._log_event("No macro selected — record one first (● Rec in Manual mode).", highlight=True)
            return
        save_selection(context.profile.path, selected, self._macro_loop_variable.get())
        context.bot_mode = "Macro (Custom)"
        self._log_event(f"Playing macro `{selected}` ({'looping' if self._macro_loop_variable.get() else 'once'}).")
        self._refresh_controls()

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

    def _close_window(self) -> None:
        """A8: the stock close path ends in os._exit(0), so atexit handlers
        never run — the exit-side cloud sync MUST happen right here, after
        `emulator.shutdown()` has flushed the save to disk and before the
        process dies. Sync is config-gated and time-boxed; any failure only
        prints a warning. (Killing the console window bypasses this — that
        path only flushes the save; the next clean exit will sync it.)"""
        profile = context.profile
        if context.emulator:
            context.emulator.shutdown()
            context.emulator = None

        try:
            from modules.cloud_sync import sync_on_exit

            result = sync_on_exit(profile)
            if result is not None:
                print(f"[sync] {result}")
        except Exception as error:
            print(f"[sync] exit sync failed: {error}")

        self._on_exit()
        os._exit(0)
