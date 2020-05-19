from builtins import super

import numpy

from . import abstract


class NumpyArray(abstract.Array):
    '''A container for a numpy array.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, array=None):
        '''**Initialization**

    :Parameters:

        array: `numpy.ndarray`
            The numpy array.

        '''
        super().__init__(array=array)

    @property
    def dtype(self):
        '''Data-type of the data elements.

    .. versionadded:: 1.7.0

    **Examples:**

    >>> a.dtype
    dtype('float64')
    >>> print(type(a.dtype))
    <type 'numpy.dtype'>

        '''
        return self._get_component('array').dtype

    @property
    def ndim(self):
        '''Number of array dimensions

    .. versionadded:: 1.7.0

    **Examples:**

    >>> a.shape
    (73, 96)
    >>> a.ndim
    2
    >>> a.size
    7008

    >>> a.shape
    (1, 1, 1)
    >>> a.ndim
    3
    >>> a.size
    1

    >>> a.shape
    ()
    >>> a.ndim
    0
    >>> a.size
    1

        '''
        return self._get_component('array').ndim

    @property
    def shape(self):
        '''Tuple of array dimension sizes.

    .. versionadded:: 1.7.0

    **Examples:**

    >>> a.shape
    (73, 96)
    >>> a.ndim
    2
    >>> a.size
    7008

    >>> a.shape
    (1, 1, 1)
    >>> a.ndim
    3
    >>> a.size
    1

    >>> a.shape
    ()
    >>> a.ndim
    0
    >>> a.size
    1

    '''
        return self._get_component('array').shape

    @property
    def size(self):
        '''Number of elements in the array.

    .. versionadded:: 1.7.0

    **Examples:**

    >>> a.shape
    (73, 96)
    >>> a.size
    7008
    >>> a.ndim
    2

    >>> a.shape
    (1, 1, 1)
    >>> a.ndim
    3
    >>> a.size
    1

    >>> a.shape
    ()
    >>> a.ndim
    0
    >>> a.size
    1
        '''
        return self._get_component('array').size

    @property
    def array(self):
        '''Return an independent numpy array containing the data.

    .. versionadded:: 1.7.0

    :Returns:

        `numpy.ndarray`
            An independent numpy array of the data.

    **Examples:**

    >>> n = a.array
    >>> isinstance(n, numpy.ndarray)
    True

        '''
        array = self._get_component('array')

        if not array.ndim and numpy.ma.isMA(array):
            # This is because numpy.ma.copy doesn't work for
            # scalar arrays (at the moment, at least)
            ma_array = numpy.ma.empty((), dtype=array.dtype)
            ma_array[...] = array
            array = ma_array
        else:
            array = array.copy()

        return array

# --- End: class
