.. cfdm documentation master file, created by
   sphinx-quickstart on Wed Aug  3 16:28:25 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. currentmodule:: cfdm
.. default-role:: obj

.. cfdm |release| documentation
   ============================

   ----

The CF (Climate and Forecast) metadata conventions (http://cfconventions.org) provide a description of the physical
meaning of data and of their spatial and temporal properties and are designed to promote the creation, processing, and sharing of climate
and forecasting data using Network Common Data Form (netCDF, https://www.unidata.ucar.edu/software/netcdf) files and libraries.

The CF data model identifies the fundamental elements of CF and shows
how they relate to each other, independently of the netCDF encoding.

The field construct, which corresponds to a CF-netCDF data variable
with all of its metadata, is central to the CF data model. The field
construct consists of a data array and the definition of its domain,
ancillary metadata fields defined over the same domain, and cell
method constructs to describe how the cell values represent the
variation of the physical quantity within the cells of the domain. The
domain itself is defined collectively by various other constructs
included in the field: domain axis, dimension coordinate, auxiliary
coordinate, cell measure, coordinate reference and domain ancillary
constructs. See https://www.geosci-model-dev.net/10/4619/2017/ for
full details.

The **cfdm** library implements the CF data model for its internal
data structures and so is able to process any CF-compliant dataset. It
is, however, not strict about CF compliance so that partially
conformant datasets may be modified in memory as well as ingested from
existing datasets, or written to new datasets.

The **cfdm** package can

* read netCDF datasets into field constructs

* create new field constructs in memory

* inspect field constructs

* modify field construct metadata and data in memory

* create subspaces of field constructs

* write field constructs to a netCDF dataset on disk

Quick start
===========

A Field object stores a field construct as defined by the CF data
model. It is a container for a data array and metadata to describe the
physical nature of the data, and its domain that describes the
positions of each element of the data array. The metadata comprises
simple propoerties (such as descriptive strings) and objects
representing other constructs of the CF data model (such as a
dimension coordinate object, that unambiguously describes cell
locations along a single domain axis).

Reading fields from disk
------------------------

The `cfdm.read` function will a read netCDF file from disk and return
its contents as one or more field objects:


>>> f = cfdm.read('file.nc')

Displaying the contents
-----------------------

The contents of a field may be exposed with three different levels of
detail.

The built-in `repr` function returns a short, one-line description of
the field:

>>> f
<Field: air_temperature(time(12), latitude(64), longitude(128)) K>

This gives the identity of the field (air_temperature), the identities
and sizes of its data array axes (time, latitude and longitude with
sizes 12, 64 and 128 respectively) and the units of the field's data
array (K).

The built-in `str` function returns the same information as the the
one-line output, along with short descriptions of the field's other
components:

>>> print f
air_temperature field summary
-----------------------------
Data           : air_temperature(time(1200), latitude(64), longitude(128)) K
Cell methods   : time: mean (interval: 1.0 month)
Axes           : time(12) = [ 450-11-01 00:00:00, ...,  451-10-16 12:00:00] noleap calendar
               : latitude(64) = [-87.8638000488, ..., 87.8638000488] degrees_north
               : longitude(128) = [0.0, ..., 357.1875] degrees_east
               : height(1) = [2.0] m

This shows that the field has a cell method and four dimension
coordinates, one of which (height) is a coordinate for a size 1 axis
that is not a axis of the field's data array. The units and first and
last values of the coordinates' data arrays are given and relative
time values are translated into strings.

The field's `~cfdm.Field.dump` method describes each component's
properties, as well as the first and last values of the field's data
array::

   >>> f.dump()
   ======================
   Field: air_temperature
   ======================
   Axes:
       height(1)
       latitude(64)
       longitude(128)
       time(12)
   
   Data(time(12), latitude(64), longitude(128)) = [[[236.512756348, ..., 256.93371582]]] K
   cell_methods = time: mean (interval: 1.0 month)
   
   experiment_id = 'pre-industrial control experiment'
   long_name = 'Surface Air Temperature'
   standard_name = 'air_temperature'
   title = 'model output prepared for IPCC AR4'

   Dimension coordinate: time
       Data(time(12)) = [ 450-11-16 00:00:00, ...,  451-10-16 12:00:00] noleap calendar
       Bounds(time(12), 2) = [[ 450-11-01 00:00:00, ...,  451-11-01 00:00:00]] noleap calendar
       axis = 'T'
       long_name = 'time'
       standard_name = 'time'
   
   Dimension coordinate: latitude
       Data(latitude(64)) = [-87.8638000488, ..., 87.8638000488] degrees_north
       Bounds(latitude(64), 2) = [[-90.0, ..., 90.0]] degrees_north
       axis = 'Y'
       long_name = 'latitude'
       standard_name = 'latitude'
   
   Dimension coordinate: longitude
       Data(longitude(128)) = [0.0, ..., 357.1875] degrees_east
       Bounds(longitude(128), 2) = [[-1.40625, ..., 358.59375]] degrees_east
       axis = 'X'
       long_name = 'longitude'
       standard_name = 'longitude'
   
   Dimension coordinate: height
       Data(height(1)) = [2.0] m
       axis = 'Z'
       long_name = 'height'
       positive = 'up'
       standard_name = 'height'

.. _fs-data-array:

Data
----

A field's data array is a `Data` object and is returned by its
`~Field.data` attribute.

>>> f.data
<CF Data: [[[89.0, ..., 66.0]]] K>

The `Data` object:

* Contains an N-dimensional array with many similarities to a `numpy`
  array.

* Contains the units of the array elements.

* Supports masked arrays [#f1]_, regardless of whether or not it was
  initialized with a masked array.

  
.. toctree::
   :maxdepth: 3
   
   introduction

.. toctree::
   :maxdepth: 3

   getting_started

.. toctree::
   :maxdepth: 3

   reference 

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

