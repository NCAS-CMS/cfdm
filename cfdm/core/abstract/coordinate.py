import abc

from . import PropertiesDataBounds


class Coordinate(PropertiesDataBounds, metaclass=abc.ABCMeta):
    '''Abstract base class for dimension and auxiliary coordinate
    constructs of the CF data model.

    .. versionadded:: 1.7.0

    '''
# --- End: class
