from future.utils import with_metaclass
from builtins import str

import abc

import numpy

from ...core.data import Array as core_Array


class Array(with_metaclass(abc.ABCMeta, core_Array)):
    '''Abstract base class for a container of an underlying array.

The form of the array is arbitrary and is defined by the
initialization parameters of a subclass of `Array`.

See `cfdm.NumpyArray` for an example implementation.

    '''
    @abc.abstractmethod
    def __getitem__(self, indices):
        '''Return a subspace as an independent numpy array.

x.__getitem__(indices) <==> x[indices]

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

    def __repr__(self):
        '''Called by the `repr` built-in function.

x.__repr__() <==> repr(x)

.. versionadded:: 1.7

        '''      
        return "<{0}: {1}>".format(self.__class__.__name__, str(self))
    #--- End: def
        
    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

.. versionadded:: 1.7

        '''
        return "shape={0}, dtype={1}".format(self.shape, self.dtype)
    #--- End: def

    def get_compression_type(self):
        '''The type of compression that has been applied to the underlying
array.

.. versionadded:: 1.7

:Returns:

    out: `str`
        The compression type. An empty string means that no
        compression has been applied.

:Examples:

>>> a.compression_type
''

>>> a.compression_type
'gathered'

>>> a.compression_type
'ragged contiguous'

        '''
        return self._get_component('compression_type', '')
    #--- End: def

    def get_compressed_array(self, *default):
        '''Return an independent numpy array containing of the underlying
compressed array.

.. versionadded:: 1.7

:Returns:

    out: `numpy.ndarray`
        The compressed array.

:Examples:

>>> n = a.get_compressed_array()
>>> isinstance(n, numpy.ndarray)
True

        '''
        return self._get_component('compressed_array').get_compressed_array()
    #--- End: def
    
    def get_compressed_axes(self):
        '''Return axes that are compressed in the underlying array.

.. versionadded:: 1.7

:Returns:

    out: `list`
        The compressed axes described by their integer positions in
        the list of uncompressed axes. If no axes have been compressed
        then the list is empty.

:Examples:

        '''
        return []
    #--- End: def

    def get_compressed_dimension(self, *default):
        '''Return the position of the compressed dimension in the compressed
array.

.. versionadded:: 1.7

.. seealso:: `get_compressed_axearray`, `get_compressed_axes`,
             `get_compressed_type`

:Parameters:

    default: optional
        Return *default* if the underlying array is not compressed.

:Returns:

    out: `int`
        The position of the compressed dimension in the compressed
        array. If the underlying is not compressed then *default* is
        returned, if provided.

**Examples:**

>>> i = d.get_compressed_dimension()

        '''
        return self._get_component('compressed_dimension', *default)
    #--- End: def

    @classmethod
    def get_subspace(cls, array, indices, copy=True):
        '''Return a subspace, defined by indices, of a numpy array.

Only certain type of indices are allowed. See the *indices* parameter
for details.

Indexing is similar to numpy indexing. Given the restrictions on the
type of indices allowed - see the *indicies* parameter - the only
difference to numpy indexing is

  * When two or more dimension's indices are sequences of integers
    then these indices work independently along each dimension
    (similar to the way vector subscripts work in Fortran).

.. versionadded:: 1.7

:Parameters:

    array: `numpy.ndarray`
        The array to be subspaced.
        
    indices: 
        The indices that define the subspace.
     ..
        Must be either `Ellipsis` or a sequence that contains an index
        for each dimension. In the latter case, each dimension's index
        must either be a `slice` object or a sequence of two or more
        integers.

          *Example:*
            indices=Ellipsis
  
          *Example:*
            indices=[[5, 7, 8]]
  
          *Example:*
            indices=[slice(4, 7)]

          *Example:*
            indices=[slice(None), [5, 7, 8]]
  
          *Example:*
            indices=[[2, 5, 6], slice(15, 4, -2), [8, 7, 5]]

    copy: `bool`
        If `False` then the returned subspace may (or may not) be
        independent of the input *array*. By default the returned
        subspace is independent of the input *array*.

:Returns:

    out: `numpy.ndarray`

        '''
        if indices is not Ellipsis:
#        if indices is Ellipsis:
#            pass
#        elif not isinstance(indices, tuple):
#            array = array[indices]
#        else:
            axes_with_list_indices = [i for i, x in enumerate(indices)
                                      if not isinstance(x, slice)]
            n_axes_with_list_indices = len(axes_with_list_indices)
        
            if n_axes_with_list_indices < 2:
                # ----------------------------------------------------
                # At most one axis has a list-of-integers index so we
                # can do a normal numpy subspace
                # ----------------------------------------------------
                array = array[tuple(indices)]
            else:
                # ----------------------------------------------------
                # At least two axes have list-of-integers indices so
                # we can't do a normal numpy subspace
                # ----------------------------------------------------
                if numpy.ma.isMA(array):
                    take = numpy.ma.take
                else:
                    take = numpy.take
        
                indices = list(indices)
                for axis in axes_with_list_indices:
                    array = take(array, indices[axis], axis=axis)
                    indices[axis] = slice(None)
        
                if n_axes_with_list_indices < len(indices):
                    # Apply subspace defined by slices
                    array = array[tuple(indices)]
        #--- End: if

        if copy:
            if numpy.ma.isMA(array) and not array.ndim:
                # This is because numpy.ma.copy doesn't work for
                # scalar arrays (at the moment, at least)
                ma_array = numpy.ma.empty((), dtype=array.dtype)
                ma_array[...] = array
                array = ma_array
            else:
                array = array.copy()
        #--- End: if
        
        return array                
    #--- End: def

#--- End: class
