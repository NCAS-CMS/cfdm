from future.utils import with_metaclass
from builtins import (range, super)

import abc

from .array import Array

_MUST_IMPLEMENT = 'This method must be implemented'


class CompressedArray(with_metaclass(abc.ABCMeta, Array)):
    '''A container for a compressed array.

The compressed array must be a subclass of `Array`.


CFDm says array is viewed as uncompressed.
ndim, etc are for uncomspressed array


It must be possible to derive the following from the contained array:

  * Data-type of the array elements (see `dtype`)

The following 
  
  * Number of array dimensions (see `ndim`)
  
  * Array dimension sizes (see `shape`)
  
  * Number of elements in the array (see `size`)
  
  * An independent numpy array containing the data (see `get_array`)

  * A subspace of the array as an independent numpy array (see
    `__getitem__`)

    '''
    def __init__(self, array=None, shape=None, size=None, ndim=None,
                 sample_axis=None, **kwargs):
        '''**Initialization**

:Parameters:

    array: `Array`

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

#    def close(self):
#        self.array.close()
#    #--- End: def

    def compressed_axes(self):
        '''
        '''
        sample_axis = self.sample_axis
        return list(range(sample_axis, self.ndim - (self.array.ndim - sample_axis - 1)))
    #--- End: def
    
    #--- End: def

    def get_array(self):
        '''Return an independent numpy array containing the data.

The compressed axes are uncompressed in the return numpy array.

:Examples:

>>> n = a.get_array()

        '''
        return self[...]
    #--- End: def

#    def open(self):
#        self.array.open()
#    #--- End: def

#--- End: class
