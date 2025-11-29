import threading
import time
from typing import Optional

from pynput import keyboard, mouse

from classifier import MovementClassifier, ShotClassification

from config import MOVE_KEYS, VOLUME_KEYS, TOGGLE_OVERLAY, TERMINATE_PROGRAM, INCREASE_SIZE, DECREASE_SIZE

from config import GOOD_FILE_PATH, BAD_FILE_PATH, OVERLAP_FILE_PATH

from cpp_sound import SoundPlayer

import time


class InputListener:
    def __init__(self, overlay: "Overlay") -> None:
        self.overlay = overlay
        self.classifier = MovementClassifier()
        self._lock = threading.Lock()
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        # only wav files supported:
        self.player = SoundPlayer({
            "good": str(GOOD_FILE_PATH),
            "bad": str(BAD_FILE_PATH),
            "overlap": str(OVERLAP_FILE_PATH),
        })
        # set default volumes
        self.player.set_max_volume(2.5)
        self.player.set_min_volume(0)
        self.player.set_master_volume(1)
        self.player.set_volume("good", 0.3)
        self.player.set_volume("bad", 0.3)
        self.player.set_volume("overlap", 0.6)

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

    def _on_key_press(self, key: keyboard.Key) -> None:
        if key == getattr(keyboard.Key, TOGGLE_OVERLAY.lower(), None):
            self.overlay.toggle_visibility()
            return

        if key == getattr(keyboard.Key, TERMINATE_PROGRAM.lower(), None):
            self.stop()
            self.overlay.terminate()
            return

        char_key = None
        vk = None

        if isinstance(key, keyboard.KeyCode):
            vk = key.vk
            char_key = key.char

        # ------------ Handle normal char keys ------------
        if char_key:
            upper_char = char_key.upper()
            timestamp = time.time() * 1000.0

            if upper_char in MOVE_KEYS.values():
                with self._lock:
                    self.classifier.on_press(upper_char, timestamp)

            lower_char = char_key.lower()

            # Normal single-character volume keys
            if lower_char in VOLUME_KEYS.values():
                self._handle_volume(lower_char)
                return

        # ------------ Handle NUMPAD special keys via VK codes ------------
        if vk is not None:
            NUMPAD_KEY_MAP = {
                107: "kp+",    # VK_ADD
                109: "kp-",    # VK_SUBTRACT
                97:  "kp1",
                98:  "kp2",
                100: "kp4",
                101: "kp5",
                103: "kp7",
                104: "kp8",
            }

            if vk in NUMPAD_KEY_MAP:
                name = NUMPAD_KEY_MAP[vk]

                if name in VOLUME_KEYS.values():
                    self._handle_volume(name)
                    return

    def _on_key_release(self, key: keyboard.Key) -> None:
        timestamp = time.time() * 1000.0
        char: Optional[str] = None
        try:
            char = key.char
        except AttributeError:
            char = None

        if char:
            upper_char = char.upper()
            if upper_char in MOVE_KEYS.values():
                with self._lock:
                    self.classifier.on_release(upper_char, timestamp)

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if button != mouse.Button.left:
            return
        current_time = time.time() * 1000.0
        if pressed:
            with self._lock:
                base_result = self.classifier.classify_shot(current_time)

            final_result = self._build_classification(
                base_result, current_time)

            print(final_result.label)
            if final_result.label == "Counter‑strafe":
                self.player.play("good")
            if final_result.label == "Bad":
                self.player.play("bad")
            if final_result.label == "Overlap":
                self.player.play("overlap")

            self.overlay.update_result(final_result)

    def stop(self) -> None:
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None

    def _handle_volume(self, key_name: str) -> None:
        if key_name == VOLUME_KEYS["volume_up"]:
            self.player.master_volume_up()
        elif key_name == VOLUME_KEYS["volume_down"]:
            self.player.master_volume_down()
        elif key_name == VOLUME_KEYS["bad_volume_up"]:
            self.player.volume_up("bad")
        elif key_name == VOLUME_KEYS["bad_volume_down"]:
            self.player.volume_down("bad")
        elif key_name == VOLUME_KEYS["overlap_volume_up"]:
            self.player.volume_up("overlap")
        elif key_name == VOLUME_KEYS["overlap_volume_down"]:
            self.player.volume_down("overlap")
        elif key_name == VOLUME_KEYS["good_volume_up"]:
            self.player.volume_up("good")
        elif key_name == VOLUME_KEYS["good_volume_down"]:
            self.player.volume_down("good")

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
