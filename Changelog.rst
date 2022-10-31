Version 1.10.0.1
----------------

**2022-10-31**

* New method: `cfdm.Data.get_tie_point_indices`
* New method: `cfdm.Data.get_interpolation_parameters`
* New method: `cfdm.Data.get_dependent_tie_points`
* Record the names of files that contain the original data
  (https://github.com/NCAS-CMS/cfdm/issues/215)
* New method: `cfdm.Field.get_original_filenames`
* New method: `cfdm.Data.get_original_filenames`
* New keyword parameter to `cfdm.write`: ``omit_data``
  (https://github.com/NCAS-CMS/cfdm/issues/221)
* Fixed bug that caused incorrect data assignment with some multiple
  list indices (https://github.com/NCAS-CMS/cfdm/issues/217)
* Fixed bug that caused a failure when printing date-time data with
  the first element masked
  (https://github.com/NCAS-CMS/cfdm/issues/211)

Version 1.10.0.0
----------------

**2022-08-17**

* New method: `cfdm.Field.auxiliary_coordinate`
* New method: `cfdm.Field.cell_measure`
* New method: `cfdm.Field.cell_method`
* New method: `cfdm.Field.coordinate`
* New method: `cfdm.Field.coordinate_reference`
* New method: `cfdm.Field.dimension_coordinate`
* New method: `cfdm.Field.domain_ancillary`
* New method: `cfdm.Field.domain_axis`
* New method: `cfdm.Field.field_ancillary`
* New method: `cfdm.Field.indices`
* New attribute: `cfdm.Field.array`
* New attribute: `cfdm.Field.datetime_array`
* New construct retrieval API methods
  (https://github.com/NCAS-CMS/cfdm/issues/179)
* Implement (bar writing to netCDF files) lossy compression by
  coordinate subsampling (https://github.com/NCAS-CMS/cfdm/issues/167)

----
  
Version 1.9.0.4
---------------

**2022-07-18**

* Upgrade to allow cfdm to work with Python 3.10
  (https://github.com/NCAS-CMS/cfdm/issues/187)
* Fix bug that caused a hang when reading zero-length files
  (https://github.com/NCAS-CMS/cfdm/issues/190)
* Fix bug to prevent error when writing vlen strings to a netCDF file
  when compression has been set (for `netCDF4>=1.6.0`)
  (https://github.com/NCAS-CMS/cfdm/issues/199)
  
Version 1.9.0.3
---------------

**2022-03-10**

* Fixed bug that caused a failure from `cfdm.write` when writing
  identical (auxiliary) coordinates to different data variables in
  different groups (https://github.com/NCAS-CMS/cfdm/issues/177)
* Fixed bug that caused `cf.Domain.__str__` to fail when a dimension
  coordinate construct does not have data
  (https://github.com/NCAS-CMS/cfdm/issues/174)
* New dependency: ``packaging>=20.0``
* Changed dependency: ``cftime>=1.6.0``

----
  
Version 1.9.0.2
---------------

**2022-01-31**

* Fixed bug that caused a `cfdm.write` failure when a vertical
  coordinate reference construct has no coordinates
  (https://github.com/NCAS-CMS/cfdm/issues/164)
* Fixed bug that caused a failure when downstream `identities` methods
  return an `itertools.chain` object
  (https://github.com/NCAS-CMS/cfdm/issues/170)

----
  
Version 1.9.0.1
---------------

**2021-10-12**

* Fixed bug that prevented some geometry coordinates being written to
  netCDF CLASSIC files (https://github.com/NCAS-CMS/cfdm/issues/140)
* Fixed bug that a caused segmentation fault when appending a string
  data type to netCDF files
  (https://github.com/NCAS-CMS/cfdm/issues/155)
* Fixed bug in `cf.Field.get_domain` when there are climatological
  time axes (https://github.com/NCAS-CMS/cfdm/issues/159)

----
  
Version 1.9.0.0
---------------

**2021-09-21**

* Python 3.6 support removed
  (https://github.com/NCAS-CMS/cfdm/issues/139)
* Conversion of `cfdm.Domain` to a non-abstract that may be read from
  and written to a netCDF dataset
  (https://github.com/NCAS-CMS/cfdm/issues/111)
* New method: `cfdm.Domain.creation_commands`
* New method: `cfdm.Domain.climatological_time_axes`
* New method: `cfdm.AuxiliaryCoordinate.del_climatology`
* New method: `cfdm.AuxiliaryCoordinate.get_climatology`
* New method: `cfdm.AuxiliaryCoordinate.is_climatology`
* New method: `cfdm.AuxiliaryCoordinate.set_climatology`
* New method: `cfdm.DimensionCoordinate.del_climatology`
* New method: `cfdm.DimensionCoordinate.get_climatology`
* New method: `cfdm.DimensionCoordinate.is_climatology`
* New method: `cfdm.DimensionCoordinate.set_climatology`
* New function: `cfdm.unique_constructs`
* New function: `cfdm.example_fields`
* Construct access API changes from 1.8.9.0 applied to `Field.convert`
* Improved error message for invalid inputs to `Field.convert`
* Raise exception when attempting to write multiply defined coordinate
  reference parameters (https://github.com/NCAS-CMS/cfdm/issues/148)
* Interpret format specifiers for size 1 `cfdm.Data` arrays
  (https://github.com/NCAS-CMS/cfdm/issues/152)
* Fix file name expansions in `cfdm.write`
  (https://github.com/NCAS-CMS/cfdm/issues/157)
  
----

Version 1.8.9.0
---------------

**2021-05-25**

* Construct access API changes
  (https://github.com/NCAS-CMS/cfdm/issues/124,
  https://github.com/NCAS-CMS/cfdm/issues/130,
  https://github.com/NCAS-CMS/cfdm/issues/132,
  https://github.com/NCAS-CMS/cfdm/issues/137)
* Performance enhancements
  (https://github.com/NCAS-CMS/cfdm/issues/124,
  https://github.com/NCAS-CMS/cfdm/issues/130)
* New write mode ``mode='a'`` for appending to, rather than over-writing,
  a netCDF file on disk (https://github.com/NCAS-CMS/cfdm/issues/143)
* Better error message in the case of a `numpy.ma.core.MaskError` occurring
  upon reading of CDL files with only header or coordinate information
  (https://github.com/NCAS-CMS/cfdm/issues/128)
* Fix for zero-sized unlimited dimensions when read from a grouped
  netCDF file (https://github.com/NCAS-CMS/cfdm/issues/113)
* Fix bug causing occasional non-symmetric `equals` operations
  (https://github.com/NCAS-CMS/cfdm/issues/133)
* Changed dependency: ``cftime>=1.5.0``
* Changed dependency: ``netCDF4>=1.5.4``

----

Version 1.8.8.0
---------------

**2020-12-18**

* The setting of global constants can now be controlled by a context
  manager (https://github.com/NCAS-CMS/cfdm/issues/100)
* Fixed bug that caused a failure when writing a dataset that contains
  a scalar domain ancillary construct
  (https://github.com/NCAS-CMS/cfdm/issues/98)
* Changed dependency: ``cftime>=1.3.0``

----

Version 1.8.7.0
---------------

**2020-10-09**

* Python 3.5 support deprecated (3.5 was retired on 2020-09-13)
* New method: `cfdm.Field.creation_commands`
* New method: `cfdm.Data.creation_commands`
* New method: `cfdm.Field._docstring_special_substitutions`
* New method: `cfdm.Field._docstring_substitutions`
* New method: `cfdm.Field._docstring_package_depth`
* New method: `cfdm.Field._docstring_method_exclusions`
* New method: `cfdm.Data.filled`
* New keyword parameter to `cfdm.Field.set_data`: ``inplace``
* New keyword parameter to `cfdm.write`: ``coordinates``
  (https://github.com/NCAS-CMS/cfdm/issues/81)
* New class: `cfdm.core.DocstringRewriteMeta`
* Comprehensive documentation coverage of class methods.
* Improved documentation following JOSS review.
* Enabled "creation commands" methods
  (https://github.com/NCAS-CMS/cfdm/issues/53)
* Fixed bug that caused failures when reading or writing a dataset
  that contains multiple geometry containers
  (https://github.com/NCAS-CMS/cfdm/issues/65)
* Fixed bug that prevented the writing of multiple fields to netCDF when
  at least one dimension was shared between some of the fields.

----

Version 1.8.6.0
---------------

**2020-07-24**

* Removed Python 2.7 support
  (https://github.com/NCAS-CMS/cfdm/issues/55)
* Implemented the reading and writing of netCDF4 group hierarchies for
  CF-1.8 (https://github.com/NCAS-CMS/cfdm/issues/13)
* Renamed to lower-case (but otherwise identical) names all functions
  which get and set global constants: `cfdm.atol`, `cfdm.rtol`,
  `cfdm.log_level`. The old names e.g. `cfdm.ATOL` remain functional
  as aliases.
* New function: `cfdm.configuration`
* New method: `cfdm.Field.nc_variable_groups`
* New method: `cfdm.Field.nc_set_variable_groups`
* New method: `cfdm.Field.nc_clear_variable_groups`
* New method: `cfdm.Field.nc_group_attributes`
* New method: `cfdm.Field.nc_set_group_attribute`
* New method: `cfdm.Field.nc_set_group_attributes`
* New method: `cfdm.Field.nc_clear_group_attributes`
* New method: `cfdm.Field.nc_geometry_variable_groups`
* New method: `cfdm.Field.nc_set_geometry_variable_groups`
* New method: `cfdm.Field.nc_clear_geometry_variable_groups`
* New method: `cfdm.DomainAxis.nc_dimension_groups`
* New method: `cfdm.DomainAxis.nc_set_dimension_groups`
* New method: `cfdm.DomainAxis.nc_clear_dimension_groups`
* New method: `cfdm.AuxiliaryCoordinate.del_interior_ring`
* New keyword parameter to `cfdm.write`: ``group``
* Keyword parameter ``verbose`` to multiple methods now accepts named
  strings, not just the equivalent integer levels, to set verbosity.
* Added test to check that cell bounds have more dimensions than the
  data.
* Added test to check that dimension coordinate construct data is
  1-dimensional.
* Fixed bug in `cfdm.CompressedArray.to_memory`.
* Fixed bug that caused an error when a coordinate bounds variable is
  missing from a dataset (https://github.com/NCAS-CMS/cfdm/issues/63)
* New dependency: ``netcdf_flattener>=1.2.0``
* Changed dependency: ``cftime>=1.2.1``
* Removed dependency: ``future``

----

Version 1.8.5
-------------

**2020-06-10**

* Fixed bug that prevented the reading of certain netCDF files, such
  as those with at least one external variable.

----

Version 1.8.4
-------------

**2020-06-08**

* Added new example field ``7`` to `cfdm.example_field`.
* Enabled configuration of the extent and nature of informational and
  warning messages output by `cfdm` using a logging framework (see
  points below) (https://github.com/NCAS-CMS/cfdm/issues/31)
* New function `cfdm.LOG_LEVEL` to set the minimum log level for which
  messages are displayed globally, i.e. to change the project-wide
  verbosity (https://github.com/NCAS-CMS/cfdm/issues/35).
* Changed behaviour and default of `verbose` keyword argument when
  available to a function/method so it interfaces with the new logging
  functionality (https://github.com/NCAS-CMS/cfdm/issues/35).
* Changed dependency: ``cftime>=1.1.3``
* Fixed bug the wouldn't allow the reading of a netCDF file which
  specifies Conventions other than CF
  (https://github.com/NCAS-CMS/cfdm/issues/36).

----

Version 1.8.3
-------------

**2020-04-30**

* `cfdm.Field.apply_masking` now masks metadata constructs.
* New method: `cfdm.Field.get_filenames`
* New method: `cfdm.Data.get_filenames`
* New function: `cfdm.abspath`
* New keyword parameter to `cfdm.read`: ``warn_valid``
  (https://github.com/NCAS-CMS/cfdm/issues/30)
* New keyword parameter to `cfdm.write`: ``warn_valid``
  (https://github.com/NCAS-CMS/cfdm/issues/30)
  

----

Version 1.8.2
-------------

**2020-04-24**

* Added time coordinate bounds to the polygon geometry example field
  ``6`` returned by `cfdm.example_field`.
* New method: `cfdm.Field.apply_masking`
* New method: `cfdm.Data.apply_masking`
* New keyword parameter to `cfdm.read`: ``mask``
* New keyword parameter to `cfdm.Field.nc_global_attributes`:
  ``values``
* Fixed bug in `cfdm.write` that caused (what are effectively)
  string-valued scalar auxiliary coordinates to not be written to disk
  as such, or even an exception to be raised.
  
----

Version 1.8.1
-------------

**2020-04-16**

* Improved source code highlighting in links from the documentation
  (https://github.com/NCAS-CMS/cfdm/issues/21).
* Fixed bug that erroneously required netCDF geometry container
  variables to have a ``geometry_dimension`` netCDF attribute.

----

Version 1.8.0
-------------

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
* Changed dependency: ``netCDF4>=1.5.3``
* Changed dependency: ``cftime>=1.1.1``
* Fixed bug that prevented the writing of ``'NETCDF3_64BIT_OFFSET'``
  and ``'NETCDF3_64BIT_DATA'`` format files
  (https://github.com/NCAS-CMS/cfdm/issues/9).
* Fixed bug that caused a failure when a "_FillValue" or
  "missing_value" property is set and data type conversions are
  specified with the ``datatype`` keyword to `cfdm.write`
  (https://github.com/NCAS-CMS/cfdm/issues/16).
* Fixed bug whereby `cfdm.Field.has_construct` would try to delete the
  construct rather than check whether it existed.

----

Version 1.7.11
--------------

**2019-11-27**

* New methods: `cfdm.Field.compress`, `cfdm.Field.uncompress`
* New methods: `cfdm.Data.flatten`, `cfdm.Data.uncompress`
* New  ``dtype`` and ``mask`` keyword parameters to `cfdm.Data`
* Changed the default value of the ``ignore_compression`` parameter to
  `True`.

----

Version 1.7.10
--------------

**2019-11-14**

* New method: `cfdm.Field.nc_set_global_attributes`.
* Fixed bug relating to the reading of some CDL files
  (https://github.com/NCAS-CMS/cfdm/issues/5).
* Fixed bug relating numpy warning when printing a field with masked
  reference time values (https://github.com/NCAS-CMS/cfdm/issues/8).

----

Version 1.7.9
-------------

**2019-11-07**

* Fixed bug relating to setting of parameters on datum and coordinate
  conversion objects of coordinate conversion constructs
  (https://github.com/NCAS-CMS/cfdm/issues/6).

----

Version 1.7.8
-------------

**2019-10-04**

* During writing to netCDF files, ensured that _FillValue and
  missing_value have the same data type as the data.
* Fixed bug during construct equality testing that didn't recognise
  equal cell method constructs in transposed, but otherwise equal
  field constructs.
* Bounds netCDF dimension name is now saved, and can be set. The
  saved/set value is written out to disk.
* Now reads CDL files (https://github.com/NCAS-CMS/cfdm/issues/5)

----

Version 1.7.7
-------------

**2019-06-13**

* Don't set the fill mode for a `netCDF4.Dataset` open for writing to
  `off`, to prevent incorrect reading of some netCDF4 files
  (https://github.com/NCAS-CMS/cfdm/issues/4).
* Updated documentation
  
----

Version 1.7.6
-------------

**2019-06-05**

* Added attributes `_ATOL` and `_RTOL` to facilitate subclassing.
* Fixed bug in `cfdm.Field.convert`.
* Fixed bug in `cfdm.core.constructs.new_identifier`.
  
----

Version 1.7.5
-------------

**2019-05-15**

* New methods: `Datum.nc_has_variable`, `Datum.nc_get_variable`,
  `Datum.nc_has_variable`, `Datum.nc_set_variable`
  (https://github.com/NCAS-CMS/cfdm/issues/3).
  
----

Version 1.7.4
-------------

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
  
----

Version 1.7.3
-------------

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
* Added ``kwargs`` parameter to
  `cfdm.CFDMImplementation.initialise_Data`, to facilitate
  subclassing.
* Added `NetCDFRead._customize_read_vars` to facilitate subclassing.
* Added `NetCDFWrite._transform_strings` to facilitate subclassing.

----

Version 1.7.2
-------------

**2019-04-05**

* New ``mode`` parameter options to `cfdm.Constructs.filter_by_axis`:
  ``'exact'``, ``'subset'``, ``'superset'``.
* Enabled setting of HDF5 chunksizes.
* Fixed bug that caused coordinate bounds to be not sliced during
  subspacing (https://github.com/NCAS-CMS/cfdm/issues/1).

----

Version 1.7.1
-------------

**2019-04-02**

* New methods `cfdm.Constructs.clear_filters_applied`,
  `cfdm.Constructs.filter_by_naxes`.
* Changed behaviour of `cfdm.Constructs.unfilter` and
  `cfdm.Constructs.inverse_filters`: added depth keyword and changed
  default.

----

Version 1.7.0
-------------

**2019-04-02**

* First release for CF-1.7

----
