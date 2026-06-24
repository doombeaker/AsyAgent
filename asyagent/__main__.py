from __future__ import annotations

import logging
import sys

from .config import Settings
from .server import run


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    settings = Settings.from_env()
    try:
        run(settings)
    except OSError as e:
        print(f"asyagent: failed to start server: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
