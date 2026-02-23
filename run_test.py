# -*- coding: utf-8 -*-
"""Quick startup test — launch main.py, wait 7s, check for errors."""
import subprocess, sys, time, os

venv_py = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "python.exe")
main_py = os.path.join(os.path.dirname(__file__), "main.py")

proc = subprocess.Popen(
    [venv_py, "-X", "utf8", main_py],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=os.path.dirname(__file__),
)

time.sleep(7)

if proc.poll() is not None:          # process already exited (crash)
    out, err = proc.communicate()
    print(f"[FAIL] App crashed (exit={proc.returncode})")
    if err:
        print("--- stderr ---")
        print(err.decode("utf-8", errors="replace"))
    sys.exit(1)
else:                                 # still running = OK
    print(f"[PASS] App started OK (PID={proc.pid})")
    proc.terminate()
    try:
        _, err = proc.communicate(timeout=3)
        if err:
            decoded = err.decode("utf-8", errors="replace")
            # Filter out normal shutdown noise
            lines = [l for l in decoded.splitlines()
                     if l.strip() and "Traceback" not in l
                     and "KeyboardInterrupt" not in l]
            if lines:
                print("--- startup warnings ---")
                for l in lines[:10]:
                    print(" ", l)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("[PASS] Phase 2 startup test complete")
