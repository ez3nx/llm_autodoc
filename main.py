#!/usr/bin/env python3
"""
Simple test application for demonstrating LLM AutoDoc functionality.
"""

import os
import sys
from typing import List, Optional


class Calculator:
    """A simple calculator class for basic arithmetic operations."""

    def __init__(self):
        """Initialize the calculator."""
        self.history: List[str] = []

    def add(self, a: float, b: float) -> float:
        """Add two numbers and return the result."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a and return the result."""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers and return the result."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    def divide(self, a: float, b: float) -> float:
        """Divide a by b and return the result."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result

    def get_history(self) -> List[str]:
        """Get the calculation history."""
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear the calculation history."""
        self.history.clear()


def greet_user(name: Optional[str] = None) -> str:
    """Greet the user with a personalized message."""
    if name:
        return f"Hello, {name}! Welcome to the Calculator app."
    return "Hello! Welcome to the Calculator app."


def main():
    """Main function to run the calculator application."""
    print(greet_user("User"))

    calc = Calculator()

    # Perform some sample calculations
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"6 * 7 = {calc.multiply(6, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")

    print("\nCalculation History:")
    for operation in calc.get_history():
        print(f"  {operation}")

    # Demonstrate new utility functions
    print("\n--- Utility Functions Demo ---")
    numbers = [1, 2, 3, 4, 5]
    avg = sum(numbers) / len(numbers)  # Simple average calculation
    print(f"Average of {numbers}: {avg}")

    # Check if a number is prime
    test_number = 17
    print(
        f"Is {test_number} prime? {test_number > 1 and all(test_number % i != 0 for i in range(2, int(test_number**0.5) + 1))}"
    )

    # Generate Fibonacci sequence
    fib_count = 8
    fib = [0, 1]
    for i in range(2, fib_count):
        fib.append(fib[i - 1] + fib[i - 2])
    print(f"First {fib_count} Fibonacci numbers: {fib}")


if __name__ == "__main__":
    main()
