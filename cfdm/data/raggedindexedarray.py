from builtins import (range, super)

import numpy

from . import abstract
from . import mixin

class RaggedIndexedArray(mixin.RaggedIndexed,
                         abstract.CompressedArray):
    '''An underlying indexed ragged array.

    A collection of features stored using an indexed ragged array
    combines all features along a single dimension (the "sample
    dimension") such that the values of each feature in the collection
    are interleaved.

    The information needed to uncompress the data is stored in an
    "index variable" that specifies the feature that each element of
    the sample dimension belongs to.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, index_variable=None):
        '''**Initialization**

    :Parameters:

        compressed_array: `Data`
            The compressed array.

        shape: `tuple`
            The uncompressed array dimension sizes.

        size: `int`
            Number of elements in the uncompressed array.

        ndim: `int`
            The number of uncompressed array dimensions

        index_variable: `Index`
            The index variable required to uncompress the data,
            corresponding to a CF-netCDF index variable.

        '''
#        if not isinstance(compressed_array, abstract.Array):
#            if not isinstance(compressed_array, numpy.ndarray):
#                compressed_array = numpy.asanyarray(compressed_array)
#
#            compressed_array = NumpyArray(compressed_array)

        super().__init__(compressed_array=compressed_array,
                         shape=shape, size=size, ndim=ndim,
                         index_variable=index_variable,
                         compressed_dimension=0,
                         compression_type='ragged indexed')

    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

    Returns an subspace of the uncompressed data an independent numpy
    array.

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

        '''
        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------

        compressed_array = self._get_compressed_Array()

        # Initialise the un-sliced uncompressed array
        uarray = numpy.ma.masked_all(self.shape, dtype=self.dtype)

        # --------------------------------------------------------
        # Compression by indexed ragged array.
        #
        # The uncompressed array has dimensions (instance
        # dimension, element dimension).
        # --------------------------------------------------------
        index_array = self.get_index().data.array

        for i in range(uarray.shape[0]):
            sample_dimension_indices = numpy.where(index_array == i)[0]

            u_indices = (i, #slice(i, i+1),
                         slice(0, len(sample_dimension_indices)))

            uarray[u_indices] = compressed_array[(sample_dimension_indices,)]

        return self.get_subspace(uarray, indices, copy=True)

    def to_memory(self):
        '''TODO

        '''
        super().to_memory()
        self.get_index().data.to_memory()
        return self


# --- End: class
