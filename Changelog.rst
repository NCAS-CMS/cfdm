version 1.7.3
-------------
----

**Not yet released**

* Renamed the "underlying_array" methods to "source"
* New method: Constructs.filter_by_size
* New method: Data.uncompress
  
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
