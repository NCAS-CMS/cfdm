from future.utils import with_metaclass
from builtins import (range, super)

import abc

import numpy

from .array import Array


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
    represents two or more uncompressed axes (see
    `get_compressed_dimension`)

See `cfdm.data.GatheredArray` for an example implementation.

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, compressed_dimension=None,
                 compression_type=None, **kwargs):
        '''**Initialization**

:Parameters:

    compressed_array:
        The compressed array. May be any object that exposes the
        `cfdm.data.abstract.Array` interface.

    shape: `tuple`
        The uncompressed array dimension sizes.

    size: `int`
        Number of elements in the uncompressed array.

    ndim: `int`
        The number of uncompressed array dimensions

    compressed_dimension: `int`
        The position of the compressed dimension in the compressed
        array.

    compression_type: `str`
        The type of compression.        
        
    kwargs: *optional*
        Further attributes that may be required to uncompress the
        compressed array.

        '''
        super().__init__(compressed_array=compressed_array,
                         shape=shape, size=size, ndim=ndim,
                         compressed_dimension=compressed_dimension,
                         compression_type=compression_type, **kwargs)
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
        raise NotImplementedError()
    #--- End: def

    def _set_compressed_Array(self, data, copy=True):
        '''Set the compressed array.

.. versionadded:: 1.7

:Parameters:

    data: `numpy` array_like or subclass of `cfdm.data.Array`
        The compressed data to be inserted.

:Returns:

    `None`

:Examples:

>>> d._set_compressed_Array(a)

        '''
        if not isinstance(data, Array):
            if not isinstance(data, numpy.ndarray):
                data = numpy.asanyarray(data)
                
            data = NumpyArray(data)

        super()._set_Array(data, copy=copy)
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
        return self._get_component('compressed_array').dtype
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
        return self._get_component('ndim')
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
        return self._get_component('shape')
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
        return self._get_component('size')
    #--- End: def

    def get_compressed_axes(self):
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
        compressed_dimension = self.get_compressed_dimension()
        compressed_ndim = self._get_component('compressed_array').ndim
        
        return list(range(compressed_dimension, self.ndim - (compressed_ndim - compressed_dimension - 1)))
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

    def get_compressed_array(self):
        '''Return an independent numpy array containing the compressed data.

:Returns:

    out: `numpy.ndarray`
        The compressed array.

:Examples:

>>> n = a.get_compressed_array()
>>> isinstance(n, numpy.ndarray)
True

        '''
        return self._get_component('compressed_array').get_array()
    #--- End: def

#--- End: class
