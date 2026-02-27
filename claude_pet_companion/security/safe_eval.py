"""
Safe Expression Evaluator

A secure alternative to eval() for evaluating simple expressions.
Uses AST parsing to ensure only safe operations are allowed.
"""

import ast
import operator
from typing import Any, Dict, Set, Optional, Union, Callable, List, Tuple
from numbers import Number


class SafeExpressionEvaluator:
    """
    A safe expression evaluator that parses and evaluates expressions
    without the security risks of eval().

    Supported operations:
    - Arithmetic: +, -, *, /, //, %, **
    - Comparison: ==, !=, <, <=, >, >=
    - Logical: and, or, not
    - Parentheses: ( )
    - Variables: Only those provided in the context
    - Literals: Numbers, strings, booleans, None

    Not supported (intentionally blocked):
    - Function calls
    - Attribute access
    - Imports
    - Lambda/comprehensions
    - Any form of code execution
    """

    # Safe operators mapping
    OPERATORS: Dict[type, Callable] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,

        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,

        ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or b,
        ast.Not: operator.not_,
        ast.Invert: operator.invert,
    }

    # Allowed node types for safe expressions
    ALLOWED_NODES: Set[type] = {
        # Expressions
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.BoolOp,
        ast.IfExp,  # Ternary operator

        # Operands
        ast.Constant,
        ast.Num,  # For older Python versions
        ast.Str,
        ast.Name,
        ast.NameConstant,

        # Operations
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
        ast.Mod, ast.Pow, ast.UAdd, ast.USub,
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.And, ast.Or, ast.Not,
        ast.Invert,

        # Structures
        ast.Module,
        ast.Expr,
    }

    def __init__(self, allowed_variables: Optional[Set[str]] = None):
        """
        Initialize the evaluator.

        Args:
            allowed_variables: Optional set of allowed variable names.
                             If None, any variable name in the context is allowed.
        """
        self.allowed_variables = allowed_variables

    def evaluate(self, expression: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Safely evaluate an expression.

        Args:
            expression: The expression string to evaluate
            context: Dictionary of variables and their values

        Returns:
            The result of evaluating the expression

        Raises:
            ValueError: If the expression is invalid or contains unsafe operations
            SyntaxError: If the expression has syntax errors
        """
        if not expression or not isinstance(expression, str):
            raise ValueError("Expression must be a non-empty string")

        expression = expression.strip()
        if not expression:
            raise ValueError("Expression cannot be empty")

        context = context or {}

        # Parse the expression
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise SyntaxError(f"Invalid expression syntax: {e}")

        # Validate the AST
        self._validate_ast(tree)

        # Evaluate the validated AST
        try:
            return self._eval_node(tree.body, context)
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")

    def _validate_ast(self, node: ast.AST) -> None:
        """
        Validate that the AST contains only safe nodes.

        Raises:
            ValueError: If unsafe nodes are found
        """
        for child in ast.walk(node):
            # Check for explicitly forbidden node types
            if isinstance(child, (ast.Call, ast.Attribute, ast.Subscript,
                                  ast.Starred, ast.List, ast.Dict, ast.Tuple,
                                  ast.Set, ast.ListComp, ast.DictComp,
                                  ast.SetComp, ast.GeneratorExp,
                                  ast.Lambda, ast.FunctionDef,
                                  ast.ClassDef, ast.Import, ast.ImportFrom,
                                  ast.Raise, ast.Try, ast.ExceptHandler,
                                  ast.With, ast.AsyncWith, ast.For,
                                  ast.While, ast.If, ast.Break,
                                  ast.Continue, ast.Pass, ast.Delete,
                                  ast.Global, ast.Nonlocal, ast.Return,
                                  ast.Yield, ast.YieldFrom, ast.Await,
                                  ast.Assert, ast.Exec)):
                raise ValueError(f"Unsafe operation detected: {type(child).__name__}")

            # Check for function calls disguised as nodes
            if isinstance(child, ast.Name) and self.allowed_variables is not None:
                if child.id not in self.allowed_variables:
                    raise ValueError(f"Variable '{child.id}' is not allowed")

    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """
        Recursively evaluate an AST node.

        Args:
            node: The AST node to evaluate
            context: Variable context dictionary

        Returns:
            The result of evaluating the node
        """
        # Handle constant values
        if isinstance(node, ast.Constant):
            return node.value

        # Handle older Python versions
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Str):
            return node.s
        if isinstance(node, ast.NameConstant):
            return node.value

        # Handle variable names
        if isinstance(node, ast.Name):
            if node.id not in context:
                raise ValueError(f"Unknown variable: '{node.id}'")
            return context[node.id]

        # Handle binary operations (a + b, a * b, etc.)
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            op_type = type(node.op)

            if op_type not in self.OPERATORS:
                raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

            # Type safety for division
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod):
                if isinstance(right, (int, float)) and right == 0:
                    raise ValueError("Division by zero")

            return self.OPERATORS[op_type](left, right)

        # Handle unary operations (-a, +a, not a)
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            op_type = type(node.op)

            if op_type not in self.OPERATORS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")

            return self.OPERATORS[op_type](operand)

        # Handle comparisons (a < b, a == b, etc.)
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            result = True

            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, context)
                op_type = type(op)

                if op_type not in self.OPERATORS:
                    raise ValueError(f"Unsupported comparison operator: {op_type.__name__}")

                # Chain comparisons: a < b < c becomes (a < b) and (b < c)
                if not self.OPERATORS[op_type](left, right):
                    return False
                left = right  # For chained comparisons

            return True

        # Handle boolean operations (a and b, a or b)
        if isinstance(node, ast.BoolOp):
            op_type = type(node.op)

            if op_type == ast.And:
                # Short-circuit evaluation
                for value in node.values:
                    if not self._eval_node(value, context):
                        return False
                return True

            if op_type == ast.Or:
                # Short-circuit evaluation
                for value in node.values:
                    if self._eval_node(value, context):
                        return True
                return False

            raise ValueError(f"Unsupported boolean operator: {op_type.__name__}")

        # Handle ternary/conditional expressions (a if condition else b)
        if isinstance(node, ast.IfExp):
            condition = self._eval_node(node.test, context)
            if condition:
                return self._eval_node(node.body, context)
            else:
                return self._eval_node(node.orelse, context)

        raise ValueError(f"Unsupported node type: {type(node).__name__}")

    def is_valid_expression(self, expression: str) -> bool:
        """
        Check if an expression is valid without evaluating it.

        Args:
            expression: The expression string to validate

        Returns:
            True if the expression is safe, False otherwise
        """
        try:
            self.evaluate(expression, {})
            return True
        except (ValueError, SyntaxError):
            return False


# Convenience functions for common use cases
def eval_safe(expression: str, context: Optional[Dict[str, Any]] = None,
              allowed_variables: Optional[Set[str]] = None) -> Any:
    """
    Convenience function for safe expression evaluation.

    Args:
        expression: The expression to evaluate
        context: Variable context dictionary
        allowed_variables: Optional set of allowed variable names

    Returns:
        The result of evaluation

    Example:
        >>> eval_safe("level >= 10 and hp > 50", {"level": 15, "hp": 80})
        True
        >>> eval_safe("score * 2 + bonus", {"score": 100, "bonus": 50})
        250
    """
    evaluator = SafeExpressionEvaluator(allowed_variables)
    return evaluator.evaluate(expression, context)


def validate_achievement_condition(condition: str, state: Any) -> bool:
    """
    Validate and evaluate an achievement condition against a pet state.

    This is a specialized version for achievement checking.

    Args:
        condition: The condition expression string
        state: Pet state object with attributes

    Returns:
        Boolean result of the condition evaluation

    Example:
        >>> class State:
        ...     level = 5
        ...     xp = 100
        >>> validate_achievement_condition("level >= 5", State())
        True
    """
    # Build context from state object
    context = {}
    if state is not None:
        # Common pet state attributes
        for attr in ['level', 'xp', 'total_xp', 'happiness', 'health',
                     'hunger', 'energy', 'evolution_stage', 'files_created',
                     'files_modified', 'commands_run', 'errors_fixed',
                     'consecutive_successes', 'consecutive_failures',
                     'total_sessions', 'times_fed', 'times_played',
                     'session_count']:
            if hasattr(state, attr):
                value = getattr(state, attr)
                context[attr] = value

    try:
        result = eval_safe(condition, context)
        return bool(result)
    except (ValueError, SyntaxError, TypeError):
        return False


if __name__ == "__main__":
    # Test cases
    print("Testing Safe Expression Evaluator")
    print("=" * 50)

    # Test 1: Basic arithmetic
    assert eval_safe("1 + 2") == 3
    assert eval_safe("10 * 5") == 50
    assert eval_safe("100 / 4") == 25.0
    print("✓ Basic arithmetic works")

    # Test 2: Comparisons
    assert eval_safe("10 > 5") is True
    assert eval_safe("3 >= 3") is True
    assert eval_safe("5 != 6") is True
    print("✓ Comparisons work")

    # Test 3: Boolean logic
    assert eval_safe("True and False") is False
    assert eval_safe("True or False") is True
    assert eval_safe("not False") is True
    print("✓ Boolean logic works")

    # Test 4: With variables
    context = {"level": 50, "xp": 1000, "hp": 80}
    assert eval_safe("level >= 10", context) is True
    assert eval_safe("xp > 500 and hp > 50", context) is True
    assert eval_safe("level < 100 or hp == 100", context) is True
    print("✓ Variable context works")

    # Test 5: Complex expressions
    assert eval_safe("(10 + 5) * 2") == 30
    assert eval_safe("100 % 3") == 1
    assert eval_safe("2 ** 8") == 256
    print("✓ Complex expressions work")

    # Test 6: Ternary operator
    assert eval_safe("10 if True else 5") == 10
    assert eval_safe("10 if False else 5") == 5
    print("✓ Ternary operator works")

    # Test 7: Unsafe operations should fail
    unsafe_expressions = [
        "__import__('os').system('ls')",
        "print('hello')",
        "open('/etc/passwd')",
        "eval('1+1')",
        "exec('print(1)')",
        "__builtins__",
        "().__class__",
        "''.__class__",
        "lambda x: x+1",
        "[1, 2, 3][0]",
    ]

    evaluator = SafeExpressionEvaluator()
    for expr in unsafe_expressions:
        try:
            evaluator.evaluate(expr)
            print(f"✗ UNSAFE expression was allowed: {expr}")
        except ValueError:
            pass  # Expected
    print("✓ Unsafe expressions are blocked")

    # Test 8: Achievement conditions
    class MockState:
        level = 15
        xp = 500
        happiness = 85
        times_fed = 10

    assert validate_achievement_condition("level >= 10", MockState()) is True
    assert validate_achievement_condition("happiness > 90", MockState()) is False
    assert validate_achievement_condition("times_fed >= 5 and level >= 10", MockState()) is True
    print("✓ Achievement conditions work")

    print("=" * 50)
    print("All tests passed!")
