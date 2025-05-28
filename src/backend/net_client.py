from PyQt6.QtCore import QThread, pyqtSignal
from typing import Callable, Optional, List, Tuple, Deque, Union  # Added Union
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


class ZmqClientThread(QThread):

    def __init__(
        self, serverIp: str = "127.0.0.1", port: str = "27132", identity: str = "GroupX"
    ) -> None:
        QThread.__init__(self)
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

        # Keep the original variables for backwards compatibility
        self._receivedMessage: Optional[str] = None
        self._messageTimeStamp: Optional[int] = None

        self.socket.connect(
            f"tcp://{serverIp}:{port}"
        )  # Both ("tcp://localhost:27132") and ("tcp://127.0.0.1:27132") are OK

        self.sendMsg(f"Client[{self.identity}] is online")  ##Telling server I'm online
        # self.start() # start() should be called by the creator of the thread instance.
        # ZmqCoordinator will call it.

    @property
    def messageTimeStamp(self) -> int:
        if self._messageTimeStamp == None:
            return -1  # Return a default value
        else:
            return self._messageTimeStamp

    @messageTimeStamp.setter
    def messageTimeStamp(self, value: int) -> None:
        self._messageTimeStamp = value

    @property
    def receivedMessage(self) -> str:
        if self._receivedMessage == None:
            return ""  # Return a default value
        else:
            return self._receivedMessage

    @receivedMessage.setter
    def receivedMessage(self, value: str) -> None:
        self._receivedMessage = value

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
        while True:
            if not socket.closed:
                try:
                    message = socket.recv_string(
                        flags=zmq.NOBLOCK
                    )  # Use NOBLOCK to avoid hanging if thread is asked to stop
                    if message:  # Check if a message was actually received
                        timestamp = int(round(time.time() * 1000))
                        with self.lock:
                            self.messageQueue.append(message)
                            self.timestampQueue.append(timestamp)
                            # Update the single message properties for backward compatibility or other uses
                            self._receivedMessage = message
                            self._messageTimeStamp = timestamp
                    else:
                        # Short sleep if no message to prevent busy-waiting if NOBLOCK is used
                        time.sleep(0.01)
                except zmq.Again:
                    # No message received, sleep briefly
                    time.sleep(0.01)
                except zmq.ZMQError as e:
                    print(f"ZmqClientThread: ZMQ Error on recv: {e}")
                    break  # Exit loop on error
            else:
                print("ZmqClientThread: Socket closed, listener terminating.")
                break

    # Override the function in threading.Thread
    def run(self) -> None:
        self.__launch(self.socket)

    # Send messages to the server
    # You can rewrite this part as long as you can send messages to server.
    def sendMsg(self, data: str) -> None:
        if not self.socket.closed:
            self.socket.send_string(data)
        else:
            print("socket is closed,can't send message...")

    def close(self):
        """Close the ZMQ socket and terminate the context."""
        if not self.socket.closed:
            self.socket.close()
            self.context.term()


class ZmqCoordinator:
    """
    Manages ZMQ client communication, including owning ZmqClientThread,
    queuing incoming messages, and providing methods to access them and send messages.
    """

    def __init__(self, identity: str):  # Removed world_add_msg_callback
        """Initialize ZmqCoordinator, create and start ZmqClientThread."""
        self.zmq_client = ZmqClientThread(identity=identity)
        # self._last_checked_timestamp: int = -1 # No longer needed with direct queue polling
        self._message_queue: Deque[Tuple[str, int]] = deque()  # Internal message queue

        if not self.zmq_client.isRunning():
            self.zmq_client.start()
        print(
            f"ZmqCoordinator: Initialized for identity '{identity}'. ZmqClientThread started."
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
            if self.zmq_client.isRunning():
                self.zmq_client.quit()  # Ask QThread to exit its event loop (if it has one, otherwise use terminate)
                self.zmq_client.wait(5000)  # Wait for thread to finish
            if (
                not self.zmq_client.isFinished()
            ):  # If still not finished, force termination
                self.zmq_client.terminate()
                self.zmq_client.wait(1000)
            self.zmq_client.close()  # Close ZMQ socket and context
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
                    floor = int(parts[1])
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
                parts = message_str.split("@")[1].split("#")
                if len(parts) > 1:
                    floor = int(parts[0])
                    elevator_id = int(parts[1])
                    return SelectFloorCommand(
                        floor=floor,
                        elevator_id=elevator_id,
                        original_message=message_str,
                    )
                else:
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
