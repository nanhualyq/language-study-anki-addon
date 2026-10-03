"""Headless profile creation for the scratch Anki base (dev tooling).

Skips Anki's first-run profile dialog so subsequent launches go straight to
the main window. Uses Anki's bundled python:

    ~/anki-bin/python/bin/python3 tools/create_profile.py <base> <profile-name>
"""
import os
import sys

sys.path.insert(0, os.path.expanduser("~/anki-bin/app_packages"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from aqt.profiles import ProfileManager  # noqa: E402


def main() -> None:
    base_path, name = sys.argv[1], sys.argv[2]
    os.environ["ANKI_BASE"] = base_path
    base = ProfileManager.get_created_base_folder(base_path)
    pm = ProfileManager(base)
    pm.setupMeta()
    # create() is itself idempotent (SQL existence check) and commits the row
    # itself. Do NOT call pm.profiles() (triggers default-profile bootstrap
    # needing fluent translations) or pm.save() (pickles an unrelated attr
    # that is None outside a full app run).
    pm.create(name)
    print(f"created profile {name!r} in {base}")


if __name__ == "__main__":
    main()
