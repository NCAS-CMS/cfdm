import abc

from .data import Data

from ..structure import DataUnits as structure_DataUnits

# ====================================================================
#
# Data object
#
# ====================================================================

class DataUnits(structure_DataUnits, Data):
    '''

An N-dimensional data array with units and masked values.

* Contains an N-dimensional array.

* Contains the units of the array elements.

* Supports masked arrays, regardless of whether or not it was
  initialised with a masked array.

    '''
    ___metaclass__ = abc.ABCMeta
#--- End: class

