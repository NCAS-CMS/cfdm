.. currentmodule:: cfdm
.. default-role:: obj

.. _tutorial:

Tutorial
========

The field construct defined by the CF data model consists of

* descriptive properties that apply to field construct as a whole

* a data array, and

* a variety of "metadata constructs" that describe

  * the locations of each cell of the data array,

  * the physical nature of each cell's datum.

The field construct is represented by the `Field` class.

The :ref:`metadata constructs <constructs>` comprise `DomainAxis`,
`DimensionCoordinate`, `AuxiliaryCoordinate`, `CoordinateReference`,
`DomainAncillary`, `CellMeasure`, `FieldAncillary`, and `CellMethod`
classes.

.. _read:

Reading datasets
----------------

The `cfdm.read` function reads a `netCDF
<https://www.unidata.ucar.edu/software/netcdf/>`_ file from disk or
from an `OPeNDAP URL
<https://www.unidata.ucar.edu/software/netcdf/docs/dap_accessing_data.html>`_
[#opendap]_ and returns its contents as a list one or more `Field`
objects.

For example, to read the file **file.nc** (:download:`download
<../netcdf_files/file.nc>`, 9kB) [#files]_:

.. code:: python

   >>> import cfdm
   >>> x = cfdm.read('file.nc')
   >>> type(x)
   list

All formats of netCDF3 and netCDF4 files can be read.

The `cfdm.read` function has optional parameters to

* provide files that contain :ref:`external variables <external>`, and

* return "metadata" netCDF variables (i.e. those that are referenced
  from CF-netCDF data variables) as independent fields.

*Note on performance*
  Descriptive properties are always read into memory, but `lazy
  loading <https://en.wikipedia.org/wiki/Lazy_loading>`_ is employed
  for all data arrays, which means that no data is read into memory
  until the data is required for inspection or to modify the array
  contents. This maximises the number of fields that may be read
  within a session, and makes the read operation very fast.

.. _inspection:
  
Inspection
----------

The contents of a field may be inspected at three different levels of
detail.

.. rubric:: 1: Minimal detail

The built-in `repr` function returns a short, one-line description of
the field:

.. code:: python

   >>> x
   [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
    <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>]
   >>> (q, t) = x
   >>> q
   <Field: specific_humidity(latitude(5), longitude(8)) 1>
   
This gives the identity of the field (e.g. "specific_humidity"), the
identities and sizes of the domain axis constructs spanned by the
field's data array (latitude and longitude with sizes 5 and 8
respectively) and the units of the field's data ("1").

.. rubric:: 2: Medium detail

The built-in `str` function returns the same information as the the
one-line output, along with short descriptions of the field's other
metadata constructs:

.. code:: python

   >>> print(q)
   Field: specific_humidity (ncvar%q)
   ----------------------------------
   Data            : specific_humidity(latitude(5), longitude(8)) 1
   Cell methods    : area: mean
   Dimension coords: time(1) = [2019-01-01 00:00:00]
                   : latitude(5) = [-75.0, ..., 75.0] degrees_north
                   : longitude(8) = [22.5, ..., 337.5] degrees_east
      
   >>> print(t)
   Field: air_temperature (ncvar%ta)
   ---------------------------------
   Data            : air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K
   Cell methods    : grid_latitude(10): grid_longitude(9): mean where land (interval: 0.1 degrees) time(1): maximum
   Field ancils    : air_temperature standard_error(grid_latitude(10), grid_longitude(9)) = [[0.81, ..., 0.78]] K
   Dimension coords: time(1) = [2019-01-01 00:00:00]
                   : atmosphere_hybrid_height_coordinate(1) = [1.5]
                   : grid_latitude(10) = [2.2, ..., -1.76] degrees
                   : grid_longitude(9) = [-4.7, ..., -1.18] degrees
   Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[53.941, ..., 50.225]] degrees_N
                   : longitude(grid_longitude(9), grid_latitude(10)) = [[2.004, ..., 8.156]] degrees_E
                   : long_name:Grid latitude name(grid_latitude(10)) = [--, ..., kappa]
   Cell measures   : measure%area(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2
   Coord references: atmosphere_hybrid_height_coordinate
                   : rotated_latitude_longitude
   Domain ancils   : ncvar%a(atmosphere_hybrid_height_coordinate(1)) = [10.0] m
                   : ncvar%b(atmosphere_hybrid_height_coordinate(1)) = [20.0]
                   : surface_altitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 270.0]] m

This shows the same one-line summary of the field as before, with
one-line summaries of all of the metadata constructs, which include
the first and last values of their data arrays.

.. rubric:: 3: Full detail

The field's `~cfdm.Field.dump` method gives all properties of all
constructs and includes other construct components, such as coordinate
bounds, as well as the first and last values of the field's data array:

.. code:: python

   >>> q.dump()
   ----------------------------------
   Field: specific_humidity (ncvar%q)
   ----------------------------------
   Conventions = 'CF-1.7'
   project = 'research'
   standard_name = 'specific_humidity'
   units = '1'
   
   Data(latitude(5), longitude(8)) = [[0.003, ..., 0.032]] 1
   
   Cell Method: area: mean
   
   Domain Axis: latitude(5)
   Domain Axis: longitude(8)
   Domain Axis: time(1)
   
   Dimension coordinate: latitude
       standard_name = 'latitude'
       units = 'degrees_north'
       Data(latitude(5)) = [-75.0, ..., 75.0] degrees_north
       Bounds:Data(latitude(5), 2) = [[-90.0, ..., 90.0]]
   
   Dimension coordinate: longitude
       standard_name = 'longitude'
       units = 'degrees_east'
       Data(longitude(8)) = [22.5, ..., 337.5] degrees_east
       Bounds:Data(longitude(8), 2) = [[0.0, ..., 360.0]]
   
   Dimension coordinate: time
       standard_name = 'time'
       units = 'days since 2018-12-01'
       Data(time(1)) = [2019-01-01 00:00:00]
  
   >>> t.dump()
   ---------------------------------
   Field: air_temperature (ncvar%ta)
   ---------------------------------
   Conventions = 'CF-1.7'
   project = 'research'
   standard_name = 'air_temperature'
   units = 'K'
   
   Data(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) = [[[0.0, ..., 89.0]]] K
   
   Cell Method: grid_latitude(10): grid_longitude(9): mean where land (interval: 0.1 degrees)
   Cell Method: time(1): maximum
   
   Field Ancillary: air_temperature standard_error
       standard_name = 'air_temperature standard_error'
       units = 'K'
       Data(grid_latitude(10), grid_longitude(9)) = [[0.81, ..., 0.78]] K
   
   Domain Axis: atmosphere_hybrid_height_coordinate(1)
   Domain Axis: grid_latitude(10)
   Domain Axis: grid_longitude(9)
   Domain Axis: time(1)
   
   Dimension coordinate: atmosphere_hybrid_height_coordinate
       computed_standard_name = 'altitude'
       standard_name = 'atmosphere_hybrid_height_coordinate'
       Data(atmosphere_hybrid_height_coordinate(1)) = [1.5]
       Bounds:Data(atmosphere_hybrid_height_coordinate(1), 2) = [[1.0, 2.0]]
   
   Dimension coordinate: grid_latitude
       standard_name = 'grid_latitude'
       units = 'degrees'
       Data(grid_latitude(10)) = [2.2, ..., -1.76] degrees
       Bounds:Data(grid_latitude(10), 2) = [[2.42, ..., -1.98]]
   
   Dimension coordinate: grid_longitude
       standard_name = 'grid_longitude'
       units = 'degrees'
       Data(grid_longitude(9)) = [-4.7, ..., -1.18] degrees
       Bounds:Data(grid_longitude(9), 2) = [[-4.92, ..., -0.96]]
   
   Dimension coordinate: time
       standard_name = 'time'
       units = 'days since 2018-12-01'
       Data(time(1)) = [2019-01-01 00:00:00]
   
   Auxiliary coordinate: latitude
       standard_name = 'latitude'
       units = 'degrees_N'
       Data(grid_latitude(10), grid_longitude(9)) = [[53.941, ..., 50.225]] degrees_N
   
   Auxiliary coordinate: longitude
       standard_name = 'longitude'
       units = 'degrees_E'
       Data(grid_longitude(9), grid_latitude(10)) = [[2.004, ..., 8.156]] degrees_E
   
   Auxiliary coordinate: long_name:Grid latitude name
       long_name = 'Grid latitude name'
       Data(grid_latitude(10)) = [--, ..., kappa]
   
   Domain ancillary: ncvar%a
       units = 'm'
       Data(atmosphere_hybrid_height_coordinate(1)) = [10.0] m
       Bounds:Data(atmosphere_hybrid_height_coordinate(1), 2) = [[5.0, 15.0]]
   
   Domain ancillary: ncvar%b
       Data(atmosphere_hybrid_height_coordinate(1)) = [20.0]
       Bounds:Data(atmosphere_hybrid_height_coordinate(1), 2) = [[14.0, 26.0]]
   
   Domain ancillary: surface_altitude
       standard_name = 'surface_altitude'
       units = 'm'
       Data(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 270.0]] m
   
   Coordinate reference: atmosphere_hybrid_height_coordinate
       Coordinate conversion:computed_standard_name = altitude
       Coordinate conversion:standard_name = atmosphere_hybrid_height_coordinate
       Coordinate conversion:a = Domain Ancillary: ncvar%a
       Coordinate conversion:b = Domain Ancillary: ncvar%b
       Coordinate conversion:orog = Domain Ancillary: surface_altitude
       Datum:earth_radius = 6371007
       Dimension Coordinate: atmosphere_hybrid_height_coordinate
   
   Coordinate reference: rotated_latitude_longitude
       Coordinate conversion:grid_mapping_name = rotated_latitude_longitude
       Coordinate conversion:grid_north_pole_latitude = 38.0
       Coordinate conversion:grid_north_pole_longitude = 190.0
       Datum:earth_radius = 6371007
       Dimension Coordinate: grid_longitude
       Dimension Coordinate: grid_latitude
       Auxiliary Coordinate: longitude
       Auxiliary Coordinate: latitude
   
   Cell measure: measure%area
       units = 'km2'
       Data(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2

.. _properties:
       
Properties
----------

Properties of the field may be retrieved with the `~Field.properties`
method:

.. code:: python

   >>> t.properties()
   {'Conventions': 'CF-1.7',
    'project': 'research',
    'standard_name': 'air_temperature',
    'units': 'K'}
   
Individual properties may be accessed and modified with the
`~Field.del_property`, `~Field.get_property`, `~Field.has_property`,
and `~Field.set_property` methods:

.. code:: python

   >>> f.has_property('standard_name')
   True
   >>> f.get_property('standard_name')
   'air_temperature'
   >>> f.del_property('standard_name')
   'air_temperature'
   >>> f.get_property('standard_name', 'not set')
   'not set'
   >>> f.set_property('standard_name', 'air_temperature')
   >>> f.get_property('standard_name', 'not set')
   'air_temperature'

All properties may be completely replaced with another collection by
providing a new set of properties to the `~Field.properties` method:

.. code:: python
	  
   >>> original = t.properties({'foo': 'bar', 'units': 'K'})
   >>> original
   {'Conventions': 'CF-1.7',
    'project': 'research',
    'standard_name': 'air_temperature',
    'units': 'K'}
   >>> t.properties()
   {'foo': 'bar',
    'units': 'K'}
   >>> t.properties(original)
   {'foo': 'bar',
     'units': 'K'}
   >>> t.properties()
   {'Conventions': 'CF-1.7',
    'project': 'research',
    'standard_name': 'air_temperature',
    'units': 'K'}

.. _data:

Data
----

The field's data array is stored in a `Data` object that is accessed
with the `~Field.get_data` method:

.. code:: python

   >>> t.get_data()
   <Data(1, 10, 9): [[[262.8, ..., 269.7]]] K>

The data may be retrieved as an independent (possibly masked) `numpy`
array with the `~Field.get_array` method:

.. code:: python

   >>> print(t.get_array())
   [[[262.8 270.5 279.8 269.5 260.9 265.0 263.5 278.9 269.2]
     [272.7 268.4 279.5 278.9 263.8 263.3 274.2 265.7 279.5]
     [269.7 279.1 273.4 274.2 279.6 270.2 280.0 272.5 263.7]
     [261.7 260.6 270.8 260.3 265.6 279.4 276.9 267.6 260.6]
     [264.2 275.9 262.5 264.9 264.7 270.2 270.4 268.6 275.3]
     [263.9 263.8 272.1 263.7 272.2 264.2 260.0 263.5 270.2]
     [273.8 273.1 268.5 272.3 264.3 278.7 270.6 273.0 270.6]
     [267.9 273.5 279.8 260.3 261.2 275.3 271.2 260.8 268.9]
     [270.9 278.7 273.2 261.7 271.6 265.8 273.0 278.5 266.4]
     [276.4 264.2 276.3 266.1 276.1 268.1 277.0 273.4 269.7]]]
   
The field also has a `~Field.data` attribute that is an alias for the
`~Field.get_data` method, which makes it easier to access attributes
and methods of the `Data` object:

.. code:: python

   >>> t.data.dtype
   dtype('float64')
   >>> t.data.ndim
   3
   >>> t.data.shape
   (1, 10, 9)
   >>> t.data.size
   90

.. _indexing:

Indexing
^^^^^^^^

A `Data` object is indexed with rules that are very similar to the
`numpy indexing rules
<https://docs.scipy.org/doc/numpy/reference/arrays.indexing.html>`_,
the only differences being:

* **An integer index i takes the i-th element but does not reduce the
  rank by one.**

..

* **When two or more dimensions' indices are sequences of integers
  then these indices work independently along each dimension (similar
  to the way vector subscripts work in Fortran). This is the same
  behaviour as indexing on a** `Variable` **object of the** `netCDF4
  package <http://unidata.github.io/netcdf4-python>`_\ **.**

.. code:: python
	    
   >>> data = t.data
   >>> data.shape
   (1, 10, 9)
   >>> data[:, :, 1].shape
   (1, 10, 1)
   >>> data[:, 0].shape
   (1, 1, 9)
   >>> data[..., 6:3:-1, 3:6].shape
   (1, 3, 3)
   >>> data[0, [2, 9], [4, 8]].shape
   (1, 2, 2)
   >>> data[0, :, -2].shape
   (1, 10, 1)
  
.. _data_assignment:

Assignment
^^^^^^^^^^

Data array elements are changed by assigning to indices of the `Data`
object, using the :ref:`cfdm indexing rules <indexing>`.

The value being assigned must be broadcastable to the shape defined by
the indices, using the `numpy broadcasting rules
<https://docs.scipy.org/doc/numpy/user/basics.broadcasting.html>`_.

.. code:: python

   >>> import numpy
   >>> t.data[:, :, 1] = -10
   >>> t.data[:, 0] = range(9)
   >>> t.data[..., 6:3:-1, 3:6] = numpy.arange(-18, -9).reshape(3, 3)
   >>> t.data[0, [2, 9], [4, 8]] =  cfdm.Data([[-2, -3]])
   >>> t.data[0, :, -2] = numpy.ma.masked
   >>> print(t.get_array())
   [[[  0.0   1.0   2.0   3.0   4.0   5.0   6.0 --   8.0]
     [272.7 -10.0 279.5 278.9 263.8 263.3 274.2 -- 279.5]
     [269.7 -10.0 273.4 274.2  -2.0 270.2 280.0 --  -3.0]
     [261.7 -10.0 270.8 260.3 265.6 279.4 276.9 -- 260.6]
     [264.2 -10.0 262.5  -3.0  -2.0  -1.0 270.4 -- 275.3]
     [263.9 -10.0 272.1  -6.0  -5.0  -4.0 260.0 -- 270.2]
     [273.8 -10.0 268.5  -9.0  -8.0  -7.0 270.6 -- 270.6]
     [267.9 -10.0 279.8 260.3 261.2 275.3 271.2 -- 268.9]
     [270.9 -10.0 273.2 261.7 271.6 265.8 273.0 -- 266.4]
     [276.4 -10.0 276.3 266.1  -2.0 268.1 277.0 --  -3.0]]]

.. _subspacing:

Subspacing
----------

Creation of a new field that spans a subspace of the original domain
is achieved by indexing the field directly. The new subspace contains
the same properties and similar metadata constructs to the original
field, but the latter are also subspaced when they span domain axes
that have been changed. Subspacing uses the same :ref:`cfdm indexing
rules <indexing>` as apply to the `Data` object.

In this example a new field is created whose domain spans the first
latitude of the original, and with a reversed longitude axis:
     
.. code:: python

   >>> print(q)
   Field: specific_humidity (ncvar%q)
   ----------------------------------
   Data            : specific_humidity(latitude(5), longitude(8)) 1
   Cell methods    : area: mean
   Dimension coords: time(1) = [2019-01-01 00:00:00]
                   : latitude(5) = [-75.0, ..., 75.0] degrees_north
                   : longitude(8) = [22.5, ..., 337.5] degrees_east

   >>> new = q[0, ::-1]
   >>> print(new)
   Field: specific_humidity (ncvar%q)
   ----------------------------------
   Data            : specific_humidity(latitude(1), longitude(8)) 1
   Cell methods    : area: mean
   Dimension coords: time(1) = [2019-01-01 00:00:00]
                   : latitude(1) = [-75.0] degrees_north
                   : longitude(8) = [337.5, ..., 22.5] degrees_east
	
.. _write:
   
Writing to disk
---------------

The `cfdm.write` function writes a field, or sequence of fields, to a
netCDF file on disk:

.. code:: python

   >>> q
   <Field: specific_humidity(latitude(5), longitude(8)) 1>
   >>> cfdm.write(q, 'q_file.nc')
   >>> f
   [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
    <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>]
   >>> cfdm.write(f, 'new_file.nc')

The `cfdm.write` function has optional parameters to

* set the output netCDF format (all netCDF3 and netCDF4 formats are
  possible);

* specify which field construct properties should become netCDF data
  variable attributes and which should, if possible, become netCDF
  global attributes;
  
* create :ref:`external variables <external>` in an external file;

* change the data type of output data arrays;
  
* apply netCDF compression and packing; and

* set the endian-ness of the output data.

It is also possible to create netCDF unlimited dimensions and set the
HDF5 chunk size using the field's `nc_unlimited_dimensions` and
`nc_chunksize` methods.

.. _field_creation:

Field creation
--------------

Creation of a field construct has three stages:

**Stage 1:** The field construct is created without metadata constructs.

..
   
**Stage 2:** Metadata constructs are created independently.

..

**Stage 3:** The metatdata constructs are inserted into the field
constuct with and cross-references to other, related metadata
construct (for example, an auxiliary coordinate construct is related
to an ordered list of the domain axis constructs which correspond to
its data array dimensions).

There are two equivalent approaches to stages **1** and **2** Either
as much of the content as possible is specified during object
instantiation:

.. code:: python

   >>> x = cfdm.Field(properties={'standard_name': 'precipitation_flux'})
   >>> x
   <Field: precipitation_flux>
   >>> dc = cfdm.DimensionCoordinate(properties='long_name': 'Longitude'},
   ...                               data=cfdm.Data([0, 1, 2..]))
   >>> dc
   <DimensionCoordinate: long_name:Longitude(3) >
   >>> fa = cfdm.FieldAncillary(
   ...        properties={'standard_name': 'precipitation_flux status_flag'},
   ...        data=cfdm.Data(numpy.array([0, 0, 2], dtype='int8')))
   >>> fa
   <FieldAncillary: precipitation_flux status_flag(3) >

or else some or all content is added after instantiation via object
methods:

.. code:: python

   >>> x = cfdm.Field()
   >>> x
   <Field: >
   >>> x.set_property('standard_name', 'precipitation_flux')
   >>> x
   <Field: precipitation_flux>
   >>> dc = cfdm.DimensionCoordinate()
   >>> dc
   <DimensionCoordinate:  >
   >>> dc.set_property('long_name', 'Longitude')
   >>> dc.set_data(cfdm.Data([1, 2, 3.]))
   <DimensionCoordinate: long_name:Longitude(3) >
   >>> fa = cfdm.FieldAncillary(
   ...        data=cfdm.Data(numpy.array([0, 0, 2], dtype='int8')))
   >>> fa
   <FieldAncillary: (3) >
   >>> fa.set_property('standard_name', 'precipitation_flux status_flag')
   >>> fa
   <FieldAncillary: precipitation_flux status_flag(3) >

For stage **3**, the field class has the follow methods for setting
metadata constructs and mapping data array dimensions to domain axes
constructs:

=============================================  =====================================
Field method for setting a metadata construct  Description
=============================================  =====================================
`~Field.set_auxiliary_coordinate`              Set an auxiliary coordinate construct
`~Field.set_cell_measure`                      Set an cell measure construct
`~Field.set_cell_method`                       Set a cell method construct
`~Field.set_coordinate_reference`              Set a coordinate reference construct
`~Field.set_dimension_coordinate`              Set a dimension coordinate construct
`~Field.set_domain_ancillary`                  Set a domain ancillary
`~Field.set_domain_axis`                       Set a domain axis construct
`~Field.set_field_ancillary`                   Set a field ancillary construct
=============================================  =====================================

The following code creates a field construct with properties and data
and domain axis, cell method and dimension coordinate metadata
constructs (data arrays have been generated with dummy values using
`numpy.arange`).

.. code:: python

   import numpy
   import cfdm

   # Initialise the field with properties
   Q = cfdm.Field(properties={'project': 'research',
                              'standard_name': 'specific_humidity',
                              'units': '1'})
			      
   # Create the domain axes
   domain_axisT = cfdm.DomainAxis(1)
   domain_axisY = cfdm.DomainAxis(5)
   domain_axisX = cfdm.DomainAxis(8)

   # Insert the domain axes into the field. The set_domain_axis method
   # returns the domain axis construct identifier that will be used
   # later to specify which domain axis corresponds to which dimension
   # coordinate construct.  
   axisT = Q.set_domain_axis(domain_axisT)
   axisY = Q.set_domain_axis(domain_axisY)
   axisX = Q.set_domain_axis(domain_axisX)

   # Field data
   data = cfdm.Data(numpy.arange(40.).reshape(5, 8))
   Q.set_data(data, axes=[axisY, axisX])

   # Create the cell methods
   cell_method1 = cfdm.CellMethod(axes=['area'], properties={'method': 'mean'})

   cell_method2 = cfdm.CellMethod()
   cell_method2.set_axes([axisT])
   cell_method2.properties({'method': 'maximum'})

   # Insert the cell methods into the field
   Q.set_cell_method(cell_method1)
   Q.set_cell_method(cell_method2)

   # Create the dimension Coordinates
   dimT = cfdm.DimensionCoordinate(
            properties={'standard_name': 'time',
                        'units': 'days since 2018-12-01'},
            data=cfdm.Data([15.5]),
            bounds=cfdm.Bounds(data=cfdm.Data([[0,31.]])))
				   
   dimY = cfdm.DimensionCoordinate(properties={'standard_name': 'latitude',
		                               'units': 'degrees_north'})
   array = numpy.arange(5.)
   dimY.set_data(cfdm.Data(array))
   bounds_array = numpy.empty((5, 2))
   bounds_array[:, 0] = array - 0.5
   bounds_array[:, 1] = array + 0.5
   bounds = cfdm.Bounds(data=cfdm.Data(bounds_array))
   dimY.set_bounds(bounds)

   dimX = cfdm.DimensionCoordinate(data=cfdm.Data(numpy.arange(8.)))
   dimX.properties({'standard_name': 'longitude',
                    'units': 'degrees_east'})
  
   # Insert the dimension coordinates into the field, specifying to
   # which domain axis each one corresponds
   Q.set_dimension_coordinate(dimT, axes=[axisT])
   Q.set_dimension_coordinate(dimY, axes=[axisY])
   Q.set_dimension_coordinate(dimX, axes=[axisX])

The new field construct may now be inspected:
   
.. code:: python

   >>> Q.dump()
   ------------------------
   Field: specific_humidity
   ------------------------
   project = 'research'
   standard_name = 'specific_humidity'
   units = '1'
   
   Data(latitude(5), longitude(8)) = [[0.0, ..., 39.0]] 1
   
   Cell Method: area: mean
   Cell Method: time(1): maximum
   
   Domain Axis: latitude(5)
   Domain Axis: longitude(8)
   Domain Axis: time(1)
   
   Dimension coordinate: time
       standard_name = 'time'
       units = 'days since 2018-12-01'
       Data(time(1)) = [2018-12-16 12:00:00]
       Bounds:Data(time(1), 2) = [[2018-12-01 00:00:00, 2019-01-01 00:00:00]]
   
   Dimension coordinate: latitude
       standard_name = 'latitude'
       units = 'degrees_north'
       Data(latitude(5)) = [0.0, ..., 4.0] degrees_north
       Bounds:Data(latitude(5), 2) = [[-0.5, ..., 4.5]] degrees_north
   
   Dimension coordinate: longitude
       standard_name = 'longitude'
       units = 'degrees_east'
       Data(longitude(8)) = [0.0, ..., 7.0] degrees_east

It is not necessary to set the field "Conventions" property, because
this is automatically included in output files as a netCDF global
attribute corresponding to the version number (e.g. ``'1.7'``) of
:ref:`cfdm <class_extended>` being used.

If this field were to be written to a netCDF dataset then, in the
absence of pre-defined names, default netCDF variable and dimension
names would be automatically generated (based on standard names where
they exist). Setting bespoke names is, however, easily done with the
:ref:`netCDF interface <netcdf_interface>`:

.. code:: python

   Q.nc_set_variable('q')

   domain_axisT.nc_set_dimension('time')
   domain_axisY.nc_set_dimension('lat')
   domain_axisX.nc_set_dimension('lon')

   dimT.nc_set_variable('time')
   dimY.nc_set_variable('lat')
   dimX.nc_set_variable('lon')

Here is a complete example, that creates a field that contains every
type of metadata construct (again, data arrays have been generated
with dummy values using `numpy.arange`):

.. code:: python

   import numpy
   import cfdm

   # Initialize the field
   tas = cfdm.Field(
	   properties={'project': 'research',
	               'standard_name': 'air_temperature',
                       'units': 'K'})

   # Create and set domain axes
   axis_T = tas.set_domain_axis(cfdm.DomainAxis(1))
   axis_Z = tas.set_domain_axis(cfdm.DomainAxis(1))
   axis_Y = tas.set_domain_axis(cfdm.DomainAxis(10))
   axis_X = tas.set_domain_axis(cfdm.DomainAxis(9))

   # Set the field data
   tas.set_data(cfdm.Data(numpy.arange(90.).reshape(10, 9),
                axes=[axis_Y, axis_X]))

   # Create and set the cell methods
   cell_method1 = cfdm.CellMethod(
             axes=[axis_Y, axis_X],
             properties={'method': 'mean',
                         'where': 'land',
	      		 'intervals': [cfdm.Data(0.1, units='degrees')]})
				
   cell_method2 = cfdm.CellMethod(
                    axes=[axis_T],
	            properties={'method': 'maximum'})
   
   tas.set_cell_method(cell_method1)
   tas.set_cell_method(cell_method1)

   # Create and set the field ancillaries
   field_ancillary = cfdm.FieldAncillary(
                properties={'standard_name': 'air_temperature standard_error',
                             'units': 'K'},
                data=cfdm.Data(numpy.arange(90.).reshape(10, 9)))

   tas.set_field_ancillary(field_ancillary, axes=[axis_Y, axis_X])
		
   # Create and set the dimension coordinates
   dimension_coordinate_T = cfdm.DimensionCoordinate(
                     	      properties={'standard_name': 'time',
                                          'units': 'days since 2018-12-01'},
	                      data=cfdm.Data([15.5]),
	                      bounds=cfdm.Bounds(cfdm.Data([0, 31])))

   dimension_coordinate_Z = cfdm.DimensionCoordinate(
	   properties={'computed_standard_name': 'altitude',
                       'standard_name': 'atmosphere_hybrid_height_coordinate'},
           data = cfdm.Data([1.5]),
           bounds=cfdm.Bounds(cfdm.Data([[1.0, 2.0]])))
       
   dimension_coordinate_Y = cfdm.DimensionCoordinate(
	        properties={'standard_name': 'grid_latitude',
		            'units': 'degrees'},
	        data=cfdm.Data(numpy.arange(10.)),
	        bounds=cfdm.Bounds(cfdm.Data(numpy.arange(20).reshape(10, 2))))

   dimension_coordinate_X = cfdm.DimensionCoordinate(
                properties={'standard_name': 'grid_longitude',
                            'units': 'degrees'},
	        data=cfdm.Data(numpy.arange(9.)),
	        bounds=cfdm.Bounds(cfdm.Data(numpy.arange(18).reshape(9, 2))))

   tas.set_dimension_coordinate(dimension_coordinate_T, axes=[axis_T])
   tas.set_dimension_coordinate(dimension_coordinate_Z, axes=[axis_Z])
   tas.set_dimension_coordinate(dimension_coordinate_Y, axes=[axis_Y])
   tas.set_dimension_coordinate(dimension_coordinate_X, axes=[axis_X])
      
   # Create and set the auxiliary coordinates
   auxiliary_coordinate_lat = cfdm.AuxiliaryCoordinate(
                         properties={'standard_name': 'latitude',
                                     'units': 'degrees_north'},
                         data=cfdm.Data(numpy.arange(90.).reshape(10, 9)))

   auxiliary_coordinate_lon = cfdm.AuxiliaryCoordinate(
                         properties={'standard_name': 'longitude',
   		                     'units': 'degrees_east'},
	                 data=cfdm.Data(numpy.arange(90.).reshape(9, 10)))

   array = numpy.ma.array(list('abcdefghij')
   array[0] = numpy.ma.masked
   auxiliary_coordinate_name = cfdm.AuxiliaryCoordinate(
                          properties={'long_name': 'Grid latitude name'},
                          data=cfdm.Data(array))

   tas.set_auxiliary_coordinate(dimension_coordinate_lat,
	                        axes=[axis_Y, axis_X])
   tas.set_auxiliary_coordinate(dimension_coordinate_lon,
	                        axes=[axis_X, axis_Y])
   tas.set_auxiliary_coordinate(dimension_coordinate_name, axes=[axis_Y])

   # Create and set domain ancillaries
   domain_ancaillary_a = cfdm.DomainAncillary(
 	                   properties={'units': 'm'},
	                   data=cfdm.Data([10.]),
                           bounds=cfdm.Bounds(cfdm.Data([[[5.0, 15.0]]))))

   domain_ancaillary_b = cfdm.DomainAncillary(
	                   properties={'units': '1'},
      	                   data=cfdm.Data([20.]),
	                   bounds=cfdm.Bounds(cfdm.Data([[[14, 26.]]))))

   domain_ancaillary_orog = cfdm.DomainAncillary(
                      	      properties={'standard_name': 'surface_altitude',
                                          'units': 'm'},
	                      data=cfdm.Data(numpy.arange(90.).reshape(10, 9)))

   tas.set_domain_ancillary(domain_ancillary_a, axes=[axis_Z])
   tas.set_domain_ancillary(domain_ancillary_b, axes=[axis_Z])
   tas.set_domain_ancillary(domain_ancillary_orog, axes=[axis_Y, axis_X])

   # Create and set the coordinate references
   datum = cfdm.Datum(parameters={'earth_radius': 6371007.})

   horizontal_crs = cfdm.CoordinateReference(datum=datum,
    	              coordinate_conversion=coordinate_conversion,
	              coordinates=[dimension_coordinate_X,
                                   dimension_coordinate_Y,
                                   auxiliary_coordinate_lat,
				   auxiliary_coordinate_lon])

   coordinate_conversion = cfdm.CoordinateConversion(
            parameters={'standard_name', 'atmosphere_hybrid_height_coordinate',
                        'computed_standard_name': 'altitude'},
            domain_ancillaries={'a': domain_ancillary_a,
                                'b': domain_ancillary_a,
                            	'orog': domain_ancillary_orog})

    vertical_crs = cfdm.CoordinateReference(datum=datum,
       	             coordinate_conversion=coordinate_conversion,
         	     coordinates=[dimension_coordinate_Z])


   tas.set_coordinate_reference(horizontal_crs)
   tas.set_coordinate_reference(vertical_crs)

   # Create and set the cell measures
   cell_meausure = cfdm.CellMeasure(measure='area',
            	     properties={'units': 'km2'},
                     data=cfdm.Data(numpy.arange(90.).reshape(9, 10)))

   tas.set_cell_measure(cel_meausre, axes=[axis_Y, axis_X])
   
.. _constructs:

Metadata constructs
-------------------

Metadata constructs of the field are all of the constructs that serve
to describe the field construct that contains them. Each metadata
construct of the CF data model has a corresponding :ref:`cfdm
<class_extended>` class:

=======================  ==============================  =====================  
CF data model construct  Description                     cfdm class             
=======================  ==============================  =====================  
Domain axis              Independent axes of the domain  `DomainAxis`           
Dimension coordinate     Domain cell locations           `DimensionCoordinate`  
Auxiliary coordinate     Domain cell locations           `AuxiliaryCoordinate`  
Coordinate reference     Domain coordinate systems       `CoordinateReference`  
Domain ancillary         Cell locations in alternative   `DomainAncillary`      
                         coordinate systems		                       
Cell measure             Domain cell size or shape       `CellMeasure`          
Field ancillary          Ancillary metadata which vary   `FieldAncillary`       
                         within the domain		                       
Cell method              Describes how data represent    `CellMethod`           
                         variation within cells		                       
=======================  ==============================  =====================  

The metadata constructs of the field are returned by the
`~Field.constructs` method that provides a dictionary of the metadata
constructs, each of which is keyed by a unique identifier called a
"construct identifier".

.. code:: python

   >>> q.constructs()
   {'cellmethod0': <CellMethod: area: mean>,
    'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>,
    'dimensioncoordinate1': <DimensionCoordinate: longitude(8) degrees_east>,
    'dimensioncoordinate2': <DimensionCoordinate: time(1) days since 2018-12-01 >,
    'domainaxis0': <DomainAxis: 5>,
    'domainaxis1': <DomainAxis: 8>,
    'domainaxis2': <DomainAxis: 1>}
   >>> t.constructs()
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
    'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
    'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >,
    'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>,
    'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
    'cellmethod1': <CellMethod: domainaxis3: maximum>,
    'coordinatereference0': <CoordinateReference: atmosphere_hybrid_height_coordinate>,
    'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>,
    'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
    'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >,
    'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
    'domainancillary1': <DomainAncillary: ncvar%b(1) >,
    'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>,
    'domainaxis0': <DomainAxis: 1>,
    'domainaxis1': <DomainAxis: 10>,
    'domainaxis2': <DomainAxis: 9>,
    'domainaxis3': <DomainAxis: 1>,
    'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}

The construct identifiers are usually generated internally by the
field object and are

* *robust* (each metadata construct within a field is guaranteed to
  have a unique identifier),

* *arbitrary* (no semantic meaning should be attached to the
  identifier and the same identifier will usually refer to different
  metadata constructs in different fields), and

* *unstable* (the identifiers could be different each time the field
  is created).

The `~Field.constructs` method has optional parameters to filter the
metadata constructs by

* construct type,

* property value,

* other attribute value (such as netCDF variable name),
  
* whether or the data array spans particular domain axes, and

* construct identifier.  

.. code:: python
	  
   >>> t.constructs('air_temperature standard_error')
   {'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}
   >>> t.constructs(construct_type='dimension_coordinate')
   {'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
    'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}
   >>> t.constructs(axes=['domainaxis1'])
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
    'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
    'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >,
    'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>,
    'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}
   >>> t.constructs(axes=['domainaxis3'])
   {'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}
   >>> t.constructs(construct_type='dimension_coordinate', axes=['domainaxis1'])
   {'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>}
   >>> t.constructs('ncvar%b')
   {'domainancillary1': <DomainAncillary: ncvar%b(1) >}
   >>> t.constructs('wavelength')
   {}
   
Selection by construct identifier is useful for systematic construct
access, and for when a construct is not identifiable by other means.

.. code:: python

   >>> t.constructs(cid='domainancillary2')
   {'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>}
   >>> t.constructs('cid%cellmethod1')
   {'cellmethod1': <CellMethod: domainaxis3: maximum>}
   >>> t.constructs(cid='auxiliarycoordinate999')
   {}

Selection is also possible via the :ref:`netCDF interface
<netcdf_interface>`:

.. code:: python

   >>> t.constructs('ncvar%lon')
   {'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>}
   
An individual metadata construct may be returned without its construct
identifier via the field's `~Field.get_construct` method, which
supports the same filtering options as above:

.. code:: python

   >>> t.get_construct('latitude')
   <AuxiliaryCoordinate: latitude(10, 9) degrees_N>
   >>> t.get_construct('units:km2')
   <CellMeasure: measure%area(9, 10) km2>
   >>> t.constructs('units:degrees')
   {'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>}
   >>> t.get_construct('units:degrees')
   ValueError: More than one construct meets criteria

Domain axes
^^^^^^^^^^^

The domain axes spanned by a metadata construct's data are found with
the field's `~Field.construct_axes` method:

.. code:: python

   >>> t.construct_axes()
   {'auxiliarycoordinate0': ('domainaxis1', 'domainaxis2'),
    'auxiliarycoordinate1': ('domainaxis2', 'domainaxis1'),
    'auxiliarycoordinate2': ('domainaxis1',),
    'cellmeasure0': ('domainaxis2', 'domainaxis1'),
    'dimensioncoordinate0': ('domainaxis0',),
    'dimensioncoordinate1': ('domainaxis1',),
    'dimensioncoordinate2': ('domainaxis2',),
    'dimensioncoordinate3': ('domainaxis3',),
    'domainancillary0': ('domainaxis0',),
    'domainancillary1': ('domainaxis0',),
    'domainancillary2': ('domainaxis1', 'domainaxis2'),
    'fieldancillary0': ('domainaxis1', 'domainaxis2')}

The domain axes spanned by a metadata construct's data are usually set
during :ref:`field creation <field_creation>`, but may be changed at
any time with field's `~Field.set_construct_axes` method.


Properties and data
^^^^^^^^^^^^^^^^^^^

Where applicable, the classes for metadata constructs share the same
API as the field. This means, for instance, that a class that has a
data array (such as `AuxiliaryCoordinate`) will have a `!get_array`
method to access its data as a numpy array:

.. code:: python

   >>> lon = q.get_construct('longitude')   
   >>> lon
   <DimensionCoordinate: longitude(8) degrees_east>
   >>> lon.set_property('long_name', 'Longitude')
   >>> lon.properties()
   {'units': 'degrees_east',
    'long_name': 'Longitude',
    'standard_name': 'longitude'}   
   >>> lon.data[2]
   <Data(1): [112.5] degrees_east>
   >>> lon.data[2] = 133.33
   >>> print(lon.get_array())
   [22.5 67.5 133.33 157.5 202.5 247.5 292.5 337.5]

Components
^^^^^^^^^^

Other classes are required to represent construct components that are
neither "properties" nor "data":

======================  ==============================  ======================
cfdm class              Description                     cfdm parent classes
======================  ==============================  ======================
`Bounds`                Cell bounds.                    `DimensionCoordinate`,
                                                        `AuxiliaryCoordinate`,
                                                        `DomainAncillary`

`CoordinateConversion`  A formula for                   `CoordinateReference`
		        converting coordinate values
		        taken from the dimension or
		        auxiliary coordinate
			constructs
		        to a different coordinate
			system.

`Datum`                 The zeroes                      `CoordinateReference`
                        of the dimension
                        and auxiliary coordinate
			constructs which define a
			coordinate system.
======================  ==============================  ======================

Where applicable, these classes also share the same API as the field:

.. code:: python
	  
   >>> lon = t.get_construct('grid_longitude')
   >>> bounds = lon.get_bounds()
   >>> bounds
   <Bounds: ncvar%grid_longitude_bounds(9, 2) >
   >>> bounds.properties()
   {}
   >>> bounds.get_data()
   <Data(9, 2): [[-4.92, ..., -0.96]]>
   >>> print(bounds.get_array())
   [[-4.92 -4.48]
    [-4.48 -4.04]
    [-4.04 -3.6 ]
    [-3.6  -3.16]
    [-3.16 -2.72]
    [-2.72 -2.28]
    [-2.28 -1.84]
    [-1.84 -1.4 ]
    [-1.4  -0.96]]
   >>> crs = t.get_construct('rotated_latitude_longitude')
   >>> crs.datum
   <Datum: Parameters: earth_radius>
   >>> crs.datum.parameters()
   {'earth_radius': 6371007}
   >>> crs = t.get_construct('atmosphere_hybrid_height_coordinate',
   ...                       construct_type='coordinate_reference')
   >>> crs.coordinate_conversion.domain_ancillaries()
   {'a': 'domainancillary0',
    'b': 'domainancillary1',
    'orog': 'domainancillary2'}

.. _domain:    

Domain
------

The `Domain` class represents the (abstract) domain of the CF data
model, that describes the locations of the field construct's data. The
domain object may be accessed with the field's `~Field.get_domain`
method:

.. code:: python

   >>> domain = t.get_domain()
   >>> domain
   <Domain: {1, 1, 9, 10}>
   >>> print(domain)
   Dimension coords: atmosphere_hybrid_height_coordinate(1) = [1.5]
                   : grid_latitude(10) = [2.2, ..., -1.76] degrees
                   : grid_longitude(9) = [-4.7, ..., -1.18] degrees
                   : time(1) = [2019-01-01 00:00:00]
   Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[53.941, ..., 50.225]] degrees_N
                   : longitude(grid_longitude(9), grid_latitude(10)) = [[2.004, ..., 8.156]] degrees_E
                   : long_name:Grid latitude name(grid_latitude(10)) = [--, ..., kappa]
   Cell measures   : measure%area(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2
   Coord references: atmosphere_hybrid_height_coordinate
                   : rotated_latitude_longitude
   Domain ancils   : ncvar%a(atmosphere_hybrid_height_coordinate(1)) = [10.0] m
                   : ncvar%b(atmosphere_hybrid_height_coordinate(1)) = [20.0]
                   : surface_altitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 270.0]] m
   >>> description = domain.dump(display=False)

Changes to domain object are seen by the parent field, and vice
versa. (This is because the domain is essentially a "view" of the
relevant metadata constructs contained in the field construct.) The
field also has a `~Field.domain` attribute that is an alias for the
`~Field.get_domain` method, which makes it easier to access attributes
and methods of the domain object:

.. code:: python

   >>> t.domain.get_construct('latitude').set_property('test', 'set by domain')
   >>> t.get_construct('latitude').get_property('test')
   'set by domain'
   >>> t.get_construct('latitude').set_property('test', 'set by field')
   >>> t.domain.get_construct('latitude').get_property('test')
   'set by field'
   >>> t.domain.get_construct('latitude').del_property('test')
   'set by field'
   >>> t.get_construct('latitude').has_property('test')
   False

.. _copying:

Copying
-------

A field may be copied with its `~Field.copy` method. This produces a
deep copy, i.e. the new field is completely independent of the original field.

.. code:: python

   >>> u = t.copy()
   >>> u.del_construct('grid_latitude')
   <DimensionCoordinate: grid_latitude(10) degrees>
   >>> t.has_construct('grid_latitude')
   True

Equivalently, the `copy.deepcopy` function may be used:

   >>> import copy
   >>> u = copy.deepcopy(t)

Metadata constructs may be individually copied in the same manner:

.. code:: python

   >>> orog = f.get_construct('surface_altitude').copy()

*Note on performance*
  Data objects within the field are copied with a `copy-on-write
  <https://en.wikipedia.org/wiki/Copy-on-write>`_ technique. This
  means that a copy of a field takes up very little extra memory, even
  when the original field contains very large data arrays, and the
  copy operation is fast---at the time of copying, it is essentially
  only the descriptive properties that are duplicated.

.. _equality:

Equality
--------

Whether or not two fields are the equal is tested with the field's
`~cfdm.Field.equals` method.

.. code:: python

   >>> t.equals(t)
   True
   >>> t.equals(t.copy())
   True
   >>> t.equals(q)
   False
   >>> t.equals(q, traceback=True)
   Field: Different units: 'K', '1'
   Field: Different properties
   False

Equality is strict by default. This means that for two fields to be
considered equal they must have corresponding metadata constructs and
for each pair of constructs:

* The properties must be the same (with the exception of the field
  construct's "Conventions" property, which is never checked), and 

* if there are data arrays then they must have same shape, data type
  and be element-wise equal.

Two numerical data elements :math:`a` and :math:`b` are considered
equal if :math:`|a - b| \le atol + rtol|b|`, where :math:`atol` (the
tolerance on absolute differences) and :math:`rtol` (the tolerance on
relative differences) are positive, typically very small numbers. By
default both are set to the system epsilon (the difference between 1
and the least value greater than 1 that is representable as a
float). Their default settings may be inspected and changed with the
`cfdm.ATOL` and `cfdm.RTOL` functions:

.. code:: python

   >>> cfdm.ATOL()
   2.220446049250313e-16
   >>> cfdm.RTOL()
   2.220446049250313e-16
   >>> original = cfdm.RTOL(0.00001)
   >>> cfdm.RTOL()
   1e-05
   >>> cfdm.RTOL(original)
   1e-05
   >>> cfdm.RTOL()
   2.220446049250313e-16
   
NetCDF elements, such as netCDF variable and dimension names, do not
constitute part of the CF data model and so are not checked on any
construct.

The `~Field.equals` function has optional parameters for relaxing the
criteria for considering two fields to be equal:

* named properties may be omitted from the comparison,

* the missing data value may be ignored,

* the data type of arrays may be ignored (i.e. arrays with different
  data types but equal elements will be accepted as being the same),
  and

* the tolerances on absolute and relative differences for numerical
  comparisons may be temporarily changed, without changing the default
  settings.

.. _netcdf_interface:

NeCDF interface
---------------

The logical CF data model is independent of netCDF, but the CF
conventions are designed to enable the processing and sharing of
datasets stored in netCDF files. Therefore, the :ref:`cfdm
<class_extended>` package includes methods for recording and editing
netCDF elements that are not part of the CF model, but are nonetheless
often required to interpret and create CF-netCDF datasets. See the
section on :ref:`philosophy <philosophy>` for a further discussion.

When a netCDF dataset is read, netCDF elements (such as dimension and
variable names, and some attribute values) that do not have a place in
the CF data model are stored within the relevant :ref:`cfdm
<class_extended>` objects. This allows them to be used when writing
fields to a new netCDF dataset, and also makes them accessible for
construct identification.

Each :ref:`cfdm <class_extended>` class has methods to access the
netCDF elements which it requires. For example, the `Field` class has
the following methods:

================================  ====================================
Field method                      Description
================================  ====================================
`~Field.nc_get_variable`          Return the netCDF variable name
`~Field.nc_set_variable`          Set the netCDF variable name
`~Field.nc_del_variable`          Remove the netCDF variable name

`~Field.nc_has_variable`          Whether the netCDF variable name has
                                  been set

`~Field.nc_global_attributes`     Return or replace the selection of
                                  properties to be written as netCDF
                                  global attributes

`~Field.nc_unlimited_dimensions`  Return or replace the selection of
                                  domain axis constructs to be written
                                  as netCDF unlimited dimensions
================================  ====================================

For example:

.. code:: python

   >>> q.nc_get_variable()
   'q'
   >>> q.nc_global_attributes()
   {'project', 'Conventions'}
   >>> q.nc_unlimited_dimensions()
   set()
   >>> q.nc_set_variable('humidity')
   >>> q.nc_get_variable()
   'humidity'

The complete collection of netCDF interface methods is:

============================  =======================================  =====================================
Method                        Classes                                  NetCDF element
============================  =======================================  =====================================
`!nc_del_variable`            `Field`, `DimensionCoordinate`,          Variable name
                              `AuxiliaryCoordinate`, `CellMeasure`,
                              `DomainAncillary`, `FieldAncillary`,
                              `CoordinateReference`,  `Bounds`,
			      `Count`, `Index`, `List`
			      				
`!nc_get_variable`            `Field`, `DimensionCoordinate`,          Variable name
                              `AuxiliaryCoordinate`, `CellMeasure`,
                              `DomainAncillary`, `FieldAncillary`,
                              `CoordinateReference`, `Bounds`,
			      `Count`, `Index`, `List`
			      
`!nc_has_variable`            `Field`, `DimensionCoordinate`,          Variable name
                              `AuxiliaryCoordinate`, `CellMeasure`,
                              `DomainAncillary`, `FieldAncillary`,
                              `CoordinateReference`, `Bounds`,
			      `Count`, `Index`, `List`
			      
`!nc_set_variable`            `Field`, `DimensionCoordinate`,          Variable name
                              `AuxiliaryCoordinate`, `CellMeasure`,
                              `DomainAncillary`, `FieldAncillary`,
                              `CoordinateReference`, `Bounds`,
			      `Count`, `Index`, `List`

`!nc_del_dimension`           `DomainAxis`                             Dimension name
			      
`!nc_get_dimension`	      `DomainAxis`                             Dimension name
			      			                    
`!nc_has_dimension`	      `DomainAxis`                             Dimension name
			      			                    
`!nc_set_dimension`	      `DomainAxis`                             Dimension name
			      
`!nc_global_attributes`	      `Field`                                  Global attributes

`!nc_unlimited_dimensions`    `Field`                                  Unlimited dimensions

`!nc_external`                `CellMeasure`                            External variable status

`!nc_del_instance_dimension`  `Index`                                  Instance dimension of a ragged array

`!nc_get_instance_dimension`  `Index`                                  Instance dimension of a ragged array

`!nc_has_instance_dimension`  `Index`                                  Instance dimension of a ragged array

`!nc_set_instance_dimension`  `Index`                                  Instance dimension of a ragged array
  
`!nc_del_sample_dimension`    `Count`, `Index`                         Sample dimension of a ragged array

`!nc_get_sample_dimension`    `Count`, `Index`                         Sample dimension of a ragged array
    
`!nc_has_sample_dimension`    `Count`, `Index`                         Sample dimension of a ragged array   

`!nc_set_sample_dimension`    `Count`, `Index`                         Sample  dimension of a ragged array
============================  =======================================  =====================================

..        `!get_count_variable`         `Data`                                   Count variable of a ragged array     `!get_index_variable`         `Data`                                   Index variable of a ragged array    `!get_list_variable`          `Data`                                   List variable of a gathered array 

For example:

.. code:: python

   >>> lon = q.get_construct('ncvar%lon')
   >>> lon
   <DimensionCoordinate: longitude(8) degrees_east>
   >>> lon.nc_get_variable()
   'lon'
   >>> axis = g.get_construct('ncdim%time')
   <DomainAxis: 1>
   >>> axis.nc_get_dimension()
   'time'


   
.. _external:

External variables
------------------

External variables are those referred to in the dataset, but which are
not present in it. Instead, such variables are stored in other files
known as "external files". External variables may, however, be
incorporated into the field constructs of the dataset, as if they had
actually been stored in the same file, simply by providing the
external file names to the `cfdm.read` function.

This is illustrated with the files **parent.nc** (:download:`download
<../netcdf_files/parent.nc>`, 2kB) and **external.nc**
(:download:`download <../netcdf_files/external.nc>`, 1kB) [#files]_:

.. code:: bash
   
   $ ncdump -h parent.nc
   netcdf parent {
   dimensions:
   	latitude = 10 ;
   	longitude = 9 ;
   variables:
   	double latitude(latitude) ;
   		latitude:units = "degrees_north" ;
   		latitude:standard_name = "latitude" ;
   	double longitude(longitude) ;
   		longitude:units = "degrees_east" ;
   		longitude:standard_name = "longitude" ;
   	double eastward_wind(latitude, longitude) ;
   		eastward_wind:units = "m s-1" ;
   		eastward_wind:standard_name = "eastward_wind" ;
   		eastward_wind:cell_measures = "area: areacella" ;
   
   // global attributes:
   		:Conventions = "CF-1.7" ;
   		:external_variables = "areacella" ;
   }

   $ ncdump -h external.nc 
   netcdf external {
   dimensions:
   	latitude = 10 ;
   	longitude = 9 ;
   variables:
   	double areacella(longitude, latitude) ;
   		areacella:units = "m2" ;
   		areacella:standard_name = "cell_area" ;
   
   // global attributes:
   		:Conventions = "CF-1.7" ;
   }

The dataset in **parent.nc** may be read without specifying the
external file **external.nc**. In this case a cell measure construct
is still created, but one without any metadata or data:

.. code:: python

   >>> f = cfdm.read('parent.nc')[0]
   >>> print(f)
   Field: eastward_wind (ncvar%eastward_wind)
   ------------------------------------------
   Data            : eastward_wind(latitude(10), longitude(9)) m s-1
   Dimension coords: latitude(10) = [0.0, ..., 9.0] degrees
                   : longitude(9) = [0.0, ..., 8.0] degrees
   Cell measures   : measure%area (external variable: ncvar%areacella)

   >>> cm = f.get_construct('measure%area')
   >>> cm
   <CellMeasure: measure%area >
   >>> cm.nc_external()
   True
   >>> cm.nc_get_variable()
   'areacella'
   >>> cm.properties()
   {}
   >>> cm.has_data()
   False

If this field were to be written to disk using `cfdm.write`, then the
output file would be identical to the original **parent.nc** file,
i.e. the netCDF variable name of the cell measure construct
("areacella") would be listed by the "external_variables" global
attribute.

However, the dataset may also be read with the external file. In this
case a cell measure construct is created with all of the metadata and
data from the external file, as if the cell measure variable had been
present in the parent dataset:

.. code:: python
   
   >>> g = cfdm.read('parent.nc', external_files='external.nc')[0]
   >>> print(g)
   Field: eastward_wind (ncvar%eastward_wind)
   ------------------------------------------
   Data            : eastward_wind(latitude(10), longitude(9)) m s-1
   Dimension coords: latitude(10) = [0.0, ..., 9.0] degrees
                   : longitude(9) = [0.0, ..., 8.0] degrees
   Cell measures   : cell_area(longitude(9), latitude(10)) = [[100000.5, ..., 100089.5]] m2
   >>> area = g.get_construct('cell_area')
   >>> area
   <CellMeasure: cell_area(9, 10) m2>
   >>> area.nc_external()
   False
   >>> area.nc_get_variable()
   'areacella'
   >>> area.properties()
   {'standard_name': 'cell_area', 'units': 'm2'}
   >>> area.get_data()
   <Data(9, 10): [[100000.5, ..., 100089.5]] m2>
   
If this field were to be written to disk using `cfdm.write` then by
default the cell measure construct, with all of its metadata and data,
would be written to the named output file, along with all of the other
constructs. There would be no "external_variables" global attribute.

In order to write a metadata construct to an external file, and refer
to it with the "external_variables" global attribute in the parent
output file, simply set the status of the construct to "external" and
provide an external file name to the `cfdm.write` function:

.. code:: python

   >>> area.nc_external(True)
   False
   >>> cfdm.write(g, 'new_parent.nc', external_file='new_external.nc')
   
Discrete sampling geometries
----------------------------

The CF data model views arrays that are compressed by removing
unwanted missing data in their uncompressed form. So, when a
collection of `discrete sampling geometry (DSG)
<http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#discrete-sampling-geometries>`_
features has been combined using a compressed ragged representation to
save space, the field construct contains the domain axis constructs
that have been compressed and presents a view of the data in its
uncompressed form, i.e. in `incomplete multidimensional form
<http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#_incomplete_multidimensional_array_representation>`_,
even though the underlying arrays may remain in their compressed
representation.

Accessing the data by a call to the `!get_array` method returns a
numpy array that is uncompressed. The underlying array will, however,
remain in its compressed form. The underlying compressed array may be
retrieved as a numpy array with the `get_compressed_array` method of
the `Data` object.

A subspace created by indexing (based on the axes of the uncompressed
form of the data) will no longer be compressed, i.e. its underlying
array will be in incomplete multidimensional representation. The
original data will, however, retain its underlying compressed form.

If the data elements are modified by indexed assignment then the
underlying compressed array is replaced by its uncompressed form.

A count variable that is required to uncompress a contiguous, or
indexed contiguous, ragged array is stored in a `Count` object and is
retrieved with the `get_count_variable` method of the `Data` object.

An index variable that is required to uncompress an indexed, or indexed
contiguous, ragged array is stored in an `Index` object and is
retrieved with the `get_index_variable` method of the `Data` object.

This is illustrated with the file **contiguous.nc**
(:download:`download <../netcdf_files/contiguous.nc>`, 2kB) [#files]_:

.. code:: bash
   
   $ ncdump -h contiguous.nc
   dimensions:
   	station = 4 ;
   	obs = 24 ;
   	strlen8 = 8 ;
   variables:
   	int row_size(station) ;
   		row_size:long_name = "number of observations for this station" ;
   		row_size:sample_dimension = "obs" ;
   	double time(obs) ;
   		time:units = "days since 1970-01-01 00:00:00" ;
   		time:standard_name = "time" ;
   	double lat(station) ;
   		lat:units = "degrees_north" ;
   		lat:standard_name = "latitude" ;
   	double lon(station) ;
   		lon:units = "degrees_east" ;
   		lon:standard_name = "longitude" ;
   	double alt(station) ;
   		alt:units = "m" ;
   		alt:positive = "up" ;
   		alt:standard_name = "height" ;
   		alt:axis = "Z" ;
   	char station_name(station, strlen8) ;
   		station_name:long_name = "station name" ;
   		station_name:cf_role = "timeseries_id" ;
   	double humidity(obs) ;
   		humidity:standard_name = "specific_humidity" ;
   		humidity:coordinates = "time lat lon alt station_name" ;
   		humidity:_FillValue = -999.9 ;
   
   // global attributes:
   		:Conventions = "CF-1.7" ;
   		:featureType = "timeSeries" ;
   }

Reading and inspecting this file shows the data presented in
two-dimensional uncompressed form, whilst the underlying array is
still in the one-dimension ragged representation described in the
file:

.. code:: python
   
   >>> h = cfdm.read('contiguous.nc')[0]
   >>> print(h)
   Field: specific_humidity (ncvar%humidity)
   -----------------------------------------
   Data            : specific_humidity(ncdim%station(4), ncdim%timeseries(9))
   Dimension coords: 
   Auxiliary coords: time(ncdim%station(4), ncdim%timeseries(9)) = [[1969-12-29 00:00:00, ..., 1970-01-07 00:00:00]]
                   : latitude(ncdim%station(4)) = [-9.0, ..., 78.0] degrees_north
                   : longitude(ncdim%station(4)) = [-23.0, ..., 178.0] degrees_east
                   : height(ncdim%station(4)) = [0.5, ..., 345.0] m
                   : cf_role:timeseries_id(ncdim%station(4)) = [station1, ..., station4]
   >>> h.data.get_compression_type()
   'ragged contiguous'
   >>> print(h.get_array())
   [[0.12 0.05 0.18   --   --   --   --   --   --]
    [0.05 0.11 0.2  0.15 0.08 0.04 0.06   --   --]
    [0.15 0.19 0.15 0.17 0.07   --   --   --   --]
    [0.11 0.03 0.14 0.16 0.02 0.09 0.1  0.04 0.11]]
   >>> print(h.data.get_compressed_array())
   [0.12 0.05 0.18 0.05 0.11 0.2 0.15 0.08 0.04 0.06 0.15 0.19 0.15 0.17 0.07
    0.11 0.03 0.14 0.16 0.02 0.09 0.1 0.04 0.11]
   >>> count_variable = h.data.get_count_variable()
   >>> count_variable
   <Count: long_name:number of observations for this station(4) >
   >>> print(count_variable.get_array())
   [3 7 5 9]

We can easily select the timeseries for the second station by indexing
the "station" axis of the field construct:

.. code:: python
	  
   >>> station = h[1]
   >>> station
   <Field: specific_humidity(ncdim%station(1), ncdim%timeseries(9))>
   >>> print(station.get_array())
   [[0.05 0.11 0.2 0.15 0.08 0.04 0.06 -- --]]

The underlying array of original data remains in compressed form until
data array elements are modified:
   
   >>> h.data.get_compression_type()
   'ragged contiguous'
   >>> h.data[1, 2] = -9
   >>> print(h.get_array())
   [[0.12 0.05 0.18   --   --   --   --   --   --]
    [0.05 0.11 -9.0 0.15 0.08 0.04 0.06   --   --]
    [0.15 0.19 0.15 0.17 0.07   --   --   --   --]
    [0.11 0.03 0.14 0.16 0.02 0.09 0.1  0.04 0.11]]
   >>> h.data.get_compression_type()
   ''

   
If the underlying array is compressed at the time of writing to disk
with the `cfdm.write` function, then it is written to the file as a
ragged array, along with the required count or index variables
required to uncompress it. This means that if a dataset using
compression is read from disk then it will be written back to disk
with the same compression, provided that no data elements have been
modified by assignment. Any compressed arrays that have been modified
will be written to an output dataset as incomplete multidimensional
arrays.

A construct with an underlying compressed array is created by
initialising the `Data` object with a compressed array that is stored
in one of three special array objects: `RaggedContiguousArray`,
`RaggedIndexedArray` or `RaggedIndexedContiguousArray`. The following
code creates a simple field construct with an underlying contiguous
ragged array:

.. code:: python

   import numpy
   import cfdm
   
   # Define the ragged array values
   ragged_array = numpy.array([280, 282.5, 281, 279, 278, 279.5],
                              dtype='float32')

   # Define the count array values
   count_array = [2, 4]

   # Create the count variable
   count_variable = cfdm.Count(data=cfdm.Data(count_array))
   count_variable.set_property('long_name', 'number of obs for this timeseries')

   # Create the contiguous ragged array object
   array = cfdm.RaggedContiguousArray(
                    compressed_array=cfdm.NumpyArray(ragged_array),
                    shape=(2, 4), size=8, ndim=2,
                    count_variable=count_variable)

   # Create the field construct with the domain axes and the ragged
   # array
   tas = cfdm.Field()
   tas.properties({'standard_name': 'air_temperature',
	           'units': 'K'})
   
   # Create the domain axis constructs for the uncompressed array
   X = tas.set_domain_axis(cfdm.DomainAxis(4))
   Y = tas.set_domain_axis(cfdm.DomainAxis(2))
   
   # Set the data for the field
   tas.set_data(cfdm.Data(array), axes=[Y, X])

				
We can now inspect the new field construct:

.. code:: python
   
   >>> tas
   <Field: air_temperature(cid%domainaxis1(2), cid%domainaxis0(4)) K>
   >>> print(tas.get_array())
   [[280.0 282.5    --    --]
    [281.0 279.0 278.0 279.5]]
   >>> tas.data.get_compression_type()
   'ragged contiguous'
   >>> print(tas.data.get_compressed_array())
   [280.  282.5 281.  279.  278.  279.5]
   >>> count_variable = tas.data.get_count_variable()
   >>> count_variable
   <Count: long_name:number of obs for this timeseries(2) >
   >>> print(count_variable.get_array())
   [2 4]

Gathering
---------

The CF data model views arrays that are compressed by removing
unwanted missing data in their uncompressed form. So, when axes have
been `compressed by gathering
<http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#compression-by-gathering>`_,
the field construct contains the domain axes that have been compressed
and presents a view of the data in their uncompressed form, even
though the underlying arrays remain in their gathered representation.

Accessing the data by a call to the `!get_array` method returns a
numpy array that is uncompressed. The underlying array will, however,
remain in its compressed form. The underlying compressed array may be
retrieved as a numpy array with the `get_compressed_array` method of a
`Data` object.

A subspace created by indexing will no longer be compressed,
i.e. its underlying array will be in incomplete multidimensional
representation. The original data will, however, retain its underlying
compressed array.

If the data elements are modified by indexed assignment then the
underlying compressed array is replaced by its uncompressed form.

Indexing is based on the axes of the uncompressed form of the data.

A list variable that is required to uncompress a gathered array is
stored in a `List` object and is retrieved with the
`get_list_variable` method of the `Data` object.

This is illustrated with the file **gathered.nc** (`download`):

.. code:: bash
   
   $ ncdump -h gathered.nc
   netcdf gathered {
   dimensions:
   	time = 2 ;
   	lat = 4 ;
   	lon = 5 ;
   	landpoint = 7 ;
   variables:
   	double time(time) ;
   		time:standard_name = "time" ;
   		time:units = "days since 2000-1-1" ;
   	double lat(lat) ;
   		lat:standard_name = "latitude" ;
   		lat:units = "degrees_north" ;
   	double lon(lon) ;
   		lon:standard_name = "longitude" ;
   		lon:units = "degrees_east" ;
   	int landpoint(landpoint) ;
   		landpoint:compress = "lat lon" ;
   	double pr(time, landpoint) ;
   		pr:standard_name = "precipitation_flux" ;
   		pr:units = "kg m2 s-1" ;
   
   // global attributes:
   		:Conventions = "CF-1.7" ;
   }

Reading and inspecting this file shows the data presented in
three-dimensional uncompressed form, whilst the underlying array is
still in the two-dimensional gathered representation described in the
file:

.. code:: python

   >>> p = cfdm.read('gathered.nc')[0]
   >>> print(p)
   Field: precipitation_flux (ncvar%pr)
   ------------------------------------
   Data            : precipitation_flux(time(2), latitude(4), longitude(5)) kg m2 s-1
   Dimension coords: time(2) = [2000-02-01 00:00:00, 2000-03-01 00:00:00]
                   : latitude(4) = [-90.0, ..., -75.0] degrees_north
                   : longitude(5) = [0.0, ..., 40.0] degrees_east
   >>> print(p.get_array())
   [[[--       0.000122 0.0008   --       --      ]
     [0.000177 --       0.000175 0.00058  --      ]
     [--       --       --       --       --      ]
     [--       0.000206 --       0.0007   --      ]]
					  	 
    [[--       0.000202 0.000174 --       --      ]
     [0.00084  --       0.000201 0.0057   --      ]
     [--       --       --       --       --      ]
     [--       0.000223 --       0.000102 --      ]]]
   >>> print(p.data.get_compressed_array())
   [[0.000122 0.0008   0.000177 0.000175 0.00058 0.000206 0.0007  ]
    [0.000202 0.000174 0.00084  0.000201 0.0057  0.000223 0.000102]]
   >>> list_variable = p.data.get_list_variable()
   >>> list_variable
   <List: ncvar%landpoint(7) >
   >>> print(list_variable.get_array())
   [1 2 5 7 8 16 18]

If the underlying array is compressed at the time of writing to disk
with the `cfdm.write` function, then it is written to the file as a
gathered array, along with the required list variable required to
uncompress it. This means that if a dataset using compression is read
from disk then it will be written back to disk with the same
compression, provided that no data elements have been modified by
assignment. Any compressed arrays that have been modified will be
written to an output dataset without compression.
   
A construct with an underlying compressed array is created by
initializing the `Data` object with a compressed array that is stored
in the special `GatheredArray` array object. The following code
creates a simple field construct with an underlying gathered array:

.. code:: python

   import numpy	  
   import cfdm

   # Define the gathered values
   gathered_array = numpy.array([[280, 282.5, 281], [279, 278, 277.5]],
                                dtype='float32')

   # Define the list array values
   list_array = [1, 4, 5]

   # Create the list variable
   list_variable = cfdm.List(data=cfdm.Data(list_array))

   # Create the gathered array object
   array = cfdm.GatheredArray(
                    compressed_array=cfdm.NumpyArray(gathered_array),
		    compressed_dimension=1,
                    shape=(2, 3, 2), size=12, ndim=3,
                    list_variable=list_variable)

   # Create the field construct with the domain axes and the gathered
   # array
   tas = cfdm.Field(properties={'standard_name': 'air_temperature',
                                'units': 'K'})

   # Create the domain axis constructs for the uncompressed array
   T = tas.set_domain_axis(cfdm.DomainAxis(2))
   Y = tas.set_domain_axis(cfdm.DomainAxis(3))
   X = tas.set_domain_axis(cfdm.DomainAxis(2))

   # Set the data for the field
   tas.set_data(cfdm.Data(array), axes=[T, Y, X])			      

Note that, because compression by gathering acts on a subset of the
array dimensions, it is necessary to state the position of the
compressed dimension in the compressed array (with the
*compressed_dimension* parameter of the `GatheredArray`
initialisation).

We can now inspect the new field construct:

.. code:: python
   
   >>> tas
   <Field: air_temperature(cid%domainaxis0(2), cid%domainaxis1(3), cid%domainaxis2(2)) K>
   >>> print(tas.get_array())
   [[[--    280.0]
     [--    --   ]
     [282.5 281.0]]
   
    [[--    279.0]
     [--    --   ]
     [278.0 277.5]]]
   >>> tas.data.get_compression_type()
   'gathered'
   >>> print(tas.data.get_compressed_array())
   [[ 280.   282.5  281. ]
    [ 279.   278.   277.5]]
   >>> list_variable = tas.data.get_list_variable()
   >>> list_variable 
   <List: (3) >
   >>> print(list_variable.get_array())
   [1 4 5]


----

.. rubric:: Footnotes
	    
.. [#opendap] Requires the netCDF-4 C library to have been compiled
              with OPeNDAP support enabled.

.. [#files] The tutorial files may be also found in the
            `docs/netcdf_files
            <https://github.com/NCAS-CMS/cfdm/tree/master/docs/netcdf_files>`_
            directory.

