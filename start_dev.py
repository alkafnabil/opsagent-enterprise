#!/usr/bin/env python3
"""
OpsAgent Local Development Orchestrator
Starts all three local services (Mock ERP :8001, Backend :8000, Frontend :5173) concurrently.
Supports graceful shutdown via Ctrl+C.
"""
import os
import sys
import time
import subprocess
import signal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def main():
    print("=" * 70)
    print("   OPSAGENT LOCAL DEVELOPMENT RUNNER (ALL-IN-ONE)")
    print("=" * 70)
    print("Memulai seluruh service operasional PT Nusantara Coal Operations...")
    print("1. Mock ERP Service   -> http://localhost:8001/docs")
    print("2. Backend API        -> http://localhost:8000/docs")
    print("3. Frontend UI        -> http://localhost:5173")
    print("Tekan Ctrl+C untuk menghentikan seluruh service secara bersamaan.")
    print("=" * 70)

    processes = []

    # Environment variables
    env = os.environ.copy()
    pythonpath = f"{ROOT_DIR / 'backend'}{os.pathsep}{ROOT_DIR / 'mock_erp'}{os.pathsep}{ROOT_DIR}"
    env["PYTHONPATH"] = pythonpath

    try:
        # 1. Start Mock ERP
        print("[1/3] Menjalankan Mock ERP Microservice di port 8001...")
        p_erp = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "mock_erp.main:app", "--port", "8001", "--host", "0.0.0.0"],
            cwd=str(ROOT_DIR),
            env=env,
        )
        processes.append(("Mock ERP", p_erp))
        time.sleep(1.5)

        # 2. Start Backend
        print("[2/3] Menjalankan Backend OpsAgent FastAPI di port 8000...")
        p_backend = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--port", "8000", "--host", "0.0.0.0"],
            cwd=str(ROOT_DIR),
            env=env,
        )
        processes.append(("Backend", p_backend))
        time.sleep(1.5)

        # 3. Start Frontend
        frontend_dir = ROOT_DIR / "frontend"
        if (frontend_dir / "node_modules").exists():
            print("[3/3] Menjalankan Frontend Vite React di port 5173...")
            npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
            p_frontend = subprocess.Popen(
                [npx_cmd, "vite", "--port", "5173", "--host"],
                cwd=str(frontend_dir),
                env=env,
            )
            processes.append(("Frontend", p_frontend))
        else:
            print("[WARNING] node_modules belum terpasang di frontend/. Jalankan 'npm install' di folder frontend/.")

        print("\n>>> SELURUH SERVICE AKTIF! Buka browser di: http://localhost:5173 <<<\n")

        # Keep running until Ctrl+C
        while True:
            time.sleep(1)
            for name, p in processes:
                if p.poll() is not None:
                    print(f"Service {name} berhenti (exit code {p.returncode}).")
                    return

    except KeyboardInterrupt:
        print("\n\nMenghentikan seluruh service OpsAgent...")
    finally:
        for name, p in processes:
            if p.poll() is None:
                print(f"Terminating {name}...")
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("Seluruh service telah dimatikan dengan aman.")

if __name__ == "__main__":
    main()
