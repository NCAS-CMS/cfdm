import abc

from .propertiesdatabounds import PropertiesDataBounds


class Coordinate(PropertiesDataBounds):
    '''Base class for a CF dimension or auxiliary coordinate construct.

    '''
    __metaclass__ = abc.ABCMeta
    
#--- End: class
