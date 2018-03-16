import abc

from .propertiesdatabounds import PropertiesDataBounds

# ====================================================================
#
# Generic coordinate object
#
# ====================================================================

class Coordinate(PropertiesDataBounds):
    '''Base class for a CFDM dimension or auxiliary coordinate construct.

    '''
    __metaclass__ = abc.ABCMeta
#--- End: class
