import time
s = time.time()
print('0 data/abstract/array')
from ... import core

from ...mixin import Container

print('  8 data/abstract/array', time.time()-s); s = time.time()

from .. import mixin
print('  9 data/abstract/array', time.time()-s); s = time.time()


class Array(mixin.ArrayMixin, Container, core.Array):
    """Abstract base class for a container of an underlying array.

    The form of the array is defined by the initialisation parameters
    of a subclass.

    .. versionadded:: (cfdm) 1.7.0

    """
