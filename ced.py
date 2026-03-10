from gint import *
import cinput
from vi_globals import G, SCREEN_W, SCREEN_H
import vi_buffer as b
import vi_screen as s
import vi_cmd as c
import time

def main():
    b.init_text_buffer("untitled.py")

    kbd = cinput.Keyboard(theme='light', layout='qwerty')
    kbd.visible = False

    clearevents()
    running = True

    while running:
        s.redraw(kb_visible=kbd.visible, kb_h=260 if kbd.visible else 0)

        if kbd.visible:
            kbd.draw()

        # Draw everything in one go
        dupdate()

        ev = pollevent()
        while ev.type != KEYEV_NONE:
            # Global keyboard toggle
            if ev.type == KEYEV_DOWN and ev.key == KEY_KBD:
                kbd.visible = not kbd.visible

            # Top bar toggle
            if ev.type == KEYEV_TOUCH_DOWN and ev.y < 30 and ev.x < 50:
                kbd.visible = not kbd.visible

            res = None
            if kbd.visible and ev.type == KEYEV_TOUCH_DOWN and ev.y >= kbd.y:
                res = kbd.update(ev)

            if G.cmd_mode == 3: # COLON COMMAND MODE
                if ev.type == KEYEV_DOWN and ev.key == KEY_EXIT:
                    G.cmd_mode = 0
                elif ev.type == KEYEV_DOWN and ev.key == KEY_DEL:
                    if len(G.status_buffer) > 0: G.status_buffer = G.status_buffer[:-1]
                    else: G.cmd_mode = 0
                elif ev.type == KEYEV_DOWN and ev.key == KEY_EXE:
                    if c.colon(G.status_buffer) == "QUIT": running = False
                elif res:
                    if res == "ENTER" or res == "\n":
                        if c.colon(G.status_buffer) == "QUIT": running = False
                    elif res == "BACKSPACE" or res == "\b":
                        if len(G.status_buffer) > 0: G.status_buffer = G.status_buffer[:-1]
                        else: G.cmd_mode = 0
                    elif len(res) == 1:
                        G.status_buffer += res
            else:
                if res:
                    c.do_cmd(res)
                elif ev.type == KEYEV_DOWN:
                    if ev.key == KEY_EXIT: c.do_cmd(27) # ESC
                    else: c.do_cmd(ev.key)

            ev = pollevent()

        time.sleep(0.01)

if __name__ == "__main__":
    main()
