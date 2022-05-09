"""
Test suite containing published examples that demonstrate how the
library can be used to synthesize circuits from functions.
"""
# pylint: disable=C0415 # Accommodates published example in its original form.
from unittest import TestCase
from itertools import product

from circuitry import * # pylint: disable=W0401, W0614

@synthesize
def equal(x: bit, y: bit) -> bit:
    """
    Function that performs a simple single-bit equality function
    using logical and arithmetic operations.
    """
    return (x & y) | ((1 - x) & (1 - y))

@synthesize
def equals_iterative(xs: bits(8), ys: bits(8)) -> bit:
    """
    Function that performs a simple single-bit equality function
    using logical and arithmetic operations.
    """
    z = 1
    for i in range(len(xs)):
        z = z & equal(xs[i], ys[i])
    return z

@synthesize
def equals_functional(xs: bits(8), ys: bits(8)) -> bit:
    from functools import reduce
    es = [equal(x, y) for (x, y) in zip(xs, ys)]
    return reduce((lambda e0, e1: e0 & e1), es)

class Test_circuitry(TestCase):
    """
    Tests involving published examples demonstrating the use of the library.
    """
    def test_example_equal(self):
        """
        Tests synthesis of a circuit for a simple single-bit equality
        function.
        """
        for (x, y) in product(*[[0, 1]] * 2):
            self.assertEqual(
                equal.circuit.evaluate([x, y]),
                [int(x == y)]
            )

    def test_example_equals_iterative(self):
        """
        Tests synthesis of a circuit for a simple bit vector equality
        function.
        """
        vectors = product(*[[0, 1]] * 8)
        for (xs, ys) in product(vectors, vectors):
            self.assertEqual(
                equals_iterative.circuit.evaluate(xs + ys),
                [int(xs == ys)]
            )

    def test_example_equals_functional(self):
        """
        Tests synthesis of a circuit for a simple bit vector equality
        function.
        """
        vectors = product(*[[0, 1]] * 8)
        for (xs, ys) in product(vectors, vectors):
            self.assertEqual(
                equals_functional.circuit.evaluate(xs + ys),
                [int(xs == ys)]
            )
