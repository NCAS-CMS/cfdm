from itertools import product

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

            compressed_array: `Data`
                The compressed data.

            shape: `tuple`
                The shape of the uncompressed array.

            count_variable: `Count`
                The count variable required to uncompress the data,
                corresponding to a CF-netCDF count variable.

            size: `int`
                Deprecated at version 1.9.TODO.0. Ignored if set.

                Number of elements in the uncompressed array.

            ndim: `int`
                Deprecated at version 1.9.TODO.0. Ignored if set.

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

    def subarrays(self):
        """Return descriptors for every subarray.

        Theses descriptors are used during subarray decompression.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            sequence of iterators
                Each iterable iterates over a particular descriptor
                from each subarray.

                There must be at least three sequences. The leading
                three of which describe:

                1. The indices of the uncompressed array that
                   correspond to each subarray.

                2. The shape of each uncompressed subarray.

                3. The indices of the compressed array that correspond
                   to each subarray.

        **Examples**

        An original 2-d array with shape (3, 5) comprising 3
        timeSeries features has been compressed as a contiguous ragged
        array. The features have counts of 2, 5, and 4 elements.

        >>> u_indices, u_shapes, c_indices = x.subarrays()
        >>> for i in u_indices:
        ...    print(i)
        ...
        (slice(0, 1, None), slice(None, None, None))
        (slice(1, 2, None), slice(None, None, None))
        (slice(2, 3, None), slice(None, None, None))
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

        """
        d1, (u_dim1, u_dim2) = self.compressed_dimensions().popitem()
        uncompressed_shape = self.shape

        n_features = uncompressed_shape[u_dim1]

        # The indices of the uncompressed array that correspond to
        # each subarray
        u_indices = [(slice(None),)] * self.ndim
        u_indices[u_dim1] = [slice(i, i + 1) for i in range(n_features)]

        # The shape of each uncompressed subarray
        u_shapes = [(n,) for n in uncompressed_shape]
        u_shapes[u_dim1] = (1,) * n_features

        # The indices of the compressed array that correspond to each
        # subarray
        c_indices = [(slice(None),)] * self.source().ndim
        count = np.array(self.get_count()).tolist()
        index = []
        start = 0
        for i, n in enumerate(count):
            index.append(slice(start, start + n))
            start += n

        c_indices[d1] = index

        return (
            product(*u_indices),
            product(*u_shapes),
            product(*c_indices),
        )
