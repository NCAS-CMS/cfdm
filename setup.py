import os
import re

from setuptools import find_packages, setup


def _read(fname):
    """Returns content of a file."""
    fpath = os.path.dirname(__file__)
    fpath = os.path.join(fpath, fname)
    with open(fpath, "r") as file_:
        return file_.read()


def _get_version():
    """Returns library version by inspecting core/__init__.py file."""
    return re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
        _read("cfdm/core/__init__.py"),
        re.MULTILINE,
    ).group(1)


version = _get_version()
packages = ["cfdm"]

long_description = """The **cfdm** Python package is a complete reference implementation
of the `CF data model
<https://www.geosci-model-dev.net/10/4619/2017>`_ for CF-1.11, that
identifies the fundamental elements of the `CF conventions
<http://cfconventions.org/>`_ and shows how they relate to each other,
independently of the `netCDF
<https://www.unidata.ucar.edu/software/netcdf/>`_ encoding.

The central element defined by the CF data model is the **field
construct**, which corresponds to a CF-netCDF data variable with all
of its metadata.

A simple example of reading a field construct from a file and
inspecting it:

    >>> import cfdm
    >>> f = cfdm.read('file.nc')
    >>> f
    [<Field: air_temperature(time(12), latitude(64), longitude(128)) K>]
    >>> print(f[0])
    Field: air_temperature (ncvar%tas)
    ----------------------------------
    Data            : air_temperature(time(12), latitude(64), longitude(128)) K
    Cell methods    : time(12): mean (interval: 1.0 month)
    Dimension coords: time(12) = [0450-11-16 00:00:00, ..., 0451-10-16 12:00:00] noleap
                    : latitude(64) = [-87.8638, ..., 87.8638] degrees_north
                    : longitude(128) = [0.0, ..., 357.1875] degrees_east
                    : height(1) = [2.0] m

The **cfdm** package can

* read field and domain constructs from netCDF, CDL, and Zarr datasets with a choice of netCDF backends,
* be fully flexible with respect to dataset storage chunking,
* create new field and domain constructs in memory,
* write and append field and domain constructs to netCDF datasets on disk,
* read, write, and manipulate UGRID mesh topologies,
* read, write, and create coordinates defined by geometry cells,
* read and write netCDF4 string data-type variables,
* read, write, and create netCDF and CDL datasets containing hierarchical groups,
* inspect field and domain constructs,
* test whether two constructs are the same,
* modify field and domain construct metadata and data,
* create subspaces of field and domain constructs,
* incorporate, and create, metadata stored in external files, and
* read, write, and create data that have been compressed by convention
  (i.e. ragged or gathered arrays, or coordinate arrays compressed
  by subsampling), whilst presenting a view of the data in its
  uncompressed form,
* read and write that data that are quantized to eliminate false
  precision.

Documentation
=============

https://ncas-cms.github.io/cfdm

Dask
====

From version 1.11.2.0 the `cfdm` package uses `Dask
<https://docs.dask.org>`_ for all of its data manipulations.

Tutorial
========

https://ncas-cms.github.io/cfdm/tutorial

Installation
============

https://ncas-cms.github.io/cfdm/installation

Command line utility
====================

During installation the `cfdump` command line tool is also installed,
which generates text descriptions of the field constructs contained
in a netCDF dataset.

Source code
===========

This project is hosted in a `GitHub repository
<https://github.com/NCAS-CMS/cfdm>`_ where you can access the most
up-to-date source."""

# Get dependencies
requirements = open("requirements.txt", "r")
install_requires = requirements.read().splitlines()

tests_require = (
    [
        "pytest",
        "pycodestyle",
        "coverage",
        "scipy",
    ],
)
extras_require = {
    "documentation": [
        "sphinx==2.4.5",
        "sphinx-copybutton",
        "sphinx-toggleprompt",
        "sphinxcontrib-spelling",
    ],
    "pre-commit hooks": [
        "pre-commit",
        "black",
        "docformatter",
        "flake8",
        "pydocstyle",
    ],
}

setup(
    name="cfdm",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    version=version,
    description="A Python reference implementation of the CF data model",
    author="David Hassell, Sadie Bartholomew",
    author_email="david.hassell@ncas.ac.uk",
    maintainer="David Hassell, Sadie Bartholomew",
    url="https://ncas-cms.github.io/cfdm",
    download_url="https://pypi.org/project/cfdm/#files",
    platforms=["Linux", "MacOS", "Windows"],
    license="MIT",
    keywords=[
        "cf",
        "netcdf",
        "data",
        "science",
        "oceanography",
        "meteorology",
        "climate",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    packages=find_packages(),
    scripts=["scripts/cfdump"],
    python_requires=">=3.9",
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
    include_package_data=True,
)
