.. currentmodule:: cfdm
.. default-role:: obj

cfdm.List
=========

----

.. autoclass:: cfdm.List
   :no-members:
   :no-inherited-members:

Inspection
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.List.dump
   ~cfdm.List.identity  
   ~cfdm.List.identities

Properties
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.List.del_property
   ~cfdm.List.get_property
   ~cfdm.List.has_property
   ~cfdm.List.set_property
   ~cfdm.List.properties
   ~cfdm.List.clear_properties
   ~cfdm.List.del_properties
   ~cfdm.List.set_properties

Data
----

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.List.apply_masking
   ~cfdm.List.del_data
   ~cfdm.List.get_data
   ~cfdm.List.has_data
   ~cfdm.List.set_data   
   ~cfdm.List.insert_dimension
   ~cfdm.List.persist
   ~cfdm.List.squeeze
   ~cfdm.List.transpose
   
.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.List.array
   ~cfdm.List.data
   ~cfdm.List.datetime_array
   ~cfdm.List.dtype
   ~cfdm.List.ndim    
   ~cfdm.List.shape
   ~cfdm.List.size    

Quantization
^^^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.List.get_quantization
   ~cfdm.List.get_quantize_on_write

Miscellaneous
-------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.List.copy
   ~cfdm.List.concatenate
   ~cfdm.List.creation_commands
   ~cfdm.List.equals
   ~cfdm.List.get_filenames
   ~cfdm.List.get_original_filenames
   ~cfdm.List.has_bounds
   ~cfdm.List.uncompress
   ~cfdm.List.to_memory

Aggregation
-----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.List.file_directories
   ~cfdm.List.replace_directory

NetCDF
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.List.nc_del_variable
   ~cfdm.List.nc_get_variable
   ~cfdm.List.nc_has_variable
   ~cfdm.List.nc_set_variable 
   ~cfdm.List.nc_clear_dataset_chunksizes
   ~cfdm.List.nc_dataset_chunksizes
   ~cfdm.List.nc_set_dataset_chunksizes

Groups
^^^^^^

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.List.nc_variable_groups
   ~cfdm.List.nc_clear_variable_groups
   ~cfdm.List.nc_set_variable_groups
   
Special
-------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.List.__deepcopy__
   ~cfdm.List.__getitem__
   ~cfdm.List.__repr__
   ~cfdm.List.__str__

Docstring substitutions
-----------------------                   
                                          
.. rubric:: Methods                       
                                          
.. autosummary::                          
   :nosignatures:                         
   :toctree: ../method/                   
   :template: method.rst                  
                                          
   ~cfdm.List._docstring_special_substitutions
   ~cfdm.List._docstring_substitutions        
   ~cfdm.List._docstring_package_depth        
   ~cfdm.List._docstring_method_exclusions    

Deprecated
----------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.List.nc_clear_hdf5_chunksizes
   ~cfdm.List.nc_hdf5_chunksizes
   ~cfdm.List.nc_set_hdf5_chunksizes
