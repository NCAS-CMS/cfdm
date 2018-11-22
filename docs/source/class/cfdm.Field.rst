.. currentmodule:: cfdm
.. default-role:: obj

cfdm.Field
==========

.. autoclass:: cfdm.Field
   :no-members:
   :no-inherited-members:

Inspection
----------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.auxiliary_coordinates
   ~cfdm.Field.cell_measures
   ~cfdm.Field.cell_methods
   ~cfdm.Field.coordinates
   ~cfdm.Field.coordinate_references
   ~cfdm.Field.constructs
   ~cfdm.Field.construct_axes
   ~cfdm.Field.dimension_coordinates
   ~cfdm.Field.domain_ancillaries
   ~cfdm.Field.domain_axes
   ~cfdm.Field.dump
   ~cfdm.Field.field_ancillaries
   ~cfdm.Field.get_array
   ~cfdm.Field.get_construct
   ~cfdm.Field.get_data
   ~cfdm.Field.get_domain
   ~cfdm.Field.has_data
   ~cfdm.Field.get_property
   ~cfdm.Field.has_construct
   ~cfdm.Field.has_property
   ~cfdm.Field.name
   ~cfdm.Field.properties

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Field.construct_type
   ~cfdm.Field.data
   ~cfdm.Field.domain

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
   ~cfdm.Field.properties
   ~cfdm.Field.set_property

Data
----

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.del_data
   ~cfdm.Field.del_data_axes
   ~cfdm.Field.get_array
   ~cfdm.Field.get_data
   ~cfdm.Field.get_data_axes
   ~cfdm.Field.has_data
   ~cfdm.Field.set_data
   ~cfdm.Field.set_data_axes   
   
.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Field.data

Metadata constructs
-------------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.constructs
   ~cfdm.Field.construct_axes
   ~cfdm.Field.del_construct
   ~cfdm.Field.get_construct
   ~cfdm.Field.has_construct
   ~cfdm.Field.set_construct
   ~cfdm.Field.set_construct_axes
   ~cfdm.Field.auxiliary_coordinates
   ~cfdm.Field.cell_measures
   ~cfdm.Field.cell_methods
   ~cfdm.Field.coordinates
   ~cfdm.Field.coordinate_references
   ~cfdm.Field.dimension_coordinates
   ~cfdm.Field.domain_ancillaries
   ~cfdm.Field.domain_axes
   ~cfdm.Field.field_ancillaries
 
Modification
------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.del_construct
   ~cfdm.Field.del_data
   ~cfdm.Field.del_data_axes
   ~cfdm.Field.del_property
   ~cfdm.Field.expand_dims
   ~cfdm.Field.properties
   ~cfdm.Field.set_construct
   ~cfdm.Field.set_construct_axes
   ~cfdm.Field.set_data
   ~cfdm.Field.set_data_axes
   ~cfdm.Field.set_property
   ~cfdm.Field.squeeze
   ~cfdm.Field.transpose
 
Miscellaneous
-------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.copy
   ~cfdm.Field.equals

NetCDF
------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~Field.nc_del_variable
   ~Field.nc_get_variable
   ~Field.nc_has_variable
   ~Field.nc_set_variable 
   ~Field.nc_global_attributes
   ~Field.nc_unlimited_dimensions

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
