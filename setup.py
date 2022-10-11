from setuptools import setup

with open("README.rst", "r") as fh:
    long_description = fh.read().replace(".. include:: toc.rst\n\n", "")

# The lines below can be parsed by `docs/conf.py`.
name = "circuitry"
version = "2.0.0"

setup(
    name=name,
    version=version,
    packages=[name,],
    install_requires=[
        "parts~=1.5",
        "bitlist~=1.0",
        "circuit~=2.0"
    ],
    license="MIT",
    url="https://github.com/nthparty/circuitry",
    author="Andrei Lapets",
    author_email="a@lapets.io",
    description="Embedded domain-specific combinator library for the abstract "+\
                "assembly and automated synthesis of logical circuits.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
)
