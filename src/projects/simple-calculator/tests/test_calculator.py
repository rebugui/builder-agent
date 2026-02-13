"""Tests for the calculator module."""

import pytest
from src.calculator import add, subtract, multiply, divide, DivisionByZeroError


class TestAdd:
    """Tests for the add function."""

    def test_add_integers(self) -> None:
        """Test adding two integers."""
        assert add(2, 3) == 5

    def test_add_negative_numbers(self) -> None:
        """Test adding negative numbers."""
        assert add(-1, -1) == -2

    def test_add_floats(self) -> None:
        """Test adding floats."""
        assert add(1.5, 2.5) == 4.0

    def test_add_mixed_types(self) -> None:
        """Test adding integer and float."""
        assert add(1, 2.5) == 3.5


class TestSubtract:
    """Tests for the subtract function."""

    def test_subtract_integers(self) -> None:
        """Test subtracting two integers."""
        assert subtract(5, 3) == 2

    def test_subtract_negative_result(self) -> None:
        """Test subtraction resulting in negative."""
        assert subtract(3, 5) == -2

    def test_subtract_floats(self) -> None:
        """Test subtracting floats."""
        assert subtract(5.5, 2.5) == 3.0


class TestMultiply:
    """Tests for the multiply function."""

    def test_multiply_integers(self) -> None:
        """Test multiplying two integers."""
        assert multiply(3, 4) == 12

    def test_multiply_by_zero(self) -> None:
        """Test multiplication by zero."""
        assert multiply(5, 0) == 0

    def test_multiply_negative_numbers(self) -> None:
        """Test multiplying negative numbers."""
        assert multiply(-2, 3) == -6

    def test_multiply_floats(self) -> None:
        """Test multiplying floats."""
        assert multiply(2.5, 4.0) == 10.0


class TestDivide:
    """Tests for the divide function."""

    def test_divide_integers(self) -> None:
        """Test dividing two integers."""
        assert divide(10, 2) == 5.0

    def test_divide_floats(self) -> None:
        """Test dividing floats."""
        assert divide(7.5, 2.5) == 3.0

    def test_divide_by_one(self) -> None:
        """Test division by one."""
        assert divide(5, 1) == 5.0

    def test_divide_by_zero_raises_error(self) -> None:
        """Test that division by zero raises DivisionByZeroError."""
        with pytest.raises(DivisionByZeroError) as exc_info:
            divide(10, 0)
        assert str(exc_info.value) == "Cannot divide by zero"

    def test_divide_negative_numbers(self) -> None:
        """Test dividing negative numbers."""
        assert divide(-10, 2) == -5.0
        assert divide(10, -2) == -5.0
        assert divide(-10, -2) == 5.0