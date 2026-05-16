from input_events import InputListener
from overlay import Overlay


def main() -> None:
    overlay = Overlay()
    listener = InputListener(overlay)
    listener.start()
    overlay.run()


if __name__ == "__main__":
    main()