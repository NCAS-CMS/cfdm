from future.utils import with_metaclass

import abc

from .propertiesdatabounds import PropertiesDataBounds


class Coordinate(with_metaclass(abc.ABCMeta, PropertiesDataBounds)):
    '''Mixin class for dimension or auxiliary coordinate constructs of the
CF data model.

    '''
    
#--- End: class
