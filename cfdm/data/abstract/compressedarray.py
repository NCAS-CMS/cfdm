from future.utils import with_metaclass
from builtins import (range, super)

import abc

import numpy

from .array import Array


class CompressedArray(with_metaclass(abc.ABCMeta, Array)):
    '''Abstract base class for a container of an underlying compressed
array

See `cfdm.GatheredArray` for an example implementation.

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, compressed_dimension=None,
                 compression_type=None, **kwargs):
        '''**Initialization**

:Parameters:

    compressed_array: numpy array or subclass of `Array`
        The compressed array.

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
        Further named parameters and their values needed to define the
        compressed array.

        '''
        super().__init__(shape=shape, size=size, ndim=ndim,
                         compressed_dimension=compressed_dimension,
                         compression_type=compression_type, **kwargs)

        self._set_compressed_Array(compressed_array)
    #--- End: def

    @abc.abstractmethod
    def __getitem__(self, indices):
        '''Return an uncompressed subspace as an independent numpy array.

x.__getitem__(indices) <==> x[indices]

The indices that define the subspace are relative to the uncompressed
array.

Indexing follows rules that are very similar to the numpy indexing
rules, the only differences being:

* An integer index i takes the i-th element but does not reduce the
  rank by one.

..

* When two or more dimensions' indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same
  behaviour as indexing on a Variable object of the netCDF4 package.

.. versionadded:: 1.7

        '''
        raise NotImplementedError()
    #--- End: def

    def _get_compressed_Array(self, *default):
        '''TODO

:Parameters:

    default: *optional*
        If there is no data then *default* if returned if set.

:Returns:

    out:
        The data. If the data has not been set then *default* is
        returned, if set.

**Examples:**

>>> a = d.get_data(None)

        '''
        array = self._get_component('compressed_Array', None)

        if array is None:
            if default:
                return default[0]     

            raise AttributeError("{!r} has no data".format(
                self.__class__.__name__))
        
        return array   
    #--- End: def

    def _set_compressed_Array(self, array, copy=True):
        '''Set the compressed array.

.. versionadded:: 1.7

:Parameters:

    array: `numpy` array_like or subclass of `cfdm.data.Array`
        The compressed data to be inserted.

:Returns:

    `None`

:Examples:

>>> d._set_compressed_Array(a)

        '''
        if not isinstance(array, Array):
            raise TypeError("asdads  0000000000000000000")
#            if not isinstance(array, numpy.ndarray):
#                data = numpy.asanyarray(array)
#                
#            array = NumpyArray(array)

        if copy:
            array = array.copy()

        self._set_component('compressed_Array', array, copy=False)
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
        return self._get_compressed_Array().dtype
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
        '''Return axes that are compressed in the underlying array.

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
        compressed_ndim = self._get_compressed_Array().ndim
        
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
        return self._get_compressed_Array().get_array()
    #--- End: def

#--- End: class
