from .array import Array


class DeprecationError(Exception):
    """Deprecation error."""

    pass


class CompressedArray(Array):
    """Mixin class for a container of an underlying compressed array.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        compressed_dimension=None,
        compressed_dimensions=(),
        compression_type=None,
        one_to_one=False,
        **kwargs
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: subclass of `Array`
                The compressed array.

            shape: `tuple`
                The uncompressed array dimension sizes.

            size: `int`
                Number of elements in the uncompressed array.

            ndim: `int`
                The number of uncompressed array dimensions

            compressed_dimension: `int`
                The position of the compressed dimension in the compressed
                array.

            compressed_dimensions: sequence of `int`
                The positions of the compressed dimensions in the
                compressed array.

                *Parameter example:*
                  ``compressed_dimensions=[1]``

                *Parameter example:*
                  ``compressed_dimensions=(0, 2)``

                .. versionadded:: (cfdm) 1.9.TODO.0

            compression_type: `str`
                The type of compression.

            one_to_one: `bool`, optional
                If True then each compressed dimension corresponds to
                a single uncompressed dimension in the same position.

                .. versionadded:: (cfdm) 1.9.TODO.0

            kwargs: optional
                Further named parameters and their values needed to define
                the compressed array.

            compressed_dimension: deprecated at version 1.9.TODO.0
                Use the *compressed_dimensions* parameter instead.

        """
        if compressed_dimension is not None:
            raise DeprecationError(
                "The 'compressed_dimension' keyword was deprecated at "
                "version 1.9.TODO.0 and will be removed at a later version. "
                "Use the 'compressed_dimensions' keyword instead."
            )

        super().__init__(
            shape=shape,
            size=size,
            ndim=ndim,
            compressed_dimension=compressed_dimension,
            compressed_dimensions=tuple(compressed_dimensions),
            compression_type=compression_type,
            one_to_one=one_to_one,
            **kwargs
        )

        self._set_compressed_Array(compressed_array, copy=False)

    def _get_compressed_Array(self, default=ValueError()):
        """Return the compressed array.

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the array
                has not been set. If set to an `Exception` instance then
                it will be raised instead.

        :Returns:

                The compressed Array instance.

        **Examples:**

        >>> c = d._get_compressed_Array()

        """
        return self._get_component("compressed_Array", default)

    def _set_compressed_Array(self, array, copy=True):
        """Set the compressed array.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            array: subclass of `cfdm.data.Array`
                The compressed data to be inserted.

        :Returns:

            `None`

        **Examples:**

        >>> d._set_compressed_Array(a)

        """
        if copy:
            array = array.copy()

        self._set_component("compressed_Array", array, copy=False)

    @property
    def array(self):
        """Returns a numpy array containing the uncompressed data.

        :Returns:

            `numpy.ndarray`
                The uncompressed array.

        **Examples:**

        >>> n = a.array
        >>> isinstance(n, numpy.ndarray)
        True

        """
        return self[...]

    @property
    def dtype(self):
        """Data-type of the data elements.

        **Examples:**

        >>> a.dtype
        dtype('float64')
        >>> print(type(a.dtype))
        <type 'numpy.dtype'>

        """
        return self._get_compressed_Array().dtype

    @property
    def ndim(self):
        """The number of dimensions of the uncompressed data.

        **Examples:**

        >>> d.shape
        (73, 96)
        >>> d.ndim
        2
        >>> d.size
        7008

        >>> d.shape
        (1, 1, 1)
        >>> d.ndim
        3
        >>> d.size
        1

        >>> d.shape
        ()
        >>> d.ndim
        0
        >>> d.size
        1

        """
        return self._get_component("ndim")

    @property
    def shape(self):
        """Shape of the uncompressed data.

        **Examples:**

        >>> d.shape
        (73, 96)
        >>> d.ndim
        2
        >>> d.size
        7008

        >>> d.shape
        (1, 1, 1)
        >>> d.ndim
        3
        >>> d.size
        1

        >>> d.shape
        ()
        >>> d.ndim
        0
        >>> d.size
        1

        """
        return self._get_component("shape")

    @property
    def size(self):
        """Number of elements in the uncompressed data.

        **Examples:**

        >>> d.shape
        (73, 96)
        >>> d.size
        7008
        >>> d.ndim
        2

        >>> d.shape
        (1, 1, 1)
        >>> d.ndim
        3
        >>> d.size
        1

        >>> d.shape
        ()
        >>> d.ndim
        0
        >>> d.size
        1

        """
        return self._get_component("size")

    @property
    def compressed_array(self):
        """Returns an independent numpy array with the compressed data.

        :Returns:

            `numpy.ndarray`
                The compressed array.

        **Examples:**

        >>> n = a.compressed_array

        >>> isinstance(n, numpy.ndarray)
        True

        """
        ca = self._get_compressed_Array(None)
        if ca is None:
            raise ValueError("There is no underlying compressed array")

        return ca.array

    def get_compressed_axes(self):
        """Return axes that are compressed in the underlying array.

        :Returns:

            `list`
                The compressed axes described by their integer
                positions in the uncompressed array.

        **Examples:**

        >>> c.ndim
        4
        >>> c.compressed_array.ndim
        3
        >>> c.compressed_axes()
        [1, 2]

        """
        compressed_dimension = self._get_component("compressed_dimensions")[0]
        compressed_ndim = self._get_compressed_Array().ndim

        return list(
            range(
                compressed_dimension,
                self.ndim - (compressed_ndim - compressed_dimension - 1),
            )
        )

    def get_compressed_dimension(self, default=ValueError()):
        """Returns the compressed dimension's position in the array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_compressed_axes`, `get_compression_type`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                underlying array is not compressed. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `int`
                The position of the compressed dimension in the compressed
                array. If the underlying is not compressed then *default*
                is returned, if provided.

        **Examples:**

        >>> i = d.get_compressed_dimension()

        """
        return self._get_component("compressed_dimensions")[0]

    def compressed_dimensions(self):
        """Mapping of compressed to uncompressed dimensions.

        Returns the positions of dimensions in the compressed data
        that represent one or more dimensions in the uncompressed
        data, and maps these to the corresponding dimension positions
        in the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO..0

        .. seealso:: `get_compressed_axes`, `get_compression_type`

        :Returns:

            `dict`

        """
        compressed_dims = self._get_component("compressed_dimensions")

        if self._get_component("one_to_one", False):
            # Each compressed dimension corresponds to a single
            # uncompressed dimension in the same position
            return {pos: [pos] for pos in compressed_dims}

        compressed_ndim = self._get_compressed_Array().ndim
        ndim = self.ndim

        return {
            pos: list(range(pos, ndim - (compressed_ndim - pos - 1)))
            for pos in compressed_dims
        }

    def to_memory(self):
        """Bring an array on disk into memory and retain it there.

        There is no change to an array that is already in memory.

        :Returns:

            `{{class}}`
                The array that is stored in memory.

        **Examples:**

        >>> b = a.to_memory()

        """
        self._get_compressed_Array(self._get_compressed_Array().to_memory())
        return self

    def source(self, default=ValueError()):
        """Return the underlying array object.

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the array
                has not been set. If set to an `Exception` instance then
                it will be raised instead.

        :Returns:

            subclass of `Array`
                The underlying array object.

        **Examples:**

        >>> array
        <RaggedContiguousArray(2, 4): >
        >>> array.source()
        <Data(5): [280.0, ..., 279.5]>

        """
        return self._get_compressed_Array(default=default)
