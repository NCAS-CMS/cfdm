.. currentmodule:: cfdm
.. default-role:: obj

.. _introduction:

CF conventions
--------------

The CF (Climate and Forecast) metadata conventions
(http://cfconventions.org) provide a description of the physical
meaning of data and of their spatial and temporal properties and are
designed to promote the creation, processing, and sharing of climate
and forecasting data using Network Common Data Form (netCDF,
https://www.unidata.ucar.edu/software/netcdf) files and libraries.


CF data model
-------------

The CF data model identifies the fundamental elements of CF and
shows how they relate to each other, independently of the netCDF
encoding.

The **field** construct, which corresponds to a CF-netCDF data
variable with all of its metadata, is central to the CF data
model. The field construct consists of descriptive properties, a data
array, the definition of its domain (that describes the locations of
each cell of the data array), **field ancillary** constructs
containing metadata defined over the same **domain**, and **cell
method** constructs to describe how the cell values represent the
variation of the physical quantity within the cells of the domain. The
domain is defined collectively by the following constructs of the CF
data model: **domain axis**, **dimension coordinate**, **auxiliary
coordinate**, **cell measure**, **coordinate reference** and **domain
ancillary** constructs.

A complete description of the CF data model, including UML diagrams,
is available at https://www.geosci-model-dev.net/10/4619/2017.

Implementation
--------------

The **cfdm** library implements the CF data model for its internal
data structures and so is able to process any CF-compliant dataset. It
is, however, not strict about CF compliance so that partially
conformant datasets may be modified in memory as well as ingested from
existing datasets, or written to new datasets.

The **cfdm** package can

* read netCDF datasets into field constructs,

* create new field constructs in memory,

* inspect field constructs,

* modify field construct metadata and data in memory,

* create subspaces of field constructs, and

* write field constructs to a netCDF dataset on disk,

* incorporate metadata stored in external files,

* read and write data that has been compressed by convention
  (i.e. ragged or gathered arrays), whilst presenting a view of the
  data in its uncompressed form.
