from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _install_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


INSTALL_ROOT = _install_root()
HOST = os.environ.get("VALIDATION_TEAM_HOST", "127.0.0.1")
PORT = int(os.environ.get("VALIDATION_TEAM_PORT", "0"))


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.3)
        if probe.connect_ex((host, port)) == 0:
            return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def _pick_port(host: str, preferred: int = 8000) -> int:
    if PORT > 0:
        return PORT
    for candidate in (preferred, 8765, 8780, 8800, 8001, 8002):
        if _port_is_free(host, candidate):
            return candidate
    raise RuntimeError("No free port available for Validation TEAM.")


def _prepare_environment() -> None:
    os.chdir(INSTALL_ROOT)
    os.environ["VALIDATION_TEAM_ROOT"] = str(INSTALL_ROOT)
    os.environ.setdefault("SERVE_STATIC", "1")
    if str(INSTALL_ROOT) not in sys.path:
        sys.path.insert(0, str(INSTALL_ROOT))


def _check_prerequisites() -> bool:
    cred_candidates = [
        INSTALL_ROOT / "backend" / "credentials.json",
        INSTALL_ROOT / "credentials.json",
    ]
    if any(p.is_file() for p in cred_candidates):
        return True
    print("\n[Validation TEAM] Missing backend/credentials.json next to the executable.")
    print("Copy the Earth Engine service account file before running.\n")
    if is_frozen():
        input("Press Enter to exit...")
    return False


def _open_browser_after(port: int) -> None:
    time.sleep(2.0)
    webbrowser.open(f"http://{HOST}:{port}/")


def main() -> int:
    _prepare_environment()
    if not _check_prerequisites():
        return 1

    from backend.core.runtime_paths import get_static_dir

    static_dir = get_static_dir()
    if static_dir is None:
        print("\n[Validation TEAM] frontend/dist not found.")
        print("Rebuild with scripts/build_exe.ps1\n")
        if is_frozen():
            input("Press Enter to exit...")
        return 1

    db_path = INSTALL_ROOT / "data" / "mapbiomas.db"
    if not db_path.is_file():
        print(f"\n[Validation TEAM] Warning: statistics DB missing at {db_path}")
        print("The statistics panel will be unavailable until mapbiomas.db is copied.\n")

    port = _pick_port(HOST)
    if port != 8000:
        print(f"[Validation TEAM] Port 8000 busy; using {port}.")

    print(f"[Validation TEAM] http://{HOST}:{port}/")
    print("[Validation TEAM] Ctrl+C to stop.\n")

    threading.Thread(target=lambda: _open_browser_after(port), daemon=True).start()

    import uvicorn
    from backend.main import app

    uvicorn.run(app, host=HOST, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
