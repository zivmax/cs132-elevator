import socket


def find_available_port(
    host: str, start_port: int, end_port: int = 65535
) -> int | None:
    """Scans for an available TCP port in a given range."""
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return port
        except OSError:
            continue  # Port is already in use
    return None
