.. currentmodule:: cfdm
.. default-role:: obj

.. raw:: html

    <style> .small {font-size:small} </style>

.. role:: small

**Introduction**
================

----

Version |release| for version |version| of the CF conventions.

The Python cfdm package is a complete implementation of the
:ref:`CF-data-model`.

**Functionality**
-----------------

----

The cfdm package implements the :ref:`CF-data-model` [#cfdm]_ for its
internal data structures and so is able to process any CF-compliant
dataset. It is not strict about CF-compliance, however, so that
partially conformant datasets may be ingested from existing datasets
and written to new datasets.This is so that datasets which are
partially conformant may nonetheless be modified in memory.

.. code-block:: python
   :caption: *A simple example of reading a field construct from a
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

* read :term:`field constructs <field construct>` from netCDF and CDL
  datasets,

* create new field constructs in memory,

* inspect field constructs,

* test whether two field constructs are the same,

* modify field construct metadata and data,

* create subspaces of field constructs,

* write field constructs to netCDF datasets on disk,

* incorporate, and create, metadata stored in external files,

* read, write, and create data that have been compressed by convention
  (i.e. ragged or gathered arrays), whilst presenting a view of the
  data in its uncompressed form, and

* read, write, and create coordinates defined by geometry cells (new
  in version 1.8.0).

Note that cfdm enables the creation of CF field constructs, but it's
:ref:`up to the user to use them in a CF-compliant way
<CF-conventions>`.

The cfdm package has, with few exceptions, only the functionality
required to read and write datasets, and to create, modify and inspect
field constructs in memory.

Hierarchical groups
^^^^^^^^^^^^^^^^^^^

Hierarchical groups provide a powerful mechanism to structure
variables within datasets. A future |version|.\ *x* release of cfdm
will include support for netCDF4 files containing data organised in
hierarchical groups, but this is not available in version |release|
(even though it is allowed in CF-|version|).

Additional functionality
^^^^^^^^^^^^^^^^^^^^^^^^

The `cf-python <https://ncas-cms.github.io/cf-python>`_ and `cf-plot
<http://ajheaps.github.io/cf-plot/>`_ packages, which are both are
built on top of the cfdm package, include higher level functionality,
such as regridding, statistical operations and comprehensive
visualisation.

----

.. [#cfdm] :small:`Hassell, D., Gregory, J., Blower, J.,
           Lawrence, B. N., and Taylor, K. E.: A data model of the
           Climate and Forecast metadata conventions (CF-1.6) with a
           software implementation (cf-python v2.1), Geosci. Model
           Dev., 10, 4619-4646,
           https://doi.org/10.5194/gmd-10-4619-2017, 2017.`

