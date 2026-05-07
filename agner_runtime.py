"""Runtime loader for the split AGNER Browser source.

The old app lived in one huge module. The files in agner_parts are executed in
order into this module namespace so the existing cross-references keep working
while the codebase is modularized.
"""

from pathlib import Path as _RuntimePath

_PART_FILES = (
    "bootstrap.py",
    "ui.py",
    "main_window.py",
    "browser_tab.py",
    "managers.py",
    "widgets.py",
    "entrypoint.py",
)

_PARTS_DIR = _RuntimePath(__file__).with_name("agner_parts")

for _part_name in _PART_FILES:
    _part_path = _PARTS_DIR / _part_name
    _source = _part_path.read_text(encoding="utf-8")
    exec(compile(_source, str(_part_path), "exec"), globals(), globals())

del _RuntimePath, _PART_FILES, _PARTS_DIR, _part_name, _part_path, _source
