from builtins import (range, super)

import numpy

from . import abstract


class RaggedIndexedArray(abstract.CompressedArray):
    '''A container for an indexed ragged compressed array.

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, instances=None):
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

    instances: `Array` or numpy array_like
        The zero-based indices of the instance to which each element
        in the compressed array belongs.

        '''
        super().__init__(compressed_array=compressed_array,
                         shape=shape, size=size, ndim=ndim,
                         instances=instances, sample_axis=0)
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
        # Compression by indexed ragged array.
        #
        # The uncompressed array has dimensions (instance
        # dimension, element dimension).
        # --------------------------------------------------------
        instances = self.instances.get_array()
        
        for i in range(uarray.shape[0]):
            sample_dimension_indices = numpy.where(instances == i)[0]
            
            u_indices = (i, #slice(i, i+1),
                         slice(0, len(sample_dimension_indices)))
            
            uarray[u_indices] = compressed_array[sample_dimension_indices]
        #--- End: for

        return self.get_subspace(uarray, indices, copy=True)
    #--- End: def

#--- End: class
