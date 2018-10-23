.. currentmodule:: cfdm
.. default-role:: obj

Tutorial
========

The field construct defined by the CF data model is represented by a
`Field` object.

Reading from disk
-----------------

The `cfdm.read` function reads a netCDF file from disk and returns its
contents as a list one or more `Field` objects:

>>> import cfdm
>>> f = cfdm.read('file.nc')

The `cfdm.read` function has options to define external files that
contain extra metadata, and to specify which metadata constructs
should also be returned as independent fields.

Inspection
----------

The contents of a field may be inspected at three different levels of
detail.

The built-in `repr` function returns a short, one-line description of
the field:

>>> f
[<Field: air_temperature(time(12), latitude(64), longitude(128)) K>,
 <Field: air_temperature(time(12), latitude(64), longitude(128)) K>]

This gives the identity of the field (that has the standard name
"air_temperature"), the identities and sizes of the domain axes
spanned by the field's data array (time, latitude and longitude with
sizes 12, 64 and 128 respectively) and the units of the field's data
(K).

The built-in `str` function returns the same information as the the
one-line output, along with short descriptions of the field's other
components:

   >>> print(f[0])
   air_temperature field summary
   -----------------------------
   Data           : air_temperature(time(1200), latitude(64), longitude(128)) K
   Cell methods   : time: mean (interval: 1.0 month)
   Axes           : time(12) = [ 450-11-01 00:00:00, ...,  451-10-16 12:00:00] noleap
                  : latitude(64) = [-87.8638000488, ..., 87.8638000488] degrees_north
                  : longitude(128) = [0.0, ..., 357.1875] degrees_east
                  : height(1) = [2.0] m

This shows that the field also has a cell method and four dimension
coordinates, one of which (height) is a coordinate for a size 1 domain
axis that is not a dimension of the field's data array. The units and
first and last values of all data arrays are given and relative time
values are translated into strings.

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

Properties
----------

Properties of the field may be retrieved with the `~Field.properties`
method:

   >>> f.properties()

Individual properties may be accessed with the `~Field.del_property`,
`~Field.get_property`, `~Field.has_property`, and
`~Field.set_property` methods:

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

All properties may be removed and completed replace with another
collection by providing the new properties to the `~Field.properties`
method:

   >>> original = f.properties({'foo': 'bar', 'units': 'm s-1'}
   >>> f.properties()
   {'foo': 'bar',
    'units': 'm s-1'}
   >>> f.properties(original)
   {'foo': 'bar',
    'units': 'm s-1'}
   >>> f.properties()
   
Data
----

The field's data array is stored in a `Data` object, that is accessed
with the `~Field.get_data` method:

   >>> f.get_data()
   <>

The data may be retrieved as an independent `numpy` array with the
`~Field.get_array` method:

   >>> f.get_array()

The file also has a `~Field.data` attribute that is an alias for the
`~Field.get_data` method, which makes it easier to access attributes
and methods of the `Data` object:

   >>> f.data.dtype
   asasdasdasd
   >>> f.data.ndim
   3
   >>> f.data.shape
   ()
   >>> f.data.size
   34534534

Indexing the `Data` object creates new, independent `Data`
object. Indexing is similar to `numpy` indexing, the only difference
being:

* When two or more dimension's indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same as
  indexing a `netCDF.Variable` object.
..

   >>> f.data[0, 1, 2]
   >>> f.data[0, ::-2, 2]
    
Data array elements are changed by assigning to indices of the `Data`
object. The value being assigned must be broadcastable to the shape
defined by the indices, using the same broadcasting rules as `numpy`:

   >>> import numpy
   >>> f.data[:, 0] = -99
   >>> f.data[:, 0] = range()
   >>> f.data[:, 0] = numpy.array()
   >>> d = f.data
   >>> f.data[:, 0] = d[0, 1]
      
Data elements may be set to missing data by assigning the `numpy` mask object:

   >>> f[...] = numpy.ma.masked

Subspacing
----------

Creation of a new field that spans a subspace of the original domain
is achieved by indexing the field directly, using the same indexing
rules as for assignment to the data array:

   >>> g = f[:, ::-1, 2]
   >>> print(g)

The new subspace contains similar constructs to the original field, but
these are also subspaced when they span the altered axes.

Constructs
----------

Each construct of the CF data model has a corresponding `cfdm` class:

=====================  ==============================  =======================
cfdm class             Description                     CF data model construct
=====================  ==============================  =======================
`Field`                Scientific data discretised     Field               
                       within a domain		                         
`DomainAxis`           Independent axes of the domain  Domain axis         
`DimensionCoordinate`  Domain cell locations           Dimension coordinate
`AuxiliaryCoordinate`  Domain cell locations           Auxiliary coordinate
`CoordinateReference`  Domain coordinate systems       Coordinate reference
`DomainAncillary`      Cell locations in alternative   Domain ancillary
                       coordinate systems
`CellMeasure`          Domain cell size or shape       Cell measure
`FieldAncillary`       Ancillary metadata which vary   Field ancillary
                       within the domain
`CellMethod`           Describes how data represent    Cell method
                       variation within cells
=====================  ==============================  =======================

The metadata constructs of the field (i.e all of the constructs
contained by the field construct) are returned by the
`~Field.constructs` method, that provides a dictionary of the
constructs keyed by an internal identifier:

   >>> f.constructs()
   
The `~Field.constructs` method has options to fileter the constructs
by their type, their property and other attribute values, and by the
domain axes that are spanned by the data array:

   >>> f.constructs(description='long_name:asdasdasdas')
   >>> f.constructs(description='dimaneioncoordinate2')
   >>> f.constructs(construct_type='dimension_coordinate')
   >>> f.constructs(axes=['domainaxis1'])
   >>> f.constructs(description='latitude',
                    construct_type='dimension_coordinate'
                    axes=['domainaxis1'])

Note that we can also use the field's internal identifier to select
constructs (e.g. "dimensioncoordinate1"), which is useful if a
construct is not identifiable from its descriptive properties. 

An individual construct may be returned without its identifier with
the `~Field.construct` method:

   >>> f.construct(description='latitude')
   <>

Where applicable, the classes representing metadata constructs share
the same API as the field. For example, this means that the class for
any construct that has a data array will have a `!get_array` method to
access the data as a numpy array:

   >>> lon = f.construct('longitude')
   >>> lon
   <>
   >>> lon.set_property('long_name', 'Longitude')
   >>> lon.properties()
   >>> lon.data[2] = 3453453454
   >>> lon.get_array()

Other `cfdm` classes are required to represent certain components of
CF data model constructs:

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

`Data`                  A container for the data        `Field`,
                        array.                          `DimensionCoordinate`,
                                                        `AuxiliaryCoordinate`,
                                                        `DomainAncillary`,
							`CellMeasure`,
							`FieldAncillary`
			
`Datum`                 The zeroes                      `CoordinateReference`
                        of the dimension
                        and auxiliary coordinate
			constructs which define a
			coordinate system.

`Domain`                The locations of the data       `Field`
                        array elements.
======================  ==============================  ======================


Writing to disk
---------------

The `cfdm.write` function writes fields to a netCDF file on disk:

   >>> cfdm.write(f, 'new_file.nc')

The `cfdm.write` function has options to set the format, netCDF
compression, endian (native), and HDF chunk size of the ouput file; as
well as options that modify output data types, and which specify which
properties should be global attributes.

Equality
--------

Whether or not two fields are the same is ascertained with either of
the field's `~cfdm.Field.equals` methods.

   >>> g = cfdm.read('new_file.nc')
   >>> f[0].equals(g[0])
   True

Field creation
--------------

Exernal variables
-----------------

Discrete sampling geometries
----------------------------

When a collection of discrete sampling geomtry (DSG) features has been
combined using a ragged representation to save space, the field
contains the domain axes that have been compressed and presents a view
of the data in their uncompressed, incomplete orthogonal form, even
though the underlying arrays remain in their ragged representation.

Accessing the data by indexing, or by a call to the `!get_array`
method, always returns data that is uncompressed, i.e. in incomplete
orthogonal representation. The compressed data may be retrieved with
the `get_compressed_data` method of a `Data` object. If the elements
are modified by indexed assignment then the underlying compressed
array is replaced by its incomplete orthogonal form.

If an underlying array is compressed at the time of writing to disk,
then it is written as a ragged array.

A count variable that is required to uncompress a contiguous, or
indexed contiguous, ragged array is retrieved and set with the
`get_count_variable` and `set_count_variable` methods respectively of
a `Data` object.

An index variable that is required to uncompress a indexed, or indexed
contiguous, ragged array is retrieved and set with the
`get_index_variable` and `set_index_variable` methods respectively of
a `Data` object.

This is illustrated with the file **contiguous.nc** (`download`):

.. code:: bash
   
   $ ncdump -h
   netcdf contiguous {
   dimensions:
	station = 4 ;
	obs = 24 ;
	name_strlen = 8 ;
   variables:
	double lon(station) ;
		lon:standard_name = "longitude" ;
		lon:units = "degrees_east" ;
	double lat(station) ;
		lat:standard_name = "latitude" ;
		lat:units = "degrees_north" ;
	double alt(station) ;
		alt:standard_name = "height" ;
		alt:units = "m" ;
		alt:positive = "up" ;
		alt:axis = "Z" ;
	char station_name(station, name_strlen) ;
		station_name:long_name = "station name" ;
		station_name:cf_role = "timeseries_id" ;
	int row_size(station) ;
		row_size:long_name = "number of observations for this station" ;
		row_size:sample_dimension = "obs" ;
	double time(obs) ;
		time:standard_name = "time" ;
		time:units = "days since 1970-01-01 00:00:00" ;
	double humidity(obs) ;
		humidity:_FillValue = -999.9 ;
		humidity:standard_name = "specific_humidity" ;
		humidity:coordinates = "time lat lon alt station_name" ;

   // global attributes:
		:Conventions = "CF-1.6" ;
		:featureType = "timeSeries" ;
   }
..

   >>> c = cfdm.read('contiguous.nc')[0]
   >>> print(c)
   >>> c.get_array()
   >>> c.data.get_compressed_array().get_array()
   >>> c.data.get_count_variable().get_array()

Gathering
---------

When axes have been compressed by gathering, the field contains the
domain axes that have been compressed and presents a view of the data
in their uncompressed form, even though the underlying arrays remain
in their gathered representation.

Accessing the data by indexing, or by a call to the `!get_array`
method, always returns data that is uncompressed. The compressed data
may be retrieved with the `get_compressed_data` method of a `Data`
object. If the elements are modified by indexed assignment then the
underlying compressed array is replaced by its uncompressed form.

If an underlying array is compressed at the time of writing to disk,
then it is written as a gathered array.

A list variable that is required to uncompress a gathered array is
retrieved and set with the `get_list_variable` and `set_list_variable`
methods respectively of a `Data` object.

This is illustrated with the file **gathered.nc** (`download`):

.. code:: bash
   
   $ ncdump -h gathered.nc
   netcdf gathered {
   dimensions:
   	time = 2 ;
   	lat = 4 ;
   	lon = 5 ;
	list = 3 ;
   variables:
   	double time(time) ;
   		time:standard_name = "time" ;
   		time:units = "days since 2000-1-1" ;
   	double lat(lat) ;
   		lat:standard_name = "latitude" ;
   		lat:units = "degrees_north" ;
   	int list(list) ;
   		list:compress = "lat lon" ;
   	double pr(time, list) ;
		pr:standard_name = "precipitation_flux" ;
		pr:units = "kg m2 s-1" ;
		
   // global attributes:
 		:Conventions = "CF-1.7" ;
   }
..

   >>> c = cfdm.read('gathered.nc')[0]
   >>> print(c)
   >>> c.get_array
   >>> c.data.get_compressed_array().get_array()
   >>> c.data.get_list_variable().get_array()
