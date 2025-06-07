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


if __name__ == "__main__":
    main()
