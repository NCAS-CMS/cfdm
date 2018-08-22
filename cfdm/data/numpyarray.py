from __future__ import absolute_import
import abc
import sys

import numpy

#from .array import Array
from . import abstract


class NumpyArray(abstract.Array):
    '''A numpy array.

    '''
    def __init__(self, array=None):
        '''
        
**Initialization**

:Parameters:

    array: `numpy.ndarray`

        '''
        if array is not None:
            super(NumpyArray, self).__init__(array=array)
    #--- End: def

    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a numpy array that might share memory with the un-indexed
numpy array.

        '''
#        # Must ascertain uniqueness *before* we create another
#        # reference to self.array!
#        isunique = sys.getrefcount(self.array) <= 2 #self.isunique
#        unique_base = sys.getrefcount(self.array.base) <= 2 #self.isunique            
#        base = self.array.base
#        if base is None:
#            unique_base = True
#        
#        array = self.array
#
#        if not unique_base:
#            
#            
#        
#        if 
#        
#        if not isunique:
#            if numpy.ma.isMA(array) and not self.ndim:
#                # This is because numpy.ma.copy doesn't work for
#                # scalar arrays (at the moment, at least)
#                ma_array = numpy.ma.empty((), dtype=array.dtype)
#                ma_array[...] = array
#                array = ma_array
#            else:
#                array = array.copy()
#        #--- End: if
#        array = self.array
        
        return self.get_subspace(self.array, indices)

#        if not isunique:
#        if numpy.ma.isMA(out) and not out.ndim:
#            # This is because numpy.ma.copy doesn't work for
#            # scalar arrays (at the moment, at least)
#            ma_out = numpy.ma.empty((), dtype=array.dtype)
#            ma_out[...] = out
#            out = ma_out
#        else:
#            out = out.copy()                
#        
#        return out
    #--- End: def

    @property
    def ndim(self):
        return self.array.ndim

    @property
    def shape(self):
        return self.array.shape

    @property
    def size(self):
        return self.array.size

    @property
    def dtype(self):
        return self.array.dtype

#    @property
#    def isunique(self):
#        '''
#        '''
#        return sys.getrefcount(self.array) <= 2
    
    def open(self):
        pass

    def close(self):
        pass
#--- End: class
