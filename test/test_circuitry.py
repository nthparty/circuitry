"""
Test suite containing examples that demonstrate how the library can be used
to synthesize circuits from functions.

To view the source code of an example function, click its **[source]** link.
These examples (as well as additional background information) are discussed
in more detail in a `relevant report <https://eprint.iacr.org/2020/1604>`_.
"""
# pylint: disable=C0301 # Accommodate original format of published examples.
from __future__ import annotations
import doctest
from unittest import TestCase
from itertools import product
from functools import reduce
import secrets
import hashlib
from parts import parts
from bitlist import bitlist

try:
    from circuitry import * # pylint: disable=W0401, W0614
except: # pylint: disable=W0702
    # Support validation of docstrings in this script via its direct execution.
    import sys
    sys.path.append('./circuitry')
    from circuitry import * # pylint: disable=W0401, W0614

@synthesize
def equal(x: bit, y: bit) -> bit:
    """
    Function that performs a simple single-bit equality calculation
    using logical and arithmetic operations.

    The synthesized :obj:`~circuit.circuit.circuit` object is introduced as
    an attribute of the function and can be evaluated on two bit values (as
    indicated by the function's type annotation).

    >>> equal.circuit.evaluate([[0], [1]])
    [[0]]

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
    """
    return (x & y) | ((1 - x) & (1 - y))

@synthesize
def equals_iterative(xs: bits(8), ys: bits(8)) -> bit:
    """
    Function that employs an iterative approach and performs a bit vector
    equality calculation. This function invokes both the single-bit equality
    function defined above and the logical conjunction operation.

    >>> bs = [0, 1, 1, 0, 1, 0, 1, 0]
    >>> equals_iterative.circuit.evaluate([bs, bs])
    [[1]]
    >>> equals_iterative.circuit.evaluate([bs, list(reversed(bs))])
    [[0]]
    """
    z = 1
    for i in range(8):
        z = z & equal(xs[i], ys[i])
    return z

@synthesize
def equals_functional(xs: bits(8), ys: bits(8)) -> bit:
    """
    Function that employs a functional approach and performs a bit vector
    equality calculation. This function invokes both the single-bit equality
    function defined above and the logical conjunction operation.

    >>> bs = [0, 1, 1, 0, 1, 0, 1, 0]
    >>> equals_functional.circuit.evaluate([bs, bs])
    [[1]]
    >>> equals_functional.circuit.evaluate([bs, list(reversed(bs))])
    [[0]]
    """
    es = [equal(x, y) for (x, y) in zip(xs, ys)]
    return reduce((lambda e0, e1: e0 & e1), es)

def add32(xs, ys):
    """
    Function that performs addition of 32-bit vectors. This function is
    intended for use by the :obj:`sha256` function that implements
    SHA-256.

    Note that this is a helper function that is invoked by the :obj:`sha256`
    function. **It is not decorated** because **execution of** :obj:`sha256`
    **is what synthesizes the overall SHA-256 circuit**. The body of this
    function could have been inlined within the body of the :obj:`sha256`
    function without impacting the synthesis of the SHA-256 circuit.
    """
    (xs, ys) = (list(reversed(xs)), list(reversed(ys)))
    (x0, xt, y0, yt) = (xs[0], xs[1:], ys[0], ys[1:])
    (s, c) = (x0 ^ y0, x0 & y0)
    def combine(zs_, xy):
        c = zs_.pop()
        (_xor, _and) = (xy[0] ^ xy[1], xy[0] & xy[1])
        return zs_ + [_xor ^ c, _and | (_xor & c)]
    zs = [s] + list(reduce(combine, zip(xt, yt), [c]))[:-1]
    return bits(list(reversed(zs)))

def sha256_iteration(d_8_32s, m_64_8s):
    """
    Perform a single iteration of the SHA-256 hash computation over the current
    digest (consisting of 32 distinct bit vectors, each having 8 bits) based on a
    message portion (consisting of 64 distinct bit vectors, each having 8 bits) to
    produce the next digest.

    Note that this is a helper function that is invoked by the :obj:`sha256`
    function. **It is not decorated** because **execution of** :obj:`sha256`
    **is what synthesizes the overall SHA-256 circuit**. The body of this
    function could have been inlined within the body of the :obj:`sha256`
    function without impacting the synthesis of the SHA-256 circuit.
    """
    # Table of constants (64 bit vectors each having 32 bits).
    table = [constants(list(bitlist(i, 32))) for i in [
        1116352408, 1899447441, 3049323471, 3921009573,  961987163, 1508970993, 2453635748, 2870763221,
        3624381080,  310598401,  607225278, 1426881987, 1925078388, 2162078206, 2614888103, 3248222580,
        3835390401, 4022224774,  264347078,  604807628,  770255983, 1249150122, 1555081692, 1996064986,
        2554220882, 2821834349, 2952996808, 3210313671, 3336571891, 3584528711,  113926993,  338241895,
        666307205,   773529912, 1294757372, 1396182291, 1695183700, 1986661051, 2177026350, 2456956037,
        2730485921, 2820302411, 3259730800, 3345764771, 3516065817, 3600352804, 4094571909,  275423344,
        430227734,   506948616,  659060556,  883997877,  958139571, 1322822218, 1537002063, 1747873779,
        1955562222, 2024104815, 2227730452, 2361852424, 2428436474, 2756734187, 3204031479, 3329325298
    ]]

    # Functions used during the hash computation.
    Ch = lambda x, y, z: (x & y) ^ ((~x) & z)
    Maj = lambda x, y, z: ((x & y) ^ (x & z)) ^ (y & z)
    Sigma_0 = lambda bs: ((bs >> {2}) ^ (bs >> {13})) ^ (bs >> {22})
    Sigma_1 = lambda bs: ((bs >> {6}) ^ (bs >> {11})) ^ (bs >> {25})
    sigma_0 = lambda bs: ((bs >> {7}) ^ (bs >> {18})) ^ (bs >> 3)
    sigma_1 = lambda bs: ((bs >> {17}) ^ (bs >> {19})) ^ (bs >> 10)

    w = [] # Message schedule.
    for j in range(16):
        w.append(m_64_8s[j*4] + m_64_8s[j*4+1] + m_64_8s[j*4+2] + m_64_8s[j*4+3])

    for j in range(16, 64):
        w.append(add32(add32(add32(sigma_1(w[j-2]), w[j-7]), sigma_0(w[j-15])), w[j-16]))

    wv = d_8_32s # Eight 32-bit working variables.
    for j in range(64):
        c = add32(add32(Ch(wv[4], wv[5], wv[6]), table[j]), w[j])
        t1 = add32(add32(wv[7], Sigma_1(wv[4])), c)
        t2 = add32(Sigma_0(wv[0]), Maj(wv[0], wv[1], wv[2]))
        wv = [add32(t1, t2), wv[0], wv[1], wv[2], add32(wv[3], t1), wv[4], wv[5], wv[6]]

    return [add32(d_8_32s[j], wv[j]) for j in range(8)] # Return intermediate hash.

@synthesize
def sha256(message: bits(512)) -> bits(256):
    """
    Accept  an appropriately padded bit vector of length 512, and compute a SHA-256 message
    digest as the output (represented as a bit vector having 256 bits).

    This SHA-256 algorithm conforms to the
    `FIPS 180-4 specification <https://www.tandfonline.com/doi/abs/10.1080/01611194.2012.687431>`_
    and expects inputs that are appropriately padded. The example below demonstrates
    how an appropriate input byte vector can be constructed for the synthesized
    circuit.

    >>> input_bytes = bytes([1, 2, 3])
    >>> input_padding = (
    ...     bytes([128] + ([0] * (55 - len(input_bytes)))) +
    ...     int(8 * len(input_bytes)).to_bytes(8, 'big')
    ... )

    When evaluating the synthesized circuit, the input must be converted into a bit vector.
    Note that the output consists of a list containing a single bit vector that has 256 bits.

    >>> [output_bits] = sha256.circuit.evaluate([
    ...     [
    ...         b
    ...         for byte in (input_bytes + input_padding)
    ...         for b in bitlist(byte, 8)
    ...     ]
    ... ])

    The output can be compared to a reference implementation.

    >>> bitlist(output_bits).hex() == hashlib.sha256(input_bytes).hexdigest()
    True
    """
    # Split input bit vector into a list of bit vectors, each having 8 bits.
    message = [bits(bs) for bs in parts(message, length=8)]

    # Initial digest value represented as eight 32-bit vectors.
    digest = [constants(list(bitlist(i, 32))) for i in [
        1779033703, 3144134277, 1013904242, 2773480762,
        1359893119, 2600822924,  528734635, 1541459225
    ]]

    # Perform hash computation for appropriate number of iterations (based on message length).
    for i in range(len(message) // 64):
        digest = sha256_iteration(digest, message[(i * 64) : (i * 64) + 64])

    # Flatten 8-bit vectors each having 32 bits into a single 256-bit vector.
    return [b for bs in digest for b in bs]

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
                equal.circuit.evaluate([[x], [y]]),
                [[int(x == y)]]
            )

    def test_example_equals_iterative(self):
        """
        Tests synthesis of a circuit for a simple bit vector equality
        function.
        """
        vectors = product(*[[0, 1]] * 8)
        for (xs, ys) in product(vectors, vectors):
            self.assertEqual(
                equals_iterative.circuit.evaluate([xs, ys]),
                [[int(xs == ys)]]
            )

    def test_example_equals_functional(self):
        """
        Tests synthesis of a circuit for a simple bit vector equality
        function.
        """
        vectors = product(*[[0, 1]] * 8)
        for (xs, ys) in product(vectors, vectors):
            self.assertEqual(
                equals_functional.circuit.evaluate([xs, ys]),
                [[int(xs == ys)]]
            )

    def test_example_sha256(self):
        """
        Tests the circuit corresponding to an implementation of SHA-256 that was
        synthesized directly using the synthesis decorator for a specific length
        of input to the hash function.
        """
        # Perform a few tests for each length of input.
        for length in range(1, 56, 3):
            for _ in range(3):
                # Assemble input and padding.
                input_bytes = secrets.token_bytes(length)
                input_padding = \
                    bytes([128] + ([0] * (55 - length))) + \
                    int(8 * length).to_bytes(8, 'big')

                # Evaluate the synthesized circuit on the input bit vector.
                [output_bits] = sha256.circuit.evaluate([
                    [
                        b
                        for byte in (input_bytes + input_padding)
                        for b in bitlist(byte, 8)
                    ]
                ])

                # Compute circuit evaluation result to that of the built-in SHA-256
                # implementation.
                self.assertEqual(
                    bitlist(output_bits).hex(),
                    hashlib.sha256(input_bytes).hexdigest()
                )

    def test_example_sha256_resynthesis_per_input_length(self):
        """
        Tests multiple circuit variants corresponding to SHA-256, each synthesized
        programmatically for one of a collection of specific input length ranges.

        Synthesis of different SHA-256 circuits for different input lengths is
        necessary because unlike a general-purpose programming lanaguage with
        support fo iteration constructs (such as loops), circuits are fixed and
        can only operate on one length of input. Due to padding requirements, input
        lengths for SHA-256 come in exact multiples of 512; therefore, a distinct
        circuit must be synthesized for each multiple of 512.

        Note that while the :obj:`sha256` method is annotated for a specific input
        bit vector size, the tests below override this annotation by invoking
        circuit synthesis programmatically (thus supplying a different annotation).
        """
        # Perform a few tests for each length of input.
        for multiple in range(2, 6):
            # Synthesize the circuit for this particular length of input.
            c = synthesize(sha256, [bits(512 * multiple)], [bits(256)])

            # Run a test for the two boundary values of current input length range.
            length_minimum = (64 * (multiple - 1)) - 8
            for length in [length_minimum, length_minimum + 63]:
                # Assemble input and padding.
                input_bytes = secrets.token_bytes(length)
                input_padding = \
                    bytes([128] + ([0] * ((64 * multiple) - 9 - length))) + \
                    int(8 * length).to_bytes(8, 'big')

                # Evaluate the synthesized circuit on the input bit vector.
                [output_bits] = c.evaluate([
                    [
                        b
                        for byte in (input_bytes + input_padding)
                        for b in bitlist(byte, 8)
                    ]
                ])

                # Compute circuit evaluation result to that of the built-in SHA-256
                # implementation.
                self.assertEqual(
                    bitlist(output_bits).hex(),
                    hashlib.sha256(input_bytes).hexdigest()
                )

# Always invoke the doctests in this module.
doctest.testmod()
