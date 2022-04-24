=========
circuitry
=========

Embedded domain-specific combinator library for assembling abstract definitions of logic circuits.

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
This embedded domain-specific language (DSL) makes it possible to write an algorithm in Python that operates over bit vectors, and then to interpret that algorithm implementation as a circuit definition in order to synthesize a logic circuit represented using the `circuit <https://github.com/reity/circuit>`_ library. Additional background information and examples can be found in a `relevant report <https://eprint.iacr.org/2020/1604>`_.

Package Installation and Usage
------------------------------
The package is available on `PyPI <https://pypi.org/project/circuitry/>`_::

    python -m pip install circuitry

The library can be imported in the usual ways::

    import circuitry
    from circuitry import *

Documentation
-------------
.. include:: toc.rst

The documentation can be generated automatically from the source files using `Sphinx <https://www.sphinx-doc.org/>`_::

    cd docs
    python -m pip install -r requirements.txt
    sphinx-apidoc -f -E --templatedir=_templates -o _source .. ../setup.py && make html

Testing and Conventions
-----------------------
All unit tests are executed and their coverage is measured when using `pytest <https://docs.pytest.org/>`_ (see ``setup.cfg`` for configuration details)::

    python -m pip install pytest pytest-cov
    python -m pytest

Alternatively, all unit tests are included in the module itself and can be executed using `doctest <https://docs.python.org/3/library/doctest.html>`_::

    python circuitry/circuitry.py -v

Style conventions are enforced using `Pylint <https://www.pylint.org/>`_::

    python -m pip install pylint
    python -m pylint circuitry

Contributions
-------------
In order to contribute to the source code, open an issue or submit a pull request on the `GitHub page <https://github.com/nthparty/circuitry>`_ for this library.

Versioning
----------
Beginning with version 0.1.0, the version number format for this library and the changes to the library associated with version number increments conform with `Semantic Versioning 2.0.0 <https://semver.org/#semantic-versioning-200>`_.

Publishing
----------
This library can be published as a `package on PyPI <https://pypi.org/project/circuitry/>`_ by a package maintainer. Install the `wheel <https://pypi.org/project/wheel/>`_ package, remove any old build/distribution files, and package the source into a distribution archive::

    python -m pip install wheel
    rm -rf dist *.egg-info
    python setup.py sdist bdist_wheel

Next, install the `twine <https://pypi.org/project/twine/>`_ package and upload the package distribution archive to PyPI::

    python -m pip install twine
    python -m twine upload dist/*
