from future.utils import with_metaclass

import abc

from .. import structure

from .propertiesdatabounds import PropertiesDataBounds


class Coordinate(with_metaclass(
        abc.ABCMeta,
        type('NewBase', (PropertiesDataBounds, structure.abstract.Coordinate), {}))):
    '''Mixin class for dimension or auxiliary coordinate constructs of the
CF data model.

    '''
    
#--- End: class
