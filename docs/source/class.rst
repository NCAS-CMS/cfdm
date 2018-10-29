.. currentmodule:: cfdm
.. default-role:: obj

.. _class:

Classes of the **cfdm** package
===============================

Field construct class
--------------------

This class represents the field construct of the CF data model.

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.Field	              

The `cfdm.Field` class inherits directly from its `cfdm.core`
counterpart, `cfdm.core.Field`.

Metadata construct classes
--------------------------

These classes represent the metadata constructs of the CF data  model.

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

These classes inherit directly from their `cfdm.core`
counterparts. For example, `cfdm.AuxiliaryCoordinate` inherits
`cfdm.core.AuxiliaryCoordinate`.


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

These classes inherit directly from their `cfdm.core`
counterparts. For example, `cfdm.Bounds` inherits `cfdm.core.Bounds`.

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

These classes provide the functionality, missing from the `cfdm.core`
package, to read and write netCDF datasets and to modify field
constructs in memory. All construct and construct compomnent classes
also inherit from one or more of these mixin classes.

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

   
