"""Shared helpers for scanning the requirements/ directory.

Implements: REQ-001
Implements: REQ-002
"""
from __future__ import annotations

import re
from pathlib import Path


REQ_FILENAME_RE = re.compile(r"^REQ-(\d{3})-.*\.md$")


def requirements_dir(root=None):
    """Return the requirements/ path under root (default: current working dir).

    Implements: REQ-001
    Implements: REQ-002
    """
    base = Path.cwd() if root is None else Path(root)
    return base / "requirements"


def iter_req_files(directory):
    """Yield (number, path) for files matching REQ-NNN-*.md in directory.

    Non-matching names are skipped. A non-existent directory yields nothing.

    Implements: REQ-001
    Implements: REQ-002
    """
    if not directory.exists():
        return
    for entry in directory.iterdir():
        m = REQ_FILENAME_RE.match(entry.name)
        if m:
            yield int(m.group(1)), entry
