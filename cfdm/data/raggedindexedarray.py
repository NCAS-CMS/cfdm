from builtins import (range, super)

import numpy

from . import abstract


class RaggedIndexedArray(abstract.CompressedArray):
    '''

    '''
    def __init__(self, array=None, shape=None, size=None, ndim=None,
                 instances=None):
        '''**Initialization**

:Parameters:

    array: `abstract.Array`

        '''
        super().__init__(array=array, shape=shape, size=size,
                         ndim=ndim, instances=instances)
    #--- End: def

    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a numpy array that does not share memory with the compressed
array.

        '''
        compressed_array = self.array

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

        return self.get_subspace(uarray, indices, copy=False)
    #--- End: def

#--- End: class
