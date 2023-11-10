.. currentmodule:: cfdm
.. default-role:: obj

.. _cfdm-Domain:

cfdm.Domain
===========

----

.. autoclass:: cfdm.Domain
   :no-members:
   :no-inherited-members:

.. rubric:: Methods

Inspection
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Domain.dump
   ~cfdm.Domain.identity  
   ~cfdm.Domain.identities

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Domain.construct_type

Metadata constructs
-------------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Domain.construct
   ~cfdm.Domain.construct_key
   ~cfdm.Domain.construct_item
   ~cfdm.Domain.del_construct
   ~cfdm.Domain.get_construct
   ~cfdm.Domain.has_construct
   ~cfdm.Domain.set_construct
   ~cfdm.Domain.del_data_axes
   ~cfdm.Domain.get_data_axes
   ~cfdm.Domain.has_data_axes
   ~cfdm.Domain.set_data_axes
   ~cfdm.Domain.domain_axis_key
   ~cfdm.Domain.auxiliary_coordinate
   ~cfdm.Domain.auxiliary_coordinates
   ~cfdm.Domain.cell_connectivity
   ~cfdm.Domain.cell_connectivities
   ~cfdm.Domain.cell_measure
   ~cfdm.Domain.cell_measures
   ~cfdm.Domain.coordinate
   ~cfdm.Domain.coordinates
   ~cfdm.Domain.coordinate_reference
   ~cfdm.Domain.coordinate_references
   ~cfdm.Domain.dimension_coordinate
   ~cfdm.Domain.dimension_coordinates
   ~cfdm.Domain.domain_ancillary
   ~cfdm.Domain.domain_ancillaries
   ~cfdm.Domain.domain_axis
   ~cfdm.Domain.domain_axes
   ~cfdm.Domain.domain_topology
   ~cfdm.Domain.domain_topologies
   ~cfdm.Domain.climatological_time_axes

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Domain.constructs

Properties
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Domain.del_property
   ~cfdm.Domain.get_property
   ~cfdm.Domain.has_property
   ~cfdm.Domain.set_property
   ~cfdm.Domain.properties
   ~cfdm.Domain.clear_properties
   ~cfdm.Domain.del_properties
   ~cfdm.Domain.set_properties

Miscellaneous
-------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Domain.apply_masking
   ~cfdm.Domain.climatological_time_axes
   ~cfdm.Domain.copy
   ~cfdm.Domain.creation_commands
   ~cfdm.Domain.equals
   ~cfdm.Domain.fromconstructs
   ~cfdm.Domain.get_filenames
   ~cfdm.Domain.has_bounds
   ~cfdm.Domain.has_data
   ~cfdm.Domain.has_geometry
   ~cfdm.Domain.apply_masking   
   ~cfdm.Domain.get_original_filenames
   ~cfdm.Domain.uncompress

NetCDF
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Domain.nc_del_variable
   ~cfdm.Domain.nc_get_variable
   ~cfdm.Domain.nc_has_variable
   ~cfdm.Domain.nc_set_variable 
   ~cfdm.Domain.nc_global_attributes
   ~cfdm.Domain.nc_clear_global_attributes
   ~cfdm.Domain.nc_set_global_attribute
   ~cfdm.Domain.nc_set_global_attributes
   
Groups
^^^^^^

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Domain.nc_variable_groups
   ~cfdm.Domain.nc_set_variable_groups
   ~cfdm.Domain.nc_clear_variable_groups
   ~cfdm.Domain.nc_group_attributes
   ~cfdm.Domain.nc_clear_group_attributes
   ~cfdm.Domain.nc_set_group_attribute
   ~cfdm.Domain.nc_set_group_attributes
  
Geometries
^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.Domain.nc_del_geometry_variable
   ~cfdm.Domain.nc_get_geometry_variable
   ~cfdm.Domain.nc_has_geometry_variable
   ~cfdm.Domain.nc_set_geometry_variable 
   ~cfdm.Domain.nc_geometry_variable_groups
   ~cfdm.Domain.nc_set_geometry_variable_groups
   ~cfdm.Domain.nc_clear_geometry_variable_groups

Components
^^^^^^^^^^

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst
	      
   ~cfdm.Domain.nc_del_component_variable
   ~cfdm.Domain.nc_set_component_variable
   ~cfdm.Domain.nc_set_component_variable_groups
   ~cfdm.Domain.nc_clear_component_variable_groups      
   ~cfdm.Domain.nc_del_component_dimension
   ~cfdm.Domain.nc_set_component_dimension
   ~cfdm.Domain.nc_set_component_dimension_groups
   ~cfdm.Domain.nc_clear_component_dimension_groups
   ~cfdm.Domain.nc_del_component_sample_dimension
   ~cfdm.Domain.nc_set_component_sample_dimension   
   ~cfdm.Domain.nc_set_component_sample_dimension_groups
   ~cfdm.Domain.nc_clear_component_sample_dimension_groups

Dataset compliance
^^^^^^^^^^^^^^^^^^

.. rubric:: Methods


.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Domain.dataset_compliance
   
Special
-------

.. rubric:: Methods

.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Domain.__deepcopy__
   ~cfdm.Domain.__repr__
   ~cfdm.Domain.__str__

Docstring substitutions
-----------------------                   
                                          
.. rubric:: Methods                       
                                          
.. autosummary::                          
   :nosignatures:                         
   :toctree: ../method/                   
   :template: method.rst                  
                                          
   ~cfdm.Domain._docstring_special_substitutions
   ~cfdm.Domain._docstring_substitutions        
   ~cfdm.Domain._docstring_package_depth        
   ~cfdm.Domain._docstring_method_exclusions    
