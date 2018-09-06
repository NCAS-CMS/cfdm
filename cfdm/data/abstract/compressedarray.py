from future.utils import with_metaclass
from builtins import (range, super)

import abc

from .array import Array

_MUST_IMPLEMENT = 'This method must be implemented'


class CompressedArray(with_metaclass(abc.ABCMeta, Array)):
    '''

    '''
    def __init__(self, array=None, shape=None, size=None, ndim=None,
                 sample_axis=None, **kwargs):
        '''**Initialization**

:Parameters:

    array: `abstract.Array`

        '''
        super().__init__(array=array, _shape=shape, _size=size,
                         _ndim=ndim, _sample_axis=sample_axis,
                         **kwargs)
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

#    def _compressed_axes(self, sample_axis):
#        '''
#        '''
#        return list(range(sample_axis, self.ndim - (self.array.ndim - sample_axis - 1)))
#    #--- End: def
    
    @property
    def ndim(self):
        '''The number of dimensions of the uncompressed data array.

:Examples:

>>> d.shape
(73, 96)
>>> d.ndim
2
>>> d.size
7008

>>> d.shape
(1, 1, 1)
>>> d.ndim
3
>>> d.size
1

>>> d.shape
()
>>> d.ndim
0
>>> d.size
1

        '''
        return self._ndim
    #--- End: def

    @property
    def sample_axis(self):
        '''
        '''
        return self._sample_axis
    #--- End: def

    @property
    def shape(self):
        '''Shape of the uncompressed data array.

:Examples:

>>> d.shape
(73, 96)
>>> d.ndim
2
>>> d.size
7008

>>> d.shape
(1, 1, 1)
>>> d.ndim
3
>>> d.size
1

>>> d.shape
()
>>> d.ndim
0
>>> d.size
1

        '''
        return self._shape
    #--- End: def

    @property
    def size(self):
        '''Number of elements in the uncompressed data array.

:Examples:

>>> d.shape
(73, 96)
>>> d.size
7008
>>> d.ndim
2

>>> d.shape
(1, 1, 1)
>>> d.ndim
3
>>> d.size
1

>>> d.shape
()
>>> d.ndim
0
>>> d.size
1
'''
        return self._size
    #--- End: def

    @property
    def dtype(self):
        return self.array.dtype
    #--- End: def

    def close(self):
        self.array.close()
    #--- End: def

    def compressed_axes(self):
        '''
        '''
        sample_axis = self.sample_axis
        return list(range(sample_axis, self.ndim - (self.array.ndim - sample_axis - 1)))
    #--- End: def
    
    #--- End: def

    def get_array(self):
        '''
        '''
        return self[...]
    #--- End: def

    def open(self):
        self.array.open()
    #--- End: def

#--- End: class
