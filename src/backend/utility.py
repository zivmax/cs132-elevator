import socket
import sys
import os

# For Windows console allocation
if os.name == "nt":
    import ctypes


def allocate_console_if_needed() -> None:
    """
    Allocate console for headless/debug mode if packaged as windowed app.
    This is primarily needed on Windows when the application is packaged
    without a console window but needs to display output.
    """
    if os.name == "nt":  # Windows-specific console allocation
        # Check if a console is already attached
        # GetStdHandle(-10) is STDIN, -11 is STDOUT, -12 is STDERR
        # If GetConsoleWindow is 0, it means no console is attached to the process
        # stdout_handle = ctypes.windll.kernel32.GetStdHandle(ctypes.c_ulong(-11))
        if ctypes.windll.kernel32.GetConsoleWindow() == 0:
            if ctypes.windll.kernel32.AllocConsole():
                # Redirect standard streams to the new console
                # Note: This might not be perfect for all scenarios, especially with input.
                # For more robust redirection, especially for input,
                # one might need to use CreateFile for CONIN$ and CONOUT$.
                sys.stdout = open("CONOUT$", "w")
                sys.stderr = open("CONOUT$", "w")
                sys.stdin = open("CONIN$", "r")
                print("Allocated a new console for headless/debug mode.")
            else:
                # This case should ideally not happen if AllocConsole is available
                # and no other console is attached by a parent process that AllocConsole would detect.
                print(
                    "Failed to allocate a new console.",
                    file=sys.stderr if sys.stderr else sys.__stderr__,
                )  # Fallback to original stderr
    # For other OS (Linux/macOS), console is typically available if launched from terminal.
    # If launched by double-clicking a .app bundle on macOS or a .desktop file on Linux
    # without a terminal, output might still go to system logs or be lost.
    # Handling for those cases is more complex and platform-specific.


def find_available_port(
    host: str, start_port: int, end_port: int = 65535
) -> int | None:
    """Scans for an available TCP port in a given range."""
    for port in range(start_port, end_port + 1):
        # Create the socket first; let creation errors propagate
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Use context manager to bind; __enter__ returns the sock (or mock)
            with sock as s:
                s.bind((host, port))
                return port
        except OSError:
            # Only suppress bind errors (port in use)
            continue
    return None
