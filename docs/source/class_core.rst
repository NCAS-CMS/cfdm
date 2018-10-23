.. currentmodule:: cfdm
.. default-role:: obj

.. _class:

Classes of the :mod:`cfdm` module
=================================

Field class
-------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.Field	              

Field component classes
-----------------------

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

Miscellaneous classes
---------------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.CellExtent
   cfdm.CoordinateConversion
   cfdm.Datum
   cfdm.Domain

Data classes
------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.Data
   cfdm.NetCDFArray
   cfdm.NumpyArray..

Mixin classes
-------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.mixin.ConstructAccess
   cfdm.mixin.Container
   cfdm.mixin.Coordinate
   cfdm.mixin.Parameters
   cfdm.mixin.ParametersDomainAncillaries
   cfdm.mixin.Properties
   cfdm.mixin.PropertiesData
   cfdm.mixin.PropertiesDataBounds
  
Abstract classes
----------------

.. autosummary::
   :nosignatures:
   :toctree: classes/

   cfdm.data.abstract.Array
   cfdm.data.abstract.CompressedArray		
  
.. inheritance-diagram:: cfdm.Field cfdm.DomainAxis
   :top-classes: cfdm.structure.abstract.Container, cfdm.mixin.Container
                         

.. graphviz::

   digraph foo {
      "bar" -> "baz";
   }
