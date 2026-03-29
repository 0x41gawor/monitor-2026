# app/cli.py
from __future__ import annotations

import argparse

from app.run_once import run_once


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Monitor once for a given date.",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date in ISO format (YYYY-MM-DD). Defaults to today.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_once(args.date)


if __name__ == "__main__":
    main()