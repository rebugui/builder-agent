"""Simple calculator module with basic arithmetic operations."""

from typing import Union

Number = Union[int, float]


class DivisionByZeroError(Exception):
    """Exception raised when attempting to divide by zero."""
    pass


def add(a: Number, b: Number) -> Number:
    """
    Add two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        The sum of a and b.
    """
    return a + b


def subtract(a: Number, b: Number) -> Number:
    """
    Subtract second number from first.

    Args:
        a: First number.
        b: Second number.

    Returns:
        The result of a minus b.
    """
    return a - b


def multiply(a: Number, b: Number) -> Number:
    """
    Multiply two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        The product of a and b.
    """
    return a * b


def divide(a: Number, b: Number) -> float:
    """
    Divide first number by second.

    Args:
        a: Dividend.
        b: Divisor.

    Returns:
        The quotient as a float.

    Raises:
        DivisionByZeroError: If b is zero.
    """
    if b == 0:
        raise DivisionByZeroError("Cannot divide by zero")
    return a / b