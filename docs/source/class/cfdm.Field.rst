.. currentmodule:: cfdm
.. default-role:: obj

.. _cfdm-Field:

cfdm.Field
==========

----

.. autoclass:: cfdm.Field
   :no-members:
   :no-inherited-members:

.. _Field-Inspection:

Inspection
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.dump
   ~cfdm.Field.identity  
   ~cfdm.Field.identities

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Field.construct_type

.. _Field-Properties:

Properties
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.del_property
   ~cfdm.Field.get_property
   ~cfdm.Field.has_property
   ~cfdm.Field.set_property
   ~cfdm.Field.properties
   ~cfdm.Field.clear_properties
   ~cfdm.Field.del_properties
   ~cfdm.Field.set_properties

.. _Field-Data:

Data
----

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.apply_masking
   ~cfdm.Field.del_data
   ~cfdm.Field.get_data
   ~cfdm.Field.has_data
   ~cfdm.Field.set_data
   ~cfdm.Field.del_data_axes
   ~cfdm.Field.get_data_axes
   ~cfdm.Field.has_data_axes
   ~cfdm.Field.set_data_axes
   ~cfdm.Field.insert_dimension
   ~cfdm.Field.squeeze
   ~cfdm.Field.transpose
   
.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Field.array
   ~cfdm.Field.data
   ~cfdm.Field.datetime_array
   ~cfdm.Field.dtype
   ~cfdm.Field.ndim
   ~cfdm.Field.shape
   ~cfdm.Field.size
   
.. _Field-Metadata-constructs:   
   
Metadata constructs
-------------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.construct
   ~cfdm.Field.construct_key
   ~cfdm.Field.construct_item
   ~cfdm.Field.del_construct
   ~cfdm.Field.get_construct
   ~cfdm.Field.has_construct
   ~cfdm.Field.set_construct
   ~cfdm.Field.domain_axis_key
   ~cfdm.Field.auxiliary_coordinate
   ~cfdm.Field.auxiliary_coordinates
   ~cfdm.Field.cell_connectivity
   ~cfdm.Field.cell_connectivities
   ~cfdm.Field.cell_measure
   ~cfdm.Field.cell_measures
   ~cfdm.Field.cell_method
   ~cfdm.Field.cell_methods
   ~cfdm.Field.coordinate
   ~cfdm.Field.coordinates
   ~cfdm.Field.coordinate_reference
   ~cfdm.Field.coordinate_references
   ~cfdm.Field.dimension_coordinate
   ~cfdm.Field.dimension_coordinates
   ~cfdm.Field.domain_ancillary
   ~cfdm.Field.domain_ancillaries
   ~cfdm.Field.domain_axis
   ~cfdm.Field.domain_axes
   ~cfdm.Field.domain_topology
   ~cfdm.Field.domain_topologies
   ~cfdm.Field.field_ancillary
   ~cfdm.Field.field_ancillaries
   ~cfdm.Field.climatological_time_axes
   
.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Field.constructs

.. _Field-Domain:

Domain
------


.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.get_domain

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Field.domain

.. _Field-Miscellaneous:

Miscellaneous
-------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.compress
   ~cfdm.Field.copy
   ~cfdm.Field.creation_commands
   ~cfdm.Field.equals
   ~cfdm.Field.convert
   ~cfdm.Field.has_bounds
   ~cfdm.Field.has_geometry
   ~cfdm.Field.indices
   ~cfdm.Field.uncompress
   ~cfdm.Field.get_filenames
   ~cfdm.Field.get_original_filenames
   ~cfdm.Field.to_memory

.. _Field-NetCDF:
   
NetCDF
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.nc_del_variable
   ~cfdm.Field.nc_get_variable
   ~cfdm.Field.nc_has_variable
   ~cfdm.Field.nc_set_variable 
   ~cfdm.Field.nc_global_attributes
   ~cfdm.Field.nc_clear_global_attributes
   ~cfdm.Field.nc_set_global_attribute
   ~cfdm.Field.nc_set_global_attributes

Groups
^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.Field.nc_variable_groups
   ~cfdm.Field.nc_set_variable_groups
   ~cfdm.Field.nc_clear_variable_groups
   ~cfdm.Field.nc_group_attributes
   ~cfdm.Field.nc_clear_group_attributes
   ~cfdm.Field.nc_set_group_attribute
   ~cfdm.Field.nc_set_group_attributes
  
Geometries
^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.Field.nc_del_geometry_variable
   ~cfdm.Field.nc_get_geometry_variable
   ~cfdm.Field.nc_has_geometry_variable
   ~cfdm.Field.nc_set_geometry_variable 
   ~cfdm.Field.nc_geometry_variable_groups
   ~cfdm.Field.nc_set_geometry_variable_groups
   ~cfdm.Field.nc_clear_geometry_variable_groups

HDF5 chunks
^^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.nc_hdf5_chunksizes
   ~cfdm.Field.nc_set_hdf5_chunksizes
   ~cfdm.Field.nc_clear_hdf5_chunksizes

Components
^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.Field.nc_del_component_variable
   ~cfdm.Field.nc_set_component_variable
   ~cfdm.Field.nc_set_component_variable_groups
   ~cfdm.Field.nc_clear_component_variable_groups      
   ~cfdm.Field.nc_del_component_dimension
   ~cfdm.Field.nc_set_component_dimension
   ~cfdm.Field.nc_set_component_dimension_groups
   ~cfdm.Field.nc_clear_component_dimension_groups
   ~cfdm.Field.nc_del_component_sample_dimension
   ~cfdm.Field.nc_set_component_sample_dimension   
   ~cfdm.Field.nc_set_component_sample_dimension_groups
   ~cfdm.Field.nc_clear_component_sample_dimension_groups

Dataset compliance
^^^^^^^^^^^^^^^^^^

.. rubric:: Methods


.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.dataset_compliance

.. _Field-Special:

Special
-------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.__deepcopy__
   ~cfdm.Field.__getitem__
   ~cfdm.Field.__repr__
   ~cfdm.Field.__str__

Docstring substitutions
-----------------------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
   
   ~cfdm.Field._docstring_special_substitutions
   ~cfdm.Field._docstring_substitutions
   ~cfdm.Field._docstring_package_depth
   ~cfdm.Field._docstring_method_exclusions
