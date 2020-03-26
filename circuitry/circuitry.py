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

if __name__ == "__main__":
    doctest.testmod()
