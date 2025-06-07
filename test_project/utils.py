#!/usr/bin/env python3
"""
Utility functions for the test project.
"""

from typing import List, Union


def format_number(number: Union[int, float], precision: int = 2) -> str:
    """
    Format a number with specified precision.

    Args:
        number: The number to format
        precision: Number of decimal places (default: 2)

    Returns:
        Formatted number as string

    Examples:
        >>> format_number(3.14159, 2)
        '3.14'
        >>> format_number(42)
        '42.00'
    """
    return f"{number:.{precision}f}"


def calculate_average(numbers: List[Union[int, float]]) -> float:
    """
    Calculate the average of a list of numbers.

    Args:
        numbers: List of numbers to average

    Returns:
        The average value

    Raises:
        ValueError: If the list is empty

    Examples:
        >>> calculate_average([1, 2, 3, 4, 5])
        3.0
        >>> calculate_average([10, 20])
        15.0
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")

    return sum(numbers) / len(numbers)


def is_prime(number: int) -> bool:
    """
    Check if a number is prime.

    Args:
        number: The number to check

    Returns:
        True if the number is prime, False otherwise

    Examples:
        >>> is_prime(7)
        True
        >>> is_prime(8)
        False
        >>> is_prime(2)
        True
    """
    if number < 2:
        return False

    if number == 2:
        return True

    if number % 2 == 0:
        return False

    for i in range(3, int(number**0.5) + 1, 2):
        if number % i == 0:
            return False

    return True


def fibonacci_sequence(n: int) -> List[int]:
    """
    Generate Fibonacci sequence up to n terms.

    Args:
        n: Number of terms to generate

    Returns:
        List containing the Fibonacci sequence

    Raises:
        ValueError: If n is negative

    Examples:
        >>> fibonacci_sequence(5)
        [0, 1, 1, 2, 3]
        >>> fibonacci_sequence(1)
        [0]
    """
    if n < 0:
        raise ValueError("Number of terms cannot be negative")

    if n == 0:
        return []

    if n == 1:
        return [0]

    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i - 1] + sequence[i - 2])

    return sequence
