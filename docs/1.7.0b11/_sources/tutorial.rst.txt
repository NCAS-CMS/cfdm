.. currentmodule:: cfdm
.. default-role:: obj

.. _Tutorial:

**Tutorial**
============

----

Version |release| for version |version| of the CF conventions.
 
The code examples in this tutorial are available in an **IPython
Jupyter notebook** (:download:`download <notebooks/tutorial.ipynb>`,
70kB) [#files]_, [#notebook]_.

.. _Import:

**Import**
----------

----

The cfdm package is imported as follows:

.. code-block:: python
   :caption: *Import the cfdm package.*

   >>> import cfdm

.. _CF-version:

**CF version**
--------------

----

The version of the `CF conventions <http://cfconventions.org>`_ and
the :ref:`CF data model <CF-data-model>` being used may be found with
the `cfdm.CF` function:

.. code-block:: python
   :caption: *Retrieve the version of the CF conventions.*
      
   >>> cfdm.CF()
   '1.7'

This indicates which version of the CF conventions are represented by
this release of the cfdm package, and therefore the version can not be
changed.

.. _Reading-datasets:

**Reading datasets**
--------------------

----

The `cfdm.read` function reads a `netCDF
<https://www.unidata.ucar.edu/software/netcdf/>`_ file from disk, or
from an `OPeNDAP <https://www.opendap.org/>`_ URL [#opendap2]_, and
returns the contents as a list of zero or more `Field` class
instances, each of which represents a field construct. (Henceforth,
the phrase "field construct" will be assumed to mean "`Field`
instance".) The list contains a field construct to represent each of
the CF-netCDF data variables in the file.

All formats of netCDF3 and netCDF4 files can be read.

For example, to read the file ``file.nc`` (:download:`download
<netcdf_files/file.nc>`, 9kB) [#files]_, which contains two field
constructs:

.. code-block:: python
   :caption: *Read file.nc and show that the result is a two-element
             list.*
		
   >>> x = cfdm.read('file.nc')
   >>> type(x)
   <type 'list'>
   >>> len(x)
   2

Descriptive properties are always read into memory, but `lazy loading
<https://en.wikipedia.org/wiki/Lazy_loading>`_ is employed for all
data arrays, which means that no data is read into memory until the
data is required for inspection or to modify the array contents. This
maximises the number of field constructs that may be read within a
session, and makes the read operation fast.

The `cfdm.read` function has optional parameters to

* allow the user to provide files that contain :ref:`external
  variables <External-variables>`;

* request :ref:`extra field constructs to be created from "metadata"
  netCDF variables <Creation-by-reading>`, i.e. those that are
  referenced from CF-netCDF data variables, but which are not regarded
  by default as data variables in their own right; and 

* display information and warnings about the mapping of the netCDF
  file contents to CF data model constructs.

.. _CF-compliance:

**CF-compliance**
^^^^^^^^^^^^^^^^^
  
If the dataset is partially CF-compliant to the extent that it is not
possible to unambiguously map an element of the netCDF dataset to an
element of the CF data model, then a field construct is still
returned, but may be incomplete. This is so that datasets which are
partially conformant may nonetheless be modified in memory and written
to new datasets. Such "structural" non-compliance would occur, for
example, if the "coordinates" attribute of a CF-netCDF data variable
refers to another variable that does not exist, or refers to a
variable that spans a netCDF dimension that does not apply to the data
variable. Other types of non-compliance are not checked, such whether
or not controlled vocabularies have been adhered to. The structural
compliance of the dataset may be checked with the
`~cfdm.Field.dataset_compliance` method of the field construct, as
well as optionally displayed when the dataset is read.

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

.. code-block:: python
   :caption: *Inspect the contents of the two field constructs from
             the dataset and create a Python variable for each of
             them.*
      
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

.. code-block:: python
  :caption: *Inspect the contents of the two field constructs with
            medium detail.*
   
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

.. code-block:: python
  :caption: *Inspect the contents of the two field constructs with
            full detail.*

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
^^^^^^^^^^

The description for every field construct in a file can also be
generated from the command line, with minimal, medium or full detail,
by using the ``cfdump`` tool, for example:

.. code-block:: shell
   :caption: *Use cfdump on the command line to inspect the field
             constructs contained in a dataset. The "-s" option
             requests short, minimal detail as output.*
	     
   $ cfdump -s file.nc
   Field: specific_humidity(latitude(5), longitude(8)) 1
   Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K

.. _Properties:

**Properties**
--------------

----

Descriptive properties that apply to field construct as a whole may be
retrieved with the `~Field.properties` method:

.. code-block:: python
   :caption: *Retrieve all of the descriptive properties*
	     
   >>> t.properties()
   {'Conventions': 'CF-1.7',
    'project': 'research',
    'standard_name': 'air_temperature',
    'units': 'K'}
   
Individual properties may be accessed and modified with the
`~Field.del_property`, `~Field.get_property`, `~Field.has_property`,
and `~Field.set_property` methods:

.. code-block:: python
   :caption: *Check is a property exists, retrieve its value, delete
             it and then set it to a new value.*
      
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

.. code-block:: python
   :caption: *Delete all the existing properties, saving the original
             ones, and replace them with two new properties; finally
             reinstate the original ones.*
	     
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

All of the methods related to the properties are listed :ref:`here
<Field-Properties>`.

.. _Metadata-constructs-1:

**Metadata constructs 1**
-------------------------

----

The metadata constructs describe the field construct that contains
them. Each :ref:`CF data model metadata construct <CF-data-model>` has
a corresponding cfdm class:

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

Metadata constructs of a particular type can be retrieved with the
following methods of the field construct:

==============================  =====================  
Method                          Metadata constructs    
==============================  =====================  
`~Field.domain_axes`            Domain axes            
`~Field.dimension_coordinates`  Dimension coordinates  
`~Field.auxiliary_coordinates`  Auxiliary coordinates  
`~Field.coordinate_references`  Coordinate references  
`~Field.domain_ancillaries`     Domain ancillaries     
				                               
`~Field.cell_measures`          Cell measures          
`~Field.field_ancillaries`      Field ancillaries      
				                              
`~Field.cell_methods`           Cell methods                               
==============================  =====================  

Each of these methods returns a dictionary whose values are the
metadata constructs of one type, keyed by a unique identifier called a
"construct key":

.. code-block:: python
   :caption: *Retrieve the field construct's coordinate reference,
             dimension coordinate and domain axis constructs.*
	     
   >>> t.coordinate_references()
   {'coordinatereference0': <CoordinateReference: atmosphere_hybrid_height_coordinate>,
    'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>}
   >>> t.dimension_coordinates()
   {'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
    'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}
   >>> t.domain_axes()
   {'domainaxis0': <DomainAxis: 1>,
    'domainaxis1': <DomainAxis: 10>,
    'domainaxis2': <DomainAxis: 9>,
    'domainaxis3': <DomainAxis: 1>}

The construct keys (e.g. ``'domainaxis1'``) are usually generated
internally and are unique within the field construct. However,
construct keys may be different for equivalent metadata constructs from
different field constructs, and for different Python sessions.

Metadata constructs of all types may be returned by the
`~Field.constructs` method of the field construct:

.. code-block:: python
   :caption: *Retrieve all of the field construct's metadata
             constructs.*

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

The `~Field.constructs` method has optional parameters to filter the
output by specifying criteria on the contents of metadata
constructs. See the :ref:`further section on metadata constructs
<Metadata-constructs-2>` for more details.

.. _Data:

**Data**
--------

----

The field construct's data array is stored in a `Data` class instance
that is accessed with the `~Field.get_data` method of the field
construct.

.. code-block:: python
   :caption: *Retrieve the data and inspect it, showing the shape and
             some illustrative values.*
		
   >>> d = t.get_data()
   >>> d
   <Data(1, 10, 9): [[[262.8, ..., 269.7]]] K>

The data array may be retrieved as an independent (possibly masked)
`numpy` array with the `~Field.get_array` method:

.. code-block:: python
   :caption: *Retrieve the data as a numpy array.*
      
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
access attributes and methods of the `Data` instance.

.. code-block:: python
   :caption: *Inspect the data type, number of dimensions, dimension
             sizes and number of elements of the data array.*
	     
   >>> t.data.dtype
   dtype('float64')
   >>> t.data.ndim
   3
   >>> t.data.shape
   (1, 10, 9)
   >>> t.data.size
   90

All of the methods and attributes related to the data are listed
:ref:`here <Field-Data>`.

.. _Data-axes:

**Data axes**
^^^^^^^^^^^^^

The data array of the field construct spans all the domain axis
constructs with the possible exception of any size one domain axis
constructs. The domain axis constructs spanned by the field
construct's data are found with the `~Field.get_data_axes` method of
the field construct. For example, the data of the field construct
``t`` does not span the size one domain axis construct with key
``'domainaxis3'``:

.. code-block:: python
   :caption: *Show which data axis constructs are spanned by the field
             construct's data.*
	    
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
   
.. _Indexing:

**Indexing**
^^^^^^^^^^^^

When a `Data` instance is indexed a new instance is created for the
part of the data defined by the indices. Indexing follows rules that
are very similar to the `numpy indexing rules
<https://docs.scipy.org/doc/numpy/reference/arrays.indexing.html>`_,
the only differences being:

* An integer index *i* specified for a dimension reduces the size of
  this dimension to unity, taking just the *i*\ -th element, but keeps
  the dimension itself, so that the rank of the array is not reduced.

..

* When two or more dimensions' indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same
  behaviour as indexing on a ``Variable`` object of the `netCDF4
  package <http://unidata.github.io/netcdf4-python>`_.

.. code-block:: python
   :caption: *Create new data by indexing and show the shape
             corresponding to the indices.*
	     
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

Values can be changed by assigning to elements selected by indices of
the `Data` instance using rules that are very similar to the `numpy
indexing rules
<https://docs.scipy.org/doc/numpy/reference/arrays.indexing.html>`_,
the only difference being:

* When two or more dimensions' indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same
  behaviour as indexing on a ``Variable`` object of the `netCDF4
  package <http://unidata.github.io/netcdf4-python>`_.

A single value may be assigned to any number of elements.
  
.. code-block:: python
   :caption: *Set a single element to -1, a "column" of elements
             to -2 and a "square" of elements to -3.*
	     
   >>> import numpy
   >>> t.data[:, 0, 0] = -1
   >>> t.data[:, :, 1] = -2
   >>> t.data[..., 6:3:-1, 3:6] = -3
   >>> print(t.get_array())
   [[[ -1.0  -2.0 279.8 269.5 260.9 265.0 263.5 278.9 269.2]
     [272.7  -2.0 279.5 278.9 263.8 263.3 274.2 265.7 279.5]
     [269.7  -2.0 273.4 274.2 279.6 270.2 280.0 272.5 263.7]
     [261.7  -2.0 270.8 260.3 265.6 279.4 276.9 267.6 260.6]
     [264.2  -2.0 262.5  -3.0  -3.0  -3.0 270.4 268.6 275.3]
     [263.9  -2.0 272.1  -3.0  -3.0  -3.0 260.0 263.5 270.2]
     [273.8  -2.0 268.5  -3.0  -3.0  -3.0 270.6 273.0 270.6]
     [267.9  -2.0 279.8 260.3 261.2 275.3 271.2 260.8 268.9]
     [270.9  -2.0 273.2 261.7 271.6 265.8 273.0 278.5 266.4]
     [276.4  -2.0 276.3 266.1 276.1 268.1 277.0 273.4 269.7]]]

An array of values can be assigned, as long as it is broadcastable to
the shape defined by the indices, using the `numpy broadcasting rules
<https://docs.scipy.org/doc/numpy/user/basics.broadcasting.html>`_.

.. code-block:: python
   :caption: *Overwrite the square of values of -3 with the numbers 0
             to 8, and set the corners of a different square to be
             either -4 or -5.*
	     
   >>> t.data[..., 6:3:-1, 3:6] = numpy.arange(9).reshape(3, 3)
   >>> t.data[0, [2, 9], [4, 8]] =  cfdm.Data([[-4, -5]])
   >>> print(t.get_array())
   [[[ -1.0  -2.0 279.8 269.5 260.9 265.0 263.5 278.9 269.2]
     [272.7  -2.0 279.5 278.9 263.8 263.3 274.2 265.7 279.5]
     [269.7  -2.0 273.4 274.2  -4.0 270.2 280.0 272.5  -5.0]
     [261.7  -2.0 270.8 260.3 265.6 279.4 276.9 267.6 260.6]
     [264.2  -2.0 262.5   6.0   7.0   8.0 270.4 268.6 275.3]
     [263.9  -2.0 272.1   3.0   4.0   5.0 260.0 263.5 270.2]
     [273.8  -2.0 268.5   0.0   1.0   2.0 270.6 273.0 270.6]
     [267.9  -2.0 279.8 260.3 261.2 275.3 271.2 260.8 268.9]
     [270.9  -2.0 273.2 261.7 271.6 265.8 273.0 278.5 266.4]
     [276.4  -2.0 276.3 266.1  -4.0 268.1 277.0 273.4  -5.0]]]

Data array elements may be set to missing values by assigning them to
`numpy.ma.masked`. Missing values may be unmasked by assigning them to
any other value.

.. code-block:: python
   :caption: *Set a column of elements to missing values, and then
             change one of them back to a non-missing value.*
	     
   >>> t.data[0, :, -2] = numpy.ma.masked
   >>> t.data[0, 5, -2] = -6
   >>> print(t.get_array())
   [[[ -1.0  -2.0 279.8 269.5 260.9 265.0 263.5    -- 269.2]
     [272.7  -2.0 279.5 278.9 263.8 263.3 274.2    -- 279.5]
     [269.7  -2.0 273.4 274.2  -4.0 270.2 280.0    --  -5.0]
     [261.7  -2.0 270.8 260.3 265.6 279.4 276.9    -- 260.6]
     [264.2  -2.0 262.5   6.0   7.0   8.0 270.4    -- 275.3]
     [263.9  -2.0 272.1   3.0   4.0   5.0 260.0  -6.0 270.2]
     [273.8  -2.0 268.5   0.0   1.0   2.0 270.6    -- 270.6]
     [267.9  -2.0 279.8 260.3 261.2 275.3 271.2    -- 268.9]
     [270.9  -2.0 273.2 261.7 271.6 265.8 273.0    -- 266.4]
     [276.4  -2.0 276.3 266.1  -4.0 268.1 277.0    --  -5.0]]]

**Manipulating dimensions**
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The dimensions of a field construct's data may be reordered, have size
one dimensions removed and have new new size one dimensions included
by using the following field construct methods:

=========================  ===========================================
Method                     Description
=========================  ===========================================
`~Field.transpose`         Reorder data dimensions

`~Field.squeeze`           Remove size one data dimensions
	   
`~Field.insert_dimension`  Insert a new size one data dimension. The
                           new dimension must correspond to an
                           existing size one domain axis construct.
=========================  ===========================================

.. code-block:: python
   :caption: *Remove all size one dimensions from the data, noting
             that metadata constructs which span the corresponding
             domain axis construct are not affected.*

   >>> t
   <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>
   >>> t2 = t.squeeze()
   >>> t2
   <Field: air_temperature(grid_latitude(10), grid_longitude(9)) K>   
   >>> t2.dimension_coordinates()
   {'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
    'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

.. code-block:: python
   :caption: *Insert a new size one dimension, corresponding to a size
             one domain axis construct, and then reorder the
             dimensions.*

   >>> t3 = t2.insert_dimension(axis='domainaxis3', position=1)
   >>> t3
   <Field: air_temperature(grid_latitude(10), time(1), grid_longitude(9)) K>  
   >>> t3.transpose([2, 0, 1])
   <Field: air_temperature(grid_longitude(9), grid_latitude(10), time(1)) K>

.. _Subspacing:

**Subspacing**
--------------

----

Creation of a new field construct which spans a subspace of the domain
of an existing field construct is achieved by indexing the field
itself, rather than its `Data` instance. This is because the operation
must also subspace any metadata constructs of the field construct
(e.g. coordinate metadata constructs) which span any of the domain
axis constructs that are affected. The new field construct is created
with the same properties as the original field. Subspacing uses the
same :ref:`cfdm indexing rules <Indexing>` that apply to the `Data`
class.

.. code-block:: python
  :caption: *Create a new field whose domain spans the first longitude
            of the original, and with a reversed latitude axis.*

   >>> print(q)
   Field: specific_humidity (ncvar%q)
   ----------------------------------
   Data            : specific_humidity(latitude(5), longitude(8)) 1
   Cell methods    : area: mean
   Dimension coords: time(1) = [2019-01-01 00:00:00]
                   : latitude(5) = [-75.0, ..., 75.0] degrees_north
                   : longitude(8) = [22.5, ..., 337.5] degrees_east

   >>> new = q[::-1, 0]
   >>> print(new)
   Field: specific_humidity (ncvar%q)
   ----------------------------------
   Data            : specific_humidity(latitude(5), longitude(1)) 1
   Cell methods    : area: mean
   Dimension coords: time(1) = [2019-01-01 00:00:00]
                   : latitude(5) = [75.0, ..., -75.0] degrees_north
                   : longitude(1) = [22.5] degrees_east


.. _Metadata-constructs-2:

**Metadata constructs 2**
-------------------------

----

Further to the functionality described in the :ref:`first section on
metadata constructs <Metadata-constructs-1>`, the `~Field.constructs`
method of the field construct has optional parameters to filter the
metadata constructs by

* metadata construct type,

* property value,

* whether the data array spans particular domain axis constructs,

* measure value (for cell measure constructs),

* construct key, and

* netCDF variable or dimension name (see the :ref:`netCDF interface
  <NetCDF-interface>`).
 
.. code-block:: python
   :caption: *Get constructs by their type*.
	  
   >>> t.constructs(construct_type='dimension_coordinate')
   {'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
    'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

.. code-block:: python
   :caption: *Get constructs by their properties*.

   >>> t.constructs(properties={'standard_name': 'air_temperature standard_error'})
   {'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}
   >>> t.constructs(properties=[{'standard_name': 'air_temperature standard_error'},
   ...                          {'units': 'm'}])
   {'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
    'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>,
    'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}

.. code-block:: python
   :caption: *Get constructs by the domain axis constructs spanned by
             their data.*

   >>> t.constructs(axis='domainaxis1')
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
    'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
    'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >,
    'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>,
    'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}

.. code-block:: python
   :caption: *Get cell measure constructs by their "measure".*
	     
   >>> t.constructs(measure='area')
   {'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>}

.. code-block:: python
   :caption: *Get constructs that meet a variety of criteria.*
	     
   >>> t.constructs(construct_type='auxiliary_coordinate',
   ...              axis='domainaxis1',
   ...              properties={'units': 'degrees_E'})
   {'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>}

Selection by construct key is useful for systematic metadata construct
access, or for when a metadata construct is not identifiable by other
means.

.. code-block:: python
   :caption: *Get constructs by constructs key.*

   >>> t.constructs(key='domainancillary2')
   {'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>}
   >>> t.constructs(key='cellmethod1')
   {'cellmethod1': <CellMethod: domainaxis3: maximum>}
   >>> t.constructs(key=['auxiliarycoordinate2', 'cellmeasure0'])
   {'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >,
    'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>}
   >>> t.constructs(key='auxiliarycoordinate999')
   {}

A less verbose, and often more convenient, method of selection is by
metadata construct "name". A construct's name is typically the
description that is displayed when the construct is inspected. For
example, the :ref:`three auxiliary coordinate constructs
<Medium-detail>` in the field construct ``t`` have names
``'latitude'``, ``'longitude'`` and ``'long_name:Grid latitude
name'``. Selection by name does not require a keyword parameter,
although the keyword ``name`` can be used:

.. code-block:: python
   :caption: *Get constructs by their name.*
	
   >>> t.constructs('latitude')
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>}
   >>> t.constructs('long_name:Grid latitude name')
   {'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >}
   >>> t.constructs(name='longitude')
   {'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>}
   >>> t.constructs('measure%area')
   {'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>}

More generally, a construct name may be constructed by any of

* The value of the "standard_name" property, e.g. ``'air_temperature'``,
* The value of any property, preceded by the property name and a
  colon, e.g. ``'long_name:Air Temperature'``,
* The cell measure, preceded by "measure%", e.g. ``'measure%volume'``
* The netCDF variable name, preceded by "ncvar%",
  e.g. ``'ncvar%tas'`` (see the :ref:`netCDF interface
  <NetCDF-interface>`), and
* The netCDF dimension name, preceded by "ncdim%" e.g. ``'ncdim%z'``
  (see the :ref:`netCDF interface <NetCDF-interface>`).

Each construct has a `!name` method that, by default, returns the
least ambiguous name, as defined in the each method's documentation.
  
Note that providing a ``type`` parameter with no other selection
parameters is equivalent to using the particular field construct
method for retrieving that type of metadata construct:

.. code-block:: python
   :caption: *There are bespoke methods for retrieving constructs by
             type.*
		
   >>> t.constructs(construct_type='cell_measure')
   {'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>}
   >>> t.cell_measures()
   {'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>}

If no constructs match the given criteria, then an empty dictionary is
returned:
   
.. code-block:: python
   :caption: *If no constructs meet the criteria then an empty
             dictionary is returned.*
	
   >>> t.constructs('radiation_wavelength')
   {}

.. _Accessing-an-individual-metadata-construct:

**Accessing an individual metadata construct**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   
An individual metadata construct may be returned, without its
construct key, via the `~Field.get_construct` method of the field
construct, which supports the same filtering options as the
`~Field.constructs` method. The existence of a metadata construct may
be checked with the `~Field.has_construct` method and a construct may
be removed with the `~Field.del_construct` method.

.. code-block:: python
   :caption: *Check the existence of, and retrieve, the "latitude"
             metadata construct.*

   >>> t.has_construct('latitude')
   True
   >>> t.get_construct('latitude')
   <AuxiliaryCoordinate: latitude(10, 9) degrees_N>

.. code-block:: python
   :caption: *Get the metadata construct with units of "km2", find its
             name and then check that it can be also be retrieved via
             its name.*

   >>> c = t.get_construct('units:km2')
   >>> c
   <CellMeasure: measure%area(9, 10) km2>
   >>> c.name()
   'measure%area'
   >>> t.get_construct('measure%area')
   <CellMeasure: measure%area(9, 10) km2>
   
.. code-block:: python
   :caption: *By default an exception is raised if there is not a
             unique construct that meets the criteria. Alternatively,
             the value of the "default" parameter is returned.*
	     
   >>> t.get_construct(measure='volume')
   ValueError: No construct meets criteria
   >>> t.constructs('units:degrees')
   {'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>}
   >>> print(t.get_construct('units:degrees', default=None))
   None
   >>> t.has_construct('units:degrees')
   False

The key of a metadata construct may be found with the
`~Field.get_constructs_key` method of the field construct:

.. code-block:: python
   :caption: *Get the construct key of the construct with name
             "latitude".*

   >>> t.get_construct_key('latitude')
   'auxiliarycoordinate0'
   
.. _Metadata-construct-properties:

**Metadata construct properties**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Metadata constructs share the :ref:`same API as the field construct
<Properties>` for accessing their properties:

.. code-block:: python
   :caption: *Retrieve the "longitude" metadata construct, set a new
             property, and then inspect all of the properties.*

   >>> lon = q.get_construct('longitude')   
   >>> lon
   <DimensionCoordinate: longitude(8) degrees_east>
   >>> lon.set_property('long_name', 'Longitude')
   >>> lon.properties()
   {'units': 'degrees_east',
    'long_name': 'Longitude',
    'standard_name': 'longitude'}

.. _Metadata-construct-data:

**Metadata construct data**
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Metadata constructs share the :ref:`a similar API as the field
construct <Data>` as the field construct for accessing their data:

.. code-block:: python
   :caption: *Retrieve the "longitude" metadata construct, inspect its
             data, change the third element of the array, and get the
             data as a numpy array.*
	     
   >>> lon = q.get_construct('longitude')   
   >>> lon
   <DimensionCoordinate: longitude(8) degrees_east>
   >>> lon.get_data()
   <Data(8): [22.5, ..., 337.5] degrees_east>
   >>> lon.data[2]
   <Data(1): [112.5] degrees_east>
   >>> lon.data[2] = 133.33
   >>> print(lon.get_array())
   [22.5 67.5 133.33 157.5 202.5 247.5 292.5 337.5]

The domain axis constructs spanned by a metadata construct's data are
found with the `~Field.constructs_data_axes` method of the field
construct:

.. code-block:: python
   :caption: *Find the construct keys of the domain axis constructs
             spanned by the data of each metadata construct.*

   >>> t.constructs_data_axes()
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

A size one domain axis construct that is *not* spanned by the field
construct's data may still be spanned by the data of metadata
constructs. For example, the data of the field construct ``t``
:ref:`does not span the size one domain axis construct <Data-axes>`
with key ``'domainaxis3'``, but this domain axis construct is spanned
by a "time" dimension coordinate construct (with key
``'dimensioncoordinate3'``). Such a dimension coordinate (i.e. one
that applies to a domain axis construct that is not spanned by the
field construct's data) corresponds to a CF-netCDF scalar coordinate
variable.

.. _Domain:

**Domain**
----------

----

The :ref:`domain of the CF data model <CF-data-model>` is *not* a
construct, but is defined collectively by various other metadata
constructs included in the field construct. It is represented by the
`Domain` class. The domain instance may be accessed with the
`~Field.get_domain` method of the field construct.

.. code-block:: python
   :caption: *Get the domain, and inspect it.*

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
attributes and methods of the domain instance.

.. code-block:: python
   :caption: *Change a property of a metadata construct of the domain
             and show that this change appears in the same metadata
             data construct of the parent field, and vice versa.*

   >>> domain = t.domain
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

All of the methods and attributes related to the domain are listed
:ref:`here <Field-Domain>`.

.. _Domain-axes:

**Domain axes**
---------------

----

A domain axis metadata construct specifies the number of points along
an independent axis of the field construct's domain and is stored in a
`~cfdm.DomainAxis` instance. The size of the axis is retrieved with
the `~cfdm.DomainAxis.get_size()` method of the domain axis construct.

.. code-block:: python
   :caption: *Get the size of a domain axis construct.*

   >>> q.domain_axes()
   {'domainaxis0': <DomainAxis: 5>,
    'domainaxis1': <DomainAxis: 8>,
    'domainaxis2': <DomainAxis: 1>}
   >>> d = q.get_construct(key='domainaxis1')
   >>> d.get_size()
   8

.. _Coordinates:
		
**Coordinates**
---------------

----

There are two types of coordinate construct, dimension and
auxiliary coordinate constructs, which can be retrieved together with
the `~cfdm.Field.coordinates` method of the field construct.

.. code-block:: python
   :caption: *Retrieve both types of coordinate constructs.*
      
   >>> t.coordinates()
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
    'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
    'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >,
    'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
    'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

A coordinate construct may contain an array of cell bounds that
provides the extent of each cell by defining the locations of the cell
vertices. This is in addition to the main data array that contains a
grid point location for each cell. The cell bounds are stored in a
`Bounds` class instance that is accessed with the
`~Coordinate.get_bounds` method, or `~Coordinate.bounds` attribute the
coordinate construct.

A `Bounds` instance shares the :ref:`the same API as the field
construct <Data>` for accessing its data.

.. code-block:: python
   :caption: *Get the Bounds instance of a coordinate construct and
             inspect its data.*
      
   >>> lon = t.get_construct('grid_longitude')
   >>> bounds = lon.get_bounds()
   >>> bounds
   <Bounds: grid_longitude(9, 2) >
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

The `Bounds` instance inherits the descriptive properties from its
parent coordinate construct, but it may also have its own properties
(although setting these is not recommended).
    
.. code-block:: python
   :caption: *Inspect the inherited and bespoke properties of a Bounds
             instance.*
      
   >>> bounds.inherited_properties()
   {'standard_name': 'grid_longitude',
    'units': 'degrees'}  
   >>> bounds.properties()
   {}

.. _Domain-ancillaries:
		
**Domain ancillaries**
----------------------

----

A domain ancillary construct provides information which is needed for
computing the location of cells in an alternative :ref:`coordinate
system <Coordinate-systems>`. If a domain ancillary construct provides
extra coordinates then it may contain cell bounds in addition to its
main data array.

.. code-block:: python
   :caption: *Get the data and bounds data of a domain ancillary
             construct.*
      
   >>> a = t.get_construct(key='domainancillary0')
   >>> print(a.get_array)
   [10.]
   >>> bounds = a.get_bounds()
   >>> print(bounds.get_array())
   [[ 5. 15.]]

.. _Coordinate-systems:

**Coordinate systems**
----------------------

A field construct may contain various coordinate systems. Each
coordinate system is either defined by a coordinate reference
construct that relates dimension coordinate, auxiliary coordinate and
domain ancillary constructs (as is the case for the field construct
``t``), or is inferred from dimension and auxiliary coordinate
constructs alone (as is the case for the field construct ``q``).

A coordinate reference construct contains

* references (by construct keys) to the dimension and auxiliary
  coordinate constructs to which it applies, accessed with the
  `~CoordinateReference.coordinates` method of the coordinate
  reference construct;

.. code-block:: python
   :caption: *Select the vertical coordinate system construct and
             inspect its coordinate constructs. (Note that the
             "construct_type" parameter is required since there is
             also a dimension coordinate construct with the same
             name.)*
     
   >>> crs = t.get_construct('atmosphere_hybrid_height_coordinate',
   ...                       construct_type='coordinate_reference')
   >>> crs
   <CoordinateReference: atmosphere_hybrid_height_coordinate>
   >>> crs.dump()
   Coordinate Reference: atmosphere_hybrid_height_coordinate
       Coordinate conversion:computed_standard_name = altitude
       Coordinate conversion:standard_name = atmosphere_hybrid_height_coordinate
       Coordinate conversion:a = domainancillary0
       Coordinate conversion:b = domainancillary1
       Coordinate conversion:orog = domainancillary2
       Datum:earth_radius = 6371007
       Coordinate: dimensioncoordinate0
   >>> crs.coordinates()
   {'dimensioncoordinate0'}

* the zeroes of the dimension and auxiliary coordinate constructs
  which define the coordinate system, stored in a `Datum` instance,
  which is accessed with the `~CoordinateReference.get_datum` method,
  or `~CoordinateReference.datum` attribute, of the coordinate
  reference construct; and

.. code-block:: python
   :caption: *Get the datum and inspect its parameters.*
	     
   >>> crs.get_datum()
   <Datum: Parameters: earth_radius>
   >>> crs.datum.parameters()
   {'earth_radius': 6371007}
   
* a formula for converting coordinate values taken from the dimension
  or auxiliary coordinate constructs to a different coordinate system,
  stored in a `CoordinateConversion` class instance, which is accessed
  with the `~CoordinateReference.get_coordinate_conversion` method,
  or `~CoordinateReference.coordinate_conversion` attribute, of the
  coordinate reference construct.

.. code-block:: python
   :caption: *Get the coordinate conversion and inspect its parameters
             and referenced domain ancillary constructs.*
	     
   >>> crs.get_coordinate_conversion()
   <CoordinateConversion: Parameters: computed_standard_name, standard_name; Ancillaries: a, b, orog>
   >>> crs.coordinate_conversion.parameters()
   {'computed_standard_name': 'altitude',
    'standard_name': 'atmosphere_hybrid_height_coordinate'}
   >>> crs.coordinate_conversion.domain_ancillaries()
   {'a': 'domainancillary0',
    'b': 'domainancillary1',
    'orog': 'domainancillary2'}    

.. _Cell-methods:
   
**Cell methods**
----------------

A cell method construct describes how the data represent the variation
of the physical quantity within the cells of the domain and is stored
in a `~cfdm.CellMethod` instance. A field constructs allows multiple
cell method constructs to be recorded. The application of cell methods
is not commutative (e.g. a mean of variances is generally not the same
as a variance of means), so the `~cfdm.Field.cell_methods` method of
the field construct returns an ordered dictionary of constructs. The
order is the same as that in which cell method constructs were added
to the field construct during :ref:`field construct creation
<Field-construct-creation>`.

.. code-block:: python
   :caption: *Inspect the cell methods. The description follows the CF
             conventions for cell_method attribute strings, apart from
             the use of construct keys instead of netCDF variable
             names for cell method axes identification.*
	     
   >>> t.cell_methods()
   OrderedDict([('cellmethod0', <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>),
                ('cellmethod1', <CellMethod: domainaxis3: maximum>)])

The axes to which the method applies, the method itself, and any
qualifying properties are accessed with the
`~cfdm.CellMethod.get_axes`, `~cfdm.CellMethod.get_method`,
`~cfdm.CellMethod.properties`, and `~cfdm.CellMethod.get_property`
methods of methods of the cell method construct.

.. code-block:: python
   :caption: *Get the domain axes constructs to which the cell method
             construct applies, and the method and other properties.*
     
   >>> cm = t.get_construct(key='cellmethod0')
   >>> cm
   <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>)
   >>> cm.get_axes()
   ('domainaxis1', 'domainaxis2')
   >>> cm.get_method()
   'mean'
   >>> cm.properties()
   {'interval': [<Data(): 0.1 degrees>], 'where': 'land'}
   >>> cm.get_property('where')
   'land'

		
.. _Field-construct-creation:

**Field construct creation**
----------------------------

----

There are three methods for creating a field construct in memory:

* :ref:`Manual creation <Manual-creation>`: Instantiate instances of
  field and metadata construct classes and manually provide the
  connections between them.

..

* :ref:`Creation by conversion <Creation-by-conversion>`: Convert a
  single metadata construct already in memory to an independent field
  construct

..
  
* :ref:`Creation by reading <Creation-by-reading>`: Create field
  constructs from the netCDF variables in a dataset.

.. _Manual-creation:

**Manual creation**
^^^^^^^^^^^^^^^^^^^

Manual creation of a field construct has three stages:

**Stage 1:** The field construct is created without metadata constructs.

..
   
**Stage 2:** Metadata constructs are created independently.

..

**Stage 3:** The metadata constructs are inserted into the field
construct with cross-references to other, related metadata constructs
if required. For example, an auxiliary coordinate construct is related
to an ordered list of the domain axis constructs which correspond to
its data array dimensions.

There are two equivalent approaches to stages **1** and **2**.

Either as much of the content as possible is specified during object
instantiation:

.. code-block:: python
   :caption: *Create a field construct with a "standard_name"
             property. Create dimension coordinate and field ancillary
             constructs, both with properties and data.*
	     
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

.. code-block:: python
   :caption: *Create empty constructs and provide them with properties
             and data after instantiation.*
	     
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
   >>> dc
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
construct key for the metadata construct which can be used when other
metadata constructs are added to the field (e.g. to specify which
domain axis constructs correspond to a data array), or when other
metadata constructs are created (e.g. to identify the domain ancillary
constructs forming part of a coordinate reference construct):

.. code-block:: python
   :caption: *Set a domain axis construct and use its construct key
             when setting the dimension coordinate construct. Also
             create a cell method construct that applies to the domain
             axis construct.*
	     
   >>> longitude_axis = p.set_construct(cfdm.DomainAxis(3))
   >>> longitude_axis
   'domainaxis0'
   >>> key = p.set_construct(dc, axes=longitude_axis)
   >>> key
   'dimensioncoordinate0'
   >>> cm = cfdm.CellMethod(axes=longitude_axis, method='minimum')
   >>> p.set_construct(cm)
   'cellmethod0'
   
In general, the order in which metadata constructs are added to the
field does not matter, except when one metadata construct is required
by another, in which case the former must be added to the field first
so that its construct key is available to the latter. Cell method
constructs must, however, be set in the relative order in which their
methods were applied to the data.

The domain axis constructs spanned by a metadata construct's data may
be changed after insertion with the `~Field.set_construct_data_axes`
method of the field construct.

.. code-block:: python
   :caption: *Create a field construct with properties; data; and
             domain axis, cell method and dimension coordinate
             metadata constructs (data arrays have been generated with
             dummy values using numpy.arange).*

   import numpy
   import cfdm

   # Initialise the field construct with properties
   Q = cfdm.Field(properties={'project': 'research',
                              'standard_name': 'specific_humidity',
                              'units': '1'})
			      
   # Create the domain axis constructs
   domain_axisT = cfdm.DomainAxis(1)
   domain_axisY = cfdm.DomainAxis(5)
   domain_axisX = cfdm.DomainAxis(8)

   # Insert the domain axis constructs into the field. The
   # set_construct method returns the domain axis construct key that
   # will be used later to specify which domain axis corresponds to
   # which dimension coordinate construct.
   axisT = Q.set_construct(domain_axisT)
   axisY = Q.set_construct(domain_axisY)
   axisX = Q.set_construct(domain_axisX)

   # Create and insert the field construct data
   data = cfdm.Data(numpy.arange(40.).reshape(5, 8))
   Q.set_data(data, axes=[axisY, axisX])

   # Create the cell method constructs
   cell_method1 = cfdm.CellMethod(axes='area', method='mean')

   cell_method2 = cfdm.CellMethod()
   cell_method2.set_axes(axisT)
   cell_method2.set_method('maximum')

   # Insert the cell method constructs into the field in the same
   # order that their methods were applied to the data
   Q.set_construct(cell_method1)
   Q.set_construct(cell_method2)

   # Create a "time" dimension coordinate construct, with coordinate
   # bounds
   dimT = cfdm.DimensionCoordinate(
                               properties={'standard_name': 'time',
                                           'units': 'days since 2018-12-01'},
                               data=cfdm.Data([15.5]),
                               bounds=cfdm.Bounds(data=cfdm.Data([[0,31.]])))

   # Create a "longitude" dimension coordinate construct, without
   # coordinate bounds
   dimX = cfdm.DimensionCoordinate(data=cfdm.Data(numpy.arange(8.)))
   dimX.properties({'standard_name': 'longitude',
                    'units': 'degrees_east'})

   # Create a "longitude" dimension coordinate construct
   dimY = cfdm.DimensionCoordinate(properties={'standard_name': 'latitude',
		                               'units': 'degrees_north'})
   array = numpy.arange(5.)
   dimY.set_data(cfdm.Data(array))

   # Create and insert the latitude coordinate bounds
   bounds_array = numpy.empty((5, 2))
   bounds_array[:, 0] = array - 0.5
   bounds_array[:, 1] = array + 0.5
   bounds = cfdm.Bounds(data=cfdm.Data(bounds_array))
   dimY.set_bounds(bounds)

   # Insert the dimension coordinate constructs into the field,
   # specifying to # which domain axis each one corresponds
   Q.set_construct(dimT, axes=axisT)
   Q.set_construct(dimY, axes=axisY)
   Q.set_construct(dimX, axes=axisX)

.. code-block:: python
   :caption: *Inspect the new field construct.* 
	  
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

The "Conventions" property is not set because it is automatically
included in output files as a netCDF global "Conventions" attribute
corresponding to the version number of CF being used, as returned by
the `cfdm.CF` function. If the "Conventions" property is set on a
field construct then it is ignored during the write process. For
example, a CF version of ``'1.7'`` will produce a netCDF global
"Conventions" attribute value of ``'CF-1.7'``. Additional conventions
can be added with the "Conventions" parameter of the `cfdm.write`
function.

If this field were to be written to a netCDF dataset then, in the
absence of pre-defined names, default netCDF variable and dimension
names would be automatically generated (based on standard names where
they exist). The setting of bespoke names is, however, easily done
with the :ref:`netCDF interface <NetCDF-interface>`.

.. code-block:: python
   :caption: *Set netCDF variable and dimension names for the field
             and metadata constructs.*

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

.. code-block:: python
   :caption: *Create a field construct that contains at least one
             instance of each type of metadata construct.*

   import numpy
   import cfdm
   
   # Initialize the field construct
   tas = cfdm.Field(
       properties={'project': 'research',
                   'standard_name': 'air_temperature',
                   'units': 'K'})
   
   # Create and set domain axis constructs
   axis_T = tas.set_construct(cfdm.DomainAxis(1))
   axis_Z = tas.set_construct(cfdm.DomainAxis(1))
   axis_Y = tas.set_construct(cfdm.DomainAxis(10))
   axis_X = tas.set_construct(cfdm.DomainAxis(9))
   
   # Set the field construct data
   tas.set_data(cfdm.Data(numpy.arange(90.).reshape(10, 9)),
                axes=[axis_Y, axis_X])
   
   # Create and set the cell method constructs
   cell_method1 = cfdm.CellMethod(
             axes=[axis_Y, axis_X],
	     method='mean',
             properties={'where': 'land',
                         'interval': [cfdm.Data(0.1, units='degrees')]})
   
   cell_method2 = cfdm.CellMethod(axes=axis_T, method='maximum')
   
   tas.set_construct(cell_method1)
   tas.set_construct(cell_method2)
   
   # Create and set the field ancillary constructs
   field_ancillary = cfdm.FieldAncillary(
                properties={'standard_name': 'air_temperature standard_error',
                             'units': 'K'},
                data=cfdm.Data(numpy.arange(90.).reshape(10, 9)))
   
   tas.set_construct(field_ancillary, axes=[axis_Y, axis_X])
   
   # Create and set the dimension coordinate constructs
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
   
   dim_T = tas.set_construct(dimension_coordinate_T, axes=axis_T)
   dim_Z = tas.set_construct(dimension_coordinate_Z, axes=axis_Z)
   dim_Y = tas.set_construct(dimension_coordinate_Y, axes=axis_Y)
   dim_X = tas.set_construct(dimension_coordinate_X, axes=axis_X)
   
   # Create and set the auxiliary coordinate constructs
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
   
   # Create and set domain ancillary constructs
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
   
   domain_anc_A    = tas.set_construct(domain_ancillary_a, axes=axis_Z)
   domain_anc_B    = tas.set_construct(domain_ancillary_b, axes=axis_Z)
   domain_anc_OROG = tas.set_construct(domain_ancillary_orog,
                                       axes=[axis_Y, axis_X])

   # Create the datum for the coordinate reference constructs
   datum = cfdm.Datum(parameters={'earth_radius': 6371007.})

   # Create the coordinate conversion for the horizontal coordinate
   # reference construct
   coordinate_conversion_h = cfdm.CoordinateConversion(
                 parameters={'grid_mapping_name': 'rotated_latitude_longitude',
                             'grid_north_pole_latitude': 38.0,
                             'grid_north_pole_longitude': 190.0})
   
   # Create the coordinate conversion for the vertical coordinate
   # reference construct
   coordinate_conversion_v = cfdm.CoordinateConversion(
            parameters={'standard_name': 'atmosphere_hybrid_height_coordinate',
                        'computed_standard_name': 'altitude'},
            domain_ancillaries={'a': domain_anc_A,
                                'b': domain_anc_B,
                                'orog': domain_anc_OROG})
   
   # Create the vertical coordinate reference construct
   horizontal_crs = cfdm.CoordinateReference(
                      datum=datum,
                      coordinate_conversion=coordinate_conversion_h,
                      coordinates=[dim_X,
                                   dim_Y,
                                   aux_LAT,
                                   aux_LON])

   # Create the vertical coordinate reference construct
   vertical_crs = cfdm.CoordinateReference(
                    datum=datum,
                    coordinate_conversion=coordinate_conversion_v,
                    coordinates=[dim_Z])

   # Set the coordinate reference constructs
   tas.set_construct(horizontal_crs)
   tas.set_construct(vertical_crs)
   
   # Create and set the cell measure constructs
   cell_measure = cfdm.CellMeasure(measure='area',
                    properties={'units': 'km2'},
                    data=cfdm.Data(numpy.arange(90.).reshape(9, 10)))
   
   tas.set_construct(cell_measure, axes=[axis_X, axis_Y])

The new field construct may now be inspected:

.. code-block:: python
   :caption: *Inspect the new field construct.*

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
		  
.. _Creating-data-from-an-array-on-disk:

Creating data from an array on disk
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All the of above examples use arrays in memory to construct the data
instances for the field and metadata constructs. It is, however,
possible to create data from arrays that reside on disk. The
`cfdm.read` function creates data in this manner. A pointer to an
array in a netCDF file can be stored in a `~cfdm.NetCDFArray`
instance, which is is used to initialize a `~cfdm.Data` instance.

.. code-block:: python
   :caption: *Define a variable from a dataset with the netCDF package
             and use it to create a NetCDFArray instance with which to
             initialize a Data instance.*
		
   >>> import netCDF4
   >>> nc = netCDF4.Dataset('file.nc', 'r')
   >>> v = nc.variables['ta']
   >>> netcdf_array = cfdm.NetCDFArray(filename='file.nc', ncvar='ta',
   ...	                               dtype=v.dtype, ndim=v.ndim,
   ...	     		  	       shape=v.shape, size=v.size)
   >>> data_disk = cfdm.Data(netcdf_array)

  
.. code-block:: python
   :caption: *Read the netCDF variable's data into memory and
             initialise another Data instance with it. Compare the
             values of the two data instances.*

   >>> numpy_array = v[...]
   >>> data_memory = cfdm.Data(numpy_array)
   >>> data_disk.equals(data_memory)
   True

Note that data type, number of dimensions, dimension sizes and number
of elements of the array on disk that are used to initialize the
`~cfdm.NetCDFArray` instance are those expected by the CF data model,
which may be different to those of the netCDF variable in the file
(although they are the same in the above example). For example, a
netCDF character array of shape ``(12, 9)`` is viewed in cfdm as a
one-dimensional string array of shape ``(12,)``.

.. _Creation-by-conversion:

**Creation by conversion**
^^^^^^^^^^^^^^^^^^^^^^^^^^

An independent field construct may be created from an existing
metadata construct using `~Field.convert` method of the field
construct, which identifies a unique metadata construct and returns a
new field construct based on its properties and data. The new field
construct always has domain axis constructs corresponding to the data,
and (by default) any other metadata constructs that further define its
domain.

.. code-block:: python
   :caption: *Create an independent field construct from the "surface
             altitude" metadata construct.*

   >>> orog = tas.convert('surface_altitude')	  
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

The `~Field.convert` method has an option to only include domain axis
constructs in the new field construct, with no other metadata
constructs.

.. code-block:: python
   :caption: *Create an independent field construct from the "surface
             altitude" metadata construct, but without a complete
             domain.*

   >>> orog1 = tas.convert('surface_altitude', full_domain=False) 
   >>> print(orog1)
   Field: surface_altitude
   -----------------------
   Data            : surface_altitude(key%domainaxis2(10), key%domainaxis3(9)) m
   
.. _Creation-by-reading:

**Creation by reading**
^^^^^^^^^^^^^^^^^^^^^^^

The `cfdm.read` function :ref:`reads a netCDF dataset
<Reading-datasets>` and returns the contents as a list of zero or more
field constructs, each one corresponding to a unique CF-netCDF data
variable in the dataset. For example, the field construct ``tas`` that
was created manually can be :ref:`written to a netCDF dataset
<Writing-to-disk>` and then read back into memory:

.. code-block:: python
   :caption: *Write the field construct that was created manually to
             disk, and then read it back into a new field construct.*

   >>> cfdm.write(tas, 'tas.nc')
   >>> f = cfdm.read('tas.nc')
   >>> f
   [<Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>]

The `cfdm.read` function also allows field constructs to be derived
directly from the netCDF variables that correspond to particular types
metadata constructs. In this case, the new field constructs will have
a domain limited to that which can be inferred from the corresponding
netCDF variable, but without the connections that are defined by the
parent netCDF data variable. This will often result in a new field
construct that has fewer metadata constructs than one created with the
`~Field.convert` method.

.. code-block:: python
   :caption: *Read the file, treating formula terms netCDF variables
             (which map to domain ancillary constructs) as additional
             CF-netCDF data variables.*

   >>> fields = cfdm.read('tas.nc', extra='domain_ancillary')
   >>> fields
   [<Field: ncvar%a(atmosphere_hybrid_height_coordinate(1)) m>,
    <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>,
    <Field: ncvar%b(atmosphere_hybrid_height_coordinate(1)) 1>,
    <Field: surface_altitude(grid_latitude(10), grid_longitude(9)) m>]
   >>> orog_from_file = fields[3]
   >>> print(orog_from_file)
   Field: surface_altitude (ncvar%surface_altitude)
   ------------------------------------------------
   Data            : surface_altitude(grid_latitude(10), grid_longitude(9)) m
   Dimension coords: grid_latitude(10) = [0.0, ..., 9.0] degrees
                   : grid_longitude(9) = [0.0, ..., 8.0] degrees

Comparing the field constructs ``orog_from_file`` (created with
`cfdm.read`) and ``orog`` (created with the `~Field.convert` method of
the ``tas`` field construct), the former lacks the auxiliary
coordinate, cell measure and coordinate reference constructs of the
latter. This is because the surface altitude netCDF variable in
``tas.nc`` does not have the "coordinates", "cell_measures" nor
"grid_mapping" netCDF attributes that would link it to auxiliary
coordinate, cell measure and grid mapping netCDF variables.

.. _Copying:

**Copying**
-----------

----

A field construct may be copied with its `~Field.copy` method. This
produces a "deep copy", i.e. the new field construct is completely
independent of the original field.

.. code-block:: python
   :caption: *Copy a field construct and change elements of the copy,
             showing that the original field construct has not been
             altered.*
     
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

.. code-block:: python
   :caption: *Copy a field construct with the built-in copy module.*
	    
   >>> import copy
   >>> u = copy.deepcopy(t)

Metadata constructs may be copied individually in the same manner:

.. code-block:: python
   :caption: *Copy a metadata construct.*

   >>> orog = t.get_construct('surface_altitude').copy()

Arrays within `Data` instances are copied with a `copy-on-write
<https://en.wikipedia.org/wiki/Copy-on-write>`_ technique. This means
that a copy takes up very little memory, even when the original
constructs contain very large data arrays, and the copy operation is
fast.

.. _Equality:

**Equality**
------------

----

Whether or not two field constructs are the same is tested with either
field construct's `~Field.equals` method.

.. code-block:: python
   :caption: *A field construct is always equal to itself, a copy of
             itself and a complete subspace of itself. The "verbose"
             keyword will give some (but not necessarily all) of the
             reasons why two field constructs are not the same.*
	     
   >>> t.equals(t)
   True
   >>> t.equals(t.copy())
   True
   >>> t.equals(t[...])
   True
   >>> t.equals(q)
   False
   >>> t.equals(q, verbose=True)
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

Two real numbers :math:`x` and :math:`y` are considered equal if
:math:`|x - y| \le a_{tol} + r_{tol}|y|`, where :math:`a_{tol}` (the
tolerance on absolute differences) and :math:`r_{tol}` (the tolerance
on relative differences) are positive, typically very small
numbers. By default both are set to the system epsilon (the difference
between 1 and the least value greater than 1 that is representable as
a float). Their values may be inspected and changed with the
`cfdm.ATOL` and `cfdm.RTOL` functions:

.. code-block:: python
   :caption: *The ATOL and RTOL functions allow the numerical equality
             tolerances to be inspected and changed.*
      
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

Note that the above equation is not symmetric in :math:`x` and
:math:`y`, so that for two fields ``f1`` and ``f2``, ``f1.equals(f2)``
may be different from ``f2.equals(f1)`` in some rare cases.
   
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

.. code-block:: python
   :caption: *Metadata constructs also have an equals method, that
             behaves in a similar manner.*
	  
   >>> orog = t.get_construct('surface_altitude')
   >>> orog.equals(orog.copy())
   True

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

.. code-block:: python
   :caption: *Retrieve metadata constructs based on their netCDF
             names.*
	  
   >>> t.constructs(ncvar='b')
   {'domainancillary1': <DomainAncillary: ncvar%b(1) >}
   >>> t.get_construct('ncvar%x')
   <DimensionCoordinate: grid_longitude(9) degrees>
   >>> t.get_construct(ncdim='x')
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

.. code-block:: python
   :caption: *Access netCDF elements associated with the field and
             metadata constructs.*

   >>> q.nc_get_variable()
   'q'
   >>> q.nc_global_attributes()
   {'project', 'Conventions'}
   >>> q.nc_unlimited_dimensions()
   set()
   >>> q.nc_set_variable('humidity')
   >>> q.nc_get_variable()
   'humidity'
   >>> q.get_construct('latitude').nc_get_variable()
   'lat'

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

.. code-block:: python
   :caption: *Write a field construct to a netCDF dataset on disk.*

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

.. code-block:: shell
   :caption: *Inspect the new dataset with the ncdump command line
             tool.*

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
   
.. code-block:: python
   :caption: *Write multiple field constructs to a netCDF dataset on
             disk.*
	     
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

A CF-netCDF scalar (i.e. zero-dimensional) coordinate variable is
created from a size one dimension coordinate construct that spans a
domain axis construct which is not spanned by the field construct's
data, nor the data of any other metadata construct. This occurs for
the field construct ``q``, for which the "time" dimension coordinate
construct was to the file ``q_file.nc`` as a scalar coordinate
variable.

To change this so that the "time" dimension coordinate construct is
written as a CF-netCDF size one coordinate variable, the field
construct's data must be expanded to span the corresponding size one
domain axis construct, by using the `~Field.insert_dimension` method
of the field construct.

.. code-block:: python
   :caption: *Write the "time" dimension coordinate construct to a
             (non-scalar) CF-netCDF coordinate variable by inserting
             the corresponding dimension into the field construct's
             data.*
		   
   >>> print(q)
   Field: specific_humidity (ncvar%humidity)
   -----------------------------------------
   Data            : specific_humidity(latitude(5), longitude(8)) 1
   Cell methods    : area: mean
   Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                   : longitude(8) = [22.5, ..., 337.5] degrees_east
                   : time(1) = [2019-01-01 00:00:00]
   <Field: specific_humidity(latitude(5), longitude(8)) 1>
   >>> q.get_construct_data_axes('time')
   ('domainaxis2',)
   >>> q2 = q.insert_dimension(axis='domainaxis2')
   >>> q2
   <Field: specific_humidity(time(1), latitude(5), longitude(8)) 1>
   >>> cfdm.write(q2, 'q2_file.nc')

The new dataset is structured as follows (note, relative to file
``q_file.nc``, the existence of the "time" dimension and the lack of a
"coordinates" attribute on the, now three-dimensional, data variable):
   
.. code-block:: shell
   :caption: *Inspect the new dataset with the ncdump command line
             tool.*

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

.. code-block:: shell
   :caption: *Inspect the parent dataset with the ncdump command line
             tool.*
   
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

.. code-block:: shell
   :caption: *Inspect the external dataset with the ncdump command
             line tool.*

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

.. code-block:: python
   :caption: *Read the parent dataset without specifying the location
             of any external datasets.*

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

.. code-block:: python
   :caption: *Read the parent dataset whilst providing the external
             dataset containing the external variables.*
   
   >>> g = cfdm.read('parent.nc', external='external.nc')[0]
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

To create a reference to an external variable in an output netCDF
file, set the status of the cell measure construct to "external" with
its `~CellMeasure.nc_external` method.

.. code-block:: python
   :caption: *Flag the cell measure as external and write the field
             construct to a new file.*

   >>> area.nc_external(True)
   False
   >>> cfdm.write(g, 'new_parent.nc')

To create a reference to an external variable in the an output netCDF
file and simultaneously create an external file containing the
variable set the status of the cell measure construct to "external"
and provide an external file name to the `cfdm.write` function:

.. code-block:: python
   :caption: *Write the field construct to a new file and the cell
             measure construct to an external file.*

   >>> cfdm.write(g, 'new_parent.nc', external='new_external.nc')

.. _Compression:
   
**Compression**
---------------

----

The CF conventions have support for space saving by identifying
unwanted missing data.  Such compression techniques store the data
more efficiently and result in no precision loss. The CF data model,
however, views compressed arrays in their uncompressed form.

Therefore, the field construct contains domain axis constructs for the
compressed dimensions and presents a view of compressed data in its
uncompressed form, even though their "underlying arrays" (i.e. the
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
  index the field construct with (indices equivalent to) `Ellipsis`.
  
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

.. code-block:: shell
   :caption: *Inspect the compressed dataset with the ncdump command
             line tool.*
   
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

.. code-block:: python
   :caption: *Read a field construct from a dataset that has been
             compressed with contiguous ragged arrays, and inspect its
             data in uncompressed form.*
   
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

.. code-block:: python
   :caption: *Inspect the underlying compressed array and the count
             variable that defines how to uncompress the data.*
	     
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

.. code-block:: python
   :caption: *Get the data for the second station.*
	  
   >>> station2 = h[1]
   >>> station2
   <Field: specific_humidity(ncdim%station(1), ncdim%timeseries(9))>
   >>> print(station2.get_array())
   [[0.05 0.11 0.2 0.15 0.08 0.04 0.06 -- --]]

The underlying array of original data remains in compressed form until
data array elements are modified:
   
.. code-block:: python
   :caption: *Change an element of the data and show that the
             underlying array is no longer compressed.*

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

.. code-block:: python
   :caption: *Create a field construct with compressed data.*

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

.. code-block:: python
   :caption: *Inspect the new field construct and wite it to disk.*
   
   >>> T
   <Field: air_temperature(key%domainaxis1(2), key%domainaxis0(4)) K>
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
  
.. code-block:: shell
   :caption: *Inspect the new compressed dataset with the ncdump
             command line tool.*   

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

.. code-block:: shell
   :caption: *Inspect the compressed dataset with the ncdump command
             line tool.*
      
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

.. code-block:: python
   :caption: *Read a field construct from a dataset that has been
             compressed by gathering, and inspect its data in
             uncompressed form.*

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

.. code-block:: python
   :caption: *Inspect the underlying compressed array and the list
             variable that defines how to uncompress the data.*
	     
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

.. code-block:: python
   :caption: *Get subspaces based on iundices of the uncompressed
             data.*
	  
   >>> p[0]
   <Field: precipitation_flux(time(1), latitude(4), longitude(5)) kg m2 s-1>
   >>> p[1, :, 3:5]
   <Field: precipitation_flux(time(1), latitude(4), longitude(2)) kg m2 s-1>

The underlying array of original data remains in compressed form until
data array elements are modified:
   
.. code-block:: python
   :caption: *Change an element of the data and show that the
             underlying array is no longer compressed.*

   >>> p.data.get_compression_type()
   'gathered'
   >>> p.data[1] = -9
   >>> p.data.get_compression_type()
   ''
   
A construct with an underlying gathered array is created by
initializing a `Data` instance with a gathered array that is stored in
the special `GatheredArray` array object. The following code creates a
simple field construct with an underlying gathered array:

.. code-block:: python
   :caption: *Create a field construct with compressed data.*

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
``compressed_dimension`` parameter of the `GatheredArray`
initialisation).

The new field construct can now be inspected and written a netCDF file:

.. code-block:: python
   :caption: *Inspect the new field construct and wite it to disk.*
   
   >>> P
   <Field: precipitation_flux(key%domainaxis0(2), key%domainaxis1(3), key%domainaxis2(2)) kg m-2 s-1>
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
   
.. code-block:: shell
   :caption: *Inspect new the compressed dataset with the ncdump
             command line tool.*
   
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

.. [#files] The tutorial files may be also found in the `downloads
            directory
            <https://github.com/NCAS-CMS/cfdm/tree/master/docs/_downloads>`_
            of the on-line code repository.

.. [#notebook] The Jupyter notebook is quite long. To aid navigation
               it has been written so that it may optionally be used
               with the "Collapsible Headings" Jupyter notebook
               extension. See
               https://jupyter-contrib-nbextensions.readthedocs.io/en/latest
               for details.

.. [#opendap2] Requires the netCDF4 python package to have been built
               with OPeNDAP support enabled. See
               http://unidata.github.io/netcdf4-python for details.

.. .. [#language] In the terminology of the CF data model, a "construct"
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
	    
.. External links to the CF conventions (will need updating with new version of CF)
   
.. _External variables:               http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#external-variables
.. _Discrete sampling geometry (DSG): http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#discrete-sampling-geometries
.. _incomplete multidimensional form: http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#_incomplete_multidimensional_array_representation
.. _Compression by gathering:         http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#compression-by-gathering
.. _contiguous:                       http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#_contiguous_ragged_array_representation
.. _indexed:                          http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#_indexed_ragged_array_representation
.. _indexed contiguous:               http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#_ragged_array_representation_of_time_series_profiles
