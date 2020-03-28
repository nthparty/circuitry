"""Embedded DSL for assembling logic circuits.

Embedded domain-specific combinator library for
assembling abstract definitions of logic circuits.
"""

from __future__ import annotations
import doctest

class bit():
    """
    Class for representing an abstract bit. Such a bit
    can be interpreted concretely as a value, but it is
    also used to keep track of relationships between
    operators and to represent the wires within a
    circuit built up out of those operators.
    """

    def __init__(self, value):
        self.value = value

    def __invert__(self: bit) -> bit:
        return bit(1 - self.value)

    def __and__(self: bit, other: bit) -> bit:
        return bit(self.value & other.value)

    def __rand__(self: bit, other) -> bit:
        return self & (constant(other) if type(other) is int else other)

    def __xor__(self: bit, other: bit) -> bit:
        return bit(self.value ^ other.value)

    def __rxor__(self: bit, other) -> bit:
        return self ^ (constant(other) if type(other) is int else other)

    def __or__(self: bit, other: bit) -> bit:
        return bit(self.value | other.value)

    def __ror__(self: bit, other) -> bit:
        return self | (constant(other) if type(other) is int else other)

    def __int__(self: bit) -> int:
        return self.value

class constant(bit):
    """Bit that is designated as a constant input."""
    pass

class input(bit):
    """Bit that is designated as a variable input."""
    pass

class input_one(input):
    """Bit that is designated as a variable input from one source."""
    pass

class input_two(input):
    """Bit that is designated as a variable input from a second source."""
    pass

class output(bit):
    """Bit that is designated an output."""

    def __init__(self, value):
        self.value = value

class bits(list):
    """
    Class for representing a vector of abstract bits.
    """

    @staticmethod
    def zeros(n: int) -> bits:
        return bits([constant(0)]*n)

    def __invert__(self: bits):
        return bits([~x for x in self])

    def __and__(self: bits, other: bits):
        return bits([x & y for (x, y) in zip(self, other)])

    def __xor__(self: bits, other: bits):
        return bits([x ^ y for (x, y) in zip(self, other)])

    def __or__(self: bits, other: bits):
        return bits([x | y for (x, y) in zip(self, other)])

if __name__ == "__main__":
    doctest.testmod()
