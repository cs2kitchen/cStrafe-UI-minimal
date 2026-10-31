from argparse import ArgumentParser
from pathlib import Path
from input_events import InputListener
from overlay import Overlay


def main() -> None:
    parser = ArgumentParser(description="Display and record counter-strafe classifications.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="CSV_PATH",
        help="append classifications and statistics to this pandas-readable CSV file",
    )
    args = parser.parse_args()

    overlay = Overlay()
    listener = InputListener(overlay, output_path=args.output)
    listener.start()
    overlay.run()


if __name__ == "__main__":
    main()