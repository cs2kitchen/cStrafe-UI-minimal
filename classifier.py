from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class AxisState:
    keys: Tuple[str, str]
    held_keys: set = field(default_factory=set)
    press_times: dict = field(default_factory=dict)
    cs_release_key: Optional[str] = None
    cs_release_time: Optional[float] = None
    cs_press_key: Optional[str] = None
    cs_press_time: Optional[float] = None
    overlap_start_time: Optional[float] = None
    micro_candidate_duration: Optional[float] = None

    def on_press(self, key: str, timestamp: float) -> None:
        other = self.keys[0] if key == self.keys[1] else self.keys[1]
        self.held_keys.add(key)
        self.press_times[key] = timestamp
        if other in self.held_keys and self.overlap_start_time is None:
            self.overlap_start_time = timestamp
        if self.cs_release_key == other and self.cs_press_time is None:
            self.cs_press_key = key
            self.cs_press_time = timestamp
            self.micro_candidate_duration = None
        self.micro_candidate_duration = None

    def on_release(self, key: str, timestamp: float) -> None:
        press_time = self.press_times.get(key)
        if press_time is not None:
            duration = timestamp - press_time
            if duration < 80:
                self.micro_candidate_duration = duration
        self.held_keys.discard(key)
        self.cs_release_key = key
        self.cs_release_time = timestamp
        self.cs_press_key = None
        self.cs_press_time = None

    def classify_shot(self, shot_time: float) -> Tuple[str, Optional[float], Optional[float]]:
        if self.overlap_start_time is not None:
            if not (
                self.cs_press_time is not None
                and self.cs_release_time is not None
                and self.cs_release_time > self.overlap_start_time
                and self.cs_press_time > self.cs_release_time
            ):
                overlap_time = shot_time - self.overlap_start_time
                self._reset()
                return "Overlap", overlap_time, None
        if (
            self.cs_press_time is not None
            and self.cs_release_time is not None
            and self.cs_press_time > self.cs_release_time
        ):
            cs_time = self.cs_press_time - self.cs_release_time
            shot_delay = shot_time - self.cs_press_time
            self._reset()
            return "Counter‑strafe", cs_time, shot_delay
        self._reset()
        return "Bad", None, None

    def _reset(self) -> None:
        self.cs_release_key = None
        self.cs_release_time = None
        self.cs_press_key = None
        self.cs_press_time = None
        self.overlap_start_time = None
        self.micro_candidate_duration = None


@dataclass
class ShotClassification:
    label: str
    cs_time: Optional[float] = None
    shot_delay: Optional[float] = None
    overlap_time: Optional[float] = None

    def to_display_string(self) -> str:
        lines = [f"Classification: {self.label}"]
        if (
            self.label == "Counter‑strafe"
            and self.cs_time is not None
            and self.shot_delay is not None
        ):
            lines.append(f"CS time: {self.cs_time:.0f} ms")
            lines.append(f"Shot delay: {self.shot_delay:.0f} ms")
        elif self.label == "Overlap" and self.overlap_time is not None:
            lines.append(f"Overlap: {self.overlap_time:.0f} ms")
        elif (
            self.label == "Bad"
            and self.cs_time is not None
            and self.shot_delay is not None
        ):
            lines.append(f"CS time: {self.cs_time:.0f} ms")
            lines.append(f"Shot delay: {self.shot_delay:.0f} ms")
        return "\n".join(lines)


class MovementClassifier:
    """
    Classifies player movement based on key presses and releases.

    By default the classifier tracks the conventional vertical (forward/backward)
    and horizontal (left/right) movement keys. Custom key bindings can be
    supplied to accommodate different keyboard layouts or player preferences.
    """

    def __init__(self, *, vertical_keys: Tuple[str, str] = ("W", "S"), horizontal_keys: Tuple[str, str] = ("A", "D")) -> None:
        v_keys = tuple(key.upper() for key in vertical_keys)
        h_keys = tuple(key.upper() for key in horizontal_keys)
        if len(set(v_keys)) != 2:
            raise ValueError(f"vertical_keys must contain two distinct keys, got {vertical_keys}")
        if len(set(h_keys)) != 2:
            raise ValueError(f"horizontal_keys must contain two distinct keys, got {horizontal_keys}")
        self.vertical = AxisState(keys=v_keys)
        self.horizontal = AxisState(keys=h_keys)

    def on_press(self, key: str, timestamp: float) -> None:
        if key in self.vertical.keys:
            self.vertical.on_press(key, timestamp)
        elif key in self.horizontal.keys:
            self.horizontal.on_press(key, timestamp)

    def on_release(self, key: str, timestamp: float) -> None:
        if key in self.vertical.keys:
            self.vertical.on_release(key, timestamp)
        elif key in self.horizontal.keys:
            self.horizontal.on_release(key, timestamp)

    def classify_shot(self, shot_time: float) -> ShotClassification:
        v_label, v_val1, v_val2 = self.vertical.classify_shot(shot_time)
        h_label, h_val1, h_val2 = self.horizontal.classify_shot(shot_time)
        negativity = {
            "Overlap": 2,
            "Counter‑strafe": 1,
            "Bad": 0,
        }
        v_score = negativity.get(v_label, 0)
        h_score = negativity.get(h_label, 0)
        if v_score > h_score:
            label, val1, val2 = v_label, v_val1, v_val2
        elif h_score > v_score:
            label, val1, val2 = h_label, h_val1, h_val2
        else:
            if v_val1 is not None and h_val1 is not None:
                if v_val1 >= h_val1:
                    label, val1, val2 = v_label, v_val1, v_val2
                else:
                    label, val1, val2 = h_label, h_val1, h_val2
            elif v_val1 is not None:
                label, val1, val2 = v_label, v_val1, v_val2
            else:
                label, val1, val2 = h_label, h_val1, h_val2
        if label == "Counter‑strafe":
            return ShotClassification(label=label, cs_time=val1, shot_delay=val2)
        elif label == "Overlap":
            return ShotClassification(label=label, overlap_time=val1)
        return ShotClassification(label=label)