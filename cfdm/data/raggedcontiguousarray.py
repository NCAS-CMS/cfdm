import numpy

from . import abstract, mixin


class RaggedContiguousArray(mixin.RaggedContiguous, abstract.CompressedArray):
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
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: `Data`
                The compressed data.

            shape: `tuple`
                The uncompressed array dimension sizes.

            size: `int`
                Number of elements in the uncompressed array.

            ndim: `int`
                The number of uncompressed array dimensions

            count_variable: `Count`
                The count variable required to uncompress the data,
                corresponding to a CF-netCDF count variable.

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            size=size,
            ndim=ndim,
            count_variable=count_variable,
            compression_type="ragged contiguous",
            compressed_dimension=0,
        )

    def __getitem__(self, indices):
        """Returns a subspace of the array defined by the given indices.

        That is, returns a subspace of the uncompressed data in an
        independent numpy array. Note that:

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

        .. versionadded:: (cfdm) 1.7.0

        """
        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------

        compressed_array = self._get_compressed_Array()

        # Initialise the un-sliced uncompressed array
        uarray = numpy.ma.masked_all(self.shape, dtype=self.dtype)

        # --------------------------------------------------------
        # Compression by contiguous ragged array
        #
        # The uncompressed array has dimensions (instance
        # dimension, element dimension).
        # --------------------------------------------------------

        count_array = self.get_count().data.array

        start = 0
        for i, n in enumerate(count_array):
            n = int(n)
            sample_indices = slice(start, start + n)

            u_indices = (
                i,
                slice(0, sample_indices.stop - sample_indices.start),
            )

            uarray[u_indices] = compressed_array[(sample_indices,)]
            start += n

        return self.get_subspace(uarray, indices, copy=True)

    def to_memory(self):
        """Bring an array on disk into memory and retain it there.

        There is no change to an array that is already in memory.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `{{class}}`
                The array that is stored in memory.

        **Examples:**

        >>> b = a.to_memory()

        """
        super().to_memory()
        self.get_count().data.to_memory()
        return self
