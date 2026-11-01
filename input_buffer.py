from collections import deque
from dataclasses import dataclass
from pprint import pformat
from threading import Lock
from typing import Literal

from movement_keys import MovementKey, LeftClick, MovementKeyPairs, SHOOT_BUTTON

@dataclass(frozen=True, kw_only=True)
class InputEvent:

    input: MovementKey | LeftClick
    input_triggered: bool
    timestamp: float

@dataclass(frozen=True, kw_only=True)
class CounterStrafeEvent:

    first_key: MovementKey
    second_key: MovementKey

    first_key_trigger_timestamp: float
    first_key_release_timestamp: float

    second_key_trigger_timestamp: float
    second_key_release_timestamp: float

    mouse_click_timestamp: float

class InputBuffer:

    def __init__(self):
        self._lock = Lock()
        self._last_key_states: dict[MovementKey, bool] = {}
        self._queue: deque[InputEvent] = deque(maxlen=5)

    def get_counter_strafe_event(self) -> CounterStrafeEvent | None:
        with self._lock:

            if self._check_valid_cs_event():

                popped_input_events = tuple(self._queue.popleft() for _ in range(5))
                shoot_button_timestamp = -1
                keyboard_event_dict = {}
                for i in range(5):
                    input_event = popped_input_events[i]
                    if input_event.input == SHOOT_BUTTON:
                        shoot_button_timestamp = input_event.timestamp
                        continue
                    if input_event.input not in keyboard_event_dict.keys():
                        keyboard_event_dict[input_event.input] = [input_event.timestamp]
                    else:
                        keyboard_event_dict[input_event.input].append(input_event.timestamp)

                first_key_triggered = popped_input_events[0].input
                second_key_triggered = MovementKeyPairs[first_key_triggered]

                cs_event = CounterStrafeEvent(
                    first_key=first_key_triggered,
                    second_key=second_key_triggered,
                    first_key_trigger_timestamp=keyboard_event_dict[first_key_triggered][0],
                    first_key_release_timestamp=keyboard_event_dict[first_key_triggered][1],
                    second_key_trigger_timestamp=keyboard_event_dict[second_key_triggered][0],
                    second_key_release_timestamp=keyboard_event_dict[second_key_triggered][1],
                    mouse_click_timestamp=shoot_button_timestamp
                )
                return cs_event

        return None


    def register_key_action(self, key: MovementKey, key_pressed: bool, action_timestamp: float):
        if key in self._last_key_states and self._last_key_states[key] == key_pressed:
            return
        self._register_action(key, key_pressed, action_timestamp)

    def register_click_action(self, action_timestamp: float):
        self._register_action(SHOOT_BUTTON, True, action_timestamp)

    def _register_action(self, key: MovementKey | LeftClick, input_triggered: bool, timestamp: float):
        event = InputEvent(
            input=key,
            input_triggered=input_triggered,
            timestamp=timestamp
        )
        with self._lock:
            self._queue.append(event)
            if key in MovementKeyPairs.keys():
                self._last_key_states[key] = input_triggered

    def _check_valid_cs_event(self) -> bool:
        if len(self._queue) != 5:
            return False

        if self._queue[0].input not in MovementKeyPairs.keys() or not self._queue[0].input_triggered:
            return False

        key_char_actions = {}

        for i in range(5):
            curr_input = self._queue[i]
            if curr_input.input == SHOOT_BUTTON:
                if len(key_char_actions) != 2:
                    return False
                continue
            if curr_input.input not in key_char_actions.keys():
                key_char_actions[curr_input.input] = [curr_input.input_triggered]
            else:
                key_char_actions[curr_input.input].append(curr_input.input_triggered)


        keys_pressed = tuple(key_char_actions.keys())
        if len(keys_pressed) != 2:
            return False
        if MovementKeyPairs[keys_pressed[0]] != keys_pressed[1]:
            return False

        for input_key, action_sequence in key_char_actions.items():
            action_set = set(action_sequence)
            if len(action_set) == 1 and len(action_sequence) > 1:
                repeated_action = "trigger" if action_set.pop() else "release"
                raise RuntimeError(f"Input buffer contains two consecutive trigger or release events for the same key. Key: {input_key}, Repeated action: {repeated_action}. Buffer: {pformat(self._queue)}")
            if len(action_set) != 2:
                return False
            if action_sequence != [True, False]:
                return False

        timestamps = [input.timestamp for input in self._queue]
        if sorted(timestamps) != timestamps:
            raise RuntimeError(f"Input buffer contains out-of-order inputs: {pformat(self._queue)}")

        return True


        




