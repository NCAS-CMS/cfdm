import numpy

from . import abstract


class NumpyArray(abstract.Array):
    """A container for a numpy array.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(self, array=None, source=None, copy=True):
        """**Initialisation**

        :Parameters:

            array: `numpy.ndarray`
                The numpy array.

        """
        super().__init__(source=source, copy=copy)

        if source is not None:
            try:
                array = source._get_component("array", None)
            except AttributeError:
                array = None

        self._set_component("array", array, copy=False)

    @property
    def dtype(self):
        """Data-type of the data elements.

        .. versionadded:: (cfdm) 1.7.0

        **Examples**

        >>> a.dtype
        dtype('float64')
        >>> print(type(a.dtype))
        <type 'numpy.dtype'>

        """
        return self._get_component("array").dtype

    @property
    def shape(self):
        """Tuple of array dimension sizes.

        .. versionadded:: (cfdm) 1.7.0

        **Examples**

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

        """
        return self._get_component("array").shape

    @property
    def array(self):
        """Return an independent numpy array containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples**

        >>> n = a.array
        >>> isinstance(n, numpy.ndarray)
        True

        """
        array = self._get_component("array")

        if not array.ndim and numpy.ma.isMA(array):
            # This is because numpy.ma.copy doesn't work for
            # scalar arrays (at the moment, at least)
            ma_array = numpy.ma.empty((), dtype=array.dtype)
            ma_array[...] = array
            array = ma_array
        else:
            array = array.copy()

        return array

    def copy(self):
        """Return a deep copy of the array.

        ``a.copy() is equivalent to ``copy.deepcopy(a)``.

        Copy-on-write is employed. Therefore, after copying, care must be
        taken when making in-place modifications to attributes of either
        the original or the new copy.

        .. versionadded:: (cfdm) 1.8.7.0

        :Returns:

            `{{class}}`
                The deep copy.

        **Examples**

        >>> b = a.copy()

        """
        klass = self.__class__
        new = klass.__new__(klass)
        new.__dict__ = self.__dict__.copy()
        return new
