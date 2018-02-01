from collections import abc

import .mixin

import ..structure


# ====================================================================
#
# Coordinate object
#
# ====================================================================

class Coordinate(structural.Coordinate, mixin.PropertiesDataBounds)
    '''Base class for a CF dimension or auxiliary coordinate construct.

    '''
    __metaclass__ = abc.ABCMeta
#--- End: class
