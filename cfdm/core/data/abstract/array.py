from ... import abstract


class Array(abstract.Container):
    """Abstract base class for a container of an array.

    The form of the array is defined by the initialisation parameters
    of a subclass.

    See `cfdm.core.NumpyArray` for an example implementation.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(self, **kwargs):
        """**Initialisation**

        :Parameters:

            kwargs: *optional*
                Named parameters and their values that define the
                array.

        """
        super().__init__()

        for key, value in kwargs.items():
            self._set_component(key, value, copy=False)

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

        **Examples:**

        >>> import copy
        >>> y = copy.deepcopy(x)

        """
        return self.copy()

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def dtype(self):
        """Data-type of the data elements.

        .. versionadded:: (cfdm) 1.7.0

        **Examples:**

        >>> a.dtype
        dtype('float64')
        >>> print(type(a.dtype))
        <type 'numpy.dtype'>

        """
        raise NotImplementedError()  # pragma: no cover

    @property
    def ndim(self):
        """Number of array dimensions.

        .. versionadded:: (cfdm) 1.7.0

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

        """
        raise NotImplementedError(
            "Subclasses of cfdm.core.AbstractArray must implement 'ndim'"
        )  # pragma: no cover

    @property
    def shape(self):
        """Tuple of array dimension sizes.

        .. versionadded:: (cfdm) 1.7.0

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

        """
        raise NotImplementedError(
            "Subclasses of cfdm.core.AbstractArray must implement 'shape'"
        )  # pragma: no cover

    @property
    def size(self):
        """Number of elements in the array.

        .. versionadded:: (cfdm) 1.7.0

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

        """
        raise NotImplementedError()  # pragma: no cover

    @property
    def array(self):
        """Return an independent numpy array containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples:**

        >>> n = a.array
        >>> isinstance(n, numpy.ndarray)
        True

        """
        raise NotImplementedError()  # pragma: no cover

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
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

        **Examples:**

        >>> b = a.copy()

        """
        klass = self.__class__
        new = klass.__new__(klass)
        new.__dict__ = self.__dict__.copy()
        return new
