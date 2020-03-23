version 1.8.0
-------------
----

**2020-03-23**

* First release for CF-1.8 (does not include netCDF hierarchical
  groups functionality).
* Implementation of simple geometries for CF-1.8
  (https://github.com/NCAS-CMS/cfdm/issues/11).
* Implementing of string data-types for CF-1.8
  (https://github.com/NCAS-CMS/cfdm/issues/12).
* New function: `cfdm.example_field`
  (https://github.com/NCAS-CMS/cfdm/issues/18)
* New attributes: `cfdm.Field.dtype`, `cfdm.Field.ndim`,
  `cfdm.Field.shape`, `cfdm.Field.size`
* New method: `cfdm.Data.any`
* New ``paths`` keyword parameter to `cfdm.environment`
* Changed minimum netCDF4 dependency to version 1.5.3.
* Changed minimum cftime dependency to version 1.1.1.
* Fixed bug that prevented the writing of ``'NETCDF3_64BIT_OFFSET'``
  and ``'NETCDF3_64BIT_DATA'`` format files
  (https://github.com/NCAS-CMS/cfdm/issues/9).
* Fixed bug that caused a failure when a "_FillValue" or
  "missing_value" property is set and data type conversions are
  specified with the ``datatype`` keyword to `cfdm.write`
  (https://github.com/NCAS-CMS/cfdm/issues/16).
* Fixed bug whereby `cfdm.Field.has_construct` would try to delete the
  construct rather than check whether it existed.

version 1.7.11
--------------
----

**2019-11-27**

* New methods: `cfdm.Field.compress`, `cfdm.Field.uncompress`
* New methods: `cfdm.Data.flatten`, `cfdm.Data.uncompress`
* New  ``dtype`` and ``mask`` keyword parameters to `cfdm.Data`
* Changed the default value of the ``ignore_compression`` parameter to
  `True`.
  
version 1.7.10
--------------
----

**2019-11-14**

* New method: `cfdm.Field.nc_set_global_attributes`.
* Fixed bug relating to the reading of some CDL files
  (https://github.com/NCAS-CMS/cfdm/issues/5).
* Fixed bug relating numpy warning when printing a field with masked
  reference time values (https://github.com/NCAS-CMS/cfdm/issues/8).

version 1.7.9
-------------
----

**2019-11-07**

* Fixed bug relating to setting of parameters on datum and coordinate
  conversion objects of coordinate conversion constructs
  (https://github.com/NCAS-CMS/cfdm/issues/6).

version 1.7.8
-------------
----

**2019-10-04**

* During writing to netCDF files, ensured that _FillValue and
  missing_value have the same data type as the data.
* Fixed bug during construct equality testing that didn't recognise
  equal cell method constructs in transposed, but otherwise equal
  field constructs.
* Bounds netCDF dimension name is now saved, and can be set. The
  saved/set value is written out to disk.
* Now reads CDL files (https://github.com/NCAS-CMS/cfdm/issues/5)

version 1.7.7
-------------
----

**2019-06-13**

* Don't set the fill mode for a `netCDF4.Dataset` open for writing to
  `off`, to prevent incorrect reading of some netCDF4 files
  (https://github.com/NCAS-CMS/cfdm/issues/4).
* Updated documentation
  
version 1.7.6
-------------
----

**2019-06-05**

* Added attributes `_ATOL` and `_RTOL` to facilitate subclassing.
* Fixed bug in `cfdm.Field.convert`.
* Fixed bug in `cfdm.core.constructs.new_identifier`.
  
version 1.7.5
-------------
----

**2019-05-15**

* New methods: `Datum.nc_has_variable`, `Datum.nc_get_variable`,
  `Datum.nc_has_variable`, `Datum.nc_set_variable`
  (https://github.com/NCAS-CMS/cfdm/issues/3).
  
version 1.7.4
-------------
----

**2019-05-14**

* Changed behaviour of `cfdm.Constructs.filter_by_axis`.
* New methods: `cfdm.Data.has_units`, `cfdm.Data.has_calendar`,
  `cfdm.Data.has_fill_value`.
* New ``constructs`` keyword parameter to `Field.transpose`.
* Keyword parameter ``axes`` to `cfdm.Field.set_data` is now optional.
* Added the 'has_bounds' method to constructs that have data but can't
  have bounds.
* New methods: `cfdm.DomainAxis.nc_is_unlimited`,
  `cfdm.DomainAxis.nc_set_unlimited`.
* Made Data a virtual subclass of Array.   
* Deprecated methods: `cfdm.Field.nc_unlimited`,
  `cfdm.Field.nc_clear_unlimited`, `cfdm.Field.nc_clear_unlimited`.
* Fixed bug when writing new horizontal coordinate reference for the
  vertical datum.
* Fixed bug in `del_data` methods.
* Fixed bug with in-place operations.
* Fixed bug with position in some `insert_dimension` methods.
* Fixed bug that sometimes made duplicate netCDF dimensions when
  writing to a file.
* Added _shape keyword to `cfdm.Field.set_data_axes` to allow the data
  shape to be checked prior to insertion.
* Added the '_custom' attribute to facilitate subclassing.
* New class `cfdm.mixin.NetCDFUnlimitedDimension` replaces
  `cfdm.mixin.NetCDFUnlimitedDimensions`, which is deprecated.
* New method `cfdm.CFDMImplementation.nc_is_unlimited_axis` replaces
  `cfdm.CFDMImplementation.nc_get_unlimited_axes`, which is
  deprecated.
* New method `cfdm.CFDMImplementation.nc_set_unlimited_axis` replaces
  `cfdm.CFDMImplementation.nc_set_unlimited_dimensions`, which is
  deprecated.
  
version 1.7.3
-------------
----

**2019-04-24**

* New method: `cfdm.Constructs.filter_by_size`.
* New method: `cfdm.Data.uncompress`.
* Changed the default behaviours of the
  `cfdm.Construct.filter_by_axis`, `cfdm.Construct.filter_by_size`,
  `cfdm.Construct.filter_by_naxes`,
  `cfdm.Construct.filter_by_property`,
  `cfdm.Construct.filter_by_ncvar`, `cfdm.Construct.filter_by_ncdim`,
  `cfdm.Construct.filter_by_method`,
  `cfdm.Construct.filter_by_measure` methods in the case when no
  arguments are provided: Now returns all possible constructs that
  *could* have the feature, with any values.
* Renamed the "underlying_array" methods to "source"
* Added _field_data_axes attribute to `Constructs` instances.
* Added _units and _fill_value arguments to get_data method.
* Moved contents of cfdm/read_write/constants.py to `NetCDFRead` and
  `NetCDFWrite`.
* Fixed bug in `cfdm.CoordinateReference.clear_coordinates`.
* Fixed bug in `cfdm.Field.convert` (which omitted domain ancillaries
  in the result).
* Added **kwargs parameter to
  `cfdm.CFDMImplementation.initialise_Data`, to facilitate
  subclassing.
* Added `NetCDFRead._customize_read_vars` to facilitate subclassing.
* Added `NetCDFWrite._transform_strings` to facilitate subclassing.

version 1.7.2
-------------
----

**2019-04-05**

* New ``mode`` parameter options to `cfdm.Constructs.filter_by_axis`:
  ``'exact'``, ``'subset'``, ``'superset'``.
* Enabled setting of HDF5 chunksizes.
* Fixed bug that caused coordinate bounds to be not sliced during
  subspacing (https://github.com/NCAS-CMS/cfdm/issues/1).

version 1.7.1
-------------
----

**2019-04-02**

* New methods `cfdm.Constructs.clear_filters_applied`,
  `cfdm.Constructs.filter_by_naxes`.
* Changed behaviour of `cfdm.Constructs.unfilter` and
  `cfdm.Constructs.inverse_filters`: added depth keyword and changed
  default.

version 1.7.0
-------------
----

**2019-04-02**

* First release for CF-1.7
