import os
import sys
import socket
import webbrowser
import threading
import time
import json
import urllib.request
import uvicorn

# Windows 控制台常见 GBK：避免 emoji/中文打印直接炸崩
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = int(os.environ.get("AIMASK_PORT", "8000"))
MAX_PORT_TRIES = 15


def tcp_open(host: str, port: int, timeout: float = 0.4) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


def probe_our_api(port: int) -> bool:
    """判断该端口上是否已是本站（AI-Mask）服务。"""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/tasks", timeout=1.0) as resp:
            if resp.status != 200:
                return False
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            return isinstance(data, dict) and "tasks" in data
    except Exception:
        return False


def find_available_port(preferred: int) -> int:
    """选择可用端口；被其他服务占用则向后尝试。"""
    for port in range(preferred, preferred + MAX_PORT_TRIES):
        if not tcp_open("127.0.0.1", port):
            return port
        if probe_our_api(port):
            return port
        print(f"  - port {port} busy (not AI-Mask), try {port + 1} ...")
    raise RuntimeError(f"no free port in {preferred}~{preferred + MAX_PORT_TRIES - 1}")


def print_conflict_hint(bad_port: int) -> None:
    print()
    print("!" * 60)
    print(f"  WARN: 127.0.0.1:{bad_port} is occupied (or ghost listener)")
    print('  Browser may only show {"detail":"Not Found"}')
    print()
    print("  Common causes:")
    print("  1. Another uvicorn still running (e.g. api.main:app)")
    print("  2. Old AI-Mask process not fully stopped")
    print("  3. Clash / VPN TUN leaving odd localhost bindings")
    print()
    print("  Check (PowerShell):")
    print(f'    netstat -ano | findstr ":{bad_port}"')
    print(f"    Get-NetTCPConnection -LocalPort {bad_port} -State Listen")
    print("    taskkill /PID <PID> /F")
    print("!" * 60)
    print()


def open_browser(port: int):
    try:
        time.sleep(1.5)
        if os.name == "nt" or "DISPLAY" in os.environ:
            webbrowser.open(f"http://127.0.0.1:{port}")
    except Exception:
        pass


if __name__ == "__main__":
    preferred = DEFAULT_PORT
    print("=" * 60)
    print("   AI-Mask starting...")
    print("=" * 60)

    if tcp_open("127.0.0.1", preferred) and not probe_our_api(preferred):
        print_conflict_hint(preferred)

    try:
        port = find_available_port(preferred)
    except RuntimeError as exc:
        print(str(exc))
        sys.exit(1)

    if tcp_open("127.0.0.1", port) and probe_our_api(port):
        print(f"  Already running at http://127.0.0.1:{port}")
        open_browser(port)
        sys.exit(0)

    if port != preferred:
        print(f"  Auto-switched to port {port} (preferred {preferred} unavailable)")
        print(f"  Open: http://127.0.0.1:{port}")

    print(f"   Local URL : http://127.0.0.1:{port}")
    print(f"   Bind      : {DEFAULT_HOST}:{port}")
    print("=" * 60)

    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    uvicorn.run("backend.app.main:app", host=DEFAULT_HOST, port=port, reload=False)
