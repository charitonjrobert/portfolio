"""Test harness: start the app on a free port with a clean database.

The app under test is the portfolio copy in ../sportsbet-scanner, never the deployed one.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

APP_DIR = Path(__file__).resolve().parents[1] / "sportsbet-scanner"
BACKEND_DIR = APP_DIR / "backend"
DB_FILE = BACKEND_DIR / "bets.db"
STARTUP_TIMEOUT = 40.0


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def base_url() -> str:
    """Run uvicorn once for the whole session and stop it afterwards."""
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    if DB_FILE.exists():
        DB_FILE.unlink()

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    env["PYTHONIOENCODING"] = "utf-8"
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("app exited during startup")
        try:
            requests.get(f"{url}/api/version", timeout=1)
            break
        except requests.RequestException:
            time.sleep(0.3)
    else:
        process.kill()
        raise RuntimeError("app did not start in time")

    yield url

    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
    if DB_FILE.exists():
        DB_FILE.unlink()


@pytest.fixture(scope="session")
def api(base_url: str) -> requests.Session:
    session = requests.Session()
    session.base_url = base_url  # type: ignore[attr-defined]
    return session


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, base_url: str) -> dict:
    return {**browser_context_args, "base_url": base_url}
