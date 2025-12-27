#!/usr/bin/env python3
"""
Unified Run Script for AI Cycling Coach

Usage:
    python run.py              # Run both backend and frontend
    python run.py backend      # Run backend only
    python run.py frontend     # Run frontend only
    python run.py --docker     # Run with Docker Compose
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path
from typing import Optional

# Project root directory
ROOT_DIR = Path(__file__).parent.resolve()


def load_env():
    """Load environment variables from .env file."""
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        print("📝 Loading environment variables from .env...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Environment variables loaded")
    else:
        print("⚠️  .env file not found. Copy .env.example to .env")
        sys.exit(1)


def get_port(name: str, default: int) -> int:
    """Get port from environment or default."""
    return int(os.environ.get(name, default))


def run_backend(port: int = None):
    """Run the backend server."""
    if port is None:
        port = get_port("BACKEND_PORT", 8005)

    print(f"🚀 Starting Backend on port {port}...")

    # Set PYTHONPATH
    pythonpath = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = f"{ROOT_DIR}:{pythonpath}"

    # Activate venv if exists
    venv_activate = ROOT_DIR / ".venv" / "bin" / "activate"

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]

    return subprocess.Popen(cmd, cwd=ROOT_DIR)


def run_frontend(port: int = None):
    """Run the frontend dev server."""
    if port is None:
        port = get_port("FRONTEND_PORT", 3005)

    print(f"🚀 Starting Frontend on port {port}...")

    frontend_dir = ROOT_DIR / "frontend"

    # Set Vite environment variables
    backend_port = get_port("BACKEND_PORT", 8005)
    os.environ["VITE_API_URL"] = f"http://localhost:{backend_port}"
    os.environ["VITE_SUPABASE_URL"] = os.environ.get("SUPABASE_URL", "")
    os.environ["VITE_SUPABASE_ANON_KEY"] = os.environ.get("SUPABASE_ANON_KEY", "")

    cmd = ["pnpm", "run", "dev", "--port", str(port)]

    return subprocess.Popen(cmd, cwd=frontend_dir)


def run_docker():
    """Run with Docker Compose."""
    print("🐳 Starting with Docker Compose...")

    cmd = ["docker-compose", "up", "--build"]

    return subprocess.Popen(cmd, cwd=ROOT_DIR)


def main():
    """Main entry point."""
    load_env()

    # Parse arguments
    args = sys.argv[1:]
    use_docker = "--docker" in args

    if use_docker:
        proc = run_docker()
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping Docker...")
            proc.terminate()
        return

    # Determine what to run
    run_be = "backend" in args or not args
    run_fe = "frontend" in args or not args

    processes = []

    try:
        if run_be:
            processes.append(("Backend", run_backend()))

        if run_fe:
            time.sleep(1)  # Give backend a head start
            processes.append(("Frontend", run_frontend()))

        print("\n" + "=" * 50)
        print("🎉 Services started! Press Ctrl+C to stop.")
        print("=" * 50)

        backend_port = get_port("BACKEND_PORT", 8005)
        frontend_port = get_port("FRONTEND_PORT", 3005)

        if run_be:
            print(f"   Backend:  http://localhost:{backend_port}")
            print(f"   API Docs: http://localhost:{backend_port}/docs")
        if run_fe:
            print(f"   Frontend: http://localhost:{frontend_port}")
        print("=" * 50 + "\n")

        # Wait for processes
        for name, proc in processes:
            proc.wait()

    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        for name, proc in processes:
            print(f"   Stopping {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("✅ All services stopped.")


if __name__ == "__main__":
    main()
