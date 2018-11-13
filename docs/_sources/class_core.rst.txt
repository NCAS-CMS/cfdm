.. currentmodule:: cfdm
.. default-role:: obj

.. _class_core:

**Classes** of the **cfdm.core** package
========================================

Field construct class
---------------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.core.Field	              

Metadata construct classes
--------------------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.core.AuxiliaryCoordinate
   cfdm.core.CellMeasure
   cfdm.core.CellMethod
   cfdm.core.CoordinateReference
   cfdm.core.DimensionCoordinate
   cfdm.core.DomainAncillary
   cfdm.core.DomainAxis
   cfdm.core.FieldAncillary

Construct component classes
---------------------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.core.Bounds
   cfdm.core.CoordinateConversion
   cfdm.core.Data
   cfdm.core.Datum
   cfdm.core.Domain

Data classes
------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.core.Data
   cfdm.core.NumpyArray
   cfdm.core.Array

Construct abstract base classes
-------------------------------

Abstract base classes that providing the basis for construct classes.

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.core.abstract.Container
   cfdm.core.abstract.Coordinate
   cfdm.core.abstract.Parameters
   cfdm.core.abstract.ParametersDomainAncillaries
   cfdm.core.abstract.Properties
   cfdm.core.abstract.PropertiesData
   cfdm.core.abstract.PropertiesDataBounds
   cfdm.core.data.abstract.Array
