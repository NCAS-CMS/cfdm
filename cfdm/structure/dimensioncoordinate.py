from collections import abc

from .coordinate import Coordinate


# ====================================================================
#
# DimensionCoordinate object
#
# ====================================================================

class DimensionCoordinate(Coordinate):
    '''A CF dimension coordinate construct.

    '''
    __metaclass__ = abc.ABCMeta
#--- End: class
