"""Language Study — four-skill English practice inside Anki.

Entry point loaded by Anki's addon manager. All Anki-facing registration
happens in ``init()``; anything raised there is reported to Anki's addon
error dialog, so init is wrapped to also emit a machine-readable marker
for the dev test harness (see tests/README).
"""

from __future__ import annotations

import os
import tempfile
import traceback

__version__ = "0.1.0"

MARKER_ENV = "LSA_DEV_MARKER"


def _dev_marker_path() -> str | None:
    """Where to write the load marker, when dev testing is requested."""
    path = os.environ.get(MARKER_ENV)
    if path:
        return path
    return None


def _write_marker(kind: str, payload: str) -> None:
    path = _dev_marker_path()
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{kind}\n{payload}")
    except OSError:
        pass


def init() -> None:
    """Called by Anki's addon manager at load time."""
    # Registration of hooks/menus is added by later tasks; a skeleton load
    # must import cleanly and register nothing harmful.
    from . import bootstrap

    bootstrap.register()
    try:
        import aqt  # noqa: F401
    except ImportError:
        pass  # outside Anki (e.g. unit tests under a system interpreter)
    else:
        from . import browser_menu, selftest, suspension

        suspension.register()
        browser_menu.register()
        selftest.register()


try:
    init()
except Exception:
    _write_marker("error", traceback.format_exc())
    raise
else:
    _write_marker("ok", __version__)
