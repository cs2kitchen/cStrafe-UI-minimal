import csv
import threading
import time
from pathlib import Path
from typing import Optional, Tuple

from pynput import keyboard, mouse

from classifier import CounterStrafeStatistics, CounterStrafeType, classify_counter_strafe, generate_counter_strafe_stats
from input_buffer import InputBuffer
from cs_types import CounterStrafeEvent

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
    def __init__(self, overlay: "Overlay", output_path: Optional[Path] = None) -> None:
        self.overlay = overlay
        self._output_path = output_path
        self._output_lock = threading.Lock()
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
        self._input_buffer = InputBuffer()

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
                    self._input_buffer.register_key_action(upper_char, True, timestamp)

        self._post_input_event()

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
                    self._input_buffer.register_key_action(upper_char, False, timestamp)


        self._post_input_event()


    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if button != self._shoot_button:
            return

        if not pressed:
            return

        current_time = time.time() * 1000.0

        with self._lock:
            self._input_buffer.register_click_action(current_time)

        self._post_input_event()

    def stop(self) -> None:
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None

    def _post_input_event(self):
        cs_event = self._input_buffer.get_counter_strafe_event()
        if cs_event:
            cs_type, cs_stats = self._build_classification(cs_event)
            self._write_classification(cs_type, cs_stats)
            self.overlay.update_result(cs_type, cs_stats)

    def _write_classification(
        self,
        cs_type: CounterStrafeType,
        cs_stats: CounterStrafeStatistics,
    ) -> None:
        if self._output_path is None:
            return

        fieldnames = (
            "classification",
            "overlap_duration",
            "cs_key_hold_duration",
            "shot_delay",
        )
        with self._output_lock:
            has_data = self._output_path.exists() and self._output_path.stat().st_size > 0
            with self._output_path.open("a", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                if not has_data:
                    writer.writeheader()
                writer.writerow(
                    {
                        "classification": cs_type.value,
                        "overlap_duration": cs_stats.overlap_duration,
                        "cs_key_hold_duration": cs_stats.cs_key_hold_duration,
                        "shot_delay": cs_stats.shot_delay,
                    }
                )

    def _build_classification(self, cs_event: CounterStrafeEvent) -> Tuple[CounterStrafeType, CounterStrafeStatistics]:
        stats = generate_counter_strafe_stats(cs_event)
        classification = classify_counter_strafe(stats)
        return classification, stats