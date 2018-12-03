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
   
   ~cfdm.Data.get_array
   ~cfdm.Data.get_dtarray
   ~cfdm.Data.first_element
   ~cfdm.Data.last_element
   ~cfdm.Data.second_element
   ~cfdm.Data.get_calendar
   ~cfdm.Data.get_fill_value
   ~cfdm.Data.get_units

.. rubric:: Attributes

.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Data.dtype
   ~cfdm.Data.ndim
   ~cfdm.Data.shape
   ~cfdm.Data.size
 
Modification
------------
.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.set_calendar
   ~cfdm.Data.set_fill_value
   ~cfdm.Data.set_units
   ~cfdm.Data.expand_dims
   ~cfdm.Data.squeeze
   ~cfdm.Data.transpose
   ~cfdm.Data.unique
      
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
 
Compression
-----------
.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst


   ~cfdm.Data.get_compression_type
   ~cfdm.Data.get_compressed_axes
   ~cfdm.Data.get_compressed_array
   ~cfdm.Data.get_compressed_dimension
   ~cfdm.Data.get_count_variable
   ~cfdm.Data.get_index_variable
   ~cfdm.Data.get_list_variable
   
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

   
