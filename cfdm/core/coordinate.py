import abc

import mixin

from ..structure import Coordinate as structure_Coordinate

# ====================================================================
#
# Coordinate object
#
# ====================================================================

class Coordinate(mixin.PropertiesDataBounds, structure_Coordinate):
    '''Base class for a CF dimension or auxiliary coordinate construct.

    '''
    __metaclass__ = abc.ABCMeta
    
#--- End: class
