"""Embedded DSL for assembling logic circuits.

Embedded domain-specific combinator library for
assembling abstract definitions of logic circuits
and synthesizing circuits from those definitions.
"""

from __future__ import annotations
from typing import Sequence
import doctest
from parts import parts
from circuit import *

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
    def circuit(circuit_=None):
        if circuit_ is not None:
            bit._circuit = circuit_
            return None
        else:
            bit._circuit.prune_and_topological_sort_stable()
            return bit._circuit

    @staticmethod
    def hook_operation(hook=None):
        bit._hook_operation = hook

    @staticmethod
    def operation(o, *args):
        # Ensure second argument is a `bit`.
        args = list(args)
        if len(args) == 2:
            args[1] = constant(args[1]) if isinstance(args[1], int) else args[1]

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
    def constructor(b1, b2=None):
        return bit
        # The inference code below is not currently in use.
        """
        if isinstance(b1, input_one) and isinstance(b2, input_one):
            return input_one
        elif isinstance(b1, input_two) and isinstance(b2, input_two):
            return input_two
        elif isinstance(b1, (input_one, input_two)) and b2 is None:
            return type(b1)
        else:
            return bit
        """

    @staticmethod
    def gate(operation, igs):
        g = bit._circuit.gate(operation, igs)
        for ig in igs:
            ig.output(g)
        return g

    def __init__(self, value, gate_=None):
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
        return self & (constant(other) if isinstance(other, int) else other)

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
        return self ^ (constant(other) if isinstance(other, int) else other)

    def or_(self, other):
        return bit.operation(op.or_, self, other)

    def __or__(self, other):
        return bit.operation(op.or_, self, other)

    def __ror__(self, other):
        return self | (constant(other) if isinstance(other, int) else other)

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

class input(bit):
    """Bit that is designated as a variable input."""

    def __init__(self: bit, value: int):
        self.value = value
        self.gate = bit._circuit.gate(op.id_, is_input=True)

class input_one(input):
    """Bit that is designated as a variable input from one source."""

class input_two(input):
    """Bit that is designated as a variable input from a second source."""

class output(bit):
    """Bit that is designated an output."""

    def __init__(self: bit, b: bit):
        self.value = b.value
        self.gate = bit._circuit.gate(op.id_, [b.gate], is_output=True)

class bits(list):
    """
    Class for representing a vector of abstract bits.
    """

    @staticmethod
    def from_byte(byte_: int, constructor=bit) -> bits:
        return bits([
            constructor(bit_)
            for bit_ in reversed([(byte_>>i)%2 for i in range(8)])
        ])

    @staticmethod
    def from_bytes(bytes_, constructor=bit) -> bits:
        return bits([
            bit_
            for byte_ in bytes_
            for bit_ in bits.from_byte(byte_, constructor)
        ])

    @staticmethod
    def zeros(n: int) -> bits:
        return bits([constant(0)]*n)

    def __int__(self: bits) -> int:
        return sum(int(b)*(2**i) for (i, b) in zip(range(len(self)), reversed(self)))

    def not_(self: bits) -> bits:
        return bits([x.not_() for x in self])

    def __invert__(self: bits) -> bits:
        return bits([x.not_() for x in self])

    def and_(self: bits, other: bits) -> bits:
        return bits([x.and_(y) for (x, y) in zip(self, other)])

    def __and__(self: bits, other: bits) -> bits:
        return bits([x.and_(y) for (x, y) in zip(self, other)])

    def nimp(self: bits, other: bits) -> bits:
        return bits([x.nimp_(y) for (x, y) in zip(self, other)])

    def nimp_(self: bits, other: bits) -> bits:
        return bits([x.nimp_(y) for (x, y) in zip(self, other)])

    def __gt__(self: bits, other: bits) -> bits:
        return bits([x.nimp_(y) for (x, y) in zip(self, other)])

    def nif(self: bits, other: bits) -> bits:
        return bits([x.nif_(y) for (x, y) in zip(self, other)])

    def nif_(self: bits, other: bits) -> bits:
        return bits([x.nif_(y) for (x, y) in zip(self, other)])

    def __lt__(self: bits, other: bits) -> bits:
        return bits([x.nif_(y) for (x, y) in zip(self, other)])

    def xor(self: bits, other: bits) -> bits:
        return bits([x.xor_(y) for (x, y) in zip(self, other)])

    def xor_(self: bits, other: bits) -> bits:
        return bits([x.xor_(y) for (x, y) in zip(self, other)])

    def __xor__(self: bits, other: bits) -> bits:
        return bits([x.xor_(y) for (x, y) in zip(self, other)])

    def or_(self: bits, other: bits) -> bits:
        return bits([x.or_(y) for (x, y) in zip(self, other)])

    def __or__(self: bits, other: bits) -> bits:
        return bits([x.or_(y) for (x, y) in zip(self, other)])

    def nor(self: bits, other: bits) -> bits:
        return bits([x.nor_(y) for (x, y) in zip(self, other)])

    def nor_(self: bits, other: bits) -> bits:
        return bits([x.nor_(y) for (x, y) in zip(self, other)])

    def __mod__(self, other) -> bits:
        return bits([x.nor_(y) for (x, y) in zip(self, other)])

    def xnor(self: bits, other: bits) -> bits:
        return bits([x.xnor_(y) for (x, y) in zip(self, other)])

    def xnor_(self: bits, other: bits) -> bits:
        return bits([x.xnor_(y) for (x, y) in zip(self, other)])

    def __eq__(self: bits, other: bits) -> bits:
        return bits([x.xnor_(y) for (x, y) in zip(self, other)])

    def if_(self: bits, other: bits) -> bits:
        return bits([x.if_(y) for (x, y) in zip(self, other)])

    def __ge__(self: bits, other: bits) -> bits:
        return bits([x.if_(y) for (x, y) in zip(self, other)])

    def imp(self: bits, other: bits) -> bits:
        return bits([x.imp_(y) for (x, y) in zip(self, other)])

    def imp_(self: bits, other: bits) -> bits:
        return bits([x.imp_(y) for (x, y) in zip(self, other)])

    def __le__(self: bits, other: bits) -> bits:
        return bits([x.imp_(y) for (x, y) in zip(self, other)])

    def nand(self: bits, other) -> bits:
        return bits([x.nand_(y) for (x, y) in zip(self, other)])

    def nand_(self: bits, other) -> bits:
        return bits([x.nand_(y) for (x, y) in zip(self, other)])

    def __rshift__(self: bits, other) -> bits:
        '''Overloaded operator: rotation and shift operations.'''
        if isinstance(other, set) and isinstance(list(other)[0], int): # Rotation.
            quantity = list(other)[0]
            return bits(self[len(self)-quantity:]) ** bits(self[0:len(self)-quantity])
        else: # Shift
            return bits([constant(0)]*other) ** bits(self[0:len(self)-other])

    def __lshift__(self: bits, other) -> bits:
        return bits(self[other:]) ** bits([constant(0) for _ in range(other)])

    def __truediv__(self: bits, other) -> Sequence[bits]:
        if isinstance(other, list) and len(other) > 0 and isinstance(other[0], int):
            return map(bits, parts(self, length=other)) # Sequence of lengths.
        elif isinstance(other, set) and len(other) == 1 and isinstance(list(other)[0], int):
            return self / (len(self)//list(other)[0]) # Parts of length `other`.
        else:
            return map(bits, parts(self, other)) # Number of parts is `other`.

    def __pow__(self: bits, other) -> bits:
        '''Concatenation of bit vectors.'''
        result = list(self)
        result.extend(list(other))
        return bits(result)

def constants(l):
    return bits(map(constant, l))

def inputs(l):
    return bits(map(input, l))

def outputs(l):
    return bits(map(output, l))

if __name__ == "__main__":
    doctest.testmod()
