=========
circuitry
=========

Embedded domain-specific combinator library for the abstract assembly and automated synthesis of logical circuits.

|pypi| |readthedocs| |actions| |coveralls|

.. |pypi| image:: https://badge.fury.io/py/circuitry.svg
   :target: https://badge.fury.io/py/circuitry
   :alt: PyPI version and link.

.. |readthedocs| image:: https://readthedocs.org/projects/circuitry/badge/?version=latest
   :target: https://circuitry.readthedocs.io/en/latest/?badge=latest
   :alt: Read the Docs documentation status.

.. |actions| image:: https://github.com/nthparty/circuitry/workflows/lint-test-cover-docs/badge.svg
   :target: https://github.com/nthparty/circuitry/actions/workflows/lint-test-cover-docs.yml
   :alt: GitHub Actions status.

.. |coveralls| image:: https://coveralls.io/repos/github/nthparty/circuitry/badge.svg?branch=main
   :target: https://coveralls.io/github/nthparty/circuitry?branch=main
   :alt: Coveralls test coverage summary.

Purpose
-------
This embedded domain-specific language (DSL) makes it possible to write an algorithm in Python that operates on bit values and/or bit vectors, and then to interpret that algorithm implementation as a circuit definition in order to synthesize automatically a logical circuit represented using the `circuit <https://pypi.org/project/circuit>`__ library. Additional background information and examples can be found in a `relevant report <https://eprint.iacr.org/2020/1604>`__.

Installation and Usage
----------------------
This library is available as a `package on PyPI <https://pypi.org/project/circuitry>`__::

    python -m pip install circuitry

The library can be imported in the usual ways::

    import circuitry
    from circuitry import *

Examples
^^^^^^^^

.. |bit| replace:: ``bit``
.. _bit: https://circuitry.readthedocs.io/en/2.0.0/_source/circuitry.html#circuitry.circuitry.bit

.. |synthesize| replace:: ``synthesize``
.. _synthesize: https://circuitry.readthedocs.io/en/2.0.0/_source/circuitry.html#circuitry.circuitry.synthesize

.. |circuit_| replace:: ``circuit``
.. _circuit_: https://circuit.readthedocs.io/en/2.0.0/_source/circuit.html#circuit.circuit.circuit

.. |disjunction| replace:: ``__or__``
.. _disjunction: https://circuitry.readthedocs.io/en/2.0.0/_source/circuitry.html#circuitry.circuitry.bit.__or__

This library makes it possible to embed within Python a function that operates on individual bits and/or bit vectors (subject to specific limitations) and then to automatically synthesize a logical circuit that implements that function. In the simple example below, the defined bit equality function takes two |bit|_ objects as its inputs and returns one |bit|_ object as its output. Because nearly all built-in Python operators are supported by the |bit|_ class via `appropriate method definitions <https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types>`__ (*e.g.*, see the |disjunction|_ method), the statements and expressions in the function can employ a straightforward and familiar syntax::

    >>> from circuitry import *
    >>> @synthesize
    ... def equal(x: bit, y: bit) -> bit:
    ...     return (x & y) | ((1 - x) & (1 - y))

The function itself can be invoked in the usual manner if the supplied inputs are integers or instances of the |bit|_ class::

    >>> equal(0, 1)
    0
    >>> b = equal(bit(0), bit(1))
    >>> isinstance(b, bit)
    True
    >>> int(b)
    0

.. |circuit__| replace:: ``circuit``
.. _circuit__: https://circuit.readthedocs.io/en/2.0.0/_source/circuit.html#circuit.circuit.circuit

The |synthesize|_ decorator automatically synthesizes the corresponding circuit (as an instance of the |circuit_|_ class defined in the `circuit <https://pypi.org/project/circuit>`__ library). The synthesized |circuit__|_ object is stored within an attribute of the function itself and can be evaluated on two bit values (as specified by the function's type annotation). See the documentation of the `circuit <https://pypi.org/project/circuit>`__ library for more information on how input bit vectors should be structured when evaluating a circuit::

    >>> equal.circuit.evaluate([[0], [1]])
    [[0]]

.. |bits| replace:: ``bits``
.. _bits: https://circuitry.readthedocs.io/en/2.0.0/_source/circuitry.html#circuitry.circuitry.bits

The |synthesize|_ decorator can also be applied to functions that are defined explicitly as operating on *bit vectors* (where bit vectors can be represented as lists of integers or as |bits|_ objects). Furthermore, functions can be invoked in other functions, making it possible to reuse modular algorithm components. In the example below, the bit vector equality function invokes the bit equality function defined above::

    >>> @synthesize
    ... def equals(xs: bits(8), ys: bits(8)) -> bit:
    ...     z = 1
    ...     for i in range(8):
    ...         z = z & equal(xs[i], ys[i])
    ...     return z
    >>> bs = [0, 1, 1, 0, 1, 0, 1, 0]
    >>> equals.circuit.evaluate([bs, bs])
    [[1]]
    >>> equals.circuit.count() # Number of gates in circuit.
    66

Because a circuit is synthesized via standard execution of a decorated Python function, all native Python language features (and even external libraries) can be employed. The most important constraint (which is the responsibility of the programmer to maintain) is that the execution of the function (*i.e.*, the `flow of control <https://en.wikipedia.org/wiki/Control_flow>`__) should not depend on the *values* of the inputs bits. The alternative implementation below demonstrates that recursion and higher-order functions can be used within decorated functions::

    >>> from functools import reduce
    >>> @synthesize
    ... def equals(xs: bits(8), ys: bits(8)) -> bit:
    ...     es = [equal(x, y) for (x, y) in zip(xs, ys)]
    ...     return reduce((lambda e0, e1: e0 & e1), es)
    >>> bs = [0, 1, 1, 0, 1, 0, 1, 0]
    >>> equals.circuit.evaluate([bs, list(reversed(bs))])
    [[0]]
    >>> equals.circuit.count() # Number of gates in circuit.
    64

A `more complex example <https://circuitry.readthedocs.io/en/2.0.0/_source/test_circuitry.html#test.test_circuitry.sha256>`__ involving an implementation of SHA-265 that conforms to the `FIPS 180-4 specification <https://www.tandfonline.com/doi/abs/10.1080/01611194.2012.687431>`__ is found in the `testing script <https://circuitry.readthedocs.io/en/2.0.0/_source/test_circuitry.html>`__ that accompanies this library. The SHA-256 example is also described in a `relevant report <https://eprint.iacr.org/2020/1604>`__.

Development
-----------
All installation and development dependencies are fully specified in ``pyproject.toml``. The ``project.optional-dependencies`` object is used to `specify optional requirements <https://peps.python.org/pep-0621>`__ for various development tasks. This makes it possible to specify additional options (such as ``docs``, ``lint``, and so on) when performing installation using `pip <https://pypi.org/project/pip>`__::

    python -m pip install .[docs,lint]

Documentation
^^^^^^^^^^^^^
The documentation can be generated automatically from the source files using `Sphinx <https://www.sphinx-doc.org>`__::

    python -m pip install .[docs]
    cd docs
    sphinx-apidoc -f -E --templatedir=_templates -o _source .. && make html

Testing and Conventions
^^^^^^^^^^^^^^^^^^^^^^^
All unit tests are executed and their coverage is measured when using `pytest <https://docs.pytest.org>`__ (see the ``pyproject.toml`` file for configuration details)::

    python -m pip install .[test]
    python -m pytest

The subset of the unit tests included in the module itself and the *documentation examples* that appear in the testing script can be executed separately using `doctest <https://docs.python.org/3/library/doctest.html>`__::

    python src/circuitry/circuitry.py -v
    python test/test_circuitry.py -v

Style conventions are enforced using `Pylint <https://pylint.pycqa.org>`__::

    python -m pip install .[lint]
    python -m pylint src/circuitry test/test_circuitry.py

Contributions
^^^^^^^^^^^^^
In order to contribute to the source code, open an issue or submit a pull request on the `GitHub page <https://github.com/nthparty/circuitry>`__ for this library.

Versioning
^^^^^^^^^^
Beginning with version 0.1.0, the version number format for this library and the changes to the library associated with version number increments conform with `Semantic Versioning 2.0.0 <https://semver.org/#semantic-versioning-200>`__.

Publishing
^^^^^^^^^^
This library can be published as a `package on PyPI <https://pypi.org/project/circuitry>`__ by a package maintainer. First, install the dependencies required for packaging and publishing::

    python -m pip install .[publish]

Ensure that the correct version number appears in ``pyproject.toml``, and that any links in this README document to the Read the Docs documentation of this package (or its dependencies) have appropriate version numbers. Also ensure that the Read the Docs project for this library has an `automation rule <https://docs.readthedocs.io/en/stable/automation-rules.html>`__ that activates and sets as the default all tagged versions. Create and push a tag for this version (replacing ``?.?.?`` with the version number)::

    git tag ?.?.?
    git push origin ?.?.?

Remove any old build/distribution files and package the source into a distribution archive::

    rm -rf build dist src/*.egg-info
    python -m build --sdist --wheel .

Finally, upload the package distribution archive to `PyPI <https://pypi.org>`__ using the `twine <https://pypi.org/project/twine>`__ package::

    python -m twine upload dist/*
