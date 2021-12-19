from itertools import product

import numpy as np

from .subarray import GatheredSubarray
from .abstract import CompressedArray


class GatheredArray(CompressedArray):
    """An underlying gathered array.

    Compression by gathering combines axes of a multidimensional array
    into a new, discrete axis whilst omitting the missing values and
    thus reducing the number of values that need to be stored.

    The information needed to uncompress the data is stored in a "list
    variable" that gives the indices of the required points.

    See CF section 8.2. "Lossless Compression by Gathering".

    .. versionadded:: (cfdm) 1.7.0

    """

    def __new__(cls, *args, **kwargs):
        """Store subarray classes.

        If a child class requires different subarray classes than the
        ones defined here, then they must be defined in the __new__
        method of the child class.

        .. versionadded:: (cfdm) 1.9.TODO.0

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
        compressed_dimensions={},
        list_variable=None,
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

                The number of uncompressed array dimensions

            compressed_dimensions: `dict`
                Mapping of dimensions of the compressed array to their
                corresponding dimensions in the uncompressed
                array. Compressed array dimensions that are not
                compressed must be omitted from the mapping.

                *Parameter example:*
                  ``{2: (2, 3)}``

                .. versionadded:: (cfdm) 1.9.TODO.0

            list_variable: `List`
                The "list variable" required to uncompress the data,
                identical to the data of a CF-netCDF list variable.

            compressed_dimension: deprecated at version 1.9.TODO.0
                Use the *compressed_dimensions* parameter instead.

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            compressed_dimension=compressed_dimension,
            compressed_dimensions=compressed_dimensions.copy(),
            list_variable=list_variable,
            compression_type="gathered",
        )

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed array as an independent
        numpy array.

        """
        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        Subarray = self._Subarray[self.get_compression_type()]

        # Initialise the un-sliced uncompressed array
        u = np.ma.masked_all(self.shape, dtype=self.dtype)

        compressed_dimensions = self.compressed_dimensions()

        conformed_data = self.conformed_data()
        compressed_data = conformed_data["data"]
        unravelled_indices = conformed_data["unravelled_indices"]

        for u_indices, u_shape, c_indices in zip(*self.subarrays()):
            subarray = Subarray(
                data=compressed_data,
                indices=c_indices,
                shape=u_shape,
                compressed_dimensions=compressed_dimensions,
                unravelled_indices=unravelled_indices,
            )
            u[u_indices] = subarray[...]

        if indices is Ellipsis:
            return u

        return self.get_subspace(u, indices, copy=True)

    def conformed_data(self):
        """The compressed data and list variable.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `dict`

                The conformed gathered data, with the key ``'data'``;
                and the `tuple` of unravelled list indices with the
                key ``'unravelled_indices'``.

        """
        out = super().conformed_data()

        _, u_dims = self.compressed_dimensions().popitem()
        list_variable = np.array(self.get_list())

        unravelled_indices = [slice(None)] * self.ndim

        unravelled_indices[u_dims[0] : u_dims[-1] + 1] = np.unravel_index(
            list_variable, self.shape[u_dims[0] : u_dims[-1] + 1]
        )

        out["unravelled_indices"] = tuple(unravelled_indices)

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

    def subarrays(self):
        """Return descriptors for every subarray.

        These descriptors are used during subarray decompression.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            sequence of iterators
                Each iterable iterates over a particular descriptor
                from each subarray.

                1. The indices of the uncompressed array that
                   correspond to each subarray.

                2. The shape of each uncompressed subarray.

                3. The indices of the compressed array that correspond
                   to each subarray.

        **Examples**

        An original 3-d array with shape (4, 73, 96) has been
        compressed by gathering the dimensions with sizes 73 and 96
        respectively.

        >>> u_indices, u_shapes, c_indices = x.subarrays()
        >>> for i in u_indices:
        ...    print(i)
        ...
        (slice(0, 1, None), slice(None, None, None), slice(None, None, None))
        (slice(1, 2, None), slice(None, None, None), slice(None, None, None))
        (slice(2, 3, None), slice(None, None, None), slice(None, None, None))
        (slice(3, 4, None), slice(None, None, None), slice(None, None, None))
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
        (slice(0, 1, None), slice(None, None, None))
        (slice(1, 2, None), slice(None, None, None))
        (slice(2, 3, None), slice(None, None, None))
        (slice(3, 4, None), slice(None, None, None))

        """
        d1, u_dims = self.compressed_dimensions().popitem()
        uncompressed_shape = self.shape

        # The indices of the uncompressed array that correspond to
        # each subarray, and the shape of each uncompressed subarray.
        u_indices = []
        u_shapes = []
        for d, size in enumerate(uncompressed_shape):
            if d in u_dims:
                u_indices.append((slice(None),))
                u_shapes.append((size,))
            else:
                u_indices.append([slice(i, i + 1) for i in range(size)])
                u_shapes.append((1,) * size)

        # The indices of the compressed array that correspond to each
        # subarray
        c_indices = []
        for d, size in enumerate(self.source().shape):
            if d == d1:
                c_indices.append((slice(None),))
            else:
                c_indices.append([slice(i, i + 1) for i in range(size)])

        return (
            product(*u_indices),
            product(*u_shapes),
            product(*c_indices),
        )

    def to_memory(self):
        """Bring an array on disk into memory and retain it there.

        There is no change to an array that is already in memory.

        :Returns:

            `{{class}}`
                TODO

        **Examples**

        >>> a.to_memory()

        """
        super().to_memory()

        list_variable = self.get_list(None)
        if list_variable is not None:
            list_variable.data.to_memory()
