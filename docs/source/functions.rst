.. currentmodule:: cfdm
.. default-role:: obj

.. _function:

**cfdm functions**
==================

----

Version |release| for version |version| of the CF conventions.

Reading and writing
-------------------

.. autosummary::
   :nosignatures:
   :toctree: function/
   :template: function.rst

   cfdm.read 
   cfdm.write
   cfdm.netcdf_flatten
   cfdm.netcdf_index

Mathematical operations
-----------------------

.. autosummary::
   :nosignatures:
   :toctree: function/
   :template: function.rst

   cf.atol
   cf.rtol

Resource management
-------------------

.. autosummary::
   :nosignatures:
   :toctree: function/
   :template: function.rst

   cf.configuration
   cf.chunksize

Miscellaneous
-------------

.. autosummary::
   :nosignatures:
   :toctree: function/
   :template: function.rst

   cfdm.CF
   cfdm.abspath
   cfdm.environment
   cfdm.example_field
   cfdm.example_fields
   cfdm.example_domain
   cfdm.implementation
   cfdm.integer_dtype
   cfdm.log_level
   cfdm.unique_constructs
