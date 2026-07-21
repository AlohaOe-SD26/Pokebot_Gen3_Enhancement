import random
import re
import time
from pathlib import Path
from tkinter import Canvas, PhotoImage, TclError, Tk, Toplevel, ttk

import PIL.Image
import PIL.ImageDraw
import PIL.ImageTk

from modules.context import context
from modules.runtime import get_sprites_path

# Show only a few save states per page and load ONLY the current page's
# thumbnails. The window used to eagerly decode every save-state screenshot (up
# to 128 PNGs) on open, so a full `states/` folder made it crawl. Paginating and
# lazily rendering one page keeps it instant no matter how many states exist.
STATES_PER_PAGE = 5


class LoadStateWindow:
    def __init__(self, window: Tk):
        state_directory = context.profile.path / "states"
        if not state_directory.is_dir():
            return

        state_files: list[Path] = list(state_directory.glob("*.ss1"))
        if not state_files:
            return

        def remove_window(event=None):
            self._load_save_window.destroy()
            self._load_save_window = None

        def load_state(state: Path):
            context.emulator.load_save_state(state.read_bytes())
            context.frame = 0
            if context.bot_mode != "Manual":
                context.toggle_manual_mode()
            self._load_save_window.after(50, remove_window)

        def filter_state_files(files: list[Path]) -> list[Path]:
            # Newest first; keep at most a few autosaves so they don't crowd out
            # the named states. NOTE: this only sorts/filters PATHS — no image is
            # decoded here, so it stays cheap even for a huge folder.
            maximum_number_of_autosave_files = 3
            maximum_number_of_entries = 128
            autosaves_already_included = 0
            number_of_entries_so_far = 0
            autosave_pattern = re.compile("^\\d{4}-\\d{2}-\\d{2}_\\d{2}-\\d{2}-\\d{2}\\.ss1$")
            files.sort(reverse=True, key=lambda file: file.stat().st_mtime)
            result: list[Path] = []
            for file in files:
                if file.name == "current_state.ss1" or autosave_pattern.match(file.name):
                    if autosaves_already_included >= maximum_number_of_autosave_files:
                        continue
                    autosaves_already_included += 1
                number_of_entries_so_far += 1
                if number_of_entries_so_far > maximum_number_of_entries:
                    break
                result.append(file)
            return result

        # Cheap up-front: just the list of paths (no thumbnails yet).
        self._states: list[Path] = filter_state_files(state_files)
        self._page = 0
        self._page_count = max(1, (len(self._states) + STATES_PER_PAGE - 1) // STATES_PER_PAGE)
        # Keeps PhotoImage references for the CURRENT page alive (cleared on flip).
        self._photo_buffer: list = []

        self._load_save_window = Toplevel(window)
        self._load_save_window.title("Load a Save State")
        self._load_save_window.geometry("525x540")
        self._load_save_window.protocol("WM_DELETE_WINDOW", remove_window)
        self._load_save_window.bind("<Escape>", remove_window)
        self._load_save_window.rowconfigure(1, weight=1)
        self._load_save_window.columnconfigure(0, weight=1)

        # --- Pagination bar (only shown when there's more than one page). ------
        nav = ttk.Frame(self._load_save_window, padding=(6, 6))
        nav.grid(row=0, column=0, sticky="WE")
        nav.columnconfigure(1, weight=1)
        prev_button = ttk.Button(nav, text="◀ Prev", width=8)
        page_label = ttk.Label(nav, anchor="center")
        next_button = ttk.Button(nav, text="Next ▶", width=8)
        prev_button.grid(row=0, column=0, sticky="W")
        page_label.grid(row=0, column=1, sticky="WE")
        next_button.grid(row=0, column=2, sticky="E")

        # --- Scrollable page area. ---------------------------------------------
        scrollable_frame = ttk.Frame(self._load_save_window)
        scrollable_frame.grid(row=1, column=0, sticky="NSWE")
        canvas = Canvas(scrollable_frame, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(scrollable_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        frame = ttk.Frame(canvas, width=500)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        canvas.create_window((0, 0), window=frame, anchor="nw")

        def thumbnail_for(state: Path):
            with open(state, "rb") as file:
                is_png = file.read(4) == b"\x89PNG"
            if is_png:
                try:
                    return PhotoImage(master=canvas, file=state)
                except TclError:
                    pass
            # No/invalid screenshot — draw a placeholder with a random TM sprite.
            placeholder = PIL.Image.new(mode="RGBA", size=(240, 160))
            draw = PIL.ImageDraw.Draw(placeholder)
            draw.rectangle(xy=[(0, 0), (placeholder.width, placeholder.height)], fill="#000000FF")
            possible_sprites = [f"TM{n:02d}" for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 23, 24, 30, 37, 40)]
            sprite = PIL.Image.open(get_sprites_path() / "items" / f"{random.choice(possible_sprites)}.png")
            if sprite.mode != "RGBA":
                sprite = sprite.convert("RGBA")
            sprite = sprite.resize((sprite.width * 3, sprite.height * 3), resample=False)
            placeholder.paste(
                sprite,
                (placeholder.width // 2 - sprite.width // 2, placeholder.height // 2 - sprite.height // 2),
                sprite,
            )
            self._photo_buffer.append(placeholder)  # keep PIL image alive too
            return PIL.ImageTk.PhotoImage(image=placeholder)

        def render_page():
            # Clear the previous page's widgets + thumbnail refs (frees memory and
            # lets Tk drop the old PhotoImages).
            for child in frame.winfo_children():
                child.destroy()
            self._photo_buffer = []

            start = self._page * STATES_PER_PAGE
            page_states = self._states[start : start + STATES_PER_PAGE]
            column = 0
            row = 0
            for state in page_states:
                photo = thumbnail_for(state)
                self._photo_buffer.append(photo)
                button_frame = ttk.Frame(frame, padding=5)
                button_frame.rowconfigure(0, weight=1)
                button_frame.columnconfigure(0, weight=1)
                button_frame.grid(row=int(row), column=column, sticky="NSWE")
                button = ttk.Button(
                    button_frame,
                    text=state.name,
                    image=photo,
                    compound="top",
                    padding=0,
                    width=1,
                    command=lambda s=state: load_state(s),
                )
                button.grid(sticky="NSWE")
                column = 1 if column == 0 else 0
                if column == 0:
                    row += 1

            page_label.configure(text=f"Page {self._page + 1} / {self._page_count}   ({len(self._states)} states)")
            prev_button.configure(state=("disabled" if self._page <= 0 else "normal"))
            next_button.configure(state=("disabled" if self._page >= self._page_count - 1 else "normal"))
            canvas.yview_moveto(0)
            canvas.configure(scrollregion=canvas.bbox("all"))

        def go(delta: int):
            new_page = min(max(0, self._page + delta), self._page_count - 1)
            if new_page != self._page:
                self._page = new_page
                render_page()

        prev_button.configure(command=lambda: go(-1))
        next_button.configure(command=lambda: go(1))
        # Arrow keys + PageUp/PageDown flip pages too.
        self._load_save_window.bind("<Left>", lambda e: go(-1))
        self._load_save_window.bind("<Right>", lambda e: go(1))
        self._load_save_window.bind("<Prior>", lambda e: go(-1))
        self._load_save_window.bind("<Next>", lambda e: go(1))

        # Hide the nav bar entirely if everything fits on one page.
        if self._page_count <= 1:
            nav.grid_remove()

        render_page()

        while self._load_save_window is not None:
            self._load_save_window.update_idletasks()
            self._load_save_window.update()
            time.sleep(1 / 60)

    def focus(self):
        self._load_save_window.focus_force()
