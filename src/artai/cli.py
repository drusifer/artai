"""artai command-line entry point (placeholder until the sprint's CLI phase lands)."""

import sys

from artai import __version__


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] in ("--version", "-V"):
        print(f"artai {__version__}")
        return 0
    print("artai: no commands implemented yet", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
