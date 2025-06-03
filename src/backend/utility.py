import socket


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
