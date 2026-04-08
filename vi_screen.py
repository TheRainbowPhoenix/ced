from vi_globals import G, SCREEN_W, SCREEN_H
from vi_movement import end_line, next_line, begin_line, sync_cursor, get_px_width
from gint import *

def indicate_error():
    pass

def status_line(msg):
    G.status_buffer = msg
    G.have_status_msg = 1

def format_edit_status():
    from vi_movement import count_lines
    cur = count_lines(0, G.dot)
    if G.modified_count != G.last_modified_count:
        G.last_modified_count = G.modified_count

    tot = count_lines(0, len(G.text) - 1)
    if tot == 0: tot = 1
    percent = (100 * cur) // tot

    # 0=CMD, 1=INS, 2=REP, 3=COLON
    mode_ind = "-I-R-"[G.cmd_mode * 2 : G.cmd_mode * 2 + 3] if G.cmd_mode in (1, 2) else "-"
    fn = G.current_filename if G.current_filename else "No file"
    mod = " [Modified]" if G.modified_count else ""

    G.status_buffer = f"{mode_ind} {fn}{mod} {cur}/{tot} {percent}%"

def show_status_line():
    if not G.have_status_msg:
        format_edit_status()
    # status buffer rendering is handled in redraw/refresh
    G.have_status_msg = 0

# Simple tokenizer for python syntax highlighting
KEYWORDS = {"def", "class", "if", "else", "elif", "while", "for", "import", "from",
            "return", "True", "False", "None", "break", "continue", "pass", "try",
            "except", "with", "as", "global", "print", "len", "range"}
OPERATORS = set("+-*/%=<>!&|^~")
SEPARATORS = set("()[]{}:,.")

def tokenize_line(line_str):
    tokens = []
    i = 0
    length = len(line_str)

    while i < length:
        char = line_str[i]

        if char == "#":
            tokens.append((line_str[i:], C_GRAY))
            break
        elif char in ('"', "'"):
            quote = char
            start = i
            i += 1
            while i < length and line_str[i] != quote:
                i += 1
            if i < length: i += 1
            tokens.append((line_str[start:i], C_GREEN))
        elif char in OPERATORS or char in SEPARATORS:
            tokens.append((char, C_MAGENTA))
            i += 1
        elif char == " " or char == "\t":
            tokens.append((char, C_BLACK))
            i += 1
        else:
            start = i
            while i < length:
                c = line_str[i]
                if c in OPERATORS or c in SEPARATORS or c in (" ", "\t", "#", '"', "'"):
                    break
                i += 1
            word = line_str[start:i]
            if word and word[0] >= "0" and word[0] <= "9":
                tokens.append((word, C_RED))
            elif word in KEYWORDS:
                tokens.append((word, C_BLUE))
            else:
                tokens.append((word, C_BLACK))
    return tokens

def refresh(kb_visible=False, kb_h=0):
    sync_cursor()

    # Calculate views
    header_h = 30
    line_h = 20
    status_h = 20 if G.cmd_mode != 3 else line_h
    view_h = SCREEN_H - header_h - kb_h - status_h

    G.rows = view_h // line_h

    dclear(C_WHITE)

    import cinput
    theme = cinput.get_theme('light')

    # Draw Header
    header_col = theme['accent']
    header_txt = theme['txt_acc']

    drect(0, 0, SCREEN_W, header_h, header_col)

    # Menu Icon (Hamburger)
    hx, hy = 10, 5
    for i in range(3):
        drect(hx, hy + 4 + i*5, hx + 18, hy + 5 + i*5, header_txt)

    # Keyboard Icon
    kx, ky = SCREEN_W - 35, 5
    drect_border(kx, ky+2, kx+22, ky+16, C_NONE, 1, header_txt)
    for r in range(2):
        for c in range(3):
            px = kx + 3 + c*6
            py = ky + 5 + r*5
            drect(px, py, px+3, py+2, header_txt)
    if kb_visible:
        drect(kx, ky+22, kx + 22, ky+23, header_txt)

    # Title
    title = G.current_filename if G.current_filename else "untitled.py"
    dtext_opt(SCREEN_W//2, header_h//2, header_txt, C_NONE, DTEXT_CENTER, DTEXT_MIDDLE, title, -1)

    # Draw Text
    tp = G.screenbegin
    dwindow_set(0, header_h, SCREEN_W, SCREEN_H - kb_h - status_h)

    margin_x = 5

    for row in range(G.rows):
        if tp >= len(G.text):
            break

        y = header_h + row * line_h + 2
        line_end = end_line(tp)
        line_bytes = G.text[tp:line_end]

        try:
            line_str = line_bytes.decode('utf-8')
        except UnicodeDecodeError:
            line_str = "?" * len(line_bytes)

        # Draw tokens
        tokens = tokenize_line(line_str)
        cur_x = margin_x
        for txt, col in tokens:
            dtext(cur_x, y, col, txt)
            w, _ = dsize(txt, None)
            cur_x += w

        # Draw cursor if on this line
        if tp <= G.dot <= line_end:
            cx_px = margin_x + G.ccol
            char_at_cursor = " "
            if G.dot < len(G.text) and G.text[G.dot] != 10:
                try:
                    char_at_cursor = G.text[G.dot:G.dot+1].decode('utf-8')
                except: pass

            cw, _ = dsize(char_at_cursor, None)
            if G.cmd_mode == 1:
                # Insert mode cursor (vertical line)
                drect(cx_px, y, cx_px + 2, y + line_h - 2, C_BLACK)
            else:
                # Normal/Replace mode cursor (block)
                drect(cx_px, y, cx_px + cw, y + line_h - 2, C_BLACK)
                # Invert character
                if char_at_cursor != " ":
                    dtext(cx_px, y, C_WHITE, char_at_cursor)

        tp = next_line(tp)

    dwindow_set(0, 0, SCREEN_W, SCREEN_H)

    # Draw Status Line / Command Line
    status_y = SCREEN_H - kb_h - status_h
    if G.cmd_mode == 3: # COLON COMMAND MODE
        drect(0, status_y, SCREEN_W, status_y + status_h, C_LIGHT)
        dtext(5, status_y + 2, C_BLACK, ":" + G.status_buffer)
        cw, _ = dsize(":" + G.status_buffer, None)
        drect(5 + cw, status_y + 2, 5 + cw + 6, status_y + status_h - 2, C_BLACK)
    else:
        dtext(5, status_y + 2, C_RED if G.have_status_msg else C_BLACK, G.status_buffer)

def redraw(kb_visible=False, kb_h=0):
    show_status_line()
    refresh(kb_visible, kb_h)
