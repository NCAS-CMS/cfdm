.. currentmodule:: cfdm
.. default-role:: obj

.. _cfdm-AuxiliaryCoordinate:

cfdm.AuxiliaryCoordinate
========================

----

.. autoclass:: cfdm.AuxiliaryCoordinate
   :no-members:
   :no-inherited-members:

Inspection
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.dump
   ~cfdm.AuxiliaryCoordinate.identity
   ~cfdm.AuxiliaryCoordinate.identities

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.AuxiliaryCoordinate.construct_type

Properties
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.del_property
   ~cfdm.AuxiliaryCoordinate.get_property
   ~cfdm.AuxiliaryCoordinate.has_property
   ~cfdm.AuxiliaryCoordinate.set_property
   ~cfdm.AuxiliaryCoordinate.properties
   ~cfdm.AuxiliaryCoordinate.clear_properties
   ~cfdm.AuxiliaryCoordinate.del_properties
   ~cfdm.AuxiliaryCoordinate.set_properties

Data
----

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.apply_masking
   ~cfdm.AuxiliaryCoordinate.del_data
   ~cfdm.AuxiliaryCoordinate.get_data
   ~cfdm.AuxiliaryCoordinate.has_data
   ~cfdm.AuxiliaryCoordinate.set_data
   ~cfdm.AuxiliaryCoordinate.insert_dimension
   ~cfdm.AuxiliaryCoordinate.persist
   ~cfdm.AuxiliaryCoordinate.squeeze
   ~cfdm.AuxiliaryCoordinate.transpose

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.AuxiliaryCoordinate.array
   ~cfdm.AuxiliaryCoordinate.data
   ~cfdm.AuxiliaryCoordinate.datetime_array
   ~cfdm.AuxiliaryCoordinate.dtype
   ~cfdm.AuxiliaryCoordinate.ndim
   ~cfdm.AuxiliaryCoordinate.shape
   ~cfdm.AuxiliaryCoordinate.size

Quantization
^^^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.get_quantization
   ~cfdm.AuxiliaryCoordinate.get_quantize_on_write

Bounds
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.del_bounds
   ~cfdm.AuxiliaryCoordinate.get_bounds
   ~cfdm.AuxiliaryCoordinate.has_bounds
   ~cfdm.AuxiliaryCoordinate.set_bounds
   ~cfdm.AuxiliaryCoordinate.get_bounds_data
   
.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.AuxiliaryCoordinate.bounds

Geometries
^^^^^^^^^^

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.del_geometry
   ~cfdm.AuxiliaryCoordinate.get_geometry
   ~cfdm.AuxiliaryCoordinate.has_geometry
   ~cfdm.AuxiliaryCoordinate.set_geometry
   ~cfdm.AuxiliaryCoordinate.del_interior_ring
   ~cfdm.AuxiliaryCoordinate.get_interior_ring
   ~cfdm.AuxiliaryCoordinate.has_interior_ring
   ~cfdm.AuxiliaryCoordinate.set_interior_ring
   ~cfdm.AuxiliaryCoordinate.del_node_count
   ~cfdm.AuxiliaryCoordinate.get_node_count
   ~cfdm.AuxiliaryCoordinate.has_node_count
   ~cfdm.AuxiliaryCoordinate.set_node_count
   ~cfdm.AuxiliaryCoordinate.del_part_node_count
   ~cfdm.AuxiliaryCoordinate.get_part_node_count
   ~cfdm.AuxiliaryCoordinate.has_part_node_count
   ~cfdm.AuxiliaryCoordinate.set_part_node_count
   
.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.AuxiliaryCoordinate.interior_ring

Climatology
^^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.del_climatology
   ~cfdm.AuxiliaryCoordinate.get_climatology
   ~cfdm.AuxiliaryCoordinate.is_climatology
   ~cfdm.AuxiliaryCoordinate.set_climatology

Miscellaneous
-------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst	     

   ~cfdm.AuxiliaryCoordinate.copy
   ~cfdm.AuxiliaryCoordinate.concatenate
   ~cfdm.AuxiliaryCoordinate.creation_commands
   ~cfdm.AuxiliaryCoordinate.equals
   ~cfdm.AuxiliaryCoordinate.uncompress
   ~cfdm.AuxiliaryCoordinate.get_filenames
   ~cfdm.AuxiliaryCoordinate.get_original_filenames
   ~cfdm.AuxiliaryCoordinate.to_memory

Aggregation
-----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.AuxiliaryCoordinate.file_directories
   ~cfdm.AuxiliaryCoordinate.replace_directory

NetCDF
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.nc_del_variable
   ~cfdm.AuxiliaryCoordinate.nc_get_variable
   ~cfdm.AuxiliaryCoordinate.nc_has_variable
   ~cfdm.AuxiliaryCoordinate.nc_set_variable
   ~cfdm.AuxiliaryCoordinate.nc_del_node_coordinate_variable
   ~cfdm.AuxiliaryCoordinate.nc_get_node_coordinate_variable
   ~cfdm.AuxiliaryCoordinate.nc_has_node_coordinate_variable
   ~cfdm.AuxiliaryCoordinate.nc_set_node_coordinate_variable

Groups
^^^^^^

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.nc_variable_groups
   ~cfdm.AuxiliaryCoordinate.nc_clear_variable_groups
   ~cfdm.AuxiliaryCoordinate.nc_set_variable_groups
   ~cfdm.AuxiliaryCoordinate.nc_clear_node_coordinate_variable_groups
   ~cfdm.AuxiliaryCoordinate.nc_node_coordinate_variable_groups
   ~cfdm.AuxiliaryCoordinate.nc_set_node_coordinate_variable_groups

Dataset chunks
^^^^^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.nc_dataset_chunksizes
   ~cfdm.AuxiliaryCoordinate.nc_set_dataset_chunksizes
   ~cfdm.AuxiliaryCoordinate.nc_clear_dataset_chunksizes

Special
-------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.__deepcopy__
   ~cfdm.AuxiliaryCoordinate.__getitem__
   ~cfdm.AuxiliaryCoordinate.__repr__
   ~cfdm.AuxiliaryCoordinate.__str__

Docstring substitutions
-----------------------                   
                                          
.. rubric:: Methods                       
                                          
.. autosummary::                          
   :nosignatures:                         
   :toctree: ../method/                   
   :template: method.rst                  
                                          
   ~cfdm.AuxiliaryCoordinate._docstring_special_substitutions
   ~cfdm.AuxiliaryCoordinate._docstring_substitutions        
   ~cfdm.AuxiliaryCoordinate._docstring_package_depth        
   ~cfdm.AuxiliaryCoordinate._docstring_method_exclusions

Deprecated
----------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.AuxiliaryCoordinate.nc_clear_hdf5_chunksizes
   ~cfdm.AuxiliaryCoordinate.nc_hdf5_chunksizes
   ~cfdm.AuxiliaryCoordinate.nc_set_hdf5_chunksizes
