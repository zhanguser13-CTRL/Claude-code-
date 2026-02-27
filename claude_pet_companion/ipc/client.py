#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPC Client for Claude Pet Companion

Client for connecting to the pet daemon IPC server.
"""
import socket
import threading
import time
import logging
from typing import Callable, Dict, Any, Optional, List
from queue import Queue, Empty

from .protocol import Message, MessageType, parse_message, create_message, build_hello_payload

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('IPCClient')


class IPCClient:
    """Client for connecting to the pet daemon"""

    def __init__(self, host: str = '127.0.0.1', port: int = 15340,
                 client_name: str = "python-client"):
        self.host = host
        self.port = port
        self.client_name = client_name
        self.version = "1.0.0"

        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.connecting = False

        # Threading
        self._receive_thread: Optional[threading.Thread] = None
        self._running = False

        # Message handling
        self._message_queue: Queue[Message] = Queue()
        self._response_waiters: Dict[str, Queue] = {}
        self._message_handlers: Dict[str, List[Callable]] = {}

        # Receive buffer
        self._buffer = ""

    def connect(self, timeout: float = 5.0) -> bool:
        """Connect to the IPC server"""
        if self.connected or self.connecting:
            logger.warning("Already connected or connecting")
            return False

        self.connecting = True

        try:
            logger.info(f"Connecting to {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(None)  # Remove timeout for normal operation

            self.connected = True
            self.connecting = False
            logger.info("Connected to IPC server")

            # Send hello handshake
            hello = create_message(
                MessageType.HELLO,
                payload=build_hello_payload(self.client_name, self.version)
            )
            self.send(hello)

            # Start receive thread
            self._running = True
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()

            return True

        except (socket.error, socket.timeout) as e:
            logger.error(f"Failed to connect: {e}")
            self.connecting = False
            if self.socket:
                self.socket.close()
                self.socket = None
            return False

    def disconnect(self):
        """Disconnect from the server"""
        if not self.connected:
            return

        logger.info("Disconnecting...")

        # Send goodbye
        try:
            goodbye = create_message(MessageType.GOODBYE)
            self.send(goodbye)
        except:
            pass

        # Stop receive thread
        self._running = False
        if self._receive_thread:
            self._receive_thread.join(timeout=1.0)

        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        self.connected = False

    def send(self, message: Message) -> bool:
        """Send a message to the server"""
        if not self.connected or not self.socket:
            logger.warning("Not connected")
            return False

        try:
            data = message.to_json() + '\n'
            self.socket.sendall(data.encode('utf-8'))
            return True
        except socket.error as e:
            logger.error(f"Error sending message: {e}")
            self.connected = False
            return False

    def send_request(self, message: Message, timeout: float = 5.0) -> Optional[Message]:
        """Send a request and wait for response"""
        if not self.send(message):
            return None

        # Create a waiter for this message
        response_queue = Queue()
        self._response_waiters[message.id] = response_queue

        try:
            response = response_queue.get(timeout=timeout)
            return response
        except Empty:
            logger.warning(f"Timeout waiting for response to {message.type}")
            return None
        finally:
            self._response_waiters.pop(message.id, None)

    def _receive_loop(self):
        """Receive loop running in separate thread"""
        while self._running and self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    logger.info("Server closed connection")
                    self.connected = False
                    break

                self._buffer += data.decode('utf-8')

                # Process complete messages
                while '\n' in self._buffer:
                    line, self._buffer = self._buffer.split('\n', 1)
                    if line.strip():
                        message = parse_message(line.strip())
                        if message:
                            self._handle_message(message)

            except socket.error as e:
                if self._running:
                    logger.error(f"Error receiving: {e}")
                    self.connected = False
                    break

    def _handle_message(self, message: Message):
        """Handle an incoming message"""
        # Check if anyone is waiting for this response
        if message.type.endswith('_response') or message.type == MessageType.ERROR.value:
            # Try to match with original message ID - improved matching logic
            matched = False
            for msg_id in list(self._response_waiters.keys()):
                waiter = self._response_waiters.get(msg_id)
                if waiter:
                    waiter.put(message)
                    matched = True
                    break
            if matched:
                return

        # Add to message queue
        self._message_queue.put(message)

        # Call registered handlers
        handlers = self._message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")

    def get_message(self, timeout: float = 0.1) -> Optional[Message]:
        """Get a message from the queue (non-blocking)"""
        try:
            return self._message_queue.get(timeout=timeout)
        except Empty:
            return None

    def on(self, message_type: str, handler: Callable[[Message], None]):
        """Register a handler for a message type"""
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)

    def off(self, message_type: str, handler: Callable[[Message], None]):
        """Unregister a handler for a message type"""
        if message_type in self._message_handlers:
            handlers = self._message_handlers[message_type]
            if handler in handlers:
                handlers.remove(handler)

    # Convenience methods

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get current pet status"""
        request = create_message(MessageType.STATUS)
        response = self.send_request(request)
        if response:
            return response.payload
        return None

    def send_action(self, action: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Send an action to the pet"""
        from .protocol import build_action_payload
        request = create_message(
            MessageType.ACTION,
            payload=build_action_payload(action, **kwargs)
        )
        response = self.send_request(request)
        if response:
            return response.payload
        return None

    def start_conversation(self, title: str, tags: List[str] = None) -> Optional[str]:
        """Start a new conversation"""
        from .protocol import build_conversation_start_payload
        request = create_message(
            MessageType.CONVERSATION_START,
            payload=build_conversation_start_payload(title, tags)
        )
        response = self.send_request(request)
        if response:
            return response.payload.get('conversation_id')
        return None

    def add_conversation_message(self, conversation_id: str, role: str,
                                 content: str, **kwargs) -> bool:
        """Add a message to a conversation"""
        from .protocol import build_conversation_message_payload
        request = create_message(
            MessageType.CONVERSATION_MESSAGE,
            payload=build_conversation_message_payload(
                conversation_id, role, content, **kwargs
            )
        )
        response = self.send_request(request)
        return response is not None

    def list_conversations(self, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """List all conversations"""
        request = create_message(
            MessageType.CONVERSATION_LIST,
            payload={'limit': limit}
        )
        response = self.send_request(request)
        if response:
            return response.payload.get('conversations')
        return None

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific conversation"""
        request = create_message(
            MessageType.CONVERSATION_GET,
            payload={'conversation_id': conversation_id}
        )
        response = self.send_request(request)
        if response:
            return response.payload
        return None

    def restore_context(self, conversation_id: str,
                        include_messages: bool = True) -> Optional[str]:
        """Restore context from a conversation"""
        from .protocol import build_restore_context_payload
        request = create_message(
            MessageType.RESTORE_CONTEXT,
            payload=build_restore_context_payload(conversation_id, include_messages)
        )
        response = self.send_request(request)
        if response:
            return response.payload.get('context')
        return None

    def ping(self) -> bool:
        """Send a ping to check if server is responsive"""
        request = create_message(MessageType.PING)
        response = self.send_request(request, timeout=2.0)
        return response is not None and response.type == MessageType.PONG.value

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


def check_server_running(host: str = '127.0.0.1', port: int = 15340) -> bool:
    """Check if an IPC server is running on the given host/port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False
