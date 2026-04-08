from vi_globals import G, ALLOW_UNDO, ALLOW_UNDO_CHAIN, YANKDEL
import vi_movement as m
import vi_buffer as b
import vi_screen as s
from gint import *

def not_implemented(cmd):
    s.status_line(f"'{cmd}' not implemented")

def do_cmd(c):
    # Mode handling
    if G.cmd_mode == 2: # REPLACE
        if c == 27: # ESC
            G.cmd_mode = 0
            if G.dot > 0 and G.text[G.dot-1] != 10: G.dot -= 1
        elif isinstance(c, str) and len(c) == 1:
            if G.text[G.dot] != 10:
                b.yank_delete(G.dot, G.dot, 0, YANKDEL, ALLOW_UNDO)
            b.string_insert(G.dot, c, ALLOW_UNDO_CHAIN)
            G.dot += 1
        return

    if G.cmd_mode == 1: # INSERT
        if c == 27: # ESC
            G.cmd_mode = 0
            if G.dot > 0 and G.dot <= len(G.text) and G.text[G.dot-1] != 10: G.dot -= 1
        elif c == KEY_EXE or c == '\n':
            b.string_insert(G.dot, '\n', ALLOW_UNDO)
            G.dot += 1
        elif c == KEY_DEL or c == '\b':
            if G.dot > 0:
                G.dot -= 1
                b.text_hole_delete(G.dot, G.dot, ALLOW_UNDO)
        elif isinstance(c, str) and len(c) == 1:
            b.string_insert(G.dot, c, ALLOW_UNDO)
            G.dot += 1
        return

    # NORMAL MODE
    if isinstance(c, int):
        if c == KEY_LEFT: m.dot_left()
        elif c == KEY_RIGHT: m.dot_right()
        elif c == KEY_UP: m.dot_prev()
        elif c == KEY_DOWN: m.dot_next()
        elif c == KEY_DEL:
            if G.dot < len(G.text) - 1: b.yank_delete(G.dot, G.dot, 1, YANKDEL, ALLOW_UNDO)
        return

    # String commands
    if c == 'h': m.dot_left()
    elif c == 'l': m.dot_right()
    elif c == 'k': m.dot_prev()
    elif c == 'j': m.dot_next()
    elif c == 'i':
        G.cmd_mode = 1
    elif c == 'I':
        m.dot_begin()
        m.dot_skip_over_ws()
        G.cmd_mode = 1
    elif c == 'a':
        if G.dot < len(G.text) and G.text[G.dot] != 10: G.dot += 1
        G.cmd_mode = 1
    elif c == 'A':
        m.dot_end()
        G.cmd_mode = 1
    elif c == 'o':
        m.dot_end()
        b.string_insert(G.dot, '\n', ALLOW_UNDO)
        G.dot += 1
        G.cmd_mode = 1
    elif c == 'O':
        m.dot_begin()
        b.string_insert(G.dot, '\n', ALLOW_UNDO)
        G.cmd_mode = 1
    elif c == 'x':
        if G.dot < len(G.text) and G.text[G.dot] != 10:
            b.yank_delete(G.dot, G.dot, 0, YANKDEL, ALLOW_UNDO)
    elif c == 'u':
        b.undo_pop()
    elif c == 'R':
        G.cmd_mode = 2
    elif c == ':':
        G.cmd_mode = 3 # COLON COMMAND MODE
        G.status_buffer = ""
    elif c == '0':
        m.dot_begin()
    elif c == '$':
        m.dot_end()
    elif c == 'w':
        # skip word
        while G.dot < len(G.text) and G.text[G.dot] not in (32, 9, 10): G.dot += 1
        while G.dot < len(G.text) and G.text[G.dot] in (32, 9): G.dot += 1
    elif c == 'b':
        if G.dot > 0: G.dot -= 1
        while G.dot > 0 and G.text[G.dot] in (32, 9): G.dot -= 1
        while G.dot > 0 and G.text[G.dot-1] not in (32, 9, 10): G.dot -= 1
    elif c == 'D':
        end = m.dollar_line(G.dot)
        if end >= G.dot:
            b.yank_delete(G.dot, end, 0, YANKDEL, ALLOW_UNDO)
    elif c == 'C':
        end = m.dollar_line(G.dot)
        if end >= G.dot:
            b.yank_delete(G.dot, end, 0, YANKDEL, ALLOW_UNDO)
        G.cmd_mode = 1

def colon(cmd):
    cmd = cmd.strip()
    if cmd in ("q", "q!"):
        if G.modified_count and cmd != "q!":
            s.status_line("No write since last change (add ! to override)")
        else:
            return "QUIT"
    elif cmd in ("w", "wq"):
        res = b.file_write(G.current_filename, 0, len(G.text)-1)
        if res < 0:
            s.status_line("Write error")
        else:
            G.modified_count = 0
            G.last_modified_count = -1
            s.status_line(f"'{G.current_filename}' written")
            if cmd == "wq": return "QUIT"
    else:
        not_implemented(cmd)

    G.cmd_mode = 0
    return None
