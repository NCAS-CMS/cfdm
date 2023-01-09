from functools import reduce
from operator import mul

from ...abstract import Container
from ...utils import cached_property


class Array(Container):
    """Abstract base class for a container of an array.

    The form of the array is defined by the initialisation parameters
    of a subclass.

    See `cfdm.core.NumpyArray` for an example implementation.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(self, source=None, copy=True):
        """**Initialisation**

        :Parameters:

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(source=source, copy=copy)

    def __array__(self, *dtype):
        """The numpy array interface.

        .. versionadded:: (cfdm) 1.8.7.0

        :Parameters:

            dtype: optional
                Typecode or data-type to which the array is cast.

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        """
        array = self.array
        if not dtype:
            return array
        else:
            return array.astype(dtype[0], copy=False)

    def __deepcopy__(self, memo):
        """Called by the `copy.deepcopy` function.

        x.__deepcopy__() <==> copy.deepcopy(x)

        Copy-on-write is employed. Therefore, after copying, care must be
        taken when making in-place modifications to attributes of either
        the original or the new copy.

        .. versionadded:: (cfdm) 1.7.0

        **Examples**

        >>> import copy
        >>> y = copy.deepcopy(x)

        """
        return self.copy()

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
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.array"
        )  # pragma: no cover

    @property
    def dtype(self):
        """Data-type of the array.

        .. versionadded:: (cfdm) 1.7.0

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.dtype"
        )  # pragma: no cover

    @cached_property
    def ndim(self):
        """Number of array dimensions.

        .. versionadded:: (cfdm) 1.7.0

        """
        return len(self.shape)

    @property
    def shape(self):
        """Shape of the array.

        .. versionadded:: (cfdm) 1.7.0

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.shape"
        )  # pragma: no cover

    @property
    def size(self):
        """Number of elements in the array.

        .. versionadded:: (cfdm) 1.7.0

        """
        return reduce(mul, self.shape, 1)

    def copy(self):
        """Return a deep copy of the array.

        ``a.copy() is equivalent to ``copy.deepcopy(a)``.

        Copy-on-write is employed. Therefore, after copying, care must be
        taken when making in-place modifications to attributes of either
        the original or the new copy.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `{{class}}`
                The deep copy.

        **Examples**

        >>> b = a.copy()

        """
        return type(self)(source=self, copy=True)
