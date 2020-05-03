=========
circuitry
=========

Embedded domain-specific combinator library for assembling abstract definitions of logic circuits.

.. image:: https://badge.fury.io/py/circuitry.svg
   :target: https://badge.fury.io/py/circuitry
   :alt: PyPI version and link.

Purpose
-------
This embedded domain-specific language (DSL) makes it possible to write an algorithm in Python that operates over bit vectors, and then to interpret that algorithm implementation as a circuit definition in order to synthesize a logic circuit.

Package Installation and Usage
------------------------------
The package is available on PyPI::

    python -m pip install circuitry

The library can be imported in the usual ways::

    import circuitry
    from circuitry import circuitry
