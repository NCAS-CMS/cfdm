from builtins import (range, super, zip)
from functools import reduce

from operator import mul

import numpy

from . import abstract


class GatheredArray(abstract.CompressedArray):
    '''A container for a gathered compressed array.

Compression by gathering combines axes of a multi-dimensional array
into a new, discrete axis (the "list dimension") whilst omitting the
missing values and thus reducing the number of values that need to be
stored.

The information needed to uncompress the data is stored in a separate
variable (the "list variable") that contains the indices needed to
uncompress the data.

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, sample_axis=None, list_array=None):
        '''**Initialization**

:Parameters:

    compressed_array: subclass of `Array`
        The compressed array.

    shape: `tuple`
        The uncompressed array dimension sizes.

    size: `int`
        Number of elements in the uncompressed array.

    ndim: `int`
        The number of uncompressed array dimensions

    sample_axis: `int`
        The position of the compressed axis in the compressed array.

    list_array: `List`
        The "list variable" required to uncompress the data, identical
        to the data of a CF-netCDF list variable.

        '''
        super().__init__(compressed_array=compressed_array,
                         shape=shape, ndim=ndim, size=size,
                         sample_axis=sample_axis,
                         compression_type='gathered',
                         _list_array=list_array)
    #--- End: def

    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns an subspace of the uncompressed data as an independent numpy
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

        # Initialise the uncomprssed array
        sample_axis = self.sample_axis
            
        compressed_axes = self.get_compressed_axes()
        
        n_compressed_axes = len(compressed_axes)

        uncompressed_shape = self.shape
        partial_uncompressed_shapes = [
            reduce(mul, [uncompressed_shape[i]
                         for i in compressed_axes[j:]], 1)
            for j in range(1, n_compressed_axes)]
        
        sample_indices = [slice(None)] * compressed_array.ndim
        u_indices      = [slice(None)] * self.ndim        
        
        zeros = [0] * n_compressed_axes
        for j, b in enumerate(self.list_array.get_array()):
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

            uarray[tuple(u_indices)] = compressed_array[tuple(sample_indices)]
        #--- End: for

        return self.get_subspace(uarray, indices, copy=True)
    #--- End: def

    @property
    def list_array(self):
        '''
        '''
        return self._list_array
    #--- End: def

    def get_list(self):
        '''
        '''
        return self._list_array
    #--- End: def

#--- End: class
