"""Embedded DSL for assembling logic circuits.

Embedded domain-specific combinator library for
assembling abstract definitions of logic circuits
and synthesizing circuits from those definitions.
"""

from __future__ import annotations
from typing import Sequence
import doctest
from parts import parts
from circuit import op, gate, circuit

class bit():
    """
    Class for representing an abstract bit. Such a bit
    can be interpreted concretely as a value, but it is
    also used to keep track of relationships between
    operators and to represent the wires within a
    circuit built up out of those operators.

    >>> bit.hook_operation(lambda o, v, *args: None)
    >>> bit.circuit(circuit())
    >>> b = output(input(1).and_(input(1)))
    >>> b.value == bit.circuit().evaluate([1,1])[0]
    True
    >>> def make_hook(bit_):
    ...     def hook(o, v, *args):
    ...         return bit_.constructor(*args)(v, bit_.gate(o, [a.gate for a in args]))
    ...     return hook
    >>> bit.hook_operation(make_hook(bit))
    >>> bit.circuit(circuit())
    >>> b = output(input(0).and_(input(0)))
    >>> b.value == bit.circuit().evaluate([0,0])[0]
    True
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
        return bit

    @staticmethod
    def gate(operation, igs):
        return bit._circuit.gate(operation, igs)

    def __init__(self, value, gate_=None):
        self.value = value
        self.gate = bit._circuit.gate() if gate_ is None else gate_

    def __int__(self):
        return self.value

    def not_(self):
        """
        >>> results = []
        >>> for x in [0, 1]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).not_())
        ...     results.append(int(b) == bit.circuit().evaluate([x])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.not_, self)

    def __invert__(self):
        """
        >>> results = []
        >>> for x in [0, 1]:
        ...     bit.circuit(circuit())
        ...     b = output(~input(x))
        ...     results.append(int(b) == bit.circuit().evaluate([x])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.not_, self)

    def __rsub__(self, other):
        """
        >>> results = []
        >>> for x in [0, 1]:
        ...     bit.circuit(circuit())
        ...     b = output(1 - input(x))
        ...     results.append(int(b) == bit.circuit().evaluate([x])[0])
        >>> all(results)
        True
        >>> bit.circuit(circuit())
        >>> 2 - input(0)
        Traceback (most recent call last):
          ...
        ValueError: can only subtract a bit from the integer 1
        """
        if other == 1:
            return bit.operation(op.not_, self)
        raise ValueError('can only subtract a bit from the integer 1')

    def and_(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).and_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.and_, self, other)

    def __and__(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) & input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.and_, self, other)

    def __rand__(self, other):
        """
        >>> bit.circuit(circuit())
        >>> b = 0 & constant(1)
        >>> b.value
        0
        """
        return self & (constant(other) if isinstance(other, int) else other)

    def nimp(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nimp(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nimp_, self, other)

    def nimp_(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nimp_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nimp_, self, other)

    def __gt__(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) > input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return self.nimp(other)

    def nif(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nif(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nif_, self, other)

    def nif_(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nif_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nif_, self, other)

    def __lt__(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) < input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return self.nif(other)

    def xor(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).xor(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xor_, self, other)

    def xor_(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).xor_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xor_, self, other)

    def __xor__(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) ^ input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xor_, self, other)

    def __rxor__(self, other):
        """
        >>> bit.circuit(circuit())
        >>> b =  1 ^ constant(0)
        >>> b.value
        1
        """
        return self ^ (constant(other) if isinstance(other, int) else other)

    def or_(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).or_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.or_, self, other)

    def __or__(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) | input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.or_, self, other)

    def __ror__(self, other):
        """
        >>> bit.circuit(circuit())
        >>> b = 1 | constant(0)
        >>> b.value
        1
        """
        return self | (constant(other) if isinstance(other, int) else other)

    def nor(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nor(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nor_, self, other)

    def nor_(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nor_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nor_, self, other)

    def __mod__(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) % input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nor_, self, other)

    def xnor(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).xnor(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xnor_, self, other)

    def xnor_(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).xnor_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xnor_, self, other)

    def __eq__(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) == input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xnor_, self, other)

    def if_(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).if_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.if_, self, other)

    def __ge__(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) >= input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.if_, self, other)

    def imp(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).imp(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.imp_, self, other)

    def imp_(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).imp_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.imp_, self, other)

    def __le__(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) <= input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.imp_, self, other)

    def nand(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nand(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nand_, self, other)

    def nand_(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nand_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nand_, self, other)

    def __matmul__(self, other):
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) @ input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x,y])[0])
        >>> all(results)
        True
        """
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
    """
    Bit that is designated an output.

    >>> bit.circuit(circuit())
    >>> b0 = output(input(1).not_())
    >>> b1 = output(b0.not_())
    >>> b2 = output(b0)
    >>> [b0.value, b1.value, b2.value]
    [0, 1, 0]
    """

    def __init__(self: bit, b: bit):
        # Check if bit is ready as final output or whether there are others dependent on it.
        if len(b.gate.outputs) > 0:
            b = ~(~b)  # Preserve the bit by copying it to a new wire.
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
        """
        >>> bit.circuit(circuit())
        >>> [b.value for b in bits.from_bytes(bytes([255]))]
        [1, 1, 1, 1, 1, 1, 1, 1]
        >>> bit.circuit(circuit())
        >>> [b.value for b in bits.from_bytes(bytes([11, 0]))]
        [0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        """
        return bits([
            bit_
            for byte_ in bytes_
            for bit_ in bits.from_byte(byte_, constructor)
        ])

    @staticmethod
    def zeros(n: int) -> bits:
        """
        >>> bit.circuit(circuit())
        >>> xs = bits.zeros(3)
        >>> ys = outputs(xs.not_())
        >>> [y.value for y in ys]
        [1, 1, 1]
        """
        return bits([constant(0)]*n)

    def __int__(self: bits) -> int:
        """
        >>> bit.circuit(circuit())
        >>> xs = constants([0, 0, 0])
        >>> ys = outputs(xs.not_())
        >>> int(ys)
        7
        """
        return sum(int(b)*(2**i) for (i, b) in zip(range(len(self)), reversed(self)))

    def not_(self: bits) -> bits:
        """
        >>> results = []
        >>> for x in [0, 1]:
        ...     bit.circuit(circuit())
        ...     xs = inputs([x, x, x])
        ...     ys = outputs(xs.not_())
        ...     ns = [int(y) for y in ys]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x]))
        >>> all(results)
        True
        """
        return bits([x.not_() for x in self])

    def __invert__(self: bits) -> bits:
        """
        >>> results = []
        >>> for x in [0, 1]:
        ...     bit.circuit(circuit())
        ...     xs = inputs([x, x, x])
        ...     ys = outputs(~xs)
        ...     ns = [int(y) for y in ys]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x]))
        >>> all(results)
        True
        """
        return bits([x.not_() for x in self])

    def and_(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.and_(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.and_(y) for (x, y) in zip(self, other)])

    def __and__(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs & ys)
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.and_(y) for (x, y) in zip(self, other)])

    def nimp(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.nimp(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.nimp_(y) for (x, y) in zip(self, other)])

    def nimp_(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.nimp_(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.nimp_(y) for (x, y) in zip(self, other)])

    def __gt__(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs > ys)
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.nimp_(y) for (x, y) in zip(self, other)])

    def nif(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.nif(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.nif_(y) for (x, y) in zip(self, other)])

    def nif_(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.nif_(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.nif_(y) for (x, y) in zip(self, other)])

    def __lt__(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs < ys)
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.nif_(y) for (x, y) in zip(self, other)])

    def xor(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.xor(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.xor_(y) for (x, y) in zip(self, other)])

    def xor_(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.xor_(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.xor_(y) for (x, y) in zip(self, other)])

    def __xor__(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs ^ ys)
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.xor_(y) for (x, y) in zip(self, other)])

    def or_(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.or_(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.or_(y) for (x, y) in zip(self, other)])

    def __or__(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs | ys)
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.or_(y) for (x, y) in zip(self, other)])

    def nor(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.nor(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.nor_(y) for (x, y) in zip(self, other)])

    def nor_(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.nor_(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.nor_(y) for (x, y) in zip(self, other)])

    def __mod__(self, other) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs % ys)
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.nor_(y) for (x, y) in zip(self, other)])

    def xnor(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.xnor(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.xnor_(y) for (x, y) in zip(self, other)])

    def xnor_(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.xnor_(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.xnor_(y) for (x, y) in zip(self, other)])

    def __eq__(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs == ys)
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.xnor_(y) for (x, y) in zip(self, other)])

    def if_(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.if_(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.if_(y) for (x, y) in zip(self, other)])

    def __ge__(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs >= ys)
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.if_(y) for (x, y) in zip(self, other)])

    def imp(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.imp(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.imp_(y) for (x, y) in zip(self, other)])

    def imp_(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.imp_(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.imp_(y) for (x, y) in zip(self, other)])

    def __le__(self: bits, other: bits) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs <= ys)
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.imp_(y) for (x, y) in zip(self, other)])

    def nand(self: bits, other) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.nand(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.nand_(y) for (x, y) in zip(self, other)])

    def nand_(self: bits, other) -> bits:
        """
        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     (xs, ys) = (inputs([x, x, x]), inputs([y, y, y]))
        ...     zs = outputs(xs.nand_(ys))
        ...     ns = [int(z) for z in zs]
        ...     c = bit.circuit()
        ...     results.append(ns == c.evaluate([x, x, x, y, y, y]))
        >>> all(results)
        True
        """
        return bits([x.nand_(y) for (x, y) in zip(self, other)])

    def __rshift__(self: bits, other) -> bits:
        """
        Overloaded operator: rotation and shift operations.

        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1,1,1,1,0,0,0,0]))
        >>> bs = bs >> 3
        >>> [b.value for b in bs]
        [0, 0, 0, 1, 1, 1, 1, 0]
        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [0,0,0,0,1,1,1,1]))
        >>> bs = bs >> {3}
        >>> [b.value for b in bs]
        [1, 1, 1, 0, 0, 0, 0, 1]
        """
        if isinstance(other, set) and isinstance(list(other)[0], int): # Rotation.
            quantity = list(other)[0]
            return bits(self[len(self)-quantity:]) ** bits(self[0:len(self)-quantity])
        else: # Shift
            return bits([constant(0)]*other) ** bits(self[0:len(self)-other])

    def __lshift__(self: bits, other) -> bits:
        """
        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1,1,1,1,0,0,0,0]))
        >>> bs = bs << 3
        >>> [b.value for b in bs]
        [1, 0, 0, 0, 0, 0, 0, 0]
        """
        return bits(self[other:]) ** bits([constant(0) for _ in range(other)])

    def __truediv__(self: bits, other) -> Sequence[bits]:
        """
        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1,1,1,1,0,0,0,0]))
        >>> bss = list(bs / 2)
        >>> ([b.value for b in bss[0]], [b.value for b in bss[1]])
        ([1, 1, 1, 1], [0, 0, 0, 0])
        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1,1,1,1,0,0,0,0]))
        >>> bss = list(bs / {2})
        >>> [[b.value for b in bs] for bs in bss]
        [[1, 1], [1, 1], [0, 0], [0, 0]]
        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1,1,1,1,0,0,0,0]))
        >>> bss = list(bs / [1, 3, 4])
        >>> [[b.value for b in bs] for bs in bss]
        [[1], [1, 1, 1], [0, 0, 0, 0]]
        """
        if isinstance(other, list) and len(other) > 0 and isinstance(other[0], int):
            return map(bits, parts(self, length=other)) # Sequence of lengths.
        elif isinstance(other, set) and len(other) == 1 and isinstance(list(other)[0], int):
            return self / (len(self)//list(other)[0]) # Parts of length `other`.
        else:
            return map(bits, parts(self, other)) # Number of parts is `other`.

    def __add__(self: bits, other) -> bits:
        """Concatenation of bit vectors."""
        result = list(self)
        result.extend(list(other))
        return bits(result)

    def __pow__(self: bits, other) -> bits:
        """Concatenation of bit vectors."""
        return self + other

def constants(l):
    return bits(map(constant, l))

def inputs(l):
    return bits(map(input, l))

def outputs(l):
    return bits(map(output, l))

if __name__ == "__main__":
    doctest.testmod() # pragma: no cover
