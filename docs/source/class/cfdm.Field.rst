.. currentmodule:: cfdm
.. default-role:: obj

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
   ~cfdm.Field.set_properties

.. _Field-Data:

Data
----

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.del_data
   ~cfdm.Field.get_data
   ~cfdm.Field.has_data
   ~cfdm.Field.set_data
   ~cfdm.Field.del_data_axes
   ~cfdm.Field.get_data_axes
   ~cfdm.Field.set_data_axes
   ~cfdm.Field.insert_dimension
   ~cfdm.Field.squeeze
   ~cfdm.Field.transpose
   
.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Field.data

.. _Field-Metadata-constructs:   
   
Metadata constructs
-------------------

.. rubric:: Methods
	    
.. autosummary::
   :nosignatures:
   :toctree: ../method/
   :template: method.rst

   ~cfdm.Field.del_construct
   ~cfdm.Field.get_construct
   ~cfdm.Field.has_construct
   ~cfdm.Field.set_construct
   ~cfdm.Field.del_data_axes
   ~cfdm.Field.get_data_axes
   ~cfdm.Field.has_data_axes
   ~cfdm.Field.set_data_axes

.. rubric:: Attributes
   
.. autosummary::
   :nosignatures:
   :toctree: ../attribute/
   :template: attribute.rst

   ~cfdm.Field.constructs
   ~cfdm.Field.auxiliary_coordinates
   ~cfdm.Field.cell_measures
   ~cfdm.Field.cell_methods
   ~cfdm.Field.coordinates
   ~cfdm.Field.coordinate_references
   ~cfdm.Field.dimension_coordinates
   ~cfdm.Field.domain_ancillaries
   ~cfdm.Field.domain_axes
   ~cfdm.Field.field_ancillaries

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

   ~cfdm.Field.copy
   ~cfdm.Field.equals
   ~cfdm.Field.convert

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
   ~cfdm.Field.nc_unlimited_dimensions
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
