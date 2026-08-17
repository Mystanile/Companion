from __future__ import annotations

import os
from pathlib import Path


def expand_path(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path))).resolve()


def load_allowed_roots(raw_roots: list[str]) -> list[Path]:
    roots: list[Path] = []
    for item in raw_roots:
        root = expand_path(item)
        if root.exists():
            roots.append(root)
    if not roots:
        roots.append(expand_path("~"))
    return roots


def is_path_allowed(path: str | Path, allowed_roots: list[Path]) -> bool:
    try:
        resolved = expand_path(str(path))
    except (OSError, ValueError):
        return False

    for root in allowed_roots:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def guard_path(path: str | Path, allowed_roots: list[Path]) -> Path:
    resolved = expand_path(str(path))
    if not is_path_allowed(resolved, allowed_roots):
        raise PermissionError(f"Path not allowed: {resolved}")
    return resolved
