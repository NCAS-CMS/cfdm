.. currentmodule:: cfdm
.. default-role:: obj


.. _Optimization:

**Optimization**
================

----

Version |release| for version |version| of the CF conventions.


* In-place operations

  Some methods that, by default, create new a field construct (such as
  `~Field.squeeze`, `~Field.transpose` and `~Field.insert_dimension`)
  have an option to perform the operation in-place, rather than
  creating a new, independent object. The in-place operation can be
  considerably faster.
  
  For example, in one test using a file from the :ref:`Tutorial`,
  removing the size 1 dimensions from the field construct's data is 45
  times faster if done in-place, compared with creating a new,
  indpendent field construct:

  .. code:: python
  
     >>> import timeit
     >>> setup = "import cfdm; q, t = cfdm.read('file.nc')"
     >>> timeit.timeit('t.squeeze()', setup=setup, number=1000)
     16.33798599243164
     >>> timeit.timeit('t.squeeze(inplace=True)', setup=setup, number=1000)
     0.3618600368499756

   
