# cStrafe UI by CS2Kitchen

This is a lightweight training tool to help players practice counter-strafing in CS2. It listens for movement-key press/release events and a configured mouse button, then classifies a shot after a detected change between opposing movement keys. The always-on-top overlay shows the classification and timing measurements in milliseconds.

![UI Preview](images/strafe_ui_2.gif)


## Installation

1. Install Python 3.13 or a recent compatible Python version.
2. Install the required dependency:

   ```bash
   pip install pynput
   ```

   Tkinter is also required for the overlay and is included with most standard Python installations. If your Python installation does not include it, install or enable its Tk support using the instructions for your Python distribution.

3. Download or clone this repository, then run the program from the project directory:

   ```bash
   python main.py
   ```

   To save each classification and its timing statistics as CSV, provide an output filepath:

   ```bash
   python main.py --output "counter-strafe-stats.csv"
   ```

   The CSV is appended to across runs and can be loaded with `pandas.read_csv("counter-strafe-stats.csv")`. The durations are in milliseconds. Its columns are:

   | Column | Meaning |
   |--------|---------|
   | `classification` | `Early Release`, `Late Release`, or `Bad`. |
   | `overlap_duration` | Time from releasing the first movement key to pressing its opposite. Positive values mean a gap; negative values mean the keys overlapped. |
   | `cs_key_hold_duration` | Time the opposite movement key was held before it was released. |
   | `shot_delay` | Time from pressing the opposite movement key to firing. |

## Configuration

Movement keys default to WASD. To change them, edit `FORWARD`, `BACKWARD`, `LEFT`, and `RIGHT` in `movement_keys.py` before starting the application. Each binding should be a single character. Set `SHOOT_BUTTON` in the same file to `"left"`, `"right"`, or `"middle"` to choose which mouse button registers a shot.

## Usage

When the application is running, an always-on-top overlay appears over your desktop. Drag it by its header to reposition it. Use windowed or borderless-windowed game mode; exclusive fullscreen may cover the overlay. Each recognized shot displays the classification, signed key overlap, opposite-key hold duration, and shot delay. Valid `Early Release` and `Late Release` results use a green background; `Bad` results use red. You can control the overlay with these keys:

- **F6** – hide or show the overlay without quitting.
- **F8** – exit the program.
- **=** – increase the size of the overlay text.
- **-** – decrease the size of the overlay text.

## Classification Rules

The tool evaluates a detected sequence of two opposing movement keys followed by a shot. A result is `Bad` if any of these timing limits are missed: the opposite key is held for more than 40 ms and less than 120 ms, the shot occurs more than 60 ms and less than 600 ms after pressing that key, and the absolute overlap/gap is no more than 60 ms. The key-hold and shot-delay bounds are strict; values exactly at their limits are `Bad`.

Sequences within those limits are labeled according to the signed overlap:

| Label | Description |
|-------|-------------|
| **Early Release** | The first key was released at or before the opposite key was pressed, so `overlap_duration` is zero or positive. |
| **Late Release** | The opposite key was pressed before the first key was released, so the keys overlapped and `overlap_duration` is negative. |
| **Bad** | A detectable opposing-key sequence did not meet one or more timing limits above. |

The overlay reports all three timing measurements for each detected sequence, including `Bad` results.