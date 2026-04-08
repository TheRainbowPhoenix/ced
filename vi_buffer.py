from vi_globals import G, UndoObject, UNDO_INS, UNDO_DEL, UNDO_INS_CHAIN, UNDO_DEL_CHAIN, NO_UNDO, ALLOW_UNDO, ALLOW_UNDO_CHAIN, YANKDEL, YANKONLY

def flush_undo_data():
    G.undo_stack_tail = None

def undo_push(src_idx, length, u_type):
    undo_text = None
    if u_type == UNDO_DEL or u_type == UNDO_DEL_CHAIN:
        undo_text = G.text[src_idx : src_idx + length]

    undo_entry = UndoObject(u_type, src_idx, length, undo_text)
    undo_entry.prev = G.undo_stack_tail
    G.undo_stack_tail = undo_entry
    G.modified_count += 1

def undo_pop():
    if not G.undo_stack_tail:
        G.status_buffer = "Already at oldest change"
        G.have_status_msg = 1
        return

    undo_entry = G.undo_stack_tail

    if undo_entry.u_type in (UNDO_DEL, UNDO_DEL_CHAIN):
        # restore deleted text
        # Since text_hole_make fills with spaces, let's just overwrite directly via concatenation
        # to avoid micropython item assignment indexing issues if length is somehow weird.
        # Actually it's easier to just concatenate the undo_text directly
        G.text = G.text[:undo_entry.start] + bytearray(undo_entry.undo_text) + G.text[undo_entry.start:]
        # adjust markers for restoration
        if G.dot >= undo_entry.start: G.dot += undo_entry.length
        if G.screenbegin >= undo_entry.start: G.screenbegin += undo_entry.length
        for i in range(len(G.mark)):
            if G.mark[i] >= undo_entry.start: G.mark[i] += undo_entry.length
    elif undo_entry.u_type in (UNDO_INS, UNDO_INS_CHAIN):
        # remove inserted text
        text_hole_delete(undo_entry.start, undo_entry.start + undo_entry.length - 1, NO_UNDO)

    repeat = undo_entry.u_type in (UNDO_DEL_CHAIN, UNDO_INS_CHAIN)

    if undo_entry.u_type in (UNDO_DEL, UNDO_INS):
        G.dot = undo_entry.start

    G.undo_stack_tail = undo_entry.prev
    G.modified_count -= 1

    if repeat:
        undo_pop()

def text_hole_make(p_idx, size):
    if size <= 0: return 0
    # MicroPython compatible bytearray insertion (concatenation)
    G.text = G.text[:p_idx] + bytearray(b' ' * size) + G.text[p_idx:]
    # adjust markers
    if G.dot >= p_idx: G.dot += size
    if G.screenbegin >= p_idx: G.screenbegin += size
    for i in range(len(G.mark)):
        if G.mark[i] >= p_idx: G.mark[i] += size
    return size

def text_hole_delete(p_idx, q_idx, undo):
    # p_idx through q_idx inclusive
    if p_idx > q_idx:
        p_idx, q_idx = q_idx, p_idx
    hole_size = q_idx - p_idx + 1

    if undo == ALLOW_UNDO: undo_push(p_idx, hole_size, UNDO_DEL)
    elif undo == ALLOW_UNDO_CHAIN: undo_push(p_idx, hole_size, UNDO_DEL_CHAIN)

    # MicroPython compatible bytearray deletion (concatenation)
    if p_idx < len(G.text):
        G.text = G.text[:p_idx] + G.text[q_idx + 1:]

    # adjust markers
    if G.dot > q_idx: G.dot -= hole_size
    elif G.dot > p_idx: G.dot = p_idx

    if G.screenbegin > q_idx: G.screenbegin -= hole_size
    elif G.screenbegin > p_idx: G.screenbegin = p_idx

    for i in range(len(G.mark)):
        if G.mark[i] > q_idx: G.mark[i] -= hole_size
        elif G.mark[i] > p_idx: G.mark[i] = p_idx

    return p_idx

def text_yank(p_idx, q_idx, dest):
    if p_idx > q_idx:
        p_idx, q_idx = q_idx, p_idx
    cnt = q_idx - p_idx + 1
    G.reg[dest] = G.text[p_idx : p_idx + cnt]
    return p_idx

def yank_delete(start, stop, dist, yf, undo):
    if start > stop:
        start, stop = stop, start

    if dist <= 0:
        # cannot cross NL
        if start < len(G.text) and G.text[start] == 10: # '\n'
            return start
        # find newline
        for i in range(start, stop + 1):
            if G.text[i] == 10:
                stop = i - 1
                break

    text_yank(start, stop, G.YDreg)

    if yf == YANKDEL:
        return text_hole_delete(start, stop, undo)
    return start

def string_insert(p_idx, s, undo):
    if isinstance(s, str):
        s = s.encode('utf-8')
    size = len(s)

    if undo == ALLOW_UNDO: undo_push(p_idx, size, UNDO_INS)
    elif undo == ALLOW_UNDO_CHAIN: undo_push(p_idx, size, UNDO_INS_CHAIN)

    # MicroPython compatible bytearray insertion (concatenation)
    G.text = G.text[:p_idx] + bytearray(s) + G.text[p_idx:]

    # adjust markers manually since we bypassed text_hole_make
    if G.dot >= p_idx: G.dot += size
    if G.screenbegin >= p_idx: G.screenbegin += size
    for i in range(len(G.mark)):
        if G.mark[i] >= p_idx: G.mark[i] += size

    return size

def stupid_insert(p_idx, c):
    # MicroPython compatible bytearray insertion
    if isinstance(c, str):
        c = ord(c)
    G.text = G.text[:p_idx] + bytearray([c]) + G.text[p_idx:]

    # adjust markers
    if G.dot >= p_idx: G.dot += 1
    if G.screenbegin >= p_idx: G.screenbegin += 1
    for i in range(len(G.mark)):
        if G.mark[i] >= p_idx: G.mark[i] += 1

    return 1

def init_text_buffer(fn):
    flush_undo_data()
    G.modified_count = 0
    G.last_modified_count = -1
    G.mark = [0] * 28
    G.text = bytearray()
    G.dot = 0
    G.screenbegin = 0

    if fn != G.current_filename:
        G.current_filename = fn

    try:
        with open(fn, "rb") as f:
            G.text = bytearray(f.read())
    except OSError:
        # empty buffer with dummy line
        G.text = bytearray(b'\n')

    if len(G.text) == 0:
        G.text = bytearray(b'\n')

def file_write(fn, first_idx, last_idx):
    if not fn: return -1
    try:
        with open(fn, "wb") as f:
            data = G.text[first_idx : last_idx + 1]
            f.write(data)
            return len(data)
    except OSError:
        return -1
