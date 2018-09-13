from builtins import super

import numpy

from . import abstract


class RaggedContiguousArray(abstract.CompressedArray):
    '''A container for a contiguous ragged compressed array.

A collection of features stored using a contiguous ragged array
combines all features along a single dimension (the "sample"
dimension) such that each feature in the collection occupies a
contiguous block.

The information needed to uncompress the data is stored in a separate
"count" array that gives the size of each block.

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, count_array=None):
        '''**Initialization**

:Parameters:

    compressed_array:
        The compressed array. May be any object that exposes the
        `cfdm.data.abstract.Array` interface.

    shape: `tuple`
        The uncompressed array dimension sizes.

    size: `int`
        Number of elements in the uncompressed array.

    ndim: `int`
        The number of uncompressed array dimensions

    sample_axis: `int`
        The position of the compressed axis in the compressed array.

    count_array:
        The "count" array required to uncompress the data, identical
        to the data of a CF-netCDF "count" variable. May be any object
        that exposes the `cfdm.data.abstract.Array` interface.

        '''
        super().__init__(compressed_array=compressed_array,
                         shape=shape, size=size, ndim=ndim,
                         compression_type='ragged contiguous',
                         _count_array=count_array, sample_axis=0)
    #--- End: def

    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns an subspace of the uncompressed data an independent numpy
array.

The indices that define the subspace are relative to the uncompressed
data and must be either `Ellipsis` or a sequence that contains an
index for each dimension. In the latter case, each dimension's index
must either be a `slice` object or a sequence of two or more integers.

Indexing is similar to numpy indexing. The only difference to numpy
indexing (given the restrictions on the type of indices allowed) is:

  * When two or more dimension's indices are sequences of integers
    then these indices work independently along each dimension
    (similar to the way vector subscripts work in Fortran).

        '''
        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        
        compressed_array = self.compressed_array

        # Initialise the un-sliced uncompressed array
        uarray = numpy.ma.masked_all(self.shape, dtype=self.dtype)

        # --------------------------------------------------------
        # Compression by contiguous ragged array
        #
        # The uncompressed array has dimensions (instance
        # dimension, element dimension).
        # --------------------------------------------------------
            
        start = 0 
        for i, n in enumerate(self.count_array.get_array()):
            n = int(n)
            sample_indices = slice(start, start + n)
            
            u_indices = (i,
                         slice(0, sample_indices.stop - sample_indices.start))
            
            uarray[u_indices] = compressed_array[sample_indices]
            
            start += n
        #--- End: for

        return self.get_subspace(uarray, indices, copy=True)
    #--- End: def


    @property
    def count_array(self):
        '''
        '''
        return self._count_array
#--- End: class
