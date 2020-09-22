.. currentmodule:: cfdm
.. default-role:: obj

.. _class_core:

**cfdm.core classes**
=====================

----

Version |release| for version |version| of the CF conventions.


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

Constructs class
----------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.core.Constructs

Coordinate component classes
----------------------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.core.Bounds
   cfdm.core.CoordinateConversion
   cfdm.core.Datum
   cfdm.core.InteriorRing

Domain class
------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.core.Domain
   
Data classes
------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.core.Data
   cfdm.core.NumpyArray
   cfdm.core.Array

Abstract base classes
---------------------

Abstract base classes that provide the basis for constructs and
construct components.

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.core.abstract.Container
   cfdm.core.abstract.Properties
   cfdm.core.abstract.PropertiesData
   cfdm.core.abstract.PropertiesDataBounds
   cfdm.core.abstract.Coordinate
   cfdm.core.abstract.Parameters
   cfdm.core.abstract.ParametersDomainAncillaries

Miscallaneous
-------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.core.meta.DocstringRewriteMeta
   
