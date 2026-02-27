"""
Unit tests for SafeExpressionEvaluator

Tests the security and functionality of the safe expression evaluator
to ensure it properly blocks malicious code while allowing valid expressions.
"""

import pytest
from pathlib import Path
import sys

# Add security module to path
security_path = Path(__file__).parent.parent / 'claude_pet_companion' / 'security'
sys.path.insert(0, str(security_path))

from claude_pet_companion.security.safe_eval import (
    SafeExpressionEvaluator,
    eval_safe,
    validate_achievement_condition
)


class TestSafeExpressionEvaluator:
    """Test suite for SafeExpressionEvaluator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = SafeExpressionEvaluator()

    def test_basic_arithmetic(self):
        """Test basic arithmetic operations."""
        assert eval_safe("1 + 2") == 3
        assert eval_safe("10 - 5") == 5
        assert eval_safe("2 * 3") == 6
        assert eval_safe("10 / 2") == 5.0
        assert eval_safe("10 // 3") == 3
        assert eval_safe("10 % 3") == 1
        assert eval_safe("2 ** 3") == 8

    def test_comparisons(self):
        """Test comparison operations."""
        assert eval_safe("5 > 3") is True
        assert eval_safe("3 > 5") is False
        assert eval_safe("5 >= 5") is True
        assert eval_safe("5 < 10") is True
        assert eval_safe("5 <= 5") is True
        assert eval_safe("5 == 5") is True
        assert eval_safe("5 != 3") is True
        assert eval_safe("5 == 3") is False

    def test_boolean_logic(self):
        """Test boolean operations."""
        assert eval_safe("True and True") is True
        assert eval_safe("True and False") is False
        assert eval_safe("False or True") is True
        assert eval_safe("False or False") is False
        assert eval_safe("not False") is True
        assert eval_safe("not True") is False

    def test_complex_expressions(self):
        """Test complex combined expressions."""
        assert eval_safe("(5 + 3) * 2") == 16
        assert eval_safe("5 + 3 * 2") == 11
        assert eval_safe("(5 + 3) * (2 + 1)") == 24
        assert eval_safe("10 > 5 and 5 < 10") is True
        assert eval_safe("10 > 5 or 1 > 10") is True
        assert eval_safe("False and True") is False

    def test_variables(self):
        """Test variable substitution."""
        context = {"level": 50, "hp": 80, "xp": 1000}
        assert eval_safe("level", context) == 50
        assert eval_safe("level + 10", context) == 60
        assert eval_safe("level * 2", context) == 100
        assert eval_safe("level >= 10", context) is True
        assert eval_safe("hp > 50 and level > 10", context) is True

    def test_ternary_operator(self):
        """Test ternary/conditional expressions."""
        assert eval_safe("10 if True else 5") == 10
        assert eval_safe("10 if False else 5") == 5
        assert eval_safe("'yes' if 5 > 3 else 'no'") == "yes"

    def test_negative_numbers(self):
        """Test negative number handling."""
        assert eval_safe("-5") == -5
        assert eval_safe("5 + -3") == 2
        assert eval_safe("-5 * 2") == -10

    def test_unary_operators(self):
        """Test unary operators."""
        assert eval_safe("+5") == 5
        assert eval_safe("-5") == -5
        assert eval_safe("not True") is False

    def test_chained_comparisons(self):
        """Test chained comparisons."""
        assert eval_safe("1 < 5 < 10") is True
        assert eval_safe("1 < 5 > 3") is True
        assert eval_safe("10 > 5 < 20") is True


class TestSecurityBlocking:
    """Test suite for security blocking of malicious code."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = SafeExpressionEvaluator()

    def test_blocks_function_calls(self):
        """Test that function calls are blocked."""
        dangerous = [
            "print('hello')",
            "len([1,2,3])",
            "int('5')",
            "str(123)",
            "max(1,2,3)",
            "min(1,2,3)",
        ]
        for expr in dangerous:
            with pytest.raises(ValueError):
                self.evaluator.evaluate(expr)

    def test_blocks_imports(self):
        """Test that imports are blocked."""
        dangerous = [
            "__import__('os')",
            "__import__('sys')",
        ]
        for expr in dangerous:
            with pytest.raises(ValueError):
                self.evaluator.evaluate(expr)

    def test_blocks_attribute_access(self):
        """Test that attribute access is blocked."""
        dangerous = [
            "''.__class__",
            "[].__class__",
            "{}.__class__",
            "(1).__class__",
        ]
        for expr in dangerous:
            with pytest.raises(ValueError):
                self.evaluator.evaluate(expr)

    def test_blocks_subscript(self):
        """Test that subscript access is blocked."""
        dangerous = [
            "[1,2,3][0]",
            "{'a': 1}['a']",
            "'hello'[0]",
        ]
        for expr in dangerous:
            with pytest.raises(ValueError):
                self.evaluator.evaluate(expr)

    def test_blocks_lambda(self):
        """Test that lambda is blocked."""
        with pytest.raises(ValueError):
            self.evaluator.evaluate("lambda x: x + 1")

    def test_blocks_list_comprehensions(self):
        """Test that list comprehensions are blocked."""
        with pytest.raises(ValueError):
            self.evaluator.evaluate("[x for x in range(5)]")

    def test_blocks_dict_comprehensions(self):
        """Test that dict comprehensions are blocked."""
        with pytest.raises(ValueError):
            self.evaluator.evaluate("{x: x*2 for x in range(5)}")

    def test_blocks_exec(self):
        """Test that exec attempts are blocked."""
        dangerous = [
            "exec('print(1)')",
            "eval('1+1')",
        ]
        for expr in dangerous:
            with pytest.raises(ValueError):
                self.evaluator.evaluate(expr)

    def test_blocks_underscore_methods(self):
        """Test that dunder methods are blocked."""
        dangerous = [
            "__name__",
            "__file__",
            "__builtins__",
        ]
        for expr in dangerous:
            with pytest.raises(ValueError):
                self.evaluator.evaluate(expr)


class TestAchievementConditions:
    """Test achievement condition validation."""

    def test_simple_conditions(self):
        """Test simple achievement conditions."""
        class MockState:
            level = 10
            xp = 500
            hp = 80

        assert validate_achievement_condition("level >= 10", MockState()) is True
        assert validate_achievement_condition("level >= 50", MockState()) is False
        assert validate_achievement_condition("xp > 100", MockState()) is True

    def test_complex_conditions(self):
        """Test complex achievement conditions."""
        class MockState:
            level = 15
            xp = 1000
            hp = 80
            times_fed = 10

        assert validate_achievement_condition("level >= 10 and hp >= 50", MockState()) is True
        assert validate_achievement_condition("level >= 10 or hp >= 100", MockState()) is True
        assert validate_achievement_condition("times_fed >= 5 and level >= 10", MockState()) is True

    def test_invalid_variables(self):
        """Test that invalid variables are handled gracefully."""
        class MockState:
            level = 10

        # Should return False for undefined variables
        result = validate_achievement_condition("nonexistent >= 10", MockState())
        assert result is False


class TestWhitelisting:
    """Test variable whitelisting functionality."""

    def test_whitelist_allows_only_specified(self):
        """Test that whitelist only allows specified variables."""
        evaluator = SafeExpressionEvaluator(allowed_variables={'level', 'hp'})

        # Should work with allowed variables
        context = {'level': 10, 'hp': 80, 'xp': 500}
        assert evaluator.evaluate("level + 1", context) == 11

        # Should fail with non-allowed variables
        with pytest.raises(ValueError, match="not allowed"):
            evaluator.evaluate("xp + 1", context)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
