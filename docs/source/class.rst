.. currentmodule:: cfdm
.. default-role:: obj

.. _class_extended:

**Classes** of the **cfdm** package
===================================

Field construct class
--------------------

This class represents the field construct of the CF data model.

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.Field	              

Metadata construct classes
--------------------------

Each of these classes represent the metadata constructs of the CF data
model.

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


Each of these classes represents a particular component found in a
subset of construct classes.

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.Bounds
   cfdm.CoordinateConversion
   cfdm.Data
   cfdm.Datum
   cfdm.Domain
..

The components may be found in construct classes as follows:

======================  ============================================================
Component               Parent constructs
======================  ============================================================
`Bounds`                `AuxiliaryCoordinate`, `DimensionCoordinate`,
                        `DomainAncillary`
`CoordinateConversion`  `CoordinateReference`
`Data`                  `AuxiliaryCoordinate`, `CellMeasure`, `DimensionCoordinate`,
                        `DomainAncillary`, `Field`, `FieldAncillary`
`Datum`                 `CoordinateReference`
`Domain`                `Field`
======================  ============================================================

Construct mixin classes
-----------------------

Each of these classes provides functionality to read and write netCDF
datasets and to modify constructs in memory.

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.mixin.ConstructAccess
   cfdm.mixin.Container
   cfdm.mixin.Coordinate
   cfdm.mixin.NetCDFDataVariable
   cfdm.mixin.NetCDFDimension,
   cfdm.mixin.NetCDFExternal
   cfdm.mixin.NetCDFInstanceDimension,
   cfdm.mixin.NetCDFSampleDimension,
   cfdm.mixin.NetCDFVariable
   cfdm.mixin.Parameters
   cfdm.mixin.ParametersDomainAncillaries
   cfdm.mixin.Properties
   cfdm.mixin.PropertiesData
   cfdm.mixin.PropertiesDataBounds
   
Data classes
------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.Data
   cfdm.NetCDFArray
   cfdm.NumpyArray
   cfdm.data.abstract.Array

Data compression classses
-------------------------

TODO

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.GatheredArray
   cfdm.RaggedContiguousArray
   cfdm.RaggedIndexedArray
   cfdm.RaggedIndexedContiguousArray
   cfdm.Count
   cfdm.Index
   cfdm.List
   cfdm.data.abstract.CompressedArray		
   cfdm.data.mixin.RaggedContiguous
   cfdm.data.mixin.RaggedIndexed

