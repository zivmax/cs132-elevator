from typing import Optional, List, Tuple, Deque, Union  # Added Union
from collections import deque
import time  # Added for timestamping in add_msg_externally
import zmq  # Assuming zmq is imported, ensure it is
import threading  # Assuming threading is imported, ensure it is
from dataclasses import dataclass  # For command objects


# Define Command and Error objects
class BaseCommand:
    """Base class for all command objects."""

    pass


@dataclass
class CallCommand(BaseCommand):
    floor: int
    direction: str
    original_message: str


@dataclass
class SelectFloorCommand(BaseCommand):
    floor: int
    elevator_id: int
    original_message: str


@dataclass
class OpenDoorCommand(BaseCommand):
    elevator_id: int
    original_message: str


@dataclass
class CloseDoorCommand(BaseCommand):
    elevator_id: int
    original_message: str


@dataclass
class ResetCommand(BaseCommand):
    original_message: str


@dataclass
class ParseError(
    BaseCommand
):  # Inherits from BaseCommand for type consistency in return types
    original_message: str
    error_type: str  # e.g., "invalid_format", "invalid_parameter"
    detail: str


class ZmqClientThread(threading.Thread):

    def __init__(
        self, serverIp: str = "127.0.0.1", port: str = "19982", identity: str = "GroupX"
    ) -> None:
        threading.Thread.__init__(self)
        self.daemon = True  # Mark as daemon thread to allow graceful shutdown
        self.context: zmq.Context = zmq.Context()
        self.socket: zmq.Socket = self.context.socket(zmq.DEALER)
        self.serverIp: str = serverIp
        self.identity: str = identity
        self.port: str = port
        self.socket.setsockopt_string(
            zmq.IDENTITY, identity
        )  # default encoding is UTF-8 #Set your IDENTITY before connection.

        # Instead of single message, use queues to store multiple messages
        self.messageQueue: deque[str] = deque()  # Explicitly type if possible
        self.timestampQueue: deque[int] = deque()  # Explicitly type if possible
        self.lock = threading.Lock()  # Thread safety for queue operations

        self._stop_event = threading.Event()  # For gracefully stopping the thread

        # Keep the original variables for backwards compatibility
        self._received_message: Optional[str] = None
        self._message_timestamp: Optional[int] = None

        self.socket.connect(
            f"tcp://{serverIp}:{port}"
        )  # Both ("tcp://localhost:19982") and ("tcp://127.0.0.1:19982") are OK

        self.sendMsg(f"Client[{self.identity}] is online")  ##Telling server I'm online
        # self.start() # start() should be called by the creator of the thread instance.
        # ZmqCoordinator will call it.

    @property
    def message_timestamp(self) -> int:
        if self._message_timestamp == None:
            return -1  # Return a default value
        else:
            return self._message_timestamp

    @message_timestamp.setter
    def message_timestamp(self, value: int) -> None:
        self._message_timestamp = value

    @property
    def received_message(self) -> str:
        if self._received_message == None:
            return ""  # Return a default value
        else:
            return self._received_message

    @received_message.setter
    def received_message(self, value: str) -> None:
        self._received_message = value

    # Get all messages in the queue
    def get_all_messages(self) -> List[Tuple[str, int]]:
        with self.lock:
            # Make sure lists are created from deques before zipping
            return list(zip(list(self.messageQueue), list(self.timestampQueue)))

    # Get the latest message without removing it
    def peek_latest_message(self) -> Tuple[str, int]:
        with self.lock:
            if self.messageQueue:
                return self.messageQueue[-1], self.timestampQueue[-1]
            return ("", -1)

    # Get and remove the oldest message (FIFO)
    def get_next_message(self) -> Tuple[str, int]:
        with self.lock:
            if self.messageQueue:
                return self.messageQueue.popleft(), self.timestampQueue.popleft()
            return ("", -1)

    # Listen from the server
    # You can rewrite this part as long as it can receive messages from server.
    def __launch(self, socket: zmq.Socket) -> None:
        while not self._stop_event.is_set():
            if socket.closed:
                print("ZmqClientThread: Socket closed, listener terminating.")
                break

            try:
                # Check if stop event is set before each recv attempt
                if self._stop_event.is_set():
                    break

                message = socket.recv_string(
                    flags=zmq.NOBLOCK
                )  # Use NOBLOCK to avoid hanging if thread is asked to stop
                if message:  # Check if a message was actually received
                    timestamp = int(round(time.time() * 1000))
                    with self.lock:
                        self.messageQueue.append(message)
                        self.timestampQueue.append(timestamp)
                        # Update the single message properties for backward compatibility or other uses
                        self._received_message = message
                        self._message_timestamp = timestamp
            except zmq.Again:
                # No message received, sleep briefly and check stop event
                if self._stop_event.wait(
                    0.01
                ):  # Wait with timeout, returns True if event is set
                    break
            except zmq.ZMQError as e:
                if not self._stop_event.is_set():  # Only log if not shutting down
                    print(f"ZmqClientThread: ZMQ Error on recv: {e}")
                break  # Exit loop on error
            except Exception as e:  # Catch other potential exceptions during shutdown
                if not self._stop_event.is_set():  # Only log if not shutting down
                    print(f"ZmqClientThread: Error during __launch: {e}")
                break
        print("ZmqClientThread: Exited __launch loop.")

    # Override the function in threading.Thread
    def run(self) -> None:
        self.__launch(self.socket)

    # Send messages to the server
    # You can rewrite this part as long as you can send messages to server.
    def sendMsg(self, data: str) -> None:
        try:
            if hasattr(self, "socket") and not self.socket.closed:
                self.socket.send_string(data)
            else:
                print("socket is closed, can't send message...")
        except Exception as e:
            print(f"ZmqClientThread: Error sending message: {e}")

    def close(self) -> None:
        """Close the ZMQ socket and terminate the context."""
        try:
            if hasattr(self, "socket") and not self.socket.closed:
                self.socket.close()
                print("ZmqClientThread: Socket closed.")
            if hasattr(self, "context"):
                self.context.term()
                print("ZmqClientThread: Context terminated.")
        except Exception as e:
            print(f"ZmqClientThread: Error during close: {e}")

    def stop(self) -> None:
        """Signals the thread to stop and waits for it to finish."""
        print("ZmqClientThread: Stop called.")
        self._stop_event.set()
        # Close socket to unblock any potential recv operations
        try:
            if hasattr(self, "socket") and not self.socket.closed:
                self.socket.close()
        except Exception as e:
            print(f"ZmqClientThread: Error closing socket during stop: {e}")
        # self.join() # Ensure the thread has finished. ZmqCoordinator will call join.
        # It's often better to call close from the thread itself or after join.
        # For now, ZmqCoordinator will call close() after stopping.


class ZmqCoordinator:
    """
    Manages ZMQ client communication, including owning ZmqClientThread,
    queuing incoming messages, and providing methods to access them and send messages.
    """

    def __init__(self, identity: str, zmq_port: str = "19982"):  # Added zmq_port parameter
        """Initialize ZmqCoordinator, create and start ZmqClientThread."""
        self.zmq_client = ZmqClientThread(identity=identity, port=zmq_port)  # Pass port to ZmqClientThread
        # self._last_checked_timestamp: int = -1 # No longer needed with direct queue polling
        self._message_queue: Deque[Tuple[str, int]] = deque()  # Internal message queue

        if not self.zmq_client.is_alive():
            self.zmq_client.start()
        print(
            f"ZmqCoordinator: Initialized for identity '{identity}' on port {zmq_port}. ZmqClientThread started."
        )

    def poll_and_queue_incoming_messages(self):
        """
        Polls all available messages from ZmqClientThread's queue and adds them
        to ZmqCoordinator's internal message queue.
        """
        if not self.zmq_client:
            print("ZmqCoordinator: ZmqClientThread not available.")
            return

        while True:
            message, timestamp = self.zmq_client.get_next_message()
            if (
                not message and timestamp == -1
            ):  # Indicator for empty queue from ZmqClientThread
                break
            self._message_queue.append((message, timestamp))
            # print(f"ZmqCoordinator: Queued message from ZMQ: {message} at {timestamp}") # Optional debug

    def add_msg_externally(self, message: str, source: str = "External") -> None:
        """Add a message from a non-ZMQ source to the internal queue."""
        timestamp = int(round(time.time() * 1000))
        self._message_queue.append((message, timestamp))
        print(f"ZmqCoordinator: Message added to queue from {source}: {message}")

    def get_next_msg_for_processing(
        self,
    ) -> Tuple[Union[BaseCommand, ParseError, None], int]:  # Return type updated
        """Get the next message from the internal queue, parse it, and return a command/error object."""
        if self._message_queue:
            message_str, timestamp = self._message_queue.popleft()
            parsed_object = self._parse_message_to_command(message_str)
            return parsed_object, timestamp
        return None, -1  # Return None for the command part if queue is empty

    def has_queued_messages(self) -> bool:
        """Check if there are messages in the internal queue."""
        return len(self._message_queue) > 0

    def send_formatted_message_to_server(
        self,
        response_data: dict,
        command_context_str: str = "",
        parsed_elevator_id_for_response: Optional[int] = None,
    ) -> bool:
        """
        Formats the response data from ElevatorAPI into the required string format and sends it.
        Handles success and error responses.
        """
        message_to_send = ""
        if response_data.get("status") == "success":
            action_type = response_data.get("action")

            if (
                action_type == "open_door"
                and parsed_elevator_id_for_response is not None
            ):
                message_to_send = f"door_opened#{parsed_elevator_id_for_response}"
            elif (
                action_type == "close_door"
                and parsed_elevator_id_for_response is not None
            ):
                message_to_send = f"door_closed#{parsed_elevator_id_for_response}"
            # For other success types (call, select_floor, reset), no immediate message is sent back to the ZMQ client.
            # Floor arrival messages are handled by a different path (ElevatorAPI.send_floor_arrived_message).
            else:
                # Log success, but don't send a ZMQ message for these actions
                success_log_message = response_data.get(
                    "message",
                    f"Action '{action_type}' for command '{command_context_str}' processed successfully.",
                )
                print(
                    f"ZmqCoordinator: API action '{action_type}' successful. No ZMQ response required. Details: {success_log_message}"
                )
                return True  # Indicate successful handling (even if no message sent)

        elif response_data.get("status") == "error":
            error_action = response_data.get("action", "command_failed")
            error_detail_from_handler = response_data.get(
                "message", "unknown_handler_error"
            )
            error_detail_slug = "_".join(str(error_detail_from_handler).lower().split())
            message_to_send = f"error:{error_action}_failed:{error_detail_slug}"
            print(
                f"ZmqCoordinator: API Error from handler: {message_to_send} (Original command context: {command_context_str})"
            )

        elif (
            response_data.get("type") == "parse_error"
        ):  # For ParseError objects handled directly by API
            message_to_send = f"error:{response_data.get('error_type', 'unknown_parse_error')}:{response_data.get('detail', 'no_detail')}"
            print(f"ZmqCoordinator: API ParseError: {message_to_send}")

        elif (
            response_data.get("type") == "handler_processing_error"
        ):  # For exceptions during handler execution in API
            message_to_send = f"error:{response_data.get('error_type', 'handler_exception')}:{response_data.get('detail', 'no_detail')}"
            print(f"ZmqCoordinator: API Handler Exception: {message_to_send}")

        elif response_data.get("type") == "world_not_initialized_error":
            message_to_send = "error:world_not_initialized"
            print(f"ZmqCoordinator: API world not initialized: {message_to_send}")

        elif response_data.get("type") == "unknown_command_type_error":
            detail = response_data.get("detail", "no_detail")
            message_to_send = f"error:unknown_command_type:{detail}"
            print(f"ZmqCoordinator: API unknown command type: {message_to_send}")

        elif response_data.get("type") == "internal_processing_error":
            detail = response_data.get("detail", "no_detail")
            message_to_send = f"error:internal_processing_error:{detail}"
            print(f"ZmqCoordinator: API internal processing error: {message_to_send}")

        if message_to_send:
            return self.send_message_to_server(message_to_send)
        elif (
            not response_data
        ):  # Should not happen if API always provides some response_data
            print(
                f"ZmqCoordinator: Warning - No response data provided by API for command context: {command_context_str}"
            )
            # Potentially send a generic error, or rely on API to have already sent one.
            # For now, let's assume API handles sending errors if response_data is None/empty.
            return False

        return True  # If no message was explicitly required to be sent (e.g. successful call/select/reset)

    def send_message_to_server(self, message: str) -> bool:
        """Send a message to the ZMQ server via ZmqClientThread."""
        if not self.zmq_client:
            print("ZmqCoordinator: ZmqClientThread not available for sending.")
            return False
        try:
            self.zmq_client.sendMsg(message)
            return True
        except Exception as e:
            print(f"ZmqCoordinator: Error sending message: {e}")
            return False

    def stop(self):
        """Stops the ZmqClientThread."""
        if self.zmq_client:  # Check if zmq_client exists
            print("ZmqCoordinator: Stopping ZmqClientThread...")
            self.zmq_client.stop()  # Signal the thread to stop

            # Wait for the thread to finish with a shorter timeout first
            self.zmq_client.join(timeout=3)

            if self.zmq_client.is_alive():
                print(
                    "ZmqCoordinator: ZmqClientThread did not stop in time, forcing close."
                )
                # Try to close the context to force the socket to close
                try:
                    if hasattr(self.zmq_client, "context"):
                        self.zmq_client.context.term()
                except Exception as e:
                    print(f"ZmqCoordinator: Error terminating context: {e}")

                # Wait a bit more after forced termination
                self.zmq_client.join(timeout=1)

                if self.zmq_client.is_alive():
                    print(
                        "ZmqCoordinator: Warning - ZmqClientThread still alive after forced termination."
                    )
                    # Since the thread is daemon, it will be terminated when main thread exits
            else:
                print("ZmqCoordinator: ZmqClientThread stopped successfully.")

            # Clean up resources if needed
            try:
                if (
                    hasattr(self.zmq_client, "socket")
                    and not self.zmq_client.socket.closed
                ):
                    self.zmq_client.close()
            except Exception as e:
                print(f"ZmqCoordinator: Error during final cleanup: {e}")

        print("ZmqCoordinator: Stopped.")

    def _parse_message_to_command(
        self, message_str: str
    ) -> Union[BaseCommand, ParseError]:
        """Parses a raw message string into a command object or a ParseError."""
        original_msg_for_error = message_str
        try:
            if message_str.startswith("call_"):
                parts = message_str.split("@")
                direction_floor_part = parts[0].split("_")
                if len(parts) > 1 and len(direction_floor_part) > 1:
                    direction = direction_floor_part[1]
                    floor_str = parts[1]
                    # Convert floor -1 to 0, otherwise parse as int
                    floor = 0 if floor_str == "-1" else int(floor_str)
                    return CallCommand(
                        floor=floor, direction=direction, original_message=message_str
                    )
                else:
                    return ParseError(
                        original_message=original_msg_for_error,
                        error_type="invalid_call_format",
                        detail=message_str,
                    )
            elif message_str.startswith("select_floor@"):
                # Expected format: select_floor@FLOOR#ELEVATOR_ID
                # Example: select_floor@-1#1 or select_floor@3#2
                parts = message_str.split("@", 1)
                if len(parts) == 2:
                    floor_and_id_part = parts[1].split("#", 1)
                    if len(floor_and_id_part) == 2:
                        floor_str = floor_and_id_part[0]
                        elevator_id_str = floor_and_id_part[1]
                        # Convert floor -1 to 0, otherwise parse as int
                        floor = 0 if floor_str == "-1" else int(floor_str)
                        elevator_id = int(elevator_id_str)
                        return SelectFloorCommand(
                            floor=floor,
                            elevator_id=elevator_id,
                            original_message=message_str,
                        )
                # If parsing failed due to format, fall through to specific ParseError
                return ParseError(
                    original_message=original_msg_for_error,
                    error_type="invalid_select_floor_format",
                    detail=message_str,
                )
            elif message_str.startswith("open_door#"):
                elevator_id_str = message_str.split("#")[1]
                elevator_id = int(elevator_id_str)
                return OpenDoorCommand(
                    elevator_id=elevator_id, original_message=message_str
                )
            elif message_str.startswith("close_door#"):
                elevator_id_str = message_str.split("#")[1]
                elevator_id = int(elevator_id_str)
                return CloseDoorCommand(
                    elevator_id=elevator_id, original_message=message_str
                )
            elif message_str == "reset":
                return ResetCommand(original_message=message_str)
            else:
                return ParseError(
                    original_message=original_msg_for_error,
                    error_type="unknown_message_format",
                    detail=message_str,
                )
        except ValueError as ve:
            return ParseError(
                original_message=original_msg_for_error,
                error_type="invalid_parameter",
                detail=f"{message_str}:{str(ve)}",
            )
        except IndexError:
            return ParseError(
                original_message=original_msg_for_error,
                error_type="invalid_message_structure",
                detail=message_str,
            )
        except Exception as e:  # Catch any other unexpected parsing errors
            return ParseError(
                original_message=original_msg_for_error,
                error_type="parsing_error",
                detail=f"{message_str}:{str(e)}",
            )
