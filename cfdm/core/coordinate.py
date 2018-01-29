from collections import abc

from .boundedvariable import BoundedVariableMixin

import ..structure


# ====================================================================
#
# Coordinate object
#
# ====================================================================

class Coordinate(structural.Coordinate, BoundedVariableMixin):
    '''Base class for a CF dimension or auxiliary coordinate construct.

    '''
    __metaclass__ = abc.ABCMeta
#--- End: class
