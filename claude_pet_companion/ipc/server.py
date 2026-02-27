#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPC Server for Claude Pet Companion

TCP socket server that runs in the pet process and handles
communication from clients.
"""
import socket
import threading
import json
import logging
from typing import Callable, Dict, Any, Optional, List, Set
from pathlib import Path
import time

from .protocol import Message, MessageType, parse_message, create_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('IPCServer')


class ClientConnection:
    """Represents a connected client"""

    def __init__(self, conn: socket.socket, addr: tuple, client_id: str):
        self.conn = conn
        self.addr = addr
        self.client_id = client_id
        self.name = f"client-{client_id[:8]}"
        self.connected = True
        self.capabilities = []
        self.version = "unknown"

    def send(self, message: Message) -> bool:
        """Send a message to this client"""
        try:
            data = message.to_json() + '\n'
            self.conn.sendall(data.encode('utf-8'))
            return True
        except (socket.error, OSError) as e:
            logger.error(f"Error sending to {self.name}: {e}")
            self.connected = False
            return False

    def receive(self) -> Optional[Message]:
        """Receive a message from this client (non-blocking)"""
        try:
            self.conn.setblocking(False)
            data = self.conn.recv(4096)
            if not data:
                self.connected = False
                return None

            # Handle partial messages - buffer until newline
            if hasattr(self, '_buffer'):
                self._buffer += data.decode('utf-8')
            else:
                self._buffer = data.decode('utf-8')

            # Extract complete messages
            while '\n' in self._buffer:
                line, self._buffer = self._buffer.split('\n', 1)
                if line.strip():
                    msg = parse_message(line.strip())
                    if msg:
                        return msg
            return None
        except BlockingIOError:
            return None
        except (socket.error, OSError) as e:
            logger.error(f"Error receiving from {self.name}: {e}")
            self.connected = False
            return None

    def close(self):
        """Close the connection"""
        try:
            self.conn.close()
        except:
            pass
        self.connected = False


class MessageHandler:
    """Base class for handling IPC messages"""

    def handle_hello(self, message: Message, client: ClientConnection) -> Optional[Message]:
        """Handle client hello handshake"""
        client.name = message.payload.get('client_name', client.name)
        client.version = message.payload.get('version', 'unknown')
        client.capabilities = message.payload.get('capabilities', [])
        logger.info(f"Client connected: {client.name} v{client.version}")
        return create_message(
            MessageType.HELLO,
            payload={
                'server_name': 'Claude Pet Daemon',
                'version': '1.0.0',
                'client_id': client.client_id
            },
            source="server"
        )

    def handle_status(self, message: Message, client: ClientConnection,
                      pet_state: Dict[str, Any]) -> Optional[Message]:
        """Handle status request"""
        from .protocol import build_status_payload
        return create_message(
            MessageType.STATUS,
            payload=build_status_payload(pet_state),
            source="server"
        )

    def handle_action(self, message: Message, client: ClientConnection,
                      action_callback: Callable) -> Optional[Message]:
        """Handle action request"""
        action = message.payload.get('action')
        if not action:
            return message.error("Missing 'action' in payload")

        try:
            result = action_callback(action, message.payload)
            return create_message(
                MessageType.ACTION_RESPONSE,
                payload={
                    'action': action,
                    'success': True,
                    'result': result
                },
                source="server"
            )
        except Exception as e:
            return message.error(str(e))

    def handle_conversation_start(self, message: Message, client: ClientConnection,
                                  callback: Callable) -> Optional[Message]:
        """Handle conversation start"""
        try:
            result = callback(message.payload)
            return create_message(
                MessageType.CONVERSATION_START,
                payload=result,
                source="server"
            )
        except Exception as e:
            return message.error(str(e))

    def handle_conversation_list(self, message: Message, client: ClientConnection,
                                 callback: Callable) -> Optional[Message]:
        """Handle conversation list request"""
        try:
            result = callback(message.payload)
            return create_message(
                MessageType.CONVERSATION_LIST,
                payload=result,
                source="server"
            )
        except Exception as e:
            return message.error(str(e))

    def handle_conversation_get(self, message: Message, client: ClientConnection,
                                callback: Callable) -> Optional[Message]:
        """Handle conversation get request"""
        try:
            result = callback(message.payload)
            return create_message(
                MessageType.CONVERSATION_GET,
                payload=result,
                source="server"
            )
        except Exception as e:
            return message.error(str(e))

    def handle_restore_context(self, message: Message, client: ClientConnection,
                               callback: Callable) -> Optional[Message]:
        """Handle restore context request"""
        try:
            result = callback(message.payload)
            return create_message(
                MessageType.RESTORE_CONTEXT,
                payload=result,
                source="server"
            )
        except Exception as e:
            return message.error(str(e))

    def handle_ping(self, message: Message, client: ClientConnection) -> Optional[Message]:
        """Handle ping"""
        return create_message(MessageType.PONG, source="server")


class DefaultMessageHandler(MessageHandler):
    """Default implementation of message handler"""


class IPCServer:
    """IPC Server for pet daemon communication"""

    def __init__(self, host: str = '127.0.0.1', port: int = 15340,
                 handler: MessageHandler = None):
        self.host = host
        self.port = port
        self.handler = handler or DefaultMessageHandler()
        self.socket = None
        self.running = False
        self.thread = None

        # Connected clients
        self.clients: Dict[str, ClientConnection] = {}
        self.clients_lock = threading.Lock()

        # Callbacks for various operations
        self.action_callback: Optional[Callable] = None
        self.state_callback: Optional[Callable[[], Dict[str, Any]]] = None
        self.conversation_callbacks: Dict[str, Callable] = {}

        # Message queue for outbound messages
        self.broadcast_queue: List[Message] = []

    def set_action_callback(self, callback: Callable):
        """Set callback for handling actions"""
        self.action_callback = callback

    def set_state_callback(self, callback: Callable[[], Dict[str, Any]]):
        """Set callback for getting current pet state"""
        self.state_callback = callback

    def set_conversation_callback(self, name: str, callback: Callable):
        """Set a conversation-related callback"""
        self.conversation_callbacks[name] = callback

    def start(self, blocking: bool = False) -> bool:
        """Start the IPC server"""
        if self.running:
            logger.warning("IPC server already running")
            return False

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.socket.settimeout(1.0)  # Non-blocking accept

            self.running = True
            logger.info(f"IPC server listening on {self.host}:{self.port}")

            # Start server thread
            self.thread = threading.Thread(target=self._server_loop, daemon=True)
            self.thread.start()

            if blocking:
                self.thread.join()

            return True

        except OSError as e:
            logger.error(f"Failed to start IPC server: {e}")
            return False

    def stop(self):
        """Stop the IPC server"""
        if not self.running:
            return

        logger.info("Stopping IPC server...")
        self.running = False

        # Close all client connections
        with self.clients_lock:
            for client in list(self.clients.values()):
                client.close()
            self.clients.clear()

        # Close server socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        # Wait for thread to finish
        if self.thread:
            self.thread.join(timeout=2.0)

        logger.info("IPC server stopped")

    def _server_loop(self):
        """Main server loop"""
        client_counter = 0

        while self.running:
            # Accept new connections
            try:
                conn, addr = self.socket.accept()
                client_id = f"{time.time()}_{client_counter}"
                client_counter += 1

                client = ClientConnection(conn, addr, client_id)

                with self.clients_lock:
                    self.clients[client_id] = client

                logger.info(f"New connection from {addr}")

            except socket.timeout:
                pass
            except OSError as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
                continue

            # Process client messages
            self._process_clients()

            # Process broadcast queue
            self._process_broadcasts()

            time.sleep(0.01)  # Small sleep to prevent busy-waiting

    def _process_clients(self):
        """Process messages from all clients"""
        with self.clients_lock:
            disconnected = []

            for client_id, client in self.clients.items():
                # Receive messages
                message = client.receive()
                if message:
                    self._handle_message(message, client)

                # Check if disconnected
                if not client.connected:
                    disconnected.append(client_id)

            # Remove disconnected clients
            for client_id in disconnected:
                client = self.clients.pop(client_id)
                client.close()
                logger.info(f"Client disconnected: {client.name}")

    def _handle_message(self, message: Message, client: ClientConnection):
        """Handle an incoming message"""
        try:
            msg_type = message.type
            response = None

            if msg_type == MessageType.HELLO.value:
                response = self.handler.handle_hello(message, client)

            elif msg_type == MessageType.STATUS.value:
                if self.state_callback:
                    state = self.state_callback()
                    response = self.handler.handle_status(message, client, state)

            elif msg_type == MessageType.ACTION.value:
                if self.action_callback:
                    response = self.handler.handle_action(
                        message, client, self.action_callback
                    )

            elif msg_type == MessageType.CONVERSATION_START.value:
                callback = self.conversation_callbacks.get('start')
                if callback:
                    response = self.handler.handle_conversation_start(
                        message, client, callback
                    )

            elif msg_type == MessageType.CONVERSATION_LIST.value:
                callback = self.conversation_callbacks.get('list')
                if callback:
                    response = self.handler.handle_conversation_list(
                        message, client, callback
                    )

            elif msg_type == MessageType.CONVERSATION_GET.value:
                callback = self.conversation_callbacks.get('get')
                if callback:
                    response = self.handler.handle_conversation_get(
                        message, client, callback
                    )

            elif msg_type == MessageType.RESTORE_CONTEXT.value:
                callback = self.conversation_callbacks.get('restore')
                if callback:
                    response = self.handler.handle_restore_context(
                        message, client, callback
                    )

            elif msg_type == MessageType.PING.value:
                response = self.handler.handle_ping(message, client)

            # Send response if any
            if response:
                client.send(response)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            client.send(message.error(str(e)))

    def _process_broadcasts(self):
        """Process broadcast message queue"""
        if not self.broadcast_queue:
            return

        with self.clients_lock:
            messages = self.broadcast_queue.copy()
            self.broadcast_queue.clear()

        for message in messages:
            self.broadcast(message)

    def broadcast(self, message: Message):
        """Broadcast a message to all connected clients"""
        with self.clients_lock:
            disconnected = []

            for client_id, client in self.clients.items():
                if not client.send(message):
                    disconnected.append(client_id)

            # Remove disconnected clients
            for client_id in disconnected:
                client = self.clients.pop(client_id)
                client.close()

    def broadcast_state(self, state: Dict[str, Any]):
        """Broadcast state update to all clients"""
        from .protocol import build_status_payload
        message = create_message(
            MessageType.STATE_UPDATE,
            payload=build_status_payload(state),
            source="server"
        )
        self.broadcast(message)

    def broadcast_event(self, event_type: str, data: Dict[str, Any] = None):
        """Broadcast an event to all clients"""
        from .protocol import build_event_payload
        message = create_message(
            MessageType.EVENT,
            payload=build_event_payload(event_type, data),
            source="server"
        )
        self.broadcast(message)

    def is_running(self) -> bool:
        """Check if server is running"""
        return self.running

    def get_client_count(self) -> int:
        """Get number of connected clients"""
        with self.clients_lock:
            return len(self.clients)


# Singleton instance
_ipc_server: Optional[IPCServer] = None


def get_ipc_server() -> IPCServer:
    """Get or create the singleton IPC server"""
    global _ipc_server
    if _ipc_server is None:
        _ipc_server = IPCServer()
    return _ipc_server
