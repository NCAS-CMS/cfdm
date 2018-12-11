.. currentmodule:: cfdm
.. default-role:: obj

**Introduction**
================

----

Version |release| for version |version| of the CF conventions.

The Python cfdm package is a complete implementation of the CF data
model.

**CF conventions**
------------------

----

The CF (Climate and Forecast) metadata conventions
(http://cfconventions.org) provide a description of the physical
meaning of data and of their spatial and temporal properties and are
designed to promote the creation, processing, and sharing of climate
and forecasting data using netCDF files and libraries
(https://www.unidata.ucar.edu/software/netcdf).

**CF data model**
-----------------

----

The `CF data model <https://www.geosci-model-dev.net/10/4619/2017>`_
identifies the fundamental elements ("constructs") of CF and shows how
they relate to each other, independently of the netCDF encoding.

The **field** construct defined by the CF data model, which
corresponds to a CF-netCDF data variable with all of its metadata, is
the central construct that includes all of the other constructs. It
consists of

- descriptive properties that apply to field construct as a whole
  (e.g. the standard name),

- a data array, and

- "metadata constructs" that describe
  
  - the locations of each cell of the data array (i.e. the "domain"),
    and

  - the physical nature of each cell's datum.

The domain is defined by

* **domain axis** constructs (corresponding to CF-netCDF dimensions or
  scalar coordinate variables),

* **dimension coordinate** constructs (corresponding to CF-netCDF
  coordinate variables or numeric scalar coordinate variables),

* **auxiliary coordinate** constructs (corresponding to CF-netCDF
  auxiliary coordinate variables and non-numeric scalar coordinate
  variables),

* **coordinate reference** constructs (corresponding to CF-netCDF grid
  mapping variables or the formula_terms attribute of a coordinate
  variable),

* **domain ancillary** constructs (corresponding to CF-netCDF
  variables named by the formula_terms attribute of a coordinate
  variable), and

* **cell measure** constructs (corresponding to CF-netCDF cell measure
  variables).
  
The physical nature of individual data values are described by 

* **field ancillary** constructs (corresponding to CF-netCDF ancillary
  variables), and

* **cell method** constructs (corresponding to a CF-netCDF
  cell_methods attribute of data variable).

A complete description of the CF data model, including UML diagrams,
is available to download at
https://www.geosci-model-dev.net/10/4619/2017.

**Implementation**
------------------

----

The cfdm package implements the CF data model for its internal data
structures and so is able to process any CF-compliant dataset. It is
not strict about CF compliance, however, so that partially conformant
datasets may be modified in memory, as well as ingested from existing
datasets and written to new datasets.

The cfdm package can

* read field constructs from netCDF datasets,

* create new field constructs in memory,

* inspect field constructs,

* test whether two field constructs are the same,

* modify field construct metadata and data,

* create subspaces of field constructs,

* write field constructs to netCDF datasets on disk,

* incorporate, and create, metadata stored in external files, and

* read, write, and create data that have been compressed by convention
  (i.e. ragged or gathered arrays), whilst presenting a view of the
  data in its uncompressed form.

