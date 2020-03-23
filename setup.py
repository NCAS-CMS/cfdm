from distutils.core import setup
#from setuptools import setup

import os
import fnmatch
import sys
import re

def find_package_data_files(directory):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, '*'):
                filename = os.path.join(root, basename)
                yield filename.replace('cfdm/', '', 1)

def _read(fname):
    """Returns content of a file.

    """
    fpath = os.path.dirname(__file__)
    fpath = os.path.join(fpath, fname)
    with open(fpath, 'r') as file_:
        return file_.read()

def _get_version():
    """Returns library version by inspecting core/__init__.py file.

    """
    return re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                     _read("cfdm/core/__init__.py"),
                     re.MULTILINE).group(1)

version      = _get_version()
packages     = ['cfdm']

long_description = """The **cfdm** Python package is a complete implementation of the `CF
data model <https://www.geosci-model-dev.net/10/4619/2017>`_, that
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

* read field constructs from netCDF datasets,
* create new field constructs in memory,
* inspect field constructs,
* test whether two field constructs are the same,
* modify field construct metadata and data,
* create subspaces of field constructs,
* write field constructs to netCDF datasets on disk,
* incorporate, and create, metadata stored in external files,
* read, write, and create data that have been compressed by convention
  (i.e. ragged or gathered arrays), whilst presenting a view of the
  data in its uncompressed form, and
* read, write, and create coordinates defined by geometry cells.

Documentation
=============

https://ncas-cms.github.io/cfdm

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

Hierarchical groups
===================

Hierarchical groups provide a powerful mechanism to structure
variables within datasets. A future 1.8.x release of cfdm will include
support for netCDF4 files containing data organised in hierarchical
groups, but this is not available in version 1.8.0 (even though it is
allowed in CF-1.8).

Source code
===========

This project is hosted in a `GitHub repository
<https://github.com/NCAS-CMS/cfdm>`_ where you may access the most
up-to-date source."""

setup(name = "cfdm",
      long_description = long_description,
      version      = version,
      description  = "A complete implementation of the CF data model",
      author       = "David Hassell",
      maintainer   = "David Hassell",
      maintainer_email = "david.hassell@ncas.ac.uk",
      author_email = "david.hassell@ncas.ac.uk",
      url          = "https://ncas-cms.github.io/cfdm",
      download_url = "https://pypi.org/project/cfdm/#files",
      platforms    = ["Linux", "MacOS", "Windows"],
      keywords     = ['cf', 'netcdf', 'data', 'science',
                      'oceanography', 'meteorology', 'climate'],
      classifiers  = ["Development Status :: 4 - Beta",
                      "Intended Audience :: Science/Research", 
                      "License :: OSI Approved :: MIT License", 
                      "Topic :: Software Development",
                      "Topic :: Scientific/Engineering",
                      "Operating System :: OS Independent",
                      "Programming Language :: Python :: 2.7",
                      "Programming Language :: Python :: 3",
                      ],
      packages     = ['cfdm',
                      'cfdm.abstract',
                      'cfdm.core',
                      'cfdm.core.abstract',
                      'cfdm.core.data',
                      'cfdm.core.data.abstract',
                      'cfdm.core.mixin',
                      'cfdm.data',
                      'cfdm.data.abstract',
                      'cfdm.data.mixin',
                      'cfdm.mixin',
                      'cfdm.read_write',
                      'cfdm.read_write.abstract',
                      'cfdm.read_write.netcdf',
                      'cfdm.test',],
      scripts      = ['scripts/cfdump'],
#      python_requires = '>= 2.7',
      install_requires = [
          'future>=0.16.0',
          'netcdf4>=1.5.3',
          'cftime>=1.1.1',
          'numpy>=1.15',
      ],
)
