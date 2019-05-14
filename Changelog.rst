version 1.7.4
-------------
----

**Not yet released**

* Changed behaviour of Constructs.filter_by_axis.
* New methods: Data.has_units, Data.has_calendar, Data.has_fill_value.
* New keyword 'constructs' to Field.transpose.
* Keyword 'axes' to Field.set_data is now optional.
* Added the 'has_bounds' method to constructs that have data but can't
  have bounds.
* New methods: DomainAxis.nc_is_unlimited,
  DomainAxis.nc_set_unlimited.
* Made Data a virtual subclass of Array.   
* Deprecated methods: Field.nc_unlimited, Field.nc_clear_unlimited,
  Field.nc_clear_unlimited.
* Fixed bug when writing new horizontal coordinate reference for the
  vertical datum.
* Fixed bug in del_data method.
* Fixed bug with in-place operations.
* Fixed bug with position in some insert_dimension methods.
* Fixed bug that sometimes made duplicate netCDF dimensions when
  writing to a file.
* Added _shape keyword to Field.set_data_axes to allow the data shape
  to be checked prior to insertion.
* Added the '_custom' attribute to facilitate subclassing.
* New class mixin.NetCDFUnlimitedDimension replaces
  mixin.NetCDFUnlimitedDimensions, which is deprecated.
* New method CFDMImplementation.nc_is_unlimited_axis replaces
  CFDMImplementation.nc_get_unlimited_axes, which is deprecated.
* New method CFDMImplementation.nc_set_unlimited_axis replaces
  CFDMImplementation.nc_set_unlimited_dimensions, which is deprecated.
  
version 1.7.3
-------------
----

**2019-04-24**

* New method: Constructs.filter_by_size
* New method: Data.uncompress
* Changed the default behaviours of the Construct.filter_by_axis,
  Construct.filter_by_size, Construct.filter_by_naxes,
  Construct.filter_by_property, Construct.filter_by_ncvar,
  Construct.filter_by_ncdim, Construct.filter_by_method,
  Construct.filter_by_measure methods in the case when no arguments
  are provided: Now returns all possible constructs that *could* have
  the feature, with any values.
* Renamed the "underlying_array" methods to "source"
* Added _field_data_axes attribute to Constructs instances.
* Added _units and _fill_value arguments to get_data method.
* Moved contents of cfdm/read_write/constants.py to NetCDFRead and
  NetCDFWrite.
* Fixed bug in CoordinateReference.clear_coordinates
* Fixed bug in Field.convert (which omitted domain ancillaries in the result)
* Added **kwargs parameter to CFDMImplementation.initialise_Data, to
  facilitate subclassing.
* Added NetCDFRead._customize_read_vars to facilitate sublcassing.
* Added NetCDFWrite._transform_strings to facilitate sublcassing.

version 1.7.2
-------------
----

**2019-04-05**

* New "mode" parameter options to Constructs.filter_by_axis: 'exact',
  'subset', 'superset'
* Enabled setting of HDF5 chunksizes
* Fixed bug that caused coordinate bounds to be not sliced during
  subspacing.

version 1.7.1
-------------
----

**2019-04-02**

* New methods Constructs.clear_filters_applied,
  Constructs.filter_by_naxes
* Changed behaviour of Constructs.unfilter and
  Constructs.inverse_filters: added depth keyword and changed default

version 1.7.0
-------------
----

**2019-04-02**

* First release for CF-1.7
