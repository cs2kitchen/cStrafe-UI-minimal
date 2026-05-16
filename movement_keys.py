"""
Defaults:
    FORWARD  = 'W'
    BACKWARD = 'S'
    LEFT     = 'A'
    RIGHT    = 'D'
These defaults match the conventional WASD movement keys. If your keyboard or
preferences differ (for example, using ESDF), update the
constants accordingly. The application will reload these values on start and
use them for both input listening and movement classification.
Note:
    Only single‐character alphanumeric keys are supported. Special keys like
    arrow keys are not guaranteed to work because the underlying input
    library may not provide a `.char` attribute for non‐alphanumeric keys.
"""

# Directional movement key bindings
# Change the binds below if you don't use WASD
FORWARD: str = 'W'
BACKWARD: str = 'S'
LEFT: str = 'A'
RIGHT: str = 'D'

# Default for normal users
SHOOT_BUTTON = "left"

# Left handed users can change it to:
#SHOOT_BUTTON = "right"
