.. Currentmodule:: cfdm
.. default-role:: obj

.. _Tutorial:


**Tutorial**
============

----

Version |release| for version |version| of the CF conventions.

All of the Python code in this tutorial is available in an executable
script (:download:`download <../source/tutorial.py>`, 12kB).

.. contents::
   :local:
   :backlinks: entry

.. include:: sample_datasets.rst

.. _Import:

**Import**
----------

The cfdm package is imported as follows:

.. code-block:: python
   :caption: *Import the cfdm package.*

   >>> import cfdm

.. _CF-version:

CF version
^^^^^^^^^^

The version of the `CF conventions <http://cfconventions.org>`_ and
the :ref:`CF data model <CF-data-model>` being used may be found with
the `cfdm.CF` function:

.. code-block:: python
   :caption: *Retrieve the version of the CF conventions.*
      
   >>> cfdm.CF()
   '1.8'

This indicates which version of the CF conventions are represented by
this release of the cfdm package, and therefore the version can not be
changed.

Note, however, that datasets of different versions may be :ref:`read
<Reading-datasets>` from, or :ref:`written <Writing-to-disk>` to,
disk.


----

**Controlling messages output by cfdm**
---------------------------------------

`cfdm` will produce messages upon the execution of operations, to provide
feedback about:

* the progress of, and under-the-hood steps involved in, the operations it
  is performing;
* the events that emerge during these operations;
* the nature of the dataset being operated on, including CF compliance
  issues that may be encountered during the operation.

This feedback may be purely informational, or may convey warning(s) about
dataset issues or the potential for future error(s).

It is possible to configure the extent to which messages are output
at runtime, i.e. the verbosity of `cfdm`, so that less serious
and/or more detailed messages can be filtered out.

There are two means to do this, which are covered in more detail in the
sub-sections below. Namely, you may configure the extent of messaging:

* **globally** i.e. for all `cfdm` operations, by setting the
  `cfdm.LOG_LEVEL` which controls the project-wide logging;
* **for a specific function only** (for many functions) by setting that
  function's `verbose` keyword argument (which overrides the
  global setting for the duration of the function call).

Both possibilities use a consistent level-based cut-off system, as
detailed below.


.. _logging:

Logging
^^^^^^^

All messages from `cfdm`, excluding exceptions which are always raised in
error cases, are incorporated into a logging system which assigns to each
a level based on the relative seriousness and/or verbosity. From highest to
lowest on this scale, these levels are:

* `WARNING`: conveys a warning;
* `INFO`: provides information concisely, in a few lines or so;
* `DETAIL`: provides information in a more detailed manner than `INFO`;
* `DEBUG`: produces highly-verbose information intended mainly for
  the purposes of debugging & `cfdm` library development.

The function `cfdm.LOG_LEVEL` sets the minimum of these levels for
which messages are displayed. Any message marked as being of any lower
level will be filtered out. Note it sets the verbosity *globally*, for *all*
`cfdm` library operations (unless these are overridden for individual
functions, as covered below).

As well as the named log levels above, `cfdm.LOG_LEVEL` accepts a
further identifier, `DISABLE`. Each of these potential settings has a
numerical value that is treated interchangeably and may instead be set (as
this may be easier to recall and write, if less explicit). The
resulting behaviour in each case is as follows:

===================  ============  =========================================
Level                Integer code  Result when set as the log severity level
===================  ============  =========================================
`DISABLE`            0             *Disable all* logging messages. Note this
                                   does not include exception messages
                                   raised by errors.

`WARNING` (default)  1             *Only show* logging messages that are
                                   *warnings* (those labelled as `WARNING`).

`INFO`               2             *Only show* logging messages that are
                                   *warnings or concise informational
                                   messages* (marked as `WARNING` or `INFO`
                                   respectively).

`DETAIL`             3             *Enable all* logging messages *except for
                                   debugging messages*. In other words,
                                   show logging messages labelled
                                   `WARNING`, `INFO` and `DETAIL`, but not
                                   `DEBUG`.

`DEBUG`              -1            *Enable all* logging messages, *including
                                   debugging messages* (labelled as
                                   `DEBUG`).
===================  ============  =========================================

Note `DEBUG` is intended as a special case for debugging, which should
not be required in general usage of `cfdm`, hence its equivalence to `-1`
rather than `4` which would follow the increasing integer code pattern.
`-1` reflects that it is the final value in the sequence, as with
Python indexing.

The default value for `cfdm.LOG_LEVEL` is `'WARNING'` (`1`).
However, whilst completing this tutorial, it may be instructive to set the
`LOG_LEVEL` to a higher verbosity level such as `'INFO'` to
gain insight into the internal workings of `cfdm` calls.


Function verbosity
^^^^^^^^^^^^^^^^^^

Functions and methods that involve a particularly high number of steps or
especially complex processing, for example the `cfdm.read` and `cfdm.write`
functions, accept a keyword argument `verbose`. This be set to
change the minimum log level at which messages are displayed for the
function/method call only, without being influenced by, or influencing,
the global `cfdm.LOG_LEVEL` value.

A `verbose` value effectively overrides the value of
`cfdm.LOG_LEVEL` for the function/method along with any
functions/methods it calls in turn, until the origin function/method
completes.

The `verbose` argument accepts the same levels as
`cfdm.LOG_LEVEL` (including `0` for `DISABLE`), as listed in
:ref:`the table in the section above <logging>`, however to
keep the keyword simple, only the integer code is recognised and should
be used, not the string name. For example, `verbose=2` should be set
rather than `verbose='INFO'`.

By default, `verbose` is set to `None`, in which case the value of the
`cfdm.LOG_LEVEL` setting is used to determine which messages,
if any, are filtered out.


----

**Field construct**
-------------------

The central construct (i.e. element) to CF is the :term:`field
construct`. The field construct, that corresponds to a CF-netCDF data
variable, includes all of the metadata to describe it:

    * descriptive properties that apply to field construct as a whole
      (e.g. the standard name),
    * a data array, and
    * "metadata constructs" that describe the locations of each cell
      of the data array, and the physical nature of each cell's datum.

A field construct is stored in a `cfdm.Field` instance, and henceforth
the phrase "field construct" will be assumed to mean "`cfdm.Field`
instance".

----

.. _Reading-datasets:

**Reading field constructs from datasets**
------------------------------------------

The `cfdm.read` function reads a `netCDF
<https://www.unidata.ucar.edu/software/netcdf/>`_ file from disk, or
from an `OPeNDAP <https://www.opendap.org/>`_ URL [#dap]_, and returns
the contents as a Python list of zero or field constructs. The list
contains a field construct to represent each of the CF-netCDF data
variables in the file.

Datasets of any version of CF up to and including CF-|version| can be
read.

All formats of netCDF3 and netCDF4 files can be read.

The following file types can be read:

* All formats of netCDF3 and netCDF4 files can be read, containing
  datasets for versions of CF up to and including CF-|version|.

..

* Files in `CDL format
  <https://www.unidata.ucar.edu/software/netcdf/docs/netcdf_working_with_netcdf_files.html#netcdf_utilities>`_,
  with or without the data array values.

..

* A future |version|.\ *x* release of cfdm will include support for
  :ref:`netCDF4 files containing data organised in hierarchical groups
  <Hierarchical-groups>`, but this is not available in version
  |release| (even though it is allowed in CF-|version|).

For example, to read the file ``file.nc`` (found in the :ref:`sample
datasets <Sample-datasets>`), which contains two field
constructs:

.. code-block:: python
   :caption: *Read file.nc and show that the result is a two-element
             list.*
		
   >>> x = cfdm.read('file.nc')
   >>> print(type(x))
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
  by default as data variables in their own right;

* request that masking is *not* applied by convention to data elements
  (see :ref:`data masking <Data-mask>`);

* issue warnings when ``valid_min``, ``valid_max`` and ``valid_range``
  attributes are present (see :ref:`data masking <Data-mask>`); and

* display information and issue warnings about the mapping of the
  netCDF file contents to CF data model constructs.

.. _CF-compliance:

CF-compliance
^^^^^^^^^^^^^
  
If the dataset is partially CF-compliant to the extent that it is not
possible to unambiguously map an element of the netCDF dataset to an
element of the CF data model, then a field construct is still
returned, but may be incomplete. This is so that datasets which are
partially conformant may nonetheless be modified in memory and written
to new datasets. Such "structural" non-compliance would occur, for
example, if the ``coordinates`` attribute of a CF-netCDF data variable
refers to another variable that does not exist, or refers to a
variable that spans a netCDF dimension that does not apply to the data
variable. Other types of non-compliance are not checked, such whether
or not controlled vocabularies have been adhered to. The structural
compliance of the dataset may be checked with the
`~cfdm.Field.dataset_compliance` method of the field construct, as
well as optionally displayed when the dataset is read.

----

.. _Inspection:

**Inspection**
--------------

The contents of a field construct may be inspected at three different
levels of detail.

.. _Minimal-detail:

Minimal detail
^^^^^^^^^^^^^^

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

Medium detail
^^^^^^^^^^^^^

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
                   : long_name=Grid latitude name(grid_latitude(10)) = [--, ..., kappa]
   Cell measures   : measure:area(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2
   Coord references: atmosphere_hybrid_height_coordinate
                   : rotated_latitude_longitude
   Domain ancils   : ncvar%a(atmosphere_hybrid_height_coordinate(1)) = [10.0] m
                   : ncvar%b(atmosphere_hybrid_height_coordinate(1)) = [20.0]
                   : surface_altitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 270.0]] m

Note that :ref:`time values <Time>` are converted to date-times with
the `cftime package <https://unidata.github.io/cftime/>`_.
		   
.. _Full-detail:

Full detail
^^^^^^^^^^^

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
   
   Auxiliary coordinate: long_name=Grid latitude name
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
   
   Cell measure: measure:area
       units = 'km2'
       Data(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2

  
.. _cfdump:
       
cfdump
^^^^^^

The description for every field construct in a file can also be
generated from the command line, with minimal, medium or full detail,
by using the ``cfdump`` tool, for example:

.. code-block:: console
   :caption: *Use cfdump on the command line to inspect the field
             constructs contained in a dataset. The "-s" option
             requests short, minimal detail as output.*

   $ cfdump
   USAGE: cfdump [-s] [-c] [-e file [-e file] ...] [-h] file
     [-s]      Display short, one-line descriptions
     [-c]      Display complete descriptions
     [-e file] External files
     [-h]      Display the full man page
     file      Name of netCDF file (or URL if DAP access enabled)
   $ cfdump -s file.nc
   Field: specific_humidity(latitude(5), longitude(8)) 1
   Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K

``cfdump`` may also be used with :ref:`external files
<External-variables-with-cfdump>`.

----

.. _Properties:

**Properties**
--------------

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
   >>> t.get_property('standard_name', default='not set')
   'not set'
   >>> t.set_property('standard_name', value='air_temperature')
   >>> t.get_property('standard_name', default='not set')
   'air_temperature'

A collection of properties may be set at the same time with the
`~Field.set_properties` method of the field construct, and all
properties may be completely removed with the
`~Field.clear_properties` method.

.. code-block:: python
   :caption: *Update the properties with a collection, delete all of
             the properties, and reinstate the original properties.*
	     
   >>> original = t.properties()
   >>> original
   {'Conventions': 'CF-1.7',
    'project': 'research',
    'standard_name': 'air_temperature',
    'units': 'K'}
   >>> t.set_properties({'foo': 'bar', 'units': 'K'})
   >>> t.properties()
   {'Conventions': 'CF-1.7',
    'foo': 'bar',
    'project': 'research',
    'standard_name': 'air_temperature',
    'units': 'K'}
   >>> t.clear_properties()
    {'Conventions': 'CF-1.7',
    'foo': 'bar',
    'project': 'research',
    'standard_name': 'air_temperature',
    'units': 'K'}
   >>> t.properties()
   {}
   >>> t.set_properties(original)
   >>> t.properties()
   {'Conventions': 'CF-1.7',
    'project': 'research',
    'standard_name': 'air_temperature',
    'units': 'K'}

All of the methods related to the properties are listed :ref:`here
<Field-Properties>`.

----

.. _Metadata-constructs:

**Metadata constructs**
-----------------------

The metadata constructs describe the field construct that contains
them. Each :ref:`CF data model metadata construct <CF-data-model>` has
a corresponding cfdm class:

=====================  ==============================================================  ==============================
Class                  CF data model construct                                         Description                     
=====================  ==============================================================  ==============================
`DomainAxis`           :term:`Domain axis <domain axis constructs>`                    Independent axes of the domain
`DimensionCoordinate`  :term:`Dimension coordinate <dimension coordinate constructs>`  Domain cell locations         
`AuxiliaryCoordinate`  :term:`Auxiliary coordinate <auxiliary coordinate constructs>`  Domain cell locations         
`CoordinateReference`  :term:`Coordinate reference <coordinate reference constructs>`  Domain coordinate systems     
`DomainAncillary`      :term:`Domain ancillary <domain ancillary constructs>`          Cell locations in alternative 
                                                                                       coordinate systems	       
`CellMeasure`          :term:`Cell measure <cell measure constructs>`                  Domain cell size or shape     
`FieldAncillary`       :term:`Field ancillary <field ancillary constructs>`            Ancillary metadata which vary 
                                                                                       within the domain	       
`CellMethod`           :term:`Cell method <cell method constructs>`                    Describes how data represent  
                                                                                       variation within cells	       
=====================  ==============================================================  ==============================

Metadata constructs of a particular type can be retrieved with the
following attributes of the field construct:

==============================  =====================  
Attribute                       Metadata constructs    
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

Each of these attributes returns a `Constructs` class instance that
maps metadata constructs to unique identifiers called "construct
keys". A `~Constructs` instance has methods for selecting constructs
that meet particular criteria (see the section on :ref:`filtering
metadata constructs <Filtering-metadata-constructs>`). It also behaves
like a "read-only" Python dictionary, in that it has
`~Constructs.items`, `~Constructs.keys` and `~Constructs.values`
methods that work exactly like their corresponding `dict` methods. It
also has a `~Constructs.get` method and indexing like a Python
dictionary (see the section on :ref:`metadata construct access
<Metadata-construct-access>` for details).

.. Each of these methods returns a dictionary whose values are the
   metadata constructs of one type, keyed by a unique identifier
   called a "construct key":

.. code-block:: python
   :caption: *Retrieve the field construct's coordinate reference
             constructs, and access them using dictionary methods.*
      
   >>> t.coordinate_references
   <Constructs: coordinate_reference(2)>
   >>> print(t.coordinate_references)
   Constructs:
   {'coordinatereference0': <CoordinateReference: atmosphere_hybrid_height_coordinate>,
    'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>}
   >>> list(t.coordinate_references.keys())
   ['coordinatereference0', 'coordinatereference1']
   >>> for key, value in t.coordinate_references.items():
   ...     print(key, repr(value))
   ...
   coordinatereference1 <CoordinateReference: rotated_latitude_longitude>
   coordinatereference0 <CoordinateReference: atmosphere_hybrid_height_coordinate>

.. code-block:: python
   :caption: *Retrieve the field construct's dimension coordinate and
             domain axis constructs.*
      
   >>> print(t.dimension_coordinates)
   Constructs:
   {'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
    'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}
   >>> print(t.domain_axes)
   Constructs:
   {'domainaxis0': <DomainAxis: size(1)>,
    'domainaxis1': <DomainAxis: size(10)>,
    'domainaxis2': <DomainAxis: size(9)>,
    'domainaxis3': <DomainAxis: size(1)>}

The construct keys (e.g. ``'domainaxis1'``) are usually generated
internally and are unique within the field construct. However,
construct keys may be different for equivalent metadata constructs
from different field constructs, and for different Python sessions.

Metadata constructs of all types may be returned by the
`~Field.constructs` attribute of the field construct:

.. code-block:: python
   :caption: *Retrieve all of the field construct's metadata
             constructs.*

   >>> q.constructs
   <Constructs: cell_method(1), dimension_coordinate(3), domain_axis(3)>
   >>> print(q.constructs)
   Constructs:
   {'cellmethod0': <CellMethod: area: mean>,
    'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>,
    'dimensioncoordinate1': <DimensionCoordinate: longitude(8) degrees_east>,
    'dimensioncoordinate2': <DimensionCoordinate: time(1) days since 2018-12-01 >,
    'domainaxis0': <DomainAxis: size(5)>,
    'domainaxis1': <DomainAxis: size(8)>,
    'domainaxis2': <DomainAxis: size(1)>}
   >>> t.constructs
   <Constructs: auxiliary_coordinate(3), cell_measure(1), cell_method(2), coordinate_reference(2), dimension_coordinate(4), domain_ancillary(3), domain_axis(4), field_ancillary(1)>
   >>> print(t.constructs)
   Constructs:
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
    'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
    'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name=Grid latitude name(10) >,
    'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>,
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
    'domainaxis0': <DomainAxis: size(1)>,
    'domainaxis1': <DomainAxis: size(10)>,
    'domainaxis2': <DomainAxis: size(9)>,
    'domainaxis3': <DomainAxis: size(1)>,
    'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}

----

.. _Data:

**Data**
--------

The field construct's data is stored in a `Data` class instance that
is accessed with the `~Field.data` attribute of the field construct.

.. code-block:: python
   :caption: *Retrieve the data and inspect it, showing the shape and
             some illustrative values.*
		
   >>> t.data
   <Data(1, 10, 9): [[[262.8, ..., 269.7]]] K>

The `Data` instance provides access to the full array of values, as
well as attributes to describe the array and methods for describing
any :ref:`data compression <Compression>`.

The `Data` instance provides access to the full array of values, as
well as attributes to describe the array and methods for describing
any data compression. However, the field construct (and any other
construct that contains data) also provides attributes for direct
access.

.. code-block:: python
   :caption: *Retrieve a numpy array of the data.*
      
   >>> print(t.data.array)
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

.. code-block:: python
   :caption: *Inspect the data type, number of dimensions, dimension
             sizes and number of elements of the data.*
	     
   >>> t.dtype
   dtype('float64')
   >>> t.ndim
   3
   >>> t.shape
   (1, 10, 9)
   >>> t.size
   90
   >>> t.data.size
   90

Note it is preferable to access the data type, number of dimensions,
dimension sizes and number of elements of the data via the parent
construct, rather than from the `Data` instance, as there are
:ref:`particular circumstances <Geometry-cells>` when there is no
`Data` instance, but the construct nonetheless has data descriptors.
   
The field construct also has a `~Field.get_data` method as an
alternative means of retrieving the data instance, which allows for a
default to be returned if no data have been set; as well as a
`~Field.del_data` method for removing the data.

All of the methods and attributes related to the data are listed
:ref:`here <Field-Data>`.

.. _Data-axes:

Data axes
^^^^^^^^^

The data array of the field construct spans all the :term:`domain axis
constructs` with the possible exception of size one domain axis
constructs. The domain axis constructs spanned by the field
construct's data are found with the `~Field.get_data_axes` method of
the field construct. For example, the data of the field construct
``t`` does not span the size one domain axis construct with key
``'domainaxis3'``.

.. code-block:: python
   :caption: *Show which data axis constructs are spanned by the field
             construct's data.*
	    
   >>> print(t.domain_axes)
   Constructs:
   {'domainaxis0': <DomainAxis: size(1)>,
    'domainaxis1': <DomainAxis: size(10)>,
    'domainaxis2': <DomainAxis: size(9)>,
    'domainaxis3': <DomainAxis: size(1)>}
   >>> t
   <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>
   >>> t.shape
   (1, 10, 9)
   >>> t.get_data_axes()
   ('domainaxis0', 'domainaxis1', 'domainaxis2')

The data may be set with the `~Field.set_data` method of the field
construct. The domain axis constructs spanned by the data may also be
set by explicitly providing them via their construct keys. In any
case, the data axes may be set at any time with the
`~Field.set_data_axes` method of the field construct.

.. code-block:: python
   :caption: *Delete the data and then reinstate it, using the
             existing data axes.*
	    
   >>> data = t.del_data()
   >>> t.has_data()
   False
   >>> t.set_data(data, axes=None)
   >>> t.data
   <Data(1, 10, 9): [[[262.8, ..., 269.7]]] K>

See the section :ref:`field construct creation <Field-creation>` for
more examples.

.. _Date-time:

Date-time
^^^^^^^^^

Data representing date-times is defined as elapsed times since a
reference date-time in a particular calendar (Gregorian, by
default). The `~cfdm.Data.array` attribute of the `Data` instance
(and any construct that contains it) returns the elapsed times, and
the `~cfdm.Data.datetime_array` (and any construct that contains it)
returns the data as an array of date-time objects.

.. code-block:: python
   :caption: *View date-times aas elapsed time or as date-time
             objects.*
	     
   >>> d = cfdm.Data([1, 2, 3], units='days since 2004-2-28')
   >>> print(d.array)   
   [1 2 3]
   >>> print(d.datetime_array)
   [cftime.DatetimeGregorian(2004-02-29 00:00:00)
    cftime.DatetimeGregorian(2004-03-01 00:00:00)
    cftime.DatetimeGregorian(2004-03-02 00:00:00)]
   >>> e = cfdm.Data([1, 2, 3], units='days since 2004-2-28',
   ...               calendar='360_day')
   >>> print(e.array)   
   [1 2 3]
   >>> print(e.datetime_array)
   [cftime.Datetime360Day(2004-02-29 00:00:00)
    cftime.Datetime360Day(2004-02-30 00:00:00)
    cftime.Datetime360Day(2004-03-01 00:00:00)]

    
.. _Manipulating-dimensions:

Manipulating dimensions
^^^^^^^^^^^^^^^^^^^^^^^

The dimensions of a field construct's data may be reordered, have size
one dimensions removed and have new new size one dimensions included
by using the following field construct methods:

=========================  ===========================================
Method                     Description
=========================  ===========================================
`~Field.insert_dimension`  Insert a new size one data dimension. The
                           new dimension must correspond to an
                           existing size one domain axis construct.

`~Field.squeeze`           Remove size one data dimensions
	   
`~Field.transpose`         Reorder data dimensions
=========================  ===========================================

.. code-block:: python
   :caption: *Remove all size one dimensions from the data, noting
             that metadata constructs which span the corresponding
             domain axis construct are not affected.*

   >>> q, t = cfdm.read('file.nc')
   >>> t
   <CF Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>
   >>> t2 = t.squeeze()
   >>> t2
   <CF Field: air_temperature(grid_latitude(10), grid_longitude(9)) K>
   >>> print(t2.dimension_coordinates)
   Constructs:
   {'dimensioncoordinate0': <CF DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
    'dimensioncoordinate1': <CF DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <CF DimensionCoordinate: grid_longitude(9) degrees>,
    'dimensioncoordinate3': <CF DimensionCoordinate: time(1) days since 2018-12-01 >}

.. code-block:: python
   :caption: *Insert a new size one dimension, corresponding to a size
             one domain axis construct, and then reorder the
             dimensions.*

   >>> t3 = t2.insert_dimension(axis='domainaxis3', position=1)
   >>> t3
   <CF Field: air_temperature(grid_latitude(10), time(1), grid_longitude(9)) K>
   >>> t3.transpose([2, 0, 1])
   <CF Field: air_temperature(grid_longitude(9), grid_latitude(10), time(1)) K>

When transposing the data dimensions, the dimensions of metadata
construct data are, by default, unchanged. It is also possible to
permute the data dimensions of the metadata constructs so that they
have the same relative order as the field construct:

.. code-block:: python
   :caption: *Also permute the data dimension of metadata constructs
             using the 'constructs' keyword.*

   >>> t4 = t.transpose([0, 2, 1], constructs=True)

.. _Data-mask:
   
Data mask
^^^^^^^^^

There is always a data mask, which may be thought of as a separate
data array of booleans with the same shape as the original data. The
data mask is `False` where the the data has values, and `True` where
the data is missing. The data mask may be inspected with the
`~cfdm.Data.mask` attribute of the data instance, which returns the
data mask in a field construct with the same metadata constructs as
the original field construct.


.. code-block:: python
   :caption: *Inspect the data mask of a field construct.*

   >>> print(q)
   Field: specific_humidity (ncvar%q)
   ----------------------------------
   Data            : specific_humidity(latitude(5), longitude(8)) 1
   Cell methods    : area: mean
   Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                   : longitude(8) = [22.5, ..., 337.5] degrees_east
                   : time(1) = [2019-01-01 00:00:00]
   >>> print(q.data.mask)
   <Data(5, 8): [[False, ..., False]]>
   >>> print(q.data.mask.array)
   [[False False False False False False False False]
    [False False False False False False False False]
    [False False False False False False False False]
    [False False False False False False False False]
    [False False False False False False False False]]

.. code-block:: python
   :caption: *Mask the polar rows (see the "Assignment by index"
             section) and inspect the new data mask.*
	  
   >>> q.data[[0, 4], :] = cfdm.masked            
   >>> print(q.data.mask.array)
   [[ True  True  True  True  True  True  True  True]
    [False False False False False False False False]
    [False False False False False False False False]
    [False False False False False False False False]
    [ True  True  True  True  True  True  True  True]]

The ``_FillValue`` and ``missing_value`` attributes of the field
construct are *not* stored as values of the field construct's
data. They are only used when :ref:`writing the data to a netCDF
dataset <Writing-to-a-netCDF-dataset>`. Therefore testing for missing
data by testing for equality to one of these property values will
produce incorrect results; the `~Data.any` method of the `Data`
instance should be used instead.

.. code-block:: python
   :caption: *See if any data points are masked.*
	     
   >>> q.data.mask.any()
   True

The mask of a netCDF dataset array is implied by array values that
meet the criteria implied by the ``missing_value``, ``_FillValue``,
``valid_min``, ``valid_max``, and ``valid_range`` properties, and is
usually applied automatically by `cfdm.read`. NetCDF data elements
that equal the values of the ``missing_value`` and ``_FillValue``
properties are masked, as are data elements that exceed the value of
the ``valid_max`` property, subceed the value of the ``valid_min``
property, or lie outside of the range defined by the ``valid_range``
property.

However, this automatic masking may be bypassed by setting the *mask*
keyword of the `cfdm.read` function to `False`. The mask, as defined
in the dataset, may subsequently be applied manually with the
`~Field.apply_masking` method of the field construct.

.. code-block:: python
   :caption: *Read a dataset from disk without automatic masking, and
             then manually apply the mask*

   >>> cfdm.write(q, 'masked_q.nc')
   >>> no_mask_q = cfdm.read('masked_q.nc', mask=False)[0]
   >>> print(no_mask_q.data.array)
   [9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36,
    9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36],
    [0.023 0.036 0.045 0.062 0.046 0.073 0.006 0.066]
    [0.11  0.131 0.124 0.146 0.087 0.103 0.057 0.011]
    [0.029 0.059 0.039 0.07  0.058 0.072 0.009 0.017]
   [9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36,
    9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36]])
   >>> masked_q = no_mask_q.apply_masking()
   >>> print(masked_q.data.array)
   [[   --    --    --    --    --    --    --    --]
    [0.023 0.036 0.045 0.062 0.046 0.073 0.006 0.066]
    [0.11  0.131 0.124 0.146 0.087 0.103 0.057 0.011]
    [0.029 0.059 0.039 0.07  0.058 0.072 0.009 0.017]
    [   --    --    --    --    --    --    --    --]]

The `~Field.apply_masking` method of the field construct utilises as
many of the ``missing_value``, ``_FillValue``, ``valid_min``,
``valid_max``, and ``valid_range`` properties as are present and may
be used on any construct, not just those that have been read from
datasets.
    
.. _Indexing:

Indexing
^^^^^^^^

When a `Data` instance is indexed a new instance is created for the
part of the data defined by the indices. Indexing follows rules that
are very similar to the `numpy indexing rules
<https://numpy.org/doc/stable/user/basics.indexing.html>`_,
the only differences being:

* An integer index *i* specified for a dimension reduces the size of
  this dimension to unity, taking just the *i*\ -th element, but keeps
  the dimension itself, so that the rank of the array is not reduced.

..

* When two or more dimensions' indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same
  indexing behaviour as on a ``Variable`` object of the `netCDF4
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

Assignment
^^^^^^^^^^

Values can be changed by assigning to elements selected by indices of
the `Data` instance using rules that are very similar to the `numpy
indexing rules
<https://numpy.org/doc/stable/user/basics.indexing.html>`_,
the only difference being:

* When two or more dimensions' indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same
  indexing behaviour as on a ``Variable`` object of the `netCDF4
  package <http://unidata.github.io/netcdf4-python>`_.

A single value may be assigned to any number of elements.
  
.. code-block:: python
   :caption: *Set a single element to -1, a "column" of elements
             to -2 and a "square" of elements to -3.*
	     
   >>> import numpy
   >>> t.data[:, 0, 0] = -1
   >>> t.data[:, :, 1] = -2
   >>> t.data[..., 6:3:-1, 3:6] = -3
   >>> print(t.data.array)
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
<https://numpy.org/doc/stable/user/basics.broadcasting.html>`_.

.. code-block:: python
   :caption: *Overwrite the square of values of -3 with the numbers 0
             to 8, and set the corners of a different square to be
             either -4 or -5.*
	     
   >>> t.data[..., 6:3:-1, 3:6] = numpy.arange(9).reshape(3, 3)
   >>> t.data[0, [2, 9], [4, 8]] =  cfdm.Data([[-4, -5]])
   >>> print(t.data.array)
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
the `cfdm.masked` constant. Missing values may be unmasked by
assigning them to any other value.

.. code-block:: python
   :caption: *Set a column of elements to missing values, and then
             change one of them back to a non-missing value.*
	     
   >>> t.data[0, :, -2] = cfdm.masked
   >>> t.data[0, 5, -2] = -6
   >>> print(t.data.array)
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

Manipulating dimensions
^^^^^^^^^^^^^^^^^^^^^^^

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
   >>> print(t2.dimension_coordinates)
   Constructs:
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

----

.. _Subspacing:

**Subspacing**
--------------

Creation of a new field construct which spans a subspace of the domain
of an existing field construct is achieved by indexing the field
itself, rather than its `Data` instance. This is because the operation
must also subspace any metadata constructs of the field construct
(e.g. coordinate metadata constructs) which span any of the
:term:`domain axis constructs` that are affected. The new field
construct is created with the same properties as the original
field. Subspacing uses the same :ref:`cfdm indexing rules <Indexing>`
that apply to the `Data` class.

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

----

.. _Filtering-metadata-constructs:

**Filtering metadata constructs**
---------------------------------

A `Constructs` instance has filtering methods for selecting constructs
that meet various criteria:

================================  ==========================================================================  
Method                            Filter criteria                                                             
================================  ==========================================================================  
`~Constructs.filter_by_identity`  Metadata construct identity                
`~Constructs.filter_by_type`      Metadata construct type                       
`~Constructs.filter_by_property`  Property values                                     
`~Constructs.filter_by_axis`      The :term:`domain axis constructs` spanned by the data
`~Constructs.filter_by_naxes`     The number of :term:`domain axis constructs` spanned by the data
`~Constructs.filter_by_size`      The size :term:`domain axis constructs`
`~Constructs.filter_by_measure`   Measure value (for cell measure constructs)
`~Constructs.filter_by_method`    Method value (for cell method constructs)	
`~Constructs.filter_by_data`      Whether or not there could be be data.
`~Constructs.filter_by_key`       Construct key			
`~Constructs.filter_by_ncvar`     NetCDF variable name (see the :ref:`netCDF interface <NetCDF-interface>`)
`~Constructs.filter_by_ncdim`     NetCDF dimension name (see the :ref:`netCDF interface <NetCDF-interface>`)
================================  ==========================================================================  

Each of these methods returns a new `Constructs` instance that
contains the selected constructs.

.. code-block:: python
   :caption: *Get constructs by their type*.
	  
   >>> print(t.constructs.filter_by_type('dimension_coordinate'))
   Constructs:
   {'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
    'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}
   >>> print(t.constructs.filter_by_type('cell_method', 'field_ancillary'))
   Constructs:
   {'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
    'cellmethod1': <CellMethod: domainaxis3: maximum>,
    'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}

.. code-block:: python
   :caption: *Get constructs by their properties*.

   >>> print(t.constructs.filter_by_property(
   ...             standard_name='air_temperature standard_error'))
   Constructs:
   {'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}
   >>> print(t.constructs.filter_by_property(
   ...             standard_name='air_temperature standard_error',
   ...             units='K'))
   Constructs:
   {'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}
   >>> print(t.constructs.filter_by_property(
   ...             'or',
   ...	           standard_name='air_temperature standard_error',
   ...             units='m'))
   Constructs:
   {'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
    'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>,
    'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}
   
.. code-block:: python
   :caption: *Get constructs whose data span the 'domainaxis1' domain
             axis construct; and those which also do not span the
             'domainaxis2' domain axis construct.*

   >>> print(t.constructs.filter_by_axis('and', 'domainaxis1'))
   Constructs:
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
    'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
    'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name=Grid latitude name(10) >,
    'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>,
    'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}

.. code-block:: python
   :caption: *Get cell measure constructs by their "measure".*
	     
   >>> print(t.constructs.filter_by_measure('area'))
   Constructs:
   {'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>}

.. code-block:: python
   :caption: *Get cell method constructs by their "method".*
	     
   >>> print(t.constructs.filter_by_method('maximum'))
   Constructs:
   {'cellmethod1': <CellMethod: domainaxis3: maximum>}

As each of these methods returns a `Constructs` instance, it is easy
to perform further filters on their results:
   
.. code-block:: python
   :caption: *Make selections from previous selections.*
	     
   >>> print(t.constructs.filter_by_type('auxiliary_coordinate').filter_by_axis('and', 'domainaxis2'))
   Constructs:
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
    'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>}
   >>> c = t.constructs.filter_by_type('dimension_coordinate')
   >>> d = c.filter_by_property(units='degrees')
   >>> print(d)
   Constructs:
   {'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>}

Another method of selection is by metadata construct "identity".
Construct identities are used to describe constructs when they are
inspected, and so it is often convenient to copy these identities
when selecting metadata constructs. For example, the :ref:`three
auxiliary coordinate constructs <Medium-detail>` in the field
construct ``t`` have identities ``'latitude'``, ``'longitude'`` and
``'long_name=Grid latitude name'``.

A construct's identity may be any one of the following

* The value of the ``standard_name`` property,
  e.g. ``'air_temperature'``,
* The value of any property, preceded by the property name and an
  equals, e.g. ``'long_name=Air Temperature'``, ``'axis=X'``,
  ``'foo=bar'``, etc.,
* The cell measure, preceded by "measure:",
  e.g. ``'measure:volume'``
* The cell method, preceded by "method:", e.g. ``'method:maximum'``
* The netCDF variable name, preceded by "ncvar%",
  e.g. ``'ncvar%tas'`` (see the :ref:`netCDF interface
  <NetCDF-interface>`),
* The netCDF dimension name, preceded by "ncdim%" e.g. ``'ncdim%z'``
  (see the :ref:`netCDF interface <NetCDF-interface>`), and 
* The construct key, preceded by "key%"
  e.g. ``'key%auxiliarycoordinate2'``.

.. Valid construct names are used to describe constructs when they are
   inspected, and so it is often convenient to copy these names when
   selecting metadata constructs. For example, the :ref:`three
   auxiliary coordinate constructs <Medium-detail>` in the field
   construct ``t`` have names ``'latitude'``, ``'longitude'`` and
   ``'long_name=Grid latitude name'``.

.. code-block:: python
   :caption: *Get constructs by their identity.*
	
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
                   : long_name=Grid latitude name(grid_latitude(10)) = [--, ..., kappa]
   Cell measures   : measure:area(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2
   Coord references: atmosphere_hybrid_height_coordinate
                   : rotated_latitude_longitude
   Domain ancils   : ncvar%a(atmosphere_hybrid_height_coordinate(1)) = [10.0] m
                   : ncvar%b(atmosphere_hybrid_height_coordinate(1)) = [20.0]
                   : surface_altitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 270.0]] m
   >>> print(t.constructs.filter_by_identity('latitude'))
   Constructs:
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>}
   >>> print(t.constructs.filter_by_identity('long_name=Grid latitude name'))
   Constructs:
   {'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name=Grid latitude name(10) >}
   >>> print(t.constructs.filter_by_identity('measure:area'))
   Constructs:
   {'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>}
   >>> print(t.constructs.filter_by_identity('ncvar%b'))
   Constructs:
   {'domainancillary1': <DomainAncillary: ncvar%b(1) >}

Each construct has an `!identity` method that, by default, returns the
least ambiguous identity (defined in the documentation of a
construct's `!identity` method); and an `!identities` method that
returns a list of all of the identities that would select the
construct.

As a further convenience, selection by construct identity is also
possible by providing identities to a call of a `Constructs` instance
itself, and this technique for selecting constructs by identity will be
used in the rest of this tutorial:

.. code-block:: python
   :caption: *Construct selection by identity is possible with via the
             "filter_by_identity" method, or directly from the
             "Constructs" instance.*

   >>> print(t.constructs.filter_by_identity('latitude'))
   Constructs:
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>}
   >>> print(t.constructs('latitude'))
   Constructs:
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>}

Selection by construct key is useful for systematic metadata construct
access, or for when a metadata construct is not identifiable by other
means:

.. code-block:: python
   :caption: *Get constructs by construct key.*

   >>> print(t.constructs.filter_by_key('domainancillary2'))
   Constructs:
   {'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>}
   >>> print(t.constructs.filter_by_key('cellmethod1'))
   Constructs:
   {'cellmethod1': <CellMethod: domainaxis3: maximum>}
   >>> print(t.constructs.filter_by_key('auxiliarycoordinate2', 'cellmeasure0'))
   Constructs:
   {'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name=Grid latitude name(10) >,
    'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>}

If no constructs match the given criteria, then an "empty"
`Constructs` instance is returned:
   
.. code-block:: python
   :caption: *If no constructs meet the criteria then an empty
             "Constructs" object is returned.*

   >>> c = t.constructs('radiation_wavelength')
   >>> c
   <Constructs: >
   >>> print(c)
   Constructs:
   {}
   >>> len(c)
   0

The constructs that were *not* selected by a filter may be returned by
the `~Constructs.inverse_filter` method applied to the results of
filters:

.. code-block:: python
   :caption: *Get the constructs that were not selected by a filter.*

   >>> c = t.constructs.filter_by_type('auxiliary_coordinate')
   >>> c
   <Constructs: auxiliary_coordinate(3)>
   >>> c.inverse_filter()
   <Constructs: cell_measure(1), cell_method(2), coordinate_reference(2), dimension_coordinate(4), domain_ancillary(3), domain_axis(4), field_ancillary(1)>
  
Note that selection by construct type is equivalent to using the
particular method of the field construct for retrieving that type of
metadata construct:

.. code-block:: python
   :caption: *The bespoke methods for retrieving constructs by type
             are equivalent to a selection on all of the metadata
             constructs.*
		
   >>> print(t.constructs.filter_by_type('cell_measure'))
   Constructs:
   {'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>}
   >>> print(t.cell_measures)
   Constructs:
   {'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>}

----
   
.. _Metadata-construct-access:

**Metadata construct access**
-----------------------------

An individual metadata construct may be returned, without its
construct key, by any of the following techniques:

* with the `~Field.construct` method of a field construct,

.. code-block:: python
   :caption: *Get the "latitude" metadata construct with its construct
             identity.*
	     
   >>> t.construct('latitude')
   <AuxiliaryCoordinate: latitude(10, 9) degrees_N>

* with the `~Field.construct_key` and `~Field.get_construct` methods of
  a field construct:

.. code-block:: python
   :caption: *Get the "latitude" metadata construct key with its construct
             identity and use the key to get the construct itself*
	     
   >>> key = t.construct_key('latitude')
   >>> t.get_construct(key)
   <AuxiliaryCoordinate: latitude(10, 9) degrees_N>

* with the `~Constructs.value` method of a `Constructs` instance
  that contains one construct,

.. code-block:: python
   :caption: *Get the "latitude" metadata construct via its identity
             and the 'value' method.*
	     
   >>> t.constructs('latitude').value()
   <AuxiliaryCoordinate: latitude(10, 9) degrees_N>

* with the `~Constructs.get` method of a `Constructs` instance, or

.. code-block:: python
   :caption: *Get the "latitude" metadata construct via its construct
             key and the 'get' method.*
	     
   >>> c = t.constructs.get(key)
   <AuxiliaryCoordinate: latitude(10, 9) degrees_N>

* by indexing a `Constructs` instance with  a construct key.

.. code-block:: python
   :caption: *Get the "latitude" metadata construct via its construct
             key and indexing*
	     
   >>> t.constructs[key]
   <AuxiliaryCoordinate: latitude(10, 9) degrees_N>

The `~Field.construct` method of the field construct and the
`~Constructs.value` method of the `Constructs` instance will raise an
exception of there is not a unique metadata construct to return, but
this may be replaced with returning a default value or raising a
customised exception:
   
.. code-block:: python
   :caption: *By default an exception is raised if there is not a
             unique construct that meets the criteria. Alternatively,
             the value of the "default" parameter is returned.*

   >>> t.construct('measure:volume')                # Raises Exception
   Traceback (most recent call last):
      ...
   ValueError: Can't return zero constructs
   >>> t.construct('measure:volume', False)
   False
   >>> c = t.constructs.filter_by_measure('volume')
   >>> len(c)
   0
   >>> c.value()                                    # Raises Exception
   Traceback (most recent call last):
      ...
   ValueError: Can't return zero constructs
   >>> c.value(default='No construct')
   'No construct'
   >>> c.value(default=KeyError('My message'))      # Raises Exception
   Traceback (most recent call last):
      ...
   KeyError: 'My message'
   >>> d = t.constructs('units=degrees')
   >>> len(d)
   2
   >>> d.value()                                    # Raises Exception
   Traceback (most recent call last):
      ...
   ValueError: Can't return 2 constructs 
   >>> print(d.value(default=None))
   None

The `~Constructs.get` method of a `Constructs` instance accepts an
optional second argument to be returned if the construct key does not
exist, exactly like the Python `dict.get` method.

.. _Metadata-construct-properties:

Metadata construct properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Metadata constructs share the :ref:`same API as the field construct
<Properties>` for accessing their properties:

.. code-block:: python
   :caption: *Retrieve the "longitude" metadata construct, set a new
             property, and then inspect all of the properties.*

   >>> lon = q.construct('longitude')
   >>> lon
   <DimensionCoordinate: longitude(8) degrees_east>
   >>> lon.set_property('long_name', 'Longitude')
   >>> lon.properties()
   {'units': 'degrees_east',
    'long_name': 'Longitude',
    'standard_name': 'longitude'}

.. code-block:: python
   :caption: *Get the metadata construct with units of "km2", find its
             canonical identity, and all of its valid identities, that
             may be used for selection by the "filter_by_identity"
             method*

   >>> area = t.constructs.filter_by_property(units='km2').value()
   >>> area
   <CellMeasure: measure:area(9, 10) km2>
   >>> area.identity()
   'measure:area'
   >>> area.identities()
   ['measure:area', 'units=km2', 'ncvar%cell_measure']

.. _Metadata-construct-data:

Metadata construct data
^^^^^^^^^^^^^^^^^^^^^^^

Metadata constructs share the :ref:`a similar API as the field
construct <Data>` as the field construct for accessing their data:

.. code-block:: python
   :caption: *Retrieve the "longitude" metadata construct, inspect its
             data, change the third element of the array, and get the
             data as a numpy array.*
	     
   >>> lon = q.constructs('longitude').value()
   >>> lon
   <DimensionCoordinate: longitude(8) degrees_east>
   >>> lon.data
   <Data(8): [22.5, ..., 337.5] degrees_east>
   >>> lon.data[2]
   <Data(1): [112.5] degrees_east>
   >>> lon.data[2] = 133.33
   >>> print(lon.data.array)
   [22.5 67.5 133.33 157.5 202.5 247.5 292.5 337.5]

The :term:`domain axis constructs` spanned by a particular metadata
construct's data are found with the `~Constructs.get_data_axes` method
of the field construct:

.. code-block:: python
   :caption: *Find the construct keys of the domain axis constructs
             spanned by the data of each metadata construct.*

   >>> key = t.construct_key('latitude')
   >>> key
   'auxiliarycoordinate0'
   >>> t.get_data_axes(key=key)
   ('domainaxis1', 'domainaxis2')
    
The domain axis constructs spanned by all the data of all metadata
construct may be found with the `~Constructs.data_axes` method of the
field construct's `Constructs` instance:

.. code-block:: python
   :caption: *Find the construct keys of the domain axis constructs
             spanned by the data of each metadata construct.*

   >>> t.constructs.data_axes()
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

----

.. _Time:

**Time**
--------

Constructs representing elapsed time (identified by the presence of
"reference time" units) have data array values that represent elapsed
time since a reference date. These values may be converted into the
date-time objects of the `cftime package
<https://unidata.github.io/cftime/>`_ with the `~Data.datetime_array`
method of the `Data` instance.

.. code-block:: python
   :caption: *Inspect the the values of a "time" construct as elapsed
             times and as date-times.*

   >>> time = q.construct('time')
   >>> time
   <DimensionCoordinate: time(1) days since 2018-12-01 >
   >>> time.get_property('units')
   'days since 2018-12-01'
   >>> time.get_property('calendar', default='standard')
   'standard'
   >>> print(time.data.array)
   [ 31.]
   >>> print(time.data.datetime_array)
   [cftime.DatetimeGregorian(2019, 1, 1, 0, 0, 0, 0, 1, 1)]

----

.. _Domain:

**Domain**
----------

The :ref:`domain of the CF data model <CF-data-model>` is *not* a
construct, but is defined collectively by various other metadata
constructs included in the field construct. It is represented by the
`Domain` class. The domain instance may be accessed with the
`~Field.domain` attribute, or `~Field.get_domain` method, of the field
construct.

.. code-block:: python
   :caption: *Get the domain, and inspect it.*

   >>> domain = t.domain
   >>> domain
   <Domain: {1, 1, 9, 10}>
   >>> print(domain)
   Dimension coords: atmosphere_hybrid_height_coordinate(1) = [1.5]
                   : grid_latitude(10) = [2.2, ..., -1.76] degrees
                   : grid_longitude(9) = [-4.7, ..., -1.18] degrees
                   : time(1) = [2019-01-01 00:00:00]
   Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[53.941, ..., 50.225]] degrees_N
                   : longitude(grid_longitude(9), grid_latitude(10)) = [[2.004, ..., 8.156]] degrees_E
                   : long_name=Grid latitude name(grid_latitude(10)) = [--, ..., kappa]
   Cell measures   : measure:area(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2
   Coord references: atmosphere_hybrid_height_coordinate
                   : rotated_latitude_longitude
   Domain ancils   : ncvar%a(atmosphere_hybrid_height_coordinate(1)) = [10.0] m
                   : ncvar%b(atmosphere_hybrid_height_coordinate(1)) = [20.0]
                   : surface_altitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 270.0]] m
   >>> description = domain.dump(display=False)

Changes to domain instance are seen by the field construct, and vice
versa. This is because the domain instance is merely a "view" of the
relevant metadata constructs contained in the field construct.

.. The field construct also has a `~Field.domain` attribute that is an
   alias for the `~Field.get_domain` method, which makes it easier to
   access attributes and methods of the domain instance.

.. code-block:: python
   :caption: *Change a property of a metadata construct of the domain
             and show that this change appears in the same metadata
             data construct of the parent field, and vice versa.*

   >>> domain_latitude = t.domain.constructs('latitude').value()
   >>> field_latitude = t.constructs('latitude').value()
   >>> domain_latitude.set_property('test', 'set by domain')
   >>> print(field_latitude.get_property('test'))
   set by domain
   >>> field_latitude.set_property('test', 'set by field')
   >>> print(domain_latitude.get_property('test'))
   set by field
   >>> domain_latitude.del_property('test')
   'set by field'
   >>> field_latitude.has_property('test')
   False

All of the methods and attributes related to the domain are listed
:ref:`here <Field-Domain>`.

----

.. _Domain-axes:

**Domain axes**
---------------

A domain axis metadata construct specifies the number of points along
an independent axis of the field construct's domain and is stored in a
`~cfdm.DomainAxis` instance. The size of the axis is retrieved with
the `~cfdm.DomainAxis.get_size` method of the domain axis construct.

.. code-block:: python
   :caption: *Get the size of a domain axis construct.*

   >>> print(q.domain_axes)
   Constructs:
   {'domainaxis0': <DomainAxis: size(5)>,
    'domainaxis1': <DomainAxis: size(8)>,
    'domainaxis2': <DomainAxis: size(1)>}
   >>> d = q.domain_axes.get('domainaxis1')
   >>> d
   <DomainAxis: size(8)>
   >>> d.get_size()
   8

----

.. _Coordinates:
		
**Coordinates**
---------------

There are two types of coordinate construct, :term:`dimension
<dimension coordinate constructs>` and :term:`auxiliary coordinate
constructs`, which can be retrieved together with the
`~cfdm.Field.coordinates` method of the field construct, as well as
individually with the `~cfdm.Field.auxiliary_coordinates` and
`~cfdm.Field.dimension_coordinates` methods.

.. code-block:: python
   :caption: *Retrieve both types of coordinate constructs.*
      
   >>> print(t.coordinates)
   Constructs:
   {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
    'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
    'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name=Grid latitude name(10) >,
    'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
    'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
    'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
    'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

.. _Bounds:

Bounds
^^^^^^

A coordinate construct may contain an array of cell bounds that
provides the extent of each cell by defining the locations of the cell
vertices. This is in addition to the main coordinate data array that
contains a representative grid point location for each cell. The cell
bounds are stored in a `Bounds` class instance that is accessed with
the `~Coordinate.bounds` attribute, or `~Coordinate.get_bounds`
method, of the coordinate construct.

A `Bounds` instance shares the :ref:`the same API as the field
construct <Data>` for accessing its data.

.. code-block:: python
   :caption: *Get the Bounds instance of a coordinate construct and
             inspect its data.*
      
   >>> lon = t.constructs('grid_longitude').value()
   >>> bounds = lon.bounds
   >>> bounds
   <Bounds: grid_longitude(9, 2) >
   >>> bounds.data
   <Data(9, 2): [[-4.92, ..., -0.96]]>
   >>> print(bounds.data.array)
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

.. TODO CF-1.8 change not on bounds properties

.. code-block:: python
   :caption: *Inspect the inherited and bespoke properties of a Bounds
             instance.*
      
   >>> bounds.inherited_properties()
   {'standard_name': 'grid_longitude',
    'units': 'degrees'}  
   >>> bounds.properties()
   {}

.. _Geometry-cells:   

Geometry cells
^^^^^^^^^^^^^^

For many geospatial applications, cell bounds can not be represented
by a simple line or polygon, and different cells may have different
numbers of nodes describing their bounds. For example, if each cell
describes the areal extent of a watershed, then it is likely that some
watersheds will require more nodes than others. Such cells are called
`geometries`_.

If a coordinate construct represents geometries then it will have a
"geometry" attribute (not a :ref:`CF property
<Metadata-construct-properties>`) with one of the values ``'point'``,
'``line'`` or ``'polygon'``.

This is illustrated with the file ``geometry.nc`` (found in the
:ref:`sample datasets <Sample-datasets>`):

.. code-block:: python
   :caption: *Read and inspect a dataset containing geometry cell
             bounds.*

   >>> f = cfdm.read('geometry.nc')[0]
   >>> print(f)
   Field: precipitation_amount (ncvar%pr)
   --------------------------------------
   Data            : precipitation_amount(cf_role=timeseries_id(2), time(4))
   Dimension coords: time(4) = [2000-01-02 00:00:00, ..., 2000-01-05 00:00:00]
   Auxiliary coords: latitude(cf_role=timeseries_id(2)) = [25.0, 7.0] degrees_north
                   : longitude(cf_role=timeseries_id(2)) = [10.0, 40.0] degrees_east
                   : altitude(cf_role=timeseries_id(2)) = [5000.0, 20.0] m
                   : cf_role=timeseries_id(cf_role=timeseries_id(2)) = [b'x1', b'y2']
   Coord references: grid_mapping_name:latitude_longitude
   >>> lon = f.construct('longitude')
   >>> lon.dump()                     
   Auxiliary coordinate: longitude
      standard_name = 'longitude'
      units = 'degrees_east'
      Data(2) = [10.0, 40.0] degrees_east
      Geometry: polygon
      Bounds:axis = 'X'
      Bounds:standard_name = 'longitude'
      Bounds:units = 'degrees_east'
      Bounds:Data(2, 3, 4) = [[[20.0, ..., --]]] degrees_east
      Interior Ring:Data(2, 3) = [[0, ..., --]]
   >>> lon.get_geometry()
   'polygon'

Bounds for geometry cells are also stored in a `Bounds` instance, but
one that always has *two* extra trailing dimensions (rather than
one). The fist trailing dimension indexes the distinct parts of a
geometry, and the second indexes the nodes of each part. When a part
has fewer nodes than another, its nodes dimension is padded with
missing data.


.. code-block:: python
   :caption: *Inspect the geometry nodes.*
 
   >>> print(lon.bounds.data.array)
   [[20.0 10.0  0.0   --]
    [ 5.0 10.0 15.0 10.0]
    [20.0 10.0  0.0   --]]

   [[50.0 40.0 30.0   --]
    [  --   --   --   --]
    [  --   --   --   --]]]

If a cell is composed of multiple polygon parts, an individual polygon
may define an "interior ring", i.e. a region that is to be omitted
from, as opposed to included in, the cell extent. Such cells also have
an interior ring array that spans the same domain axes as the
coordinate cells, with the addition of one extra dimension that
indexes the parts for each cell. This array records whether each
polygon is to be included or excluded from the cell, with values of
``1`` or ``0`` respectively.

.. code-block:: python
   :caption: *Inspect the interior ring information.*
 
   >>> print(lon.get_interior_ring().data.array)
   [[0  1  0]
    [0 -- --]]

Note it is preferable to access the data type, number of dimensions,
dimension sizes and number of elements of the coordinate construct via
the construct's attributes, rather than the attributes of the `Data`
instance that provides representative values for each cell. This is
because the representative cell values for geometries are optional,
and if they are missing then the construct attributes are able to
infer these attributes from the bounds.
  
When a field construct containing geometries is written to disk, a
CF-netCDF geometry container variable is automatically created, and
the cells encoded with the :ref:`compression <Compression>` techniques
defined in the CF conventions.

----

.. _Domain-ancillaries:
		
**Domain ancillaries**
----------------------

A :term:`domain ancillary <domain ancillary constructs>` construct
provides information which is needed for computing the location of
cells in an alternative :ref:`coordinate system
<Coordinate-systems>`. If a domain ancillary construct provides extra
coordinates then it may contain cell bounds in addition to its main
data array.

.. code-block:: python
   :caption: *Get the data and bounds data of a domain ancillary
             construct.*
      
   >>> a = t.constructs.get('domainancillary0')
   >>> print(a.data.array)
   [10.]
   >>> bounds = a.bounds
   >>> bounds
   <Bounds: ncvar%a_bounds(1, 2) >
   >>> print(bounds.data.array)
   [[  5.  15.]]

----

.. _Coordinate-systems:

**Coordinate systems**
----------------------

A field construct may contain various coordinate systems. Each
coordinate system is either defined by a :term:`coordinate reference
construct <coordinate reference constructs>` that relates dimension
coordinate, auxiliary coordinate and domain ancillary constructs (as
is the case for the field construct ``t``), or is inferred from
dimension and auxiliary coordinate constructs alone (as is the case
for the field construct ``q``).

A coordinate reference construct contains

* references (by construct keys) to the dimension and auxiliary
  coordinate constructs to which it applies, accessed with the
  `~CoordinateReference.coordinates` method of the coordinate
  reference construct;

..

* the zeroes of the dimension and auxiliary coordinate constructs
  which define the coordinate system, stored in a `Datum` instance,
  which is accessed with the `~CoordinateReference.datum` attribute,
  or `~CoordinateReference.get_datum` method, of the coordinate
  reference construct; and

..

* a formula for converting coordinate values taken from the dimension
  or auxiliary coordinate constructs to a different coordinate system,
  stored in a `CoordinateConversion` class instance, which is accessed
  with the `~CoordinateReference.coordinate_conversion` attribute, or
  `~CoordinateReference.get_coordinate_conversion` method, of the
  coordinate reference construct.

.. code-block:: python
   :caption: *Select the vertical coordinate system construct and
             inspect its coordinate constructs.*
     
   >>> crs = t.constructs('standard_name:atmosphere_hybrid_height_coordinate').value()
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

.. code-block:: python
   :caption: *Get the datum and inspect its parameters.*
	     
   >>> crs.datum
   <Datum: Parameters: earth_radius>
   >>> crs.datum.parameters()
   {'earth_radius': 6371007}


.. code-block:: python
   :caption: *Get the coordinate conversion and inspect its parameters
             and referenced domain ancillary constructs.*
	     
   >>> crs.coordinate_conversion
   <CoordinateConversion: Parameters: computed_standard_name, standard_name; Ancillaries: a, b, orog>
   >>> crs.coordinate_conversion.parameters()
   {'computed_standard_name': 'altitude',
    'standard_name': 'atmosphere_hybrid_height_coordinate'}
   >>> crs.coordinate_conversion.domain_ancillaries()
   {'a': 'domainancillary0',
    'b': 'domainancillary1',
    'orog': 'domainancillary2'}    

----

.. _Cell-methods:
   
**Cell methods**
----------------

A cell method construct describes how the data represent the variation
of the physical quantity within the cells of the domain and is stored
in a `~cfdm.CellMethod` instance. A field constructs allows multiple
cell method constructs to be recorded.

.. code-block:: python
   :caption: *Inspect the cell methods. The description follows the CF
             conventions for cell_method attribute strings, apart from
             the use of construct keys instead of netCDF variable
             names for cell method axes identification.*
	     
   >>> print(t.cell_methods)
   Constructs:
   {'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
    'cellmethod1': <CellMethod: domainaxis3: maximum>}

The application of cell methods is not commutative (e.g. a mean of
variances is generally not the same as a variance of means), so a
`Constructs` instance has an `~Constructs.ordered` method to retrieve
the cell method constructs in the same order that they were were added
to the field construct during :ref:`field construct creation
<Field-creation>`.

.. code-block:: python
   :caption: *Retrieve the cell method constructs in the same order
             that they were applied.*
	     
   >>> t.cell_methods.ordered()
   OrderedDict([('cellmethod0', <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>),
                ('cellmethod1', <CellMethod: domainaxis3: maximum>)])

The axes to which the method applies, the method itself, and any
qualifying properties are accessed with the
`~cfdm.CellMethod.get_axes`, `~cfdm.CellMethod.get_method`, ,
`~cfdm.CellMethod.get_qualifier` and `~cfdm.CellMethod.qualifiers`
methods of the cell method construct.

.. code-block:: python
   :caption: *Get the domain axes constructs to which the cell method
             construct applies, and the method and other properties.*
     
   >>> cm = t.constructs('method:mean').value()
   >>> cm
   <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>)
   >>> cm.get_axes()
   ('domainaxis1', 'domainaxis2')
   >>> cm.get_method()
   'mean'
   >>> cm.qualifiers()
   {'interval': [<Data(): 0.1 degrees>], 'where': 'land'}
   >>> cm.get_qualifier('where')
   'land'

----

.. _Field-ancillaries:
		
**Field ancillaries**
---------------------

A :term:`field ancillary construct <field ancillary constructs>`
provides metadata which are distributed over the same domain as the
field construct itself. For example, if a field construct holds a data
retrieved from a satellite instrument, a field ancillary construct
might provide the uncertainty estimates for those retrievals (varying
over the same spatiotemporal domain).

.. code-block:: python
   :caption: *Get the properties and data of a field ancillary
             construct.*

   >>> a = t.get_construct('fieldancillary0')
   >>> a
   <FieldAncillary: air_temperature standard_error(10, 9) K>
   >>> a.properties()
   {'standard_name': 'air_temperature standard_error',
    'units': 'K'}
   >>> a.data
   <Data(10, 9): [[0.76, ..., 0.32]] K>

----

.. _Field-creation:

**Field creation**
------------------

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

Manual creation
^^^^^^^^^^^^^^^

Manual creation of a field construct has three stages:

**Stage 1:** The field construct is created without metadata
constructs.

..
   
**Stage 2:** Metadata constructs are created independently.

..

**Stage 3:** The metadata constructs are inserted into the field
construct with cross-references to other, related metadata constructs
if required. For example, an auxiliary coordinate construct is related
to an ordered list of the :term:`domain axis constructs` which correspond to
its data array dimensions.

There are two equivalent approaches to **stages 1** and **2**.

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
   <DimensionCoordinate: long_name=Longitude(3) >
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
   <DimensionCoordinate: long_name=Longitude(3) >
   >>> fa = cfdm.FieldAncillary(
   ...        data=cfdm.Data(numpy.array([0, 0, 2], dtype='int8')))
   >>> fa
   <FieldAncillary: (3) >
   >>> fa.set_property('standard_name', 'precipitation_flux status_flag')
   >>> fa
   <FieldAncillary: precipitation_flux status_flag(3) >

For **stage 3**, the `~cfdm.Field.set_construct` method of the field
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
be changed after insertion with the `~Field.set_data_axes` method of
the field construct.

.. Code Block 1
   
.. code-block:: python
   :caption: *Create a field construct with properties; data; and
             domain axis, cell method and dimension coordinate
             metadata constructs (data arrays have been generated with
             dummy values using numpy.arange).*

   import numpy
   import cfdm

   # Initialise the field construct with properties
   Q = cfdm.Field(
	     properties={'project': 'research',
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
   dimX.set_properties({'standard_name': 'longitude',
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

The ``Conventions`` property does not need to be set because it is
automatically included in output files as a netCDF global
``Conventions`` attribute, either as the CF version of the cfdm
package (as returned by the `cfdm.CF` function), or else specified via
the *Conventions* keyword of the `cfdm.write` function. See the
section on :ref:`Writing-to-disk` for details on how to specify
additional conventions.

If this field were to be written to a netCDF dataset then, in the
absence of predefined names, default netCDF variable and dimension
names would be automatically generated (based on standard names where
they exist). The setting of bespoke netCDF names is, however, easily
done with the :ref:`netCDF interface <NetCDF-interface>`.

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

.. Code Block 2
   
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
             qualifiers={'where': 'land',
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
                   : long_name=Grid latitude name(grid_latitude(10)) = [--, ..., j]
   Cell measures   : measure:area(grid_longitude(9), grid_latitude(10)) = [[0.0, ..., 89.0]] km2
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

Creation by conversion
^^^^^^^^^^^^^^^^^^^^^^

An independent field construct may be created from an existing
metadata construct using `~Field.convert` method of the field
construct, which identifies a unique metadata construct and returns a
new field construct based on its properties and data. The new field
construct always has :term:`domain axis constructs` corresponding to
the data, and (by default) any other metadata constructs that further
define its domain.

.. code-block:: python
   :caption: *Create an independent field construct from the "surface
             altitude" metadata construct.*

   >>> key = tas.construct_key('surface_altitude')
   >>> orog = tas.convert(key)
   >>> print(orog)
   Field: surface_altitude
   -----------------------
   Data            : surface_altitude(grid_latitude(10), grid_longitude(9)) m
   Dimension coords: grid_latitude(10) = [0.0, ..., 9.0] degrees
                   : grid_longitude(9) = [0.0, ..., 8.0] degrees
   Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 89.0]] degrees_north
                   : longitude(grid_longitude(9), grid_latitude(10)) = [[0.0, ..., 89.0]] degrees_east
                   : long_name=Grid latitude name(grid_latitude(10)) = [--, ..., j]
   Cell measures   : measure:area(grid_longitude(9), grid_latitude(10)) = [[0.0, ..., 89.0]] km2
   Coord references: rotated_latitude_longitude

The `~Field.convert` method has an option to only include domain axis
constructs in the new field construct, with no other metadata
constructs.

.. code-block:: python
   :caption: *Create an independent field construct from the "surface
             altitude" metadata construct, but without a complete
             domain.*

   >>> orog1 = tas.convert(key, full_domain=False) 
   >>> print(orog1)
   Field: surface_altitude
   -----------------------
   Data            : surface_altitude(key%domainaxis2(10), key%domainaxis3(9)) m
   
.. _Creation-by-reading:

Creation by reading
^^^^^^^^^^^^^^^^^^^

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
``tas.nc`` does not have the ``coordinates``, ``cell_measures`` nor
``grid_mapping`` netCDF attributes that would link it to auxiliary
coordinate, cell measure and grid mapping netCDF variables.

----

.. _Copying-and-equality:

**Copying and equality**
------------------------

A field construct may be copied with its `~Field.copy` method. This
produces a "deep copy", i.e. the new field construct is completely
independent of the original field.

.. code-block:: python
   :caption: *Copy a field construct and change elements of the copy,
             showing that the original field construct has not been
             altered.*
     
   >>> u = t.copy()
   >>> u.data[0, 0, 0] = -1e30
   >>> u.data[0, 0, 0]
   <Data(1, 1, 1): [[[-1e+30]]] K>
   >>> t.data[0, 0, 0]
   <Data(1, 1, 1): [[[-1.0]]] K>
   >>> key = u.construct_key('grid_latitude')    
   >>> u.del_construct(key)
   <DimensionCoordinate: grid_latitude(10) degrees>
   >>> u.constructs('grid_latitude')
   Constructs:
   {}
   >>> t.constructs('grid_latitude')
   Constructs:
   {'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>}

Equivalently, the `copy.deepcopy` function may be used:

.. code-block:: python
   :caption: *Copy a field construct with the built-in copy module.*
	    
   >>> import copy
   >>> u = copy.deepcopy(t)

Metadata constructs may be copied individually in the same manner:

.. code-block:: python
   :caption: *Copy a metadata construct.*

   >>> orog = t.constructs('surface_altitude').value().copy()

Arrays within `Data` instances are copied with a `copy-on-write
<https://en.wikipedia.org/wiki/Copy-on-write>`_ technique. This means
that a copy takes up very little memory, even when the original
constructs contain very large data arrays, and the copy operation is
fast.

.. _Equality:

Equality
^^^^^^^^

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
  the field construct's ``Conventions`` property, which is never
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
	  
   >>> orog = t.constructs('surface_altitude').value()
   >>> orog.equals(orog.copy())
   True

----

.. _NetCDF-interface:

**NetCDF interface**
--------------------

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
constructs to a new netCDF dataset, and also makes them accessible as
filters to a `Constructs` instance:

.. code-block:: python
   :caption: *Retrieve metadata constructs based on their netCDF
             names.*
	  
   >>> print(t.constructs.filter_by_ncvar('b'))
   Constructs:
   {'domainancillary1': <DomainAncillary: ncvar%b(1) >}
   >>> t.constructs('ncvar%x').value()
   <DimensionCoordinate: grid_longitude(9) degrees>
   >>> t.constructs('ncdim%x')
   <Constructs: domain_axis(1)>
     
Each construct has methods to access the netCDF elements which it
requires. For example, the field construct has the following methods:

======================================  ======================================
Method                                  Description
======================================  ======================================
`~Field.nc_get_variable`                Return the netCDF variable name
`~Field.nc_set_variable`                Set the netCDF variable name
`~Field.nc_del_variable`                Remove the netCDF variable name
				        
`~Field.nc_has_variable`                Whether the netCDF variable name has
                                        been set
				        
`~Field.nc_global_attributes`           Return the selection of properties to 
                                        be written as netCDF global attributes
				        
`~Field.nc_set_global_attribute`        Set a property to be written as a
                                        netCDF global attribute

`~Field.nc_set_global_attributes`       Set properties to be written as
                                        netCDF global attributes

`~Field.nc_clear_global_attributes`     Clear the selection of properties
                                        to be written as netCDF global
                                        attributes
======================================  ======================================

.. code-block:: python
   :caption: *Access netCDF elements associated with the field and
             metadata constructs.*

   >>> q.nc_get_variable()
   'q'
   >>> q.nc_global_attributes()
   {'project': None, 'Conventions': None}
   >>> q.nc_set_variable('humidity')
   >>> q.nc_get_variable()
   'humidity'
   >>> q.constructs('latitude').value().nc_get_variable()
   'lat'

The complete collection of netCDF interface methods is:

================================  =======================================  =====================================
Method                            Classes                                  NetCDF element
================================  =======================================  =====================================
`!nc_del_variable`                `Field`, `DimensionCoordinate`,          Variable name
                                  `AuxiliaryCoordinate`, `CellMeasure`,
                                  `DomainAncillary`, `FieldAncillary`,
                                  `CoordinateReference`,  `Bounds`,
			          `Datum`, `Count`, `Index`, `List`
			          				
`!nc_get_variable`                `Field`, `DimensionCoordinate`,          Variable name
                                  `AuxiliaryCoordinate`, `CellMeasure`,
                                  `DomainAncillary`, `FieldAncillary`,
                                  `CoordinateReference`, `Bounds`,
			          `Datum`, `Count`, `Index`, `List`
			          
`!nc_has_variable`                `Field`, `DimensionCoordinate`,          Variable name
                                  `AuxiliaryCoordinate`, `CellMeasure`,
                                  `DomainAncillary`, `FieldAncillary`,
                                  `CoordinateReference`, `Bounds`,
			          `Datum`, `Count`, `Index`, `List`
			          
`!nc_set_variable`                `Field`, `DimensionCoordinate`,          Variable name
                                  `AuxiliaryCoordinate`, `CellMeasure`,
                                  `DomainAncillary`, `FieldAncillary`,
                                  `CoordinateReference`, `Bounds`,
			          `Datum`, `Count`, `Index`, `List`
			          
`!nc_del_dimension`               `DomainAxis`, `Count`, `Index`           Dimension name
			          
`!nc_get_dimension`	          `DomainAxis`, `Count`, `Index`           Dimension name
			          			                    
`!nc_has_dimension`	          `DomainAxis`, `Count`, `Index`           Dimension name
			          			                    
`!nc_set_dimension`	          `DomainAxis`, `Count`, `Index`           Dimension name

`!nc_is_unlimited`                `DomainAxis`                             Unlimited dimension

`!nc_set_unlimited` 	          `DomainAxis`   	                   Unlimited dimension

`!nc_global_attributes`	          `Field`                                  Global attributes
			          
`!nc_set_global_attribute`        `Field`                                  Global attributes
			          
`!nc_set_global_attributes`       `Field`                                  Global attributes
			          
`!nc_clear_global_attributes`     `Field`                                  Global attributes
			          
`!nc_get_external`                `CellMeasure`                            External variable status

`!nc_set_external`                `CellMeasure`                            External variable status
			          
`!nc_del_sample_dimension`        `Count`, `Index`                         Sample dimension name
			          
`!nc_get_sample_dimension`        `Count`, `Index`                         Sample dimension name
    			          
`!nc_has_sample_dimension`        `Count`, `Index`                         Sample dimension name
			          
`!nc_set_sample_dimension`        `Count`, `Index`                         Sample dimension name
================================  =======================================  =====================================

----

.. _Writing-to-disk:
   
**Writing to disk**
-------------------

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

.. code-block:: console
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

By default the output file will be for CF-|version|.
   
The `cfdm.write` function has optional parameters to

* set the output netCDF format (all netCDF3 and netCDF4 formats are
  possible);

* specify which field construct properties should become netCDF data
  variable attributes and which should become netCDF global
  attributes;
  
* set extra netCDF global attributes;
  
* create :ref:`external variables <External-variables>` in an external
  file;

* specify the version of the CF conventions (from CF-1.6 up to
  CF-|version|), and of any other conventions that the file adheres
  to;

* change the data type of output data arrays;
  
* apply netCDF compression and packing;

* set the endian-ness of the output data; and 

* specify whether or not :ref:`netCDF string arrays <Strings>` are to
  be used.

Output netCDF variable and dimension names read from a netCDF dataset
are stored in the resulting field constructs, and may also be set
manually with the `!nc_set_variable`, `nc_set_dimension` and
`nc_set_sample_dimension` methods. If a name has not been set then one
will be generated internally (usually based on the standard name if it
exists).

It is possible to create netCDF unlimited dimensions using the
`~DomainAxis.nc_set_unlimited` method of the domain axis construct.

A field construct is not transformed through being written to a file
on disk and subsequently read back from that file.

.. code-block:: python
   :caption: *Read a file that has been created by writing a field
             construct, and compare the result with the original field
             construct in memory.*
	     
   >>> f = cfdm.read('q_file.nc')[0]
   >>> q.equals(f)
   True


.. _Global-attributes:

Global attributes
^^^^^^^^^^^^^^^^^

The field construct properties that correspond to the standardised
description-of-file-contents attributes are automatically written as
netCDF global attributes. Other attributes may also be written as
netCDF global attributes if they have been identified as such with the
*global_attributes* keyword, or via the
`~Field.nc_set_global_attribute` or `~Field.nc_set_global_attributes`
method of the field constructs. In either case, the creation of a
netCDF global attribute depends on the corresponding property values
being identical across all of the field constructs being written to
the file. If they are all equal then the property will be written as a
netCDF global attribute and not as an attribute of any netCDF data
variable; if any differ then the property is written only to each
netCDF data variable.

.. code-block:: python
   :caption: *Request that the "model" property is written as a netCDF
             global attribute, using the "global_attributes" keyword.*
	     
   >>> f.set_property('model', 'model_A')
   >>> cfdm.write(f, 'f_file.nc', global_attributes='model')

.. code-block:: python
   :caption: *Request that the "model" property is written as a netCDF
             global attribute, using the "nc_set_global_attribute"
             method.*
	     
   >>> f.nc_global_attributes()
   {'Conventions': None, 'project': None}
   >>> f.nc_set_global_attribute('model')
   >>> f.nc_global_attributes()
   {'Conventions': None, 'model': None, 'project': None}
   >>> f.nc_global_attributes(values=True)
   {'Conventions': 'CF-1.7', 'project': 'research', 'model': 'model_A'}
   >>> cfdm.write(f, 'f_file.nc')

It is possible to create both a netCDF global attribute and a netCDF
data variable attribute with the same name, but with different
values. This may be done by assigning the global value to the property
name with the `~Field.nc_set_global_attribute` or
`~Field.nc_set_global_attributes` method, or by via the
*file_descriptors* keyword. For the former technique, any
inconsistencies arising from multiple field constructs being written
to the same file will be resolved by omitting the netCDF global
attribute from the file.

.. code-block:: python
   :caption: *Request that the "information" property is written as
             netCDF global and data variable attributes, with
             different values, using the "nc_set_global_attribute"
             method.*
	     
   >>> f.set_property('information', 'variable information')
   >>> f.properties()
   {'Conventions': 'CF-1.7',
    'information': 'variable information',
    'project': 'research',
    'standard_name': 'specific_humidity',
    'units': '1'}
   >>> f.nc_set_global_attribute('information', 'global information')
   >>> f.nc_global_attributes()
   {'Conventions': None,
   'information': 'global information',
    'model': None,
    'project': None}
   >>> cfdm.write(f, 'f_file.nc')

NetCDF global attributes defined with the *file_descriptors* keyword
of the `cfdm.write` function will always be written as requested,
independently of the netCDF data variable attributes, and superseding
any global attributes that may have been defined with the
*global_attributes* keyword, or set on the individual field
constructs.

.. code-block:: python
   :caption: *Insist that the "history" property is written as netCDF
             a global attribute, with the "file_descriptors" keyword.*
	     
   >>> cfdm.write(f, 'f_file_nc', file_descriptors={'history': 'created in 2020'})
   >>> f_file = cfdm.read('f_file.nc')[0]
   >>> f_file.nc_global_attributes()
   >>> f_file.properties()
   {'Conventions': 'CF-1.7',
    'history': 'created in 2020',
    'information': 'variable information',
    'model': 'model_A',
    'project': 'research',
    'standard_name': 'specific_humidity',
    'units': '1'}
   >>> f_file.nc_global_attributes()
   {'Conventions': None,
    'history': None,
    'information': 'global information',
    'project': None}

.. _Conventions:

Conventions
^^^^^^^^^^^

The ``Conventions`` netCDF global attribute containing the version of
the CF conventions is always automatically created. If the version of
the CF conventions has been set as a field property, or with the
*Conventions* keyword of the `cfdm.write` function, then it is
ignored. However, other conventions that may apply can be set with
either technique.

.. code-block:: python
   :caption: *Two ways to add additional conventions to the
             "Conventions" netCDF global attribute.*
	     
   >>> f_file.set_property('Conventions', 'UGRID1.0')
   >>> cfdm.write(f, 'f_file.nc', Conventions='UGRID1.0')   

   
.. _Scalar-coordinate-variables:

Scalar coordinate variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
   >>> key = q.construct_key('time')
   >>> axes = q.get_data_axes(key)
   >>> axes
   ('domainaxis2',)
   >>> q2 = q.insert_dimension(axis=axes[0])
   >>> q2
   <Field: specific_humidity(time(1), latitude(5), longitude(8)) 1>
   >>> cfdm.write(q2, 'q2_file.nc')

The new dataset is structured as follows (note, relative to file
``q_file.nc``, the existence of the "time" dimension and the lack of a
``coordinates`` attribute on the, now three-dimensional, data
variable):
   
.. code-block:: console
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

.. _Strings:
  
Strings
^^^^^^^

String-valued data may be written to netCDF files either as netCDF
character arrays with a trailing dimension large enough to contain the
longest value, or as netCDF4 string arrays. The former is allowed for
all formats of netCDF3 and netCDF4 format files; but string arrays may
only be written to netCDF4 format files (note that string arrays can
not be written to netCDF4 classic format files).

By default, netCDF string arrays will be created whenever possible,
and in all other cases netCDF character arrays will be
used. Alternatively, netCDF character arrays can be used in all cases
by setting the *string* keyword of the `cfdm.write` function.

----
      
.. _Hierarchical-groups:

**Hierarchical groups**
-----------------------

`Hierarchical groups`_ provide a powerful mechanism to structure
variables within datasets. A future |version|.\ *x* release of cfdm
will include support for netCDF4 files containing data organised in
hierarchical groups, but this is not available in version |release|
(even though it is allowed in CF-|version|).

----
   
.. _External-variables:

**External variables**
----------------------

`External variables`_ are those in a netCDF file that are referred to,
but which are not present in it. Instead, such variables are stored in
other netCDF files known as "external files". External variables may,
however, be incorporated into the field constructs of the dataset, as
if they had actually been stored in the same file, simply by providing
the external file names to the `cfdm.read` function.

This is illustrated with the files ``parent.nc`` (found in the
:ref:`sample datasets <Sample-datasets>`):

.. code-block:: console
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

and ``external.nc`` (found in the :ref:`sample datasets
<Sample-datasets>`):

.. code-block:: console
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
   Cell measures   : measure:area (external variable: ncvar%areacella)

   >>> area = u.constructs('measure:area').value()
   >>> area
   <CellMeasure: measure:area >
   >>> area.nc_get_external()
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
(``areacella``) would be listed by the ``external_variables`` global
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
   >>> area = g.constructs('measure:area').value()
   >>> area
   <CellMeasure: cell_area(9, 10) m2>
   >>> area.nc_get_external()
   False
   >>> area.nc_get_variable()
   'areacella'
   >>> area.properties()
   {'standard_name': 'cell_area', 'units': 'm2'}
   >>> area.data
   <Data(9, 10): [[100000.5, ..., 100089.5]] m2>
   
If this field construct were to be written to disk using `cfdm.write`
then by default the cell measure construct, with all of its metadata
and data, would be written to the named output file, along with all of
the other constructs. There would be no ``external_variables`` global
attribute.

To create a reference to an external variable in an output netCDF
file, set the status of the cell measure construct to "external" with
its `~CellMeasure.nc_set_external` method.

.. code-block:: python
   :caption: *Flag the cell measure as external and write the field
             construct to a new file.*

   >>> area.nc_set_external(True)
   >>> cfdm.write(g, 'new_parent.nc')

To create a reference to an external variable in the an output netCDF
file and simultaneously create an external file containing the
variable, set the status of the cell measure construct to "external"
and provide an external file name to the `cfdm.write` function:

.. code-block:: python
   :caption: *Write the field construct to a new file and the cell
             measure construct to an external file.*

   >>> cfdm.write(g, 'new_parent.nc', external='new_external.nc')

.. _External-variables-with-cfdump:

External files with cfdump
^^^^^^^^^^^^^^^^^^^^^^^^^^

One or more external files may also be included with :ref:`cfdump
<cfdump>`.

.. code-block:: console
   :caption: *Use cfdump to describe the parent file without resolving
             the external variable reference.*
	     
   $ cfdump parent.nc 
   Field: eastward_wind (ncvar%eastward_wind)
   ------------------------------------------
   Data            : eastward_wind(latitude(10), longitude(9)) m s-1
   Dimension coords: latitude(10) = [0.0, ..., 9.0] degrees_north
                   : longitude(9) = [0.0, ..., 8.0] degrees_east
   Cell measures   : measure:area (external variable: ncvar%areacella)

.. code-block:: console
   :caption: *Providing an external file with the "-e" option allows
             the reference to be resolved.*
	     
   $ cfdump -e external.nc parent.nc 
   Field: eastward_wind (ncvar%eastward_wind)
   ------------------------------------------
   Data            : eastward_wind(latitude(10), longitude(9)) m s-1
   Dimension coords: latitude(10) = [0.0, ..., 9.0] degrees_north
                   : longitude(9) = [0.0, ..., 8.0] degrees_east
   Cell measures   : measure:area(longitude(9), latitude(10)) = [[100000.5, ..., 100089.5]] m2

----

.. _Compression:
   
**Compression**
---------------

The CF conventions have support for saving space by identifying
unwanted missing data.  Such compression techniques store the data
more efficiently and result in no precision loss. The CF data model,
however, views compressed arrays in their uncompressed form.

Therefore, the field construct contains :term:`domain axis constructs`
for the compressed dimensions and presents a view of compressed data
in its uncompressed form, even though the "underlying array" (i.e. the
actual array on disk or in memory that is contained in a `Data`
instance) is compressed. This means that the cfdm package includes
algorithms for uncompressing each type of compressed array.

There are two basic types of compression supported by the CF
conventions: ragged arrays (as used by :ref:`discrete sampling
geometries <Discrete-sampling-geometries>`) and :ref:`compression by
gathering <Gathering>`, each of which has particular implementation
details, but the following access patterns and behaviours apply to
both:

* Whether or not the data are compressed is tested with the
  `~Data.get_compression_type` method of the `Data` instance.

..

* Accessing the data via the `~Data.array` attribute of a `Data`
  instance returns a numpy array that is uncompressed. The underlying
  array will, however, remain in its compressed form. The compressed
  underlying array may be retrieved as a numpy array with the
  `~Data.compressed_array` attribute of the `Data` instance.

..

* A :ref:`subspace <Subspacing>` of a field construct is created with
  indices of the uncompressed form of the data. The new subspace will
  no longer be compressed, i.e. its underlying arrays will be
  uncompressed, but the original data will remain compressed. It
  follows that to uncompress all of the data in a field construct,
  index the field construct with (indices equivalent to) `Ellipsis`.
  
..

* If data elements are modified by :ref:`assigning <Assignment>` to
  indices of the uncompressed form of the data, then the compressed
  underlying array is replaced by its uncompressed form.

..

* An uncompressed field construct can be compressed, prior to being
  written to a dataset, with its `~Field.compress` method, which also
  compresses the metadata constructs as required.

..

* An compressed field construct can be uncompressed with its
  `~Field.uncompress` method, which also uncompresses the metadata
  constructs as required.

..

* If an underlying array is compressed at the time of writing to disk
  with the `cfdm.write` function, then it is written to the file as a
  compressed array, along with the supplementary netCDF variables and
  attributes that are required for the encoding. This means that if a
  dataset using compression is read from disk then it will be written
  back to disk with the same compression, unless data elements have
  been modified by assignment.

Examples of all of the above may be found in the sections on
:ref:`discrete sampling geometries <Discrete-sampling-geometries>` and
:ref:`gathering <Gathering>`.

.. _Discrete-sampling-geometries:
   
Discrete sampling geometries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Discrete sampling geometry (DSG)`_ features may be compressed by
combining them using one of three ragged array representations:
`contiguous`_, `indexed`_ or `indexed contiguous`_.

The count variable that is required to uncompress a contiguous, or
indexed contiguous, ragged array is stored in a `Count` instance and
is accessed with the `~Data.get_count` method of the `Data` instance.

The index variable that is required to uncompress an indexed, or
indexed contiguous, ragged array is stored in an `Index` instance and
is accessed with the `~Data.get_index` method of the `Data` instance.

The contiguous case is is illustrated with the file ``contiguous.nc``
(found in the :ref:`sample datasets <Sample-datasets>`):
     
.. code-block:: console
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
   >>> print(h.data.array)
   [[0.12 0.05 0.18   --   --   --   --   --   --]
    [0.05 0.11 0.2  0.15 0.08 0.04 0.06   --   --]
    [0.15 0.19 0.15 0.17 0.07   --   --   --   --]
    [0.11 0.03 0.14 0.16 0.02 0.09 0.1  0.04 0.11]]

.. code-block:: python
   :caption: *Inspect the underlying compressed array and the count
             variable that defines how to uncompress the data.*
	     
   >>> h.data.get_compression_type()
   'ragged contiguous'
   >>> print(h.data.compressed_array)
   [0.12 0.05 0.18 0.05 0.11 0.2 0.15 0.08 0.04 0.06 0.15 0.19 0.15 0.17 0.07
    0.11 0.03 0.14 0.16 0.02 0.09 0.1 0.04 0.11]
   >>> count_variable = h.data.get_count()
   >>> count_variable
   <Count: long_name=number of observations for this station(4) >
   >>> print(count_variable.data.array)
   [3 7 5 9]

The timeseries for the second station is easily selected by indexing
the "station" axis of the field construct:

.. code-block:: python
   :caption: *Get the data for the second station.*
	  
   >>> station2 = h[1]
   >>> station2
   <Field: specific_humidity(ncdim%station(1), ncdim%timeseries(9))>
   >>> print(station2.data.array)
   [[0.05 0.11 0.2 0.15 0.08 0.04 0.06 -- --]]

The underlying array of original data remains in compressed form until
data array elements are modified:
   
.. code-block:: python
   :caption: *Change an element of the data and show that the
             underlying array is no longer compressed.*

   >>> h.data.get_compression_type()
   'ragged contiguous'
   >>> h.data[1, 2] = -9
   >>> print(h.data.array)
   [[0.12 0.05 0.18   --   --   --   --   --   --]
    [0.05 0.11 -9.0 0.15 0.08 0.04 0.06   --   --]
    [0.15 0.19 0.15 0.17 0.07   --   --   --   --]
    [0.11 0.03 0.14 0.16 0.02 0.09 0.1  0.04 0.11]]
   >>> h.data.get_compression_type()
   ''

Perhaps the easiest way to create a compressed field construct is to
create the equivalent uncompressed field construct and then compress
it with its `~Field.compress` method, which also compresses the
metadata constructs as required.
   
.. Code Block 3

.. code-block:: python
   :caption: *Create a field construct and then compress it.*

   import numpy
   import cfdm
   
   # Define the array values
   data = cfdm.Data([[280.0,   -99,   -99,   -99],
	             [281.0, 279.0, 278.0, 279.5]],
      	            mask=[[0, 1, 1, 1],
                          [0, 0, 0, 0]])
   	     
   # Create the field construct
   T = cfdm.Field()
   T.set_properties({'standard_name': 'air_temperature',
                     'units': 'K',
                     'featureType': 'timeSeries'})
   
   # Create the domain axis constructs
   X = T.set_construct(cfdm.DomainAxis(4))
   Y = T.set_construct(cfdm.DomainAxis(2))
   
   # Set the data for the field
   T.set_data(data, axes=[Y, X])
 
   # Compress the data 
   T.compress('contiguous',
              count_properties={'long_name': 'number of obs for this timeseries'},
              inplace=True)
		
The new field construct can now be inspected and written to a netCDF file:

.. code-block:: python
   :caption: *Inspect the new field construct and write it to disk.*
   
   >>> T
   <Field: air_temperature(key%domainaxis1(2), key%domainaxis0(4)) K>
   >>> print(T.data.array)
   [[280.0    --    --    --]
    [281.0 279.0 278.0 279.5]]
   >>> T.data.get_compression_type()
   'ragged contiguous'
   >>> print(T.data.compressed_array)
   [280.  281.  279.  278.  279.5]
   >>> count_variable = T.data.get_count()
   >>> count_variable
   <Count: long_name=number of obs for this timeseries(2) >
   >>> print(count_variable.data.array)
   [1 4]
   >>> cfdm.write(T, 'T_contiguous.nc')

The content of the new file is:
  
.. code-block:: console
   :caption: *Inspect the new compressed dataset with the ncdump
             command line tool.*   

   $ ncdump T_contiguous.nc
   netcdf T_contiguous {
   dimensions:
   	dim = 2 ;
   	element = 5 ;
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
   
    count = 1, 4 ;
   
    air_temperature = 280, 281, 279, 278, 279.5 ;
   }

Exactly the same field construct may be also created explicitly with
underlying compressed data. A construct with an underlying ragged
array is created by initialising a `Data` instance with a ragged
array that is stored in one of three special array objects:
`RaggedContiguousArray`, `RaggedIndexedArray` or
`RaggedIndexedContiguousArray`.

.. Code Block 4

.. code-block:: python
   :caption: *Create a field construct with compressed data.*

   import numpy
   import cfdm
   
   # Define the ragged array values
   ragged_array = cfdm.Data([280, 281, 279, 278, 279.5])

   # Define the count array values
   count_array = [1, 4]

   # Create the count variable
   count_variable = cfdm.Count(data=cfdm.Data(count_array))
   count_variable.set_property('long_name', 'number of obs for this timeseries')

   # Create the contiguous ragged array object, specifying the
   # uncompressed shape
   array = cfdm.RaggedContiguousArray(
                    compressed_array=ragged_array,
                    shape=(2, 4), size=8, ndim=2,
                    count_variable=count_variable)

   # Create the field construct with the domain axes and the ragged
   # array
   T = cfdm.Field()
   T.set_properties({'standard_name': 'air_temperature',
                     'units': 'K',
                     'featureType': 'timeSeries'})
   
   # Create the domain axis constructs for the uncompressed array
   X = T.set_construct(cfdm.DomainAxis(4))
   Y = T.set_construct(cfdm.DomainAxis(2))
   
   # Set the data for the field
   T.set_data(cfdm.Data(array), axes=[Y, X])

   
.. _Gathering:

Gathering
^^^^^^^^^

`Compression by gathering`_ combines axes of a multidimensional array
into a new, discrete axis whilst omitting the missing values and thus
reducing the number of values that need to be stored.

The list variable that is required to uncompress a gathered array is
stored in a `List` object and is retrieved with the `~Data.get_list`
method of the `Data` instance.

This is illustrated with the file ``gathered.nc`` (found in the
:ref:`sample datasets <Sample-datasets>`):

.. code-block:: console
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
   >>> print(p.data.array)
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
   >>> print(p.data.compressed_array)
   [[0.000122 0.0008   0.000177 0.000175 0.00058 0.000206 0.0007  ]
    [0.000202 0.000174 0.00084  0.000201 0.0057  0.000223 0.000102]]
   >>> list_variable = p.data.get_list()
   >>> list_variable
   <List: ncvar%landpoint(7) >
   >>> print(list_variable.data.array)
   [1 2 5 7 8 16 18]

Subspaces based on the uncompressed axes of the field construct are
easily created:

.. code-block:: python
   :caption: *Get subspaces based on indices of the uncompressed
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

.. Code Block 5

.. code-block:: python
   :caption: *Create a field construct with compressed data.*

   import numpy	  
   import cfdm

   # Define the gathered values
   gathered_array = cfdm.Data([[2, 1, 3], [4, 0, 5]])

   # Define the list array values
   list_array = [1, 4, 5]

   # Create the list variable
   list_variable = cfdm.List(data=cfdm.Data(list_array))

   # Create the gathered array object, specifying the uncompressed
   # shape
   array = cfdm.GatheredArray(
                    compressed_array=gathered_array,
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
   :caption: *Inspect the new field construct and write it to disk.*
   
   >>> P
   <Field: precipitation_flux(key%domainaxis0(2), key%domainaxis1(3), key%domainaxis2(2)) kg m-2 s-1>
   >>> print(P.data.array)
   [[[ -- 2.0]
     [ --  --]
     [1.0 3.0]]

    [[ -- 4.0]
     [ --  --]
     [0.0 5.0]]]
   >>> P.data.get_compression_type()
   'gathered'
   >>> print(P.data.compressed_array)
   [[2. 1. 3.]
    [4. 0. 5.]]
   >>> list_variable = P.data.get_list()
   >>> list_variable 
   <List: (3) >
   >>> print(list_variable.data.array)
   [1 4 5]
   >>> cfdm.write(P, 'P_gathered.nc')

The content of the new file is:
   
.. code-block:: console
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

.. rubric:: Footnotes

----

.. [#dap] Requires the netCDF4 python package to have been built with
          OPeNDAP support enabled. See
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
	    
.. External links to the CF conventions (will need updating with new versions of CF)
   
.. _External variables:               http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#external-variables
.. _Discrete sampling geometry (DSG): http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#discrete-sampling-geometries
.. _incomplete multidimensional form: http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#_incomplete_multidimensional_array_representation
.. _Compression by gathering:         http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#compression-by-gathering
.. _contiguous:                       http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#_contiguous_ragged_array_representation
.. _indexed:                          http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#_indexed_ragged_array_representation
.. _indexed contiguous:               http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#_ragged_array_representation_of_time_series_profiles
.. _geometries:                       http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#geometries
.. _Hierarchical groups:              http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#groups

.. The code examples in this tutorial are available in an **IPython
   Jupyter notebook** (:download:`download
   <notebooks/tutorial.ipynb>`, 80kB) [asdasds#files]_, [assadasdsa#notebook]_.
