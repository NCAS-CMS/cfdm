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

Metadata constructs
-------------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Domain.construct
   ~cfdm.Domain.construct_key
   ~cfdm.Domain.del_construct
   ~cfdm.Domain.get_construct
   ~cfdm.Domain.has_construct
   ~cfdm.Domain.set_construct
   ~cfdm.Domain.del_data_axes
   ~cfdm.Domain.get_data_axes
   ~cfdm.Domain.has_data_axes
   ~cfdm.Domain.set_data_axes
   ~cfdm.Domain.domain_axis_key

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Domain.constructs
   ~cfdm.Domain.auxiliary_coordinates
   ~cfdm.Domain.cell_measures
   ~cfdm.Domain.coordinates
   ~cfdm.Domain.coordinate_references
   ~cfdm.Domain.dimension_coordinates
   ~cfdm.Domain.domain_ancillaries
   ~cfdm.Domain.domain_axes

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
   ~cfdm.Domain.set_properties

Miscellaneous
-------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Domain.copy
   ~cfdm.Domain.equals
   ~cfdm.Domain.fromconstructs

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
   
Groups
^^^^^^

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Domain.nc_variable_groups
   ~cfdm.Domain.nc_clear_variable_groups
   ~cfdm.Domain.nc_set_variable_groups

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
