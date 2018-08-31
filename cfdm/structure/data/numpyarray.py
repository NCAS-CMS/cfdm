from builtins import super

import numpy

from . import abstract


class NumpyArray(abstract.Array):
    '''A numpy array.

    '''
    def __init__(self, array):
        '''
        
**Initialization**

:Parameters:

    array: `numpy.ndarray`

        '''
        super().__init__(array=array)
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

    def get_array(self):
        '''
        '''
        array = self.array
        
        if not array.ndim and numpy.ma.isMA(array):
            # This is because numpy.ma.copy doesn't work for
            # scalar arrays (at the moment, at least)
            ma_array = numpy.ma.empty((), dtype=array.dtype)
            ma_array[...] = array
            array = ma_array
        else:
            array = array.copy()

        return array
    #--- End: def

#--- End: class
