.. currentmodule:: cfdm
.. default-role:: obj

Field tutorial
==============

The field construct defined by the CF data model is represented by a
`Field` object.

Reading from disk
-----------------

The `cfdm.read` function reads netCDF file from disk and returns its
contents as a list one or more `Field` objects:

>>> import cfdm
>>> f = cfdm.read('file.nc')

Inspection
----------

The contents of a field may be inspected at three different levels of
detail.

The built-in `repr` function returns a short, one-line description of
the field:

   >>> f
   [<Field: air_temperature(time(12), latitude(64), longitude(128)) K>,
    <Field: air_temperature(time(12), latitude(64), longitude(128)) K>]

This gives the identity of the field (air_temperature), the identities
and sizes of its data array axes (time, latitude and longitude with
sizes 12, 64 and 128 respectively) and the units of the field's data
array (K).

The built-in `str` function returns the same information as the the
one-line output, along with short descriptions of the field's other
components:

   >>> print f[0]
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

   >>> g = f[0]
   >>> g.dump()
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

Construct classes
-----------------

Each construct of the CF data model has a corresponding `cfdm` class:

=====================  ==============================  ====================
Class                  Description                     Construct           
=====================  ==============================  ====================
`Field`                Scientific data discretised     Field               
                       within a domain		                         
`DomainAxis`           Independent axes of the domain  Domain Axis         
`DimensionCoordinate`  Domain cell locations           Dimension Coordinate
`AuxiliaryCoordinate`  Domain cell locations           Auxiliary Coordinate
=====================  ==============================  ====================

The constructs contained by the field (i.e. the metadata constructs)
are accessed with the field's `~Field.constructs` and
`~Field.construct` methods:

   >>> f.constructs

   >>> f.construct('latitude')

Where applicable, the metadata constructs share the same API as the
field. For example, this means that any construct that has a data
array will have a `!get_array` method to access the data as a numpy
array

   >>> lon = f.construct('longitude')
   >>> lon
   <>
   >>> lon.set_property('long_name', 'Longitude')
   >>> lon.properties()
   >>> lon.data[2] = 3453453454
   >>> lon.get_array()
   
Other classes are required to represent certain components of CF data
model constructs:

======================  ==============================  ======================
Class                   Description                     Parent classes
======================  ==============================  ======================
`Bounds`                Cell bounds                     `DimensionCoordinate`,
                                                        `AuxiliaryCoordinate`,
                                                        `DomainAncillary`

`CoordinateConversion`  A formula for                   `CoordinateReference`
		        converting coordinate values
		        taken from the dimension or
		        auxiliary coordinate
			constructs
		        to a different coordinate
			system

`Data`                                                  `Field`,
                                                        `DimensionCoordinate`,
                                                        `AuxiliaryCoordinate`,
                                                        `DomainAncillary`,
							`CellMeasure`,
							`FieldAncillary`
			
`Datum`                 The zeroes                      `CoordinateReference`
                        of the dimension
                        and auxiliary coordinate
			constructs which define the
			coordinate system
======================  ==============================  ======================


Writing to disk
---------------

The `cfdm.write` function writes fields to a netCDF file on disk:

   >>> cfdm.write(f, 'new_file.nc')

Equality
--------

Whether or not two fields are the same is ascertained with either of
the field's `~cfdm.Field.equals` methods.

   >>> g = cfdm.read('new_file.nc')
   >>> f[0].equals(g[0])
   True

Properties
----------

.. autosummary::
   :nosignatures:
   :template: method.rst

   ~cfdm.Field.del_property
   ~cfdm.Field.get_property
   ~cfdm.Field.has_property
   ~cfdm.Field.set_property
   ~cfdm.Field.properties

Data
----

Creation
--------

Exernal variables
-----------------

Discrete sampling geomtries
---------------------------

Gathering
---------
