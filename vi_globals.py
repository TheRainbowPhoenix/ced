# Ported global state for vi
class ViGlobals:
    def __init__(self):
        self.text = bytearray()
        self.text_size = 10240
        self.dot = 0  # index into text
        self.screenbegin = 0 # index into text

        self.cmd_mode = 0  # 0=command, 1=insert, 2=replace, 3=colon
        self.modified_count = 0
        self.last_modified_count = -1

        self.vi_setops = 1 | 2 | 4  # autoindent, showmatch, ignorecase
        self.readonly_mode = 0

        self.crow = 0
        self.ccol = 0
        self.offset = 0

        self.have_status_msg = 0
        self.status_buffer = ""
        self.current_filename = None

        self.tabstop = 8
        self.last_forward_char = ''
        self.erase_char = '\x08'
        self.last_input_char = ''

        self.cmdcnt = 0

        # Yank/Mark
        self.YDreg = 26
        self.Ureg = 27
        self.reg = [None] * 28
        self.mark = [0] * 28

        # Undo stack
        self.undo_stack_tail = None

        # Search
        self.last_search_pattern = ""

        # Gint specific
        self.rows = 0 # Calculated from DHEIGHT
        self.columns = 0 # Calculated from DWIDTH (approximate)

G = ViGlobals()

# Constants
SCREEN_W = 320
SCREEN_H = 528

FORWARD = 1
BACK = -1
LIMITED = 0
FULL = 1
YANKONLY = False
YANKDEL = True

UNDO_INS = 0
UNDO_DEL = 1
UNDO_INS_CHAIN = 2
UNDO_DEL_CHAIN = 3

NO_UNDO = 0
ALLOW_UNDO = 1
ALLOW_UNDO_CHAIN = 2

class UndoObject:
    def __init__(self, u_type, start, length, text=None):
        self.prev = None
        self.start = start
        self.length = length
        self.u_type = u_type
        self.undo_text = text
