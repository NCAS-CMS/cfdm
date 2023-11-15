from itertools import accumulate
from numbers import Number

from ..subarray import RaggedSubarray
from .compressedarray import CompressedArray


class RaggedArray(CompressedArray):
    """An underlying ragged array.

    See CF section 9 "Discrete Sampling Geometries"

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def __new__(cls, *args, **kwargs):
        """Store subarray classes.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        instance = super().__new__(cls)

        instance._Subarray = {
            "ragged contiguous": RaggedSubarray,
            "ragged indexed": RaggedSubarray,
            "ragged indexed contiguous": RaggedSubarray,
        }

        return instance

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        compressed_dimensions=None,
        count_variable=None,
        index_variable=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: array_like
                The compressed data.

            shape: `tuple`
                The shape of the uncompressed array.

            compressed_dimensions: `dict`
                Mapping of dimensions of the compressed array to their
                corresponding dimensions in the uncompressed
                array. Compressed array dimensions that are not
                compressed must be omitted from the mapping.

                *Parameter example:*
                  ``{0: (0, 1)}``

                *Parameter example:*
                  ``{0: (0, 1, 2)}``

            count_variable: `Count`, optional
                A count variable for uncompressing the data,
                corresponding to a CF-netCDF count variable, if
                required by the decompression method.

            index_variable: `Index`, optional
                An index variable for uncompressing the data,
                corresponding to a CF-netCDF count variable, if
                required by the decompression method.

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        if count_variable is not None:
            if index_variable is not None:
                compression_type = "ragged indexed contiguous"
            else:
                compression_type = "ragged contiguous"
        elif index_variable is not None:
            compression_type = "ragged indexed"
        else:
            compression_type = None

        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            compressed_dimensions=compressed_dimensions,
            compression_type=compression_type,
            source=source,
            copy=copy,
        )

        if source is not None:
            try:
                index_variable = source.get_index(None)
            except AttributeError:
                index_variable = None

            try:
                count_variable = source.get_count(None)
            except AttributeError:
                count_variable = None

        if index_variable is not None:
            self._set_component("index_variable", index_variable, copy=copy)

        if count_variable is not None:
            self._set_component("count_variable", count_variable, copy=copy)

    def _uncompressed_descriptors(self, u_dims, shapes):
        """Create descriptors of uncompressed subarrays.

        Returns the location of each subarray, the indices of the
        uncompressed array that correspond to each subarray, and the
        shape of each uncompressed subarray.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `subarray`

        :Parameters:

            u_dims: sequence of `int`
                The positions of the uncompressed dimensions that have
                been compressed.

            shapes: sequence of `tuple`
                The subarray shapes along each uncompressed
                dimension. It is assumed that they have been output by
                `subarray_shapes`.

        :Returns:

            3-`tuple` of `list`
                The location, shape, and index descriptors.

        """
        locations = []
        u_shapes = []
        u_indices = []
        for d, (size, c) in enumerate(zip(self.shape, shapes)):
            if d in u_dims[:-1]:
                locations.append([i for i in range(len(c))])
                u_shapes.append(c)
                u_indices.append([slice(i, i + 1) for i in range(len(c))])
            elif d == u_dims[-1]:
                locations.append((0,))
                u_shapes.append((size,))
                u_indices.append((slice(0, size),))
            else:
                locations.append([i for i in range(len(c))])
                u_shapes.append(c)

                c = tuple(accumulate((0,) + c))
                u_indices.append([slice(i, j) for i, j in zip(c[:-1], c[1:])])

        return locations, u_shapes, u_indices

    @property
    def dtype(self):
        """Data-type of the uncompressed data."""
        return self.source().dtype

    def get_count(self, default=ValueError()):
        """Return the count variable for the compressed array.

        .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `Count`

        """
        out = self._get_component("count_variable", None)
        if out is None:
            if default is None:
                return

            return self._default(
                default, f"{self.__class__.__name__!r} has no count variable"
            )

        return out

    def get_index(self, default=ValueError()):
        """Return the index variable for the compressed array.

        .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `Index`

        """
        out = self._get_component("index_variable", None)
        if out is None:
            if default is None:
                return

            return self._default(
                default, f"{self.__class__.__name__!r} has no index variable"
            )

        return out

    def subarray_shapes(self, shapes):
        """Create the subarray shapes along each uncompressed dimension.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `subarray`

        :Parameters:

            {{subarray_shapes chunks: `int`, sequence, `dict`, or `str`, optional}}

        :Returns:

            `list`
                The subarray sizes along each uncompressed dimension.

        **Examples**

        >>> a.shape
        (2, 3, 4)
        >>> a.compressed_dimensions()
        {0: (0, 1)}
        >>> a.subarray_shapes(-1)
        [(1, 1), (3,), (4,)]
        >>> a.subarray_shapes("auto")
        [(1, 1), (3,), "auto"]
        >>> a.subarray_shapes(2)
        [(1, 1), (3,), 2]
        >>> a.subarray_shapes("60B")
        [(1, 1), (3,), "60B"]
        >>> a.subarray_shapes((None, None, 2))
        [(1, 1), (3,), 2]
        >>> a.subarray_shapes((None, None, (1, 3)))
        [(1, 1), (3,), (1, 3)]
        >>> a.subarray_shapes((None, None, "auto"))
        [(1, 1), (3,), "auto"]
        >>> a.subarray_shapes((None, None, "60B"))
        [(1, 1), (3,), "60B"]
        >>> a.subarray_shapes({2: (1, 3)})
        [(1, 1), (3,), (1, 3)]

        >>> import dask.array as da
        >>> da.core.normalize_chunks(
        ...   a.subarray_shapes("auto"), shape=a.shape, dtype=a.dtype
        ... )
        [(1, 1), (3,), (4,)]
        >>> da.core.normalize_chunks(
        ...   a.subarray_shapes(2, shape=a.shape, dtype=a.dtype
        ... )
        [(1, 1), (3,), (2, 2)]

        >>> a.shape
        (2, 3, 3, 4)
        >>> a.compressed_dimensions()
        {0: (0, 1, 2)}
        >>> a.subarray_shapes(-1)
        [(1, 1), (1, 1, 1), (3,), (4,)]
        >>> a.subarray_shapes("auto")
        [(1, 1), (1, 1, 1), (3,), "auto"]
         >>> a.subarray_shapes(2)
        [(1, 1), (1, 1, 1), (3,), 2]
         >>> a.subarray_shapes("60B")
        [(1, 1), (1, 1, 1), (3,), "60B"]
        >>> a.subarray_shapes((None, None, None, 2))
        [(1, 1), (1, 1, 1), (3,), 2]
        >>> a.subarray_shapes((None, None, None, (1, 3)))
        [(1, 1), (1, 1, 1), (3,), (1, 3)]
        >>> a.subarray_shapes((None, None, None, "auto"))
        [(1, 1), (1, 1, 1), (3,), "auto"]
        >>> a.subarray_shapes((None, None, None, "60B"))
        [(1, 1), (1, 1, 1), (3,), "60B"]
        >>> a.subarray_shapes({3: (1, 3)})
        [(1, 1), (1, 1, 1), (3,), (1, 3)]

        """
        u_dims = self.get_compressed_axes()

        uncompressed_shape = self.shape

        if shapes == -1:
            return [
                (1,) * size if i in u_dims[:-1] else (size,)
                for i, size in enumerate(uncompressed_shape)
            ]

        if isinstance(shapes, (str, Number)):
            shapes = [
                (1,) * size if i in u_dims[:-1] else shapes
                for i, size in enumerate(uncompressed_shape)
            ]
            shapes[u_dims[-1]] = (uncompressed_shape[u_dims[-1]],)
            return shapes

        if isinstance(shapes, dict):
            shapes = [
                shapes[i] if i in shapes else None for i in range(self.ndim)
            ]
        elif len(shapes) != self.ndim:
            raise ValueError(
                f"Wrong number of 'shapes' elements in {shapes}: "
                f"Got {len(shapes)}, expected {self.ndim}"
            )

        # chunks is a sequence
        shapes = list(shapes)
        shapes[u_dims[0] : u_dims[-1]] = [
            (1,) * size for size in uncompressed_shape[u_dims[0] : u_dims[-1]]
        ]
        shapes[u_dims[-1]] = (uncompressed_shape[u_dims[-1]],)
        return shapes

    def to_memory(self):
        """Bring data on disk into memory.

        There is no change to data that is already in memory.

        .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `{{class}}`
                A copy of the array with all of its data in memory.

        """
        a = super().to_memory()

        count = a.get_count(None)
        if count is not None:
            try:
                a._set_component(
                    "count_variable", count.to_memory(), copy=False
                )
            except AttributeError:
                pass

        index = a.get_index(None)
        if index is not None:
            try:
                a._set_component(
                    "index_variable", index.to_memory(), copy=False
                )
            except AttributeError:
                pass

        return a
