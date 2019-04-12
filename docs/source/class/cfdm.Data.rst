.. currentmodule:: cfdm
.. default-role:: obj

cfdm.Data
=========

----

.. autoclass:: cfdm.Data
   :no-members:
   :no-inherited-members:

Inspection
-----------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
   
   ~cfdm.Data.first_element
   ~cfdm.Data.second_element
   ~cfdm.Data.last_element

.. rubric:: Attributes

.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Data.array
   ~cfdm.Data.datetime_array
   ~cfdm.Data.dtype
   ~cfdm.Data.ndim
   ~cfdm.Data.shape
   ~cfdm.Data.size
 
Units
-----

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
   
   ~cfdm.Data.get_units
   ~cfdm.Data.set_units
   ~cfdm.Data.set_calendar 
   ~cfdm.Data.get_calendar

Fill value
----------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
   
   ~cfdm.Data.get_fill_value
   ~cfdm.Data.set_fill_value

Dimensions
----------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.insert_dimension
   ~cfdm.Data.squeeze
   ~cfdm.Data.transpose

      
Calculation
-----------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.max
   ~cfdm.Data.min
   ~cfdm.Data.sum
   ~cfdm.Data.unique
      
Miscellaneous
-------------
.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.copy
   ~cfdm.Data.equals
   ~cfdm.Data.to_memory
   
Compression
-----------
.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst


   ~cfdm.Data.get_compression_type
   ~cfdm.Data.get_compressed_axes
   ~cfdm.Data.get_compressed_dimension
   ~cfdm.Data.get_count
   ~cfdm.Data.get_index
   ~cfdm.Data.get_list
   
.. rubric:: Attributes

.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Data.compressed_array

NetCDF
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.nc_hdf5_chunksizes
   ~cfdm.Data.nc_clear_hdf5_chunksizes
   ~cfdm.Data.nc_set_hdf5_chunksizes

Special
-------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.__array__
   ~cfdm.Data.__deepcopy__
   ~cfdm.Data.__getitem__
   ~cfdm.Data.__repr__
   ~cfdm.Data.__setitem__
   ~cfdm.Data.__str__

   
