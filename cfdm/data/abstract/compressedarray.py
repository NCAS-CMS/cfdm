from future.utils import with_metaclass
from builtins import (range, super)

import abc

from .array import Array

_MUST_IMPLEMENT = 'This method must be implemented'


class CompressedArray(with_metaclass(abc.ABCMeta, Array)):
    '''A container for a compressed array.

The compressed array must be a subclass of `Array`.

It must be possible to derive the following from the compressed array:

  * Data-type of the array elements (see `dtype`)

  * An independent numpy array containing the uncompressed data (see
    `get_array`)

  * A uncompressed subspace of the array as an independent numpy array
    (see `__getitem__`)

The CF data model views compressed arrays in their uncompressed form,
so the following need to be provided as atttributes (as opposed to
being derived from the compressed array):

  * Number of uncompressed array dimensions (see `ndim`)
  
  * Uncompressed array dimension sizes (see `shape`)
  
  * Number of elements in the uncompressed array (see `size`)

  * The sample axis, i.e. which axis in the compressed array
    represents two or more uncompressed axes (see `sample_axis`)

See `cfdm.data.GatheredArray` for an example implementation.

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, sample_axis=None, **kwargs):
        '''**Initialization**

:Parameters:

    compressed_array: `Array`
        The compressed array.

    shape: `tuple`
        The uncompressed array dimension sizes.

    size: `int`
        Number of elements in the uncompressed array.

    ndim: `int`
        The number of uncompressed array dimensions

    sample_axis: `int`
        The position of the compressed axis in the compressed array.

    kwargs: *optional*
        Further attributes that may be required to uncompress the
        compressed array.

        '''
        super().__init__(compressed_array=compressed_array,
                         _shape=shape, _size=size, _ndim=ndim,
                         _sample_axis=sample_axis, **kwargs)
    #--- End: def

    @abc.abstractmethod
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns an uncompressed subspace of the compressed array as an
independent numpy array.

The indices that define the subspace are relative to the full
uncompressed array and must be either `Ellipsis` or a sequence that
contains an index for each dimension. In the latter case, each
dimension's index must either be a `slice` object or a sequence of
integers.

        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def

    @property
    def ndim(self):
        '''The number of dimensions of the uncompressed data.

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
        '''Shape of the uncompressed data.

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
        '''Number of elements in the uncompressed data.

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
        '''Data-type of the data elements.

:Examples:

>>> a.dtype
dtype('float64')
>>> print(type(a.dtype))
<type 'numpy.dtype'>

        '''
        return self.compressed_array.dtype
    #--- End: def

#    def close(self):
#        self.compressed_array.close()
#    #--- End: def

    def compressed_axes(self):
        '''The axes of the uncompressed array that have been compressed.

:Returns:

    out: `list`
        The compressed axes described by their integer positions.

:Examples:

>>> c.ndim
4
>>> c.compressed_array.ndim
3
>>> c.compressed_axes()
[1, 2]

        '''
        sample_axis = self.sample_axis
        return list(range(sample_axis, self.ndim - (self.compressed_array.ndim - sample_axis - 1)))
    #--- End: def

    def get_array(self):
        '''Return an independent numpy array containing the uncompressed data.

:Returns:

    out: `numpy.ndarray`
        The uncompressed array.

:Examples:

>>> n = a.get_array()
>>> isinstance(n, numpy.ndarray)
True

        '''
        return self[...]
    #--- End: def

#    def open(self):
#        self.compressed_array.open()
#    #--- End: def

#--- End: class
