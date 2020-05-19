from future.utils import with_metaclass
from builtins import (range, super)

import abc

import numpy

from .array import Array


class CompressedArray(with_metaclass(abc.ABCMeta, Array)):
    '''Abstract base class for a container of an underlying compressed
    array.

    See `cfdm.GatheredArray` for an example implementation.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, compressed_dimension=None,
                 compression_type=None, **kwargs):
        '''**Initialization**

    :Parameters:

        compressed_array: subclass of `Array`
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

        kwargs: optional
            Further named parameters and their values needed to define
            the compressed array.

        '''
        super().__init__(shape=shape, size=size, ndim=ndim,
                         compressed_dimension=compressed_dimension,
                         compression_type=compression_type, **kwargs)

        self._set_compressed_Array(compressed_array, copy=False)

    @abc.abstractmethod
    def __getitem__(self, indices):
        '''Return an uncompressed subspace as an independent numpy array.

    x.__getitem__(indices) <==> x[indices]

    The indices that define the subspace are relative to the
    uncompressed array.

    Indexing follows rules that are very similar to the numpy indexing
    rules, the only differences being:

    * An integer index i takes the i-th element but does not reduce
      the rank by one.

    ..

    * When two or more dimensions' indices are sequences of integers
      then these indices work independently along each dimension
      (similar to the way vector subscripts work in Fortran). This is
      the same behaviour as indexing on a Variable object of the
      netCDF4 package.

    .. versionadded:: 1.7.0

        '''
        raise NotImplementedError() # pragma: no cover

    def _get_compressed_Array(self, default=ValueError()):
        '''TODO

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the array
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

            The compressed Array instance.

    **Examples:**

    >>> a = d.get_data(None)

        '''
        return self._get_component('compressed_Array', default)

    def _set_compressed_Array(self, array, copy=True):
        '''Set the compressed array.

    .. versionadded:: 1.7.0

    :Parameters:

        array: subclass of `cfdm.data.Array`
            The compressed data to be inserted.

    :Returns:

        `None`

    **Examples:**

    >>> d._set_compressed_Array(a)

        '''
        if copy:
            array = array.copy()

        self._set_component('compressed_Array', array, copy=False)

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def array(self):
        '''Return an independent numpy array containing the uncompressed data.

    :Returns:

        `numpy.ndarray`
            The uncompressed array.

    **Examples:**

    >>> n = a.array
    >>> isinstance(n, numpy.ndarray)
    True

        '''
        return self[...]

    @property
    def dtype(self):
        '''Data-type of the data elements.

    **Examples:**

    >>> a.dtype
    dtype('float64')
    >>> print(type(a.dtype))
    <type 'numpy.dtype'>

        '''
        return self._get_compressed_Array().dtype

    @property
    def ndim(self):
        '''The number of dimensions of the uncompressed data.

    **Examples:**

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

    @property
    def shape(self):
        '''Shape of the uncompressed data.

    **Examples:**

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

    @property
    def size(self):
        '''Number of elements in the uncompressed data.

    **Examples:**

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

    @property
    def compressed_array(self):
        '''Return an independent numpy array containing the compressed data.

    :Returns:

        `numpy.ndarray`
            The compressed array.

    **Examples:**

    >>> n = a.compressed_array
    >>> import numpy
    >>> isinstance(n, numpy.ndarray)
    True

        '''
        ca = self._get_compressed_Array(None)
        if ca is None:
            raise ValueError("There is no underlying compressed array")

        return ca.array

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def get_compressed_axes(self):
        '''Return axes that are compressed in the underlying array.

    :Returns:

        `list`
            The compressed axes described by their integer positions.

    **Examples:**

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

    def get_compressed_dimension(self, *default):
        '''Return the position of the compressed dimension in the compressed
    array.

    .. versionadded:: 1.7.0

    .. seealso:: `get_compressed_axearray`, `get_compressed_axes`,
                 `get_compressed_type`

    :Parameters:

        default: optional
            Return *default* if the underlying array is not
            compressed.

    :Returns:

        `int`
            The position of the compressed dimension in the compressed
            array. If the underlying is not compressed then *default*
            is returned, if provided.

    **Examples:**

    >>> i = d.get_compressed_dimension()

        '''
        return self._get_component('compressed_dimension', *default)

    @abc.abstractmethod
    def to_memory(self):
        '''TODO

    :Returns:
            TODO

    **Examples:**
         TODO
        '''
        self._set_compressed_Array(self._get_compressed_Array().to_memory())
        return self

    def source(self, default=ValueError()):
        '''TODO Return the underlying array object.

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the array
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

        subclass of `Array`
            TODO The underlying array object.

    **Examples:**

    >>> TODO

        '''
        return self._get_compressed_Array(default=default)

# --- End: class
