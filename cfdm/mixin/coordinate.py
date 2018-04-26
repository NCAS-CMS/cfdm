import abc

from .propertiesdatabounds import PropertiesDataBounds


class Coordinate(PropertiesDataBounds):
    '''Mixin class for dimension or auxiliary coordinate constructs of the
CF data model.

    '''
    __metaclass__ = abc.ABCMeta
    
#--- End: class
