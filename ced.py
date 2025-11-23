from gint import *
from io import open

# =============================================================================
# CONFIGURATION
# =============================================================================

# Screen
SCREEN_W = 320
SCREEN_H = 528

C_GRAY = 0x7BEF
C_MAGENTA = 0xF81F

COL_BG = C_WHITE
COL_TXT = C_BLACK
COL_KBD_BG = C_LIGHT    # Background of the keyboard area
COL_KEY_BG = C_WHITE    # Background of normal keys
COL_KEY_SPECIAL = 0xDDDD # Light gray for special keys
COL_KEY_BORDER = C_DARK
COL_HIGHLIGHT = C_BLUE

# Syntax Colors
COL_KW = C_BLUE
COL_STR = C_GREEN
COL_COM = C_GRAY
COL_NUM = C_RED
COL_OP = C_MAGENTA

# Layout Sizes
HEADER_H = 30
KEYBOARD_H = 260
TAB_H = 30
ROW_H = 45
TEXT_LINE_H = 20
TEXT_MARGIN_X = 5

# =============================================================================
# DATA & UTILS
# =============================================================================

KEYWORDS = {
    "def", "class", "if", "else", "elif", "while", "for", "import", "from", 
    "return", "True", "False", "None", "break", "continue", "pass", "try", 
    "except", "with", "as", "global", "print", "len", "range"
}

# Keyboard Layouts
LAYOUT_ABC = [
    list("1234567890"),
    list("qwertyuiop"),
    list("asdfghjkl:"),
    list("zxcvbnm,._")
]

LAYOUT_SYM = [
    list("()[]{}"),      
    list("=+-*/%"),      
    list("'\"#\\_"),     
    list("@?!$;")        
]

LAYOUT_MATH = [
    list("<>!=&|"),      
    list("^~`"),         
    list("01234"),       
    list("56789")
]

def is_digit(char: str) -> bool:
    return "0" <= char <= "9"

def tokenize_line(line: str) -> list[tuple[str, int]]:
    """Splits a line into (text_segment, color) tuples for highlighting."""
    tokens = []
    i = 0
    length = len(line)
    OPERATORS = set("+-*/%=<>!&|^~")
    SEPARATORS = set("()[]{}:,.")
    
    while i < length:
        char = line[i]
        
        if char == "#":
            tokens.append((line[i:], COL_COM))
            break
        elif char in ('"', "'"):
            quote = char
            start = i
            i += 1
            while i < length and line[i] != quote:
                i += 1
            if i < length: i += 1
            tokens.append((line[start:i], COL_STR))
        elif char in OPERATORS or char in SEPARATORS:
            tokens.append((char, COL_OP))
            i += 1
        elif char == " " or char == "\t":
            tokens.append((char, COL_TXT))
            i += 1
        else:
            start = i
            while i < length:
                c = line[i]
                if c in OPERATORS or c in SEPARATORS or c in (" ", "\t", "#", '"', "'"):
                    break
                i += 1
            word = line[start:i]
            if is_digit(word[0]):
                tokens.append((word, COL_NUM))
            elif word in KEYWORDS:
                tokens.append((word, COL_KW))
            else:
                tokens.append((word, COL_TXT))
    return tokens

# =============================================================================
# VIRTUAL KEYBOARD ENGINE
# =============================================================================

class VirtualKeyboard:
    def __init__(self):
        self.visible = False
        self.y = SCREEN_H - KEYBOARD_H
        self.current_tab = 0 
        self.shift = False
        self.tabs = ["abc", "Sym", "Math"]
        
    def get_layout(self):
        if self.current_tab == 0:
            return LAYOUT_ABC
        elif self.current_tab == 1:
            return LAYOUT_SYM
        else:
            return LAYOUT_MATH

    def draw_key(self, x, y, w, h, label, is_special=False, is_pressed=False):
        bg = COL_HIGHLIGHT if is_pressed else (COL_KEY_SPECIAL if is_special else COL_KEY_BG)
        drect(x + 1, y + 1, x + w - 1, y + h - 1, bg)
        drect_border(x, y, x + w, y + h, C_NONE, 1, COL_KEY_BORDER)
        dtext_opt(x + w//2, y + h//2, COL_TXT, C_NONE, DTEXT_CENTER, DTEXT_MIDDLE, label, -1)

    def draw(self):
        if not self.visible:
            return

        # Background
        drect(0, self.y, SCREEN_W, SCREEN_H, COL_KBD_BG)
        dhline(self.y, COL_KEY_BORDER)

        # Tabs
        tab_w = SCREEN_W // 3
        for i, tab_name in enumerate(self.tabs):
            tx = i * tab_w
            is_active = (i == self.current_tab)
            bg = COL_KBD_BG if is_active else COL_KEY_SPECIAL
            drect(tx, self.y, tx + tab_w, self.y + TAB_H, bg)
            drect_border(tx, self.y, tx + tab_w, self.y + TAB_H, C_NONE, 1, COL_KEY_BORDER)
            if is_active:
                drect(tx + 1, self.y + TAB_H - 2, tx + tab_w - 1, self.y + TAB_H + 2, COL_KBD_BG)
            dtext_opt(tx + tab_w//2, self.y + TAB_H//2, COL_TXT, C_NONE, 
                      DTEXT_CENTER, DTEXT_MIDDLE, tab_name, -1)

        # Key Grid
        layout = self.get_layout()
        grid_y_start = self.y + TAB_H
        
        for r, row in enumerate(layout):
            count = len(row)
            kw = SCREEN_W // count
            for c, char in enumerate(row):
                kx = c * kw
                ky = grid_y_start + r * ROW_H
                label = char
                if self.current_tab == 0 and self.shift:
                    label = char.upper()
                self.draw_key(kx, ky, kw, ROW_H, label)

        # Bottom Control Row
        bot_y = grid_y_start + 4 * ROW_H
        bot_h = ROW_H
        
        self.draw_key(0, bot_y, 50, bot_h, "CAPS", True, self.shift)
        self.draw_key(50, bot_y, 50, bot_h, "<-", True)
        self.draw_key(100, bot_y, 160, bot_h, "Space", False)
        self.draw_key(260, bot_y, 60, bot_h, "EXE", True)

    def handle_touch(self, x, y, type):
        if not self.visible or y < self.y:
            return None

        # Tabs
        if y < self.y + TAB_H:
            if type == KEYEV_TOUCH_DOWN:
                tab_w = SCREEN_W // 3
                idx = x // tab_w
                if 0 <= idx < 3:
                    self.current_tab = idx
            return "TAB"

        # Grid vs Bottom
        grid_y_start = self.y + TAB_H
        row_idx = (y - grid_y_start) // ROW_H
        
        if 0 <= row_idx < 4:
            layout = self.get_layout()
            row_chars = layout[row_idx]
            kw = SCREEN_W // len(row_chars)
            col_idx = x // kw
            if 0 <= col_idx < len(row_chars):
                char = row_chars[col_idx]
                if self.current_tab == 0 and self.shift:
                    char = char.upper()
                return char

        elif row_idx == 4:
            if x < 50:
                if type == KEYEV_TOUCH_DOWN: self.shift = not self.shift
                return "SHIFT"
            elif x < 100: return "BACKSPACE"
            elif x < 260: return " "
            else: return "ENTER"
        return None

# =============================================================================
# EDITOR LOGIC
# =============================================================================

class Editor:
    def __init__(self):
        self.lines = [""]
        self.filename = "example.py"
        self.cy = 0
        self.cx = 0
        self.vy = 0
        self.keyboard = VirtualKeyboard()
        self.msg = ""
        self.msg_timer = 0
        
    def clamp_cursor(self):
        """Ensures cursor is within valid bounds."""
        if self.cy < 0: self.cy = 0
        if self.cy >= len(self.lines): self.cy = len(self.lines) - 1
        
        line_len = len(self.lines[self.cy])
        if self.cx < 0: self.cx = 0
        if self.cx > line_len: self.cx = line_len

    def load_file(self):
        try:
            with open(self.filename, "r") as f:
                content = f.read()
                # Handle different line endings just in case
                self.lines = content.replace("\r\n", "\n").split("\n")
                if not self.lines: self.lines = [""]
            self.msg = "Loaded " + self.filename
            self.cy = 0
            self.cx = 0
        except:
            self.msg = "File not found"
        self.msg_timer = 50
        self.clamp_cursor()

    def save_file(self):
        try:
            with open(self.filename, "w") as f:
                f.write("\n".join(self.lines))
            self.msg = "Saved " + self.filename
        except Exception as e:
            self.msg = "Save Error"
        self.msg_timer = 50

    def insert_char(self, char):
        self.clamp_cursor()
        line = self.lines[self.cy]
        self.lines[self.cy] = line[:self.cx] + char + line[self.cx:]
        self.cx += 1
        self.clamp_cursor()

    def delete_char(self):
        self.clamp_cursor()
        if self.cx > 0:
            line = self.lines[self.cy]
            self.lines[self.cy] = line[:self.cx-1] + line[self.cx:]
            self.cx -= 1
        elif self.cy > 0:
            curr = self.lines.pop(self.cy)
            self.cy -= 1
            self.cx = len(self.lines[self.cy])
            self.lines[self.cy] += curr
        self.clamp_cursor()

    def new_line(self):
        self.clamp_cursor()
        line = self.lines[self.cy]
        rem = line[self.cx:]
        self.lines[self.cy] = line[:self.cx]
        self.cy += 1
        self.lines.insert(self.cy, rem)
        self.cx = 0
        self.clamp_cursor()

    def get_cx_from_px(self, line: str, target_x: int) -> int:
        if target_x <= TEXT_MARGIN_X:
            return 0
        rel_x = target_x - TEXT_MARGIN_X
        
        # Binary search or scan for closest index
        best_i = 0
        min_diff = 10000
        
        for i in range(len(line) + 1):
            w, _ = dsize(line[:i], None)
            diff = abs(w - rel_x)
            if diff < min_diff:
                min_diff = diff
                best_i = i
            else:
                break
        return best_i

    def process_event(self, ev):
        if ev.type == KEYEV_TOUCH_DOWN or ev.type == KEYEV_TOUCH_DRAG:
            # Check Keyboard
            if self.keyboard.visible and ev.y >= self.keyboard.y:
                if ev.type == KEYEV_TOUCH_DOWN: 
                    res = self.keyboard.handle_touch(ev.x, ev.y, ev.type)
                    if res and len(res) == 1: self.insert_char(res)
                    elif res == "BACKSPACE": self.delete_char()
                    elif res == "ENTER": self.new_line()
                return

            # Check Menu
            if ev.y < HEADER_H and ev.type == KEYEV_TOUCH_DOWN:
                if ev.x > SCREEN_W - 60: self.keyboard.visible = not self.keyboard.visible
                elif ev.x < 60: self.load_file()
                elif ev.x < 120: self.save_file()
                return

            # Check Text Area
            txt_area_h = SCREEN_H - HEADER_H - (KEYBOARD_H if self.keyboard.visible else 0)
            if HEADER_H <= ev.y <= HEADER_H + txt_area_h:
                row = (ev.y - HEADER_H) // TEXT_LINE_H + self.vy
                if 0 <= row < len(self.lines):
                    self.cy = row
                    self.cx = self.get_cx_from_px(self.lines[row], ev.x)
                    self.clamp_cursor()

        elif ev.type == KEYEV_DOWN:
            if ev.key == KEY_EXP: self.keyboard.visible = not self.keyboard.visible
            elif ev.key == KEY_EXE: self.new_line()
            elif ev.key == KEY_DEL: self.delete_char()
            elif ev.key == KEY_UP: 
                self.cy -= 1
                self.clamp_cursor()
            elif ev.key == KEY_DOWN: 
                self.cy += 1
                self.clamp_cursor()
            elif ev.key == KEY_LEFT: 
                self.cx -= 1
                if self.cx < 0 and self.cy > 0:
                    self.cy -= 1
                    self.cx = len(self.lines[self.cy])
                self.clamp_cursor()
            elif ev.key == KEY_RIGHT: 
                self.cx += 1
                if self.cx > len(self.lines[self.cy]) and self.cy < len(self.lines) - 1:
                    self.cy += 1
                    self.cx = 0
                self.clamp_cursor()
            elif ev.key == KEY_DOT: self.insert_char('.')
        
        # Ensure we never go out of bounds after any event
        self.clamp_cursor()

    def draw(self):
        dclear(COL_BG)
        
        # Menu Bar
        drect(0, 0, SCREEN_W, HEADER_H, C_LIGHT)
        dline(0, HEADER_H, SCREEN_W, HEADER_H, C_BLACK)
        dtext(10, 8, C_BLACK, "Load")
        dtext(70, 8, C_BLACK, "Save")
        dtext(SCREEN_W - 50, 8, C_BLACK, "KBD")
        dtext(SCREEN_W // 2 - 40, 8, C_BLUE, self.filename)

        # Text Area
        kb_h = KEYBOARD_H if self.keyboard.visible else 0
        view_h = SCREEN_H - HEADER_H - kb_h
        lines_vis = view_h // TEXT_LINE_H
        
        # Auto scroll
        if self.cy < self.vy: self.vy = self.cy
        if self.cy >= self.vy + lines_vis: self.vy = self.cy - lines_vis + 1
        
        # Clip
        dwindow_set(0, HEADER_H, SCREEN_W, SCREEN_H - kb_h)

        for i in range(lines_vis):
            idx = self.vy + i
            if idx >= len(self.lines): break
            
            line_str = self.lines[idx]
            y = HEADER_H + i * TEXT_LINE_H + 2
            
            # Draw Text
            # Track the character index to calculate position based on full string width
            # rather than adding up token widths, to avoid rounding/kerning drift.
            current_char_idx = 0
            tokens = tokenize_line(line_str)
            
            for txt, col in tokens:
                # Calculate X based on the width of everything preceding this token
                # This ensures alignment with dsize() cursor logic
                prefix_width, _ = dsize(line_str[:current_char_idx], None)
                x_pos = TEXT_MARGIN_X + prefix_width
                
                dtext(x_pos, y, col, txt)
                current_char_idx += len(txt)
                
            # Draw Cursor
            if idx == self.cy:
                # Use dsize on the exact substring to match visual placement. You may need a recent PythonExtra
                cursor_offset, _ = dsize(line_str[:self.cx], None)
                cx_px = TEXT_MARGIN_X + cursor_offset
                drect(cx_px, y, cx_px + 2, y + 18, C_BLACK)

        # Reset Clip
        dwindow_set(0, 0, SCREEN_W, SCREEN_H)

        # Message
        if self.msg_timer > 0:
            self.msg_timer -= 1
            dtext(10, SCREEN_H - 20, C_RED, self.msg)

        # Keyboard
        self.keyboard.draw()
        
        dupdate()

# =============================================================================
# MAIN
# =============================================================================

def main():
    editor = Editor()
    clearevents()
    
    # Attempt initial load
    editor.load_file()
    
    while True:
        ev = getkey_opt(GETKEY_DEFAULT, 100) 
        if ev.key == KEY_EXIT:
            break
        if ev.type != KEYEV_NONE:
            editor.process_event(ev)
        editor.draw()

if __name__ == "__main__":
    main()