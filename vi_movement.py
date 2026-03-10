from vi_globals import G
from gint import dsize

def bound_dot(p):
    if p >= len(G.text) and len(G.text) > 0:
        return len(G.text) - 1
    if p < 0:
        return 0
    return p

def begin_line(p):
    if p > 0:
        idx = G.text.rfind(b'\n', 0, p)
        if idx == -1:
            return 0
        return idx + 1
    return p

def end_line(p):
    if p < len(G.text) - 1:
        idx = G.text.find(b'\n', p)
        if idx == -1:
            return len(G.text) - 1
        return idx
    return p

def dollar_line(p):
    p = end_line(p)
    if p < len(G.text) and G.text[p] == 10 and (p - begin_line(p)) > 0:
        p -= 1
    return p

def prev_line(p):
    p = begin_line(p)
    if p > 0 and G.text[p-1] == 10:
        p -= 1
    return begin_line(p)

def next_line(p):
    p = end_line(p)
    if p < len(G.text) - 1 and G.text[p] == 10:
        p += 1
    return p

def end_screen():
    q = G.screenbegin
    for _ in range(G.rows - 2):
        q = next_line(q)
    return end_line(q)

def count_lines(start, stop):
    if stop < start:
        start, stop = stop, start
    cnt = 0
    stop = end_line(stop)
    while start <= stop and start < len(G.text):
        start = end_line(start)
        if start < len(G.text) and G.text[start] == 10:
            cnt += 1
        start += 1
    return cnt

def find_line(li):
    q = 0
    for _ in range(li - 1):
        q = next_line(q)
    return q

def dot_left():
    if G.dot > 0 and G.text[G.dot - 1] != 10:
        G.dot -= 1

def dot_right():
    if G.dot < len(G.text) - 1 and G.text[G.dot] != 10:
        G.dot += 1

def dot_begin():
    G.dot = begin_line(G.dot)

def dot_end():
    G.dot = end_line(G.dot)

def dot_next():
    G.dot = next_line(G.dot)

def dot_prev():
    G.dot = prev_line(G.dot)

def dot_skip_over_ws():
    while G.dot < len(G.text) - 1 and G.text[G.dot] in (32, 9) and G.text[G.dot] != 10: # space or tab
        G.dot += 1

def dot_scroll(cnt, dir):
    for _ in range(cnt):
        if dir < 0:
            G.screenbegin = prev_line(G.screenbegin)
        else:
            G.screenbegin = next_line(G.screenbegin)

    if G.dot < G.screenbegin:
        G.dot = G.screenbegin
    q = end_screen()
    if G.dot > q:
        G.dot = begin_line(q)
    dot_skip_over_ws()

# Adaptation for variable width
def get_px_width(text_bytes):
    # decodes to string and gets pixel width using gint
    try:
        s = text_bytes.decode('utf-8')
    except UnicodeDecodeError:
        # fallback
        s = "?" * len(text_bytes)
    w, _ = dsize(s, None)
    return w

def move_to_px(p, target_px):
    p = begin_line(p)
    current_px = 0
    while current_px < target_px and p < len(G.text) and G.text[p] != 10:
        char_bytes = G.text[p:p+1]
        char_px = get_px_width(char_bytes)
        if current_px + char_px/2 > target_px:
            break
        current_px += char_px
        p += 1
    return p

def sync_cursor():
    # keep dot on screen
    beg_cur = begin_line(G.dot)

    if beg_cur < G.screenbegin:
        G.screenbegin = beg_cur
    else:
        end_scr = end_screen()
        if beg_cur > end_scr:
            cnt = count_lines(end_scr, beg_cur)
            for _ in range(cnt):
                G.screenbegin = next_line(G.screenbegin)

    # find out which row
    tp = G.screenbegin
    ro = 0
    for _ in range(G.rows - 1):
        if tp == beg_cur:
            break
        tp = next_line(tp)
        ro += 1

    G.crow = ro

    # Calculate pixel offset for ccol instead of char offset
    line_bytes = G.text[beg_cur:G.dot]
    G.ccol = get_px_width(line_bytes)
