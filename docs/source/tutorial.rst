.. currentmodule:: cfdm
.. default-role:: obj

.. _tutorial:

Tutorial
========

The field construct defined by the CF data model is represented by a
`Field` object.

.. _read:

Reading from disk
-----------------

The `cfdm.read` function reads a `netCDF
<https://www.unidata.ucar.edu/software/netcdf/>`_ file from disk or
from an `OPeNDAP URL
<https://www.unidata.ucar.edu/software/netcdf/docs/dap_accessing_data.html>`_
[#opendap]_ and returns its contents as a list one or more `Field`
objects.

For example, to read the file **file.nc** (:download:`download
<../netcdf_files/file.nc>`) [#files]_:


>>> import cfdm
>>> f = cfdm.read('file.nc')

The `cfdm.read` function has optional parameters to

* provide files that contain :ref:`external variables <external>`, and

* specify which netCDF variables which correspond to metadata
  constructs should also be returned as independent fields.

All formats of netCDF3 and netCDF4 files can be read.
  
.. _inspection:
  
Inspection
----------

The contents of a field may be inspected at three different levels of
detail.

.. rubric:: 1: Minimal

The built-in `repr` function returns a short, one-line description of
the field:

   >>> f
   TODO
   [<Field: air_temperature(time(12), latitude(64), longitude(128)) K>,
    <Field: air_temperature(time(12), latitude(64), longitude(128)) K>]
   >>> f[0]
   TODO
   <Field: air_temperature(time(12), latitude(64), longitude(128)) K>

This gives the identity of the field (that has the standard name
"air_temperature"), the identities and sizes of the domain axis
constructs spanned by the field's data array (time, latitude and
longitude with sizes 12, 64 and 128 respectively) and the units of the
field's data (K).

.. rubric:: 2: Medium

The built-in `str` function returns the same information as the the
one-line output, along with short descriptions of the field's other
metadata constructs:

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
coordinate constructs, one of which (height) is a coordinate for a
size 1 domain axis that is not a dimension of the field's data
array. The units and first and last values of all data arrays are
given and relative time values are translated into strings.

.. rubric:: 3: Full

The field's `~cfdm.Field.dump` method gives all properties of all
constructs as well as the first and last values of the field's data
array

.. code:: python

   >>> g = f[0]
   >>> g.dump()
   TODO
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
       Data(time(12)) = [ 450-11-16 00:00:00, ...,  451-10-16 12:00:00] noleap
       Bounds(time(12), 2) = [[ 450-11-01 00:00:00, ...,  451-11-01 00:00:00]] noleap
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
   TODO
   
Individual properties may be accessed and modified with the
`~Field.del_property`, `~Field.get_property`, `~Field.has_property`,
and `~Field.set_property` methods:

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
	  
   >>> original = f.properties({'foo': 'bar', 'units': 'm s-1'}
   >>> f.properties()
   {'foo': 'bar',
    'units': 'm s-1'}
   >>> f.properties(original)
   {'foo': 'bar',
    'units': 'm s-1'}
   >>> f.properties()
   TODO
   >>> f.properties({})
   TODO
   >>> f.properties()
   {}

.. _data:

Data
----

The field's data array is stored in a `Data` object that is accessed
with the `~Field.get_data` method:

   >>> f.get_data()
   TODO

The data may be retrieved as an independent `numpy` array with the
`~Field.get_array` method:

   >>> f.get_array()
   TODO
   
The field also has a `~Field.data` attribute that is an alias for the
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

.. _data_assignment:

Data assignment
^^^^^^^^^^^^^^^

Data array elements are changed by assigning to indices of the `Data`
object. The indexing rules are similar to the `numpy indexing rules
<https://docs.scipy.org/doc/numpy/reference/arrays.indexing.html>`_,
the only differences being:

* **When two or more dimensions' indices are sequences of integers
  then these indices work independently along each dimension (similar
  to the way vector subscripts work in Fortran). This is the same
  behaviour as indexing on a** `Variable` **object of the** `netCDF4
  package <http://unidata.github.io/netcdf4-python>`_\ **.**

The value being assigned must be broadcastable to the shape defined by
the indices, using the `numpy broadcasting rules
<https://docs.scipy.org/doc/numpy/user/basics.broadcasting.html>`_.

   >>> import numpy
   >>> f.data[:, 0] = -99
   >>> f.data[:, 0] = range()
   >>> f.data[:, 0] = numpy.array()
   >>> d = f.data
   >>> f.data[:, 0] = d[0, 1]
      
Data elements may be set to missing data by assigning the `numpy` mask object:

   >>> f.data[...] = numpy.ma.masked

Subspacing
----------

Creation of a new field that spans a subspace of the original domain
is achieved by indexing the field directly. The new subspace contains
the same properties and similar metadata constructs to the original
field, but the latter are also subspaced when they span domain axes
that have been changed. The indexing rules are the same as for
:ref:`data assignment <data_assignment>`, with the additional rule
that:
     
* **An integer index i takes the i-th element but does not reduce the
  rank of the output data by one.**

.. code:: python

   >>> g = f[..., ::-1, 2]
   >>> print(g)
   TODO
   >>> f.data[0, [1, 3], [2, 4, 5]]
   >>> print(g)
   TODO
   
The `Data` object may also be indexed with the same indexing rules to
produce a new, independent `Data` object.

   >>> f.data[..., ::-1, 2]
   <DATA TODO>

.. _constructs:

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

The metadata constructs of the field (i.e. all of the constructs
contained by the field construct) are returned by the
`~Field.constructs` method that provides a dictionary of the
constructs, keyed by unique internal identifiers:

   >>> f.constructs()
   TODO
   
The `~Field.constructs` method has options to filter the constructs by
their type, property (and other attribute) values, and by which domain
axes that are spanned by the data array:

.. code:: python
	  
   >>> f.constructs('long_name:asdasdasdas')
   TODO
   >>> f.constructs(construct_type='dimension_coordinate')
   TODO
   >>> f.constructs(axes=['domainaxis1'])
   TODO
   >>> f.constructs('latitude',
   ...              construct_type='dimension_coordinate'
   ...              axes=['domainaxis1'])
   TODO
   
An internal identifier may also be used to select constructs, which is
useful if a construct is not identifiable by other means.

   >>> f.constructs(id='dimensioncoordinate1')
   TODO
   
An individual construct may be returned, without its identifier, with
the field's `~Field.get_construct` method (which supports the same
filtering as techniques as above):

   >>> f.get_construct('latitude')
   TODO

Where applicable, the classes for metadata constructs share the same
API as the field. This means, for instance, that a class that has a
data array (such as `DomainAncillary`) will have a `!get_array` method
to access its data as a numpy array:

.. code:: python
	  
   >>> lon = f.get_construct('longitude')
   >>> lon
   <TODO>
   >>> lon.set_property('long_name', 'Longitude')
   >>> lon.properties()
   TODO
   >>> lon.data[2] = 3453453454
   >>> lon.get_array()
   TODO

Construct components
^^^^^^^^^^^^^^^^^^^^

Other classes are used to represent construct components that are
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

`Domain`                The locations of the data       `Field`
                        array elements.
======================  ==============================  ======================

Where applicable, these classes also share the same API as the field:

.. code:: python
	  
   >>> lon = f.get_construct('longitude')
   >>> bounds = lon.get_bounds()
   >>> bounds
   TODO
   >>> bounds.properties()
   TODO
   >>> bounds.get_data()
   TODO
   >>> f.domain.get_construct('longitude')
   TODO
   >>> crs = f.get_construct(TODO)
   >>> crs.datum
   TODO
   >>> crs.datum.parameters()
   TODO
   >>> crs = f.get_construct(TODO)
   >>> crs.coordinate_conversion
   TODO

.. _write:
   
Writing to disk
---------------

The `cfdm.write` function writes fields to a netCDF file on disk:

   >>> cfdm.write(f, 'new_file.nc')

The `cfdm.write` function has optional parameters to

* TODO specify which attributes should, where possibleor should not, be global attributes,
  
* TODO specify which attributes should, or should not, be global attributes,
  
* create :ref:`external variables <external>` in an external file,

* change the data type of output data arrays,
  
* set the output netCDF format (all netCDF3 and netCDF4 formats are
  possible),

* apply netCDF compression,

* set the endian-ness of the output data, and

* set the HDF chunk size

.. _equality:

Equality
--------

Whether or not two fields are the same is ascertained with either of
the field's `~cfdm.Field.equals` methods.

   >>> g = cfdm.read('new_file.nc')
   >>> f.equals(g[0])
   True
   >>> g.data[0, 0, 0] = -99
   >>> g.set_property('long_name') = 'foo'
   >>> f.equals(g[0])
   False
   

Field creation
--------------

.. _external:

External variables
------------------

External variables named are those referred to in the dataset, but
which are not present in it. Instead such variables are stored in
other files known as "external files". External variables may,
however, be incorporated into the field constructs of the dataset, as
if they had actually been stored in the same file, simply by providing
the external file names to the `cfdm.read` function.

This is illustrated with the files **parent.nc** (:download:`download
<../netcdf_files/parent.nc>`) and **external.nc** (:download:`download
<../netcdf_files/external.nc>`) [#files]_:

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
   		:Conventions = "1.7" ;
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
   		:Conventions = "1.7" ;
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

   >>> c = f.get_construct('measure%area')
   >>> c
   <CellMeasure: measure%area >
   >>> c.nc_get_external()
   True
   >>> c.nc_get_variable()
   'areacella'
   >>> c.properties()
   {}
   >>> c.has_data()
   False

If this field were to be written to disk using `cfdm.write`, then the
output file would be identical to the original **parent.nc** file,
i.e. the netCDF variable name of the cell measure construct
("areacella") would be listed by the "external_variables" global
attribute.

The dataset may also be read with specifying the external file. In
this case a cell measure construct is created with all of the metadata
or data from the external file, as if the cell measure variable had
been present in the parent dataset:

.. code:: python
   
   >>> g = cfdm.read('parent.nc', external_files='external.nc')[0]
   >>> print(g)
   Field: eastward_wind (ncvar%eastward_wind)
   ------------------------------------------
   Data            : eastward_wind(latitude(10), longitude(9)) m s-1
   Dimension coords: latitude(10) = [0.0, ..., 9.0] degrees
                   : longitude(9) = [0.0, ..., 8.0] degrees
   Cell measures   : cell_area(longitude(9), latitude(10)) = [[100000.5, ..., 100089.5]] m2
   >>> c = g.get_construct('cell_area')
   >>> c
   <CellMeasure: cell_area(9, 10) m2>
   >>> c.nc_get_external()
   False
   >>> c.nc_get_variable()
   'areacella'
   >>> c.properties()
   {'standard_name': 'cell_area', 'units': 'm2'}
   >>> c.get_data()
   <Data: [[100000.5, ..., 100089.5]] m2>
   
If this field were to be written to disk using `cfdm.write` then, by
default, the cell measure construct, with all of its metadata and
data, would be written to the output file, along with all of the other
constructs. There would be no "external_variables" global attribute.

In order to write a construct to an external file, and refer to it
with the "external_variables" global attribute in the parent output
file, simply set the status of the construct to "external" and provide
an external file name to the `cfdm.write` function:

.. code:: python

   >>> c.nc_set_external(True)
   False
   >>> cfdm.write(g, 'new_parent.nc', external_file='new_external.nc')
   
Discrete sampling geometries
----------------------------

The CF data model views data arrays that have been compressed by
convention in their uncompressed form. So, when a collection of
`discrete sampling geometry (DSG)
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


A subspace created by indexing will no longer be compressed,
i.e. its underlying array will be in incomplete multidimensional
representation. The original data will, however, retain its underlying
compressed array.

If the data elements are modified by indexed assignment then the
underlying compressed array is replaced by its uncompressed form.

Indexing is based on the axes of the uncompressed form of the data.

A count variable that is required to uncompress a contiguous, or
indexed contiguous, ragged array is stored in a `Count` object and is
retrieved with the `get_count_variable` method of the `Data` object.

An index variable that is required to uncompress a indexed, or indexed
contiguous, ragged array is stored in an `Index` object and is
retrieved with the `get_index_variable` method of the `Data` object.

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

Reading and inspecting this file shows the data presented in
two-dimensional uncompressed form, whilst the underlying array is
still in the one-dimension ragged representation described in the
file:

.. code:: python
   
   >>> c = cfdm.read('contiguous.nc')[0]
   >>> print(c)
   >>> c.data.get_compression_type()
   >>> c.get_array()
   >>> c.data.get_compressed_array()
   >>> count = c.data.get_count_variable()
   >>> count
   >>> count.get_array()

We can easily select the timeseries for the second station by indexing
the first (i.e. station) axis of the field construct:

.. code:: python
	  
   >>> ts1 = c[1]
   TODO
   >>> ts1.get_array()
   TODO
   
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
code creates an auxiliary coordinate construct with an underlying
contiguous ragged array:

.. code:: python

   import cfdm, numpy

   # Define the ragged array values
   ragged_array = numpy.array([1, 3, 4, 3, 6], dtype='float32')
   # Define the count array values
   count_array = [2, 3]

   # Initialise the count variable
   count_variable = cfdm.Count(data=cfdm.Data(count_array))
   count_variable.set_property('long_name', 'number of obs for this timeseries')

   # Initialise the contiguous ragged array object
   array = cfdm.RaggedContiguousArray(
                    compressed_array=cfdm.Data(ragged_array),
                    shape=(2, 3), size=6, ndim=2,
                    count_variable=count_variable)

   # Initialize the auxiliary coordinate construct with the ragged
   # array and set some properties
   z = cfdm.AuxiliaryCoordinate(
                    data=cfdm.Data(array),
                    properties={'standard_name': 'height',
                                'units': 'km',
                                'positive': 'up'})

We can now inspect the new auxiliary coordinate construct:

.. code:: python
   
   >>> z
   <AuxiliaryCoordinate: height(2, 3) km>
   >>> z.get_array()
   masked_array(
     data=[[1.0, 3.0, --],
           [4.0, 3.0, 6.0]],
     mask=[[False, False,  True],
           [False, False, False]],
     fill_value=1e+20,
     dtype=float32)
   >>> z.data.get_compression_type()
   'ragged contiguous'
   >>> z.data.get_compressed_array()
   array([1., 3., 4., 3., 6.], dtype=float32)
   >>> z.data.get_count_variable()
   <Count: long_name:number of obs for this timeseries(2) >
   >>> z.data.get_count_variable().get_array()
   array([2, 3])

Gathering
---------

The CF data model views data arrays that have been compressed by
convention in their uncompressed form. So, when axes have been
`compressed by gathering
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
in the special `GatheredArray` array object. The following code creates
a simple field construct an underlying gathered array:

.. code:: python

   import cfdm, numpy

   # Define the gathered values
   gathered_array = numpy.array([[280, 282.5, 281], [279, 278, 277.5]],
                                dtype='float32')
   # Define the list array values
   list_array = [1, 4, 5]

   # Initialise the list variable
   list_variable = cfdm.List(data=cfdm.Data(list_array))

   # Initialise the gathered array object
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
compressed dimension in the compressed array.

We can now inspect the new field construct:

.. code:: python
   
   >>> tas.get_array()
   masked_array(
     data=[[[--, 280.0],
            [--, --],
            [282.5, 281.0]],
     
           [[--, 279.0],
            [--, --],
            [278.0, 277.5]]],
     mask=[[[ True, False],
            [ True,  True],
            [False, False]],
     
           [[ True, False],
            [ True,  True],
            [False, False]]],
     fill_value=1e+20,
     dtype=float32)
   >>> tas.data.get_compression_type()
   'gathered'
   >>> tas.data.get_compressed_array()
   array([[280. , 282.5, 281. ],
          [279. , 278. , 277.5]], dtype=float32)
   >>> tas.data.get_list_variable()
   <List: (3) >
   >>> tas.data.get_list_variable().get_array()
   array([1, 4, 5])

----

.. rubric:: Footnotes
	    
.. [#opendap] Requires the netCDF-4 C library to have been compiled
              with OPeNDAP support enabled.

.. [#files] Tutorial files may be also found in the `docs/netcdf_files
            <https://github.com/NCAS-CMS/cfdm/tree/master/docs/netcdf_files>`_
            directory of the installation.

