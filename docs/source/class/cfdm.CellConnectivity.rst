.. currentmodule:: cfdm
.. default-role:: obj

.. _cfdm-CellConnectivity:

cfdm.CellConnectivity
=====================

----

.. autoclass:: cfdm.CellConnectivity
   :no-members:
   :no-inherited-members:

Inspection
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.dump
   ~cfdm.CellConnectivity.identity  
   ~cfdm.CellConnectivity.identities

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.CellConnectivity.construct_type

Properties
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.del_property
   ~cfdm.CellConnectivity.get_property
   ~cfdm.CellConnectivity.has_property
   ~cfdm.CellConnectivity.set_property
   ~cfdm.CellConnectivity.properties
   ~cfdm.CellConnectivity.clear_properties
   ~cfdm.CellConnectivity.del_properties
   ~cfdm.CellConnectivity.set_properties

Topology
--------
 
.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.del_connectivity
   ~cfdm.CellConnectivity.get_connectivity
   ~cfdm.CellConnectivity.has_connectivity
   ~cfdm.CellConnectivity.set_connectivity
   ~cfdm.CellConnectivity.normalise

Data
----

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.apply_masking
   ~cfdm.CellConnectivity.del_data
   ~cfdm.CellConnectivity.get_data
   ~cfdm.CellConnectivity.has_data
   ~cfdm.CellConnectivity.set_data
   ~cfdm.CellConnectivity.insert_dimension
   ~cfdm.CellConnectivity.persist
   ~cfdm.CellConnectivity.squeeze
   ~cfdm.CellConnectivity.transpose
   
.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.CellConnectivity.array
   ~cfdm.CellConnectivity.data
   ~cfdm.CellConnectivity.datetime_array
   ~cfdm.CellConnectivity.dtype
   ~cfdm.CellConnectivity.ndim
   ~cfdm.CellConnectivity.shape
   ~cfdm.CellConnectivity.size

Quantization
^^^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.get_quantization
   ~cfdm.CellConnectivity.get_quantize_on_write

Bounds
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.has_bounds

Miscellaneous
-------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.copy
   ~cfdm.CellConnectivity.concatenate
   ~cfdm.CellConnectivity.creation_commands
   ~cfdm.CellConnectivity.equals
   ~cfdm.CellConnectivity.uncompress
   ~cfdm.CellConnectivity.get_filenames
   ~cfdm.CellConnectivity.get_original_filenames
   ~cfdm.CellConnectivity.to_memory

Aggregation
-----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.CellConnectivity.file_directories
   ~cfdm.CellConnectivity.replace_directory

NetCDF
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.nc_del_variable
   ~cfdm.CellConnectivity.nc_get_variable
   ~cfdm.CellConnectivity.nc_has_variable
   ~cfdm.CellConnectivity.nc_set_variable

Groups
^^^^^^

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.nc_variable_groups
   ~cfdm.CellConnectivity.nc_clear_variable_groups
   ~cfdm.CellConnectivity.nc_set_variable_groups

Dataset chunks
^^^^^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.nc_dataset_chunksizes
   ~cfdm.CellConnectivity.nc_set_dataset_chunksizes
   ~cfdm.CellConnectivity.nc_clear_dataset_chunksizes

Special
-------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.__deepcopy__
   ~cfdm.CellConnectivity.__getitem__
   ~cfdm.CellConnectivity.__repr__
   ~cfdm.CellConnectivity.__str__

Docstring substitutions
-----------------------                   
                                          
.. rubric:: Methods                       
                                          
.. autosummary::                          
   :nosignatures:                         
   :toctree: ../method/                   
   :template: method.rst                  
                                          
   ~cfdm.CellConnectivity._docstring_special_substitutions
   ~cfdm.CellConnectivity._docstring_substitutions        
   ~cfdm.CellConnectivity._docstring_package_depth        
   ~cfdm.CellConnectivity._docstring_method_exclusions    

Deprecated
----------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.CellConnectivity.nc_clear_hdf5_chunksizes
   ~cfdm.CellConnectivity.nc_hdf5_chunksizes
   ~cfdm.CellConnectivity.nc_set_hdf5_chunksizes
