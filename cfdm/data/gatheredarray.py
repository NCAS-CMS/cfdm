from builtins import (range, super, zip)
from functools import reduce

from operator import mul

import numpy

from . import abstract


class GatheredArray(abstract.CompressedArray):
    '''A container for a gathered compressed array.

Compression by gathering combines axes of an orthogonal
multi-dimensional array into a new, discrete axis (the "list axis")
whilst omitting the missing values and thus reducing the number of
values that need to be stored.

The information needed to uncompress the data is stored in a separate
variable (the "list variable") that contains the indices needed to
uncompress the data.

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, compressed_dimension=None,
                 list_variable=None):
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

    compressed_dimension: `int`
        The position of the compressed dimension in the compressed
        array.

    list_variable: `List`
        The "list variable" required to uncompress the data, identical
        to the data of a CF-netCDF list variable.

        '''
        super().__init__(compressed_array=compressed_array,
                         shape=shape, ndim=ndim, size=size,
                         compressed_dimension=compressed_dimension,
                         compression_type='gathered',
                         list_variable=list_variable)
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
        
        compressed_array = self._get_component('compressed_array')

        # Initialise the un-sliced uncompressed array
        uarray = numpy.ma.masked_all(self.shape, dtype=self.dtype)

        # Initialise the uncomprssed array
        compressed_dimension = self.get_compressed_dimension()
            
        compressed_axes = self.get_compressed_axes()
        
        n_compressed_axes = len(compressed_axes)

        uncompressed_shape = self.shape
        partial_uncompressed_shapes = [
            reduce(mul, [uncompressed_shape[i]
                         for i in compressed_axes[j:]], 1)
            for j in range(1, n_compressed_axes)]
        
        sample_indices = [slice(None)] * compressed_array.ndim
        u_indices      = [slice(None)] * self.ndim        

        list_array = self.get_list_variable().get_array()
        
        zeros = [0] * n_compressed_axes
        for j, b in enumerate(list_array):
            sample_indices[compressed_dimension] = j
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

    def get_list_variable(self, *default):
        '''TODO

.. versionadded:: 1.7

:Parameters:

    default: optional
        Return *default* if the list variable has not been set.

:Returns:

    out:
        TODO

**Examples**

TODO
        '''
        return self._get_component('list_variable', *default)
#        try:
#            return self._list_variable
#        except AttributeError:
#            if default:
#                return default[0]
#
#            raise AttributeError("{!r} has no list variable".format(
#                self.__class__.__name__))
    #--- End: def

#--- End: class
