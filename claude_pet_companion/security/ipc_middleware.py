"""
IPC Security Middleware

Provides security enhancements for IPC communication including:
- Connection token authentication
- Message size limits
- Rate limiting
- Input validation
- IP whitelist/blacklist support
"""

import time
import hashlib
import hmac
import socket
import threading
from typing import Dict, Any, Optional, Set, Callable, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network
import secrets
import json

from ..ipc.protocol import Message


@dataclass
class SecurityConfig:
    """Configuration for IPC security."""
    # Authentication
    enable_auth: bool = True
    shared_secret: Optional[str] = None  # If None, generates a random one
    token_ttl: int = 3600  # Token time-to-live in seconds

    # Rate limiting
    enable_rate_limit: bool = True
    max_messages_per_minute: int = 100
    max_messages_per_second: int = 10

    # Message size
    max_message_size: int = 1024 * 1024  # 1MB default
    max_payload_size: int = 512 * 1024   # 512KB default

    # IP filtering
    allowed_ips: Set[str] = field(default_factory=lambda: {'127.0.0.1', '::1'})
    blocked_ips: Set[str] = field(default_factory=set)

    # Message validation
    validate_message_types: bool = True
    allowed_message_types: Optional[Set[str]] = None  # None = all types allowed

    # Connection limits
    max_connections_per_ip: int = 5
    max_total_connections: int = 50


class RateLimiter:
    """Token bucket rate limiter for IPC messages."""

    def __init__(self, max_per_second: int = 10, max_per_minute: int = 100):
        self.max_per_second = max_per_second
        self.max_per_minute = max_per_minute
        self.lock = threading.Lock()

        # Track requests per client
        self.secondly_requests: Dict[str, deque] = defaultdict(deque)
        self.minutely_requests: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, client_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a request from this client is allowed.

        Returns:
            Tuple of (allowed, reason)
        """
        with self.lock:
            now = time.time()

            # Clean old requests
            self._clean_old_requests(client_id, now)

            # Check secondly limit
            secondly_count = len(self.secondly_requests[client_id])
            if secondly_count >= self.max_per_second:
                return False, f"Rate limit exceeded: {secondly_count} requests in last second"

            # Check minutely limit
            minutely_count = len(self.minutely_requests[client_id])
            if minutely_count >= self.max_per_minute:
                return False, f"Rate limit exceeded: {minutely_count} requests in last minute"

            # Record this request
            self.secondly_requests[client_id].append(now)
            self.minutely_requests[client_id].append(now)

            return True, None

    def _clean_old_requests(self, client_id: str, now: float):
        """Remove old request records."""
        # Clean requests older than 1 second
        while self.secondly_requests[client_id]:
            if now - self.secondly_requests[client_id][0] > 1.0:
                self.secondly_requests[client_id].popleft()
            else:
                break

        # Clean requests older than 1 minute
        while self.minutely_requests[client_id]:
            if now - self.minutely_requests[client_id][0] > 60.0:
                self.minutely_requests[client_id].popleft()
            else:
                break

    def reset_client(self, client_id: str):
        """Reset rate limiting for a specific client."""
        with self.lock:
            self.secondly_requests.pop(client_id, None)
            self.minutely_requests.pop(client_id, None)


class TokenAuthenticator:
    """Handles token-based authentication for IPC connections."""

    def __init__(self, shared_secret: Optional[str] = None, token_ttl: int = 3600):
        self.shared_secret = shared_secret or secrets.token_hex(32)
        self.token_ttl = token_ttl
        self.issued_tokens: Dict[str, float] = {}
        self.lock = threading.Lock()

    def generate_token(self, client_id: str) -> str:
        """Generate an authentication token for a client."""
        timestamp = time.time()
        data = f"{client_id}:{timestamp}".encode('utf-8')

        # Create HMAC signature
        signature = hmac.new(
            self.shared_secret.encode('utf-8'),
            data,
            hashlib.sha256
        ).hexdigest()

        token = f"{client_id}:{int(timestamp)}:{signature}"
        return token

    def validate_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an authentication token.

        Returns:
            Tuple of (is_valid, client_id or error_message)
        """
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False, "Invalid token format"

            client_id, timestamp_str, signature = parts
            timestamp = float(timestamp_str)

            # Check token age
            age = time.time() - timestamp
            if age > self.token_ttl:
                return False, "Token expired"

            if age < 0:
                return False, "Token timestamp is in the future"

            # Verify signature
            data = f"{client_id}:{timestamp}".encode('utf-8')
            expected_signature = hmac.new(
                self.shared_secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                return False, "Invalid token signature"

            return True, client_id

        except (ValueError, IndexError) as e:
            return False, f"Token validation error: {e}"

    def revoke_token(self, client_id: str):
        """Revoke a client's token."""
        with self.lock:
            # Remove all tokens for this client
            to_remove = [k for k in self.issued_tokens.keys() if k.startswith(client_id)]
            for key in to_remove:
                del self.issued_tokens[key]

    def clean_expired_tokens(self):
        """Remove expired tokens from the issued tokens dict."""
        now = time.time()
        with self.lock:
            expired = [k for k, v in self.issued_tokens.items() if now - v > self.token_ttl]
            for key in expired:
                del self.issued_tokens[key]


class IPFilter:
    """IP address filtering for connections."""

    def __init__(self, allowed_ips: Set[str] = None, blocked_ips: Set[str] = None):
        self.allowed_ips = allowed_ips or {'127.0.0.1', '::1'}
        self.blocked_ips = blocked_ips or set()

        # Convert to ip_network objects for CIDR support
        self.allowed_networks = [ip_network(ip) for ip in self.allowed_ips]
        self.blocked_networks = [ip_network(ip) for ip in self.blocked_ips]

    def is_allowed(self, ip_str: str) -> Tuple[bool, Optional[str]]:
        """
        Check if an IP address is allowed to connect.

        Returns:
            Tuple of (allowed, reason)
        """
        try:
            ip = ip_address(ip_str)

            # Check blocked list first
            for network in self.blocked_networks:
                if ip in network:
                    return False, f"IP {ip_str} is blocked"

            # If no allowed list, all non-blocked IPs are allowed
            if not self.allowed_networks:
                return True, None

            # Check allowed list
            for network in self.allowed_networks:
                if ip in network:
                    return True, None

            return False, f"IP {ip_str} is not in allowed list"

        except ValueError as e:
            return False, f"Invalid IP address: {e}"


class MessageValidator:
    """Validates incoming messages for security."""

    def __init__(self, config: SecurityConfig):
        self.config = config

    def validate_message(self, message: Message) -> Tuple[bool, Optional[str]]:
        """
        Validate a message for security issues.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check message size
        message_json = message.to_json()
        if len(message_json) > self.config.max_message_size:
            return False, f"Message too large: {len(message_json)} bytes"

        # Check payload size
        payload_json = json.dumps(message.payload)
        if len(payload_json) > self.config.max_payload_size:
            return False, f"Payload too large: {len(payload_json)} bytes"

        # Validate message type
        if self.config.allowed_message_types:
            if message.type not in self.config.allowed_message_types:
                return False, f"Message type '{message.type}' not allowed"

        # Check for suspicious patterns in payload
        error = self._check_payload_patterns(message.payload)
        if error:
            return False, error

        return True, None

    def _check_payload_patterns(self, payload: Dict[str, Any]) -> Optional[str]:
        """Check payload for potentially dangerous patterns."""
        if not isinstance(payload, dict):
            return None

        # Convert to string for pattern matching
        payload_str = json.dumps(payload)

        # Check for suspicious patterns
        dangerous_patterns = [
            '__import__',
            '__builtins__',
            'eval(',
            'exec(',
            'compile(',
            'open(',
            'file(',
            '<script>',
            'javascript:',
            'data:text/html',
        ]

        for pattern in dangerous_patterns:
            if pattern in payload_str:
                return f"Suspicious pattern detected: {pattern}"

        return None


class SecurityMiddleware:
    """
    Main security middleware for IPC communication.

    Integrates all security components.
    """

    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()

        # Initialize security components
        self.auth = TokenAuthenticator(
            self.config.shared_secret,
            self.config.token_ttl
        )
        self.rate_limiter = RateLimiter(
            self.config.max_messages_per_second,
            self.config.max_messages_per_minute
        )
        self.ip_filter = IPFilter(
            self.config.allowed_ips,
            self.config.blocked_ips
        )
        self.validator = MessageValidator(self.config)

        # Track authenticated clients and their IPs
        self.authenticated_clients: Dict[str, str] = {}
        self.client_ips: Dict[str, str] = {}
        self.ip_connection_counts: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()

    def check_connection(self, client_addr: Tuple[str, int]) -> Tuple[bool, Optional[str]]:
        """
        Check if a connection should be allowed.

        Returns:
            Tuple of (allowed, reason)
        """
        ip, _port = client_addr

        # Check IP filter
        if self.config.allowed_ips or self.config.blocked_ips:
            allowed, reason = self.ip_filter.is_allowed(ip)
            if not allowed:
                return False, reason

        # Check connection limits
        with self.lock:
            # Check total connections
            total_connections = len(self.client_ips)
            if total_connections >= self.config.max_total_connections:
                return False, "Maximum total connections reached"

            # Check per-IP connections
            ip_count = self.ip_connection_counts[ip]
            if ip_count >= self.config.max_connections_per_ip:
                return False, f"Maximum connections per IP reached for {ip}"

        return True, None

    def register_connection(self, client_id: str, client_addr: Tuple[str, int]):
        """Register a new connection."""
        ip, _port = client_addr
        with self.lock:
            self.client_ips[client_id] = ip
            self.ip_connection_counts[ip] += 1

    def unregister_connection(self, client_id: str):
        """Unregister a connection."""
        with self.lock:
            if client_id in self.client_ips:
                ip = self.client_ips[client_id]
                self.ip_connection_counts[ip] -= 1
                if self.ip_connection_counts[ip] <= 0:
                    del self.ip_connection_counts[ip]
                del self.client_ips[client_id]

            self.authenticated_clients.pop(client_id, None)
            self.rate_limiter.reset_client(client_id)

    def authenticate(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Authenticate a client using a token.

        Returns:
            Tuple of (authenticated, client_id or error_message)
        """
        if not self.config.enable_auth:
            return True, None

        is_valid, result = self.auth.validate_token(token)
        if is_valid:
            client_id = result
            self.authenticated_clients[client_id] = token
            return True, client_id

        return False, result

    def check_rate_limit(self, client_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a client is within rate limits.

        Returns:
            Tuple of (allowed, reason)
        """
        if not self.config.enable_rate_limit:
            return True, None

        return self.rate_limiter.is_allowed(client_id)

    def validate_message(self, message: Message, client_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an incoming message.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check rate limit
        allowed, reason = self.check_rate_limit(client_id)
        if not allowed:
            return False, reason

        # Validate message content
        if self.config.validate_message_types:
            is_valid, error = self.validator.validate_message(message)
            if not is_valid:
                return False, error

        return True, None

    def generate_token(self, client_id: str) -> str:
        """Generate an authentication token for a client."""
        return self.auth.generate_token(client_id)

    def get_shared_secret(self) -> str:
        """Get the shared secret (for debugging/testing)."""
        return self.auth.shared_secret


def create_security_middleware(
    enable_auth: bool = True,
    shared_secret: Optional[str] = None,
    max_message_size: int = 1024 * 1024,
    allowed_ips: Optional[Set[str]] = None
) -> SecurityMiddleware:
    """
    Convenience function to create a security middleware.

    Args:
        enable_auth: Whether to enable authentication
        shared_secret: Shared secret for token generation
        max_message_size: Maximum message size in bytes
        allowed_ips: Set of allowed IP addresses

    Returns:
        Configured SecurityMiddleware instance
    """
    config = SecurityConfig(
        enable_auth=enable_auth,
        shared_secret=shared_secret,
        max_message_size=max_message_size,
        allowed_ips=allowed_ips or {'127.0.0.1', '::1'}
    )
    return SecurityMiddleware(config)


if __name__ == "__main__":
    # Test the security middleware
    print("Testing IPC Security Middleware")

    # Create middleware
    middleware = create_security_middleware(
        enable_auth=True,
        allowed_ips={'127.0.0.1'}
    )

    # Test token generation
    token = middleware.generate_token("test_client")
    print(f"Generated token: {token[:50]}...")

    # Test token validation
    is_valid, result = middleware.authenticate(token)
    print(f"Token valid: {is_valid}, client_id: {result}")

    # Test invalid token
    is_valid, result = middleware.authenticate("invalid_token")
    print(f"Invalid token: {is_valid}, error: {result}")

    # Test connection check
    allowed, reason = middleware.check_connection(("127.0.0.1", 12345))
    print(f"Localhost connection: {allowed}, reason: {reason}")

    allowed, reason = middleware.check_connection(("192.168.1.1", 12345))
    print(f"Remote connection: {allowed}, reason: {reason}")

    print("\nShared secret:", middleware.get_shared_secret()[:20] + "...")
