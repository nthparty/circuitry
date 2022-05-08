"""
Test suite containing published examples that demonstrate how the
library can be used to synthesize circuits from functions.
"""
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
