"""Dark, touch-optimized theme constants for the native GUI.

Mirrors the look of the web GUI (dark theme, large touch targets) so the field
experience is consistent. Colors are RGBA tuples in Kivy's 0..1 range.
"""

from kivy.metrics import dp

# --- Palette (dark theme) ---
BG = (0.07, 0.08, 0.10, 1)          # app background
SURFACE = (0.12, 0.13, 0.16, 1)     # cards / panels
SURFACE_ALT = (0.16, 0.17, 0.21, 1) # list rows, inputs
ACCENT = (0.15, 0.55, 0.95, 1)      # primary actions
ACCENT_DOWN = (0.10, 0.42, 0.78, 1) # primary pressed
DANGER = (0.85, 0.25, 0.25, 1)      # destructive actions / warnings
DANGER_DOWN = (0.68, 0.18, 0.18, 1)
OK = (0.20, 0.70, 0.40, 1)          # success / connected
WARN = (0.90, 0.65, 0.20, 1)        # processing / caution
MUTED = (0.55, 0.58, 0.64, 1)       # secondary text / inactive

TEXT = (0.92, 0.93, 0.95, 1)
TEXT_DIM = (0.62, 0.65, 0.70, 1)

# --- Sizing (touch-first) ---
BTN_HEIGHT = dp(54)        # minimum comfortable touch target
ROW_HEIGHT = dp(48)
INPUT_HEIGHT = dp(46)
PAD = dp(10)
GAP = dp(8)
RADIUS = dp(8)

TITLE_FS = '20sp'
SECTION_FS = '17sp'
BODY_FS = '15sp'
SMALL_FS = '13sp'
