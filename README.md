# cStrafe UI by CS2Kitchen

This is the second project in this domain. I made this so it could be more simplified and not too confusing like the previous version.This is a lightweight training tool to help players practice  counterstrafing mechanics in CS2. It listens to your movement keys (W, A, S and D) and the left mouse button to decide whether you fired while coming to a full stop, started moving the other way or were still overlapping directions.

![UI Preview](images/strafe_ui_2.gif)


## Installation

1. Make sure you have a recent Python installed. ( Install 3.13 from microsoft store if you get into issues)
2. Install the required dependency:

   ```bash
   pip install pynput tkinter
   ```

   The Tkinter library (`tkinter`) is included with most standard Python installations on Windows and macOS.

3. Download or clone this repository, then run the program from the project directory:

   ```bash
   python main.py
   ```

## Usage

When the application is running, an overlay appears on top of your game window. It updates whenever you fire the left mouse button. You can drag it to any part of screen. Make sure to run your game in fullscreen windowed(won't work in fullscreen). You can control the overlay with a few simple keys:

- **F6** – hide or show the overlay without quitting.
- **F8** – exit the program.
- **=** – increase the size of the overlay text.
- **-** – decrease the size of the overlay text.

## Classification Labels

After each shot the tool displays one of three labels along with timing information (when applicable):

| Label            | Description |
|------------------|-------------|
| **Counter‑strafe** | You released one movement key and quickly pressed the opposite key before shooting. A valid counterstrafe should be followed by a shot within a short delay. The overlay shows the time between the key release and the opposite key press (*CS time*) and the delay between pressing the opposite key and firing (*Shot delay*). |
| **Overlap** | Both opposing movement keys were held at the same time. This indicates overlapping movement, which should be avoided for accurate shooting. The overlay shows how long the keys overlapped before the shot. |
| **Bad** | No valid counterstrafe pattern was detected before the shot. This can mean you shot without changing direction, your movement timing was too slow or you were moving in only one direction. |

Keep your movements crisp and have fun hope this helps you :D