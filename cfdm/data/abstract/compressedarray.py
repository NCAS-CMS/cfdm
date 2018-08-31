from future.utils import with_metaclass
from builtins import (range, super)

import abc

from .array import Array

_MUST_IMPLEMENT = 'This method must be implemented'


class CompressedArray(with_metaclass(abc.ABCMeta, Array)):
    '''

    '''
    def __init__(self, array=None, shape=None, size=None, ndim=None,
                 **kwargs):
        '''**Initialization**

:Parameters:

    array: `abstract.Array`

        '''
        super().__init__(array=array, _shape=shape, _size=size,
                         _ndim=ndim, **kwargs)
    #--- End: def

    @abc.abstractmethod
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a numpy array that does not share memory with the un-indexed
array.


MORE BLURB HERE ON UNPACKING ALGORITHM
        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def

    @property
    def ndim(self):
        return self._ndim

    @property
    def shape(self):
        return self._shape

    @property
    def size(self):
        return self._size

    @property
    def dtype(self):
        return self.array.dtype

    def close(self):
        self.array.close()
    
    def compressed_axes(self):
        '''
        '''
#        sample_axis = self.compression_parameters.get('sample_axis', 0)
        sample_axis = getattr(self, 'sample_axis', 0)

        return list(range(sample_axis, self.ndim - (self.array.ndim - sample_axis - 1)))
    #--- End: def

    def get_array(self):
        '''
        '''
        return self[...]
    
    def open(self):
        self.array.open()

#--- End: class
