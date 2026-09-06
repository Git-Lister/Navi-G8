#!/usr/bin/env python3
"""
Diagnostic harness for Navi-G8 backend.
Runs the backend in daemon mode and captures everything.
"""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path


def log(msg):
    """Print with timestamp."""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    log("=== NAVI-G8 BACKEND DIAGNOSTIC ===")

    # 1. Environment
    log("1. Environment:")
    log(f"   CWD: {os.getcwd()}")
    log(f"   PYTHONPATH: {os.environ.get('PYTHONPATH', 'NOT SET')}")
    log(f"   PATH (first 3): {os.environ['PATH'].split(';')[:3]}")

    # 2. Python version
    log("2. Python version:")
    result = subprocess.run(["python", "--version"], capture_output=True, text=True)
    log(f"   {result.stdout.strip()}")

    # 3. Check agent folder
    agent_path = Path("C:/Users/DaveH/Navi-G8/agent")
    log(f"3. Agent path: {agent_path}")
    log(f"   Exists: {agent_path.exists()}")
    if agent_path.exists():
        main_py = agent_path / "src" / "navi_agent" / "__main__.py"
        log(f"   __main__.py exists: {main_py.exists()}")

    # 4. Launch backend with logging to file
    log("4. Launching backend...")
    log_file = Path("C:/Users/DaveH/Navi-G8/backend_diagnostic.log")
    with open(log_file, "w") as f:
        f.write(f"=== BACKEND LOG ({time.ctime()}) ===\n")
        f.flush()

        python_path = agent_path / ".venv" / "Scripts" / "python.exe"
        log(f"   Python executable: {python_path}")
        log(f"   Exists: {python_path.exists()}")

        if not python_path.exists():
            log("   ❌ Python executable not found!")
            return

        proc = subprocess.Popen(
            [str(python_path), "-m", "navi_agent", "--mode", "daemon"],
            cwd=str(agent_path),
            stdin=subprocess.DEVNULL,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True,
        )

        log(f"   PID: {proc.pid}")

        # 5. Wait for socket
        log("5. Waiting for socket (max 10 seconds)...")
        socket_ready = False
        for i in range(50):
            time.sleep(0.2)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect(("127.0.0.1", 9876))
                s.close()
                socket_ready = True
                log(f"   ✅ Socket ready after {i * 0.2:.1f}s")
                break
            except:
                pass

        if not socket_ready:
            log("   ❌ Socket never became ready!")
            log("   Dumping log file contents:")
            with open(log_file, "r") as f2:
                content = f2.read()
                log("   --- BEGIN LOG ---")
                for line in content.split("\n")[-50:]:
                    log(f"   {line}")
                log("   --- END LOG ---")
            proc.kill()
            return

        # 6. Send a test query
        log("6. Sending test query...")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(("127.0.0.1", 9876))
            s.sendall(b'{"type": "query", "query": "Hello, diagnostic"}\n')
            response = s.recv(4096).decode()
            log(f"   ✅ Response: {response[:200]}...")
            s.close()
        except Exception as e:
            log(f"   ❌ Query failed: {e}")

        # 7. Kill process
        log("7. Cleaning up...")
        proc.kill()
        log("   ✅ Done")


if __name__ == "__main__":
    main()
