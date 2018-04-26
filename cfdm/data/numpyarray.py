import abc

import operator
import sys

import numpy
import netCDF4

from .array import Array


class NumpyArray(Array):
    '''A numpy  array.

    '''
    def __init__(self, array=None):
        '''
        
**Initialization**

:Parameters:

    array: `numpy.ndarray`

        '''
        super(NumpyArray, self).__init__(array=array)
    #--- End: def

    def __getitem__(self, indices):
        '''

x.__getitem__(indices) <==> x[indices]

Returns an independent numpy array.

        '''
        # Must ascertain uniqueness *before* we create another
        # reference to self.array!
        isunique = self.isunique
        
        array = self.array

        if not isunique:
            if numpy.ma.isMA(array) and not self.ndim:
                # This is because numpy.ma.copy doesn't work for
                # scalar arrays (at the moment, at least)
                ma_array = numpy.ma.empty((), dtype=array.dtype)
                ma_array[...] = array
                array = ma_array
            else:
                array = array.copy()
        #--- End: if
        
        return self.get_subspace(array, indices)
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

    @property
    def isunique(self):
        '''
        '''
        return sys.getrefcount(self.array) <= 2
    
    def open(self):
        pass

    def close(self):
        pass
#--- End: class
