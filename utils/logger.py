"""集中式日志：控制台 + 可选文件输出"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_LEVEL = os.environ.get("SCY_LOG_LEVEL", "INFO").upper()
_LOG_DIR = os.environ.get("SCY_LOG_DIR", "")

_FMT = "%(asctime)s %(levelname)s %(name)s — %(message)s"


def _configure_root() -> None:
    root = logging.getLogger("scy")
    if getattr(root, "_scy_configured", False):
        return
    root.setLevel(getattr(logging, _LEVEL, logging.INFO))

    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(logging.Formatter(_FMT))
    root.addHandler(stream)

    if _LOG_DIR:
        try:
            os.makedirs(_LOG_DIR, exist_ok=True)
            fh = RotatingFileHandler(
                os.path.join(_LOG_DIR, "scy.log"),
                maxBytes=2 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
            fh.setFormatter(logging.Formatter(_FMT))
            root.addHandler(fh)
        except OSError:
            pass

    root._scy_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    _configure_root()
    return logging.getLogger(f"scy.{name}")
