from future.utils import with_metaclass
from builtins import (object, str)
import abc

import numpy

from ...structure.data.abstract import Array as structure_data_Array

_MUST_IMPLEMENT = 'This method must be implemented'


class Array(with_metaclass(abc.ABCMeta, structure_data_Array)):
    '''A container for an array.
    
    '''
           
#    def __init__(self, **kwargs):
#        '''
#        
#**Initialization**
#
#:Parameters:
#
#    dtype: `numpy.dtype`
#        The numpy data type of the data array.
#
#    ndim: `int`
#        Number of dimensions in the data array.
#
#    shape: `tuple`
#        The data array's dimension sizes.
#
#    size: `int`
#        Number of elements in the data array.
#
#'''
#        self.__dict__ = kwargs
#    #--- End: def
               
#    def __deepcopy__(self, memo):
#        '''
#
#Used if copy.deepcopy is called on the variable.
#
#'''
#        return self.copy()
#    #--- End: def

    @abc.abstractmethod
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a numpy array.
        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def

#    def __repr__(self):
#        '''
#
#x.__repr__() <==> repr(x)
#
#'''      
#        return "<{0}: {1}>".format(self.__class__.__name__, str(self))
#    #--- End: def
#        
#    def __str__(self):
#        '''
#
#x.__str__() <==> str(x)
#
#'''
#        return "shape={0}, dtype={1}".format(self.shape, self.dtype)
#    #--- End: def

#    @abc.abstractproperty
#    def ndim(self):
#        raise NotImplementedError(_MUST_IMPLEMENT)
#
#    @abc.abstractproperty
#    def shape(self):
#        raise NotImplementedError(_MUST_IMPLEMENT)
#
#    @abc.abstractproperty
#    def size(self):
#        raise NotImplementedError(_MUST_IMPLEMENT)
#    
#    @abc.abstractproperty
#    def dtype(self):
#        raise NotImplementedError(_MUST_IMPLEMENT)
    
    @abc.abstractmethod
    def close(self):
        '''
        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def

#    def copy(self):
#        '''Return a deep copy.
#
#``f.copy() is equivalent to ``copy.deepcopy(f)``.
#
#:Returns:
#
#    out :
#        A deep copy.
#
#:Examples:
#
#>>> g = f.copy()
#
#        '''
#        klass = self.__class__
#        new = klass.__new__(klass)
#        new.__dict__ = self.__dict__.copy()
#        return new
#    #--- End: def

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
