from setuptools import setup

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name="circuitry",
    version="0.2.0",
    packages=["circuitry",],
    install_requires=["parts>=1.0.2","circuit>=0.3.1",],
    license="MIT",
    url="https://github.com/nthparty/circuitry",
    author="Andrei Lapets",
    author_email="a@lapets.io",
    description="Embedded domain-specific combinator library for "+\
                "assembling abstract definitions of logic circuits.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    test_suite="nose.collector",
    tests_require=["nose"],
)
