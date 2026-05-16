import threading
import time
from typing import Optional

from pynput import keyboard, mouse

from classifier import MovementClassifier, ShotClassification

try:
    # Attempt to import user configured keys. The movement_keys module defines
    # FORWARD, BACKWARD, LEFT and RIGHT constants. If it cannot be imported or
    # does not define the expected attributes, defaults will be used later.
    from movement_keys import FORWARD, BACKWARD, LEFT, RIGHT  # type: ignore
except Exception:
    # Provide dummy values here; real defaults are set below in InputListener
    FORWARD = 'E'  # type: ignore
    BACKWARD = 'D'  # type: ignore
    LEFT = 'S'  # type: ignore
    RIGHT = 'F'  # type: ignore

try:
    from movement_keys import SHOOT_BUTTON  # type: ignore
except Exception:
    SHOOT_BUTTON = 'left'  # type: ignore

class InputListener:
    def __init__(self, overlay: "Overlay") -> None:
        self.overlay = overlay
        # Determine movement keys from configuration. Use uppercase to
        # standardise comparisons. Fallback to defaults if the values are
        # missing or invalid.
        try:
            forward = str(FORWARD)
            backward = str(BACKWARD)
            left = str(LEFT)
            right = str(RIGHT)
        except Exception:
            forward, backward, left, right = 'W', 'S', 'A', 'D'
        # Ensure single characters and normalise to uppercase
        forward = (forward[0] if forward else 'W').upper()
        backward = (backward[0] if backward else 'S').upper()
        left = (left[0] if left else 'A').upper()
        right = (right[0] if right else 'D').upper()
        self._movement_keys = {forward, backward, left, right}
        self._shoot_button = self._parse_shoot_button(SHOOT_BUTTON)

        # Initialise classifier with the configured key pairs
        try:
            self.classifier = MovementClassifier(vertical_keys=(forward, backward), horizontal_keys=(left, right))
        except Exception:
            # Fallback to default WASD if invalid configuration is provided
            self.classifier = MovementClassifier()
        self._lock = threading.Lock()
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._mouse_listener: Optional[mouse.Listener] = None

    def start(self) -> None:
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._keyboard_listener.start()
        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
        )
        self._mouse_listener.start()
        
    def _parse_shoot_button(self, value: object) -> mouse.Button:
        button = str(value).strip().lower()

        if button in {'right', 'mouse.right', 'm2', '2'}:
            return mouse.Button.right

        if button in {'middle', 'mouse.middle', 'm3', '3'}:
            return mouse.Button.middle

        return mouse.Button.left

    def _on_key_press(self, key: keyboard.Key) -> None:
        if key == keyboard.Key.f6:
            self.overlay.toggle_visibility()
            return
        if key == keyboard.Key.f8:
            self.stop()
            self.overlay.terminate()
            return
        char_key: Optional[str] = None
        try:
            char_key = key.char
        except AttributeError:
            char_key = None
        if char_key == "=":
            self.overlay.increase_size()
            return
        if char_key == "-":
            self.overlay.decrease_size()
            return
        timestamp = time.time() * 1000.0
        char: Optional[str] = None
        try:
            char = key.char
        except AttributeError:
            char = None
        if char:
            upper_char = char.upper()
            if upper_char in self._movement_keys:
                with self._lock:
                    self.classifier.on_press(upper_char, timestamp)

    def _on_key_release(self, key: keyboard.Key) -> None:
        timestamp = time.time() * 1000.0
        char: Optional[str] = None
        try:
            char = key.char
        except AttributeError:
            char = None
        if char:
            upper_char = char.upper()
            if upper_char in self._movement_keys:
                with self._lock:
                    self.classifier.on_release(upper_char, timestamp)

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if button != self._shoot_button:
            return

        if not pressed:
            return

        current_time = time.time() * 1000.0

        with self._lock:
            base_result = self.classifier.classify_shot(current_time)

        final_result = self._build_classification(base_result, current_time)
        self.overlay.update_result(final_result)

    def stop(self) -> None:
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None

    def _build_classification(self, base: ShotClassification, shot_time: float) -> ShotClassification:
        if base.label == "Overlap":
            return ShotClassification(label="Overlap", overlap_time=base.overlap_time)
        if base.label == "Counter‑strafe":
            cs_time = base.cs_time
            shot_delay = base.shot_delay
            if cs_time is not None and shot_delay is not None:
                if shot_delay > 230.0 or (cs_time > 215.0 and shot_delay > 215.0):
                    return ShotClassification(label="Bad", cs_time=cs_time, shot_delay=shot_delay)
                return ShotClassification(label="Counter‑strafe", cs_time=cs_time, shot_delay=shot_delay)
            return ShotClassification(label="Bad")
        return ShotClassification(label="Bad")