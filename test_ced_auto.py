import sys
import pygame
import threading
import time

# Inject Pygame Events Programmatically
def run_automation():
    import gint
    import ced

    # We need to wait for `ced.main()` to start rendering
    time.sleep(1)

    def post_key(k):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': k}))
        pygame.event.post(pygame.event.Event(pygame.KEYUP, {'key': k}))
        time.sleep(0.1)

    def post_touch(x, y):
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (x, y), 'button': 1}))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (x, y), 'button': 1}))
        time.sleep(0.1)

    # 1. Initial State
    pygame.image.save(gint.vram, "screenshot_01_initial.png")

    # 2. Enter Insert Mode 'i' -> cinput KBD normally requires touch, but we added hardware key support
    # Actually 'i' is typed via OSK or hardware. In our simulator gint.py, keys are mapped.
    # Let's just touch the top left (KBD button) to open KBD
    post_touch(10, 15)
    time.sleep(0.5)
    pygame.image.save(gint.vram, "screenshot_02_keyboard.png")

    # Let's type via OSK (we'll tap 'i' using coordinates).
    # In cinput.py qwerty layout: row 1, col 7 -> 'i'
    # Tab H = 30. Grid Y = 528 - 260 + 30 = 298.
    # Row H = 45.
    # 'i' is in row 1, which means Y = 298 + 45 = 343.
    # 'i' is the 8th key in row 1 (0-indexed 7). X = 7 * (320//10) + 16 = 7*32 + 16 = 240
    post_touch(240, 360) # roughly center of 'i'
    pygame.image.save(gint.vram, "screenshot_03_insert_mode.png")

    # 3. Type "hello" using OSK
    # 'h' (row 2, col 5) -> Y=298+45*2=388, X=5*32+16=176
    post_touch(176, 400)
    # 'e' (row 1, col 2) -> Y=343, X=2*32+16=80
    post_touch(80, 360)
    # 'l' (row 2, col 8) -> Y=388, X=8*32+16=272
    post_touch(272, 400)
    post_touch(272, 400)
    # 'o' (row 1, col 8) -> Y=343, X=8*32+16=272
    post_touch(272, 360)
    pygame.image.save(gint.vram, "screenshot_04_typed_hello.png")

    # 4. Exit Insert Mode (Top right touch isn't ESC. Let's use physical F1/Exit mapped in gint)
    post_key(pygame.K_ESCAPE) # mapped to KEY_EXIT in gint
    time.sleep(0.5)

    # 5. Open Colon Mode (shift + ; on physical keyboard, or OSK)
    # Let's use physical keys for speed
    # We don't have colon mapped directly as a single physical key in gint simulator,
    # we can tap OSK SYM tab -> ':'
    post_touch(160, 280) # Tap 'Sym' tab
    time.sleep(0.5)
    # ':' is row 2, col 6 -> Y=388, X=6*(320/10)=192+16=208
    post_touch(208, 400)
    time.sleep(0.5)
    pygame.image.save(gint.vram, "screenshot_05_colon_mode.png")

    # 6. Quit out via the new Menu
    post_key(pygame.K_ESCAPE) # Ensure Normal Mode
    time.sleep(0.5)
    post_touch(10, 15) # Tap top left to open menu
    time.sleep(0.5)
    pygame.image.save(gint.vram, "screenshot_06_menu.png")

    # Tap "Quit"
    # Picker row height = 50, Header = 40. "Quit" is index 4 (0-based)
    # Y = 40 + 4 * 50 + 25 = 40 + 200 + 25 = 265
    post_touch(160, 265)
    time.sleep(0.5)

    # Send a fallback exit event just in case
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))

# Run automation in background thread
t = threading.Thread(target=run_automation)
t.daemon = True
t.start()

import ced
