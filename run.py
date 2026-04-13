"""Start both backend and frontend servers with one command."""

import subprocess
import sys
import os
import signal

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8001"],
        cwd=os.path.join(ROOT, "backend"),
    )

    frontend = subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=os.path.join(ROOT, "frontend"),
    )

    try:
        while True:
            # Check if either process has exited
            be_status = backend.poll()
            fe_status = frontend.poll()

            if be_status is not None:
                print(f"Backend exited with code {be_status}")
                frontend.terminate()
                sys.exit(be_status)

            if fe_status is not None:
                print(f"Frontend exited with code {fe_status}")
                backend.terminate()
                sys.exit(fe_status)

            # Wait a bit before checking again
            try:
                backend.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass

    except KeyboardInterrupt:
        print("\nShutting down...")
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()


if __name__ == "__main__":
    main()
