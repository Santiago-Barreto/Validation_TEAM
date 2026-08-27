from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_install_root() -> Path:
    env = os.environ.get("VALIDATION_TEAM_ROOT")
    if env:
        return Path(env).resolve()
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def get_bundle_root() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", get_install_root() / "_internal"))
    return get_install_root()


def get_backend_dir() -> Path:
    return get_install_root() / "backend"


def get_static_dir() -> Path | None:
    for base in (get_bundle_root(), get_install_root()):
        for rel in ("frontend/dist",):
            candidate = base / rel
            if candidate.is_dir() and (candidate / "index.html").is_file():
                return candidate
    return None
