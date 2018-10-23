.. currentmodule:: cfdm
.. default-role:: obj

.. _class:

Classes of the **cfdm** package
===============================

Field construct class
--------------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.Field	              

Metadata construct classes
--------------------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.AuxiliaryCoordinate
   cfdm.CellMeasure
   cfdm.CellMethod
   cfdm.CoordinateReference
   cfdm.DimensionCoordinate
   cfdm.DomainAncillary
   cfdm.DomainAxis
   cfdm.FieldAncillary

Construct component classes
---------------------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.Bounds
   cfdm.CoordinateConversion
   cfdm.Data
   cfdm.Datum
   cfdm.Domain

Data classes
------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.Data
   cfdm.GatheredArray
   cfdm.NetCDFArray
   cfdm.NumpyArray
   cfdm.RaggedContiguousArray
   cfdm.RaggedIndexedArray
   cfdm.RaggedIndexedContiguousArray
  
Abstract classes
----------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.data.abstract.Array
   cfdm.data.abstract.CompressedArray		

Mixin classes
-------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.mixin.ConstructAccess
   cfdm.mixin.Container
   cfdm.mixin.Coordinate
   cfdm.mixin.External
   cfdm.mixin.NetCDFDimension,
   cfdm.mixin.NetCDFInstanceDimension,
   cfdm.mixin.NetCDFSampleDimension,
   cfdm.mixin.NetCDFVariable)
   cfdm.mixin.Parameters
   cfdm.mixin.ParametersDomainAncillaries
   cfdm.mixin.Properties
   cfdm.mixin.PropertiesData
   cfdm.mixin.PropertiesDataBounds
