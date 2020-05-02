"""Embedded DSL for assembling logic circuits.

Embedded domain-specific combinator library for
assembling abstract definitions of logic circuits
and synthesizing circuits from those definitions.
"""

from parts import parts
from circuit import *
from __future__ import annotations
from typing import Sequence
import doctest

class bit():
    """
    Class for representing an abstract bit. Such a bit
    can be interpreted concretely as a value, but it is
    also used to keep track of relationships between
    operators and to represent the wires within a
    circuit built up out of those operators.
    """

    @staticmethod
    def circuit(circuit_ = None):
        if circuit_ is not None:
            bit._circuit = circuit_
        else:
            bit._circuit.prune_and_stable_topological_sort(lambda b: type(b) is output)
            return bit._circuit

    def __init__(self, value, gate_ = None):
        self.value = value
        self.gate = gate(attributes = {'bit': self}) if gate_ is None else gate_

    def __invert__(self: bit) -> bit:
        return bit(1 - self.value)

    def __and__(self: bit, other: bit) -> bit:
        return bit(self.value & other.value)

    def __rand__(self: bit, other) -> bit:
        return self & (constant(other) if type(other) is int else other)

    def __gt__(self: bit, other: bit) -> bit: # NIMP operation.
        return bit(1 if self.value > other.value else 0)

    def __lshift__(self: bit, other: bit) -> bit: # FST operation.
        return bit(self.value)

    def __lt__(self: bit, other: bit) -> bit: # NIF operation.
        return bit(1 if self.value < other.value else 0)

    def __rshift__(self: bit, other: bit) -> bit: # SND operation.
        return bit(other.value)

    def __xor__(self: bit, other: bit) -> bit:
        return bit(self.value ^ other.value)

    def __rxor__(self: bit, other) -> bit:
        return self ^ (constant(other) if type(other) is int else other)

    def __or__(self: bit, other: bit) -> bit:
        return bit(self.value | other.value)

    def __ror__(self: bit, other) -> bit:
        return self | (constant(other) if type(other) is int else other)

    def __mod__(self: bit, other: bit) -> bit: # NOR operation.
        return bit(0 if self.value | other.value else 1)

    def __eq__(self: bit, other: bit) -> bit: # XNOR operation.
        return bit(1 if self.value == other.value else 0)

    def __floordiv__(self: bit, other: bit) -> bit: # NSND operation.
        return bit(1 - other.value)

    def __ge__(self: bit, other: bit) -> bit: # IF operation.
        return bit(1 if self.value >= other.value else 0)

    def __truediv__(self: bit, other: bit) -> bit: # NFST operation.
        return bit(1 - self.value)

    def __le__(self: bit, other: bit) -> bit: # IMP operation.
        return bit(1 if self.value <= other.value else 0)

    def __matmul__(self: bit, other: bit) -> bit: # NAND operation.
        return bit(0 if self.value & other.value else 1)

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

    def __init__(self: bit, b: bit):
        self.value = b.value
        self.gate = b.gate
        bit._circuit.final(self)
        self.gate.bit = self

class bits(list):
    """
    Class for representing a vector of abstract bits.
    """

    @staticmethod
    def from_byte(byte_: int, constructor = bit) -> bits:
        return bits([
            constructor(bit_)
            for bit_ in reversed([(byte_>>i)%2 for i in range(8)])
        ])

    @staticmethod
    def from_bytes(bytes_, constructor = bit) -> bits:
        return bits([
            bit_
            for byte in bytes_
            for bit_ in bits.from_byte(byte_, constructor)
        ])

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

    def __rshift__(self: bits, other: int) -> bits:
        return bits([constant(0)]*other) @ bits(self[0:len(self)-other])

    def __truediv__(self: bits, other) -> Sequence[bits]:
        if type(other) is list and len(other) > 0 and type(other[0]) is int:
            return self / (len(self)//other[0]) # Parts of length `other`.
        else:
            return map(bits, parts(self, other)) # Number of parts is `other`.

    def __matmul__(self: bits, other) -> bits:
        if type(other) is int: # Right rotation.
            return bits(self[len(self)-other:]) @ bits(self[0:len(self)-other])
        else: # Concatenation.
            result = [b for b in self]
            result.extend([b for b in other])
            return bits(result)

    def __int__(self: bits) -> int:
        return sum(int(b)*(2**i) for (i, b) in zip(range(len(self)), reversed(self)))

if __name__ == "__main__":
    doctest.testmod()
