cfdm
====

**cfdm** is a complete implementation of the [CF data
model](https://www.geosci-model-dev.net/10/4619/2017), that identifies
the fundamental elements of the [CF
conventions](http://cfconventions.org/) and shows how they relate to
each other, independently of the
[netCDF](https://www.unidata.ucar.edu/software/netcdf/) encoding.

The central element defined by the CF data model is the **field
construct**, which corresponds to a CF-netCDF data variable with all
of its metadata.

The **cfdm** package can

* read field constructs from netCDF datasets,

* create new field constructs in memory,

* inspect field constructs,

* modify field construct metadata and data,

* create subspaces of field constructs,

* write field constructs to netCDF datasets on disk,

* incorporate, and create, metadata stored in external files,

* read and write data that has been compressed by convention
  (i.e. ragged or gathered arrays), whilst presenting a view of the
  data in its uncompressed form.

Documentation
=============

https://ncas-cms.github.io/cfdm

Tests
=====

Tests are run from within the ``cfdm/test`` directory:

    python run_tests.py
