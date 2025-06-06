.. currentmodule:: cfdm
.. default-role:: obj

.. _cfdm-FieldAncillary:

cfdm.FieldAncillary
===================

----

.. autoclass:: cfdm.FieldAncillary
   :no-members:
   :no-inherited-members:

Inspection
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.FieldAncillary.dump
   ~cfdm.FieldAncillary.identity  
   ~cfdm.FieldAncillary.identities
   
.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.FieldAncillary.construct_type

Properties
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.FieldAncillary.del_property
   ~cfdm.FieldAncillary.get_property
   ~cfdm.FieldAncillary.has_property
   ~cfdm.FieldAncillary.set_property
   ~cfdm.FieldAncillary.properties
   ~cfdm.FieldAncillary.clear_properties
   ~cfdm.FieldAncillary.del_properties
   ~cfdm.FieldAncillary.set_properties

Data
----

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.FieldAncillary.apply_masking
   ~cfdm.FieldAncillary.del_data
   ~cfdm.FieldAncillary.get_data
   ~cfdm.FieldAncillary.has_data
   ~cfdm.FieldAncillary.set_data
   ~cfdm.FieldAncillary.insert_dimension
   ~cfdm.FieldAncillary.persist
   ~cfdm.FieldAncillary.squeeze
   ~cfdm.FieldAncillary.transpose

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.FieldAncillary.array
   ~cfdm.FieldAncillary.data
   ~cfdm.FieldAncillary.datetime_array
   ~cfdm.FieldAncillary.dtype
   ~cfdm.FieldAncillary.ndim
   ~cfdm.FieldAncillary.shape
   ~cfdm.FieldAncillary.size

Quantization
^^^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.FieldAncillary.get_quantization
   ~cfdm.FieldAncillary._set_quantization
   ~cfdm.FieldAncillary._del_quantization
   ~cfdm.FieldAncillary.get_quantize_on_write
   ~cfdm.FieldAncillary.set_quantize_on_write
   ~cfdm.FieldAncillary.del_quantize_on_write

Miscellaneous
-------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.FieldAncillary.copy
   ~cfdm.FieldAncillary.concatenate
   ~cfdm.FieldAncillary.creation_commands
   ~cfdm.FieldAncillary.equals
   ~cfdm.FieldAncillary.has_bounds
   ~cfdm.FieldAncillary.uncompress
   ~cfdm.FieldAncillary.get_filenames
   ~cfdm.FieldAncillary.get_original_filenames
   ~cfdm.FieldAncillary.to_memory

Aggregation
-----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.FieldAncillary.file_directories
   ~cfdm.FieldAncillary.replace_directory

NetCDF
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.FieldAncillary.nc_del_variable
   ~cfdm.FieldAncillary.nc_get_variable
   ~cfdm.FieldAncillary.nc_has_variable
   ~cfdm.FieldAncillary.nc_set_variable
   
Dataset chunks
^^^^^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.FieldAncillary.nc_dataset_chunksizes
   ~cfdm.FieldAncillary.nc_set_dataset_chunksizes
   ~cfdm.FieldAncillary.nc_clear_dataset_chunksizes

Groups
^^^^^^

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.FieldAncillary.nc_variable_groups
   ~cfdm.FieldAncillary.nc_clear_variable_groups
   ~cfdm.FieldAncillary.nc_set_variable_groups

Special
-------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.FieldAncillary.__deepcopy__
   ~cfdm.FieldAncillary.__getitem__
   ~cfdm.FieldAncillary.__repr__
   ~cfdm.FieldAncillary.__str__

Docstring substitutions
-----------------------                   
                                          
.. rubric:: Methods                       
                                          
.. autosummary::                          
   :nosignatures:                         
   :toctree: ../method/                   
   :template: method.rst                  
                                          
   ~cfdm.FieldAncillary._docstring_special_substitutions
   ~cfdm.FieldAncillary._docstring_substitutions        
   ~cfdm.FieldAncillary._docstring_package_depth        
   ~cfdm.FieldAncillary._docstring_method_exclusions    

Deprecated
----------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.FieldAncillary.nc_clear_hdf5_chunksizes
   ~cfdm.FieldAncillary.nc_hdf5_chunksizes
   ~cfdm.FieldAncillary.nc_set_hdf5_chunksizes
