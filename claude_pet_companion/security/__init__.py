"""
Security Module

Contains security-related utilities for the Claude Pet Companion.
"""

from .safe_eval import (
    SafeExpressionEvaluator,
    eval_safe,
    validate_achievement_condition
)

from .ipc_middleware import (
    SecurityMiddleware,
    SecurityConfig,
    RateLimiter,
    TokenAuthenticator,
    IPFilter,
    MessageValidator,
    create_security_middleware
)

__all__ = [
    'SafeExpressionEvaluator',
    'eval_safe',
    'validate_achievement_condition',
    'SecurityMiddleware',
    'SecurityConfig',
    'RateLimiter',
    'TokenAuthenticator',
    'IPFilter',
    'MessageValidator',
    'create_security_middleware'
]
