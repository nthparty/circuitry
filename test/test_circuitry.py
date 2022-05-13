"""
Test suite containing published examples that demonstrate how the
library can be used to synthesize circuits from functions.
"""
# pylint: disable=C0301 # Accommodate original format of published examples.
from unittest import TestCase
from itertools import product
from functools import reduce
import secrets
import hashlib
from parts import parts
from bitlist import bitlist

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
    for i in range(8):
        z = z & equal(xs[i], ys[i])
    return z

@synthesize
def equals_functional(xs: bits(8), ys: bits(8)) -> bit:
    es = [equal(x, y) for (x, y) in zip(xs, ys)]
    return reduce((lambda e0, e1: e0 & e1), es)

def add32(xs, ys):
    """
    Addition of 32-bit vectors intended for use with the SHA-256
    implementation.
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
    produce an intermediate digest.
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
    Accept ``message``, a list of bit vectors each having 8 bits (for a total
    number of bits up to 1024), and compute a SHA-256 message digest as the output
    consisting of 32 distinct bit vectors (each having 8 bits).
    """
    # Split input into 8-bit vectors.
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
        Tests synthesis of the circuit corresponding to the SHA-256
        implementation.
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

                # Compute circuit evaluation result to built-in SHA-256 implementation.
                self.assertEqual(
                    bitlist(output_bits).hex(),
                    hashlib.sha256(input_bytes).hexdigest()
                )
