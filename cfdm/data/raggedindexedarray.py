from itertools import accumulate, product

import numpy as np

from .abstract import RaggedArray


class RaggedIndexedArray(RaggedArray):
    """An underlying indexed ragged array.

    A collection of features stored using an indexed ragged array
    combines all features along a single dimension (the "sample
    dimension") such that the values of each feature in the collection
    are interleaved.

    The information needed to uncompress the data is stored in an
    "index variable" that specifies the feature that each element of
    the sample dimension belongs to.

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
        index_variable=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: array_like
                The compressed array.

            shape: `tuple`
                The shape of the uncompressed array.

            index_variable: `Index`
                The index variable required to uncompress the data,
                corresponding to a CF-netCDF index variable.

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
            index_variable=index_variable,
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
        timeSeries features has been compressed as an indexed ragged
        array. The features have counts of have counts of 2, 5, and 4
        elements, at compressed locations (5, 8), (1, 3, 4, 7, 10),
        and (0, 2, 6, 9) respectively.

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
        (1, 12)
        (1, 12)
        (1, 12)
        >>> for i in c_indices:
        ...    print(i)
        ...
        (array([5, 8]),)
        (array([1, 3, 4, 7, 10]),)
        (array([0, 2, 6, 9]),)
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
                index = np.array(self.get_index())
                unique = np.unique(index).tolist()
                c_indices.append([np.where(index == i)[0] for i in unique])
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
