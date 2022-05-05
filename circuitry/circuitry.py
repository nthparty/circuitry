"""
Embedded domain-specific combinator library for assembling abstract definitions
of logic circuits and synthesizing circuits from those definitions.
"""
from __future__ import annotations
from typing import Sequence, Union, Optional, Callable
import doctest
from parts import parts
from circuit import op, gate, circuit, signature

class bit:
    """
    Class for representing an abstract bit. Such a bit can be interpreted
    concretely as a value, but it is also used to keep track of relationships
    between operators and to represent the wires within a circuit built up
    out of those operators.

    It is first necessary to introduce a new circuit object and to designate
    this object as the circuit that is being constructed.

    >>> c = circuit()
    >>> bit.circuit(c)

    Subsequently, it is possible to instantiate subclasses of :obj:`bit` that
    service specific roles (such as :obj:`input`, which represents an input
    value into the overall circuit being constructed). An operator method such
    as :obj:`bit.and_` can be used to operate on :obj:`bit` instances (and, at
    the same time to introduce a gate into the circuit).

    >>> b = output(input(1).and_(input(1)))

    At this point, constructed circuit can be retrieved and evaluated on a
    vector of bits.

    >>> b.value == bit.circuit().evaluate([1, 1])[0]
    True

    It is possible to add custom hook functions that are applied when an operator
    is introduced. If a hook function returns ``None``, then the default instance
    of :obj:`bit` is returned when an operation is applied.

    >>> bit.hook_operation(lambda o, v, *args: None)
    >>> bit.circuit(circuit())
    >>> b = output(input(1).and_(input(1)))
    >>> b.value == bit.circuit().evaluate([1, 1])[0]
    True

    More complex hook functions can also be introduced.

    >>> def make_hook(bit_):
    ...     def hook(o, v, *args):
    ...         return bit_.constructor(*args)(v, bit_.gate(o, [a.gate for a in args]))
    ...     return hook
    >>> bit.hook_operation(make_hook(bit))
    >>> bit.circuit(circuit())
    >>> b = output(input(0).and_(input(1)))
    >>> b.value == bit.circuit().evaluate([0, 1])[0] == 0
    True

    Note that a hook must be removed in order to avoid its effects when subsequent
    circuits are constructed.

    >>> bit.hook_operation()
    """
    _circuit = None
    _hook_operation = None

    def __init__(self: bit, value: int, gate_: Optional[gate] = None):
        """
        Create an instance with the specified value and (if one is supplied)
        designate an associate gate object.
        """
        self.value = value

        if bit._circuit is not None:
            self.gate = bit._circuit.gate() if gate_ is None else gate_

    @staticmethod
    def circuit(circuit_: Optional[circuit] = None) -> Optional[circuit]:
        """
        Designate the circuit object that is under construction. Any invocation
        of the :obj:`bit` constructor adds a gate to the circuit designated
        using this method.

        >>> c = circuit()
        >>> bit.circuit(c)
        >>> b = output(input(1).and_(input(1)))
        >>> b.value == bit.circuit().evaluate([1, 1])[0]
        True
        """
        if circuit_ is not None:
            bit._circuit = circuit_
            return None
        else:
            bit._circuit.prune_and_topological_sort_stable()
            return bit._circuit

    @staticmethod
    def hook_operation(hook: Optional[Callable] = None):
        """
        Assign a function that is invoked whenever the :obj:`bit.operation` method
        is used to create a new instance of :obj:`bit`.

        >>> def make_hook(bit_):
        ...     def hook(o, v, *args):
        ...         return bit_.constructor(*args)(v, bit_.gate(o, [a.gate for a in args]))
        ...     return hook
        >>> bit.hook_operation(make_hook(bit))
        >>> bit.circuit(circuit())
        >>> b = output(input(0).and_(input(0)))
        >>> b.value == bit.circuit().evaluate([0, 0])[0]
        True
        """
        bit._hook_operation = hook

    @staticmethod
    def operation(o: Callable, *args) -> bit:
        """
        Apply the supplied operation method to zero or more :obj:`bit` arguments.

        >>> bit.circuit(circuit())
        >>> b = output(bit.operation(op.and_, input(1), input(1)))
        >>> b.value == bit.circuit().evaluate([1, 1])[0]
        True
        """
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
    def constructor(b1: bit, b2: Optional[bit] = None) -> type:
        """
        Return the constructor to use for instantiating a :obj:`bit` object.
        This method is used by the :obj:`bit.operation` and :obj:`bits.from_byte`
        methods. It is provided primarily to aid in the implementation of custom
        hooks that can be set using the :obj:`bit.hook_operation` method.
        """
        # # The inference code below is not currently in use.
        # if isinstance(b1, input_one) and isinstance(b2, input_one):
        #     return input_one
        # elif isinstance(b1, input_two) and isinstance(b2, input_two):
        #     return input_two
        # elif isinstance(b1, (input_one, input_two)) and b2 is None:
        #     return type(b1)
        # else:
        #     return bit
        return bit

    @staticmethod
    def gate(operation: op, igs: Sequence[gate]) -> Optional[gate]:
        """
        Add a gate to the designated circuit object that is under construction. This
        method is primarily provided to aid in the implementation of custom hooks
        that can be set using the :obj:`bit.hook_operation` method.

        >>> def make_hook(bit_):
        ...     def hook(o, v, *args):
        ...         return bit_.constructor(*args)(v, bit_.gate(o, [a.gate for a in args]))
        ...     return hook
        >>> bit.hook_operation(make_hook(bit))
        >>> bit.circuit(circuit())
        >>> b = output(input(0).and_(input(0)))
        >>> b.value == bit.circuit().evaluate([0, 0])[0]
        True
        """
        return (
            bit._circuit.gate(operation, igs) \
            if bit._circuit is not None else \
            None
        )

    def __int__(self: bit) -> int:
        """
        Convert this :obj:`bit` instance into its integer representation.

        >>> bit.circuit(circuit())
        >>> int(bit(1))
        1
        """
        return self.value

    def not_(self: bit) -> bit:
        """
        Operation for an individual :obj:`bit` instance.

        >>> results = []
        >>> for x in [0, 1]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).not_())
        ...     results.append(int(b) == bit.circuit().evaluate([x])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.not_, self)

    def __invert__(self: bit) -> bit:
        """
        Operation for an individual :obj:`bit` instance.

        >>> results = []
        >>> for x in [0, 1]:
        ...     bit.circuit(circuit())
        ...     b = output(~input(x))
        ...     results.append(int(b) == bit.circuit().evaluate([x])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.not_, self)

    def __rsub__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

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

    def and_(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).and_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.and_, self, other)

    def __and__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) & input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.and_, self, other)

    def __rand__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> bit.circuit(circuit())
        >>> b = 0 & constant(1)
        >>> b.value
        0
        """
        return self & (constant(other) if isinstance(other, int) else other)

    def nimp(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nimp(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nimp_, self, other)

    def nimp_(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nimp_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nimp_, self, other)

    def __gt__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) > input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return self.nimp(other)

    def nif(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nif(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nif_, self, other)

    def nif_(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nif_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nif_, self, other)

    def __lt__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) < input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return self.nif(other)

    def xor(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).xor(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xor_, self, other)

    def xor_(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).xor_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xor_, self, other)

    def __xor__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) ^ input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xor_, self, other)

    def __rxor__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> bit.circuit(circuit())
        >>> b =  1 ^ constant(0)
        >>> b.value
        1
        """
        return self ^ (constant(other) if isinstance(other, int) else other)

    def or_(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).or_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.or_, self, other)

    def __or__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) | input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.or_, self, other)

    def __ror__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> bit.circuit(circuit())
        >>> b = 1 | constant(0)
        >>> b.value
        1
        """
        return self | (constant(other) if isinstance(other, int) else other)

    def nor(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nor(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nor_, self, other)

    def nor_(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nor_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nor_, self, other)

    def __mod__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) % input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nor_, self, other)

    def xnor(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).xnor(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xnor_, self, other)

    def xnor_(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).xnor_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xnor_, self, other)

    def __eq__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) == input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.xnor_, self, other)

    def if_(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).if_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.if_, self, other)

    def __ge__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) >= input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.if_, self, other)

    def imp(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).imp(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.imp_, self, other)

    def imp_(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).imp_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.imp_, self, other)

    def __le__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) <= input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.imp_, self, other)

    def nand(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nand(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nand_, self, other)

    def nand_(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).nand_(input(y)))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nand_, self, other)

    def __matmul__(self: bit, other: bit) -> bit:
        """
        Operation for individual :obj:`bit` instances.

        >>> results = []
        >>> for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x) @ input(y))
        ...     results.append(int(b) == bit.circuit().evaluate([x, y])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.nand_, self, other)

class constant(bit):
    """
    Instance of a :obj:`bit` that is designated as a constant value.

    >>> bit.circuit(circuit())
    >>> constant(1).value
    1

    When constructing a circuit, a gate with a nullary operator is added to
    the circuit.

    >>> bit.circuit(circuit())
    >>> _ = output(constant(0))
    >>> c = bit.circuit()
    >>> c.count()
    1
    >>> c.evaluate([])
    [0]
    """
    def __init__(self: bit, value: int):
        """Instantiate an instance that is designated as a variable input."""
        self.value = value

        if bit._circuit is not None:
            self.gate = bit._circuit.gate(op.nf_ if self.value == 0 else op.nt_)

class input(bit):
    """
    Instance of a :obj:`bit` that is designated as a variable input.

    >>> bit.circuit(circuit())
    >>> b0 = output(input(1).not_())
    >>> b0.value
    0
    """
    def __init__(self: bit, value: int):
        """Instantiate an instance that is designated as a variable input."""
        self.value = value

        if bit._circuit is not None:
            self.gate = bit._circuit.gate(op.id_, is_input=True)

class input_one(input):
    """
    Instance of a :obj:`bit` that is designated as a variable input from one source.
    """

class input_two(input):
    """
    Instance of a :obj:`bit` that is designated as a variable input from a second source
    """

class output(bit):
    """
    Instance of a :obj:`bit` that is designated as an output.

    >>> bit.circuit(circuit())
    >>> b0 = output(input(1).not_())
    >>> b1 = output(b0.not_())
    >>> b2 = output(b0)
    >>> [b0.value, b1.value, b2.value]
    [0, 1, 0]
    """
    def __init__(self: bit, b: bit):
        """
        Instantiate a bit that is designated as an output.
        """
        self.value = b.value

        if bit._circuit is not None:
            # Check if bit is ready as final output or whether there are others
            # dependent on it.
            if len(b.gate.outputs) > 0:
                b = ~(~b)  # Preserve the bit by copying it to a new wire.

            self.gate = bit._circuit.gate(op.id_, [b.gate], is_output=True)

class bits_type(int): # pylint: disable=R0903
    """
    Class for representing an input or output type of a function decorated
    for automated synthesis. This class is used within the :obj:`bits`
    constructor implementation.
    """

class bits(list):
    """
    Class for representing a *bit vector* (*i.e.*, a list of abstract :obj:`bit`
    instances).

    >>> bit.circuit(circuit())
    >>> bs = bits([constant(1)] * 3)
    >>> [b.value for b in bs]
    [1, 1, 1]
    """
    def __new__(cls, argument=None) -> bits:
        """
        Instantiate bit vector object given the supplied argument.
        """
        return bits_type(argument)\
            if isinstance(argument, int) else\
            list.__new__(cls, argument)

    @staticmethod
    def from_byte(byte_: int, constructor=bit) -> bits:
        """
        Convert a byte into a corresponding bit vector.

        >>> bit.circuit(circuit())
        >>> [b.value for b in bits.from_byte(255)]
        [1, 1, 1, 1, 1, 1, 1, 1]
        """
        return bits([
            constructor(bit_)
            for bit_ in reversed([(byte_ >> i) % 2 for i in range(8)])
        ])

    @staticmethod
    def from_bytes(bytes_, constructor=bit) -> bits:
        """
        Convert a vector of bytes into a corresponding bit vector.

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
        Create a vector (of the specified length) of constant zero bits.

        >>> bit.circuit(circuit())
        >>> xs = bits.zeros(3)
        >>> ys = outputs(xs.not_())
        >>> [y.value for y in ys]
        [1, 1, 1]
        """
        return bits([constant(0)]*n)

    def __int__(self: bits) -> int:
        """
        Convert a bit vector into an integer.

        >>> bit.circuit(circuit())
        >>> xs = constants([0, 0, 0])
        >>> ys = outputs(xs.not_())
        >>> int(ys)
        7
        """
        return sum(int(b)*(2**i) for (i, b) in zip(range(len(self)), reversed(self)))

    def not_(self: bits) -> bits:
        """
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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

    def __mod__(self: bits, other: bits) -> bits:
        """
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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
        Operation for bit vectors.

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

    def nand(self: bits, other: bits) -> bits:
        """
        Operation for bit vectors.

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

    def nand_(self: bits, other: bits) -> bits:
        """
        Operation for bit vectors.

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
        Overloaded operator for performing rotation and shift operations on
        bit vectors.

        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1, 1, 1, 1, 0, 0, 0, 0]))
        >>> bs = bs >> 3
        >>> [b.value for b in bs]
        [0, 0, 0, 1, 1, 1, 1, 0]
        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [0, 0, 0, 0, 1, 1, 1, 1]))
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
        Overloaded operator for performing shift operations on bit vectors.

        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1, 1, 1, 1, 0, 0, 0, 0]))
        >>> bs = bs << 3
        >>> [b.value for b in bs]
        [1, 0, 0, 0, 0, 0, 0, 0]
        """
        return bits(self[other:]) ** bits([constant(0) for _ in range(other)])

    def __truediv__(self: bits, other) -> Sequence[bits]:
        """
        Overloaded operator for splitting a bit vector into a collection of
        smaller bit vectors.

        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1, 1, 1, 1, 0, 0, 0, 0]))
        >>> bss = list(bs / 2)
        >>> ([b.value for b in bss[0]], [b.value for b in bss[1]])
        ([1, 1, 1, 1], [0, 0, 0, 0])
        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1, 1, 1, 1, 0, 0, 0, 0]))
        >>> bss = list(bs / {2})
        >>> [[b.value for b in bs] for bs in bss]
        [[1, 1], [1, 1], [0, 0], [0, 0]]
        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1, 1, 1, 1, 0, 0, 0, 0]))
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

    def __add__(self: bits, other: Union[bits, Sequence[int]]) -> bits:
        """
        Overloaded operator for concatenating bit vectors.

        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1, 1])) + bits(map(bit, [0, 0]))
        >>> [b.value for b in bs]
        [1, 1, 0, 0]
        """
        result = list(self)
        result.extend(list(other))
        return bits(result)

    def __pow__(self: bits, other: Union[bits, Sequence[int]]) -> bits:
        """
        Overloaded operator for concatenating bit vectors.

        >>> bit.circuit(circuit())
        >>> bs = bits(map(bit, [1, 1])) ** bits(map(bit, [0, 0]))
        >>> [b.value for b in bs]
        [1, 1, 0, 0]
        """
        return self + other

def constants(l: Sequence[int]) -> bits:
    """
    Synonym for concisely constructing a vector of constant-designated
    :obj:`bit` objects.

    >>> bit.circuit(circuit())
    >>> xs = constants([0, 0, 0])
    >>> ys = outputs(xs.not_())
    >>> int(ys)
    7
    """
    return bits(map(constant, l))

def inputs(l: Sequence[int]) -> bits:
    """
    Synonym for concisely constructing a vector of input-designated
    :obj:`bit` objects.

    >>> results = []
    >>> bit.circuit(circuit())
    >>> xs = inputs([1, 1, 1])
    >>> ys = outputs(xs.not_())
    >>> ns = [int(y) for y in ys]
    >>> c = bit.circuit()
    >>> ns == c.evaluate([1, 1, 1])
    True
    """
    return bits(map(input, l))

def outputs(l: Sequence[int]) -> bits:
    """
    Synonym for concisely constructing a vector of output-designated
    :obj:`bit` objects.

    >>> bit.circuit(circuit())
    >>> xs = bits.zeros(3)
    >>> ys = outputs(xs.not_())
    >>> [y.value for y in ys]
    [1, 1, 1]
    """
    return bits(map(output, l))

def synthesize(f: Callable) -> Callable:
    """
    Decorator for automatically synthesizing a circuit from a function that
    takes only :obj:`bit` and/or :obj:`bits` objects as its arguments and
    returns an output of type :obj:`bit` or :obj:`bits`.

    In the example below, a function ``equal`` is defined that determines
    whether two bits are equivalent. The use of this decorator causes a
    circuit that implements this function to be constructed.

    >>> @synthesize
    ... def equal(x: bit, y: bit) -> bit:
    ...     return (x & y) | ((1 - x) & (1 - y))

    The circuit is introduced as an attribute of the function and can
    be evaluated on :obj:`bits` objects.

    >>> xys = [bits([x, y]) for x in (0, 1) for y in (0, 1)]
    >>> [equal.circuit.evaluate(xy) for xy in xys]
    [[1], [0], [0], [1]]

    This decorator can also be applied to functions that are defined
    explicitly as operating on bit vectors (in the form of :obj:`bits`
    objects).

    >>> @synthesize
    ... def conjunction(xy: bits(2)) -> bits(2):
    ...     return (xy[0], xy[0] & xy[1])
    >>> xys = [bits([x, y]) for x in (0, 1) for y in (0, 1)]
    >>> [conjunction.circuit.evaluate(xy) for xy in xys]
    [[0, 0], [0, 0], [1, 0], [1, 1]]

    Functions to which this decorator is applied must have type annotations.

    >>> @synthesize
    ... def equal(x, y):
    ...     return x & y
    Traceback (most recent call last):
      ...
    RuntimeError: automated circuit synthesis failed
    """
    # Functions for determining types/signature from
    # the type annotation of the decorated function.
    type_in = lambda a: input(0) if a is bit else inputs([0] * a)
    type_out = lambda a: output if a is bit else outputs

    # For forward-compatibility with PEP 563.
    eval_ = lambda a: eval(a) if isinstance(a, str) else a # pylint: disable=W0123

    try:
        # Construct the circuit and add it to the function as an attribute.
        bit.circuit(circuit())
        args_in = {
            k: type_in(eval_(a))
            for (k, a) in f.__annotations__.items() if k != 'return'
        }
        type_out(eval_(f.__annotations__['return']))(f(**args_in))
        f.circuit = bit.circuit()

        # Assign a signature to the circuit.
        #size = lambda a: 1 if a is bit else a.length
        #f.circuit.signature = signature(
        #    [size(a) for (k, a) in f.__annotations__.items() if k != 'return'],
        #    [size(a) for (k, a) in f.__annotations__.items() if k == 'return']
        #)
    except:
        raise RuntimeError('automated circuit synthesis failed') from None

    # Return the original function.
    return f

if __name__ == "__main__":
    doctest.testmod() # pragma: no cover
