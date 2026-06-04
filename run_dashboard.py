"""Launch the Operations Inventory Streamlit dashboard on port 8502."""

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_FILE = (PROJECT_ROOT / "dashboard" / "operations_app.py").resolve()
DEFAULT_PORT = "8502"


def _python() -> str:
    venv_py = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_py.is_file():
        return str(venv_py)
    return sys.executable


def _resolve_port(argv: list[str]) -> str:
    for i, arg in enumerate(argv):
        if arg.startswith("--server.port="):
            return arg.split("=", 1)[1]
        if arg == "--server.port" and i + 1 < len(argv):
            return argv[i + 1]
    return os.getenv("OPERATIONS_STREAMLIT_PORT", DEFAULT_PORT)


def main() -> int:
    port = _resolve_port(sys.argv[1:])
    os.environ["OPERATIONS_STREAMLIT_PORT"] = port

    if not APP_FILE.is_file():
        print(f"Error: dashboard not found at {APP_FILE}", file=sys.stderr)
        return 1

    url = f"http://localhost:{port}"
    extra = list(sys.argv[1:])
    has_port_flag = any(
        a == "--server.port" or a.startswith("--server.port=") for a in extra
    )

    args = [
        _python(),
        "-m",
        "streamlit",
        "run",
        str(APP_FILE),
        "--server.address",
        "localhost",
        "--browser.serverAddress",
        "localhost",
    ]
    if not has_port_flag:
        args.extend(["--server.port", port])
    args.extend(extra)

    print("=" * 60)
    print("  Operations Inventory Assistant (Week 14)")
    print(f"  Open this URL (NOT MarketMind on 8501): {url}")
    print("=" * 60)

    try:
        webbrowser.open(url)
    except Exception:
        pass

    return subprocess.call(args, cwd=str(PROJECT_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
