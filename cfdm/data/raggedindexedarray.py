from itertools import product

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

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        index_variable=None,
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: `Data`
                The compressed array.

            shape: `tuple`
                The shape of the uncompressed array.

            size: `int`
                Deprecated at version 1.9.TODO.0. Ignored if set.

                Number of elements in the uncompressed array.

            ndim: `int`
                Deprecated at version 1.9.TODO.0. Ignored if set.

                The number of uncompressed array dimensions.

            index_variable: `Index`
                The index variable required to uncompress the data,
                corresponding to a CF-netCDF index variable.

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            index=index_variable,
            compressed_dimensions={0: (0, 1)},
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

        TODO

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
        index = np.array(self.get_index())
        unique = np.unique(index).tolist()
        c_indices[d1] = [np.where(index == i)[0] for i in unique]

        return (
            product(*u_indices),
            product(*u_shapes),
            product(*c_indices),
        )
