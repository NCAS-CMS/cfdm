#from __future__ import absolute_import
from builtins import super

import sys

import numpy

from . import abstract

from ..structure.data import NumpyArray as structure_NumpyArray


class NumpyArray(abstract.Array, structure_NumpyArray):
    '''A numpy array.

    '''
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a numpy array that does not share memory with the un-indexed
array.

        '''
        
        return self.get_subspace(self.array, indices, copy=True)
    #--- End: def

    def close(self):
        '''
        '''
        pass
    #--- End: def

    def open(self):
        '''
        '''
        pass
    #--- End: def

#--- End: class
