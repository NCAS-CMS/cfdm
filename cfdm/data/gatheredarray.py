from functools import reduce
from operator import mul

import numpy as np

from .abstract import CompressedArray


class GatheredArray(CompressedArray):
    """An underlying gathered array.

    Compression by gathering combines axes of a multidimensional array
    into a new, discrete axis whilst omitting the missing values and
    thus reducing the number of values that need to be stored.

    The information needed to uncompress the data is stored in a "list
    variable" that gives the indices of the required points.

    .. versionadded:: (cfdm) 1.7.0

    """

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
                The uncompressed array dimension sizes.

            size: `int`
                Number of elements in the uncompressed array.

            ndim: `int`
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
            ndim=ndim,
            size=size,
            compressed_dimension=compressed_dimension,
            compressed_dimensions=compressed_dimensions.copy(),
            list_variable=list_variable,
            compression_type="gathered",
        )

    def __getitem__(self, indices):
        """Returns a subspace of the uncompressed data as a numpy array.

        x.__getitem__(indices) <==> x[indices]

        The indices that define the subspace are relative to the
        uncompressed data and must be either `Ellipsis` or a sequence that
        contains an index for each dimension. In the latter case, each
        dimension's index must either be a `slice` object or a sequence of
        two or more integers.

        Indexing is similar to numpy indexing. The only difference to
        numpy indexing (given the restrictions on the type of indices
        allowed) is:

          * When two or more dimension's indices are sequences of integers
            then these indices work independently along each dimension
            (similar to the way vector subscripts work in Fortran).

        """
        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------

        compressed_array = self._get_compressed_Array().array

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=self.dtype)

        # Initialise the uncomprssed array
        (
            compressed_dimension,
            compressed_axes,
        ) = self.compressed_dimensions().popitem()

        n_compressed_axes = len(compressed_axes)

        uncompressed_shape = self.shape
        partial_uncompressed_shapes = [
            reduce(
                mul, [uncompressed_shape[i] for i in compressed_axes[j:]], 1
            )
            for j in range(1, n_compressed_axes)
        ]

        sample_indices = [slice(None)] * compressed_array.ndim
        u_indices = [slice(None)] * self.ndim

        list_array = self.get_list().data.array

        zeros = [0] * n_compressed_axes
        for j, b in enumerate(list_array):
            sample_indices[compressed_dimension] = slice(j, j + 1)

            # Note that it is important for indices a and b to be
            # integers (rather than the slices a:a+1 and b:b+1) so
            # that these dimensions are dropped from uarray[u_indices]
            u_indices[compressed_axes[0] : compressed_axes[-1] + 1] = zeros
            for i, z in zip(compressed_axes[:-1], partial_uncompressed_shapes):
                if b >= z:
                    (a, b) = divmod(b, z)
                    u_indices[i] = a

            u_indices[compressed_axes[-1]] = b

            compressed = compressed_array[tuple(sample_indices)]
            sample_indices[compressed_dimension] = 0
            compressed = compressed[tuple(sample_indices)]

            uarray[tuple(u_indices)] = compressed

        return self.get_subspace(uarray, indices, copy=True)

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

        **Examples**

        >>> l = g.get_list()

        >>> l = g.get_list(default=None)

        """
        return self._get_component("list_variable", default=default)

    def to_memory(self):
        """Bring an array on disk into memory and retain it there.

        There is no change to an array that is already in memory.

        :Returns:

            `{{class}}`
                The array that is stored in memory.

        **Examples**

        >>> b = a.to_memory()

        """
        super().to_memory()
        self.get_list().data.to_memory()
        return self
