from collections import abc

import .abstract


# ====================================================================
#
# Generic coordinate object
#
# ====================================================================

class Coordinate(abstract.PropertiesDataBounds):
    '''Base class for a CFDM dimension or auxiliary coordinate construct.

    '''
    __metaclass__ = abc.ABCMeta
#--- End: class
