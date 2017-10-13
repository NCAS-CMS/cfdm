Introduction
============

`CF <http://cfconventions.org/>`_ is a `netCDF
<http://www.unidata.ucar.edu/software/netcdf>`_ convention which is in
wide and growing use for the storage of model-generated and
observational data relating to the atmosphere, ocean and Earth system.

This package is an implementation of the `CF data model <URL to
GMD>`_, and as such its API allows for the full scope of data and
metadata interactions described by the CF conventions.

With this package you can:

  * Read `CF-netCDF <http://cfconventions.org/>`_ files,
    `CFA-netCDF <http://www.met.reading.ac.uk/~david/cfa/0.4>`_ files
    and UK Met Office fields files and PP files.
  
  * Create CF fields.

  * Write fields to CF-netCDF and CFA-netCDF files on disk.

  * Aggregate collections of fields into as few multidimensional
    fields as possible using the `CF aggregation rules
    <http://cf-trac.llnl.gov/trac/ticket/78>`_.

  * Create, delete and modify a field's data and metadata.

  * Select and subspace fields according to their metadata.

  * Perform broadcastable, metadata-aware arithmetic, comparison and
    trigonometric operation with fields.

  * Collapse fields by statistical operations.

  * Sensibly deal with date-time data.

  * Allow for cyclic axes.

  * Visualize fields the `cf-plot package
    <http://climate.ncas.ac.uk/~andy/cfplot_sphinx/_build/html/>`_.

All of the above use :ref:`LAMA` functionality, which allows multiple
fields larger than the available memory to exist and be manipulated.

See the `cf-python home page <http://cfpython.bitbucket.org/>`_ for
downloads, installation and source code.
