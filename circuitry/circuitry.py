"""
Embedded domain-specific combinator library for assembling abstract definitions
of logic circuits and synthesizing circuits from those definitions.
"""
from __future__ import annotations
from typing import Sequence, Union, Optional, Callable
import doctest
import inspect
from parts import parts
from circuit import op, gate, circuit, signature

class bit:
    """
    Class for representing an abstract bit. Such a bit can be interpreted
    concretely as a value, but it is also used to keep track of relationships
    between operators and to represent the individual wires within a circuit
    that is built up from gates that correspond to those operators.

    It is first necessary to introduce a new circuit object and to designate
    this object as the circuit that is being constructed.

    >>> c = circuit()
    >>> bit.circuit(c)

    Subsequently, it is possible to instantiate subclasses of :obj:`bit` that
    serve specific roles (such as :obj:`input`, which represents an input value
    into the overall circuit being constructed). An operator method such as
    :obj:`bit.and_` can be used to operate on :obj:`bit` instances (and, at the
    same time to introduce a gate into the circuit).

    >>> b = output(input(1).and_(input(1)))

    At this point, constructed circuit can be retrieved and evaluated on a
    vector of bit values (wherein each value is represented using the integer
    ``0`` or the integer ``1``).

    >>> b.value == bit.circuit().evaluate([1, 1])[0]
    True

    It is possible to add custom hook functions that are applied whenever an
    operator is introduced using the :obj:`bit.hook_operation` method.

    >>> def make_hook_that_prints_created_gates(bit_):
    ...     def hook(o, v, *args):
    ...         print('created gate with operation "' + o.name() + '"')
    ...         return bit_.constructor(*args)(v, bit_.gate(o, [a.gate for a in args]))
    ...     return hook
    >>> bit.hook_operation(make_hook_that_prints_created_gates(bit))
    >>> bit.circuit(circuit())
    >>> b = output(input(0).and_(input(1)).not_())
    created gate with operation "and"
    created gate with operation "not"

    Note that a hook must be removed if its effects are not desired when subsequent
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

        Invoking this method with no argument retrieves *and removes* the
        circuit object (leaving no designated circuit object). Note that
        because of the invocation of this method at the end of the above
        example, the invocation below returns ``None``.

        >>> bit.circuit() is None
        True
        """
        if circuit_ is not None:
            bit._circuit = circuit_
            return None

        if bit._circuit is not None:
            bit._circuit.prune_and_topological_sort_stable()
            c = bit._circuit
            bit._circuit = None
            return c

        return None

    @staticmethod
    def hook_operation(hook: Optional[Callable] = None):
        """
        Assign a function that is invoked whenever the :obj:`bit.operation` method
        is used to create a new instance of :obj:`bit`.

        >>> def make_hook_that_prints_created_gates(bit_):
        ...     def hook(o, v, *args):
        ...         print('created gate with operation "' + o.name() + '"')
        ...         return bit_.constructor(*args)(v, bit_.gate(o, [a.gate for a in args]))
        ...     return hook
        >>> bit.hook_operation(make_hook_that_prints_created_gates(bit))
        >>> bit.circuit(circuit())
        >>> b = output(input(0).and_(input(1)).not_())
        created gate with operation "and"
        created gate with operation "not"
        >>> b.value == bit.circuit().evaluate([0, 0])[0]
        True

        If a hook function returns ``None``, then the default instance of :obj:`bit`
        is returned when an operation is applied.

        >>> bit.hook_operation(lambda o, v, *args: None)
        >>> bit.circuit(circuit())
        >>> b = output(input(1).and_(input(1)))
        >>> b.value == bit.circuit().evaluate([1, 1])[0]
        True

        It is only possible to assign one hook function at a time. A hook must
        be removed if its effects are not desired when subsequent circuits are
        constructed.

        >>> bit.hook_operation()
        """
        bit._hook_operation = hook

    @staticmethod
    def operation(o: Callable, *args) -> bit:
        """
        Apply the supplied operation method to zero or more :obj:`bit` arguments.
        Gate operations are represented using instances of the
        :obj:`~logical.logical.logical` class exported by the
        `logical <https://pypi.org/project/logical/>`_ library. This module
        indirectly imports the :obj:`~logical.logical.logical` class via the
        :obj:`~circuit.circuit.op` synonym defined in the
        `circuit <https://pypi.org/project/circuit/>`_ library, enabling the
        more concise syntax used in the example below.

        >>> bit.circuit(circuit())
        >>> b = output(bit.operation(op.and_, input(1), input(1)))
        >>> b.value == bit.circuit().evaluate([1, 1])[0]
        True

        Arguments that are instances of :obj:`output` are not permitted.

        >>> bit.circuit(circuit())
        >>> b0 = output(input(0).not_())
        >>> b1 = b0.not_()
        Traceback (most recent call last):
          ...
        TypeError: cannot supply an output as an argument to an operation
        >>> _ = bit.circuit() # Remove designated circuit.
        """
        # Ensure second argument is a `bit`.
        args = list(args)
        if len(args) == 2:
            args[1] = constant(args[1]) if isinstance(args[1], int) else args[1]

        # Ensure none of the arguments are outputs.
        for a in args:
            if isinstance(a, output):
                raise TypeError(
                    "cannot supply an output as an argument to an operation"
                )

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
        return bit

    @staticmethod
    def gate(operation: op, igs: Sequence[gate]) -> Optional[gate]:
        """
        Add a gate to the designated circuit object that is under construction.
        This method is primarily provided to aid in the implementation of custom
        hooks that can be set using the :obj:`bit.hook_operation` method.
        Gate operations are represented using instances of the
        :obj:`~logical.logical.logical` class exported by the
        `logical <https://pypi.org/project/logical/>`_ library (which is indirectly
        imported into this module as the :obj:`~circuit.circuit.op` synonym
        from the `circuit <https://pypi.org/project/circuit/>`_ library).

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
        Convert this :obj:`bit` instance into the integer representation of
        its value.

        >>> int(bit(1))
        1
        """
        return self.value

    def id_(self: bit) -> bit:
        """
        Logical operation for an individual :obj:`bit` instance.

        >>> results = []
        >>> for x in [0, 1]:
        ...     bit.circuit(circuit())
        ...     b = output(input(x).id_())
        ...     results.append(int(b) == bit.circuit().evaluate([x])[0])
        >>> all(results)
        True
        """
        return bit.operation(op.id_, self)

    def not_(self: bit) -> bit:
        """
        Logical operation for an individual :obj:`bit` instance.

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
        Logical operation for an individual :obj:`bit` instance.

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
        Arithmetic operation involving an individual :obj:`bit` instance that
        is often used to represent the logical negation operation. This method
        is provided primarily as a convenience enabling use of the syntax
        ``1 - b`` to represent logical negation of a bit value ``b``; it
        **does not enable subtraction of one** :obj:`bit` **instance from
        another**.

        >>> results = []
        >>> for x in [0, 1]:
        ...     bit.circuit(circuit())
        ...     b = output(1 - input(x))
        ...     results.append(int(b) == bit.circuit().evaluate([x])[0])
        >>> all(results)
        True
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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

        >>> b = 0 & constant(1)
        >>> b.value
        0
        """
        return self & (constant(other) if isinstance(other, int) else other)

    def nimp(self: bit, other: bit) -> bit:
        """
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

        >>> b =  1 ^ constant(0)
        >>> b.value
        1
        """
        return self ^ (constant(other) if isinstance(other, int) else other)

    def or_(self: bit, other: bit) -> bit:
        """
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

        >>> b = 1 | constant(0)
        >>> b.value
        1
        """
        return self | (constant(other) if isinstance(other, int) else other)

    def nor(self: bit, other: bit) -> bit:
        """
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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
        Logical operation for individual :obj:`bit` instances.

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

    >>> constant(1).value
    1

    When a :obj:`constant` instance is introduced during circuit construction,
    a gate with a nullary operator (*i.e.*, one of the two appearing in
    :obj:`~logical.logical.logical.nullary`) is added to the circuit.

    >>> bit.circuit(circuit())
    >>> _ = output(constant(0))
    >>> c = bit.circuit()
    >>> c.count()
    2
    >>> c.evaluate([])
    [0]
    """
    def __init__(self: bit, value: int):
        """Instantiate an instance that is designated as a constant input."""
        self.value = value

        if bit._circuit is not None:
            self.gate = bit._circuit.gate(op.nf_ if self.value == 0 else op.nt_)

class input(bit):
    """
    Instance of a :obj:`bit` that is designated as a variable input. When an
    :obj:`input` instance is introduced during circuit construction, a gate
    is added to the circuit that is explicitly marked as an input gate (as
    defined in the `circuit <https://pypi.org/project/circuit/>`_ library).

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
    Instance of a :obj:`bit` that is designated as an output. When an
    :obj:`output` instance is introduced during circuit construction, a gate is
    added to the circuit that is explicitly marked as an output gate (as defined
    in the `circuit <https://pypi.org/project/circuit/>`_ library).

    >>> bit.circuit(circuit())
    >>> b0 = input(0).not_()
    >>> b1 = output(b0.not_())
    >>> [b0.value, b1.value]
    [1, 0]
    >>> bit.circuit().evaluate([1])
    [1]

    It is not possible to apply an operation to an :obj:`output` instance. Any
    attempt to do so raises an exception (see implementation of :obj:`bit.operation`
    for more details).

    >>> bit.circuit(circuit())
    >>> b0 = output(input(0).not_())
    >>> b1 = b0.not_()
    Traceback (most recent call last):
      ...
    TypeError: cannot supply an output as an argument to an operation

    If the value represented by a :obj:`bit` instance must be both an argument
    into another operation and an output, an :obj:`bit.id_` operation can be
    introduced.

    >>> bit.circuit(circuit())
    >>> b0 = input(1).not_()
    >>> b1 = output(b0.id_())
    >>> b2 = output(b0.not_())
    >>> [b0.value, b1.value, b2.value]
    [0, 0, 1]
    >>> bit.circuit().evaluate([0])
    [1, 0]
    """
    def __init__(self: bit, b: bit):
        """
        Instantiate a bit that is designated as an output.
        """
        self.value = b.value

        if bit._circuit is not None:
            self.gate = bit._circuit.gate(op.id_, [b.gate], is_output=True)

class bits_type(int): # pylint: disable=R0903
    """
    Class for representing an input or output type of a function decorated
    for automated synthesis. This class is employed internally within the
    :obj:`bits` constructor implementation and is not intended to be used
    directly. It is not exported.
    """

class bits(list):
    """
    Class for representing a *bit vector* (*i.e.*, a list of abstract :obj:`bit`
    instances).

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
        Convert an integer representing a single byte into a corresponding bit
        vector.

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

        >>> [b.value for b in bits.from_bytes(bytes([255]))]
        [1, 1, 1, 1, 1, 1, 1, 1]
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
        >>> _ = bit.circuit() # Remove designated circuit.
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
        >>> _ = bit.circuit() # Remove designated circuit.
        """
        return sum(int(b)*(2**i) for (i, b) in zip(range(len(self)), reversed(self)))

    def not_(self: bits) -> bits:
        """
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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
        Logical operation for bit vectors.

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

    def __rshift__(self: bits, other: Union[int, set]) -> bits:
        """
        Overloaded operator for performing rotation and shift operations on
        bit vectors. When the second parameter is an integer, a shift operation
        is performed. When the second parameter is a set containing a single
        integer, a rotation operation is performed.

        >>> bs = bits(map(bit, [1, 1, 1, 1, 0, 0, 0, 0]))
        >>> bs = bs >> 3
        >>> [b.value for b in bs]
        [0, 0, 0, 1, 1, 1, 1, 0]
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

    def __lshift__(self: bits, other: int) -> bits:
        """
        Overloaded operator for performing shift operations on bit vectors.

        >>> bs = bits(map(bit, [1, 1, 1, 1, 0, 0, 0, 0]))
        >>> bs = bs << 3
        >>> [b.value for b in bs]
        [1, 0, 0, 0, 0, 0, 0, 0]
        """
        return bits(self[other:]) ** bits([constant(0) for _ in range(other)])

    def __truediv__(self: bits, other: [Union, set, list]) -> Sequence[bits]:
        """
        Overloaded operator for splitting a bit vector into a collection of
        smaller bit vectors. Three operations are possible depending on the
        type of the second parameter.

        When the second parameter is an integer, this instance is split into
        that number of bit vectors. If the size of the vector is not an exact
        multiple of the integer, the parts in the result may not all be the
        same length.

        >>> bs = bits(map(bit, [1, 1, 1, 1, 0, 0, 0, 0]))
        >>> bss = list(bs / 2)
        >>> ([b.value for b in bss[0]], [b.value for b in bss[1]])
        ([1, 1, 1, 1], [0, 0, 0, 0])
        >>> bs = bits(map(bit, [1, 1, 1, 1, 0, 0, 0, 0]))
        >>> [len(bs) for bs in list(bs / 3)]
        [2, 3, 3]

        When the second parameter is a set containing a single integer, this
        instance is split into parts of the size specified by that integer.

        >>> bs = bits(map(bit, [1, 1, 1, 1, 0, 0, 0, 0]))
        >>> bss = list(bs / {2})
        >>> [[b.value for b in bs] for bs in bss]
        [[1, 1], [1, 1], [0, 0], [0, 0]]
        >>> bs = bits(map(bit, [1, 1, 1, 1, 0, 0, 0, 0]))
        >>> bss = list(bs / {1})
        >>> [[b.value for b in bs] for bs in bss]
        [[1], [1], [1], [1], [0], [0], [0], [0]]

        When the second parameter is a list of integers, this instance is split
        into parts the sizes of which correspond to the entries (in order) of
        the list of integers.

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

        >>> bs = bits(map(bit, [1, 1])) ** bits(map(bit, [0, 0]))
        >>> [b.value for b in bs]
        [1, 1, 0, 0]
        """
        return self + other

def constants(l: Sequence[int]) -> bits:
    """
    Synonym for concisely constructing a vector of :obj:`bit` objects that
    are designated as constants.

    >>> bit.circuit(circuit())
    >>> xs = constants([0, 0, 0])
    >>> ys = outputs(xs.not_())
    >>> int(ys)
    7
    >>> _ = bit.circuit() # Remove designated circuit.
    """
    return bits(map(constant, l))

def inputs(l: Sequence[int]) -> bits:
    """
    Synonym for concisely constructing a vector of :obj:`bit` objects that
    are designated as inputs.

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
    Synonym for concisely constructing a vector of :obj:`bit` objects that
    are designated as outputs.

    >>> bit.circuit(circuit())
    >>> xs = bits.zeros(3)
    >>> ys = outputs(xs.not_())
    >>> [y.value for y in ys]
    [1, 1, 1]
    >>> _ = bit.circuit() # Remove designated circuit.
    """
    return bits(map(output, l))

def synthesize(function: Callable, in_type=None, out_type=None) -> Callable:
    """
    Decorator for automatically synthesizing a circuit from a function that
    takes only :obj:`bit` and/or :obj:`bits` objects as its arguments and
    returns an output of type :obj:`bit` or :obj:`bits` (or a tuple or list
    thereof).

    In the example below, a function ``equal`` is defined that determines
    whether two bits are equivalent. The use of this decorator causes a
    circuit that implements this function to be constructed.

    >>> @synthesize
    ... def equal(x: bit, y: bit) -> bit:
    ...     return (x & y) | ((1 - x) & (1 - y))

    The synthesized :obj:`~circuit.circuit.circuit` object is introduced as
    an attribute of the function and can be evaluated on two bit values (as
    indicated by the function's type annotation).

    >>> [equal.circuit.evaluate([[x], [y]]) for x in (0, 1) for y in (0, 1)]
    [[[1]], [[0]], [[0]], [[1]]]

    Note that the function itself can still be invoked on its own in the usual
    manner if the supplied inputs are integers or :obj:`bit` instances. When
    the function is invoked in this way, the output of the function corresponds
    to its output type annotation.

    >>> equal(0, 1)
    0
    >>> b = equal(bit(0), bit(1))
    >>> isinstance(b, bit)
    True
    >>> int(b)
    0

    This decorator can also be applied to functions that are defined
    explicitly as operating on bit vectors (in the form of :obj:`bits`
    objects).

    >>> @synthesize
    ... def conjunction(xy: bits(2)) -> bits(2):
    ...     return (xy[0], xy[0] & xy[1])
    >>> [conjunction.circuit.evaluate([[x, y]]) for x in (0, 1) for y in (0, 1)]
    [[[0, 0]], [[0, 0]], [[1, 0]], [[1, 1]]]

    If the decorated function returns multiple outputs, the output type annotation
    should indicate this.

    >>> @synthesize
    ... def swap(x: bit, y: bit) -> (bit, bit):
    ...     return (y, x)
    >>> [swap.circuit.evaluate([[x], [y]]) for x in (0, 1) for y in (0, 1)]
    [[[0], [0]], [[1], [0]], [[0], [1]], [[1], [1]]]

    Functions to which this decorator is applied must have valid type annotations
    that specify the lengths of the input and output bit vectors.

    >>> @synthesize
    ... def equal(x, y):
    ...     return x & y
    Traceback (most recent call last):
      ...
    ValueError: function must have a type annotation for every argument
    >>> @synthesize
    ... def equal(x: bit, y: bit):
    ...     return x & y
    Traceback (most recent call last):
      ...
    ValueError: function must have an output type annotation
    >>> @synthesize
    ... def equal(x: 'ABC', y: 'ABC') -> bit:
    ...     return x & y
    Traceback (most recent call last):
      ...
    TypeError: input type annotations must be specified using bit or bits
    >>> @synthesize
    ... def swap(x: bit, y: bit) -> ('ABC', 'ABC'):
    ...     return (y, x)
    Traceback (most recent call last):
      ...
    TypeError: output type annotation components must be specified using bit or bits
    >>> @synthesize
    ... def swap(x: bit, y: bit) -> 'ABC':
    ...     return (y, x)
    Traceback (most recent call last):
      ...
    TypeError: output type must be specified using bit/bits, or a list/tuple thereof

    If an exception occurs during the execution (for the purpose of circuit synthesis)
    of the decorated function, then synthesis will fail.

    >>> @synthesize
    ... def equal(x: bit, y: bit) -> bit:
    ...     return 1 / 0 # Run-time error.
    Traceback (most recent call last):
      ...
    RuntimeError: automated circuit synthesis failed

    To support programmatic synthesis (*e.g.*, of circuit variants of many different
    sizes from the same function definition), this function can accept input and output
    type information via two optional parameters.

    >>> def conjunction(xy):
    ...     return (xy[0], xy[0] & xy[1])
    >>> c = synthesize(conjunction, {'xy': bits(2)}, bits(2))
    >>> [c.evaluate([[x, y]]) for x in (0, 1) for y in (0, 1)]
    [[[0, 0]], [[0, 0]], [[1, 0]], [[1, 1]]]

    >>> def swap(x: bit, y: bit) -> (bit, bit):
    ...     return (y, x)
    >>> c = synthesize(swap, (bit, bit), (bit, bit))
    >>> [c.evaluate([[x], [y]]) for x in (0, 1) for y in (0, 1)]
    [[[0], [0]], [[1], [0]], [[0], [1]], [[1], [1]]]

    When synthesizing programmatically, the input type information must be supplied
    either (1) as a dictionary that maps input type parameter names to types or (2)
    as a tuple or list (the length of which matches the number of parameters). The
    output type information must follow the same conventions as an output type
    annotation.

    >>> def equal(x, y):
    ...     return (x & y) | ((1 - x) & (1 - y))
    >>> c = synthesize(equal, (bit, bit), bit)
    >>> [c.evaluate([[x], [y]]) for x in (0, 1) for y in (0, 1)]
    [[[1]], [[0]], [[0]], [[1]]]
    >>> def swap(xy):
    ...     return [xy[1], xy[0]]
    >>> c = synthesize(swap, bits(2), bits(2))
    >>> [c.evaluate([[x, y]]) for x in (0, 1) for y in (0, 1)]
    [[[0, 0]], [[1, 0]], [[0, 1]], [[1, 1]]]

    If the supplied type information does not have the correct type or is incomplete,
    an exception is raised.

    >>> c = synthesize(equal, (bit, bit))
    Traceback (most recent call last):
      ...
    ValueError: must include input and output types when supplying type information via parameters
    >>> c = synthesize(equal, bits(2), bit)
    Traceback (most recent call last):
      ...
    ValueError: number of input type components does not match number of function arguments
    >>> c = synthesize(equal, ('ABC', 'ABC'), bit)
    Traceback (most recent call last):
      ...
    TypeError: input type components must be specified using bit or bits
    >>> c = synthesize(equal, 'bits(2)', bit)
    Traceback (most recent call last):
      ...
    TypeError: input type must be specified using bit/bits, or a dict/list/tuple thereof
    >>> c = synthesize(equal, {'x': 'ABC', 'y': 'ABC'}, bit)
    Traceback (most recent call last):
      ...
    TypeError: input type components must be specified using bit or bits
    >>> c = synthesize(equal, (bit, bit), 'ABC')
    Traceback (most recent call last):
      ...
    TypeError: output type must be specified using bit/bits, or a list/tuple thereof
    >>> c = synthesize(equal, (bit, bit), ('ABC', bit))
    Traceback (most recent call last):
      ...
    TypeError: output type components must be specified using bit or bits
    """
    # pylint: disable=R0912,R0915

    # Assume the type information is supplied via type annotations for the function until
    # it is determined otherwise.
    type_supplied_via_annotation = True

    # For forward-compatibility with PEP 563.
    eval_ = lambda a: eval(a) if isinstance(a, str) else a # pylint: disable=W0123

    # If the type information is supplied via parameters, then both input and output
    # types must be supplied.
    if (in_type is None and out_type is not None) or (in_type is not None and out_type is None):
        raise ValueError(
            "must include input and output types when supplying type information via parameters"
        )

    # If the type information is supplied via parameters, then both input and output
    # types must be supplied.
    if (in_type is not None) and (out_type is not None):
        type_supplied_via_annotation = False

        # Ensure that the input type is specified in a valid way.
        if in_type is bit or isinstance(in_type, bits_type):
            in_type = (in_type,)
        elif isinstance(in_type, (tuple, list)):
            if not all(t is bit or isinstance(t, bits_type) for t in in_type):
                raise TypeError("input type components must be specified using bit or bits")
        elif isinstance(in_type, dict):
            if not all(t is bit or isinstance(t, bits_type) for t in in_type.values()):
                raise TypeError("input type components must be specified using bit or bits")
        else:
            raise TypeError(
                "input type must be specified using bit/bits, or a dict/list/tuple thereof"
            )

        # If the type information is supplied via parameters, ensure that the input type
        # information is converted into a dictionary that maps the function's input variables
        # to the corresponding type information (*i.e.*, if the user supplied a tuple or list
        # and not a dictionary for the input type information).
        if isinstance(in_type, (tuple, list)):
            if len(in_type) != len(inspect.getfullargspec(function).args):
                raise ValueError(
                    "number of input type components does not match number of function arguments"
                )
            in_type = dict(zip(inspect.getfullargspec(function).args, in_type))

        # Ensure that the output type is specified in a valid way.
        if out_type is bit or isinstance(out_type, bits_type):
            out_type = (out_type,)
        elif isinstance(out_type, (tuple, list)):
            if not all(t is bit or isinstance(t, bits_type) for t in out_type):
                raise TypeError("output type components must be specified using bit or bits")
        else:
            raise TypeError(
                "output type must be specified using bit/bits, or a list/tuple thereof"
            )

    # If the type information is supplied the function's annotation, ensure that its structure
    # is valid (and extract it for later use).
    if type_supplied_via_annotation:
        # Ensure that every one of the function's arguments and its output has a corresponding
        # type annotation.
        if (
            len([() for k in function.__annotations__ if k != 'return']) \
            != \
            len(inspect.getfullargspec(function).args)
        ):
            print(function.__code__.co_varnames)
            print(function.__annotations__)
            raise ValueError("function must have a type annotation for every argument")
        if 'return' not in function.__annotations__:
            raise ValueError("function must have an output type annotation")

        # Extract the type annotations and evaluate them for later processing.
        in_type = {k: eval_(a) for (k, a) in function.__annotations__.items() if k != 'return'}
        out_type = eval_(function.__annotations__['return'])

        # Ensure that every argument's type annotation is specified in a valid way.
        if not all(t is bit or isinstance(t, bits_type) for t in in_type.values()):
            raise TypeError("input type annotations must be specified using bit or bits")

        # Ensure that the output type annotation is specified in a valid way.
        if out_type is bit or isinstance(out_type, bits_type):
            out_type = (out_type,)
        elif isinstance(out_type, (tuple, list)):
            if not all(t is bit or isinstance(t, bits_type) for t in out_type):
                raise TypeError(
                    "output type annotation components must be specified using bit or bits"
                )
        else:
            raise TypeError(
                "output type must be specified using bit/bits, or a list/tuple thereof"
            )

    # Designate the circuit to be synthesized.
    bit.circuit(circuit())

    # Construct the input bit vector(s) and output wrapper based on the function's
    # type annotation or type information supplied via the parameters.
    in_values = {k: (input(0) if a is bit else inputs([0] * a)) for (k, a) in in_type.items()}
    out_values = output if out_type == (bit,) else outputs

    # Construct a signature to the circuit based on the type annotation of the
    # decorated function.
    signature_ = signature(
        [(1 if a is bit else a) for a in in_type.values()],
        [(1 if a is bit else a) for a in out_type]
    )

    # Synthesize the circuit by evaluating the function, add it to the function as an
    # attribute, and give the circuit its signature.
    try:
        out_values(function(**in_values))
        function_circuit = bit.circuit()
        function_circuit.signature = signature_
        if type_supplied_via_annotation:
            function.circuit = function_circuit
    except Exception as e:
        raise RuntimeError('automated circuit synthesis failed') from e

    # Return the original function if the function is being used as a decorator, or
    # the circuit if the function is being used programmatically (*i.e.*, with type
    # information supplied via its parameters).
    return function if type_supplied_via_annotation else function_circuit

if __name__ == "__main__":
    doctest.testmod() # pragma: no cover
