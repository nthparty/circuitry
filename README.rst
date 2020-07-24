=========
circuitry
=========

Embedded domain-specific combinator library for assembling abstract definitions of logic circuits.

|pypi| |travis| |coveralls|

.. |pypi| image:: https://badge.fury.io/py/circuitry.svg
   :target: https://badge.fury.io/py/circuitry
   :alt: PyPI version and link.

.. |travis| image:: https://travis-ci.com/nthparty/circuitry.svg?branch=master
    :target: https://travis-ci.com/nthparty/circuitry

.. |coveralls| image:: https://coveralls.io/repos/github/nthparty/circuitry/badge.svg?branch=master
   :target: https://coveralls.io/github/nthparty/circuitry?branch=master

Purpose
-------
This embedded domain-specific language (DSL) makes it possible to write an algorithm in Python that operates over bit vectors, and then to interpret that algorithm implementation as a circuit definition in order to synthesize a logic circuit represented using the `circuit <https://github.com/reity/circuit>`_ library.

Package Installation and Usage
------------------------------
The package is available on PyPI::

    python -m pip install circuitry

The library can be imported in the usual ways::

    import circuitry
    from circuitry import *

Testing and Conventions
-----------------------
All unit tests are executed and their coverage is measured when using `nose <https://nose.readthedocs.io/>`_ (see ``setup.cfg`` for configution details)::

    nosetests

Alternatively, all unit tests are included in the module itself and can be executed using `doctest <https://docs.python.org/3/library/doctest.html>`_::

    python circuitry/circuitry.py -v

Style conventions are enforced using `Pylint <https://www.pylint.org/>`_::

    pylint circuitry

Contributions
-------------
In order to contribute to the source code, open an issue or submit a pull request on the GitHub page for this library.

Versioning
----------
Beginning with version 0.1.0, the version number format for this library and the changes to the library associated with version number increments conform with `Semantic Versioning 2.0.0 <https://semver.org/#semantic-versioning-200>`_.
