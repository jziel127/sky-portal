"""
SkyPortal Master System Orchestrator
------------------------------------
Spawns and monitors both background processes simultaneously:
1. Circadian Engine (Circadian.py) -> Weather API & Servo Control on COM7
2. LED Matrix Clock (matrix_clock.py) -> WLED Matrix Display Driver

Author: SkyPortal Project
"""

import sys
import os
import time
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROCESSES = [
    {"name": "Circadian Engine", "script": os.path.join(SCRIPT_DIR, "Circadian.py")},
    {"name": "LED Matrix Clock", "script": os.path.join(SCRIPT_DIR, "matrix_clock.py")},
]


def start_process(proc_info):
    script_path = proc_info["script"]
    print(f"[ORCHESTRATOR] Starting {proc_info['name']} ({os.path.basename(script_path)})...")
    return subprocess.Popen([sys.executable, script_path])


def main():
    print("=======================================================")
    print("             SKYPORTAL MASTER ORCHESTRATOR             ")
    print("=======================================================")

    running_procs = []

    # Launch both background processes
    for proc_info in PROCESSES:
        p = start_process(proc_info)
        running_procs.append((proc_info, p))
        time.sleep(1.5)

    print("\n[ORCHESTRATOR] All background services successfully running.")
    print("Press Ctrl+C at any time to terminate all services cleanly.\n")

    try:
        while True:
            # Monitor process health
            for proc_info, p in running_procs:
                poll = p.poll()
                if poll is not None:
                    print(f"[WARNING] {proc_info['name']} exited (code {poll}). Restarting...")
                    p_new = start_process(proc_info)
                    idx = running_procs.index((proc_info, p))
                    running_procs[idx] = (proc_info, p_new)

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[ORCHESTRATOR] Shutting down all services...")
        for proc_info, p in running_procs:
            print(f"  Stopping {proc_info['name']}...")
            p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()

        print("[ORCHESTRATOR] System safely stopped.")


if __name__ == "__main__":
    main()