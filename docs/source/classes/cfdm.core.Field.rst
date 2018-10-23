.. currentmodule:: cfdm
.. default-role:: obj

cfdm.core.Field
===============

.. autoclass:: cfdm.core.Field
   :no-members:
   :no-inherited-members:

Properties
----------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.core.Field.del_property
   ~cfdm.core.Field.get_property
   ~cfdm.core.Field.has_property
   ~cfdm.core.Field.properties
   ~cfdm.core.Field.set_property

.. _field_methods:

Inspection
----------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.core.Field.__repr__
   ~cfdm.core.Field.__str__
   ~cfdm.core.Field.constructs
   ~cfdm.core.Field.dump
   ~cfdm.core.Field.files
   ~cfdm.core.Field.identity
   ~cfdm.core.Field.match
   ~cfdm.core.Field.name

Domain axes
-----------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.core.Field.axes
   ~cfdm.core.Field.axes_sizes
   ~cfdm.core.Field.axis
   ~cfdm.core.Field.axis_name
   ~cfdm.core.Field.axis_size
   ~cfdm.core.Field.data_axes
   ~cfdm.core.Field.insert_axis
   ~cfdm.core.Field.item_axes
   ~cfdm.core.Field.items_axes
   ~cfdm.core.Field.remove_axes
   ~cfdm.core.Field.remove_axis

Field items
-----------

A field item is a dimension coordinate, auxiliary coordinate, cell
measure, coordinate reference, domain ancillary or field ancillary
object.
   
.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.core.Field.insert_aux
   ~cfdm.core.Field.insert_cell_methods
   ~cfdm.core.Field.insert_dim
   ~cfdm.core.Field.insert_domain_anc
   ~cfdm.core.Field.insert_field_anc
   ~cfdm.core.Field.insert_measure
   ~cfdm.core.Field.insert_ref
   ~cfdm.core.Field.item
   ~cfdm.core.Field.items
   ~cfdm.core.Field.remove_item
   ~cfdm.core.Field.remove_items

Subspacing
----------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.core.Field.__getitem__
 
Data array
----------

.. http://docs.scipy.org/doc/numpy/reference/routines.array-manipulation.html

.. _field_data_array_access:


.. rubric:: Data array access

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: attribute.rst

   ~cfdm.core.Field.array
   ~cfdm.core.Field.data
   ~cfdm.core.Field.datum
   ~cfdm.core.Field.dtarray
   ~cfdm.core.Field.dtype
   ~cfdm.core.Field.hasdata
   ~cfdm.core.Field.ndim
   ~cfdm.core.Field.shape
   ~cfdm.core.Field.size
   ~cfdm.core.Field.varray


Units
-----

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: attribute.rst

   ~cfdm.core.Field.calendar
   ~cfdm.core.Field.units
   ~cfdm.core.Field.Units

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.core.Field.override_units
   ~cfdm.core.Field.override_calendar

Data array mask
---------------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: attribute.rst

   ~cfdm.core.Field.count
   ~cfdm.core.Field.hardmask
   ~cfdm.core.Field.mask

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.core.Field.fill_value
 
Order and number of dimensions
------------------------------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.core.Field.expand_dims
   ~cfdm.core.Field.squeeze
   ~cfdm.core.Field.transpose
   ~cfdm.core.Field.unsqueeze

.. rubric:: Changing data array values

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.core.Field.__setitem__
   ~cfdm.core.Field.mask_invalid
 
Miscellaneous data array operations
-----------------------------------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: attribute.rst

   ~cfdm.core.Field.insert_data
   ~cfdm.core.Field.isscalar
   ~cfdm.core.Field.remove_data

Comparison
----------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst


   ~cfdm.core.Field.equals

NetCDF methods
--------------


.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst


   ~cfdm.core.Field.nc_del_variable
   ~cfdm.core.Field.nc_get_variable
   ~cfdm.core.Field.nc_has_variable
   ~cfdm.core.Field.nc_set_variable

Miscellaneous
-------------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.core.Field.attributes
   ~cfdm.core.Field.copy 
   ~cfdm.core.Field.field
   ~cfdm.core.Field.HDF_chunks
   ~cfdm.core.Field.unlimited

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: attribute.rst

   ~cfdm.core.Field.Flags
   ~cfdm.core.Field.hasbounds
   ~cfdm.core.Field.isfield
   ~cfdm.core.Field.rank
   ~cfdm.core.Field.T
   ~cfdm.core.Field.X
   ~cfdm.core.Field.Y
   ~cfdm.core.Field.Z

Special methods
---------------

.. autosummary::
   :nosignatures:
   :toctree: generated/
   :template: method.rst

   ~cfdm.core.Field.__deepcopy__
