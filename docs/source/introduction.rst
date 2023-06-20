.. currentmodule:: cfdm
.. default-role:: obj

.. raw:: html

    <style> .small {font-size:small} </style>

.. role:: small

**Introduction**
================

----

Version |release| for version |version| of the CF conventions.

.. contents::
   :local:
   :backlinks: entry

The cfdm library implements the data model of the CF (Climate and
Forecast) metadata conventions (http://cfconventions.org) and so
should be able to represent and manipulate all existing and
conceivable CF-compliant datasets.

The CF conventions are designed to promote the creation, processing,
and sharing of climate and forecasting data using Network Common Data
Form (netCDF) files and libraries
(https://www.unidata.ucar.edu/software/netcdf). They cater for data
from model simulations as well as from observations, made in situ or
by remote sensing platforms, of the planetary surface, ocean, and
atmosphere. For a netCDF data variable, they provide a description of
the physical meaning of data and of its spatial, temporal, and other
dimensional properties. The CF data model is an abstract
interpretation of the CF conventions that is independent of the netCDF
encoding.

For more details see *cfdm: A Python reference implementation of the
CF data model* in the Journal of Open Source Software:
https://doi.org/10.21105/joss.02717

----
    
**Functionality**
-----------------

The cfdm library can create field constructs ab initio, or read them
from netCDF files, inspect, subspace and modify in memory, and write
them to CF-netCDF dataset files. As long as it can interpret the data,
cfdm does not enforce CF-compliance, allowing non-compliant datasets
to be read, processed, corrected and rewritten.

It does not contain higher-level analysis functions (such as
regridding) because the expectation is that other libraries will build
on cfdm, inheriting its comprehensive knowledge of the CF conventions,
to add more sophisticated methods.

.. code-block:: python
   :caption: *A basic example of reading a field construct from a
             file and inspecting it.*

   >>> import cfdm
   >>> f = cfdm.read('file.nc')
   >>> f
   [<Field: air_temperature(time(12), latitude(64), longitude(128)) K>]
   >>> print(f[0])
   Field: air_temperature (ncvar%tas)
   ----------------------------------
   Data            : air_temperature(time(12), latitude(64), longitude(128)) K
   Cell methods    : time(12): mean (interval: 1.0 month)
   Dimension coords: time(12) = [0450-11-16 00:00:00, ..., 0451-10-16 12:00:00] noleap
                   : latitude(64) = [-87.8638, ..., 87.8638] degrees_north
                   : longitude(128) = [0.0, ..., 357.1875] degrees_east
                   : height(1) = [2.0] m

The cfdm package can

* read :term:`field constructs <field construct>` and :term:`domain
  constructs <domain construct>` from netCDF and CDL datasets,

* create new field and domain constructs in memory,

* write field and domain constructs to netCDF datasets on disk,

* read, write, and create coordinates defined by geometry cells,

* read and write netCDF4 string data-type variables,

* read, write, and create netCDF and CDL datasets containing
  hierarchical groups,

* inspect field and domain constructs,

* test whether two constructs are the same,

* modify field and domain construct metadata and data,

* create subspaces of field and domain constructs,

* incorporate, and create, metadata stored in external files, and

* read, write, and create data that have been compressed by convention
  (i.e. ragged or gathered arrays, or coordinate arrays compressed by
  subsampling), whilst presenting a view of the data in its
  uncompressed form.

Note that the cfdm package enables the representation and creation of
CF field constructs, but it is largely :ref:`up to the user to use
them in a CF-compliant way <CF-conventions>`.

A command line tool is provided that allows inspection of datasets
outside of a Python environment:

.. code-block:: console
   :caption: *Inspect a dataset from the command line.*

   $ cfdump file.nc
   Field: air_temperature (ncvar%tas)
   ----------------------------------
   Data            : air_temperature(time(12), latitude(64), longitude(128)) K
   Cell methods    : time(12): mean (interval: 1.0 month)
   Dimension coords: time(12) = [0450-11-16 00:00:00, ..., 0451-10-16 12:00:00] noleap
                   : latitude(64) = [-87.8638, ..., 87.8638] degrees_north
                   : longitude(128) = [0.0, ..., 357.1875] degrees_east
                   : height(1) = [2.0] m

----

**Related packages**
--------------------

The `cf-python <https://ncas-cms.github.io/cf-python>`_ package, which
is built as an extension to cfdm, includes higher-level functionality,
such as regridding, and statistical operations. In turn, the `cf-plot
<http://ajheaps.github.io/cf-plot/>`_ package provides comprehensive
visualisation of field constructs created by cf-python.

----

**Citation**
------------

If you use cfdm, either as a stand-alone application or to provide a
CF data model implementation to another software library, please
consider including the reference:

Hassell, D., and Bartholomew, S. L. (2020). cfdm: A Python reference
  implementation of the CF data model. Journal of Open Source
  Software, 5(54), 2717, https://doi.org/10.21105/joss.02717

.. code-block:: bibtex
   
   @article{Hassell2020,
     doi = {10.21105/joss.02717},
     url = {https://doi.org/10.21105/joss.02717},
     year = {2020},
     publisher = {The Open Journal},
     volume = {5},
     number = {54},
     pages = {2717},
     author = {David Hassell and Sadie L. Bartholomew},
     title = {cfdm: A Python reference implementation of the CF data model},
     journal = {Journal of Open Source Software}
   }

----

**References**
--------------

Eaton, B., Gregory, J., Drach, B., Taylor, K., Hankin, S., Caron, J.,
  Signell, R., et al. (2020). NetCDF Climate and Forecast (CF)
  Metadata Conventions. CF Conventions Committee. Retrieved from
  https://cfconventions.org/cf-conventions/cf-conventions.html

Hassell, D., and Bartholomew, S. L. (2020). cfdm: A Python reference
  implementation of the CF data model. Journal of Open Source
  Software, 5(54), 2717, https://doi.org/10.21105/joss.02717

Hassell, D., Gregory, J., Blower, J., Lawrence, B. N., and
  Taylor, K. E. (2017). A data model of the Climate and Forecast
  metadata conventions (CF-1.6) with a software implementation
  (cf-python v2.1), Geosci. Model Dev., 10, 4619-4646,
  https://doi.org/10.5194/gmd-10-4619-2017

Rew, R., and Davis, G. (1990). NetCDF: An Interface for Scientific
  Data Access. IEEE Computer Graphics and Applications, 10(4),
  76–82. https://doi.org/10.1109/38.56302

Rew, R., Hartnett, E., and Caron, J. (2006). NetCDF-4: Software
  Implementing an Enhanced Data Model for the Geosciences. In 22nd
  International Conference on Interactive Information Processing
  Systems for Meteorology, Oceanography, and Hydrology. AMS. Retrieved
  from
  https://www.unidata.ucar.edu/software/netcdf/papers/2006-ams.pdf
