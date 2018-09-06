from builtins import super

import numpy

from . import abstract


class RaggedContiguousArray(abstract.CompressedArray):
    '''

    '''
    def __init__(self, array=None, shape=None, size=None, ndim=None,
                 elements_per_instance=None):
        '''**Initialization**

:Parameters:

    array: `abstract.Array`

        '''
        super().__init__(array=array, shape=shape, size=size,
                         ndim=ndim,
                         elements_per_instance=elements_per_instance)
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

        return self.get_subspace(uarray, indices, copy=False)
    #--- End: def

    def compressed_axes(self):
        '''
        '''
        return self._compressed_axes(sample_axis=0)
    #--- End: def

#--- End: class
