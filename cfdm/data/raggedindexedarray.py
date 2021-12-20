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

            source: optional
                Initialise the array from the given object.

                {{init source}}

                .. versionadded:: (cfdm) 1.9.TODO.0

            copy: `bool`, optional
                If False then do not deep copy input parameters prior
                to initialisation. By default arguments are deep
                copied.

                .. versionadded:: (cfdm) 1.9.TODO.0

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
            index_variable=index_variable,
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
        timeSeries features has been compressed as an indexed ragged
        array. The features have counts of have counts of 2, 5, and 4
        elements, at compressed locations (5, 8), (1, 3, 4, 7, 10),
        and (0, 2, 6, 9) respectively.

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
        (1, 12)
        (1, 12)
        (1, 12)
        >>> for i in c_indices:
        ...    print(i)
        ...
        (array([5, 8]),)
        (array([1, 3, 4, 7, 10]),)
        (array([0, 2, 6, 9]),)

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
