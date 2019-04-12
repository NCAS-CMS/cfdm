.. currentmodule:: cfdm
.. default-role:: obj


.. _Performance:

**Performance**
===============
----

Version |release| for version |version| of the CF conventions.

Memory
------
----

When a dataset is read using `cfdm.read` but `lazy loading
<https://en.wikipedia.org/wiki/Lazy_loading>`_ is employed for all
data arrays, which means that no data is read into memory until the
data is required for inspection or to modify the array contents. This
maximizes the number of field constructs that may be read within a
session, and makes the read operation fast. If a :ref:`subspace
<Subspacing>` of the data in the file is requested then only that
subspace is read into memory. These behaviours are inherited from the
`netCDF4 python package
<http://unidata.github.io/netcdf4-python/netCDF4/index.html>`_.

When an instance is copied with its `!copy` method, any data are
copied with a `copy-on-write
<https://en.wikipedia.org/wiki/Copy-on-write>`_ technique. This means
that a copy takes up very little memory, even when the original data
comprises a very large array in memory, and the copy operation is
fast.



In-place operations
-------------------
----

Some methods that create new a instance by default have an option to
perform the operation in-place, rather than creating a new,
independent object. The in-place operation can be considerably
faster. These methods have the ``inplace`` keyword parameter, such as
the `~Field.squeeze`, `~Field.transpose` and `~Field.insert_dimension`
methods of a field construct.
  
For example, in one test using a file from the :ref:`Tutorial`,
transposing the data dimensions of the field construct was ~10 times
faster when done in-place, compared with creating a new independent
field construct:

.. code-block:: python
   :caption: *Calculate the speed-up of performing the "transpose"
             operation in-place. The data are brought into memory
             prior to the to remove the time taken to read the dataset
             from disk from the results.*
      
   >>> import timeit
   >>> import cfdm
   >>> q, t = cfdm.read('file.nc')
   >>> t.data.to_memory()
   >>> min(timeit.repeat('t.transpose()', globals=globals(), number=1000))
   1.3255651500003296
   >>> min(timeit.repeat('t.transpose(inplace=True)', globals=globals(), number=1000))
   0.10816403700118826
