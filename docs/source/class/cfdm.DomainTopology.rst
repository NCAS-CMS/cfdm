.. currentmodule:: cfdm
.. default-role:: obj

.. _cfdm-DomainTopology:

cfdm.DomainTopology
===================

----

.. autoclass:: cfdm.DomainTopology
   :no-members:
   :no-inherited-members:

Inspection
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.DomainTopology.dump
   ~cfdm.DomainTopology.identity  
   ~cfdm.DomainTopology.identities

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.DomainTopology.construct_type
   
Properties
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.DomainTopology.del_property
   ~cfdm.DomainTopology.get_property
   ~cfdm.DomainTopology.has_property
   ~cfdm.DomainTopology.set_property
   ~cfdm.DomainTopology.properties
   ~cfdm.DomainTopology.clear_properties
   ~cfdm.DomainTopology.del_properties
   ~cfdm.DomainTopology.set_properties

Topology
--------
 
.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.DomainTopology.del_cell
   ~cfdm.DomainTopology.get_cell
   ~cfdm.DomainTopology.has_cell
   ~cfdm.DomainTopology.set_cell
   ~cfdm.DomainTopology.normalise

Data
----

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.DomainTopology.apply_masking
   ~cfdm.DomainTopology.del_data
   ~cfdm.DomainTopology.get_data
   ~cfdm.DomainTopology.has_data
   ~cfdm.DomainTopology.set_data
   ~cfdm.DomainTopology.insert_dimension
   ~cfdm.DomainTopology.persist
   ~cfdm.DomainTopology.squeeze
   ~cfdm.DomainTopology.transpose
   
.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.DomainTopology.array
   ~cfdm.DomainTopology.data
   ~cfdm.DomainTopology.datetime_array
   ~cfdm.DomainTopology.dtype
   ~cfdm.DomainTopology.ndim
   ~cfdm.DomainTopology.shape
   ~cfdm.DomainTopology.size

Bounds
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.DomainTopology.has_bounds

Miscellaneous
-------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.DomainTopology.copy
   ~cfdm.DomainTopology.concatenate
   ~cfdm.DomainTopology.creation_commands
   ~cfdm.DomainTopology.equals
   ~cfdm.DomainTopology.uncompress
   ~cfdm.DomainTopology.get_filenames
   ~cfdm.DomainTopology.get_original_filenames
   ~cfdm.DomainTopology.to_memory

Aggregation
-----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.DomainTopology.file_directories
   ~cfdm.DomainTopology.replace_directory

NetCDF
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.DomainTopology.nc_del_variable
   ~cfdm.DomainTopology.nc_get_variable
   ~cfdm.DomainTopology.nc_has_variable
   ~cfdm.DomainTopology.nc_set_variable

Groups
^^^^^^

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.DomainTopology.nc_variable_groups
   ~cfdm.DomainTopology.nc_clear_variable_groups
   ~cfdm.DomainTopology.nc_set_variable_groups

Dataset chunks
^^^^^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.DomainTopology.nc_dataset_chunksizes
   ~cfdm.DomainTopology.nc_set_dataset_chunksizes
   ~cfdm.DomainTopology.nc_clear_dataset_chunksizes

Special
-------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.DomainTopology.__deepcopy__
   ~cfdm.DomainTopology.__getitem__
   ~cfdm.DomainTopology.__repr__
   ~cfdm.DomainTopology.__str__

Docstring substitutions
-----------------------                   
                                          
.. rubric:: Methods                       
                                          
.. autosummary::                          
   :nosignatures:                         
   :toctree: ../method/                   
   :template: method.rst                  
                                          
   ~cfdm.DomainTopology._docstring_special_substitutions
   ~cfdm.DomainTopology._docstring_substitutions        
   ~cfdm.DomainTopology._docstring_package_depth        
   ~cfdm.DomainTopology._docstring_method_exclusions    

Deprecated
----------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.DomainTopology.nc_clear_hdf5_chunksizes
   ~cfdm.DomainTopology.nc_hdf5_chunksizes
   ~cfdm.DomainTopology.nc_set_hdf5_chunksizes
