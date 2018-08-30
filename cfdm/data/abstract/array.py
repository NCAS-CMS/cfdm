from future.utils import with_metaclass
from builtins import str
import abc

import numpy

from ...structure.data.abstract import Array as structure_Array

_MUST_IMPLEMENT = 'This method must be implemented'


class Array(with_metaclass(abc.ABCMeta, structure_Array)):
    '''A container for an array.
    
    '''
    @abc.abstractmethod
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a numpy array that does not share memory with the un-indexed
array.
        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def

    @abc.abstractmethod
    def close(self):
        '''
        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def

    @classmethod
    def get_subspace(cls, array, indices, copy=True):
        '''Subset the input numpy array with the given indices.

Indexing is similar to that of a numpy array. The differences to numpy
array indexing are

  1. An integer index i takes the i-th element but does not reduce the
     rank of the output array by one.

  2. When more than one dimension's slice is a 1-d boolean array or
     1-d sequence of integers then these indices work independently
     along each dimension (similar to the way vector subscripts work
     in Fortran).

indices must contain an index for each dimension of the input array.

:Parameters:

    array: `numpy.ndarray`

    indices: `list`

    copy: `bool`
        Return an independent array.

:Returns:

    out: `numpy.ndarray`

        '''
        if indices is Ellipsis:
            return array
        
        axes_with_list_indices = [i for i, x in enumerate(indices)
                                  if not isinstance(x, slice)]
        n_axes_with_list_indices = len(axes_with_list_indices)
    
        if n_axes_with_list_indices < 2:
            # ------------------------------------------------------------
            # At most one axis has a list-of-integers index so we can do a
            # normal numpy subspace
            # ------------------------------------------------------------
            array = array[tuple(indices)]
        else:
            # ------------------------------------------------------------
            # At least two axes have list-of-integers indices so we can't
            # do a normal numpy subspace
            # ------------------------------------------------------------
            if numpy.ma.isMA(array):
                take = numpy.ma.take
            else:
                take = numpy.take
    
            indices = list(indices)
            for axis in axes_with_list_indices:
                array = take(array, indices[axis], axis=axis)
                indices[axis] = slice(None)
    
            if n_axes_with_list_indices < len(indices):
                # Apply subspace defined by slices
                array = array[tuple(indices)]
        #--- End: if

        if copy:
            if numpy.ma.isMA(array) and not array.ndim:
                # This is because numpy.ma.copy doesn't work for
                # scalar arrays (at the moment, at least)
                ma_array = numpy.ma.empty((), dtype=array.dtype)
                ma_array[...] = array
                array = ma_array
            else:
                array = array.copy()
        #--- End: if
        
        return array                
    #--- End: def

    @abc.abstractmethod
    def open(self):
        '''
        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #---End: def
    
#--- End: class
