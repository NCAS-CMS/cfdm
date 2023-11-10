from itertools import accumulate, product
from numbers import Number

import numpy as np

from .abstract import CompressedArray
from .subarray import GatheredSubarray


class DeprecationError(Exception):
    """Deprecation error."""

    pass


class GatheredArray(CompressedArray):
    """An underlying gathered array.

    Compression by gathering combines axes of a multidimensional array
    into a new, discrete axis whilst omitting the missing values and
    thus reducing the number of values that need to be stored.

    The information needed to uncompress the data is stored in a "list
    variable" that gives the indices of the required points.

    See CF section 8.2 "Lossless Compression by Gathering".

    .. versionadded:: (cfdm) 1.7.0

    """

    def __new__(cls, *args, **kwargs):
        """Store subarray classes.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        instance = super().__new__(cls)
        instance._Subarray = {"gathered": GatheredSubarray}
        return instance

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        compressed_dimension=None,
        compressed_dimensions=None,
        list_variable=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: array_like
                The compressed array.

            shape: `tuple`
                The shape of the uncompressed array.

            {{init compressed_dimensions: `dict`}}

                *Parameter example:*
                  ``{2: (2, 3)}``

                .. versionadded:: (cfdm) 1.10.0.0

            list_variable: `List`
                The "list variable" required to uncompress the data,
                identical to the data of a CF-netCDF list variable.

            compressed_dimension: deprecated at version 1.10.0.0
                Use the *compressed_dimensions* parameter instead.

            {{init source: optional}}

                .. versionadded:: (cfdm) 1.10.0.0

            {{init copy: `bool`, optional}}

                .. versionadded:: (cfdm) 1.10.0.0

            size: `int`
                Deprecated at version 1.10.0.0. Ignored if set.

                Number of elements in the uncompressed array.

            ndim: `int`
                Deprecated at version 1.10.0.0. Ignored if set.

                The number of uncompressed array dimensions

        """
        if compressed_dimension is not None:
            raise DeprecationError(
                "The 'compressed_dimension' keyword was deprecated at "
                "version 1.10.0.0. "
                "Use the 'compressed_dimensions' keyword instead."
            )  # pragma: no cover

        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            compressed_dimensions=compressed_dimensions,
            compression_type="gathered",
            source=source,
            copy=copy,
        )

        if source is not None:
            try:
                list_variable = source.get_list(None)
            except AttributeError:
                list_variable = None

        if list_variable is not None:
            self._set_component("list_variable", list_variable, copy=copy)

    def _uncompressed_indices(self):
        """Indices of the uncompressed subarray for the compressed data.

        .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `tuple`
                The indices of the uncompressed subarray for the
                compressed data. Dimensions not compressed by
                gathering will have an index of ``slice(None)``.

        **Examples**

        For an original 3-d array with shape (12, 4, 6) for which the
        last two dimensions have been compressed by gathering with
        list variable indices (1, 2, 5, 6, 13, 15, 16, 22) then:

        >>> for i in x._uncompressed_indices():
        ...     print(i)
        ...
        slice(None, None, None)
        array([0, 0, 0, 1, 2, 2, 2, 3])
        array([1, 2, 5, 0, 1, 3, 4, 4])

        """
        _, u_dims = self.compressed_dimensions().popitem()
        list_variable = np.array(self.get_list())

        u_indices = [slice(None)] * self.ndim

        u_indices[u_dims[0] : u_dims[-1] + 1] = np.unravel_index(
            list_variable, self.shape[u_dims[0] : u_dims[-1] + 1]
        )

        return tuple(u_indices)

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self.source().dtype

    def conformed_data(self):
        """The compressed data and list variable.

        .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `dict`
                The conformed gathered data, with the key ``'data'``;
                and the `tuple` of uncompressed indices with the key
                ``'uncompressed_indices'``.

        """
        out = super().conformed_data()
        out["uncompressed_indices"] = self._uncompressed_indices()
        return out

    def get_list(self, default=ValueError()):
        """Return the list variable for a compressed array.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the list
                variable has not been set.

                {{default Exception}}

        :Returns:

            `List`
                The list variable.

        """
        return self._get_component("list_variable", default=default)

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
        [(2,), (3,), (4,)]
        >>> a.subarray_shapes("auto")
        [(2,), (3,), "auto"]
        >>> a.subarray_shapes(2)
        [(2,), (3,), 2]
        >>> a.subarray_shapes("60B")
        [(2,), (3,), "60B"]
        >>> a.subarray_shapes((None, None, 2))
        [(2,), (3,), 2]
        >>> a.subarray_shapes((None, None, (1, 3)))
        [(2,), (3,), (1, 3)]
        >>> a.subarray_shapes((None, None, "auto"))
        [(2,), (3,), "auto"]
        >>> a.subarray_shapes((None, None, "60B"))
        [(2,), (3,), "60B"]
        >>> a.subarray_shapes({2: (1, 3)})
        [(2,), (3,), (1, 3)]

        >>> import dask.array as da
        >>> da.core.normalize_chunks(
        ...   a.subarray_shapes("auto"), shape=a.shape, dtype=a.dtype
        ... )
        [(2,), (3,), (4,)]
        >>> da.core.normalize_chunks(
        ...   a.subarray_shapes(2, shape=a.shape, dtype=a.dtype
        ... )
        [(2,), (3,), (2, 2)]

        """
        u_dims = self.get_compressed_axes()

        if shapes == -1:
            return [(size,) for size in self.shape]

        if isinstance(shapes, (str, Number)):
            return [
                (size,) if i in u_dims else shapes
                for i, size in enumerate(self.shape)
            ]

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
        return [
            (size,) if i in u_dims else c
            for i, (size, c) in enumerate(zip(self.shape, shapes))
        ]

    def subarrays(self, shapes=-1):
        """Return descriptors for every subarray.

        These descriptors are used during subarray decompression.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            {{subarrays chunks: ``-1`` or sequence, optional}}

        :Returns:

             4-`tuple` of iterators
                Each iterable iterates over a particular descriptor
                from each subarray.

                1. The indices of the uncompressed array that
                   correspond to each subarray.

                2. The shape of each uncompressed subarray.

                3. The indices of the compressed array that correspond
                   to each subarray.

                4. The location of each subarray on the uncompressed
                   dimensions.

        **Examples**

        An original 3-d array with shape (4, 73, 96) has been
        compressed by gathering the dimensions with sizes 73 and 96
        respectively into a single dimension of size 3028.

        >>> u_indices, u_shapes, c_indices, locations = x.subarrays()
        >>> for i in u_indices:
        ...    print(i)
        ...
        (slice(0, 4, None), slice(0, 73, None), slice(0, 96, None))
        >>> for i in u_shapes
        ...    print(i)
        ...
        (4, 73, 96)
        >>> for i in c_indices:
        ...    print(i)
        ...
        (slice(0, 4, None), slice(0, 3028, None))
        >>> for i in locations:
        ...    print(i)
        ...
        (0, 0, 0)

        >>> (
        ...  u_indices, u_shapes, c_indices, locations
        ... )= x.subarrays(shapes="most")
        >>> for i in u_indices:
        ...    print(i)
        ...
        (slice(0, 1, None), slice(0, 73, None), slice(0, 96, None))
        (slice(1, 2, None), slice(0, 73, None), slice(0, 96, None))
        (slice(2, 3, None), slice(0, 73, None), slice(0, 96, None))
        (slice(3, 4, None), slice(0, 73, None), slice(0, 96, None))
        >>> for i in u_shapes
        ...    print(i)
        ...
        (1, 73, 96)
        (1, 73, 96)
        (1, 73, 96)
        (1, 73, 96)
        >>> for i in c_indices:
        ...    print(i)
        ...
        (slice(0, 1, None), slice(0, 3028, None))
        (slice(1, 2, None), slice(0, 3028, None))
        (slice(2, 3, None), slice(0, 3028, None))
        (slice(3, 4, None), slice(0, 3028, None))
        >>> for i in locations:
        ...    print(i)
        ...
        (0, 0, 0)
        (1, 0, 0)
        (2, 0, 0)
        (3, 0, 0)

        >>> (
        ...  u_indices, u_shapes, c_indices, locations
        ... ) = x.subarrays(shapes=((3, 1), None, None))
        >>> for i in u_indices:
        ...    print(i)
        ...
        (slice(0, 3, None), slice(0, 73, None), slice(0, 96, None))
        (slice(3, 4, None), slice(0, 73, None), slice(0, 96, None))
        >>> for i in u_shapes
        ...    print(i)
        ...
        (3, 73, 96)
        (1, 73, 96)
        >>> for i in c_indices:
        ...    print(i)
        ...
        (slice(0, 3, None), slice(0, 3028, None))
        (slice(3, 4, None), slice(0, 3028, None))
        >>> for i in locations:
        ...    print(i)
        ...
        (0, 0, 0)
        (1, 0, 0)

        """
        d1, u_dims = self.compressed_dimensions().popitem()

        shapes = self.subarray_shapes(shapes)

        # The indices of the uncompressed array that correspond to
        # each subarray, the shape of each uncompressed subarray, and
        # the location of each subarray
        locations = []
        u_shapes = []
        u_indices = []
        for d, (size, c) in enumerate(zip(self.shape, shapes)):
            if d in u_dims:
                locations.append((0,))
                u_shapes.append((size,))
                u_indices.append((slice(0, size),))
            else:
                locations.append([i for i in range(len(c))])
                u_shapes.append(c)

                c = tuple(accumulate((0,) + c))
                u_indices.append([slice(i, j) for i, j in zip(c[:-1], c[1:])])

        # The indices of the compressed array that correspond to each
        # subarray
        c_indices = []
        for d, size in enumerate(self.source().shape):
            if d == d1:
                c_indices.append((slice(0, size),))
            else:
                if d < d1:
                    c = shapes[d]
                else:
                    c = shapes[d + len(u_dims) - 1]

                c = tuple(accumulate((0,) + c))
                c_indices.append([slice(i, j) for i, j in zip(c[:-1], c[1:])])

        return (
            product(*u_indices),
            product(*u_shapes),
            product(*c_indices),
            product(*locations),
        )

    def to_memory(self):
        """Bring data on disk into memory.

        There is no change to data that is already in memory.

        .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `{{class}}`
                A copy of the array with all of its data in memory.

        """
        a = super().to_memory()

        list_variable = self.get_list(None)
        if list_variable is not None:
            try:
                a._set_component(
                    "list_variable", list_variable.to_memory(), copy=False
                )
            except AttributeError:
                pass

        return a
