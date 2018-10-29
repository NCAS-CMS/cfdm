.. currentmodule:: cfdm
.. default-role:: obj

.. _class:

Classes of the **cfdm** package
===============================

Field construct class
--------------------

This class represents the field construct of the CF data model. It
inherits directly from `cfdm.core.Field`, its `cfdm.core` counterpart.

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.Field	              

Metadata construct classes
--------------------------

Each of these classes represent the metadata constructs of the CF data
model. They inherit directly from their `cfdm.core` counterparts. For
example, `cfdm.AuxiliaryCoordinate` inherits
`cfdm.core.AuxiliaryCoordinate`.

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
subset of construct classes. They inherit directly from their
`cfdm.core` counterparts. For example, `cfdm.Bounds` inherits
`cfdm.core.Bounds`.

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

These classes inherit, directly or indirectly, from their `cfdm.core`
counterparts. For example, `cfdm.Data` inherits `cfdm.core.Data`.

Abstract classes
----------------

These classes inherit, directly or indirectly, from their `cfdm.core`
counterparts. For example `cfdm.data.abstract.Array` inherits
`cfdm.core.data.abstract.Array`.

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.data.abstract.Array
   cfdm.data.abstract.CompressedArray		

These classes inherit, directly or indirectly, from their `cfdm.core`
counterparts. For example `cfdm.data.abstract.Array` inherits
`cfdm.core.data.abstract.Array`.

Mixin classes
-------------

Each of these classes provides functionality, that is missing from the
`cfdm.core` package, to read and write netCDF datasets and to modify
constructs in memory. All construct and construct component classes
inherit from one or more of these mixin classes.

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
   cfdm.mixin.NetCDFVariable
   cfdm.mixin.Parameters
   cfdm.mixin.ParametersDomainAncillaries
   cfdm.mixin.Properties
   cfdm.mixin.PropertiesData
   cfdm.mixin.PropertiesDataBounds

   
