.. currentmodule:: cfdm
.. default-role:: obj

cfdm.Field
==========

.. autoclass:: cfdm.Field
   :no-members:
   :no-inherited-members:

.. _field_cf_properties:

CF Properties
-------------
 
.. autosummary::
   :toctree: ../generated/
   :template: attribute.rst

   ~cfdm.Field.add_offset
   ~cfdm.Field.calendar
   ~cfdm.Field.cell_methods
   ~cfdm.Field.comment
   ~cfdm.Field.Conventions
   ~cfdm.Field._FillValue
   ~cfdm.Field.flag_masks
   ~cfdm.Field.flag_meanings
   ~cfdm.Field.flag_values
   ~cfdm.Field.history
   ~cfdm.Field.institution
   ~cfdm.Field.leap_month
   ~cfdm.Field.leap_year
   ~cfdm.Field.long_name
   ~cfdm.Field.missing_value
   ~cfdm.Field.month_lengths
   ~cfdm.Field.references
   ~cfdm.Field.scale_factor
   ~cfdm.Field.source
   ~cfdm.Field.standard_error_multiplier
   ~cfdm.Field.standard_name
   ~cfdm.Field.title
   ~cfdm.Field.units
   ~cfdm.Field.valid_max
   ~cfdm.Field.valid_min
   ~cfdm.Field.valid_range

.. rubric:: Setting, retrieving and deleting non-standard (and reserved) CF properties.

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.Field.delprop
   ~cfdm.Field.getprop
   ~cfdm.Field.hasprop
   ~cfdm.Field.properties
   ~cfdm.Field.setprop

.. _field_methods:

Inspection
----------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.Field.__repr__
   ~cfdm.Field.__str__
   ~cfdm.Field.constructs
   ~cfdm.Field.dump
   ~cfdm.Field.files
   ~cfdm.Field.identity
   ~cfdm.Field.match
   ~cfdm.Field.name

Domain axes
-----------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.Field.axes
   ~cfdm.Field.axes_sizes
   ~cfdm.Field.axis
   ~cfdm.Field.axis_name
   ~cfdm.Field.axis_size
   ~cfdm.Field.data_axes
   ~cfdm.Field.insert_axis
   ~cfdm.Field.item_axes
   ~cfdm.Field.items_axes
   ~cfdm.Field.remove_axes
   ~cfdm.Field.remove_axis

Field items
-----------

A field item is a dimension coordinate, auxiliary coordinate, cell
measure, coordinate reference, domain ancillary or field ancillary
object.
   
.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.Field.insert_aux
   ~cfdm.Field.insert_cell_methods
   ~cfdm.Field.insert_dim
   ~cfdm.Field.insert_domain_anc
   ~cfdm.Field.insert_field_anc
   ~cfdm.Field.insert_measure
   ~cfdm.Field.insert_ref
   ~cfdm.Field.item
   ~cfdm.Field.items
   ~cfdm.Field.remove_item
   ~cfdm.Field.remove_items

Subspacing
----------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.Field.__getitem__
 
Data array
----------

.. http://docs.scipy.org/doc/numpy/reference/routines.array-manipulation.html

.. _field_data_array_access:


.. rubric:: Data array access

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: attribute.rst

   ~cfdm.Field.array
   ~cfdm.Field.data
   ~cfdm.Field.datum
   ~cfdm.Field.dtarray
   ~cfdm.Field.dtype
   ~cfdm.Field.hasdata
   ~cfdm.Field.ndim
   ~cfdm.Field.shape
   ~cfdm.Field.size
   ~cfdm.Field.varray


Units
-----

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: attribute.rst

   ~cfdm.Field.calendar
   ~cfdm.Field.units
   ~cfdm.Field.Units

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.Field.override_units
   ~cfdm.Field.override_calendar

Data array mask
---------------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: attribute.rst

   ~cfdm.Field.count
   ~cfdm.Field.hardmask
   ~cfdm.Field.mask

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.Field.fill_value
 
Order and number of dimensions
------------------------------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.Field.expand_dims
   ~cfdm.Field.squeeze
   ~cfdm.Field.transpose
   ~cfdm.Field.unsqueeze

.. rubric:: Changing data array values

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.Field.__setitem__
   ~cfdm.Field.mask_invalid
 
Miscellaneous data array operations
-----------------------------------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: attribute.rst

   ~cfdm.Field.insert_data
   ~cfdm.Field.isscalar
   ~cfdm.Field.remove_data

Comparison
----------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst


   ~cfdm.Field.equals


Miscellaneous
-------------

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: method.rst

   ~cfdm.Field.attributes
   ~cfdm.Field.copy 
   ~cfdm.Field.field
   ~cfdm.Field.HDF_chunks
   ~cfdm.Field.unlimited

.. autosummary::
   :nosignatures:
   :toctree: ../generated/
   :template: attribute.rst

   ~cfdm.Field.Flags
   ~cfdm.Field.hasbounds
   ~cfdm.Field.isfield
   ~cfdm.Field.rank
   ~cfdm.Field.T
   ~cfdm.Field.X
   ~cfdm.Field.Y
   ~cfdm.Field.Z

Special methods
---------------

.. autosummary::
   :nosignatures:
   :toctree: generated/
   :template: method.rst

   ~cfdm.Field.__deepcopy__
