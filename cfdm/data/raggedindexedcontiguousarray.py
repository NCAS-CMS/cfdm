from builtins import (range, super, zip)

import numpy

from . import abstract
from . import mixin


class RaggedIndexedContiguousArray(mixin.RaggedContiguous,
                                   mixin.RaggedIndexed,
                                   abstract.CompressedArray):
    '''An underlying indexed contiguous ragged array.

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

    .. versionadded:: 1.7.0

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, count_variable=None, index_variable=None):
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

        count_variable: `Count`
            The count variable required to uncompress the data,
            corresponding to a CF-netCDF count variable.

        index_variable: `Index`
            The index variable required to uncompress the data,
            corresponding to a CF-netCDF CF-netCDF index variable.

        '''
#        if not isinstance(compressed_array, abstract.Array):
#            if not isinstance(compressed_array, numpy.ndarray):
#                compressed_array = numpy.asanyarray(compressed_array)
#
#            compressed_array = NumpyArray(compressed_array)

        super().__init__(compressed_array=compressed_array,
                         shape=shape, size=size, ndim=ndim,
                         count_variable=count_variable,
                         index_variable=index_variable,
                         compression_type='ragged indexed contiguous',
                         compressed_dimension=0)

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

        count_array = self.get_count().data.array
        index_array = self.get_index().data.array

        # Loop over instances
        for i in range(uarray.shape[0]):

            # For all of the profiles in ths instance, find the
            # locations in the count array of the number of elements
            # in the profile
            xprofile_indices = numpy.where(index_array == i)[0]

            # Find the number of profiles in this instance
            n_profiles = xprofile_indices.size

            # Loop over profiles in this instance
            for j in range(uarray.shape[1]):
                if j >= n_profiles:
                    continue

                # Find the location in the count array of the number
                # of elements in this profile
                profile_index = xprofile_indices[j]

                if profile_index == 0:
                    start = 0
                else:
                    start = int(count_array[:profile_index].sum())

                stop = start + int(count_array[profile_index])

                sample_indices = slice(start, stop)

                u_indices = (i, #slice(i, i+1),
                             j, #slice(j, j+1),
                             slice(0, stop-start)) #slice(0, sample_indices.stop - sample_indices.start))

                uarray[u_indices] = compressed_array[(sample_indices,)]
            # --- End: for
        # --- End: for

        return self.get_subspace(uarray, indices, copy=True)

    def to_memory(self):
        '''TODO

    :Returns:

        `RaggedIndexedContiguousArray`
            TODO

    **Examples:**

    TODO

        '''
        super().to_memory()
        self.get_count().data.to_memory()
        self.get_index().data.to_memory()
        return self

# --- End: class
