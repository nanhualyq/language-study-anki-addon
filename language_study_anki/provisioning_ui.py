"""Confirm-and-provision UI: the one place that asks before creating.

Specs: article-storage → Auto-provisioning of note types and deck;
design D2 (shared helper), D3 (self-test auto-accept), D5 (data-driven
message). Both stages call ``ensure_provisioned``: at profile open with the
article scope (registered here) and from the extract flow with the extract
scope. aqt is imported lazily so the module stays importable without Anki
(tests/ contract).
"""

from __future__ import annotations

import os
import traceback

from . import provisioning

# Design D3: the headless self-test harness cannot answer a modal dialog.
SELFTEST_ENV = "LSA_SELFTEST"

CONFIRM_TITLE = "Language Study"


def ensure_provisioned(col, parent, *, scope: str, context: str) -> dict | None:
    """Provision one scope, asking the user first when items are missing.

    Returns the ``provision_scope`` result dict, or ``None`` when the user
    declines. With nothing missing — or under ``LSA_SELFTEST`` — provisions
    silently without any dialog.
    """
    missing = provisioning.missing_items(col, scope)
    needs_confirm = bool(missing["note_types"] or missing["decks"])
    if needs_confirm and not os.environ.get(SELFTEST_ENV):
        from aqt.qt import QMessageBox

        text = (
            f"{context}\n\n"
            f"{provisioning.build_confirm_message(missing)}\n\n"
            "Create them now?"
        )
        answer = QMessageBox.question(
            parent,
            CONFIRM_TITLE,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,  # consent-first: Enter must not mutate
        )
        if answer != QMessageBox.StandardButton.Yes:
            return None
    return provisioning.provision_scope(col, scope)


def register() -> None:
    """Startup stage (design D1): offer article provisioning on profile open."""
    from aqt import gui_hooks

    gui_hooks.profile_did_open.append(_on_profile_open)


def _on_profile_open() -> None:
    try:
        from aqt import mw

        if mw is None or getattr(mw, "col", None) is None:
            return
        ensure_provisioned(
            mw.col,
            mw,
            scope="article",
            context=(
                "Language Study needs the following missing items before it "
                "can store articles:"
            ),
        )
    except Exception:
        print(
            "language_study_anki: startup provisioning failed:\n"
            + traceback.format_exc()
        )
