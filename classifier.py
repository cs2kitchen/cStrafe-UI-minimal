from dataclasses import dataclass
from enum import Enum

from input_buffer import CounterStrafeEvent

class CounterStrafeType(Enum):
    EARLY_RELEASE = "Early Release"
    LATE_RELEASE = "Late Release"
    BAD = "Bad"

@dataclass(frozen=True, kw_only=True)
class CounterStrafeStatistics:

    overlap_duration: float
    cs_key_hold_duration: float
    shot_delay: float

def generate_counter_strafe_stats(event: CounterStrafeEvent) -> CounterStrafeStatistics:

    overlap_duration = event.second_key_trigger_timestamp - event.first_key_release_timestamp
    cs_key_hold_duration = event.second_key_release_timestamp - event.second_key_trigger_timestamp
    shot_delay = event.mouse_click_timestamp - event.second_key_trigger_timestamp
    return CounterStrafeStatistics(
        overlap_duration=overlap_duration,
        cs_key_hold_duration=cs_key_hold_duration,
        shot_delay=shot_delay
    )

def classify_counter_strafe(stats: CounterStrafeStatistics) -> CounterStrafeType:

    if not 40 < stats.cs_key_hold_duration < 120 or stats.shot_delay > 600 or abs(stats.overlap_duration) > 60:
        return CounterStrafeType.BAD

    if stats.overlap_duration >= 0:
        return CounterStrafeType.EARLY_RELEASE
    else:
        return CounterStrafeType.LATE_RELEASE
