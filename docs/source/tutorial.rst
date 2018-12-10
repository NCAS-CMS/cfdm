.. currentmodule:: cfdm
.. default-role:: obj

.. _Tutorial:

**Tutorial**
============

Version |release| for version |version| of the CF conventions.

----
 
The code examples in this tutorial are available in an **IPython
Jupyter notebook** (:download:`download <notebooks/tutorial.ipynb>`,
70kB) [#notebook]_, [#files]_.

.. _Import:

**Import**
----------

----

The cfdm package is imported as follows:

.. code:: python

   >>> import cfdm

.. _CF-version:

**CF version**
--------------

----

The version of the `CF conventions <http://cfconventions.org>`_ and
the CF data model being used may be found with the `cfdm.CF` function:

.. code:: python

   >>> cfdm.CF()
   '1.7'

.. _Reading-datasets:

**Reading datasets**
--------------------

----

The `cfdm.read` function reads a `netCDF
<https://www.unidata.ucar.edu/software/netcdf/>`_ file from disk, or
from an `OPeNDAP <https://www.opendap.org/>`_ URL [#opendap2]_, and
returns the contents as a list of zero or more `Field` class
instances, each of which represents a field construct. Henceforth, the
phrase "field construct" will be assumed to mean "`Field` instance",
unless stated otherwise [#language]_.

For example, to read the file ``file.nc`` (:download:`download
<netcdf_files/file.nc>`, 9kB) [#files]_:

.. code:: python

   >>> x = cfdm.read('file.nc')
   >>> type(x)
   list

All formats of netCDF3 and netCDF4 files can be read.

The `cfdm.read` function has optional parameters to

* provide files that contain :ref:`external variables
  <External-variables>`, and

* :ref:`create independent field constructs from "metadata" netCDF
  variables <Creating-field-constructs-from-metadata-constructs>`,
  i.e. those that are referenced from CF-netCDF data variables.

*Note on performance*
  Descriptive properties are always read into memory, but `lazy
  loading <https://en.wikipedia.org/wiki/Lazy_loading>`_ is employed
  for all data arrays, which means that no data is read into memory
  until the data is required for inspection or to modify the array
  contents. This maximises the number of field constructs that may be
  read within a session, and makes the read operation fast.

.. _Inspection:

**Inspection**
--------------

----


The contents of a field construct may be inspected at three different
levels of detail.

.. _Minimal-detail:

**Minimal detail**
^^^^^^^^^^^^^^^^^^

The built-in `repr` function returns a short, one-line description:

.. code:: python

   >>> x
   [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
    <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>]
   >>> q = x[0]
   >>> t = x[1]
   >>> q
   <Field: specific_humidity(latitude(5), longitude(8)) 1>
   
This gives the identity of the field construct
(e.g. "specific_humidity"), the identities and sizes of the dimensions
spanned by the data array ("latitude" and "longitude" with sizes 5 and
8 respectively) and the units of the data ("1").

.. _Medium-detail:

**Medium detail**
^^^^^^^^^^^^^^^^^

The built-in `str` function returns similar information as the
one-line output, along with short descriptions of the metadata
constructs, which include the first and last values of their data
arrays:

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

.. _Full-detail:

**Full detail**
^^^^^^^^^^^^^^^

The `~cfdm.Field.dump` method of the field construct gives all
properties of all constructs, including metadata constructs and their
components, and shows the first and last values of all data arrays:

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

  
.. _cfdump:
       
**cfdump**
----------

The description for every field construct in a file can also be
generated from the command line, with minimal, medium or full detail,
by using the ``cfdump`` tool, for example:

.. code:: bash

   $ cfdump -s file.nc
   Field: specific_humidity(latitude(5), longitude(8)) 1
   Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K

       
.. _Properties:
       
**Properties**
--------------

----

Descriptive properties that apply to field construct as a whole may be
retrieved with the `~Field.properties` method:

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

   >>> t.has_property('standard_name')
   True
   >>> t.get_property('standard_name')
   'air_temperature'
   >>> t.del_property('standard_name')
   'air_temperature'
   >>> t.get_property('standard_name', 'not set')
   'not set'
   >>> t.set_property('standard_name', 'air_temperature')
   >>> t.get_property('standard_name', 'not set')
   'air_temperature'

The properties may be completely replaced with another collection by
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

.. _Data:

**Data**
--------

----

The field construct's data array is stored in a `Data` class instance
that is accessed with the `~Field.get_data` method:

.. code:: python

   >>> t.get_data()
   <Data(1, 10, 9): [[[262.8, ..., 269.7]]] K>

The data array may be retrieved as an independent (possibly masked)
`numpy` array with the `~Field.get_array` method:

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
   
The field construct also has a `~Field.data` attribute that is an
alias for the `~Field.get_data` method, which makes it easier to
access attributes and methods of the `Data` instance:

.. code:: python

   >>> t.data.dtype
   dtype('float64')
   >>> t.data.ndim
   3
   >>> t.data.shape
   (1, 10, 9)
   >>> t.data.size
   90


.. _Indexing:

**Indexing**
^^^^^^^^^^^^

Indexing a `Data` instance follows rules that are very similar to the
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


.. _Assignment:

**Assignment**
^^^^^^^^^^^^^^

Data array elements are changed by assigning to elements selected by
indexing the `Data` instance using the :ref:`cfdm indexing rules
<Indexing>`.

The value, or values, being assigned must be broadcastable to the
shape defined by the indices, using the `numpy broadcasting rules
<https://docs.scipy.org/doc/numpy/user/basics.broadcasting.html>`_.

Data array elements may be set to missing values by assigning them to
`numpy.ma.masked`. Missing values may be unmasked by assigning them to
any other value.

.. code:: python

   >>> import numpy
   >>> t.data[:, :, 1] = -10
   >>> t.data[:, 0] = range(9)
   >>> t.data[..., 6:3:-1, 3:6] = numpy.arange(-18, -9).reshape(3, 3)
   >>> t.data[0, [2, 9], [4, 8]] =  cfdm.Data([[-2, -3]])
   >>> t.data[0, :, -2] = numpy.ma.masked
   >>> t.data[0, 5, -2] = -1
   >>> print(t.get_array())
   [[[  0.0   1.0   2.0   3.0   4.0   5.0   6.0   --   8.0]
     [272.7 -10.0 279.5 278.9 263.8 263.3 274.2   -- 279.5]
     [269.7 -10.0 273.4 274.2  -2.0 270.2 280.0   --  -3.0]
     [261.7 -10.0 270.8 260.3 265.6 279.4 276.9   -- 260.6]
     [264.2 -10.0 262.5  -3.0  -2.0  -1.0 270.4   -- 275.3]
     [263.9 -10.0 272.1  -6.0  -5.0  -4.0 260.0 -1.0 270.2]
     [273.8 -10.0 268.5  -9.0  -8.0  -7.0 270.6   -- 270.6]
     [267.9 -10.0 279.8 260.3 261.2 275.3 271.2   -- 268.9]
     [270.9 -10.0 273.2 261.7 271.6 265.8 273.0   -- 266.4]
     [276.4 -10.0 276.3 266.1  -2.0 268.1 277.0   --  -3.0]]]

**Data dimensions**
^^^^^^^^^^^^^^^^^^^

The dimensions of a field construct's data may be reordered, have size
one dimensions removed and have new new size one dimensions included
by using the following field construct methods:

====================  ====================================
Method                Description
====================  ====================================
`~Field.transpose`    Reorder data dimensions
`~Field.expand_dims`  Insert a new size one data dimension
`~Field.squeeze`      Remove size one data dimensions
====================  ====================================

.. code:: python

   >>> t
   <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>
   >>> t2 = t.squeeze(0)
   >>> t2
   <Field: air_temperature(grid_latitude(10), grid_longitude(9)) K>   
   >>> t2 = t2.expand_dims(axis='domainaxis3', position=1)
   >>> t2
   <Field: air_temperature(grid_latitude(10), time(1), grid_longitude(9)) K>  
   >>> t2.transpose([2, 0, 1])
   <Field: air_temperature(grid_longitude(9), grid_latitude(10), time(1)) K>

.. _Subspacing:

**Subspacing**
--------------

----

Creation of a new field construct which spans a subspace of the
original domain is achieved by indexing the field directly (rather
than its `Data` instance). The new subspace contains the same
properties and similar metadata constructs to the original field, but
the latter are also subspaced when they span domain axis constructs
that have been changed. Subspacing uses the same :ref:`cfdm indexing
rules <Indexing>` that apply to the `Data` class.

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




.. _Metadata-constructs:

**Metadata constructs**
-----------------------

----

The metadata constructs are all of the constructs that serve to
describe the field construct that contains them. Each CF data model
metadata construct has a corresponding cfdm class:

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

The metadata constructs are returned by the `~Field.constructs` method
of the field construct, which provides a dictionary of the metadata
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
field construct and are

* *robust* (each metadata construct is guaranteed to have a unique
  identifier within its parent field construct),

..

* *arbitrary* (no semantic meaning should be attached to the
  identifier, and the same identifier will usually refer to different
  metadata constructs in different field constructs), and

..

* *unstable* (the identifiers could be different each time the field
  construct is created).

The `~Field.constructs` method has optional parameters to filter the
metadata constructs by

* metadata construct type,

* property value,

* whether or the data array spans particular domain axis constructs,

* construct identifier, and 

* netCDF variable or dimension name (see the :ref:`netCDF interface
  <NetCDF-interface>`).
 

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
   >>> t.constructs('wavelength')
   {}
   
Selection by construct identifier is useful for systematic metadata
construct access, and for when a metadata construct is not
identifiable by other means.

.. code:: python

   >>> t.constructs(cid='domainancillary2')
   {'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>}
   >>> t.constructs('cid%cellmethod1')
   {'cellmethod1': <CellMethod: domainaxis3: maximum>}
   >>> t.constructs(cid='auxiliarycoordinate999')
   {}

An individual metadata construct may be returned without its construct
identifier, via the `~Field.get_construct` method of the field
construct, which supports the same filtering options as the
`~Field.constructs` method. The existence of a metadata construct may
be checked with the `~Field.has_construct` method and a construct may
be removed with the `~Field.del_construct` method.

.. code:: python

   >>> t.has_construct('latitude')
   True
   >>> t.get_construct('latitude')
   <AuxiliaryCoordinate: latitude(10, 9) degrees_N>
   >>> t.get_construct('units:km2')
   <CellMeasure: measure%area(9, 10) km2>
   >>> t.constructs('units:degrees')
   {'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>}
   >>> t.get_construct('units:degrees')
   ValueError: More than one construct meets criteria
   >>> t.has_construct('units:degrees')
   False

Metadata constructs of a particular type can also be retrieved more
conveniently with the following methods of the field construct:

==============================  ====================================
Method                          Description
==============================  ====================================
`~Field.domain_axes`            The domain axis constructs
`~Field.cell_methods`           The ordered cell method constructs
`~Field.field_ancillaries`      The field ancillary constructs
`~Field.auxiliary_coordinates`  The auxiliary coordinate constructs
`~Field.cell_measures`          The cell measure constructs
`~Field.dimension_coordinates`  The dimension coordinates
`~Field.domain_ancillaries`     The domain ancillary constructs
`~Field.coordinate_references`  The coordinate reference constructs
==============================  ====================================

.. code:: python

   >>> t.coordinate_references()
   {'coordinatereference0': <CoordinateReference: atmosphere_hybrid_height_coordinate>,
    'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>}
   >>> t.dimension_coordinates()
   {'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
    'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

**Properties and data**
^^^^^^^^^^^^^^^^^^^^^^^

Where applicable, metadata constructs share the same API as the field
construct. This means, for instance, that any construct that has a
data array (i.e. auxiliary coordinate, dimension coordinate, cell
measure, domain ancillary and field ancillary constructs) will have a
`!get_array` method to access its data as an independent numpy array:

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

**Domain axes**
^^^^^^^^^^^^^^^

The domain axis constructs spanned by a metadata construct's data are
found with the `~Field.construct_axes` method of the field construct:

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

The domain axis constructs spanned by the field construct's data found
with the `~Field.get_data_axes` method of the field construct:

.. code:: python

   >>> t.domain_axes()
   {'domainaxis0': <DomainAxis: 1>,
    'domainaxis1': <DomainAxis: 10>,
    'domainaxis2': <DomainAxis: 9>,
    'domainaxis3': <DomainAxis: 1>}
   >>> t
   <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>
   >>> t.data.shape
   (1, 10, 9)
   >>> t.get_data_axes()
   ('domainaxis0', 'domainaxis1', 'domainaxis2')

.. _Cell-methods:
   
**Cell methods**
^^^^^^^^^^^^^^^^

A cell method construct describes how the data represent the variation
of the physical quantity within the cells of the domain, and multiple
cell method constructs allow multiple methods to be recorded. Because
the application of cell methods is not commutative (e.g. a mean of
variances is generally not the same as a variance of means), the
`~cfdm.Field.cell_methods` method of the field construct returns an
ordered dictionary of constructs. The order is the same as that
described by a cell method attribute read from a netCDF dataset, or
the same as that in which cell method constructs were added to the
field construct during :ref:`field construct creation
<Field-construct-creation>`.

.. code:: python

   >>> t.cell_methods()
   OrderedDict([('cellmethod0', <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>),
                ('cellmethod1', <CellMethod: domainaxis3: maximum>)])


**Components**
^^^^^^^^^^^^^^

Other classes are required to represent metadata construct components
that are neither "properties" nor "data":

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
    
.. _NetCDF-interface:

**NetCDF interface**
--------------------

----

The logical CF data model is independent of netCDF, but the CF
conventions are designed to enable the processing and sharing of
datasets stored in netCDF files. Therefore, the cfdm package includes
methods for recording and editing netCDF elements that are not part of
the CF model, but are nonetheless often required to interpret and
create CF-netCDF datasets. See the section on :ref:`philosophy
<philosophy>` for a further discussion.

When a netCDF dataset is read, netCDF elements (such as dimension and
variable names, and some attribute values) that do not have a place in
the CF data model are, nevertheless, stored within the appropriate
cfdm constructs. This allows them to be used when writing field
constructs to a new netCDF dataset, and also makes them accessible for
metadata construct identification with the `~Field.constructs` and
`~Field.get_construct` methods of the field construct:

.. code:: python
	  
   >>> t.constructs('ncvar%b')
   {'domainancillary1': <DomainAncillary: ncvar%b(1) >}
   >>> t.get_construct('ncvar%x')
   <DimensionCoordinate: grid_longitude(9) degrees>
   >>> t.get_construct('ncdim%x')
   <DomainAxis: 9>
     
Each construct has methods to access the netCDF elements which it
requires. For example, the field construct has the following methods:

================================  ====================================
Method                            Description
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
   
.. _Writing-to-disk:
   
**Writing to disk**
-------------------

----

The `cfdm.write` function writes a field construct, or a sequence of
field constructs, to a new netCDF file on disk:

.. code:: python

   >>> print(q)
   Field: specific_humidity (ncvar%humidity)
   -----------------------------------------
   Data            : specific_humidity(latitude(5), longitude(8)) 1
   Cell methods    : area: mean
   Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                   : longitude(8) = [22.5, ..., 337.5] degrees_east
                   : time(1) = [2019-01-01 00:00:00]
   >>> cfdm.write(q, 'q_file.nc')

The new dataset is structured as follows:

.. code:: bash

   $ ncdump -h q_file.nc
   netcdf q_file {
   dimensions:
   	lat = 5 ;
   	bounds2 = 2 ;
   	lon = 8 ;
   variables:
   	double lat_bnds(lat, bounds2) ;
   	double lat(lat) ;
   		lat:units = "degrees_north" ;
   		lat:standard_name = "latitude" ;
   		lat:bounds = "lat_bnds" ;
   	double lon_bnds(lon, bounds2) ;
   	double lon(lon) ;
   		lon:units = "degrees_east" ;
   		lon:standard_name = "longitude" ;
   		lon:bounds = "lon_bnds" ;
   	double time ;
   		time:units = "days since 2018-12-01" ;
   		time:standard_name = "time" ;
   	double humidity(lat, lon) ;
   		humidity:standard_name = "specific_humidity" ;
   		humidity:cell_methods = "area: mean" ;
   		humidity:units = "1" ;
   		humidity:coordinates = "time" ;
   
   // global attributes:
   		:Conventions = "CF-1.7" ;
   		:project = "research" ;
   }

A sequence of field constructs is written in exactly the same way:
   
.. code:: python
	     
   >>> x
   [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
    <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>]
   >>> cfdm.write(x, 'new_file.nc')

The `cfdm.write` function has optional parameters to

* set the output netCDF format (all netCDF3 and netCDF4 formats are
  possible);

* specify which field construct properties should become netCDF data
  variable attributes and which should, if possible, become netCDF
  global attributes;
  
* create :ref:`external variables <External-variables>` in an external
  file;

* change the data type of output data arrays;
  
* apply netCDF compression and packing; and

* set the endian-ness of the output data.

Output netCDF variable and dimension names read from a netCDF dataset
are stored in the resulting field constructs, and may also be set
manually with the `!nc_set_variable` and `nc_set_dimension`
methods. If a name has not been set then one will be generated
internally (usually based on the standard name if it exists).

It is possible to create netCDF unlimited dimensions and set the HDF5
chunk size using the `nc_unlimited_dimensions` and
`~Field.nc_chunksize` methods of the field construct.

.. _Scalar-coordinate-variables

**Scalar coordinate variables**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

CF-netCDF scalar (i.e. zero-dimensional) coordinate variables are
created when there is a size one domain axis construct which is
spanned by a dimension coordinate construct's data array, but not the
field construct's data, nor the data of any other metadata construct.

This is the case for the "specific humidity" field construct ``q``
that was written to the file ``q_file.nc``.

To change this so that the "time" dimension coordinate construct is
written as a CF-netCDF size one coordinate variable, the field
construct's data must be expanded to span the corresponding size one
domain axis construct, by using the `~Field.expand_dims` method of the
field construct:

.. code:: python
		   
   >>> print(q)
   Field: specific_humidity (ncvar%humidity)
   -----------------------------------------
   Data            : specific_humidity(latitude(5), longitude(8)) 1
   Cell methods    : area: mean
   Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                   : longitude(8) = [22.5, ..., 337.5] degrees_east
                   : time(1) = [2019-01-01 00:00:00]
   <Field: specific_humidity(latitude(5), longitude(8)) 1>
   >>> q.get_construct_axes('time')
   ('domainaxis2',)
   >>> q2 = q.expand_dims(axis='domainaxis2')
   >>> q2
   <Field: specific_humidity(time(1), latitude(5), longitude(8)) 1>
   >>> cfdm.write(q2, 'q2_file.nc')

The new dataset is structured as follows (note, relative to file
``q_file.nc``, the existence of the "time" dimension and the lack of a
"coordinates" attribute on the, now three-dimensional, data variable):
   
.. code:: bash

   $ ncdump -h q2_file.nc
   netcdf q2_file {
   dimensions:
   	lat = 5 ;
   	bounds2 = 2 ;
   	lon = 8 ;
   	time = 1 ;
   variables:
   	double lat_bnds(lat, bounds2) ;
   	double lat(lat) ;
   		lat:units = "degrees_north" ;
   		lat:standard_name = "latitude" ;
   		lat:bounds = "lat_bnds" ;
   	double lon_bnds(lon, bounds2) ;
   	double lon(lon) ;
   		lon:units = "degrees_east" ;
   		lon:standard_name = "longitude" ;
   		lon:bounds = "lon_bnds" ;
   	double time(time) ;
   		time:units = "days since 2018-12-01" ;
   		time:standard_name = "time" ;
   	double humidity(time, lat, lon) ;
   		humidity:units = "1" ;
   		humidity:standard_name = "specific_humidity" ;
   		humidity:cell_methods = "area: mean" ;
   
   // global attributes:
   		:Conventions = "CF-1.7" ;
   		:project = "research" ;
   }
    

.. _Field-construct-creation:

**Field construct creation**
----------------------------

----

Creation of a field construct has three stages:

**Stage 1:** The field construct is created without metadata constructs.

..
   
**Stage 2:** Metadata constructs are created independently.

..

**Stage 3:** The metadata constructs are inserted into the field
construct with cross-references to other, related metadata constructs
if required (for example, an auxiliary coordinate construct is related
to an ordered list of the domain axis constructs which correspond to
its data array dimensions).

There are two equivalent approaches to stages **1** and **2**.

Either as much of the content as possible is specified during object
instantiation:

.. code:: python

   >>> p = cfdm.Field(properties={'standard_name': 'precipitation_flux'})
   >>> p
   <Field: precipitation_flux>
   >>> dc = cfdm.DimensionCoordinate(properties={'long_name': 'Longitude'},
   ...                               data=cfdm.Data([0, 1, 2.]))
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

   >>> p = cfdm.Field()
   >>> p
   <Field: >
   >>> p.set_property('standard_name', 'precipitation_flux')
   >>> p
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

For stage **3**, the `~cfdm.Field.set_construct` method of the field
construct is used for setting metadata constructs and mapping data
array dimensions to domain axis constructs. This method returns the
construct identifier for the metadata construct which can be used when
other metadata constructs are added to the field (e.g. to specify
which domain axis constructs correspond to a data array), or when
other metadata constructs are created (e.g. to identify the domain
ancillary constructs forming part of a coordinate reference
construct):


.. =============================================  ======================================================================
   Method for setting a metadata construct        Description
   =============================================  ======================================================================
   `~Field.set_domain_axis`                       Set a domain axis construct
   `~Field.set_cell_method`                       Set a cell method construct
   `~Field.set_field_ancillary`                   Set a field ancillary construct and the axes spanned by its data
   `~Field.set_auxiliary_coordinate`              Set an auxiliary coordinate construct and the axes spanned by its data
   `~Field.set_cell_measure`                      Set an cell measure construct and the axes spanned by its data
   `~Field.set_dimension_coordinate`              Set a dimension coordinate construct and the axes spanned by its data
   `~Field.set_domain_ancillary`                  Set a domain ancillary and the axes spanned by its data
   `~Field.set_coordinate_reference`              Set a coordinate reference construct
   =============================================  ======================================================================

.. code:: python
	  
   >>> longitude_axis = p.set_construct(cfdm.DomainAxis(3))
   >>> longitude_axis
   'domainaxis0'
   >>> cid = p.set_construct(dc, axes=[longitude_axis])
   >>> cid
   'dimensioncoordinate0'
   >>> cm = cfdm.CellMethod(axes=[longitude_axis],
   ...                      properties={'method': 'minimum'})
   >>> p.set_construct(cm)
   'cellmethod0'
   
In general, the order in which metadata constructs are added to the
field does not matter, except when one metadata construct is required
by another, in which case the former must be added to the field first
so that its construct identifier is available to the latter. Cell
method constructs must, however, be set in the relative order in which
their methods were applied to the data.

The domain axis constructs spanned by a metadata construct's data may
be changed after insertion with the `~Field.set_construct_axes` method
of the field construct.

The following code creates a field construct with properties; data;
and domain axis, cell method and dimension coordinate metadata
constructs (data arrays have been generated with dummy values using
`numpy.arange`):

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

   # Insert the domain axes into the field. The set_construct method
   # returns the domain axis construct identifier that will be used
   # later to specify which domain axis corresponds to which dimension
   # coordinate construct.  
   axisT = Q.set_construct(domain_axisT)
   axisY = Q.set_construct(domain_axisY)
   axisX = Q.set_construct(domain_axisX)

   # Field data
   data = cfdm.Data(numpy.arange(40.).reshape(5, 8))
   Q.set_data(data, axes=[axisY, axisX])

   # Create the cell methods
   cell_method1 = cfdm.CellMethod(axes=['area'], properties={'method': 'mean'})

   cell_method2 = cfdm.CellMethod()
   cell_method2.set_axes([axisT])
   cell_method2.properties({'method': 'maximum'})

   # Insert the cell methods into the field in the same order that
   # their methods were applied to the data
   Q.set_construct(cell_method1)
   Q.set_construct(cell_method2)

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
   Q.set_construct(dimT, axes=[axisT])
   Q.set_construct(dimY, axes=[axisY])
   Q.set_construct(dimX, axes=[axisX])

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

It is not necessary to set the "Conventions" property, because this is
automatically included in output files as a netCDF global
"Conventions" attribute corresponding to the version number of CF
being used, as returned by the `cfdm.CF` function. For example, a CF
version of ``'1.7'`` will produce a "Conventions" attribute value of
``'CF-1.7'``.

If this field were to be written to a netCDF dataset then, in the
absence of pre-defined names, default netCDF variable and dimension
names would be automatically generated (based on standard names where
they exist). The setting of bespoke names is, however, easily done
with the :ref:`netCDF interface <NetCDF-interface>`:

.. code:: python

   Q.nc_set_variable('q')

   domain_axisT.nc_set_dimension('time')
   domain_axisY.nc_set_dimension('lat')
   domain_axisX.nc_set_dimension('lon')

   dimT.nc_set_variable('time')
   dimY.nc_set_variable('lat')
   dimX.nc_set_variable('lon')

Here is a more complete example which creates a field construct that
contains every type of metadata construct (again, data arrays have
been generated with dummy values using `numpy.arange`):

.. code:: python

   import numpy
   import cfdm
   
   # Initialize the field
   tas = cfdm.Field(
       properties={'project': 'research',
                   'standard_name': 'air_temperature',
                   'units': 'K'})
   
   # Create and set domain axes
   axis_T = tas.set_construct(cfdm.DomainAxis(1))
   axis_Z = tas.set_construct(cfdm.DomainAxis(1))
   axis_Y = tas.set_construct(cfdm.DomainAxis(10))
   axis_X = tas.set_construct(cfdm.DomainAxis(9))
   
   # Set the field data
   tas.set_data(cfdm.Data(numpy.arange(90.).reshape(10, 9)),
                axes=[axis_Y, axis_X])
   
   # Create and set the cell methods
   cell_method1 = cfdm.CellMethod(
             axes=[axis_Y, axis_X],
             properties={'method': 'mean',
                         'where': 'land',
                         'intervals': [cfdm.Data(0.1, units='degrees')]})
   
   cell_method2 = cfdm.CellMethod(
                    axes=[axis_T],
                    properties={'method': 'maximum'})
   
   tas.set_construct(cell_method1)
   tas.set_construct(cell_method2)
   
   # Create and set the field ancillaries
   field_ancillary = cfdm.FieldAncillary(
                properties={'standard_name': 'air_temperature standard_error',
                             'units': 'K'},
                data=cfdm.Data(numpy.arange(90.).reshape(10, 9)))
   
   tas.set_construct(field_ancillary, axes=[axis_Y, axis_X])
   
   # Create and set the dimension coordinates
   dimension_coordinate_T = cfdm.DimensionCoordinate(
                              properties={'standard_name': 'time',
                                          'units': 'days since 2018-12-01'},
                              data=cfdm.Data([15.5]),
                              bounds=cfdm.Bounds(data=cfdm.Data([[0., 31]])))
   
   dimension_coordinate_Z = cfdm.DimensionCoordinate(
           properties={'computed_standard_name': 'altitude',
                       'standard_name': 'atmosphere_hybrid_height_coordinate'},
           data = cfdm.Data([1.5]),
           bounds=cfdm.Bounds(data=cfdm.Data([[1.0, 2.0]])))
   
   dimension_coordinate_Y = cfdm.DimensionCoordinate(
           properties={'standard_name': 'grid_latitude',
                       'units': 'degrees'},
           data=cfdm.Data(numpy.arange(10.)),
           bounds=cfdm.Bounds(data=cfdm.Data(numpy.arange(20).reshape(10, 2))))
   
   dimension_coordinate_X = cfdm.DimensionCoordinate(
           properties={'standard_name': 'grid_longitude',
                       'units': 'degrees'},
       data=cfdm.Data(numpy.arange(9.)),
       bounds=cfdm.Bounds(data=cfdm.Data(numpy.arange(18).reshape(9, 2))))
   
   dim_T = tas.set_construct(dimension_coordinate_T, axes=[axis_T])
   dim_Z = tas.set_construct(dimension_coordinate_Z, axes=[axis_Z])
   dim_Y = tas.set_construct(dimension_coordinate_Y, axes=[axis_Y])
   dim_X = tas.set_construct(dimension_coordinate_X, axes=[axis_X])
   
   # Create and set the auxiliary coordinates
   auxiliary_coordinate_lat = cfdm.AuxiliaryCoordinate(
                         properties={'standard_name': 'latitude',
                                     'units': 'degrees_north'},
                         data=cfdm.Data(numpy.arange(90.).reshape(10, 9)))
   
   auxiliary_coordinate_lon = cfdm.AuxiliaryCoordinate(
                     properties={'standard_name': 'longitude',
                                 'units': 'degrees_east'},
                     data=cfdm.Data(numpy.arange(90.).reshape(9, 10)))
   
   array = numpy.ma.array(list('abcdefghij'))
   array[0] = numpy.ma.masked
   auxiliary_coordinate_name = cfdm.AuxiliaryCoordinate(
                          properties={'long_name': 'Grid latitude name'},
                          data=cfdm.Data(array))
   
   aux_LAT  = tas.set_construct(auxiliary_coordinate_lat, axes=[axis_Y, axis_X])
   aux_LON  = tas.set_construct(auxiliary_coordinate_lon, axes=[axis_X, axis_Y])
   aux_NAME = tas.set_construct(auxiliary_coordinate_name, axes=[axis_Y])
   
   # Create and set domain ancillaries
   domain_ancillary_a = cfdm.DomainAncillary(
                      properties={'units': 'm'},
                      data=cfdm.Data([10.]),
                      bounds=cfdm.Bounds(data=cfdm.Data([[5., 15.]])))
   
   domain_ancillary_b = cfdm.DomainAncillary(
                          properties={'units': '1'},
                          data=cfdm.Data([20.]),
                          bounds=cfdm.Bounds(data=cfdm.Data([[14, 26.]])))
   
   domain_ancillary_orog = cfdm.DomainAncillary(
                             properties={'standard_name': 'surface_altitude',
                                        'units': 'm'},
                             data=cfdm.Data(numpy.arange(90.).reshape(10, 9)))
   
   domain_anc_A    = tas.set_construct(domain_ancillary_a, axes=[axis_Z])
   domain_anc_B    = tas.set_construct(domain_ancillary_b, axes=[axis_Z])
   domain_anc_OROG = tas.set_construct(domain_ancillary_orog,
                                       axes=[axis_Y, axis_X])
   
   # Create and set the coordinate references
   datum = cfdm.Datum(parameters={'earth_radius': 6371007.})
   
   coordinate_conversion_h = cfdm.CoordinateConversion(
                 parameters={'grid_mapping_name': 'rotated_latitude_longitude',
                             'grid_north_pole_latitude': 38.0,
                             'grid_north_pole_longitude': 190.0})
   
   horizontal_crs = cfdm.CoordinateReference(
                      datum=datum,
                      coordinate_conversion=coordinate_conversion_h,
                      coordinates=[dim_X,
                                   dim_Y,
                                   aux_LAT,
                                   aux_LON])
   
   coordinate_conversion_v = cfdm.CoordinateConversion(
            parameters={'standard_name': 'atmosphere_hybrid_height_coordinate',
                        'computed_standard_name': 'altitude'},
            domain_ancillaries={'a': domain_anc_A,
                                'b': domain_anc_B,
                                'orog': domain_anc_OROG})
   
   vertical_crs = cfdm.CoordinateReference(
                    datum=datum,
                    coordinate_conversion=coordinate_conversion_v,
                    coordinates=[dim_Z])
   
   tas.set_construct(horizontal_crs)
   tas.set_construct(vertical_crs)
   
   # Create and set the cell measures
   cell_measure = cfdm.CellMeasure(measure='area',
                    properties={'units': 'km2'},
                    data=cfdm.Data(numpy.arange(90.).reshape(9, 10)))
   
   tas.set_construct(cell_measure, axes=[axis_X, axis_Y])

The new field construct may now be inspected:

.. code:: python

   >>> print(tas)
   Field: air_temperature
   ----------------------
   Data            : air_temperature(grid_latitude(10), grid_longitude(9)) K
   Cell methods    : grid_latitude(10): grid_longitude(9): mean where land (interval: 0.1 degrees) time(1): maximum
   Field ancils    : air_temperature standard_error(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 89.0]] K
   Dimension coords: time(1) = [2018-12-16 12:00:00]
                   : atmosphere_hybrid_height_coordinate(1) = [1.5]
                   : grid_latitude(10) = [0.0, ..., 9.0] degrees
                   : grid_longitude(9) = [0.0, ..., 8.0] degrees
   Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 89.0]] degrees_north
                   : longitude(grid_longitude(9), grid_latitude(10)) = [[0.0, ..., 89.0]] degrees_east
                   : long_name:Grid latitude name(grid_latitude(10)) = [--, ..., j]
   Cell measures   : measure%area(grid_longitude(9), grid_latitude(10)) = [[0.0, ..., 89.0]] km2
   Coord references: atmosphere_hybrid_height_coordinate
                   : rotated_latitude_longitude
   Domain ancils   : domainancillary0(atmosphere_hybrid_height_coordinate(1)) = [10.0] m
                   : domainancillary1(atmosphere_hybrid_height_coordinate(1)) = [20.0] 1
                   : surface_altitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 89.0]] m

.. _Creating-field-constructs-from-metadata-constructs:

Creating field constructs from metadata constructs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Independent field constructs may be created from metadata in two ways:
either derived from a netCDF variable using the `cfdm.read` function,
or derived from a metadata construct using the `~Field.create_field`
method of the field construct.

The `~Field.create_field` method of the field construct identifies a
unique metadata construct and returns a new field construct based on
its properties and data. The new field construct always has domain
axis constructs corresponding to the data, and may also contain other
metadata constructs that further define its domain.

.. code:: python

   >>> orog = tas.create_field('surface_altitude')	  
   >>> print(orog)
   Field: surface_altitude
   -----------------------
   Data            : surface_altitude(grid_latitude(10), grid_longitude(9)) m
   Dimension coords: grid_latitude(10) = [0.0, ..., 9.0] degrees
                   : grid_longitude(9) = [0.0, ..., 8.0] degrees
   Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 89.0]] degrees_north
                   : longitude(grid_longitude(9), grid_latitude(10)) = [[0.0, ..., 89.0]] degrees_east
                   : long_name:Grid latitude name(grid_latitude(10)) = [--, ..., j]
   Cell measures   : measure%area(grid_longitude(9), grid_latitude(10)) = [[0.0, ..., 89.0]] km2
   Coord references: rotated_latitude_longitude

   >>> orog1 = tas.create_field('surface_altitude', domain=False) 
   >>> print(orog1)
   Field: surface_altitude
   -----------------------
   Data            : surface_altitude(cid%domainaxis2(10), cid%domainaxis3(9)) m
   
The `cfdm.read` function allows field constructs to be derived
directly from the netCDF variables that, in turn, correspond to
metadata constructs. In this case, the new field constructs will have
a domain limited to that which can be inferred from the corresponding
netCDF variable, but without the connections that are defined by the
parent netCDF data variable. This will usually result in different
field constructs than are created with the `~Field.create_field`
method.

.. code:: python

   >>> cfdm.write(tas, 'tas.nc')
   >>> fields = cfdm.read('tas.nc', create_field='domain_ancillary')
   >>> fields
   [<Field: ncvar%a(atmosphere_hybrid_height_coordinate(1)) m>,
    <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>,
    <Field: ncvar%b(atmosphere_hybrid_height_coordinate(1)) 1>,
    <Field: surface_altitude(grid_latitude(10), grid_longitude(9)) m>]
   >>> print(fields[3])
   Field: surface_altitude (ncvar%surface_altitude)
   ------------------------------------------------
   Data            : surface_altitude(grid_latitude(10), grid_longitude(9)) m
   Dimension coords: grid_latitude(10) = [0.0, ..., 9.0] degrees
                   : grid_longitude(9) = [0.0, ..., 8.0] degrees

.. _Domain:

**Domain**
----------

----

The domain of the CF data model describes the locations of the field
construct's data and is represented by the `Domain` class. The domain
instance may be accessed with the `~Field.get_domain` method of the
field construct:

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

Changes to domain instance are seen by the field construct, and vice
versa. This is because the domain instance is merely "view" of the
relevant metadata constructs contained in the field construct. The
field construct also has a `~Field.domain` attribute that is an alias
for the `~Field.get_domain` method, which makes it easier to access
attributes and methods of the domain instance:

.. code:: python

   >>> domain.get_construct('latitude').set_property('test', 'set by domain')
   >>> t.get_construct('latitude').get_property('test')
   'set by domain'
   >>> t.get_construct('latitude').set_property('test', 'set by field')
   >>> domain.get_construct('latitude').get_property('test')
   'set by field'
   >>> domain.get_construct('latitude').del_property('test')
   'set by field'
   >>> t.get_construct('latitude').has_property('test')
   False


.. _Copying:

**Copying**
-----------

----

A field construct may be copied with its `~Field.copy` method. This
produces a "deep copy", i.e. the new field construct is completely
independent of the original field.

.. code:: python

   >>> u = t.copy()
   >>> u.data[0, 0, 0] = -1e30
   >>> print(u.data[0, 0, 0])
   [[[-1e+30]]] K
   >>> print(t.data[0, 0, 0])
   [[[0.0]]] K
   >>> u.del_construct('grid_latitude')
   <DimensionCoordinate: grid_latitude(10) degrees>
   >>> u.constructs('grid_latitude')
   {}
   >>> t.constructs('grid_latitude')
   {'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>}

Equivalently, the `copy.deepcopy` function may be used:

.. code:: python

   >>> import copy
   >>> u = copy.deepcopy(t)

Metadata constructs may be copied individually in the same manner:

.. code:: python

   >>> orog = t.get_construct('surface_altitude').copy()

*Note on performance*
  Arrays within `Data` instances are copied with a `copy-on-write
  <https://en.wikipedia.org/wiki/Copy-on-write>`_ technique. This
  means that a copy takes up very little extra memory, even when the
  original constructs contain very large data arrays, and the copy
  operation is fast.

.. _Equality:

**Equality**
------------

----

Whether or not two field constructs are the same is tested with either
field construct's `~Field.equals` method.

.. code:: python

   >>> t.equals(t)
   True
   >>> t.equals(t.copy())
   True
   >>> t.equals(t[...])
   True
   >>> t.equals(q)
   False
   >>> t.equals(q, traceback=True)
   Field: Different units: 'K', '1'
   Field: Different properties
   False

Equality is strict by default. This means that for two field
constructs to be considered equal they must have corresponding
metadata constructs and for each pair of constructs:

* the descriptive properties must be the same (with the exception of
  the field construct's "Conventions" property, which is never
  checked), and vector-valued properties must have same the size and
  be element-wise equal, and
  
* if there are data arrays then they must have same shape, data type
  and be element-wise equal.

Two real numbers :math:`a` and :math:`b` are considered equal if
:math:`|a - b| \le atol + rtol|b|`, where :math:`atol` (the tolerance
on absolute differences) and :math:`rtol` (the tolerance on relative
differences) are positive, typically very small numbers. By default
both are set to the system epsilon (the difference between 1 and the
least value greater than 1 that is representable as a float). Their
values may be inspected and changed with the `cfdm.ATOL` and
`cfdm.RTOL` functions:

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

The `~Field.equals` method has optional parameters for modifying the
criteria for considering two fields to be equal:

* named properties may be omitted from the comparison,

* fill value and missing data value properties may be ignored,

* the data type of data arrays may be ignored, and

* the tolerances on absolute and relative differences for numerical
  comparisons may be temporarily changed, without changing the default
  settings.

Metadata constructs may also be tested for equality:

.. code:: python
	  
   >>> orog = t.get_construct('surface_altitude')
   >>> orog.equals(orog.copy())
   True


.. _External-variables:

**External variables**
----------------------

----

`External variables`_ are those in a netCDF file that are referred to,
but which are not present in it. Instead, such variables are stored in
other netCDF files known as "external files". External variables may,
however, be incorporated into the field constructs of the dataset, as
if they had actually been stored in the same file, simply by providing
the external file names to the `cfdm.read` function.

This is illustrated with the files ``parent.nc`` (:download:`download
<netcdf_files/parent.nc>`, 2kB) [#files]_:

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

and ``external.nc`` (:download:`download <netcdf_files/external.nc>`,
1kB) [#files]_:

.. code:: bash

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

The dataset in ``parent.nc`` may be read *without* specifying the
external file ``external.nc``. In this case a cell measure construct
is still created, but one without any metadata or data:

.. code:: python

   >>> u = cfdm.read('parent.nc')[0]
   >>> print(u)
   Field: eastward_wind (ncvar%eastward_wind)
   ------------------------------------------
   Data            : eastward_wind(latitude(10), longitude(9)) m s-1
   Dimension coords: latitude(10) = [0.0, ..., 9.0] degrees
                   : longitude(9) = [0.0, ..., 8.0] degrees
   Cell measures   : measure%area (external variable: ncvar%areacella)

   >>> area = u.get_construct('measure%area')
   >>> area
   <CellMeasure: measure%area >
   >>> area.nc_external()
   True
   >>> area.nc_get_variable()
   'areacella'
   >>> area.properties()
   {}
   >>> area.has_data()
   False

If this field construct were to be written to disk using `cfdm.write`,
then the output file would be identical to the original ``parent.nc``
file, i.e. the netCDF variable name of the cell measure construct
("areacella") would be listed by the "external_variables" global
attribute.

However, the dataset may also be read *with* the external file. In
this case a cell measure construct is created with all of the metadata
and data from the external file, as if the netCDF cell measure
variable had been present in the parent dataset:

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
   
If this field construct were to be written to disk using `cfdm.write`
then by default the cell measure construct, with all of its metadata
and data, would be written to the named output file, along with all of
the other constructs. There would be no "external_variables" global
attribute.

In order to write a metadata construct to an external file, and refer
to it with the "external_variables" global attribute in the parent
output file, simply set the status of the cell measure construct to
"external" with its `~CellMeasure.nc_external` method, and provide an
external file name to the `cfdm.write` function:

.. code:: python

   >>> area.nc_external(True)
   False
   >>> cfdm.write(g, 'new_parent.nc', external_file='new_external.nc')


.. _Compression:
   
**Compression**
---------------

----

The CF conventions have support for space saving by identifying
unwanted missing data.  Such compression techniques store the data
more efficiently and result in no precision loss. The CF data model,
however, views arrays that are compressed in their uncompressed
form.

Therefore, the field construct contains domain axis constructs for the
compressed dimensions and presents a view of compressed data in its
uncompressed form, even though their "underlying" arrays (i.e. the
arrays contained in `Data` instances) are compressed. This means that
the cfdm package includes algorithms that are required to uncompress
each type of compressed array.

There are two basic types of compression supported by the CF
conventions: ragged arrays (as used by :ref:`discrete sampling
geometries <Discrete-sampling-geometries>`) and :ref:`compression by
gathering <Gathering>`, each of which has particular implementation
details, but the following access patterns and behaviours apply to
both:

* Whether or not the data are compressed is tested with the
  `~Data.get_compression_type` method of the `Data` instance.
..

* Accessing the data by a call to the `!get_array` method of a field
  or metadata construct returns a numpy array that is
  uncompressed. The underlying array will, however, remain in its
  compressed form. The underlying compressed array may be retrieved as
  a numpy array with the `~Data.get_compressed_array` method of the
  `Data` instance.

..

* A :ref:`subspace <Subspacing>` of a field construct is created with
  indices of the uncompressed form of the data. The new subspace will
  no longer be compressed, i.e. its underlying arrays will be
  uncompressed, but the original data will remain compressed. It
  follows that to uncompress all of the data in a field construct,
  index the field construct with `Ellipsis`.
  
..

* If data elements are modified by :ref:`assigning <Assignment>` to
  indices of the uncompressed form of the data, then the underlying
  compressed array is replaced by its uncompressed form.

..

* If an underlying array is compressed at the time of writing to disk
  with the `cfdm.write` function, then it is written to the file as a
  compressed array, along with the supplementary netCDF variables and
  attributes that are required for the encoding. This means that if a
  dataset using compression is read from disk then it will be written
  back to disk with the same compression, unless data elements have
  been modified by assignment. Any compressed arrays that have been
  modified will be written to an output dataset as uncompressed
  arrays.

Examples of all of the above may be found in the sections on
:ref:`discrete sampling geometries <Discrete-sampling-geometries>` and
:ref:`gathering <Gathering>`.

.. _Discrete-sampling-geometries:
   
**Discrete sampling geometries**
--------------------------------

----

`Discrete sampling geometry (DSG)`_ features may be compressed by
combining them using one of three ragged array representations:
`contiguous`_, `indexed`_ or `indexed contiguous`_.

The count variable that is required to uncompress a contiguous, or
indexed contiguous, ragged array is stored in a `Count` instance and
is accessed with the `~Data.get_count_variable` method of the `Data`
instance.

The index variable that is required to uncompress an indexed, or
indexed contiguous, ragged array is stored in an `Index` instance and
is accessed with the `~Data.get_index_variable` method of the `Data`
instance.

The contiguous case is is illustrated with the file ``contiguous.nc``
(:download:`download <netcdf_files/contiguous.nc>`, 2kB) [#files]_:

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
   >>> print(h.get_array())
   [[0.12 0.05 0.18   --   --   --   --   --   --]
    [0.05 0.11 0.2  0.15 0.08 0.04 0.06   --   --]
    [0.15 0.19 0.15 0.17 0.07   --   --   --   --]
    [0.11 0.03 0.14 0.16 0.02 0.09 0.1  0.04 0.11]]
   >>> h.data.get_compression_type()
   'ragged contiguous'
   >>> print(h.data.get_compressed_array())
   [0.12 0.05 0.18 0.05 0.11 0.2 0.15 0.08 0.04 0.06 0.15 0.19 0.15 0.17 0.07
    0.11 0.03 0.14 0.16 0.02 0.09 0.1 0.04 0.11]
   >>> count_variable = h.data.get_count_variable()
   >>> count_variable
   <Count: long_name:number of observations for this station(4) >
   >>> print(count_variable.get_array())
   [3 7 5 9]

The timeseries for the second station is easily selected by indexing
the "station" axis of the field construct:

.. code:: python
	  
   >>> station = h[1]
   >>> station
   <Field: specific_humidity(ncdim%station(1), ncdim%timeseries(9))>
   >>> print(station.get_array())
   [[0.05 0.11 0.2 0.15 0.08 0.04 0.06 -- --]]

The underlying array of original data remains in compressed form until
data array elements are modified:
   
.. code:: python

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

A construct with an underlying ragged array is created by initialising
a `Data` instance with a ragged array that is stored in one of three
special array objects: `RaggedContiguousArray`, `RaggedIndexedArray`
or `RaggedIndexedContiguousArray`. The following code creates a simple
field construct with an underlying contiguous ragged array:

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
   T = cfdm.Field()
   T.properties({'standard_name': 'air_temperature',
                 'units': 'K',
      	         'featureType': 'timeSeries'})
   
   # Create the domain axis constructs for the uncompressed array
   X = T.set_construct(cfdm.DomainAxis(4))
   Y = T.set_construct(cfdm.DomainAxis(2))
   
   # Set the data for the field
   T.set_data(cfdm.Data(array), axes=[Y, X])
				
The new field construct can now be inspected and written to a netCDF file:

.. code:: python
   
   >>> T
   <Field: air_temperature(cid%domainaxis1(2), cid%domainaxis0(4)) K>
   >>> print(T.get_array())
   [[280.0 282.5    --    --]
    [281.0 279.0 278.0 279.5]]
   >>> T.data.get_compression_type()
   'ragged contiguous'
   >>> print(T.data.get_compressed_array())
   [280.  282.5 281.  279.  278.  279.5]
   >>> count_variable = T.data.get_count_variable()
   >>> count_variable
   <Count: long_name:number of obs for this timeseries(2) >
   >>> print(count_variable.get_array())
   [2 4]
   >>> cfdm.write(T, 'T_contiguous.nc')

The content of the new file is:
  
.. code:: bash

   $ ncdump T_contiguous.nc
   netcdf T_contiguous {
   dimensions:
   	dim = 2 ;
   	element = 6 ;
   variables:
   	int64 count(dim) ;
   		count:long_name = "number of obs for this timeseries" ;
   		count:sample_dimension = "element" ;
   	float air_temperature(element) ;
   		air_temperature:units = "K" ;
   		air_temperature:standard_name = "air_temperature" ;
   
   // global attributes:
		:Conventions = "CF-1.7" ;
		:featureType = "timeSeries" ;
   data:
   
    count = 2, 4 ;
   
    air_temperature = 280, 282.5, 281, 279, 278, 279.5 ;
   }

.. _Gathering:

**Gathering**
-------------

----

`Compression by gathering`_ combines axes of a multidimensional array
into a new, discrete axis whilst omitting the missing values and thus
reducing the number of values that need to be stored.

The list variable that is required to uncompress a gathered array is
stored in a `List` object and is retrieved with the
`~Data.get_list_variable` method of the `Data` instance.

This is illustrated with the file ``gathered.nc`` (:download:`download
<netcdf_files/gathered.nc>`, 1kB) [#files]_:

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
   >>> p.data.get_compression_type()
   'gathered'
   >>> print(p.data.get_compressed_array())
   [[0.000122 0.0008   0.000177 0.000175 0.00058 0.000206 0.0007  ]
    [0.000202 0.000174 0.00084  0.000201 0.0057  0.000223 0.000102]]
   >>> list_variable = p.data.get_list_variable()
   >>> list_variable
   <List: ncvar%landpoint(7) >
   >>> print(list_variable.get_array())
   [1 2 5 7 8 16 18]

Subspaces based on the uncompressed axes of the field construct are
easily created:

.. code:: python
	  
   >>> p[0]
   <Field: precipitation_flux(time(1), latitude(4), longitude(5)) kg m2 s-1>
   >>> p[1, :, 3:5]
   <Field: precipitation_flux(time(1), latitude(4), longitude(2)) kg m2 s-1>

The underlying array of original data remains in compressed form until
data array elements are modified:
   
.. code:: python

   >>> p.data.get_compression_type()
   'gathered'
   >>> p.data[1] = -9
   >>> p.data.get_compression_type()
   ''
   
A construct with an underlying gathered array is created by
initializing a `Data` instance with a gathered array that is stored in
the special `GatheredArray` array object. The following code creates a
simple field construct with an underlying gathered array:

.. code:: python

   import numpy	  
   import cfdm

   # Define the gathered values
   gathered_array = numpy.array([[2, 1, 3], [4, 0, 5]],
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
   P = cfdm.Field(properties={'standard_name': 'precipitation_flux',
                              'units': 'kg m-2 s-1'})

   # Create the domain axis constructs for the uncompressed array
   T = P.set_construct(cfdm.DomainAxis(2))
   Y = P.set_construct(cfdm.DomainAxis(3))
   X = P.set_construct(cfdm.DomainAxis(2))

   # Set the data for the field
   P.set_data(cfdm.Data(array), axes=[T, Y, X])			      

Note that, because compression by gathering acts on a subset of the
array dimensions, it is necessary to state the position of the
compressed dimension in the compressed array (with the
"compressed_dimension" parameter of the `GatheredArray`
initialisation).

The new field construct can now be inspected and written a netCDF file:

.. code:: python
   
   >>> P
   <Field: precipitation_flux(cid%domainaxis0(2), cid%domainaxis1(3), cid%domainaxis2(2)) kg m-2 s-1>
   >>> print(P.get_array())
   [[[ -- 2.0]
     [ --  --]
     [1.0 3.0]]

    [[ -- 4.0]
     [ --  --]
     [0.0 5.0]]]
   >>> P.data.get_compression_type()
   'gathered'
   >>> print(P.data.get_compressed_array())
   [[2. 1. 3.]
    [4. 0. 5.]]
   >>> list_variable = P.data.get_list_variable()
   >>> list_variable 
   <List: (3) >
   >>> print(list_variable.get_array())
   [1 4 5]
   >>> cfdm.write(P, 'P_gathered.nc')

The content of the new file is:
   
.. code:: bash

   $ ncdump P_gathered.nc
   netcdf P_gathered {
   dimensions:
   	dim = 2 ;
   	dim_1 = 3 ;
   	dim_2 = 2 ;
   	list = 3 ;
   variables:
   	int64 list(list) ;
   		list:compress = "dim_1 dim_2" ;
   	float precipitation_flux(dim, list) ;
   		precipitation_flux:units = "kg m-2 s-1" ;
   		precipitation_flux:standard_name = "precipitation_flux" ;
   
   // global attributes:
   		:Conventions = "CF-1.7" ;
   data:
   
    list = 1, 4, 5 ;
   
    precipitation_flux =
     2, 1, 3,
     4, 0, 5 ;
   }

----

.. rubric:: Footnotes

.. [#notebook] The Jupyter notebook is quite long. To aid navigation
               it has been written so that it may optionally be used
               with the "Collapsible Headings" Jupyter notebook
               extension. See
               https://jupyter-contrib-nbextensions.readthedocs.io/en/latest
               for details.
..

.. [#files] The tutorial files may be also found in the `downloads
            directory
            <https://github.com/NCAS-CMS/cfdm/tree/master/docs/_downloads>`_
            of the on-line code repository.

..

.. [#opendap2] Requires the netCDF4 python package to have been built
               with OPeNDAP support enabled. See
               http://unidata.github.io/netcdf4-python for details.

..
       
.. [#language] In the terminology of the CF data model, a "construct"
               is an abstract concept which is distinct from its
               realization, e.g. a `Field` instance is not, strictly
               speaking, a field construct. However, the distinction
               is moot and the descriptive language used in this
               tutorial is greatly simplified by allowing the term
               "construct" to mean "class instance" (e.g. "field
               construct" means "`Field` instance"), and this
               convention is applied throughout this tutorial. The
               phrase "CF data model construct" is used on the few
               occasions when the original abstract meaning is
               intended.
	    

.. External links to the CF conventions
   
.. _External variables:               http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#external-variables
.. _Discrete sampling geometry (DSG): http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#discrete-sampling-geometries
.. _incomplete multidimensional form: http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#_incomplete_multidimensional_array_representation
.. _Compression by gathering:         http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#compression-by-gathering
.. _contiguous:                       http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#_contiguous_ragged_array_representation
.. _indexed:                          http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#_indexed_ragged_array_representation
.. _indexed contiguous:               http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#_ragged_array_representation_of_time_series_profiles
