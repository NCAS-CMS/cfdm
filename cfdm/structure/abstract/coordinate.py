import abc

from .propertiesdatabounds import PropertiesDataBounds


class Coordinate(PropertiesDataBounds):
    '''Base class for dimension and auxiliary coordinate constructs of the
CF data model.

    '''
    __metaclass__ = abc.ABCMeta
#--- End: class
