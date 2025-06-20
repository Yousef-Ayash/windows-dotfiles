import curses
import os

class FileRenamerTUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.cwd = os.getcwd()
        self.entries = []
        self.edits = {}
        self.selected, self.top = 0, 0
        self.message = ""
        self.filter_ext = ""
        self.filter_text = ""
        self.filter_type = 'both'

        # Setup colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_WHITE, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_GREEN, -1)
        curses.init_pair(5, curses.COLOR_RED, -1)
        curses.curs_set(0)

    def refresh_entries(self):
        parent = os.path.dirname(self.cwd)
        items = []
        if parent and parent != self.cwd:
            items.append(('..', True))
        dirs, files = [], []
        for e in os.scandir(self.cwd):
            if e.is_dir(): dirs.append((e.name, True))
            elif e.is_file(): files.append((e.name, False))
        dirs.sort(key=lambda x: x[0].lower())
        files.sort(key=lambda x: x[0].lower())

        def visible(name, is_dir):
            if is_dir and self.filter_type == 'files': return False
            if not is_dir and self.filter_type == 'dirs': return False
            if not is_dir and self.filter_ext and not name.lower().endswith(self.filter_ext.lower()): return False
            if self.filter_text and self.filter_text.lower() not in name.lower(): return False
            return True

        for entry in dirs + files:
            if visible(entry[0], entry[1]): items.append(entry)
        self.entries = items

    def draw_separator(self, y):
        _, w = self.stdscr.getmaxyx()
        self.stdscr.hline(y, 0, '-', w)

    def draw(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        header = f" Dir: {self.cwd} | Filter: '{self.filter_text}' Ext: '{self.filter_ext}' Type: {self.filter_type} "
        self.stdscr.addstr(0, 0, header[:w-1], curses.A_BOLD)
        self.draw_separator(1)
        for i, (name, is_dir) in enumerate(self.entries[self.top:self.top + h - 6]):
            ri = self.top + i
            disp = self.edits.get(ri, name)
            tag = '[DIR]' if is_dir else '[FILE]'
            prefix = '>' if ri == self.selected else ' '
            line = f"{prefix} {tag} {disp}"
            if ri == self.selected:
                attr = curses.A_REVERSE
            elif ri in self.edits:
                attr = curses.color_pair(3)
            else:
                attr = curses.color_pair(1) if is_dir else curses.color_pair(2)
            self.stdscr.addnstr(i + 2, 0, line, w-1, attr)
        self.draw_separator(h - 3)
        footer = "↑/↓ Move  Enter Open  n Rename  b Bulk  r Apply  f Filter  Esc/Ctrl+Q Cancel  q Quit"
        self.stdscr.addstr(h - 2, 0, footer[:w-1], curses.A_DIM)
        if self.message:
            col = curses.color_pair(4) if 'Renamed' in self.message or 'scheduled' in self.message else curses.color_pair(5)
            self.stdscr.addstr(h - 1, 0, self.message[:w-1], col | curses.A_BOLD)
        self.stdscr.refresh()

    def prompt_input(self, prompt):
        h, w = self.stdscr.getmaxyx()
        buf = ''
        curses.curs_set(1)
        self.stdscr.addstr(h - 2, 0, prompt)
        self.stdscr.clrtoeol()
        while True:
            ch = self.stdscr.getch()
            if ch in (10, 13): break
            if ch in (27, 17): buf = None; break
            if ch in (curses.KEY_BACKSPACE, 127, 8): buf = buf[:-1]
            elif 32 <= ch <= 126: buf += chr(ch)
            self.stdscr.addstr(h - 2, 0, prompt + (buf or ''))
            self.stdscr.clrtoeol()
        curses.curs_set(0)
        return buf

    def choose_filter_type(self):
        options = ['files', 'dirs', 'both']
        idx = options.index(self.filter_type)
        h, w = self.stdscr.getmaxyx()
        prompt_y = h - 4
        while True:
            for i, opt in enumerate(options):
                x = i * (w // len(options))
                attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
                self.stdscr.addstr(prompt_y, x, opt.center(w // len(options)), attr)
            self.stdscr.refresh()
            ch = self.stdscr.getch()
            if ch in (curses.KEY_LEFT, ord('h')): idx = (idx - 1) % len(options)
            elif ch in (curses.KEY_RIGHT, ord('l')): idx = (idx + 1) % len(options)
            elif ch in (10, 13): self.filter_type = options[idx]; break
            elif ch in (27, 17): break
        self.stdscr.move(h - 4, 0)
        self.stdscr.clrtoeol()

    def filter_entries(self):
        t = self.prompt_input("Filter text (empty to clear): ")
        if t is None: self.message = "Filter canceled"; return
        x = self.prompt_input("Filter ext (e.g. .txt, empty to clear): ")
        if x is None: self.message = "Filter canceled"; return
        self.message = "Select filter type:"
        self.draw()
        self.choose_filter_type()
        self.filter_text, self.filter_ext = t, x
        self.selected, self.top = 0, 0
        self.edits.clear()
        self.message = f"Filter set: text='{t}', ext='{x}', type={self.filter_type}"
        self.refresh_entries()

    def navigate_entry(self, idx):
        name, is_dir = self.entries[idx]
        if is_dir:
            if name == '..': self.cwd = os.path.dirname(self.cwd)
            else: self.cwd = os.path.join(self.cwd, name)
            self.selected, self.top = 0, 0
            self.edits.clear()
            self.message = f"Changed directory to {self.cwd}"
            self.refresh_entries()

    def rename_item(self, idx):
        name, is_dir = self.entries[idx]
        base, ext = os.path.splitext(name)
        new = self.prompt_input(f"Rename '{name}' to (omit extension to keep): ")
        if new is None:
            self.message = "Rename canceled"
        else:
            # Preserve extension if omitted
            if not os.path.splitext(new)[1] and ext:
                new = new + ext
            if new and new != name:
                self.edits[idx] = new
                self.message = f"Scheduled rename: {name} -> {new}"
            else:
                self.message = "Rename unchanged"

    def bulk_pattern(self):
        find = self.prompt_input("Find: ")
        if find is None: self.message = "Bulk canceled"; return
        rep = self.prompt_input("Replace: ")
        if rep is None: return
        pre = self.prompt_input("Prefix: ") or ''
        suf = self.prompt_input("Suffix: ") or ''
        cnt = 0
        for i, (n, _) in enumerate(self.entries):
            if n == '..': continue
            base, ext = os.path.splitext(n)
            new = f"{pre}{base.replace(find, rep)}{suf}{ext}"
            if new != n:
                self.edits[i] = new
                cnt += 1
        self.message = f"Bulk scheduled {cnt} renames"

    def rename_entries(self):
        if not self.edits: self.message = "Nothing to rename"; return
        succ, errs = 0, []
        for i, new in list(self.edits.items()):
            old, _ = self.entries[i]
            pold = os.path.join(self.cwd, old)
            pnew = os.path.join(self.cwd, new)
            try:
                if os.path.exists(pnew): raise FileExistsError
                os.rename(pold, pnew)
                succ += 1
            except Exception as e: errs.append(str(e))
        self.edits.clear(); self.refresh_entries()
        self.message = f"Renamed {succ} items" + (f", {len(errs)} errors" if errs else "")

    def run(self):
        self.refresh_entries()
        while True:
            self.draw()
            k = self.stdscr.getch()
            if k in (curses.KEY_DOWN, ord('j')) and self.selected < len(self.entries) - 1:
                self.selected += 1
                if self.selected >= self.top + self.stdscr.getmaxyx()[0] - 6: self.top += 1
            elif k in (curses.KEY_UP, ord('k')) and self.selected > 0:
                self.selected -= 1
                if self.selected < self.top: self.top -= 1
            elif k in (curses.KEY_ENTER, 10, 13): self.navigate_entry(self.selected)
            elif k in (curses.KEY_BACKSPACE, 127, 8):
                idx = next((i for i, e in enumerate(self.entries) if e == ('..', True)), None)
                if idx is not None: self.navigate_entry(idx)
            elif k == ord('n'): self.rename_item(self.selected)
            elif k == ord('b'): self.bulk_pattern()
            elif k == ord('r'): self.rename_entries()
            elif k == ord('f'): self.filter_entries()
            elif k in (27, 17): self.message = "Operation canceled"
            elif k == ord('q'): break


def main(stdscr):
    app = FileRenamerTUI(stdscr)
    app.run()

if __name__ == '__main__':
    curses.wrapper(main)
