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
pumped from `update()`, which the emulator calls once per frame. Every
popup is floated above the emulator and made input-modal by
`_prepare_dialog` (-topmost + lift + grab_set); this matters most in
handheld fullscreen, where a plain Toplevel would otherwise open BEHIND the
video and look like nothing happened. A grab only redirects INPUT — it does
NOT pause emulation. The Restore dialog and the species picker therefore
keep emulation running while they are open (they never call wait_window).
The text prompt (`_ask_text`, used for the macro name and the cloud-import
profile name) additionally calls `wait_window`, whose nested event loop runs
inside the frame callback, so emulation pauses until it is closed. That is
harmless by design: recording/importing has already finished before the
prompt opens.
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

# Gen-3 type colours (for the party hover tooltip's type badges). Text on a
# badge is dark or light depending on the badge's luminance.
TYPE_COLORS = {
    "Normal": "#A8A878", "Fire": "#F08030", "Water": "#6890F0", "Grass": "#78C850",
    "Electric": "#F8D030", "Ice": "#98D8D8", "Fighting": "#C03028", "Poison": "#A040A0",
    "Ground": "#E0C068", "Flying": "#A890F0", "Psychic": "#F85888", "Bug": "#A8B820",
    "Rock": "#B8A038", "Ghost": "#705898", "Dragon": "#7038F8", "Dark": "#705848",
    "Steel": "#B8B8D0", "???": "#68A090", "Fairy": "#EE99AC",
}


def _readable_text_on(hex_color: str) -> str:
    """Black or white text for legibility on a coloured badge."""
    try:
        r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
        return "#1a1a19" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#ffffff"
    except Exception:
        return "#ffffff"


def _iv_color(value: int) -> str:
    """Colour an individual IV (0-31) green→red by quality."""
    if value >= 28:
        return COLOR_GOOD
    if value >= 20:
        return "#7bbf3a"
    if value >= 10:
        return COLOR_WARNING
    return COLOR_CRITICAL


TOOL_COLUMN_WIDTH = 360
TAB_ORDER = ["Play", "Party", "Hunt", "Stats", "Cheats", "Backups"]
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
        # Desktop: the tool column can be hidden (Pokéball reopens it) so the
        # emulator can fill the window — the handheld drawer's paradigm,
        # brought to desktop. Handheld uses `_drawer_open` instead.
        self._tools_hidden = False

        # Tabbed tool column: a row of category tabs, each holding a subset
        # of the cards, so nothing needs scrolling to reach on a handheld.
        self._tab_buttons: dict = {}
        self._tab_frames: dict = {}
        self._active_tab: "str | None" = None
        self._tab_bar: "tkinter.Frame | None" = None

        # Cheat species picker (sprite dropdown)
        self._species_picker_button: "tkinter.Button | None" = None
        self._species_sprite_cache: dict = {}  # Tk needs live PhotoImage refs
        self._species_names_cache: "list | None" = None
        self._force_species_name: "str | None" = None

        # Widgets that get updated live
        self._mode_button: tkinter.Button | None = None
        self._debug_log_var: "tkinter.BooleanVar | None" = None  # Run-menu debug toggle
        self._speed_buttons: dict[int, tkinter.Button] = {}
        self._video_button: tkinter.Button | None = None
        self._audio_button: tkinter.Button | None = None
        self._coords_button: tkinter.Button | None = None
        self._coords_label: tkinter.Label | None = None
        self._show_coords: bool = False
        self._kpi_values: dict[str, tkinter.Label] = {}
        self._party_rows: list[dict] = []
        self._sprite_cache: dict = {}  # Tk needs live references to PhotoImages
        self._shiny_log_label: tkinter.Label | None = None
        self._event_list: tkinter.Listbox | None = None
        self._message_label: tkinter.Label | None = None
        self._state_label: tkinter.Label | None = None
        self._fps_label: tkinter.Label | None = None
        self._controller_label: tkinter.Label | None = None
        self._watchdog_label: tkinter.Label | None = None
        self._update_label: tkinter.Label | None = None
        self._update_notice_logged = False

        # #11 analytics (Stats tab): enc/hr trend sparkline + luck meter +
        # the pop-out sortable stats browser.
        from modules.analytics import TrendBuffer

        self._analytics_trend = TrendBuffer(capacity=120)
        self._trend_canvas: "Canvas | None" = None
        self._luck_label: "tkinter.Label | None" = None
        self._stats_browser: "tkinter.Toplevel | None" = None

        self._pokeball_button: Canvas | None = None
        self._menu_bar: Menu | None = None

        # #30(a) persistent column header (Handheld toggle always visible)
        self._column_header: "tkinter.Frame | None" = None
        self._tools_label: "tkinter.Label | None" = None
        self._hide_button: "tkinter.Button | None" = None
        self._handheld_button: "tkinter.Button | None" = None

        # #30(c) Left Party Section (strip of icons left of the video)
        self._party_strip: "tkinter.Frame | None" = None
        self._party_slots: list = []
        self._party_icon_cache: dict = {}  # keep PhotoImage refs alive
        self._current_party: list = []

        # #30(d) hover-stats tooltip (also driven by the gamepad nav, #32)
        self._party_tooltip: "tkinter.Toplevel | None" = None
        self._party_tooltip_label: "tkinter.Label | None" = None
        self._tooltip_hide_after = None

        # #32 gamepad-driven GUI navigation: when active, the controller moves
        # a focus ring across widgets instead of playing the game.
        self._gui_nav_active: bool = False
        self._focus_targets: list = []  # ordered [{"kind","widget",...}]
        self._focus_index: int = -1
        # KI-9 safety valve: master switch for controller GUI menu-control.
        # When False the gamepad NEVER drives the dashboard — it only plays the
        # game (Manual) — regardless of drawer state. Toggle via the View menu
        # or F10. Default on; flip off if GUI-nav ever misbehaves.
        self._gamepad_gui_control_enabled: bool = True

        # #31 adjustable money cheat widgets
        self._money_entry: "tkinter.Entry | None" = None
        self._money_variable: "tkinter.StringVar | None" = None
        self._money_lock_variable: "tkinter.BooleanVar | None" = None

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
        self.window.columnconfigure(0, weight=0)  # left party strip
        self.window.columnconfigure(1, weight=1)  # emulator video
        self.window.columnconfigure(2, weight=0)  # tool column

        self._build_menu_bar()
        self._build_party_strip()
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
        # Left party strip + hover tooltip are also root-window children.
        if self._party_strip is not None:
            self._party_strip.destroy()
            self._party_strip = None
        if self._party_tooltip is not None:
            self._party_tooltip.destroy()
            self._party_tooltip = None
        if self._tooltip_hide_after is not None:
            try:
                self.window.after_cancel(self._tooltip_hide_after)
            except Exception:
                pass
            self._tooltip_hide_after = None
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
        self._coords_button = None
        self._coords_label = None
        self._kpi_values = {}
        self._party_rows = []
        self._sprite_cache = {}
        self._shiny_log_label = None
        self._event_list = None
        self._message_label = None
        self._state_label = None
        self._fps_label = None
        self._controller_label = None
        self._watchdog_label = None
        self._update_label = None
        self._update_notice_logged = False  # re-show the notice if re-enabled
        self._sync_label = None
        self._sync_import_button = None
        self._sync_status_logged = False
        self._menu_bar = None
        self._debug_tabs = []
        # Tabs + species picker: drop refs so a later enable() starts clean.
        self._tab_buttons = {}
        self._tab_frames = {}
        self._active_tab = None
        self._tab_bar = None
        self._species_picker_button = None
        self._species_sprite_cache = {}
        self._force_species_name = None
        # #30/#31 widgets
        self._column_header = None
        self._tools_label = None
        self._hide_button = None
        self._handheld_button = None
        self._party_slots = []
        self._party_icon_cache = {}
        self._current_party = []
        self._tools_hidden = False
        # #32 gamepad-nav state
        self._gui_nav_active = False
        self._focus_targets = []
        self._focus_index = -1
        self._party_tooltip_label = None
        self._money_entry = None
        self._money_variable = None
        self._money_lock_variable = None
        # #23 living-dex panel widgets (cleared so a post-disable refresh no-ops)
        self._livingdex_label = None
        self._livingdex_plan_label = None
        self._livingdex_custom_button = None
        self._livingdex_pending = []
        # #11 analytics widgets
        self._trend_canvas = None
        self._luck_label = None
        if self._stats_browser is not None:
            try:
                self._stats_browser.destroy()
            except Exception:
                pass
        self._stats_browser = None
        self._analytics_trend.clear()

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

    # Menu command callbacks — shared by the Tk menu bar (desktop) AND the
    # in-tab "GAME MENU" card (#30b), so handheld can drop the menu bar
    # entirely while keeping every command reachable.
    def _menu_load_milestone_state(self) -> None:
        """User directive 2026-07-23: like Load Save State, but for the repo's story
        checkpoint library — fast test entry at any built milestone."""
        from modules.gui.milestone_window import MilestoneWindow

        MilestoneWindow(self.window)

    def _menu_load_save_state(self) -> None:
        from modules.gui.load_state_window import LoadStateWindow

        LoadStateWindow(self.window)

    def _menu_new_save_state(self) -> None:
        context.emulator.create_save_state("Manual")

    def _menu_screenshot(self) -> None:
        context.emulator.take_screenshot("manual")

    def _menu_reset(self) -> None:
        context.emulator.reset()

    def _menu_open_profile_folder(self) -> None:
        from showinfm import show_in_file_manager

        show_in_file_manager(str(context.profile.path))

    def _menu_wiki(self) -> None:
        import webbrowser

        webbrowser.open_new_tab("https://github.com/40Cakes/pokebot-gen3/tree/main/wiki")

    def _menu_commands(self) -> list:
        """(label, callback) for every stock menu command — the single source
        of truth for both the menu bar and the in-tab menu card."""
        return [
            ("Load Save State", self._menu_load_save_state),
            ("Load Milestone State", self._menu_load_milestone_state),
            ("New Save State", self._menu_new_save_state),
            ("Take Screenshot", self._menu_screenshot),
            ("Reset", self._menu_reset),
            ("Open Profile Folder", self._menu_open_profile_folder),
            ("Classic GUI", self._explain_classic_gui),
            ("Wiki", self._menu_wiki),
        ]

    def _build_menu_bar(self) -> None:
        # Same menus as the stock GUI (emulator_controls.py) so no stock
        # functionality is lost. Shown on desktop; in handheld mode the bar is
        # hidden entirely and these commands live in the Play tab's menu card.
        menu_bar = Menu(self.window)

        emulator_menu = Menu(self.window, tearoff=0)
        emulator_menu.add_command(label="Load Save State", command=self._menu_load_save_state)
        emulator_menu.add_command(label="Load Milestone State", command=self._menu_load_milestone_state)
        emulator_menu.add_command(label="New Save State", command=self._menu_new_save_state)
        emulator_menu.add_command(label="Take Screenshot", command=self._menu_screenshot)
        emulator_menu.add_separator()
        emulator_menu.add_command(label="Reset", command=self._menu_reset)

        profile_menu = Menu(self.window, tearoff=0)
        profile_menu.add_command(label="Open Profile Folder", command=self._menu_open_profile_folder)

        view_menu = Menu(self.window, tearoff=0)
        view_menu.add_command(label="Handheld Mode (F11)", command=self.toggle_handheld)
        self._gamepad_gui_control_var = tkinter.BooleanVar(value=self._gamepad_gui_control_enabled)
        view_menu.add_checkbutton(
            label="Controller GUI Control (F10)",
            variable=self._gamepad_gui_control_var,
            command=self._menu_toggle_gamepad_gui_control,
        )
        view_menu.add_command(label="Classic GUI", command=self._explain_classic_gui)

        help_menu = Menu(self.window, tearoff=0)
        help_menu.add_command(label=f"{pokebot_name} Wiki", command=self._menu_wiki)

        menu_bar.add_cascade(label="Emulator", menu=emulator_menu)
        menu_bar.add_cascade(label="Profile", menu=profile_menu)
        menu_bar.add_cascade(label="View", menu=view_menu)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        if context.debug:
            from modules.gui.debug_menu import DebugMenu

            menu_bar.add_cascade(label="Debug", menu=DebugMenu(self.window))

        self._menu_bar = menu_bar
        self.window.config(menu=menu_bar)

    def _build_menu_card(self, parent: tkinter.Widget) -> None:
        """#30b: the stock menu's commands as a grid of buttons in the Play
        tab, so handheld mode (no menu bar) keeps them one tap away."""
        card = self._card(parent, "GAME MENU")
        grid = tkinter.Frame(card, background=COLOR_CARD)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="menu")
        grid.columnconfigure(1, weight=1, uniform="menu")
        for index, (label, command) in enumerate(self._menu_commands()):
            tkinter.Button(
                grid, text=label, command=command, background=COLOR_SURFACE, foreground=COLOR_INK,
                activebackground=COLOR_ACCENT, activeforeground=COLOR_INK, relief="flat",
                font=("Segoe UI", 8), padx=4, pady=2,
            ).grid(row=index // 2, column=index % 2, sticky="ew", padx=2, pady=2)

    def _explain_classic_gui(self) -> None:
        context.message = "Restart the bot with --classic-gui to use the original interface."

    def _build_video_area(self) -> None:
        self.canvas = Canvas(self.window, background="#000000", highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky="NSWE")  # column 0 = party strip
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

        # --- persistent column header (#30a) ---
        # Always visible above the tabs, so the Handheld toggle is reachable
        # from every tab. In the handheld drawer it also carries the "TOOLS"
        # label (left) and the "Hide" button (right); on desktop only the
        # Handheld button shows (right-aligned). Layout is arranged by
        # _layout_column_header().
        self._column_header = tkinter.Frame(column, background=COLOR_SURFACE)
        self._column_header.pack(fill="x")
        self._tools_label = tkinter.Label(
            self._column_header, text="TOOLS", background=COLOR_SURFACE, foreground=COLOR_INK_2,
            font=("Segoe UI", 9, "bold"),
        )
        self._handheld_button = tkinter.Button(
            self._column_header,
            text="⛶ Handheld",
            command=self.toggle_handheld,
            background=COLOR_CARD,
            foreground=COLOR_INK_2,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            font=("Segoe UI", 8),
            padx=8,
        )
        self._hide_button = tkinter.Button(
            self._column_header,
            text="Hide",
            command=self._on_hide_clicked,
            background=COLOR_CARD,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            padx=10,
        )
        self._layout_column_header()

        # --- category tab bar: one row of buttons, each showing a subset of
        # the cards, so you don't have to scroll to find a setting (works the
        # same in the handheld drawer). Sits above the scrollable area.
        self._tab_bar = tkinter.Frame(column, background=COLOR_SURFACE)
        self._tab_bar.pack(fill="x", padx=6, pady=(6, 2))
        # Wrap tabs to two balanced rows when there are more than 4, so 6+
        # tabs stay legible at the ~360px tool-column width instead of
        # overlapping/truncating (KI-6). One row for <=4 tabs.
        tab_count = len(TAB_ORDER)
        per_row = tab_count if tab_count <= 4 else (tab_count + 1) // 2
        for col in range(per_row):
            self._tab_bar.columnconfigure(col, weight=1, uniform="tab")
        for index, tab_name in enumerate(TAB_ORDER):
            row, col = divmod(index, per_row)
            button = tkinter.Button(
                self._tab_bar,
                text=tab_name,
                command=lambda name=tab_name: self._show_tab(name),
                background=COLOR_SURFACE,
                foreground=COLOR_INK_2,
                activebackground=COLOR_ACCENT,
                activeforeground=COLOR_INK,
                relief="flat",
                font=("Segoe UI", 8, "bold"),
                padx=2,
                pady=4,
            )
            button.grid(row=row, column=col, sticky="ew", padx=1, pady=1)
            self._tab_buttons[tab_name] = button

        # --- scrollable card area (A4): all cards live inside `tools`, which
        # sits in a canvas window so the column can never clip off-screen at
        # small window heights or high DPI — desktop and handheld drawer alike.
        # With tabs, only the active tab's cards are packed, but the scroll
        # area stays as a safety net for very short windows / high DPI.
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

        # One content frame per tab; only the active one is packed (_show_tab).
        self._tab_frames = {name: tkinter.Frame(tools, background=COLOR_SURFACE) for name in TAB_ORDER}
        play_tab = self._tab_frames["Play"]
        party_tab = self._tab_frames["Party"]
        stats_tab = self._tab_frames["Stats"]
        cheats_tab = self._tab_frames["Cheats"]
        backups_tab = self._tab_frames["Backups"]

        # --- controls card ---
        controls = self._card(play_tab, "CONTROLS")

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

        # --- Show Coords (debug readout; user directive 2026-07-23) ---------------
        # A mapping aid, not a gameplay feature: when the bot misroutes, the user reads
        # the live tile + area off this line and reports it, which is far faster than
        # reconstructing a position from a log after the fact. Off by default; purely a
        # display, it never touches the emulator or the running mode.
        coords_row = tkinter.Frame(controls, background=COLOR_CARD)
        coords_row.pack(fill="x", pady=(0, 4))
        tkinter.Label(coords_row, text="Debug", width=9, anchor="w", background=COLOR_CARD, foreground=COLOR_INK_2).pack(
            side="left"
        )
        self._coords_button = tkinter.Button(
            coords_row,
            text="Show Coords",
            command=self._toggle_show_coords,
            background=COLOR_SURFACE,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            padx=8,
        )
        self._coords_button.pack(side="left", padx=1)
        self._coords_label = tkinter.Label(
            controls,
            text="",
            anchor="w",
            justify="left",
            background=COLOR_CARD,
            foreground=COLOR_INK,
            font=("Consolas", 9),
            wraplength=240,
        )
        # Packed/unpacked by the toggle so the card keeps its height when off. The
        # preference survives a GUI rebuild (handheld toggle, mode change), so re-pack
        # here when it was already on — otherwise the button would read active with no
        # readout under it.
        if self._show_coords:
            self._coords_label.pack(fill="x", pady=(0, 4))

        # (The Handheld toggle now lives in the persistent column header so it
        # is visible on every tab — see _build_tool_column / #30a.)

        # --- game menu card (#30b): stock menu commands, always in Play tab
        # so handheld mode can drop the Tk menu bar entirely. ---
        self._build_menu_card(play_tab)

        # --- macros card (sandbox A2; grouped with Controls on the Play tab) ---
        macro_card = self._card(play_tab, "MACROS")
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
        kpis = self._card(stats_tab, "STATS")
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

        # --- analytics card (#11): enc/hr trend + luck meter + browser ---
        analytics = self._card(stats_tab, "ANALYTICS")
        tkinter.Label(
            analytics, text="Encounters / hr", background=COLOR_CARD, foreground=COLOR_INK_2,
            font=("Segoe UI", 7, "bold"), anchor="w",
        ).pack(fill="x")
        self._trend_canvas = Canvas(
            analytics, height=44, background=COLOR_SURFACE, highlightthickness=0, borderwidth=0,
        )
        self._trend_canvas.pack(fill="x", pady=(2, 6))
        self._luck_label = tkinter.Label(
            analytics, text="Luck: no encounters yet.", background=COLOR_CARD, foreground=COLOR_MUTED,
            anchor="w", justify="left", wraplength=TOOL_COLUMN_WIDTH - 44, font=("Segoe UI", 8),
        )
        self._luck_label.pack(fill="x")
        tkinter.Button(
            analytics, text="Open stats browser…", command=self._open_stats_browser,
            background=COLOR_SURFACE, foreground=COLOR_INK, activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK, relief="flat", font=("Segoe UI", 9),
        ).pack(fill="x", pady=(6, 0))

        # --- party card ---
        party_card = self._card(party_tab, "PARTY")
        self._party_container = tkinter.Frame(party_card, background=COLOR_CARD)
        self._party_container.pack(fill="x")

        # --- shiny log card (sandbox A4) ---
        shiny_card = self._card(party_tab, "SHINY LOG")
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
        backup_card = self._card(backups_tab, "BACKUPS")
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

        # --- cheats card (sandbox) ---
        self._build_cheats_card(cheats_tab)

        # --- status line + message ---
        status_card = self._card(stats_tab, "STATUS")
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
        self._watchdog_label = tkinter.Label(
            status_card, text="", background=COLOR_CARD, foreground=COLOR_MUTED, anchor="w", font=("Segoe UI", 8)
        )
        self._watchdog_label.pack(fill="x")
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
        log_card = self._card(stats_tab, "EVENT LOG")
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

        # --- Hunt tab (#9) ---
        self._build_hunt_card(self._tab_frames["Hunt"])
        # --- Living Dex orchestrator (#23) ---
        self._build_living_dex_card(self._tab_frames["Hunt"])
        # --- Catch-ball allowlist (#40) ---
        self._build_catch_balls_card(self._tab_frames["Hunt"])

        # Show the default tab now that every card exists (persist=False so
        # it doesn't clobber a saved tab before _restore_ui_state reads it).
        self._show_tab(TAB_ORDER[0], persist=False)

    def _card(self, parent: tkinter.Widget, title: str, expand: bool = False) -> tkinter.Frame:
        outer = tkinter.Frame(parent, background=COLOR_SURFACE)
        outer.pack(fill="both" if expand else "x", expand=expand, padx=8, pady=(8, 0))
        card = tkinter.Frame(outer, background=COLOR_CARD, padx=8, pady=6)
        card.pack(fill="both", expand=True)
        tkinter.Label(
            card, text=title, background=COLOR_CARD, foreground=COLOR_INK_2, font=("Segoe UI", 8, "bold"), anchor="w"
        ).pack(fill="x", pady=(0, 4))
        return card

    def _show_tab(self, name: str, persist: bool = True) -> None:
        """Show one category tab's cards and hide the rest; highlight the
        active tab button. Resets the scroll position so a taller previous
        tab can't leave the new one scrolled out of view.

        `persist=False` for the initial build call, so it doesn't overwrite
        the saved tab before _restore_ui_state has had a chance to read it."""
        if name not in self._tab_frames:
            return
        for tab_name, frame in self._tab_frames.items():
            if tab_name == name:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        for tab_name, button in self._tab_buttons.items():
            active = tab_name == name
            button.config(
                background=COLOR_ACCENT if active else COLOR_SURFACE,
                foreground=COLOR_INK if active else COLOR_INK_2,
            )
        self._active_tab = name
        try:
            self._cards_canvas.update_idletasks()
            self._cards_canvas.yview_moveto(0.0)
            self._cards_canvas.configure(scrollregion=self._cards_canvas.bbox("all"))
        except tkinter.TclError:
            pass
        if persist:
            self._persist_ui_state()

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
        ball.bind("<Button-1>", lambda _event: self._on_pokeball_clicked())
        ball.configure(cursor="hand2")
        self._pokeball_button = ball
        # placed/hidden by _apply_handheld_layout

    # ------------------------------------------------------------------
    # Left Party Section (#30c) + hover stats (#30d)
    # ------------------------------------------------------------------

    _PARTY_ICON_SIZE = 84

    def _build_party_strip(self) -> None:
        """A vertical strip of 6 party icons to the left of the video (both
        desktop and handheld). Empty slot = a large Poké Ball; filled slot =
        the mon over its caught ball (ball a clear backdrop behind the mon).
        Hovering a slot shows its stats."""
        strip = tkinter.Frame(self.window, background=COLOR_SURFACE, width=self._PARTY_ICON_SIZE + 14)
        strip.grid(row=0, column=0, sticky="ns")
        strip.grid_propagate(False)
        self._party_strip = strip
        self._party_slots = []
        for index in range(6):
            slot = tkinter.Label(strip, background=COLOR_SURFACE, borderwidth=0)
            slot.pack(pady=1, padx=5)
            slot.bind("<Enter>", lambda event, i=index: self._party_hover_enter(i, event.x_root, event.y_root))
            slot.bind("<Leave>", lambda _event: self._party_hover_leave())
            self._party_slots.append(slot)
        self._refresh_party_strip()

    def _refresh_party_strip(self) -> None:
        if not self._party_slots:
            return
        party = self._current_party
        for index, slot in enumerate(self._party_slots):
            mon = party[index] if index < len(party) else None
            icon = self._party_icon(mon)
            slot.config(image=icon if icon is not None else "")
            slot.image = icon  # keep a ref (cache also holds it)

    def _party_icon(self, pokemon) -> "PIL.ImageTk.PhotoImage | None":
        if pokemon is None or getattr(pokemon, "is_empty", False):
            key = "empty"
        elif pokemon.is_egg:
            key = "egg"
        else:
            try:
                species = pokemon.species_name_for_stats
            except Exception:
                species = pokemon.name
            # The strip no longer draws the caught ball (moved to the hover
            # tooltip), so the ball is not part of the cache key.
            key = f"{species}|{bool(pokemon.is_shiny)}"
        if key in self._party_icon_cache:
            return self._party_icon_cache[key]
        photo = None
        try:
            photo = self._build_party_icon(pokemon, key)
        except Exception:
            photo = None
        self._party_icon_cache[key] = photo
        return photo

    def _build_party_icon(self, pokemon, key: str) -> "PIL.ImageTk.PhotoImage | None":
        from modules.runtime import get_sprites_path

        size = self._PARTY_ICON_SIZE
        canvas = PIL.Image.new("RGBA", (size, size), (0, 0, 0, 0))
        items_dir = get_sprites_path() / "items"

        def load(path, box) -> "PIL.Image.Image | None":
            if path is None or not path.is_file():
                return None
            image = PIL.Image.open(path)
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            image.thumbnail((box, box), PIL.Image.NEAREST)
            return image

        def paste(image, alpha_mul: float = 1.0, anchor: str = "center") -> None:
            if image is None:
                return
            if alpha_mul < 1.0:
                faded = image.split()[3].point(lambda a: int(a * alpha_mul))
                image = image.copy()
                image.putalpha(faded)
            x = (size - image.width) // 2
            y = size - image.height - 2 if anchor == "bottom" else (size - image.height) // 2
            canvas.alpha_composite(image, (x, y))

        mon_box = int(size * 0.9)  # clean, prominent mon sprite (no ball backdrop)
        if key == "empty":
            # Empty slot: a faded Poké Ball just denotes "no Pokémon here".
            paste(load(items_dir / "Poké Ball.png", int(size * 0.7)), alpha_mul=0.55)
        elif key == "egg":
            paste(load(get_sprites_path() / "pokemon" / "Egg.png", mon_box))
        else:
            try:
                from modules.sprites import get_sprite

                # Just the Pokémon, centered and large — the caught ball now
                # lives in the hover tooltip instead of behind the sprite.
                paste(load(get_sprite(pokemon), mon_box))
            except Exception:
                pass
        return PIL.ImageTk.PhotoImage(canvas)

    def _tooltip_ball_icon(self, ball_name: str) -> "PIL.ImageTk.PhotoImage | None":
        """~54px caught-ball icon for the hover tooltip (#46: ~3× the old
        18px), cached per ball name. Falls back to the plain Poké Ball if the
        asset is missing."""
        if not hasattr(self, "_tooltip_ball_cache"):
            self._tooltip_ball_cache = {}
        if ball_name in self._tooltip_ball_cache:
            return self._tooltip_ball_cache[ball_name]
        photo = None
        try:
            from modules.runtime import get_sprites_path

            items_dir = get_sprites_path() / "items"
            path = items_dir / f"{ball_name}.png"
            if not path.is_file():
                path = items_dir / "Poké Ball.png"
            if path.is_file():
                image = PIL.Image.open(path)
                if image.mode != "RGBA":
                    image = image.convert("RGBA")
                # resize (not thumbnail) so the 24px item icon UPSCALES to ~3×
                # (thumbnail only shrinks). NEAREST keeps the pixel art crisp.
                image = image.resize((54, 54), PIL.Image.NEAREST)
                photo = PIL.ImageTk.PhotoImage(image)
        except Exception:
            photo = None
        self._tooltip_ball_cache[ball_name] = photo
        return photo

    def _bind_party_row_hover(self, widget, index: int) -> None:
        """Bind hover-stats on a party-tab row and all its children (Tk
        Enter/Leave don't bubble, so every child must be bound)."""
        widget.bind("<Enter>", lambda event, i=index: self._party_hover_enter(i, event.x_root, event.y_root), add="+")
        widget.bind("<Leave>", lambda _event: self._party_hover_leave(), add="+")
        for child in widget.winfo_children():
            self._bind_party_row_hover(child, index)

    # --- hover-stats tooltip (also called by the future gamepad nav, #32) ---
    def _party_hover_enter(self, index: int, x_root: int, y_root: int) -> None:
        if self._tooltip_hide_after is not None:
            try:
                self.window.after_cancel(self._tooltip_hide_after)
            except Exception:
                pass
            self._tooltip_hide_after = None
        self._show_party_tooltip(index, x_root + 16, y_root + 10)

    def _party_hover_leave(self) -> None:
        # Debounced: moving between a row and its child widgets fires
        # Leave/Enter; a short delay (cancelled by the next Enter) avoids flicker.
        if self._tooltip_hide_after is not None:
            return
        try:
            self._tooltip_hide_after = self.window.after(120, self._do_hide_tooltip)
        except Exception:
            self._hide_party_tooltip()

    def _do_hide_tooltip(self) -> None:
        self._tooltip_hide_after = None
        self._hide_party_tooltip()

    # ------------------------------------------------------------------
    # #32 Gamepad-driven GUI navigation
    #
    # When GUI-nav is active the controller drives a focus ring across the
    # dashboard instead of playing the game (the gamepad layer suppresses
    # game input while active — see modules/gamepad.py). Activation:
    #   - Handheld: opening the Pokéball drawer turns nav ON; closing it OFF
    #     (wired in _set_drawer). Back+Start opens/closes the drawer.
    #   - Desktop: Back+Start toggles nav on/off directly.
    # Mapping (nav active): D-pad/stick = move focus, A = activate,
    # B = back/close, LB/RB = previous/next tab.
    # Every method here runs on the Tk main thread (the gamepad listener's
    # handle_frame is called on the main thread), so direct Tk calls are safe.
    # ------------------------------------------------------------------

    def set_gui_nav_active(self, active: bool) -> None:
        active = bool(active)
        if active == self._gui_nav_active:
            return
        self._gui_nav_active = active
        try:
            if active:
                self._rebuild_focus_targets()
                self._set_focus_index(0)
            else:
                self._clear_focus_highlight()
                self._hide_party_tooltip()
                self._focus_targets = []
                self._focus_index = -1
        except Exception:
            pass

    @property
    def gui_nav_active(self) -> bool:
        return self._gui_nav_active

    def gamepad_gui_nav_engaged(self) -> bool:
        """KI-9: authoritative, DERIVED answer to 'should the controller drive
        the menu right now?' — never a cached flag that can desync. The gamepad
        suppresses game input only when ALL hold: the master toggle is on, we're
        in handheld, and the drawer is actually open. The moment the drawer
        closes (or handheld exits), this is False and the controller plays the
        game again."""
        return bool(
            self._gamepad_gui_control_enabled
            and self._handheld
            and self._drawer_open
            and self._gui_nav_active
        )

    def set_gamepad_gui_control(self, enabled: bool) -> None:
        """KI-9 safety valve. Flipping this off immediately drops any active
        GUI-nav so the controller returns to the game."""
        self._gamepad_gui_control_enabled = bool(enabled)
        var = getattr(self, "_gamepad_gui_control_var", None)
        if var is not None and var.get() != self._gamepad_gui_control_enabled:
            var.set(self._gamepad_gui_control_enabled)
        if not self._gamepad_gui_control_enabled:
            self.set_gui_nav_active(False)
        state = "ON" if self._gamepad_gui_control_enabled else "OFF"
        context.message = f"Controller GUI control: {state}"

    def _menu_toggle_gamepad_gui_control(self) -> None:
        # The checkbutton has already flipped the bound var; honor its new value.
        self.set_gamepad_gui_control(self._gamepad_gui_control_var.get())

    def toggle_gamepad_gui_control(self) -> None:
        self.set_gamepad_gui_control(not self._gamepad_gui_control_enabled)

    def _collect_interactive(self, widget, out: list) -> None:
        """Recursively collect activatable widgets (buttons/checkbuttons) of a
        tab frame, in child (≈ top-to-bottom) order."""
        try:
            children = widget.winfo_children()
        except Exception:
            return
        for child in children:
            if isinstance(child, (tkinter.Button, tkinter.Checkbutton)):
                if child.winfo_exists() and str(child.cget("state")) != "disabled":
                    out.append({"kind": "button", "widget": child})
            self._collect_interactive(child, out)

    def _rebuild_focus_targets(self) -> None:
        """Focus order: persistent Handheld button → 6 left-party slots
        (controller 'hover' any mon on any tab) → the active tab's buttons."""
        targets: list = []
        if self._handheld_button is not None and self._handheld_button.winfo_exists():
            targets.append({"kind": "button", "widget": self._handheld_button})
        for index, slot in enumerate(self._party_slots):
            try:
                if slot.winfo_exists():
                    targets.append({"kind": "party", "index": index, "widget": slot})
            except Exception:
                pass
        active_frame = self._tab_frames.get(self._active_tab) if self._active_tab else None
        if active_frame is not None:
            self._collect_interactive(active_frame, targets)
        self._focus_targets = targets
        if self._focus_index >= len(targets):
            self._focus_index = len(targets) - 1

    def _clear_focus_highlight(self) -> None:
        for target in self._focus_targets:
            widget = target.get("widget")
            try:
                if widget is not None and widget.winfo_exists():
                    widget.config(highlightthickness=0)
                    if "_orig_bg" in target:
                        widget.config(background=target.pop("_orig_bg"))
            except Exception:
                pass

    def _set_focus_index(self, index: int) -> None:
        self._clear_focus_highlight()
        if not self._focus_targets:
            self._focus_index = -1
            self._hide_party_tooltip()
            return
        index = index % len(self._focus_targets)
        self._focus_index = index
        target = self._focus_targets[index]
        widget = target.get("widget")
        try:
            if widget is not None and widget.winfo_exists():
                # A thick accent ring PLUS an accent background tint, so the
                # focused widget is unmistakable on a handheld screen / from
                # across the room with a controller.
                target["_orig_bg"] = widget.cget("background")
                widget.config(
                    highlightthickness=3, highlightbackground=COLOR_ACCENT,
                    highlightcolor=COLOR_ACCENT, background=COLOR_ACCENT,
                )
        except Exception:
            pass
        # Focusing a party slot shows that mon's stats (the controller "hover").
        if target.get("kind") == "party":
            try:
                slot = target["widget"]
                x = slot.winfo_rootx() + slot.winfo_width() + 8
                y = slot.winfo_rooty()
                self._show_party_tooltip(target["index"], x, y)
            except Exception:
                pass
        else:
            self._hide_party_tooltip()

    def gui_focus_move(self, direction: str) -> None:
        """direction: 'next'/'down'/'right' → forward; 'prev'/'up'/'left' → back."""
        if not self._gui_nav_active:
            return
        if not self._focus_targets:
            self._rebuild_focus_targets()
        if not self._focus_targets:
            return
        step = -1 if direction in ("prev", "up", "left") else 1
        base = self._focus_index if self._focus_index >= 0 else 0
        self._set_focus_index(base + step)

    def gui_focus_activate(self) -> None:
        if not self._gui_nav_active or not (0 <= self._focus_index < len(self._focus_targets)):
            return
        target = self._focus_targets[self._focus_index]
        try:
            if target["kind"] == "button":
                widget = target["widget"]
                if widget.winfo_exists():
                    widget.invoke()
                    # Activating may have changed the tab/cards or opened a
                    # dialog; rebuild so focus stays valid.
                    self.window.after_idle(self._rebuild_focus_targets)
            elif target["kind"] == "party":
                # Re-show the tooltip (toggle-friendly).
                self._set_focus_index(self._focus_index)
        except Exception:
            pass

    def gui_focus_back(self) -> None:
        # Close an open picker/dialog first; else close the drawer (handheld);
        # else exit GUI-nav.
        try:
            for child in self.window.winfo_children():
                if isinstance(child, tkinter.Toplevel) and child.winfo_exists() and child is not self._party_tooltip:
                    child.destroy()
                    return
        except Exception:
            pass
        if self._handheld and self._drawer_open:
            self._set_drawer(False)
        else:
            self.set_gui_nav_active(False)

    def gui_tab_next(self) -> None:
        self._cycle_tab(1)

    def gui_tab_prev(self) -> None:
        self._cycle_tab(-1)

    def _cycle_tab(self, step: int) -> None:
        if not self._gui_nav_active or not TAB_ORDER:
            return
        try:
            current = self._active_tab if self._active_tab in TAB_ORDER else TAB_ORDER[0]
            new_tab = TAB_ORDER[(TAB_ORDER.index(current) + step) % len(TAB_ORDER)]
            self._show_tab(new_tab)
            self._rebuild_focus_targets()
            # Land focus on the first widget of the new tab (after the header
            # button + party slots) if there is one, else the header.
            first_tab_widget = 1 + len(self._party_slots)
            self._set_focus_index(first_tab_widget if first_tab_widget < len(self._focus_targets) else 0)
        except Exception:
            pass

    def _show_party_tooltip(self, index: int, x: "int | None" = None, y: "int | None" = None) -> None:
        """Show all stats for party member `index`. Index-based so the future
        gamepad-GUI navigation (#32) can show stats for the focused slot."""
        party = self._current_party
        if index < 0 or index >= len(party):
            self._hide_party_tooltip()
            return
        mon = party[index]
        if mon is None or getattr(mon, "is_empty", False):
            self._hide_party_tooltip()
            return
        try:
            if self._party_tooltip is None or not self._party_tooltip.winfo_exists():
                tip = tkinter.Toplevel(self.window)
                tip.overrideredirect(True)
                tip.attributes("-topmost", True)
                tip.configure(background=COLOR_ACCENT)  # 1px accent border
                self._party_tooltip = tip
            tip = self._party_tooltip
            for child in tip.winfo_children():
                child.destroy()
            body = tkinter.Frame(tip, background=COLOR_CARD)
            body.pack(padx=1, pady=1)
            self._build_tooltip_body(body, mon)
            tip.update_idletasks()
            if x is None:
                x = self.window.winfo_pointerx() + 16
                y = self.window.winfo_pointery() + 12
            # Keep the card on-screen (it can be tall).
            try:
                sh = self.window.winfo_screenheight()
                if int(y) + tip.winfo_height() > sh - 8:
                    y = max(8, sh - tip.winfo_height() - 8)
            except Exception:
                pass
            tip.geometry(f"+{int(x)}+{int(y)}")
            tip.deiconify()
            tip.lift()
        except tkinter.TclError:
            pass

    def _tooltip_sprite(self, mon) -> "PIL.ImageTk.PhotoImage | None":
        try:
            key = f"tip|{mon.species_name_for_stats}|{bool(mon.is_shiny)}"
        except Exception:
            key = None
        if key and key in self._party_icon_cache:
            return self._party_icon_cache[key]
        image = None
        try:
            from modules.sprites import get_sprite

            path = get_sprite(mon)
            if path and path.is_file():
                pic = PIL.Image.open(path)
                if pic.mode != "RGBA":
                    pic = pic.convert("RGBA")
                pic.thumbnail((56, 56), PIL.Image.NEAREST)
                image = PIL.ImageTk.PhotoImage(pic)
        except Exception:
            image = None
        if key:
            self._party_icon_cache[key] = image
        return image

    def _build_tooltip_body(self, parent, mon) -> None:
        """Pokémon-themed hover card: sprite + name + type badges + a
        colour-coded IV grid + nature/ability/item/HP + moves."""
        def safe(func, default="?"):
            try:
                value = func()
                return value if value is not None else default
            except Exception:
                return default

        try:
            if mon.is_egg:
                tkinter.Label(parent, text="Egg", background=COLOR_CARD, foreground=COLOR_MUTED,
                              font=("Segoe UI", 11, "bold"), padx=14, pady=10).pack()
                return
        except Exception:
            pass

        pad = 10
        header = tkinter.Frame(parent, background=COLOR_CARD)
        header.pack(fill="x", padx=pad, pady=(pad, 4))
        sprite_img = self._tooltip_sprite(mon)
        if sprite_img is not None:
            sprite_label = tkinter.Label(header, image=sprite_img, background=COLOR_CARD)
            sprite_label.image = sprite_img
            sprite_label.pack(side="left", padx=(0, 8))
        name_col = tkinter.Frame(header, background=COLOR_CARD)
        name_col.pack(side="left", anchor="w")
        is_shiny = safe(lambda: bool(mon.is_shiny), False)
        name_row = tkinter.Frame(name_col, background=COLOR_CARD)
        name_row.pack(anchor="w")
        tkinter.Label(name_row, text=safe(lambda: mon.name), background=COLOR_CARD,
                      foreground=COLOR_SHINY if is_shiny else COLOR_INK,
                      font=("Segoe UI", 13, "bold")).pack(side="left")
        if is_shiny:
            tkinter.Label(name_row, text=" ✨", background=COLOR_CARD, foreground=COLOR_SHINY,
                          font=("Segoe UI", 11)).pack(side="left")
        gender = safe(lambda: mon.gender, "")
        tkinter.Label(name_col, text=f"Lv {safe(lambda: mon.level)}    {gender}".rstrip(),
                      background=COLOR_CARD, foreground=COLOR_INK_2, font=("Segoe UI", 9)).pack(anchor="w")

        # Type badges (de-duplicated for mono-type mons).
        types = []
        try:
            for kind in mon.species.types:
                if kind.name not in types:
                    types.append(kind.name)
        except Exception:
            types = []
        if types:
            badges = tkinter.Frame(parent, background=COLOR_CARD)
            badges.pack(fill="x", padx=pad, pady=(0, 6))
            for kind in types:
                color = TYPE_COLORS.get(kind, COLOR_MUTED)
                tkinter.Label(badges, text=kind.upper(), background=color, foreground=_readable_text_on(color),
                              font=("Segoe UI", 8, "bold"), padx=8, pady=2).pack(side="left", padx=(0, 4))

        info = tkinter.Frame(parent, background=COLOR_CARD)
        info.pack(fill="x", padx=pad, pady=(0, 4))

        def info_line(text):
            tkinter.Label(info, text=text, background=COLOR_CARD, foreground=COLOR_INK_2,
                          font=("Segoe UI", 9), anchor="w", justify="left").pack(fill="x")

        info_line(f"{safe(lambda: mon.nature.name)} nature")
        info_line(f"Ability: {safe(lambda: mon.ability.name)}")
        held = safe(lambda: mon.held_item.name if mon.held_item is not None else "—", "—")
        info_line(f"Held: {held}")
        # Caught-ball row: small ball icon + name (moved here from the party strip).
        ball_name = safe(lambda: mon.poke_ball.name, "Poké Ball")
        ball_row = tkinter.Frame(info, background=COLOR_CARD)
        ball_row.pack(fill="x")
        ball_icon = self._tooltip_ball_icon(ball_name)
        if ball_icon is not None:
            icon_label = tkinter.Label(ball_row, image=ball_icon, background=COLOR_CARD)
            icon_label.image = ball_icon
            icon_label.pack(side="left", padx=(0, 4))
        tkinter.Label(ball_row, text=f"Caught in: {ball_name}", background=COLOR_CARD,
                      foreground=COLOR_INK_2, font=("Segoe UI", 9), anchor="w").pack(side="left")
        info_line(f"HP: {safe(lambda: mon.current_hp)}/{safe(lambda: mon.total_hp)}")

        try:
            ivs = mon.ivs
            iv_cells = [("HP", ivs.hp), ("Atk", ivs.attack), ("Def", ivs.defence),
                        ("SpA", ivs.special_attack), ("SpD", ivs.special_defence), ("Spe", ivs.speed)]
            tkinter.Label(parent, text="IVs", background=COLOR_CARD, foreground=COLOR_MUTED,
                          font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", padx=pad)
            grid = tkinter.Frame(parent, background=COLOR_CARD)
            grid.pack(padx=pad, pady=(1, 6))
            for i, (tag, val) in enumerate(iv_cells):
                cell = tkinter.Frame(grid, background=COLOR_SURFACE)
                cell.grid(row=i // 3, column=i % 3, padx=2, pady=2, sticky="nsew")
                tkinter.Label(cell, text=tag, background=COLOR_SURFACE, foreground=COLOR_MUTED,
                              font=("Segoe UI", 7), width=5).pack()
                tkinter.Label(cell, text=str(val), background=COLOR_SURFACE, foreground=_iv_color(val),
                              font=("Segoe UI", 11, "bold")).pack()
        except Exception:
            pass

        try:
            moves = [move.move.name for move in mon.moves if move is not None]
            if moves:
                tkinter.Label(parent, text="Moves", background=COLOR_CARD, foreground=COLOR_MUTED,
                              font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", padx=pad)
                move_box = tkinter.Frame(parent, background=COLOR_CARD)
                move_box.pack(fill="x", padx=pad, pady=(0, pad))
                for name in moves:
                    tkinter.Label(move_box, text=f"•  {name}", background=COLOR_CARD, foreground=COLOR_INK_2,
                                  font=("Segoe UI", 9), anchor="w").pack(fill="x")
        except Exception:
            pass

    def _hide_party_tooltip(self) -> None:
        if self._party_tooltip is not None:
            try:
                self._party_tooltip.withdraw()
            except tkinter.TclError:
                pass

    def _format_pokemon_stats(self, mon) -> str:
        if mon is None or getattr(mon, "is_empty", False):
            return ""

        def safe(func, default="?"):
            try:
                value = func()
                return value if value is not None else default
            except Exception:
                return default

        try:
            if mon.is_egg:
                return "Egg"
        except Exception:
            pass

        shiny = safe(lambda: " ✨" if mon.is_shiny else "", "")
        lines = [f"{safe(lambda: mon.name)}{shiny}   Lv {safe(lambda: mon.level)}"]
        gender = safe(lambda: mon.gender, "")
        lines.append(f"{safe(lambda: mon.nature.name)} nature   {gender}".rstrip())
        lines.append(f"Ability: {safe(lambda: mon.ability.name)}")
        held = safe(lambda: mon.held_item.name if mon.held_item is not None else "—", "—")
        lines.append(f"Item: {held}    Ball: {safe(lambda: mon.poke_ball.name)}")
        lines.append(f"HP: {safe(lambda: mon.current_hp)}/{safe(lambda: mon.total_hp)}")
        try:
            ivs = mon.ivs
            lines.append(
                f"IVs  HP {ivs.hp}  Atk {ivs.attack}  Def {ivs.defence}  "
                f"SpA {ivs.special_attack}  SpD {ivs.special_defence}  Spe {ivs.speed}"
            )
        except Exception:
            pass
        try:
            moves = [move.move.name for move in mon.moves if move is not None]
            if moves:
                lines.append("Moves: " + ", ".join(moves))
        except Exception:
            pass
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Handheld mode
    # ------------------------------------------------------------------

    def toggle_handheld(self) -> None:
        self._handheld = not self._handheld
        self._drawer_open = False
        # KI-9: leaving/entering handheld force-closes the drawer, so GUI-nav
        # must be cleared too — otherwise the gamepad stays stuck driving the
        # menu and can never return control to the game.
        self.set_gui_nav_active(False)
        self._apply_handheld_layout()
        self._persist_ui_state()

    def handle_hotkey(self, keysym: str) -> bool:
        """Called by PokebotDashboardGui's key handler. Returns True if handled."""
        key = keysym.lower()
        if key == "f11":
            self.toggle_handheld()
            return True
        if key == "f10":
            self.toggle_gamepad_gui_control()
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
        # #32: in handheld, the open drawer IS the gamepad-nav context — the
        # controller navigates the tools while it's open, and returns to
        # playing the game when it closes.
        if self._handheld:
            self.set_gui_nav_active(open_)

    def _on_pokeball_clicked(self) -> None:
        """The Pokéball reopens the side menu — the drawer in handheld, the
        docked tool column on desktop."""
        if self._handheld:
            self._set_drawer(True)
        else:
            self._set_tools_hidden(False)

    def _on_hide_clicked(self) -> None:
        """The "Hide" button collapses the side menu — closing the drawer in
        handheld, hiding the tool column on desktop."""
        if self._handheld:
            self._set_drawer(False)
        else:
            self._set_tools_hidden(True)

    def _set_tools_hidden(self, hidden: bool) -> None:
        """Desktop: hide/show the tool column so the emulator can fill the
        window; the Pokéball reopens it. (Handheld uses the drawer instead.)
        The Left Party strip stays visible either way."""
        self._tools_hidden = hidden
        if not self._handheld:
            self._apply_handheld_layout()
        self._persist_ui_state()

    def _apply_handheld_layout(self) -> None:
        try:
            self.window.attributes("-fullscreen", self._handheld)
        except tkinter.TclError:
            pass
        self._apply_menu_visibility()
        self._layout_column_header()
        self._layout_party_strip()

        if self._handheld:
            self.frame.grid_remove()
            if self._drawer_open:
                self.frame.place(relx=1.0, rely=0.0, relheight=1.0, anchor="ne", width=TOOL_COLUMN_WIDTH)
                self._pokeball_button.place_forget()
            else:
                self.frame.place_forget()
                self._pokeball_button.place(relx=1.0, x=-12, y=12, anchor="ne")
        else:
            # Desktop: tools docked in column 2, OR hidden (Pokéball reopens),
            # letting the video fill the freed space. Column 0 (party strip)
            # is untouched, so the Left Party stays visible either way.
            self.frame.place_forget()
            if self._tools_hidden:
                self.frame.grid_remove()
                self._pokeball_button.place(relx=1.0, x=-12, y=12, anchor="ne")
                # NB: `_pokeball_button` is a Canvas, and Canvas aliases BOTH
                # `.lift()` AND `.tkraise()` to `tag_raise` (raise a canvas ITEM,
                # needs a tag) — either errors with no args. Call the base
                # `Misc.tkraise` directly to raise the whole widget's stacking.
                tkinter.Misc.tkraise(self._pokeball_button)
            else:
                self._pokeball_button.place_forget()
                self.frame.grid(row=0, column=2, sticky="NSE")  # column 0=party, 1=video

    def _layout_column_header(self) -> None:
        """#30a: arrange the persistent header. Handheld drawer shows
        TOOLS + Handheld + Hide; desktop shows just the Handheld toggle."""
        if self._column_header is None:
            return
        for widget in (self._tools_label, self._handheld_button, self._hide_button):
            if widget is not None:
                widget.pack_forget()
        if self._handheld and self._drawer_open:
            self._tools_label.pack(side="left", padx=10, pady=6)
            self._handheld_button.pack(side="left", padx=6, pady=4)
            self._hide_button.pack(side="right", padx=10, pady=4)
            self._handheld_button.config(text="⛶ Windowed")
        else:
            # Desktop: show both the Handheld toggle AND a "Hide" that
            # collapses the tool column (Pokéball reopens it) — same paradigm
            # as the handheld drawer.
            self._tools_label.pack(side="left", padx=10, pady=6)
            self._hide_button.pack(side="right", padx=8, pady=4)
            self._handheld_button.pack(side="right", padx=6, pady=4)
            self._handheld_button.config(text="⛶ Handheld")

    def _layout_party_strip(self) -> None:
        """#30c: desktop = a grid column left of the video; handheld = an
        overlay strip on the left edge of the fullscreen video."""
        if self._party_strip is None:
            return
        if self._handheld:
            self._party_strip.grid_remove()
            self._party_strip.place(relx=0.0, rely=0.0, relheight=1.0, anchor="nw")
            # The video canvas was created AFTER the strip, so it stacks above
            # it; raise the strip (and its live contents) so the overlay is
            # actually visible over the fullscreen video.
            self._party_strip.lift()
        else:
            self._party_strip.place_forget()
            self._party_strip.grid(row=0, column=0, sticky="ns")

    def _apply_menu_visibility(self) -> None:
        """#30b: in handheld mode the Tk menu bar is hidden ENTIRELY (even
        with the drawer open) — the menu's commands live in the Play tab's
        GAME MENU card instead. Desktop always shows the bar. Applied AFTER
        the fullscreen toggle: on Windows, toggling fullscreen recreates the
        native window, so the menu must be (re)asserted on the new hwnd."""
        if self._menu_bar is None:
            return
        try:
            self.window.config(menu=self._menu_bar if not self._handheld else "")
        except tkinter.TclError:
            pass

    def _build_cheats_card(self, tools: tkinter.Widget) -> None:
        """CHEATS card: one-shot action buttons + persistent toggles that
        modify the live game via modules/game_cheats.py. See CHEATS-DESIGN.md."""
        from modules.game_cheats import cheat_manager

        try:
            cheat_manager.load_config()
        except Exception:
            pass

        card = self._card(tools, "CHEATS")
        tkinter.Label(
            card, text="⚠ Modifies your live game — back up first.",
            background=COLOR_CARD, foreground=COLOR_WARNING, anchor="w",
            font=("Segoe UI", 8), wraplength=TOOL_COLUMN_WIDTH - 40, justify="left",
        ).pack(fill="x", pady=(0, 4))

        def run_action(method_name: str, *args) -> None:
            try:
                message = getattr(cheat_manager, method_name)(*args)
            except Exception as error:  # defensive: the manager already guards, but never let the GUI die
                message = f"Cheat failed: {error}"
            self._log_event(f"Cheat: {message}")

        def small_button(parent: tkinter.Widget, text: str, command) -> tkinter.Button:
            return tkinter.Button(
                parent, text=text, command=command, background=COLOR_SURFACE, foreground=COLOR_INK,
                activebackground=COLOR_ACCENT, activeforeground=COLOR_INK, relief="flat",
                font=("Segoe UI", 8), padx=4, pady=2,
            )

        actions = [
            ("Heal party", lambda: run_action("heal_party")),
            ("Max level", lambda: run_action("max_level")),
            ("Perfect IVs", lambda: run_action("perfect_ivs")),
            ("Max friendship", lambda: run_action("max_friendship")),
            ("Max money", lambda: run_action("max_money")),
            ("Item pack", lambda: run_action("give_item_pack")),
            ("Max Poké Balls", lambda: run_action("max_poke_balls")),
            ("99× Rare Candy", lambda: run_action("give_item", "Rare Candy", 99)),
        ]
        grid = tkinter.Frame(card, background=COLOR_CARD)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="cheat")
        grid.columnconfigure(1, weight=1, uniform="cheat")
        for index, (text, command) in enumerate(actions):
            small_button(grid, text, command).grid(row=index // 2, column=index % 2, sticky="ew", padx=2, pady=2)

        def toggle_checkbox(parent: tkinter.Widget, text: str, key: str) -> None:
            variable = tkinter.BooleanVar(value=bool(cheat_manager.get(key)))

            def on_change() -> None:
                cheat_manager.set_toggle(key, variable.get())

            tkinter.Checkbutton(
                parent, text=text, variable=variable, command=on_change,
                background=COLOR_CARD, foreground=COLOR_INK_2, selectcolor=COLOR_SURFACE,
                activebackground=COLOR_CARD, activeforeground=COLOR_INK, anchor="w",
                font=("Segoe UI", 8), highlightthickness=0, borderwidth=0,
            ).pack(fill="x", pady=(4, 0) if key == "infinite_money" else 0)

        toggle_checkbox(card, "Infinite money", "infinite_money")

        # Adjustable money (#31): field defaults to current money; "Set" applies
        # it once; "Lock" freezes the game at the typed value every tick.
        money_row = tkinter.Frame(card, background=COLOR_CARD)
        money_row.pack(fill="x", pady=(2, 0))
        tkinter.Label(
            money_row, text="Money", background=COLOR_CARD, foreground=COLOR_INK_2, font=("Segoe UI", 8)
        ).pack(side="left")
        self._money_variable = tkinter.StringVar()
        self._money_entry = tkinter.Entry(
            money_row, textvariable=self._money_variable, background=COLOR_SURFACE, foreground=COLOR_INK,
            insertbackground=COLOR_INK, relief="flat", font=("Segoe UI", 8), width=8,
        )
        self._money_entry.pack(side="left", padx=(4, 4))

        def set_money_now() -> None:
            run_action("set_money", self._money_variable.get().strip())

        small_button(money_row, "Set", set_money_now).pack(side="left", padx=(0, 6))
        self._money_lock_variable = tkinter.BooleanVar(value=bool(cheat_manager.get("lock_money")))

        def on_money_lock() -> None:
            locked = self._money_lock_variable.get()
            if locked:
                cheat_manager.set_toggle("locked_money_value", self._money_variable.get().strip())
            cheat_manager.set_toggle("lock_money", locked)
            self._log_event("Money lock " + (f"ON @ {self._money_variable.get().strip()}" if locked else "OFF"))

        tkinter.Checkbutton(
            money_row, text="Lock", variable=self._money_lock_variable, command=on_money_lock,
            background=COLOR_CARD, foreground=COLOR_INK_2, selectcolor=COLOR_SURFACE,
            activebackground=COLOR_CARD, activeforeground=COLOR_INK, font=("Segoe UI", 8),
            highlightthickness=0, borderwidth=0,
        ).pack(side="left")

        initial_money = cheat_manager.get_current_money()
        if initial_money is None:
            initial_money = cheat_manager.get("locked_money_value") or ""
        self._money_variable.set(str(initial_money))

        toggle_checkbox(card, "Auto-heal party (overworld)", "auto_heal_party")
        toggle_checkbox(card, "Force wild species", "force_wild_species")

        force_row = tkinter.Frame(card, background=COLOR_CARD)
        force_row.pack(fill="x")
        level_variable = tkinter.StringVar(value=str(cheat_manager.get("force_wild_species_level")))

        def commit_level(*_event) -> None:
            cheat_manager.set_toggle("force_wild_species_level", level_variable.get().strip())

        # Sprite dropdown (replaces the old free-text species field): a button
        # showing the selected species' sprite + name that opens a searchable,
        # sprite-illustrated picker (_open_species_picker).
        self._force_species_name = str(cheat_manager.get("force_wild_species_name"))
        self._species_picker_button = tkinter.Button(
            force_row,
            text=f" {self._force_species_name} ▾",
            compound="left",
            command=self._open_species_picker,
            background=COLOR_SURFACE,
            foreground=COLOR_INK,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK,
            relief="flat",
            font=("Segoe UI", 8),
            anchor="w",
            padx=4,
        )
        self._species_picker_button.pack(side="left", padx=(18, 4))
        self._update_species_picker_button()
        tkinter.Label(
            force_row, text="Lv", background=COLOR_CARD, foreground=COLOR_MUTED, font=("Segoe UI", 8)
        ).pack(side="left")
        level_entry = tkinter.Entry(
            force_row, textvariable=level_variable, background=COLOR_SURFACE, foreground=COLOR_INK,
            insertbackground=COLOR_INK, relief="flat", font=("Segoe UI", 8), width=4,
        )
        level_entry.pack(side="left", padx=(2, 0))
        level_entry.bind("<FocusOut>", commit_level)
        level_entry.bind("<Return>", commit_level)

        toggle_checkbox(card, "Guaranteed shiny wild", "guaranteed_shiny_wild")

    # ------------------------------------------------------------------
    # Cheat species picker (sprite dropdown)
    # ------------------------------------------------------------------

    def _all_species_names(self) -> list:
        """All selectable species names (skips the index-0 '??????????'
        placeholder). Cached; sourced from the bot's own species data."""
        if self._species_names_cache is None:
            try:
                from modules.pokemon import _species_by_index

                self._species_names_cache = [
                    species.name
                    for species in _species_by_index
                    if species and species.name and not species.name.startswith("?")
                ]
            except Exception:
                self._species_names_cache = []
        return self._species_names_cache

    def _get_species_sprite(self, species_name: str, shiny: bool = False, size: int = 20):
        """A cached ~size-px PhotoImage of a species' sprite (shiny variant if
        requested). Returns None if the sprite is missing. Tk needs the
        reference kept alive, so the cache holds it."""
        cache_key = f"{species_name}|{shiny}|{size}"
        if cache_key in self._species_sprite_cache:
            return self._species_sprite_cache[cache_key]
        photo = None
        try:
            from modules.pokemon import get_species_by_name
            from modules.sprites import get_regular_sprite, get_shiny_sprite

            species = get_species_by_name(species_name)
            path = get_shiny_sprite(species) if shiny else get_regular_sprite(species)
            if path.is_file():
                image = PIL.Image.open(path)
                if image.mode != "RGBA":
                    image = image.convert("RGBA")
                image.thumbnail((size, size), PIL.Image.NEAREST)
                photo = PIL.ImageTk.PhotoImage(image)
        except Exception:
            photo = None
        self._species_sprite_cache[cache_key] = photo
        return photo

    def _force_species_is_shiny(self) -> bool:
        try:
            from modules.game_cheats import cheat_manager

            return bool(cheat_manager.get("guaranteed_shiny_wild"))
        except Exception:
            return False

    def _update_species_picker_button(self) -> None:
        if self._species_picker_button is None:
            return
        name = self._force_species_name or "Bulbasaur"
        image = self._get_species_sprite(name, shiny=self._force_species_is_shiny(), size=20)
        self._species_picker_button.config(
            text=f" {name} ▾", image=image if image is not None else "", compound="left"
        )
        # Belt-and-suspenders ref (the cache already holds it).
        self._species_picker_button.image = image

    def _set_force_species(self, name: str) -> None:
        try:
            from modules.game_cheats import cheat_manager

            cheat_manager.set_toggle("force_wild_species_name", name)
        except Exception:
            pass
        self._force_species_name = name
        self._update_species_picker_button()

    def _ball_icon(self, path) -> "PIL.ImageTk.PhotoImage | None":
        cache = getattr(self, "_ball_icon_cache", None)
        if cache is None:
            cache = self._ball_icon_cache = {}
        key = str(path)
        if key in cache:
            return cache[key]
        icon = None
        try:
            if path.is_file():
                image = PIL.Image.open(path)
                if image.mode != "RGBA":
                    image = image.convert("RGBA")
                image.thumbnail((18, 18), PIL.Image.NEAREST)
                icon = PIL.ImageTk.PhotoImage(image)
        except Exception:
            icon = None
        cache[key] = icon
        return icon

    def _build_catch_balls_card(self, parent: tkinter.Widget) -> None:
        """#40: choose which Poké Balls the bot may throw when catching."""
        from modules.catch_balls import ALL_BALLS, allowed_ball_names, set_allowed_ball_names
        from modules.runtime import get_sprites_path

        card = self._card(parent, "CATCH BALLS")
        tkinter.Label(
            card, text="Balls the bot may use for catching (unchecked = never thrown; protects your Master Ball).",
            background=COLOR_CARD, foreground=COLOR_MUTED, anchor="w", wraplength=320, font=("Segoe UI", 8),
        ).pack(fill="x", pady=(0, 4))

        items_dir = get_sprites_path() / "items"
        allowed = allowed_ball_names()
        self._catch_ball_vars = {}
        grid = tkinter.Frame(card, background=COLOR_CARD)
        grid.pack(fill="x")

        def save() -> None:
            names = [ball for ball, var in self._catch_ball_vars.items() if var.get()]
            set_allowed_ball_names(names)
            self._log_event(f"Catch balls updated ({len(names)} allowed).")

        for i, ball in enumerate(ALL_BALLS):
            var = tkinter.BooleanVar(value=(ball in allowed))
            self._catch_ball_vars[ball] = var
            icon = self._ball_icon(items_dir / f"{ball}.png")
            checkbox = tkinter.Checkbutton(
                grid, text=f" {ball}", variable=var, command=save, image=icon, compound="left",
                background=COLOR_CARD, foreground=COLOR_INK, selectcolor=COLOR_SURFACE,
                activebackground=COLOR_CARD, activeforeground=COLOR_INK, font=("Segoe UI", 8), anchor="w",
            )
            checkbox.image = icon
            checkbox.grid(row=i // 2, column=i % 2, sticky="w", padx=2, pady=1)

    def _build_hunt_card(self, parent: tkinter.Widget) -> None:
        """Hunt Planner (#9): pick a target → ranked wild locations + the
        recommended bot mode, one click to set that mode."""
        card = self._card(parent, "HUNT PLANNER")
        tkinter.Label(
            card, text="Pick a target — see where it's found and the mode to use.",
            background=COLOR_CARD, foreground=COLOR_MUTED, anchor="w", wraplength=320, font=("Segoe UI", 8),
        ).pack(fill="x", pady=(0, 4))
        self._hunt_target_button = tkinter.Button(
            card, text="Choose target ▾",
            command=lambda: self._open_species_picker(on_choose=self._plan_hunt, shiny=False),
            background=COLOR_SURFACE, foreground=COLOR_INK, activebackground=COLOR_ACCENT,
            activeforeground=COLOR_INK, relief="flat", anchor="w", padx=8,
        )
        self._hunt_target_button.pack(fill="x")
        self._hunt_results = tkinter.Frame(card, background=COLOR_CARD)
        self._hunt_results.pack(fill="x", pady=(6, 0))
        tkinter.Label(
            self._hunt_results, text="No target selected.",
            background=COLOR_CARD, foreground=COLOR_MUTED, anchor="w",
        ).pack(fill="x")

    def _plan_hunt(self, species_name: str) -> None:
        self._hunt_species = species_name
        try:
            self._hunt_target_button.config(text=f"{species_name} ▾")
            for widget in self._hunt_results.winfo_children():
                widget.destroy()
        except tkinter.TclError:
            return
        try:
            from modules import encounter_index
            from modules.modes import get_bot_mode_names

            try:
                modes = get_bot_mode_names()
            except Exception:
                modes = []
            locations = encounter_index.locations_for_species(species_name)
        except Exception as error:
            tkinter.Label(
                self._hunt_results, text=f"Could not load encounter data: {error}",
                background=COLOR_CARD, foreground=COLOR_WARNING, anchor="w", wraplength=320,
            ).pack(fill="x")
            return
        if not locations:
            tkinter.Label(
                self._hunt_results,
                text=f"{species_name}: no wild locations (legendary / gift / evolve-only).",
                background=COLOR_CARD, foreground=COLOR_INK_2, anchor="w", wraplength=320,
            ).pack(fill="x")
            return
        for loc in locations[:12]:
            mode = encounter_index.recommended_mode_for_method(loc["method"], modes)
            level = f"Lv {loc['min_level']}" + ("" if loc["min_level"] == loc["max_level"] else f"-{loc['max_level']}")
            row = tkinter.Frame(self._hunt_results, background=COLOR_SURFACE, padx=6, pady=3)
            row.pack(fill="x", pady=1)
            tkinter.Label(
                row, text=loc["map_name"], background=COLOR_SURFACE, foreground=COLOR_INK,
                anchor="w", font=("Segoe UI", 9, "bold"),
            ).pack(fill="x")
            bottom = tkinter.Frame(row, background=COLOR_SURFACE)
            bottom.pack(fill="x")
            tkinter.Label(
                bottom, text=f"{loc['method']} · {loc['rate']}% · {level} · {mode}",
                background=COLOR_SURFACE, foreground=COLOR_INK_2, anchor="w", font=("Segoe UI", 8),
            ).pack(side="left")
            tkinter.Button(
                bottom, text="Hunt", command=lambda l=loc: self._start_hunt(l),
                background=COLOR_ACCENT, foreground=COLOR_INK, relief="flat", font=("Segoe UI", 8), padx=8,
            ).pack(side="right")

    def _start_hunt(self, location: dict) -> None:
        # v2: one click = travel to the encounter tile + hunt. We resolve a
        # representative tile now (reads the target map's tiles from the ROM),
        # store the selection, then switch to the "Hunt (Custom)" mode which
        # walks there via global navigation and hunts. Falls back gracefully
        # if no tile can be auto-found.
        try:
            from modules import encounter_index

            method = location["method"]
            map_key = tuple(location["map"])
            map_name = location["map_name"]
            species = getattr(self, "_hunt_species", None) or "target"
            try:
                tile = encounter_index.find_encounter_tile(map_key, method)
            except Exception:
                tile = None
            encounter_index.set_hunt_target(
                {
                    "species": species,
                    "map": [map_key[0], map_key[1]],
                    "map_name": map_name,
                    "method": method,
                    "tile": list(tile) if tile else None,
                }
            )
            context.bot_mode = "Hunt (Custom)"
            self._refresh_controls()
            if tile:
                self._log_event(f"Hunt: travelling to {map_name} ({method}) to hunt {species}.")
            else:
                self._log_event(
                    f"Hunt: set target {species} on {map_name}, but couldn't auto-find a "
                    f"{method} tile — walk to the encounter area, then it'll hunt."
                )
        except Exception as error:
            self._log_event(f"Could not start hunt: {error}", highlight=True)

    def _build_living_dex_card(self, parent: tkinter.Widget) -> None:
        """Living Dex orchestrator (#23): run through a target list, catching
        the first of each species, autonomously."""
        card = self._card(parent, "LIVING DEX")
        self._livingdex_pending: list = []
        self._livingdex_label = tkinter.Label(
            card, text="No run.", background=COLOR_CARD, foreground=COLOR_INK_2,
            anchor="w", justify="left", wraplength=300, font=("Segoe UI", 9),
        )
        self._livingdex_label.pack(fill="x")

        # #41/#42: how the remaining dex is obtained + what the player can do now.
        self._livingdex_plan_label = tkinter.Label(
            card, text="", background=COLOR_CARD, foreground=COLOR_MUTED,
            anchor="w", justify="left", wraplength=300, font=("Segoe UI", 8),
        )
        self._livingdex_plan_label.pack(fill="x", pady=(2, 0))

        tkinter.Button(
            card, text="Start — all uncaught wild", command=self._livingdex_start_all,
            background=COLOR_ACCENT, foreground=COLOR_INK, activebackground=COLOR_ACCENT,
            relief="flat", font=("Segoe UI", 9),
        ).pack(fill="x", pady=(6, 2))

        custom_row = tkinter.Frame(card, background=COLOR_CARD)
        custom_row.pack(fill="x")
        tkinter.Button(
            custom_row, text="＋ Add species", command=self._livingdex_add_species,
            background=COLOR_SURFACE, foreground=COLOR_INK, relief="flat", font=("Segoe UI", 9),
        ).pack(side="left", fill="x", expand=True, padx=(0, 3))
        self._livingdex_custom_button = tkinter.Button(
            custom_row, text="Start custom (0)", command=self._livingdex_start_custom,
            background=COLOR_SURFACE, foreground=COLOR_MUTED, relief="flat", font=("Segoe UI", 9),
        )
        self._livingdex_custom_button.pack(side="left", fill="x", expand=True)

        tkinter.Button(
            card, text="Stop & clear run", command=self._livingdex_stop,
            background=COLOR_SURFACE, foreground=COLOR_INK_2, relief="flat", font=("Segoe UI", 9),
        ).pack(fill="x", pady=(2, 0))

    def _livingdex_add_species(self) -> None:
        def _add(name: str) -> None:
            if name not in self._livingdex_pending:
                self._livingdex_pending.append(name)
            self._livingdex_custom_button.config(
                text=f"Start custom ({len(self._livingdex_pending)})",
                foreground=COLOR_INK if self._livingdex_pending else COLOR_MUTED,
            )
            self._log_event(f"Living Dex custom list: {', '.join(self._livingdex_pending)}")

        self._open_species_picker(on_choose=_add, shiny=False)

    def _livingdex_start_all(self) -> None:
        self._livingdex_begin(explicit_names=None)

    def _livingdex_start_custom(self) -> None:
        if not self._livingdex_pending:
            self._log_event("Living Dex: add at least one species first.")
            return
        self._livingdex_begin(explicit_names=list(self._livingdex_pending))

    def _livingdex_begin(self, explicit_names: "list | None") -> None:
        try:
            from modules import living_dex

            run = living_dex.derive_targets(explicit_names=explicit_names)
            if not run.get("targets"):
                self._log_event("Living Dex: nothing to catch (all owned, or none are wild-catchable).")
                return
            living_dex.save_run(run)
            context.bot_mode = "Living Dex (Custom)"
            self._refresh_controls()
            skipped = f" ({len(run['skipped'])} skipped)" if run.get("skipped") else ""
            self._log_event(f"Living Dex started: {len(run['targets'])} targets{skipped}.")
        except Exception as error:
            self._log_event(f"Could not start Living Dex: {error}", highlight=True)

    def _livingdex_stop(self) -> None:
        try:
            from modules import living_dex

            living_dex.clear_run()
            self._livingdex_pending = []
            if hasattr(self, "_livingdex_custom_button") and self._livingdex_custom_button.winfo_exists():
                self._livingdex_custom_button.config(text="Start custom (0)", foreground=COLOR_MUTED)
            if context.bot_mode == "Living Dex (Custom)":
                context.set_manual_mode()
                self._refresh_controls()
            self._log_event("Living Dex run cleared.")
        except Exception as error:
            self._log_event(f"Could not stop Living Dex: {error}", highlight=True)

    def _refresh_living_dex(self) -> None:
        # The obtainability/capability line is independent of whether a run is
        # configured, so refresh it always.
        self._refresh_living_dex_plan()
        label = getattr(self, "_livingdex_label", None)
        if label is None or not label.winfo_exists():
            return
        try:
            from modules import living_dex
            from modules.pokemon import get_species_by_index

            run = living_dex.load_run()
            if run is None:
                label.config(text="No run.")
                return
            done, total = living_dex.progress(run)
            nxt = living_dex.next_target_index(run)
            if nxt is None:
                label.config(text=f"Complete — {done}/{total} owned.")
                return
            try:
                name = get_species_by_index(nxt).name
            except Exception:
                name = f"#{nxt}"
            label.config(text=f"{done}/{total} owned · next: {name}")
        except Exception:
            pass

    def _refresh_living_dex_plan(self) -> None:
        """#41/#42: obtainability breakdown of the uncaught dex + the player's
        current capabilities (what field moves / rods / badges they have)."""
        label = getattr(self, "_livingdex_plan_label", None)
        if label is None or not label.winfo_exists():
            return
        try:
            from modules import living_dex, capabilities

            breakdown = living_dex.obtainability_breakdown()
            caps = capabilities.capability_report()
            have = []
            if caps.get("surf"):
                have.append("Surf")
            for rod, key in (("Old Rod", "old_rod"), ("Good Rod", "good_rod"), ("Super Rod", "super_rod")):
                if caps.get(key):
                    have.append(rod)
            if caps.get("rock_smash"):
                have.append("Rock Smash")
            have_text = ", ".join(have) if have else "none yet"
            cats = breakdown.get("categories", {})
            dens = breakdown.get("denominators", {})

            def _n(kind):
                return len(cats.get(kind, ()))

            gift_static = _n("gift") + _n("static") + _n("roamer")
            trade_event = _n("ingame_trade") + _n("event") + _n("unobtainable")
            owned = dens.get("owned", 0)
            obtainable = dens.get("obtainable_in_emerald", 0)
            owned_obtainable = dens.get("owned_obtainable", 0)
            label.config(
                text=(
                    f"Owned: {owned}/386 National Dex · {owned_obtainable}/{obtainable} obtainable in Emerald\n"
                    f"Uncaught: {len(breakdown['wild'])} wild · {len(breakdown['evolution'])} evolve · "
                    f"{gift_static} gift/static/roam · {trade_event} trade/event/blocked\n"
                    f"You can use: {have_text}"
                )
            )
        except Exception:
            try:
                label.config(text="")
            except Exception:
                pass

    def _open_species_picker(self, on_choose=None, shiny: "bool | None" = None) -> None:
        """Searchable, sprite-illustrated species dropdown. Type to filter
        (handy across ~400 species); click a row to select. Floats above the
        emulator in handheld fullscreen via _prepare_dialog.

        on_choose(name) is called with the chosen species (default: set the
        force-wild-species cheat). Reused by the Hunt tab (#9)."""
        dialog = tkinter.Toplevel(self.window)
        dialog.title("Choose a species")
        dialog.configure(background=COLOR_SURFACE)
        dialog.geometry("300x470")

        if shiny is None:
            shiny = self._force_species_is_shiny()

        filter_variable = tkinter.StringVar()
        filter_entry = tkinter.Entry(
            dialog, textvariable=filter_variable, background=COLOR_CARD, foreground=COLOR_INK,
            insertbackground=COLOR_INK, relief="flat", font=("Segoe UI", 11),
        )
        filter_entry.pack(fill="x", padx=8, pady=8, ipady=4)

        list_area = tkinter.Frame(dialog, background=COLOR_SURFACE)
        list_area.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        list_canvas = Canvas(list_area, background=COLOR_SURFACE, highlightthickness=0, borderwidth=0)
        scrollbar = tkinter.Scrollbar(list_area, orient="vertical", command=list_canvas.yview, width=10)
        scrollbar.pack(side="right", fill="y")
        list_canvas.pack(side="left", fill="both", expand=True)
        rows_frame = tkinter.Frame(list_canvas, background=COLOR_SURFACE)
        rows_window = list_canvas.create_window((0, 0), window=rows_frame, anchor="nw")
        list_canvas.configure(yscrollcommand=scrollbar.set)
        rows_frame.bind(
            "<Configure>", lambda _event: list_canvas.configure(scrollregion=list_canvas.bbox("all"))
        )
        list_canvas.bind(
            "<Configure>", lambda event: list_canvas.itemconfigure(rows_window, width=event.width)
        )
        # This picker is modal (grab_set via _prepare_dialog), so route the
        # wheel straight to its own canvas; the global tool-column wheel
        # handler no-ops here (pointer isn't over the tool container).
        dialog.bind("<MouseWheel>", lambda event: (list_canvas.yview_scroll(int(-event.delta / 120), "units"), "break")[1])

        def choose(name: str) -> None:
            (on_choose or self._set_force_species)(name)
            dialog.destroy()

        # Show the FULL species list (scrollable) by default; typing filters
        # it. Every row loads a sprite, but sprites are cached after first
        # open, so the whole list stays scrollable and responsive.
        def render(*_args) -> None:
            for widget in rows_frame.winfo_children():
                widget.destroy()
            needle = filter_variable.get().strip().lower()
            names = [n for n in self._all_species_names() if needle in n.lower()] if needle else self._all_species_names()
            for name in names:
                image = self._get_species_sprite(name, shiny=shiny, size=22)
                row_button = tkinter.Button(
                    rows_frame,
                    text=f"  {name}",
                    image=image if image is not None else "",
                    compound="left",
                    anchor="w",
                    background=COLOR_SURFACE,
                    foreground=COLOR_INK,
                    activebackground=COLOR_ACCENT,
                    activeforeground=COLOR_INK,
                    relief="flat",
                    font=("Segoe UI", 9),
                    command=lambda n=name: choose(n),
                )
                row_button.image = image
                row_button.pack(fill="x", pady=1)
            if not names:
                tkinter.Label(
                    rows_frame, text="No match.", background=COLOR_SURFACE, foreground=COLOR_MUTED, anchor="w",
                ).pack(fill="x", pady=4)
            list_canvas.yview_moveto(0.0)

        filter_variable.trace_add("write", render)
        render()
        self._prepare_dialog(dialog)
        filter_entry.focus_set()

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
            state_file.write_text(
                json.dumps(
                    {
                        "handheld": self._handheld,
                        "active_tab": self._active_tab,
                        "tools_hidden": self._tools_hidden,
                    }
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _restore_ui_state(self) -> None:
        try:
            state_file = context.profile.path / UI_STATE_FILE
            if state_file.is_file():
                state = json.loads(state_file.read_text(encoding="utf-8"))
                # Apply the saved handheld flag BEFORE _show_tab: _show_tab
                # persists the UI state, and if _handheld were still False at
                # that point it would clobber a saved handheld=True back to
                # False on disk (lost on the next launch). Set the flag first
                # so the persist inside _show_tab writes the correct value.
                if state.get("handheld"):
                    self._handheld = True
                if state.get("tools_hidden"):
                    self._tools_hidden = True
                tab = state.get("active_tab")
                if tab in self._tab_frames:
                    self._show_tab(tab)
                if self._handheld or self._tools_hidden:
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
        self._refresh_coords()
        self._refresh_party()
        if time.monotonic() - self._last_kpi_refresh >= KPI_REFRESH_SECONDS:
            self._refresh_kpis()
            self._refresh_backup_label()
            self._refresh_shiny_log()
            self._refresh_money_field()
            self._refresh_living_dex()
            self._refresh_analytics()

    def _refresh_money_field(self) -> None:
        """#31: keep the money field showing the character's current money —
        unless it is locked (show the locked value) or being edited."""
        if self._money_entry is None or self._money_variable is None:
            return
        try:
            from modules.game_cheats import cheat_manager

            if cheat_manager.get("lock_money"):
                return
            if self.window.focus_get() is self._money_entry:
                return  # don't clobber while the user is typing
            current = cheat_manager.get_current_money()
            if current is not None:
                self._money_variable.set(str(current))
        except Exception:
            pass

    def _refresh_controls(self) -> None:
        if self._mode_button is None:
            return
        self._mode_button.config(text=f"{context.bot_mode} ▾")
        for speed, button in self._speed_buttons.items():
            active = context.emulation_speed == speed
            button.config(background=COLOR_ACCENT if active else COLOR_SURFACE)
        self._video_button.config(background=COLOR_ACCENT if context.video else COLOR_SURFACE)
        self._audio_button.config(background=COLOR_ACCENT if context.audio else COLOR_SURFACE)
        if self._coords_button is not None:
            self._coords_button.config(background=COLOR_ACCENT if self._show_coords else COLOR_SURFACE)

    def _toggle_show_coords(self) -> None:
        """Show Coords (user directive 2026-07-23): a debug readout of the player's live
        tile and area, for reporting better pathing coordinates back into development.

        Display only — it reads state and never writes, so it is safe to flip at any
        time, including mid-run."""
        self._show_coords = not self._show_coords
        if self._coords_label is not None:
            if self._show_coords:
                self._coords_label.pack(fill="x", pady=(0, 4))
            else:
                self._coords_label.pack_forget()
        self._refresh_controls()
        self._refresh_coords()

    def _refresh_coords(self) -> None:
        """Update the Show Coords readout: local tile, map name, map group/number, and
        facing. Every read is guarded — this runs on the GUI tick, including while the
        emulator is between maps or on the title screen, where any of it can be absent.
        A debug display must never be able to take the GUI down."""
        if not self._show_coords or self._coords_label is None:
            return
        try:
            from modules.map import get_map_data_for_current_position
            from modules.player import get_player_avatar

            avatar = get_player_avatar()
            x, y = avatar.local_coordinates
            group, number = avatar.map_group_and_number
            try:
                area = get_map_data_for_current_position().map_name
            except Exception:
                area = "?"
            try:
                facing = str(avatar.facing_direction)
            except Exception:
                facing = "?"
            text = (
                f"({x}, {y})  {area}" + "\n" + f"map ({group}, {number})   facing {facing}"
            )
        except Exception:
            # No avatar yet (title screen, mid-warp, no save loaded) — say so plainly
            # rather than showing a stale position the user might report as current.
            text = "(no player position available)"
        self._coords_label.config(text=text)

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

        if getattr(self, "_watchdog_label", None) is not None:
            try:
                from modules.watchdog import watchdog

                line = watchdog.get_status_line()
                self._watchdog_label.config(
                    text=line,
                    foreground=COLOR_CRITICAL if "FAULT" in line else COLOR_MUTED,
                )
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

    # ------------------------------------------------------------------
    # Analytics (#11): enc/hr trend sparkline + luck meter + stats browser
    # ------------------------------------------------------------------
    def _refresh_analytics(self) -> None:
        if self._trend_canvas is None or not self._trend_canvas.winfo_exists():
            return
        try:
            from modules.analytics import luck_meter

            # Sample the current enc/hr into the trend ring buffer.
            rate = int(getattr(context.stats, "encounter_rate", 0) or 0)
            self._analytics_trend.add(rate)
            self._draw_trend()

            global_stats = context.stats.get_global_stats()
            totals = global_stats.totals
            result = luck_meter(totals.total_encounters, totals.shiny_encounters)
            if result.encounters == 0:
                self._luck_label.config(text="Luck: no encounters yet.", foreground=COLOR_MUTED)
            else:
                color = {
                    "lucky": COLOR_GOOD,
                    "unlucky": COLOR_CRITICAL,
                    "on track": COLOR_INK_2,
                }.get(result.verdict, COLOR_INK_2)
                self._luck_label.config(text=f"Luck: {result.summary}", foreground=color)
        except Exception:
            pass

    def _draw_trend(self) -> None:
        canvas = self._trend_canvas
        if canvas is None or not canvas.winfo_exists():
            return
        try:
            canvas.delete("all")
            width = max(canvas.winfo_width(), 1)
            height = max(canvas.winfo_height(), 1)
            samples = self._analytics_trend.samples()
            if len(samples) < 2:
                canvas.create_text(
                    6, height / 2, anchor="w", text="collecting…", fill=COLOR_MUTED, font=("Segoe UI", 8)
                )
                return
            peak = max(self._analytics_trend.peak(), 1.0)
            pad = 3
            plot_w = width - pad * 2
            plot_h = height - pad * 2
            step = plot_w / (len(samples) - 1)
            points = []
            for i, value in enumerate(samples):
                x = pad + i * step
                y = pad + plot_h - (min(value, peak) / peak) * plot_h
                points.extend((x, y))
            canvas.create_line(*points, fill=COLOR_ACCENT, width=2, smooth=True)
            # Peak label, top-right.
            canvas.create_text(
                width - 4, 8, anchor="e", text=f"peak {int(peak):,}", fill=COLOR_MUTED, font=("Segoe UI", 7)
            )
        except Exception:
            pass

    def _open_stats_browser(self) -> None:
        """Sortable, filterable per-species stats table in a floating window."""
        if self._stats_browser is not None and self._stats_browser.winfo_exists():
            self._stats_browser.lift()
            return
        try:
            from tkinter import ttk

            from modules.analytics import build_stats_rows, filter_rows, sort_rows

            rows_all = build_stats_rows(context.stats.get_global_stats())
        except Exception as error:
            self._log_event(f"Could not open stats browser: {error}", highlight=True)
            return

        dialog = tkinter.Toplevel(self.window)
        dialog.title("Per-species stats")
        dialog.configure(background=COLOR_SURFACE)
        dialog.geometry("560x520")
        self._stats_browser = dialog

        def _on_close() -> None:
            self._stats_browser = None
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", _on_close)

        top = tkinter.Frame(dialog, background=COLOR_SURFACE)
        top.pack(fill="x", padx=8, pady=8)
        tkinter.Label(
            top, text="Filter:", background=COLOR_SURFACE, foreground=COLOR_INK_2, font=("Segoe UI", 10)
        ).pack(side="left")
        filter_var = tkinter.StringVar()
        tkinter.Entry(
            top, textvariable=filter_var, background=COLOR_CARD, foreground=COLOR_INK,
            insertbackground=COLOR_INK, relief="flat", font=("Segoe UI", 11),
        ).pack(side="left", fill="x", expand=True, padx=(6, 0), ipady=3)

        # Dark ttk styling for the Treeview.
        style = ttk.Style(dialog)
        try:
            style.theme_use("clam")
        except tkinter.TclError:
            pass
        style.configure(
            "Dex.Treeview", background=COLOR_CARD, fieldbackground=COLOR_CARD, foreground=COLOR_INK,
            rowheight=26, borderwidth=0, font=("Segoe UI", 9),
        )
        style.configure(
            "Dex.Treeview.Heading", background=COLOR_SURFACE, foreground=COLOR_INK_2,
            font=("Segoe UI", 9, "bold"), relief="flat",
        )
        style.map("Dex.Treeview", background=[("selected", COLOR_ACCENT)])

        columns = ("total", "shinies", "catches", "best_iv", "best_sv")
        headings = {
            "total": "Enc", "shinies": "✨", "catches": "Caught", "best_iv": "Best IV", "best_sv": "Best SV",
        }
        tree = ttk.Treeview(dialog, columns=columns, show="tree headings", style="Dex.Treeview")
        tree.heading("#0", text="Species", command=lambda: _sort("species"))
        tree.column("#0", width=200, anchor="w")
        for col in columns:
            tree.heading(col, text=headings[col], command=lambda c=col: _sort(c))
            tree.column(col, width=64, anchor="center")
        scroll = ttk.Scrollbar(dialog, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        state = {"key": "total", "reverse": True}
        sprite_refs: list = []  # keep PhotoImages alive for the tree

        def _populate() -> None:
            tree.delete(*tree.get_children())
            sprite_refs.clear()
            rows = filter_rows(rows_all, filter_var.get())
            rows = sort_rows(rows, state["key"], state["reverse"])
            for r in rows:
                img = self._get_species_sprite(r["species"], shiny=False, size=22)
                if img is not None:
                    sprite_refs.append(img)
                tree.insert(
                    "", "end", text=f" {r['species']}", image=img if img is not None else "",
                    values=(f"{r['total']:,}", r["shinies"], r["catches"], r["best_iv"], r["best_sv"]),
                )
            if not rows:
                tree.insert("", "end", text="  (no matching species yet)", values=("", "", "", "", ""))
            dialog._sprite_refs = sprite_refs  # anchor on the window too

        def _sort(key: str) -> None:
            if state["key"] == key:
                state["reverse"] = not state["reverse"]
            else:
                state["key"] = key
                state["reverse"] = key != "species"  # names A→Z, numbers high→low
            _populate()

        filter_var.trace_add("write", lambda *_a: _populate())
        _populate()
        self._prepare_dialog(dialog)

    def _refresh_party(self) -> None:
        try:
            from modules.pokemon_party import get_party

            party = list(get_party())
        except Exception:
            party = []

        self._current_party = party  # shared by the party tab rows + left strip hover

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
                # Hover any part of the row (#30d) — bind after all children exist.
                self._bind_party_row_hover(row_frame, len(self._party_rows))
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

        self._refresh_party_strip()

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
            if game_state in (GameState.TITLE_SCREEN, GameState.MAIN_MENU):
                # At the title/main menu only modes that opt in (e.g. Story Mode,
                # which drives the New Game intro) are offered; everything else
                # needs an in-game overworld and stays greyed out.
                try:
                    is_selectable = mode.is_selectable_from_title_screen() and mode.is_selectable()
                except Exception:
                    if context.debug:
                        console.print_exception()
                    is_selectable = False
            elif game_state is None:
                is_selectable = False
            else:
                try:
                    is_selectable = mode.is_selectable()
                except Exception:
                    if context.debug:
                        console.print_exception()
                    is_selectable = False
            if is_selectable:
                menu.add_command(label=mode.name(), command=lambda m=mode: select_bot_mode(m.name()))
            else:
                disabled_modes.append(mode.name())
        if disabled_modes:
            menu.add_separator()
            for mode_name in disabled_modes:
                menu.add_command(label=mode_name, state="disabled")
        # Debug logging toggle (sandbox) — default OFF. When on, the whole run is
        # written to an extensive diagnostic log (<profile>/debug-logs/…) so hard
        # freezes can be diagnosed from the file.
        from modules import debug_logger

        menu.add_separator()
        if self._debug_log_var is None:
            self._debug_log_var = tkinter.BooleanVar(self.window)
        self._debug_log_var.set(debug_logger.is_enabled())
        menu.add_checkbutton(
            label="Debug Logging (diagnostic file)",
            variable=self._debug_log_var,
            command=self._toggle_debug_logging,
        )
        # ENDLESS DEBUG-RESET RUNS (user request 2026-07-25). ‼ This is the DASHBOARD GUI,
        # which `pokebot.py` launches BY DEFAULT — the classic GUI in emulator_controls.py is
        # only reached via `--classic-gui`. The first attempt at this feature added the item
        # to the classic GUI only, so the user tested twice and could not find it.
        menu.add_separator()
        menu.add_command(label="Endless Debug-Reset Runs…", command=self._start_endless_runs)
        menu.tk_popup(
            self._mode_button.winfo_rootx(), self._mode_button.winfo_rooty() + self._mode_button.winfo_height()
        )

    def _start_endless_runs(self) -> None:
        """Ask for a run count, then switch to the chained DEBUG-RESET bot mode.

        ‼ THIS SELECTS A BOT MODE — it does not shell out. The first version launched
        `tools/story-dev/endless_runs.py` as a subprocess; the dialogs appeared and nothing
        appeared to happen, because a separate headless harness is not what the user asked for.
        They want `Story (DEBUG - RESET)` chained back to back in THIS emulator — so this sets
        the run count and selects `Story (ENDLESS RESET)`, which loops it in-process.
        """
        import tkinter.messagebox
        import tkinter.simpledialog

        count = tkinter.simpledialog.askinteger(
            "Endless Debug-Reset Runs",
            "How many chained DEBUG-RESET runs?\n\n"
            "Each one hard-resets to the title screen, picks NEW GAME, and plays the\n"
            "story with debug logging on until it finishes, reaches the end of built\n"
            "content, or derails. Then the next one starts automatically.\n\n"
            "0 = run forever (switch to Manual to stop).",
            parent=self.window,
            initialvalue=10,
            minvalue=0,
        )
        if count is None:
            return

        try:
            from plugins.custom_modes import story_mode as _sm

            _sm.ENDLESS_RESET_TARGET = int(count)
            mode_name = _sm.StoryEndlessResetMode.name()
        except Exception as exc:  # noqa: BLE001
            tkinter.messagebox.showerror(
                "Endless Debug-Reset Runs",
                f"Could not load the endless-reset mode:\n{type(exc).__name__}: {exc}",
                parent=self.window,
            )
            return

        # Turn debug logging on for the batch — the whole point is diagnosable overnight runs.
        try:
            from modules import debug_logger

            if not debug_logger.is_enabled():
                debug_logger.enable(context.profile)
        except Exception:
            pass

        context.bot_mode = mode_name
        self._log_event(f"Endless reset batch: {'infinite' if count == 0 else count} run(s)")
        tkinter.messagebox.showinfo(
            "Endless Debug-Reset Runs",
            f"Bot mode set to “{mode_name}” for "
            f"{'an INFINITE batch' if count == 0 else f'{count} runs'}.\n\n"
            f"It hard-resets and replays the story back to back, with debug logging on. Each "
            f"run's outcome is printed to the console as it ends.\n\n"
            f"Switch the bot mode to Manual to stop the batch.",
            parent=self.window,
        )

    def _toggle_debug_logging(self) -> None:
        from modules import debug_logger

        try:
            if self._debug_log_var is not None and self._debug_log_var.get():
                path = debug_logger.enable(context.profile)
                self._log_event(f"Debug logging ON → {path}")
            else:
                debug_logger.disable()
                self._log_event("Debug logging OFF")
        except Exception as exc:  # noqa: BLE001
            self._log_event(f"Debug logging toggle failed: {exc}")

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
