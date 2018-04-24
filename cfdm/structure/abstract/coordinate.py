import abc

from .propertiesdatabounds import PropertiesDataBounds

# ====================================================================
#
# Generic coordinate object
#
# ====================================================================

class Coordinate(PropertiesDataBounds):
    '''Base class for dimension or auxiliary coordinate constructs of the
CF data model.

    '''
    __metaclass__ = abc.ABCMeta
#--- End: class
