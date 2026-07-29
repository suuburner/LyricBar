"""One-shot logging configuration for the whole app.

Call `configure_logging()` exactly once, from `main.py`, before anything
else is imported. Every other module should get its own logger with
`logging.getLogger(__name__)` and use `.debug()/.info()/.warning()/.exception()`
instead of `print()` -- that gives timestamps, levels, and a module name for
free, and lets a user turn debug spam on/off without editing source.
"""
import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if root.handlers:
        # Already configured (e.g. re-entered on a module reload) -- don't
        # stack duplicate handlers, which would duplicate every log line.
        return

    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S")
    )
    root.addHandler(handler)