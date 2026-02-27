"""
Unit Tests for IPC Security

Tests the security middleware for IPC communication.
"""

import pytest
import time
import socket
import threading
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pet_companion.security.ipc_middleware import (
    SecurityMiddleware,
    SecurityConfig,
    RateLimiter,
    TokenAuthenticator,
    IPFilter,
    create_security_middleware,
)


class TestSecurityConfig:
    """Test SecurityConfig creation and defaults."""

    def test_default_config(self):
        """Test default security configuration."""
        config = SecurityConfig()
        assert config.enable_auth is True
        assert config.enable_rate_limit is True
        assert config.max_message_size == 1024 * 1024
        assert config.allowed_ips == {'127.0.0.1', '::1'}


class TestRateLimiter:
    """Test rate limiting functionality."""

    def test_rate_limit_within_limit(self):
        """Test that requests within limit are allowed."""
        limiter = RateLimiter(max_per_second=10, max_per_minute=100)

        for _ in range(10):
            allowed, reason = limiter.is_allowed("client1")
            assert allowed, f"Should be allowed: {reason}"

    def test_rate_limit_exceeded(self):
        """Test that rate limit is enforced."""
        limiter = RateLimiter(max_per_second=2, max_per_minute=10)

        # Use up the rate limit
        for _ in range(2):
            limiter.is_allowed("client1")

        # Next request should be blocked
        allowed, reason = limiter.is_allowed("client1")
        assert not allowed, "Should be rate limited"
        assert "rate limit" in reason.lower()

    def test_different_clients_separate_limits(self):
        """Test that different clients have separate limits."""
        limiter = RateLimiter(max_per_second=5)

        # Client 1 uses 3 requests
        for _ in range(3):
            limiter.is_allowed("client1")

        # Client 2 should still have full allowance
        for _ in range(5):
            allowed, _ = limiter.is_allowed("client2")
            assert allowed, "Client 2 should not be affected by client 1"

    def test_rate_limit_reset(self):
        """Test that rate limit resets properly."""
        limiter = RateLimiter(max_per_second=1)
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")

        # Should be blocked now
        allowed, _ = limiter.is_allowed("client1")
        assert not allowed

        # Reset
        limiter.reset_client("client1")

        # Should be allowed again
        allowed, _ = limiter.is_allowed("client1")
        assert allowed


class TestTokenAuthenticator:
    """Test token-based authentication."""

    def test_token_generation(self):
        """Test token generation."""
        auth = TokenAuthenticator(shared_secret="test_secret")
        token = auth.generate_token("client1")

        assert "client1" in token
        assert len(token.split(':')) >= 3

    def test_valid_token(self):
        """Test valid token validation."""
        auth = TokenAuthenticator(shared_secret="test_secret")
        token = auth.generate_token("client1")

        is_valid, result = auth.validate_token(token)

        assert is_valid
        assert result == "client1"

    def test_invalid_token(self):
        """Test invalid token validation."""
        auth = TokenAuthenticator(shared_secret="test_secret")

        is_valid, result = auth.validate_token("invalid_token")

        assert not is_valid
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_expired_token(self):
        """Test expired token validation."""
        auth = TokenAuthenticator(shared_secret="test_secret", token_ttl=0.1)
        token = auth.generate_token("client1")

        time.sleep(0.2)

        is_valid, result = auth.validate_token(token)
        assert not is_valid, "Token should be expired"
        assert "expired" in result.lower()

    def test_wrong_secret(self):
        """Test token with wrong secret fails."""
        auth1 = TokenAuthenticator(shared_secret="secret1")
        auth2 = TokenAuthenticator(shared_secret="secret2")

        token = auth1.generate_token("client1")

        is_valid, _ = auth2.validate_token(token)
        assert not is_valid, "Token with different secret should be invalid"


class TestIPFilter:
    """Test IP filtering functionality."""

    def test_allowed_ip(self):
        """Test that allowed IPs pass filter."""
        filter = IPFilter(allowed_ips={'192.168.1.1', '127.0.0.1'})

        allowed, _ = filter.is_allowed('127.0.0.1')
        assert allowed

    def test_blocked_ip(self):
        """Test that non-allowed IPs are blocked."""
        filter = IPFilter(allowed_ips={'192.168.1.1'})

        allowed, _ = filter.is_allowed('10.0.0.1')
        assert not allowed

    def test_blocked_list(self):
        """Test explicitly blocked IPs."""
        filter = IPFilter(
            allowed_ips={'0.0.0.0', '::'},
            blocked_ips={'192.168.1.100'}
        )

        allowed, _ = filter.is_allowed('192.168.1.100')
        assert not allowed, "Blocked IP should be rejected"

    def test_cidr_notation(self):
        """Test CIDR notation in allowed list."""
        filter = IPFilter(allowed_ips={'192.168.1.0/24'})

        allowed, _ = filter.is_allowed('192.168.1.50')
        assert allowed, "IP in CIDR range should be allowed"

        allowed, _ = filter.is_allowed('192.168.2.50')
        assert not allowed, "IP outside CIDR range should be blocked"


class TestSecurityMiddleware:
    """Test security middleware integration."""

    def test_connection_check_allowed(self):
        """Test allowed connection."""
        middleware = create_security_middleware(
            allowed_ips={'127.0.0.1'},
            enable_auth=True
        )

        allowed, reason = middleware.security.check_connection(('127.0.0.1', 12345))
        assert allowed
        assert middleware.security.check_connection(('10.0.0.1', 12345))[0] is False

    def test_message_validation(self):
        """Test message validation."""
        middleware = create_security_middleware()

        # Valid message
        from claude_pet_companion.ipc.protocol import Message, MessageType
        msg = Message(type=MessageType.HELLO, payload={'test': 'data'})

        is_valid, error = middleware.security.validate_message(msg, "client1")
        assert is_valid

    def test_oversized_message(self):
        """Test that oversized messages are rejected."""
        middleware = create_security_middleware(max_message_size=100)

        from claude_pet_companion.ipc.protocol import Message, MessageType

        # Create message with large payload
        large_payload = {'data': 'x' * 1000}
        msg = Message(type=MessageType.HELLO, payload=large_payload)

        is_valid, error = middleware.security.validate_message(msg, "client1")
        assert not is_valid
        assert "size" in error.lower()

    def test_rate_limiting(self):
        """Test rate limiting on messages."""
        middleware = create_security_middleware(
            max_messages_per_second=5
        )

        from claude_pet_companion.ipc.protocol import Message, MessageType
        msg = Message(type=MessageType.HELLO, payload={})

        # Send 5 messages quickly
        for i in range(5):
            is_valid, _ = middleware.security.validate_message(msg, f"client{i}")
            assert is_valid, f"Message {i+1} should be allowed"

        # 6th message should be rate limited
        is_valid, error = middleware.security.validate_message(msg, "client6")
        assert not is_valid
        assert "rate" in error.lower() or "limit" in error.lower()


@pytest.mark.legacy
def test_message_input_validation_with_safe_eval():
    """Legacy test for message input validation."""
    # Tests that suspicious patterns are blocked
    from claude_pet_companion.security.ipc_middleware import MessageValidator

    validator = MessageValidator(SecurityConfig())

    # Test malicious patterns
    malicious_payloads = [
        {'command': '__import__("os").system("ls")'},
        {'eval': 'print("hello")'},
        {'exec': 'exit(1)'},
        {'code': 'eval(input())'},
    ]

    for payload in malicious_payloads:
        from claude_pet_companion.ipc.protocol import Message, MessageType
        msg = Message(type=MessageType.HELLO, payload=payload)
        is_valid, error = validator.validate_message(msg)
        assert not is_valid, f"Malicious payload should be rejected: {error}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
