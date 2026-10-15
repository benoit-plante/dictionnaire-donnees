"""Quit the tool from the interface (v0.7.1, D-055): without a console window, there is
nothing else to close. The process ends a moment later, once the page has said so; every
decision is already saved."""

from __future__ import annotations

import os
import threading

DELAY = 1.0  # seconds: time for the page to show that the tool stopped


def stop_soon(delay: float = DELAY) -> None:
    timer = threading.Timer(delay, os._exit, args=(0,))
    timer.daemon = True
    timer.start()
