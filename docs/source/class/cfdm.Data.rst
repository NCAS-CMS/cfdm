.. currentmodule:: cfdm
.. default-role:: obj

cfdm.Data
=========

.. autoclass:: cfdm.Data
   :no-members:
   :no-inherited-members:

Inspection
----------

.. rubric:: Attributes
	    
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Data.array
   ~cfdm.Data.sparse_array
   ~cfdm.Data.dtype
   ~cfdm.Data.ndim
   ~cfdm.Data.shape
   ~cfdm.Data.size
   ~cfdm.Data.nbytes
   
Units
-----

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.del_units
   ~cfdm.Data.get_units
   ~cfdm.Data.has_units
   ~cfdm.Data.set_units

.. rubric:: Attributes
	    
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Data.Units
   
Date-time support
-----------------

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.del_calendar
   ~cfdm.Data.get_calendar
   ~cfdm.Data.has_calendar
   ~cfdm.Data.set_calendar

.. rubric:: Attributes

.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Data.datetime_array
   ~cfdm.Data.dtarray
   ~cfdm.Data.datetime_as_string

Dask
----

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.compute
   ~cfdm.Data.persist
   ~cfdm.Data.cull_graph
   ~cfdm.Data.dask_compressed_array
   ~cfdm.Data.rechunk
   ~cfdm.Data.chunk_indices
   ~cfdm.Data.todict
   ~cfdm.Data.to_dask_array
   ~cfdm.Data.get_deterministic_name
   ~cfdm.Data.has_deterministic_name

.. rubric:: Attributes

.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Data.chunks
   ~cfdm.Data.chunksize
   ~cfdm.Data.npartitions
   ~cfdm.Data.numblocks
   
Data creation routines
----------------------

Ones and zeros
^^^^^^^^^^^^^^
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.empty
   ~cfdm.Data.ones
   ~cfdm.Data.zeros
   ~cfdm.Data.full

From existing data
^^^^^^^^^^^^^^^^^^

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.asdata
   ~cfdm.Data.copy

Data manipulation routines
--------------------------

Changing data shape
^^^^^^^^^^^^^^^^^^^

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.flatten
   ~cfdm.Data.reshape


Transpose-like operations
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.transpose

Changing number of dimensions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.insert_dimension
   ~cfdm.Data.squeeze

Adding and removing elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.unique

Expanding the data
^^^^^^^^^^^^^^^^^^

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.pad_missing
	    
Indexing routines
-----------------

Single value selection
^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.first_element
   ~cfdm.Data.second_element
   ~cfdm.Data.last_element

Logic functions
---------------

Truth value testing
^^^^^^^^^^^^^^^^^^^
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.all
   ~cfdm.Data.any

Comparison
^^^^^^^^^^

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.equals

Mask support
------------

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.harden_mask
   ~cfdm.Data.soften_mask
   ~cfdm.Data.apply_masking
   ~cfdm.Data.masked_where
   ~cfdm.Data.filled
   ~cfdm.Data.masked_values
   ~cfdm.Data.del_fill_value
   ~cfdm.Data.get_fill_value
   ~cfdm.Data.has_fill_value
   ~cfdm.Data.set_fill_value
   
.. rubric:: Attributes

.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Data.hardmask
   ~cfdm.Data.mask
   ~cfdm.Data.fill_value

Mathematical functions
----------------------

Sums, products, differences
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.sum

Set routines
-------------

Making proper sets
^^^^^^^^^^^^^^^^^^    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.unique
	    
Sorting, searching, and counting
--------------------------------

Statistics
----------

Order statistics
^^^^^^^^^^^^^^^^

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.maximum
   ~cfdm.Data.minimum
   ~cfdm.Data.max
   ~cfdm.Data.min

Sums
^^^^

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.sum

Compression by convention
-------------------------
   
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.get_compressed_axes
   ~cfdm.Data.get_compressed_dimension
   ~cfdm.Data.get_compression_type
   ~cfdm.Data.get_count
   ~cfdm.Data.get_index
   ~cfdm.Data.get_list
   ~cfdm.Data.get_dependent_tie_points
   ~cfdm.Data.get_interpolation_parameters
   ~cfdm.Data.get_tie_point_indices
   ~cfdm.Data.uncompress

.. rubric:: Attributes

.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Data.compressed_array

Miscellaneous
-------------
   
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.creation_commands
   ~cfdm.Data.get_data
   ~cfdm.Data.get_filenames
   ~cfdm.Data.get_original_filenames
   ~cfdm.Data.source
   ~cfdm.Data.chunk_indices

.. rubric:: Attributes
	    
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

    ~cfdm.Data.data
    ~cfdm.Data.tolist

Performance
-----------

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.Data.nc_clear_hdf5_chunksizes
   ~cfdm.Data.nc_hdf5_chunksizes
   ~cfdm.Data.nc_set_hdf5_chunksizes
   ~cfdm.Data.to_memory

Special
-------

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Data.__array__
   ~cfdm.Data.__deepcopy__
   ~cfdm.Data.__getitem__ 
   ~cfdm.Data.__int__
   ~cfdm.Data.__iter__ 
   ~cfdm.Data.__repr__
   ~cfdm.Data.__setitem__ 
   ~cfdm.Data.__str__

Docstring substitutions
-----------------------                   
                                          
.. rubric:: Methods                       
                                          
.. autosummary::                          
   :nosignatures:                         
   :toctree: ../method/                   
   :template: method.rst                  
                                          
   ~cfdm.Data._docstring_special_substitutions
   ~cfdm.Data._docstring_substitutions        
   ~cfdm.Data._docstring_package_depth        
   ~cfdm.Data._docstring_method_exclusions    
