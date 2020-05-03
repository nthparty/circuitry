"""Embedded DSL for assembling logic circuits.

Embedded domain-specific combinator library for
assembling abstract definitions of logic circuits
and synthesizing circuits from those definitions.
"""

from __future__ import annotations
from typing import Sequence
from parts import parts
from circuit import *
import doctest

class bit():
    """
    Class for representing an abstract bit. Such a bit
    can be interpreted concretely as a value, but it is
    also used to keep track of relationships between
    operators and to represent the wires within a
    circuit built up out of those operators.
    """

    _circuit = None
    _hook_operation = None

    @staticmethod
    def circuit(circuit_ = None):
        if circuit_ is not None:
            bit._circuit = circuit_
        else:
            bit._circuit.prune_and_topological_sort_stable()
            return bit._circuit

    @staticmethod
    def hook_operation(hook = None):
        bit._hook_operation = hook

    @staticmethod
    def operation(o, *args):
        # Ensure second argument is a `bit`.
        args = list(args)
        if len(args) == 2:
            args[1] = constant(args[1]) if type(args[1]) is int else args[1]

        # Compute the value of the result of the operation on the arguments.
        v = o(*[a.value for a in args])

        # Return output from hook if it exists and if
        # it returns an output.
        if bit._hook_operation is not None:
            r = bit._hook_operation(o, v, *args)
            if r is not None:
                return r

        return bit.constructor(*args)(v, bit.gate(o, [a.gate for a in args]))

    @staticmethod
    def constructor(b1, b2 = None):
        return bit

        # The inference code below is not currently in use.
        if type(b1) is input_one and type(b2) is input_one:
            return input_one
        elif type(b1) is input_two and type(b2) is input_two:
            return input_two
        elif type(b1) in [input_one, input_two] and b2 is None:
            return type(b1)
        else:
            return bit

    @staticmethod
    def gate(operation, igs):
        g = bit._circuit.gate(operation, igs)
        for ig in igs:
            ig.output(g)
        return g

    def __init__(self, value, gate_ = None):
        self.value = value
        self.gate = bit._circuit.gate() if gate_ is None else gate_

    def __int__(self):
        return self.value

    def not_(self):
        return bit.operation(op.not_, self)

    def __invert__(self):
        return bit.operation(op.not_, self)

    def and_(self, other):
        return bit.operation(op.and_, self, other)

    def __and__(self, other):
        return bit.operation(op.and_, self, other)

    def __rand__(self, other):
        return self & (constant(other) if type(other) is int else other)

    def nimp(self, other):
        return bit.operation(op.nimp_, self, other)

    def nimp_(self, other):
        return bit.operation(op.nimp_, self, other)

    def __gt__(self, other):
        return self.nimp(other)

    def nif(self, other):
        return bit.operation(op.nif_, self, other)

    def nif_(self, other):
        return bit.operation(op.nif_, self, other)

    def __lt__(self, other):
        return self.nif(other)

    def xor(self, other):
        return bit.operation(op.xor_, self, other)

    def xor_(self, other):
        return bit.operation(op.xor_, self, other)

    def __xor__(self, other):
        return bit.operation(op.xor_, self, other)

    def __rxor__(self, other):
        return self ^ (constant(other) if type(other) is int else other)

    def or_(self, other):
        return bit.operation(op.or_, self, other)

    def __or__(self, other):
        return bit.operation(op.or_, self, other)

    def __ror__(self, other):
        return self | (constant(other) if type(other) is int else other)

    def nor(self, other):
        return bit.operation(op.nor_, self, other)

    def nor_(self, other):
        return bit.operation(op.nor_, self, other)

    def __mod__(self, other):
        return bit.operation(op.nor_, self, other)

    def xnor(self, other):
        return bit.operation(op.xnor_, self, other)

    def xnor_(self, other):
        return bit.operation(op.xnor_, self, other)

    def __eq__(self, other):
        return bit.operation(op.xnor_, self, other)

    def if_(self, other):
        return bit.operation(op.if_, self, other)

    def __ge__(self, other):
        return bit.operation(op.if_, self, other)

    def imp(self, other):
        return bit.operation(op.imp_, self, other)

    def imp_(self, other):
        return bit.operation(op.imp_, self, other)

    def __le__(self, other):
        return bit.operation(op.imp_, self, other)

    def nand(self, other):
        return bit.operation(op.nand_, self, other)

    def nand_(self, other):
        return bit.operation(op.nand_, self, other)

    def __matmul__(self, other):
        return bit.operation(op.nand_, self, other)

class constant(bit):
    """Bit that is designated as a constant input."""
    pass

class input(bit):
    """Bit that is designated as a variable input."""

    def __init__(self: bit, value: int):
        self.value = value
        self.gate = bit._circuit.gate(op.id_, is_input = True)

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
        self.gate = bit._circuit.gate(op.id_, [b.gate], is_output = True)

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

    def nif(self: bits, other: bits) -> bits:
        return bits([x.nif(y) for (x, y) in zip(self, other)])

    def nimp(self: bits, other: bits) -> bits:
        return bits([x.nimp(y) for (x, y) in zip(self, other)])

    def __rshift__(self: bits, other):
        return bits([constant(0)]*other) @ bits(self[0:len(self)-other])

    def __lshift__(self: bits, other):
        return bits(self[other:]) @ bits([constant(0) for _ in range(other)])

    def __truediv__(self: bits, other) -> Sequence[bits]:
        if type(other) is list and len(other) > 0 and type(other[0]) is int:
            return map(bits, parts(self, length=other)) # Number of parts is `other`.
        elif type(other) is set and len(other) == 1 and type(list(other)[0]) is int:
            return self / (len(self)//list(other)[0]) # Parts of length `other`.
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

def constants(l):
    return bits(map(constant, l))

def inputs(l):
    return bits(map(input, l))

def outputs(l):
    return bits(map(output, l))

if __name__ == "__main__":
    doctest.testmod()
