"""'Load Milestone State' popup (user directive 2026-07-23).

Sibling of LoadStateWindow, but for the REPO's story checkpoint library instead of
the profile's own states folder: a story-ordered, clearly-labeled list (chapter tag +
what the state is), a one-line safety note, and Load on double-click or button.

Loading mirrors LoadStateWindow semantics exactly: load the state bytes, reset the
frame counter, and drop to Manual so the user decides when to start a bot mode
(milestones pair with the resume-anywhere Story modes — NOT "Story (DEBUG - RESET)",
which forces a new game and would discard the loaded state)."""

from tkinter import Tk, Toplevel, messagebox, ttk

from modules.context import context
from modules.story_milestones import get_milestones


class MilestoneWindow:
    def __init__(self, window: Tk):
        milestones = get_milestones()
        if not milestones:
            messagebox.showinfo(
                "No milestone states",
                "The milestone library (tools/story-dev/saves) was not found in this "
                "checkout — pull the repository to get the story checkpoints.",
            )
            return
        self._milestones = milestones

        self._window = Toplevel(window)
        self._window.title("Load a Milestone State")
        self._window.geometry("560x480")
        self._window.bind("<Escape>", self._close)
        self._window.protocol("WM_DELETE_WINDOW", self._close)
        self._window.rowconfigure(1, weight=1)
        self._window.columnconfigure(0, weight=1)

        header = ttk.Label(
            self._window,
            text=(
                "Story checkpoints from the repo's test library (trainer: NICK).\n"
                "Loading replaces the CURRENT game session — your profile's saved game on disk "
                "is only touched if you later save in-game. Use a test profile.\n"
                "Start 'Story' or 'Story (DEBUG)' afterwards — NOT 'DEBUG - RESET' (forces a new game)."
            ),
            padding=(8, 6),
            justify="left",
        )
        header.grid(row=0, column=0, sticky="ew")

        columns = ("milestone", "detail")
        self._tree = ttk.Treeview(self._window, columns=columns, show="headings", selectmode="browse")
        self._tree.heading("milestone", text="Milestone")
        self._tree.heading("detail", text="Where / What")
        self._tree.column("milestone", width=230, anchor="w")
        self._tree.column("detail", width=290, anchor="w")
        for index, m in enumerate(self._milestones):
            self._tree.insert("", "end", iid=str(index), values=(m.title, m.detail))
        self._tree.grid(row=1, column=0, sticky="nsew", padx=8)
        self._tree.bind("<Double-1>", lambda e: self._load())
        self._tree.bind("<Return>", lambda e: self._load())

        scrollbar = ttk.Scrollbar(self._window, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        bar = ttk.Frame(self._window, padding=(8, 8))
        bar.grid(row=2, column=0, sticky="ew")
        ttk.Button(bar, text="Load selected milestone", command=self._load).pack(side="left")
        ttk.Button(bar, text="Cancel", command=self._close).pack(side="right")

    def _load(self) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        milestone = self._milestones[int(selection[0])]
        try:
            state_bytes = milestone.path.read_bytes()
        except OSError as e:
            messagebox.showerror("Milestone unreadable", f"Could not read {milestone.path.name}:\n{e}")
            return
        context.emulator.load_save_state(state_bytes)
        context.frame = 0
        if context.bot_mode != "Manual":
            context.toggle_manual_mode()
        context.message = f"Milestone loaded: {milestone.title} — start a Story mode to continue from here."
        self._close()

    def _close(self, event=None) -> None:
        if self._window is not None:
            self._window.destroy()
            self._window = None
