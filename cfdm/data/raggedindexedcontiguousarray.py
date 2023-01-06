from itertools import accumulate, product

import numpy as np

from .abstract import RaggedArray


class RaggedIndexedContiguousArray(RaggedArray):
    """An underlying indexed contiguous ragged array.

    A collection of features, each of which is sequence of (vertical)
    profiles, stored using an indexed contiguous ragged array combines
    all feature elements along a single dimension (the "sample
    dimension") such that a contiguous ragged array representation is
    used for each profile and the indexed ragged array representation
    to organise the profiles into timeseries.

    The information needed to uncompress the data is stored in a
    "count variable" that gives the size of each profile; and in a
    "index variable" that specifies the feature that each profile
    belongs to.

    It is assumed that the compressed dimensions are the two left-most
    dimensions in the compressed array.

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

            count_variable: `Count`
                The count variable required to uncompress the data,
                corresponding to a CF-netCDF count variable.

            index_variable: `Index`
                The index variable required to uncompress the data,
                corresponding to a CF-netCDF CF-netCDF index variable.

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
            index_variable=index_variable,
            compressed_dimensions={0: (0, 1, 2)},
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

        An original 3-d array with shape (2, 3, 4) comprising 2
        timeSeriesProfile features has been compressed as an indexed
        contiguous ragged array. The first feature has 3 profiles with
        counts of 2, 4, and 3 elements, at compressed locations (4,
        5), (0, 1, 2, 3), and (9, 10, 11) respectively. The second
        feature has 1 profile with a count of 3 elements, at
        compressed locations (6, 7, 8).

        >>> u_indices, u_shapes, c_indices, locations = x.subarrays()
        >>> for i in u_indices:
        ...    print(i)
        ...
        (slice(0, 1, None), slice(0, 1, None), slice(0, 4, None))
        (slice(0, 1, None), slice(1, 2, None), slice(0, 4, None))
        (slice(0, 1, None), slice(2, 3, None), slice(0, 4, None))
        (slice(1, 2, None), slice(0, 1, None), slice(0, 4, None))
        (slice(1, 2, None), slice(1, 2, None), slice(0, 4, None))
        (slice(1, 2, None), slice(2, 3, None), slice(0, 4, None))
        >>> for i in u_shapes
        ...    print(i)
        ...
        (1, 1, 4)
        (1, 1, 4)
        (1, 1, 4)
        (1, 1, 4)
        (1, 1, 4)
        (1, 1, 4)
        >>> for i in c_indices:
        ...    print(i)
        ...
        (slice(4, 6, None),)
        (slice(0, 4, None),)
        (slice(9, 12, None),)
        (slice(6, 9, None),)
        (slice(0, 0, None),)
        (slice(0, 0, None),)
        >>> for i in locations:
        ...    print(i)
        ...
        (0, 0, 0)
        (0, 1, 0)
        (0, 2, 0)
        (1, 0, 0)
        (1, 1, 0)
        (1, 2, 0)

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
                count_partial_sums = np.cumsum(
                    np.array(self.get_count())
                ).tolist()

                max_n_profiles = self.shape[u_dims[1]]

                ind = []
                for i in unique:
                    # find the locations in the count array for the profiles
                    # in this feature.
                    profile_locations = np.where(index == i)[0]

                    for j in profile_locations:
                        if not j:
                            start = 0
                        else:
                            start = count_partial_sums[j - 1]

                        ind.append(slice(start, count_partial_sums[j]))

                    # Add zero-sized slices for this feature's "missing"
                    # profiles
                    ind.extend(
                        (slice(0, 0),)
                        * (max_n_profiles - profile_locations.size)
                    )

                c_indices.append(ind)
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
