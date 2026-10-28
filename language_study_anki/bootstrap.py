"""Idempotence guard for addon registration.

The actual hook/menu registrations live in ``__init__.init()`` (suspension
hook, Tools-menu Hub entry, dev self-test). This guard makes a repeated
``register()`` call — e.g. during an addon reload — a no-op.
"""

from __future__ import annotations


def register() -> None:
    global _registered
    if _registered:
        return
    _registered = True


_registered = False
