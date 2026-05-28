from __future__ import annotations

from datetime import datetime
from typing import Callable


LogCallback = Callable[[str], None]


def emit(callback: LogCallback | None, message: str) -> None:
    if callback:
        callback(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
