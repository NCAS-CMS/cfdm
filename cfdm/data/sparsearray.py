from .numpyarray import NumpyArray


class SparseArray(NumpyArray):
    """An underlying sparse array.

    The sparse array is assumed to have the same API as `scipy` sparse
    arrays.

    .. versionadded:: (cfdm) 1.11.0.0

    """

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
