from builtins import super

import numpy

from . import abstract


class RaggedContiguousArray(abstract.CompressedArray):
    '''A container for a contiguous ragged compressed array.

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, elements_per_instance=None):
        '''**Initialization**

:Parameters:

    compressed_array: `Array`
        The compressed array.

    shape: `tuple`
        The uncompressed array dimension sizes.

    size: `int`
        Number of elements in the uncompressed array.

    ndim: `int`
        The number of uncompressed array dimensions

    sample_axis: `int`
        The position of the compressed axis in the compressed array.

    elements_per_instance: `Array` or numpy array_like
        The number of elements that each instance has in the
        compressed array.

        '''
        super().__init__(compressed_array=compressed_array,
                         shape=shape, size=size, ndim=ndim,
                         elements_per_instance=elements_per_instance,
                         sample_axis=0)
    #--- End: def

    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns an uncompressed subspace of the gathered array as an
independent numpy array.

The indices that define the subspace are relative to the full
uncompressed array and must be either `Ellipsis` or a sequence that
contains an index for each dimension. In the latter case, each
dimension's index must either be a `slice` object or a sequence of
integers.

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
        for i, n in enumerate(self.elements_per_instance):
            n = int(n)
            sample_indices = slice(start, start + n)
            
            u_indices = (i,
                         slice(0, sample_indices.stop - sample_indices.start))
            
            uarray[u_indices] = compressed_array[sample_indices]
            
            start += n
        #--- End: for

        return self.get_subspace(uarray, indices, copy=True)
    #--- End: def

#--- End: class
