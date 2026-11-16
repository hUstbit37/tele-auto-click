import argparse
import asyncio
import logging
import sys
from pathlib import Path

from checkin.config import DEFAULT_CONFIG, load_targets
from checkin.runner import run


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check in to every Telegram target listed in targets.toml."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--only", nargs="+", metavar="NAME", help="run only these targets")
    parser.add_argument("--force", action="store_true", help="ignore cooldowns")
    parser.add_argument("--dry-run", action="store_true", help="show due targets, do nothing")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("telethon").setLevel(logging.WARNING)

    targets = load_targets(args.config)

    if args.only:
        known = {t.name for t in targets}
        unknown = set(args.only) - known
        if unknown:
            parser.error(f"unknown target(s): {', '.join(sorted(unknown))}")
        targets = [t for t in targets if t.name in args.only]

    failures = asyncio.run(run(targets, force=args.force, dry_run=args.dry_run))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
