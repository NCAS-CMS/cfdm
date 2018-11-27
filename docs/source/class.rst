.. currentmodule:: cfdm
.. default-role:: obj

.. _class_extended:

**cfdm classes**
================

Version |release| for version |version| of the CF conventions.

----

**Field construct class**
-------------------------

.. autosummary::
   :nosignatures:
   :toctree: class/
		 
   cfdm.Field	              

**Metadata construct classes**
------------------------------

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

**Construct component classes**
-------------------------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.Domain
   cfdm.Bounds
   cfdm.CoordinateConversion
   cfdm.Data
   cfdm.Datum

**Data classes**
----------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.Data
   cfdm.NetCDFArray
   cfdm.NumpyArray
   cfdm.Array

**Data compression classses**
-----------------------------

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

.. **Mixin classes**
   ------------------
   
   Classes that provide functionality that is shared by constructs and
   construct components.
   
   .. autosummary::
      :nosignatures:
      :toctree: class/
   
      cfdm.mixin.ConstructAccess
      cfdm.mixin.Container
      cfdm.mixin.Coordinate
      cfdm.mixin.NetCDFDataVariable
      cfdm.mixin.NetCDFDimension
      cfdm.mixin.NetCDFExternal
      cfdm.mixin.NetCDFInstanceDimension,
      cfdm.mixin.NetCDFSampleDimension,
      cfdm.mixin.NetCDFVariable
      cfdm.mixin.Parameters
      cfdm.mixin.ParametersDomainAncillaries
      cfdm.mixin.Properties
      cfdm.mixin.PropertiesData
      cfdm.mixin.PropertiesDataBounds
   
