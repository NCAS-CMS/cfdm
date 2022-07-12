from ... import core
from ...mixin import Container
from .. import mixin


class Array(mixin.ArrayMixin, Container, core.Array):
    """Abstract base class for a container of an underlying array.

    The form of the array is defined by the initialisation parameters
    of a subclass.

    .. versionadded:: (cfdm) 1.7.0

    """
