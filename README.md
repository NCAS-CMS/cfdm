cfdm
====

A complete implementation of the CF data model.

Documentation
=============

https://ncas-cms.github.io/cfdm

Tutorial
========

https://ncas-cms.github.io/cfdm/tutorial

Installation
============

https://ncas-cms.github.io/cfdm/installation

Functionality
=============

The ``cfdm`` package implements the CF data model
(https://doi.org/10.5194/gmd-10-4619-2017) for its internal data
structures and so is able to process any CF-compliant dataset. It is
not strict about CF-compliance, however, so that partially conformant
datasets may be ingested from existing datasets and written to new
datasets. This is so that datasets which are partially conformant may
nonetheless be modified in memory.

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

The ``cfdm`` package can:

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

Command line utility
====================

During installation the `cfdump` command line tool is also installed,
which generates text descriptions of the field constructs contained in
a netCDF dataset.

Hierarchical groups
===================

Hierarchical groups provide a powerful mechanism to structure
variables within datasets. A future 1.8.x release of cfdm will include
support for netCDF4 files containing data organised in hierarchical
groups, but this is not available in version 1.8.0 (even though it is
allowed in CF-1.8).

Tests
=====

Tests are run from within the ``cfdm/test`` directory:

    $ python run_tests.py
