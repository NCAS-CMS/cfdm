.. currentmodule:: cfdm
.. default-role:: obj

.. _field_structure:

Introduction to the `Field` object
==================================

A `Field` object stores a field as defined by the `CF-netCDF
conventions <http://cfconventions.org>`_ and the `CF data model
<http://cf-trac.llnl.gov/trac/ticket/95>`_. It is a container for a
data array and metadata comprising properties to describe the physical
nature of the data and a coordinate system (called a *domain*), which
describes the positions of each element of the data array.

It is structured in exactly the same way as a filed in the CF data
model and, as in the CF data model, all components of a `Field` object
are optional.

Displaying the contents
-----------------------

The structure may be exposed with three different levels of detail.

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

Data attributes
---------------

Some of a field's reserved attributes return information on its
data. See the :ref:`list of reserved data attributes
<field_attributes>` for details.

For example, to find the shape of the data and to retrieve the data
array as an actual `numpy` array:

>>> f.shape
(1, 3, 4)
>>> f.array
array([[[ 89.,  80.,  71.],
        [ 85.,  76.,  67.],
        [ 83.,  74.,  65.],
        [ 84.,  75.,  66.]]])

The data array's missing value mask may be retrieved with the
`~Field.mask` attribute. The mask is returned as a new field with a
boolean data array:

>>> m = f.mask
>>> m.data
<Data: [[[False, ..., True]]]>

If the field contains no missing data then a mask field with False
values is still returned.


CF properties
-------------

Standard CF data variable properties (such as
`~cfdm.Field.standard_name`, `~cfdm.Field.units`, etc.) all have reserved
attribute names. See the :ref:`list of reserved CF properties
<field_cf_properties>` for details. These properties may be set,
retrieved and deleted like normal python object attributes:

>>> f.standard_name = 'air_temperature'
>>> f.standard_name
'air_temperature'
>>> del f.standard_name

as well as with the dedicated `~Field.setprop`, `~Field.getprop` and
`~Field.delprop` field methods:

>>> f.setprop('standard_name', 'air_temperature')
>>> f.getprop('standard_name')
'air_temperature'
>>> f.delprop('standard_name')

Non-standard CF properties *must* be accessed using these three methods:

>>> f.setprop('foo', 'bar')
>>> f.getprop('foo')
'bar'
>>> f.delprop('foo')

All of the field's CF properties may be retrieved with the field's
`~Field.properties` attribute:

>>> f.properties
{'_FillValue': 1e+20,
 'foo': 'bar',
 'long_name': 'Surface Air Temperature',
 'standard_name': 'air_temperature',
 'units': 'K'}


Other attributes
----------------

A field has other reserved attributes which have a variety of
roles. See the :ref:`list of reserved attributes <field_attributes>`
for details.

Any unreserved attribute may be set on a field object with, in
general, no special meaning attached to it. The following unreserved
attributes do, however, have particular interpretations:

=========  ==============================================================
Attribute  Description
=========  ==============================================================
`!file`    The name of the file the field was read from     
`!id`      An identifier for the field in the absence of a  
           standard name. See the `~Field.identity` method for details.
`!ncvar`   A netCDF variable name of the field.           
=========  ==============================================================

All of the field's attributes may be retrieved with the field's
`~Field.attributes` attribute:

>>> f.attributes
{'ncar': 'tas'}

Methods
-------

A field has a large range of methods which, in general, either return
information about the field or change the field in place. See the
:ref:`list of methods <field_methods>` and :ref:`manipulating fields
<manipulating-fields>` section for details.

.. _domain_structure:

Domain structure
----------------

A field's domain completely describes the field's coordinate system
and is stored in its `~Field.domain` attribute, the value of which is
a `cf.Domain` object.

It contains axes (which describe the field's dimensionality),
dimension coordinate, auxiliary coordinate and cell measure objects
(which themselves contain data arrays and properties to describe them)
and coordinate reference objects (which relate the field's coordinate
values to locations in a planetary reference frame).

Each item has a unique internal identifier (is a string containing a
number), which serves to link related items.

Items
^^^^^

Domain items are stored in the following objects:

===========================  ========================
Item                         `cf` object
===========================  ========================
Dimension coordinate object  `cf.DimensionCoordinate`
Auxiliary coordinate object  `cf.AuxiliaryCoordinate`
Cell measure object          `cf.CellMeasure`
Coordinate reference object  `cf.CoordinateReference`
===========================  ========================

These items may be retrieved with a variety of methods, some specific
to each item type (such as `cf.Field.dim`) and some more generic (such
as `cf.Field.coords` and `cf.Field.item`):

===========================  ==================================================================
Item                         Field retrieval methods
===========================  ==================================================================
Dimension coordinate object  `~Field.dim`, `~Field.dims`, `~Field.coord`, `~Field.coords`
	                     `~Field.item`, `~Field.items`
Auxiliary coordinate object  `~Field.aux`, `~Field.auxs`, `~Field.coord`, `~Field.coords`
	                     `~Field.item`, `~Field.items`
Cell measure object          `~Field.measure`, `~Field.measures`, `~Field.item`, `~Field.items`
Coordinate reference object  `~Field.ref`, `~Field.refs`, `~Field.item`, `~Field.items`
===========================  ==================================================================

In each case the singular method form (such as `~Field.aux`) returns
an actual domain item whereas the plural method form (such as
`~Field.auxs`) returns a dictionary whose keys are the domain item
identifiers with corresponding values of the items themselves.

For example, to retrieve a unique dimension coordinate object with a
standard name of "time":

>>> f.dim('time')
<CF DimensionCoordinate: time(12) noleap>

To retrieve all coordinate objects and their domain identifiers:

>>> f.coords()
{'dim0': <CF DimensionCoordinate: time(12) noleap>,
 'dim1': <CF DimensionCoordinate: latitude(64) degrees_north>,
 'dim2': <CF DimensionCoordinate: longitude(128) degrees_east>,
 'dim3': <CF DimensionCoordinate: height(1) m>}

To retrieve all domain items and their domain identifiers:

>>> f.items()
{'dim0': <CF DimensionCoordinate: time(12) noleap>,
 'dim1': <CF DimensionCoordinate: latitude(64) degrees_north>,
 'dim2': <CF DimensionCoordinate: longitude(128) degrees_east>,
 'dim3': <CF DimensionCoordinate: height(1) m>}

In this example, all of the items happen to be coordinates.

Axes
^^^^

Common axes of variation in the field's data array and the domain's
items are defined by the domain's axes.

Each axis has a domain identifier (such as ``'dim1'``) and an integer
size and is stored in the domain's `!dimension_sizes` attribute:

>>> f.domain.dimension_sizes
{'dim1': 19, 'dim0': 12, 'dim2': 73, 'dim3': 96}

Particular axes may be retrieved with the `~cfdm.Field.axes` method:

>>> f.axes()
set(['dim1', 'dim0' 'dim2' 'dim3'])
>>> f.axes(size=19)
set(['dim1'])
>>> f.axes('time')
set(['dim0'])

The axes spanned by a domain item or the field's data array may be
retrieved with the fields `~cfdm.Field.item_axes` or
`~cfdm.Field.data_axes` methods respectively:

>>> f.item_axes('time')
['dim0']
>>> f.data_axes()
['dim0', 'dim1' 'dim2' 'dim3']

Note that the field's data array may contain fewer size 1 axes than
its domain.

----

.. rubric:: Footnotes

.. [#f1] Arrays that may have missing or invalid entries
