from builtins import (range, super, zip)
from functools import reduce

from operator import mul

import numpy

from . import abstract


class GatheredArray(abstract.CompressedArray):
    '''

    '''
    def __init__(self, array=None, shape=None, size=None, ndim=None,
                 sample_axis=None, indices=None):
        '''**Initialization**

:Parameters:

    array: `abstract.Array`

        '''
        super().__init__(array=array, shape=shape, ndim=ndim,
                         size=size, sample_axis=sample_axis,
                         indices=indices)
    #--- End: def

    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a numpy array that does not share memory with the compressed
array.

'''
        compressed_array = self.array

        # Initialise the un-sliced uncompressed array
        uarray = numpy.ma.masked_all(self.shape, dtype=self.dtype)

        # Initialise the uncomprssed array
        sample_axis           = self.sample_axis
        uncompression_indices = self.indices
        
        
        compressed_axes = self.compressed_axes()
        
        n_compressed_axes = len(compressed_axes)

        uncompressed_shape = self.shape
        partial_uncompressed_shapes = [
            reduce(mul, [uncompressed_shape[i] for i in compressed_axes[i:]], 1)
            for i in range(1, n_compressed_axes)]
        
        sample_indices = [slice(None)] * compressed_array.ndim
        u_indices      = [slice(None)] * self.ndim        
        
        zeros = [0] * n_compressed_axes
        for j, b in enumerate(uncompression_indices):
            sample_indices[sample_axis] = j
            # Note that it is important for this index to be an
            # integer (rather than the slice j:j+1) so that this
            # dimension is dropped from
            # compressed_array[sample_indices]
                
            u_indices[compressed_axes[0]:compressed_axes[-1]+1] = zeros
            for i, z in zip(compressed_axes[:-1], partial_uncompressed_shapes):
                if b >= z:
                    (a, b) = divmod(b, z)
                    u_indices[i] = a
            #--- End: for                    
            u_indices[compressed_axes[-1]] = b
            # Note that it is important for indices a and b to be
            # integers (rather than the slices a:a+1 and b:b+1) so
            # that these dimensions are dropped from uarray[u_indices]
                
            uarray[u_indices] = compressed_array[sample_indices]
        #--- End: for

        return self.get_subspace(uarray, indices, copy=False)
    #--- End: def

    def compressed_axes(self):
        '''
        '''
        return self._compressed_axes(sample_axis=self.sample_axis)
    #--- End: def

#--- End: class
