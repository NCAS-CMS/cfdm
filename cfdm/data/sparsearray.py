from .abstract import Array


class SparseArray(Array):
    """An underlying sparse array.

    The sparse array is assumed to have the same API as `scipy` sparse
    arrays.

    .. versionadded:: (cfdm) 1.11.0.0

    """

    def __init__(self, array=None, source=None, copy=True):
        """**Initialisation**

        :Parameters:

            array: `numpy.ndarray`
                The numpy array.

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(source=source, copy=copy)

        if source is not None:
            try:
                array = source._get_component("array", None)
            except AttributeError:
                array = None

        self._set_component("array", array, copy=False)
        if array is not None:
            self._set_component("dtype", array.dtype, copy=False)
            self._set_component("shape", array.shape, copy=False)

    @property
    def array(self):
        """Return an independent numpy array containing the data.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `sparse_array`

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples**

        >>> isinstance(a.array, numpy.ndarray)
        True

        """
        return self._get_component("array").toarray()

    @property
    def sparse_array(self):
        """Return an independent `scipy` sparse array of the data.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `array`

        :Returns:

                An independent `scipy` sparse array of the data.

        **Examples**

        >>> from scipy.sparse import issparse
        >>> issparse(a.sparse_array)
        True

        """
        return self._get_component("array").copy()

    def to_memory(self):
        """Bring data on disk into memory.

        .. versionadded:: (cfdm) 1.11.0.0

        :Returns:

                Returns the contained sparse array, which is already
                in memory.

        """
        return self
