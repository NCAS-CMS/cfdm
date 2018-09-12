from future.utils import with_metaclass
from builtins import str

import abc

import numpy

from ...structure.data.abstract import Array as structure_Array

_MUST_IMPLEMENT = 'This method must be implemented'


class Array(with_metaclass(abc.ABCMeta, structure_Array)):
    '''A container for an array.

The form of the array is arbitrary and is defined by the attributes
set on a subclass of the abstract `Array` object.

It must be possible to derive the following from the array:

  * Data-type of the array elements (see `dtype`)
  
  * Number of array dimensions (see `ndim`)
  
  * Array dimension sizes (see `shape`)
  
  * Number of elements in the array (see `size`)
  
  * An independent numpy array containing the data (see `get_array`)

  * A subspace of the array as an independent numpy array (see
    `__getitem__`)

See `cfdm.data.NumpyArray` for an example implementation.

    '''
    @abc.abstractmethod
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a subspace of the array as an independent numpy array.

The indices that define the subspace must be either `Ellipsis` or a
sequence that contains an index for each dimension. In the latter
case, each dimension's index must either be a `slice` object or a
sequence of two or more integers.

Indexing is similar to numpy indexing. The only difference to numpy
indexing (given the restrictions on the type of indices allowed) is:

  * When two or more dimension's indices are sequences of integers
    then these indices work independently along each dimension
    (similar to the way vector subscripts work in Fortran).

        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def

    @classmethod
    def get_subspace(cls, array, indices, copy=True):
        '''Return subspace, defined by indices, of a numpy array.

Indexing is similar to numpy indexing. The only difference to numpy
indexing (given the restrictions on the type of indices allowed, see
the *indices* parameter for details) is:

  * When two or more dimension's indices are sequences of integers
    then these indices work independently along each dimension
    (similar to the way vector subscripts work in Fortran).

:Parameters:

    array: `numpy.ndarray`
        The array to be subspaced.
        
    indices: 
        The indices that define the subspace.
     ..
        Must be either `Ellipsis` or a sequence that contains an index
        for each dimension. In the latter case, each dimension's index
        must either be a `slice` object or a sequence of two or more
        integers.

          *Example:*
            indices=Ellipsis
  
          *Example:*
            indices=[[5, 7, 8]]
  
          *Example:*
            indices=[slice(4, 7)]

          *Example:*
            indices=[slice(None), [5, 7, 8]]
  
          *Example:*
            indices=[[2, 5, 6], slice(15, 4, -2), [8, 7, 5]]

    copy: `bool`
        If `False` then the returned subspace may (or may not) be
        independent of the input *array*. By default the returned
        subspace is independent of the input *array*.

:Returns:

    out: `numpy.ndarray`

        '''
        if indices is not Ellipsis:
            axes_with_list_indices = [i for i, x in enumerate(indices)
                                      if not isinstance(x, slice)]
            n_axes_with_list_indices = len(axes_with_list_indices)
        
            if n_axes_with_list_indices < 2:
                # ----------------------------------------------------
                # At most one axis has a list-of-integers index so we
                # can do a normal numpy subspace
                # ----------------------------------------------------
                array = array[tuple(indices)]
            else:
                # ----------------------------------------------------
                # At least two axes have list-of-integers indices so
                # we can't do a normal numpy subspace
                # ----------------------------------------------------
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

#    @abc.abstractmethod
#    def open(self):
#        '''
#        '''
#        raise NotImplementedError(_MUST_IMPLEMENT)
#    #---End: def
    
#--- End: class
