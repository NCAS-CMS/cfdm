.. currentmodule:: cfdm
.. default-role:: obj

.. _class_extended:

**cfdm classes**
================

----

Version |release| for version |version| of the CF conventions.

.. note:: See also the :ref:`class_core`.


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
   cfdm.CellConnectivity
   cfdm.CellMeasure
   cfdm.CellMethod
   cfdm.CoordinateReference
   cfdm.DimensionCoordinate
   cfdm.DomainAncillary
   cfdm.DomainAxis
   cfdm.DomainTopology
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


Array classes
-------------

Classes that support the creation and storage of arrays.

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.Array
   cfdm.XnetcdfArray
   cfdm.AggregatedArray
   cfdm.FullArray
   cfdm.NumpyArray
   cfdm.SparseArray


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
   cfdm.RaggedArray
   cfdm.RaggedSubarray
   cfdm.RaggedContiguousArray
   cfdm.RaggedIndexedArray
   cfdm.RaggedIndexedContiguousArray
   cfdm.CompressedArray
   cfdm.Quantization
   cfdm.BiLinearSubarray
   cfdm.BiQuadraticLatitudeLongitudeSubarray
   cfdm.GatheredSubarray
   cfdm.InterpolationSubarray
   cfdm.LinearSubarray
   cfdm.QuadraticLatitudeLongitudeSubarray
   cfdm.QuadraticSubarray
   cfdm.Subarray
   cfdm.SubsampledArray
   cfdm.SubsampledSubarray

UGRID related classes
---------------------

Classes that support the creation and storage of UGRID related arrays.

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.BoundsFromNodesArray
   cfdm.BoundsFromNodesSubarray
   cfdm.CellConnectivityArray
   cfdm.CellConnectivitySubarray
   cfdm.PointTopologyArray

Abstract base classes
---------------------

Abstract base classes that provide the basis for constructs and
construct components.

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.NodeCountProperties
   cfdm.PartNodeCountProperties
   cfdm.Container

Implementation classes
----------------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.Implementation
   cfdm.CFDMImplementation


Miscellaneous classes
---------------------

.. autosummary::
   :nosignatures:
   :toctree: class/

   cfdm.Constant
   cfdm.Configuration
   cfdm.InterpolationParameter
   cfdm.TiePointIndex
   cfdm.Units
