"""
Shared pytest fixtures for frontend tests.

This module contains shared fixtures that can be used across multiple test modules
in the frontend test suite, including the app fixture for starting/stopping the
application in headless mode.
"""

import pytest
import subprocess
import time
import os
import signal
import requests
import sys
from requests.exceptions import ConnectionError


# Configuration
APP_HOST = "127.0.0.1"
APP_HTTP_PORT = 19876  # Using a different port for testing to avoid conflicts
APP_WS_PORT = 19875  # Using a different port for testing
APP_URL = f"http://{APP_HOST}:{APP_HTTP_PORT}/?wsPort={APP_WS_PORT}&showDebug=false"
MAIN_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "main.py")


@pytest.fixture(scope="session")
def app():
    """Fixture to start and stop the application in headless mode."""
    command = [
        sys.executable,
        MAIN_SCRIPT_PATH,
        "--headless",
        f"--http-port={APP_HTTP_PORT}",
        f"--ws-port={APP_WS_PORT}",
    ]

    print(f"Starting app with command: {' '.join(command)}")
    # Start the process in a new process group to ensure it can be killed properly
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )

    # Wait for the server to be ready
    max_wait_time = 30  # seconds
    start_time = time.time()
    server_ready = False

    while time.time() - start_time < max_wait_time:
        # Check if HTTP server is accessible
        try:
            response = requests.get(f"http://{APP_HOST}:{APP_HTTP_PORT}/", timeout=1)
            if response.status_code == 200:
                print(f"HTTP server is up! (Status {response.status_code})")
                server_ready = True
                break
        except ConnectionError:
            # print("HTTP server not yet available, retrying...")
            pass  # Server not up yet

        # Check for process termination or output indicating readiness (optional)
        if process.poll() is not None:
            print("Application process terminated prematurely.")
            stdout, stderr = process.communicate()
            print(f"STDOUT:\\n{stdout}")
            print(f"STDERR:\\n{stderr}")
            break

        time.sleep(0.5)

    if not server_ready:
        print("Server did not start within the allocated time.")
        # Try to kill the process if it's still running
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=5)
        print(f"STDOUT on failure:\\n{stdout}")
        print(f"STDERR on failure:\\n{stderr}")
        pytest.fail("App server failed to start")

    yield APP_URL  # Provide the URL to the tests

    print("\nShutting down app...")
    if os.name == "nt":
        process.send_signal(
            signal.CTRL_BREAK_EVENT
        )  # Preferred way to terminate process group on Windows
    else:
        os.killpg(
            os.getpgid(process.pid), signal.SIGTERM
        )  # Terminate the process group

    try:
        stdout, stderr = process.communicate(
            timeout=10
        )  # Wait for process to terminate
        print("App process terminated.")
        # print(f"STDOUT:\\n{stdout}")
        # print(f"STDERR:\\n{stderr}")
    except subprocess.TimeoutExpired:
        print("App process did not terminate gracefully, killing.")
        process.kill()
        stdout, stderr = process.communicate()
        # print(f"STDOUT after kill:\\n{stdout}")
        # print(f"STDERR after kill:\\n{stderr}")
    print("App stopped.")
