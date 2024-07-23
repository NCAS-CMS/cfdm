.. currentmodule:: cfdm
.. default-role:: obj

.. _class_extended:

**cfdm classes**
================

----

Version |release| for version |version| of the CF conventions.


Field construct class
---------------------

.. autosummary::
   :nosignatures:
   :toctree: class/
		 
   cfdm.Field

Domain construct class
----------------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.Domain

Metadata construct classes
--------------------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.AuxiliaryCoordinate
   cfdm.CellMeasure
   cfdm.CellMethod
   cfdm.CoordinateReference
   cfdm.DimensionCoordinate
   cfdm.DomainAncillary
   cfdm.DomainAxis
   cfdm.FieldAncillary
  
Constructs class
----------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.Constructs

Coordinate component classes
----------------------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.Bounds
   cfdm.CoordinateConversion
   cfdm.Datum
   cfdm.InteriorRing

Data classes
------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.Data
   cfdm.NetCDF4Array
   cfdm.H5netcdfArray
   cfdm.NumpyArray
   cfdm.Array

Data compression classes
------------------------

Classes that support the creation and storage of compressed arrays.

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.Count
   cfdm.Index
   cfdm.List
   cfdm.GatheredArray
   cfdm.RaggedContiguousArray
   cfdm.RaggedIndexedArray
   cfdm.RaggedIndexedContiguousArray
   cfdm.CompressedArray


Miscellaneous classes
---------------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.Constant
   cfdm.Configuration

