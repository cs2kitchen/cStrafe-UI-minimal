import json
from pathlib import Path
from pprint import pprint
CONFIG_FILE = Path(__file__).parent / "config.json"

default_config = {
    "move_up": "W",
    "move_down": "S",
    "move_left": "A",
    "move_right": "D",
    "toggle_overlay": "F6",
    "terminate_program": "F8",
    "increase_size": "=",
    "decrease_size": "-",
    "good_file_name": "sounds/good.wav",
    "bad_file_name": "sounds/bad.wav",
    "overlap_file_name": "sounds/overlap.wav",
    "master_volume_up": "kp+",
    "master_volume_down": "kp-",
    "bad_volume_up": "kp1",
    "bad_volume_down": "kp2",
    "overlap_volume_up": "kp4",
    "overlap_volume_down": "kp5",
    "good_volume_up": "kp7",
    "good_volume_down": "kp8",
}

try:
    with open(CONFIG_FILE, "r") as f:
        config_data = json.load(f)
except FileNotFoundError:
    config_data = default_config
    with open(CONFIG_FILE, "w") as f:
        json.dump(default_config, f, indent=4)

MOVE_KEYS = {
    "up": config_data["move_up"].upper(),
    "down": config_data["move_down"].upper(),
    "left": config_data["move_left"].upper(),
    "right": config_data["move_right"].upper()
}

VOLUME_KEYS = {
    "volume_up": config_data["master_volume_up"].lower(),
    "volume_down": config_data["master_volume_down"].lower(),
    "bad_volume_up": config_data["bad_volume_up"].lower(),
    "bad_volume_down": config_data["bad_volume_down"].lower(),
    "overlap_volume_up": config_data["overlap_volume_up"].lower(),
    "overlap_volume_down": config_data["overlap_volume_down"].lower(),
    "good_volume_up": config_data["good_volume_up"].lower(),
    "good_volume_down": config_data["good_volume_down"].lower(),
}

TOGGLE_OVERLAY = config_data["toggle_overlay"]
TERMINATE_PROGRAM = config_data["terminate_program"]
INCREASE_SIZE = config_data["increase_size"]
DECREASE_SIZE = config_data["decrease_size"]
GOOD_FILE_PATH = Path(__file__).parent / config_data["good_file_name"]
BAD_FILE_PATH = Path(__file__).parent / config_data["bad_file_name"]
OVERLAP_FILE_PATH = Path(__file__).parent / config_data["overlap_file_name"]