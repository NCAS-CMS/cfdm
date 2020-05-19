from future.utils import with_metaclass

import abc

from . import PropertiesDataBounds


class Coordinate(with_metaclass(abc.ABCMeta, PropertiesDataBounds)):
    '''Abstract base class for dimension and auxiliary coordinate
    constructs of the CF data model.

    .. versionadded:: 1.7.0

    '''
# --- End: class
