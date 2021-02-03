.. currentmodule:: cfdm
.. default-role:: obj


.. _Performance:

**Performance**
===============
----

Version |release| for version |version| of the CF conventions.


.. contents::
   :local:
   :backlinks: entry

.. _Memory:

**Memory**
----------

When a dataset is read using `cfdm.read`, `lazy loading
<https://en.wikipedia.org/wiki/Lazy_loading>`_ is employed for all
data arrays, which means that no data is read into memory until the
data is required for inspection or to modify the array contents. This
maximises the number of :term:`field constructs <field construct>`
that may be read within a session, and makes the read operation
fast. If a :ref:`subspace <Subspacing>` of data still in the file is
requested then only that subspace is read into memory. These
behaviours are inherited from the `netCDF4 python package
<http://unidata.github.io/netcdf4-python/netCDF4/index.html>`_.

When an instance is copied with its `!copy` method, all data are
copied with a `copy-on-write
<https://en.wikipedia.org/wiki/Copy-on-write>`_ technique. This means
that a copy takes up very little memory, even when the original data
comprises a very large array in memory, and the copy operation is
fast.

----

.. _In-place-operations:

**In-place operations**
-----------------------

Some methods that create new a instance have an option to perform the
operation in-place, rather than creating a new independent object. The
in-place operation can be considerably faster. These methods have the
``inplace`` keyword parameter, such as the `~Field.squeeze`,
`~Field.transpose`, `~Field.insert_dimension`, `~Field.compress`, and
`~Field.uncompress` methods of a field construct.
  
For example, in one particular test, transposing the data dimensions
of the field construct was ~10 times faster when done in-place,
compared with creating a new independent field construct:

.. code-block:: python
   :caption: *Calculate the speed-up of performing the "transpose"
             operation in-place.
      
   >>> import timeit
   >>> import cfdm
   >>> f = cfdm.example_field(0)
   >>> print(f)
   Field: specific_humidity (ncvar%q)
   ----------------------------------
   Data            : specific_humidity(latitude(5), longitude(8)) 1
   Cell methods    : area: mean
   Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                   : longitude(8) = [22.5, ..., 337.5] degrees_east
                   : time(1) = [2019-01-01 00:00:00]
   >>> min(timeit.repeat('g = f.transpose()',
   ...                   globals=globals(), number=1000))
   1.2819487630004005
   >>> min(timeit.repeat('f.transpose(inplace=True)',
   ...                   globals=globals(), number=1000))
   0.13453567200122052

