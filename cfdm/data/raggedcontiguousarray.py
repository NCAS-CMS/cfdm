from itertools import accumulate, product

import numpy as np

from .abstract import RaggedArray


class RaggedContiguousArray(RaggedArray):
    """An underlying contiguous ragged array.

    A collection of features stored using a contiguous ragged array
    combines all features along a single dimension (the "sample
    dimension") such that each feature in the collection occupies a
    contiguous block.

    The information needed to uncompress the data is stored in a
    "count variable" that gives the size of each block.

    It is assumed that the compressed dimension is the left-most
    dimension in the compressed array.

    See CF section 9 "Discrete Sampling Geometries".

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        count_variable=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: array_like
                The compressed data.

            shape: `tuple`
                The shape of the uncompressed array.

            count_variable: `Count`
                The count variable required to uncompress the data,
                corresponding to a CF-netCDF count variable.

            {{init source: optional}}

                .. versionadded:: (cfdm) 1.10.0.0

            {{init copy: `bool`, optional}}

                .. versionadded:: (cfdm) 1.10.0.0

            size: `int`
                Deprecated at version 1.10.0.0. Ignored if set.

                Number of elements in the uncompressed array.

            ndim: `int`
                Deprecated at version 1.10.0.0. Ignored if set.

                The number of uncompressed array dimensions.

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            count_variable=count_variable,
            compressed_dimensions={0: (0, 1)},
            source=source,
            copy=copy,
        )

    def subarrays(self, shapes=-1):
        """Return descriptors for every subarray.

        Theses descriptors are used during subarray decompression.

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

        An original 2-d array with shape (3, 5) comprising 3
        timeSeries features has been compressed as a contiguous ragged
        array. The features have counts of 2, 5, and 4 elements.

        >>> u_indices, u_shapes, c_indices, locations = x.subarrays()
        >>> for i in u_indices:
        ...    print(i)
        ...
        (slice(0, 1, None), slice(0, 5, None))
        (slice(1, 2, None), slice(0, 5, None))
        (slice(2, 3, None), slice(0, 5, None))
        >>> for i in u_shapes
        ...    print(i)
        ...
        (1, 5)
        (1, 5)
        (1, 5)
        >>> for i in c_indices:
        ...    print(i)
        ...
        (slice(0, 2, None),)
        (slice(2, 7, None),)
        (slice(7, 11, None),)
        >>> for i in locations:
        ...    print(i)
        ...
        (0, 0)
        (1, 0)
        (2, 0)

        """
        d1, u_dims = self.compressed_dimensions().popitem()

        shapes = self.subarray_shapes(shapes)

        # The indices of the uncompressed array that correspond to
        # each subarray, the shape of each uncompressed subarray, and
        # the location of each subarray
        locations, u_shapes, u_indices = self._uncompressed_descriptors(
            u_dims, shapes
        )

        # The indices of the compressed array that correspond to each
        # subarray
        c_indices = []
        for d, size in enumerate(self.source().shape):
            if d == d1:
                count = np.array(self.get_count()).tolist()
                c = tuple(accumulate([0] + count))
            else:
                if d < d1:
                    c = shapes[d]
                else:
                    c = shapes[d + 1]

                c = tuple(accumulate((0,) + c))

            c_indices.append([slice(i, j) for i, j in zip(c[:-1], c[1:])])

        return (
            product(*u_indices),
            product(*u_shapes),
            product(*c_indices),
            product(*locations),
        )
