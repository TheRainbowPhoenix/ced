import sys
import os

# Create a mock module directly instead of a class
import types
gint = types.ModuleType('gint')

gint.DWIDTH = 320
gint.DHEIGHT = 528
gint.C_WHITE = 1
gint.C_BLACK = 2
gint.C_LIGHT = 3
gint.C_DARK = 4
gint.C_RED = 5
gint.C_GREEN = 6
gint.C_BLUE = 7
gint.C_NONE = 8
gint.C_GRAY = 9
gint.C_MAGENTA = 10

gint.KEY_LEFT = 101
gint.KEY_RIGHT = 102
gint.KEY_UP = 103
gint.KEY_DOWN = 104
gint.KEY_EXE = 105
gint.KEY_EXIT = 106
gint.KEY_DEL = 107
gint.KEY_KBD = 108

gint.KEYEV_NONE = 0
gint.KEYEV_DOWN = 1
gint.KEYEV_UP = 2
gint.KEYEV_HOLD = 3
gint.KEYEV_TOUCH_DOWN = 4
gint.KEYEV_TOUCH_UP = 5

gint.DTEXT_LEFT = 1
gint.DTEXT_CENTER = 2
gint.DTEXT_RIGHT = 3
gint.DTEXT_TOP = 4
gint.DTEXT_MIDDLE = 5
gint.DTEXT_BOTTOM = 6

def _dsize(text, font): return len(text)*8, 12
gint.dsize = _dsize
gint.dclear = lambda col: None
gint.drect = lambda x1, y1, x2, y2, col: None
gint.dline = lambda x1, y1, x2, y2, col: None
gint.drect_border = lambda *a: None
gint.dtext = lambda *a: None
gint.dtext_opt = lambda *a: None
gint.dwindow_set = lambda *a: None
gint.dupdate = lambda: None
gint.clearevents = lambda: None

# we need to simulate breaking out of the loop
# in main, there's no `running = False` for KEY_EXIT, it uses `c.do_cmd(27)`
# let's just mock `pollevent` to raise an exception to exit the loop
class ExitLoop(Exception): pass

def _pollevent():
    raise ExitLoop()

gint.pollevent = _pollevent

sys.modules['gint'] = gint

cinput = types.ModuleType('cinput')
class MockKeyboard:
    def __init__(self, *args, **kwargs):
        self.visible = False
        self.y = 300
    def draw(self): pass
    def update(self, ev): return None
cinput.Keyboard = MockKeyboard
sys.modules['cinput'] = cinput

try:
    import ced
    try:
        ced.main()
    except ExitLoop:
        pass
    print("Main loop executed successfully")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
