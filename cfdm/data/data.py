import itertools
import operator

import numpy
import netCDF4

from ..constants  import masked

from ..functions  import RTOL, ATOL, _numpy_allclose

from .array      import Array
from .numpyarray import NumpyArray

from ..structure import Data as structure_Data

# ====================================================================
#
# Data object
#
# ====================================================================

class Data(structure_Data):
    '''

An N-dimensional data array with units and masked values.

* Contains an N-dimensional, indexable and broadcastable array with
  many similarities to a `numpy` array.

* Contains the units of the array elements.

* Supports masked arrays, regardless of whether or not it was
  initialised with a masked array.

**Indexing**

A data array is indexable in a similar way to numpy array:

>>> d.shape
(12, 19, 73, 96)
>>> d[...].shape
(12, 19, 73, 96)
>>> d[slice(0, 9), 10:0:-2, :, :].shape
(9, 5, 73, 96)

There are three extensions to the numpy indexing functionality:

* Size 1 dimensions are never removed by indexing.

  An integer index i takes the i-th element but does not reduce the
  rank of the output array by one:

  >>> d.shape
  (12, 19, 73, 96)
  >>> d[0, ...].shape
  (1, 19, 73, 96)
  >>> d[:, 3, slice(10, 0, -2), 95].shape
  (12, 1, 5, 1)

  Size 1 dimensions may be removed with the `squeeze` method.

* The indices for each axis work independently.

  When more than one dimension's slice is a 1-d boolean sequence or
  1-d sequence of integers, then these indices work independently
  along each dimension (similar to the way vector subscripts work in
  Fortran), rather than by their elements:

  >>> d.shape
  (12, 19, 73, 96)
  >>> d[0, :, [0, 1], [0, 13, 27]].shape
  (1, 19, 2, 3)

* Boolean indices may be any object which exposes the numpy array
  interface.

  >>> d.shape
  (12, 19, 73, 96)
  >>> d[..., d[0, 0, 0]>d[0, 0, 0].min()]

    '''

    def __init__(self, data=None, units=None, calendar=None,
                 fill_value=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    data: array-like, optional
        The data for the array.

    fill_value: optional 
        The fill value of the data. By default, or if None, the numpy
        fill value appropriate to the array's data type will be used.

:Examples:

>>> d = Data(5)
>>> d = Data([1,2,3])
>>> import numpy   
>>> d = Data(numpy.arange(10).reshape(2, 5), fill_value=-999)
>>> d = Data(tuple('fly'))

        '''
        if data is not None and not isinstance(data, Array):
            if not isinstance(data, numpy.ndarray):
                data = numpy.asanyarray(data)
                
            data = NumpyArray(data)
        #-- End: if

        super(Data, self).__init__(data=data, units=units,
                                   calendar=calendar,
                                   fill_value=fill_value,
                                   source=source, copy=copy)
                                   
        # The _HDF_chunks attribute is.... Is either None or a
        # dictionary. DO NOT CHANGE IN PLACE.
#        self._HDF_chunks = {}
    #--- End: def
                                   
    def __data__(self):
        '''Return self

        '''
        return self
    #--- End: def
 
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

        '''
        array = self._get_master_array()
        return type(self)(array[indices], units=self.get_units(None),
                          calendar=self.get_calendar(None),
                          fill_value=self.get_fill_value(None))
    #--- End: def

    def __int__(self):
        '''x.__int__() <==> int(x)

        '''
        if self.size != 1:
            raise TypeError(
"only length-1 arrays can be converted to Python scalars. Got {}".format(self))

        array = self.get_array()
        return int(array)
    #--- End: def

    def __iter__(self):
        '''x.__iter__() <==> iter(x)

:Examples:

>>> d = Data([1, 2, 3], 'metres')
>>> for i in d:
...    print repr(i), type(i)
...
1 <type 'int'>
2 <type 'int'>
3 <type 'int'>

>>> d = Data([[1, 2], [4, 5]], 'metres')
>>> for e in d:
...    print repr(e)
...
<Data: [1, 2] metres>
<Data: [4, 5] metres>

>>> d = Data(34, 'metres')
>>> for e in d:
...     print repr(e)
...
TypeError: iteration over a 0-d Data

        '''
        ndim = self.ndim

        if not ndim:
            raise TypeError(
                "Iteration over 0-d {}".format(self.__class__.__name__))
            
        if ndim == 1:
            array = self.get_array()
            i = iter(array)
            while 1:
                yield i.next()
        else:
            # ndim > 1
            for n in range(self.shape[0]):
                yield self[n, ...].squeeze(0, copy=False)
    #--- End: def

    def __setitem__(self, indices, value):
        '''Implement indexed assignment

x.__setitem__(indices, y) <==> x[indices]=y

Assignment to data array elements defined by indices.

Elements of a data array may be changed by assigning values to a
subspace. See `__getitem__` for details on how to define subspace of
the data array.

**Missing data**

The treatment of missing data elements during assignment to a subspace
depends on the value of the `hardmask` attribute. If it is True then
masked elements will notbe unmasked, otherwise masked elements may be
set to any value.

In either case, unmasked elements may be set, (including missing
data).

Unmasked elements may be set to missing data by assignment to the
`masked` constant or by assignment to a value which contains masked
elements.

.. seealso:: `masked`

:Examples:

        '''
        array = self.get_array()

        if value is masked or numpy.ma.isMA(value):
            # The data is not masked and the assignment is masking
            # elements, so turn the non-masked array into a masked
            # one.
            array = array.view(numpy.ma.MaskedArray)
            
        indices = self.parse_indices(indices)

        self._set_subspace(array, indices, numpy.asanyarray(value))

        self._set_master_array(NumpyArray(array))
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        units    = self.get_units(None)
        calendar = self.get_calendar(None)

        if units is not None:
            isreftime = ('since' in units)
        else:
            isreftime = False

        try:
            first = self.first_element()
        except:            
            out = ''
            if units:
                out += ' {0}'.format(units)
            if calendar:
                out += ' {0}'.format(calendar)
               
            return out
        #--- End: try

        size = self.size
        ndim = self.ndim
        open_brackets  = '[' * ndim
        close_brackets = ']' * ndim

        if size == 1:
            if isreftime:
                # Convert reference time to date-time
                try:
                    first = type(self)(
                        numpy.ma.array(first), units, calendar).get_dtarray()
                except OverflowError:
                    first = '??'

            out = '{0}{1}{2}'.format(open_brackets,
                                     first,
                                     close_brackets)
        else:
            last = self.last_element()
            if isreftime:
                # Convert reference times to date-times
                try:
                    first, last = type(self)(
                        numpy.ma.array([first, last]), units, calendar).get_dtarray()
                except OverflowError:
                    first, last = ('??', '??')
            if size > 3:
                out = '{0}{1}, ..., {2}{3}'.format(open_brackets,
                                                   first,last,
                                                   close_brackets)
            elif size == 3:                
                middle = self.second_element()
                if isreftime:
                    # Convert reference times to date-times
                    try:
                        middle = type(self)(
                            numpy.ma.array(middle), units, calendar).get_dtarray()
                    except OverflowError:
                        middle = '??'
                        
                out = '{0}{1}, {2}, {3}{4}'.format(open_brackets,
                                                   first, middle, last,
                                                   close_brackets)
            else:
                out = '{0}{1}, {2}{3}'.format(open_brackets,
                                              first, last,
                                              close_brackets)
        #--- End: if
        
        if isreftime:
            if calendar:
                out += ' {0}'.format(calendar)
        elif units:
            out += ' {0}'.format(units)
            
        return out
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute
    # ----------------------------------------------------------------
    @property
    def dtype(self):
        '''The `numpy` data type of the data.

Setting the data type to a `numpy.dtype` object (or any object
convertible to a `numpy.dtype` object, such as the string
``'int32'``), will cause the data array elements to be recast to the
specified type.

.. versionadded:: 1.6

:Examples:

>>> d.dtype
dtype('float64')
>>> type(d.dtype)
<type 'numpy.dtype'>

>>> d = Data([0.5, 1.5, 2.5])
>>> print d.array
[0.5 1.5 2.5]
>>> import numpy
>>> d.dtype = numpy.dtype(int)
>>> print d.array
[0 1 2]
>>> d.dtype = bool
>>> print d.array
[False  True  True]
>>> d.dtype = 'float64'
>>> print d.array
[ 0.  1.  1.]

        '''
        return self._get_master_array().dtype
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute
    # ----------------------------------------------------------------
    @property
    def fill_value(self):
        '''

The data array missing data value.

If set to None then the default numpy fill value appropriate to the
data array's data type will be used.

Deleting this attribute is equivalent to setting it to None, so this
attribute is guaranteed to always exist.

:Examples:

>>> d.fill_value = 9999.0
>>> d.fill_value
9999.0
>>> del d.fill_value
>>> d.fill_value
None

'''
        return self._fill_value
    #--- End: def
    @fill_value.setter
    def fill_value(self, value): self._fill_value = value
    @fill_value.deleter
    def fill_value(self)       : self._fill_value = None

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def array(self):
        '''A numpy array copy the data.

.. note:: If the data array is stored as date-time objects then a
          numpy array of numeric reference times will be returned. A
          numpy array of date-time objects may be returned by the
          `dtarray` attribute.

.. seealso:: `dtarray`

:Examples:

>>> d = Data([1, 2, 3.0], 'km')
>>> a = d.array
>>> isinstance(a, numpy.ndarray)
True
>>> print a
[ 1.  2.  3.]
>>> d[0] = -99 
>>> print a[0] 
1.0
>>> a[0] = 88
>>> print d[0]
-99.0 km

        '''
        array = self.varray
        
        if numpy.ma.isMA(array) and not self.ndim:
            # This is because numpy.ma.copy doesn't work for
            # scalar arrays (at the moment, at least)
            temp = numpy.ma.masked_all((), dtype=array.dtype)
            temp[...] = array
            array = temp
        else:
            array = array.copy()

        return array
    #--- End: def

    @classmethod
    def asdata(cls, d, copy=False):
        '''Convert the input to a `Data` object.

:Parameters:

    d: data-like
        Input data in any form that can be converted to an `Data`
        object. This includes `Data` and `Field` objects, numpy arrays
        and any object which may be converted to a numpy array.

:Returns:

    out: `Data`
        The `Data` interpretation of *d*. No copy is performed on the
        input.

:Examples:

>>> d = Data([1, 2])
>>> Data.asdata(d) is d
True
>>> d.asdata(d) is d
True

>>> Data.asdata([1, 2])
<Data: [1, 2]>

>>> Data.asdata(numpy.array([1, 2]))
<Data: [1, 2]>

        '''
        __data__ = getattr(d, '__data__', None)
        if __data__ is None:
            return cls(d)

        data = __data__()
        if copy:
            return data.copy()
        else:
            return data
    #--- End: def

    def get_dtarray(self):
        '''
        '''
        array = self.get_array()

        mask = None
        if numpy.ma.isMA(array):
            # num2date has issues if the mask is nomask
            mask = array.mask
            if mask is numpy.ma.nomask or not numpy.ma.is_masked(array):
                array = array.view(numpy.ndarray)
        #--- End: if

#        calendar = self.get_calendar('standard')
#        if calendar is None:
#            calendar = 'standard'
#        print  'array=', array
#        try:
        array = netCDF4.num2date(array, units=self.get_units(None),
                                 calendar=self.get_calendar('standard'))
#        except OverflowError:
            
        if mask is None:
            # There is no missing data
            array = numpy.array(array, dtype=object)
        else:
            # There is missing data
            array = numpy.ma.masked_where(mask, array)
            if not numpy.ndim(array):
                array = numpy.ma.masked_all((), dtype=object)

        return array
    #--- End: def

    def parse_indices(self, indices):
        '''
    
:Parameters:
    
    indices: `tuple` (not a `list`!)
    
:Returns:
    
    out: `list`
    
:Examples:
    
    '''
        shape = self.shape
        
        parsed_indices = []
        roll           = {}
        flip           = []
        compressed_indices = []
    
        if not isinstance(indices, tuple):
            indices = (indices,)
    
        # Initialize the list of parsed indices as the input indices with any
        # Ellipsis objects expanded
        length = len(indices)
        n = len(shape)
        ndim = n
        for index in indices:
            if index is Ellipsis:
                m = n - length + 1
                parsed_indices.extend([slice(None)] * m)
                n -= m            
            else:
                parsed_indices.append(index)
                n -= 1
    
            length -= 1
        #--- End: for
        len_parsed_indices = len(parsed_indices)
    
        if ndim and len_parsed_indices > ndim:
            raise IndexError("Invalid indices %s for array with shape %s" %
                             (parsed_indices, shape))
    
        if len_parsed_indices < ndim:
            parsed_indices.extend([slice(None)]*(ndim-len_parsed_indices))
    
        if not ndim and parsed_indices:
            raise IndexError("Scalar array can only be indexed with () or Ellipsis")
    
        for i, (index, size) in enumerate(zip(parsed_indices, shape)):
            if isinstance(index, slice):            
                continue
    
            if isinstance(index, (int, long)):
                if index < 0: 
                    index += size
    
                index = slice(index, index+1, 1)
            else:
                if getattr(getattr(index, 'dtype', None), 'kind', None) == 'b':
                    # Convert booleans to non-negative integers. We're
                    # assuming that anything with a dtype attribute also
                    # has a size attribute.
                    if index.size != size:
                        raise IndexError(
    "Invalid indices {} for array with shape {}".format(parsed_indices, shape))
                    
                    index = numpy.where(index)[0]
                #--- End: if
    
                if not numpy.ndim(index):
                    if index < 0:
                        index += size
    
                    index = slice(index, index+1, 1)
                else:
                    len_index = len(index)
                    if len_index == 1:                
                        index = index[0]
                        if index < 0:
                            index += size
                        
                        index = slice(index, index+1, 1)
                    else:
                        raise IndexError(
                            "Invalid indices {} for array with shape {}".format(
                                parsed_indices, shape))                
                #--- End: if
            #--- End: if
            
            parsed_indices[i] = index    
        #--- End: for
    
        return parsed_indices
    #--- End: def

    def allclose(self, y, rtol=None, atol=None):
        '''Returns True if two broadcastable arrays have equal values, False
otherwise.

For numeric data arrays ``d.allclose(y, rtol, atol)`` is equivalent to
``(abs(d - y) <= atol + rtol*abs(y)).all()``, otherwise it is
equivalent to ``(d == y).all()``.

.. seealso:: `all`, `any`, `isclose`

:Parameters:

    y: data_like

    atol: `float`, optional
        The absolute tolerance for all numerical comparisons. By
        default the value returned by the `ATOL` function is used.

    rtol: `float`, optional
        The relative tolerance for all numerical comparisons. By
        default the value returned by the `RTOL` function is used.

:Returns:

     out: `bool`

:Examples:

>>> d = cf.Data([1000, 2500], 'metre')
>>> e = cf.Data([1, 2.5], 'km')
>>> d.allclose(e)
True

>>> d = cf.Data(['ab', 'cdef'])
>>> d.allclose([[['ab', 'cdef']]])
True

>>> d.allclose(e)
True

>>> d = cf.Data([[1000, 2500], [1000, 2500]], 'metre')
>>> e = cf.Data([1, 2.5], 'km')
>>> d.allclose(e)
True

>>> d = cf.Data([1, 1, 1], 's')
>>> d.allclose(1)
True

        '''  
        return self.isclose(y, atol=atol, rtol=rtol).varray.all()
    #--- End: def

    def isclose(self, y, rtol=None, atol=None):
        '''Return a boolean data array showing where two broadcastable arrays
have equal values within a tolerance.

For numeric data arrays, ``d.isclose(y, rtol, atol)`` is equivalent to
``abs(d - y) <= ``atol + rtol*abs(y)``, otherwise it is equivalent to
``d == y``.

:Parameters:

    y: data_like

    atol: `float`, optional
        The absolute tolerance for all numerical comparisons. By
        default the value returned by the `ATOL` function is used.

    rtol: `float`, optional
        The relative tolerance for all numerical comparisons. By
        default the value returned by the `RTOL` function is used.

:Returns:

     out: `Data`

:Examples:

>>> d = cf.Data([1000, 2500], 'metre')
>>> e = cf.Data([1, 2.5], 'km')
>>> print d.isclose(e).array
[ True  True]

>>> d = cf.Data(['ab', 'cdef'])
>>> print d.isclose([[['ab', 'cdef']]]).array
[[[ True  True]]]

>>> d = cf.Data([[1000, 2500], [1000, 2500]], 'metre')
>>> e = cf.Data([1, 2.5], 'km')
>>> print d.isclose(e).array
[[ True  True]
 [ True  True]]

>>> d = cf.Data([1, 1, 1], 's')
>>> print d.isclose(1).array
[ True  True  True]

        '''     
#        if isinstance(y, self.__class__):
#            if y.Units and y.Units != self.Units:
#                array = numpy.zeros(self.shape, dtype=bool)
#                return type(self)(array)
#        #--- End: if

        if atol is None:
            atol = ATOL()        
        if rtol is None:
            rtol = RTOL()

        y = numpy.asanyarray(y)

        array = numpy.isclose(self.varray, y, atol=atol, rtol=rtol)

        return type(self)(array)
    #--- End: def

#    def close(self):
#        '''
#'''
#        self._get_Array().close()
#    #--- End: def
#    
#    def open(self):
#        '''
#'''
#        self._get_Array().open()
#        self._get_Array().keep_open(True)
#    #--- End: def

    def copy(self):
        '''Return a deep copy.

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

:Returns:

    out: 
        The deep copy.

:Examples:

>>> e = d.copy()

        '''
        new = super(Data, self).copy()
#        new.HDF_chunks(self.HDF_chunks())
        return new
    #--- End: def

    def max(self, axes=None):
        '''Return the maximum of an array or the maximum along axes.

Missing data array elements are omitted from the calculation.

.. seealso:: `min`

:Parameters:

    axes: (sequence of) `int`, optional

:Returns:

    out: `Data`
        Maximum of the data along the specified axes.

:Examples:

        '''
        # Parse the axes. By default flattened input is used.
        if axes is not None:
            axes = self._parse_axes(axes, 'max')

        array = self.get_array()
        array = numpy.amax(array, axis=axes, keepdims=True)

        d = self.copy()
        d._set_master_array(NumpyArray(array))
        
#        if d._HDF_chunks:            
#            HDF = {}
#            for axis in axes:
#                HDF[axis] = None
#
#            d.HDF_chunks(HDF)
#        #--- End: if

        return d
    #--- End: def

    def min(self, axes=None):
        '''Return the minimum of an array or minimum along axes.

Missing data array elements are omitted from the calculation.

.. seealso:: `max`

:Parameters:

    axes: (sequence of) `int`, optional

:Returns:

    out: `Data`
        Minimum of the data along the specified axes.

:Examples:

        '''
        # Parse the axes. By default flattened input is used.
        if axes is not None:
            axes = self._parse_axes(axes, 'min')

        array = self.get_array()
        array = numpy.amin(array, axis=axes, keepdims=True)
            
        d = self.copy()
        d._set_master_array(NumpyArray(array))

#        if d._HDF_chunks:            
#            HDF = {}
#            for axis in axes:
#                HDF[axis] = None
#
#            d.HDF_chunks(HDF)
#        #--- End: if

        return d
    #--- End: def

    def ndindex(self):
        '''Return an iterator over the N-dimensional indices of the data.

At each iteration a tuple of indices is returned, the last (left hand)
dimension is iterated over first.

:Returns:

    out: iterator
        An iterator over tuples of indices of the data array.

:Examples:

>>> d.shape
(2, 1, 3)
>>> for i in d.ndindex():
...     print i
...
(0, 0, 0)
(0, 0, 1)
(0, 0, 2)
(1, 0, 0)
(1, 0, 1)
(1, 0, 2)

> d.shape
()
>>> for i in d.ndindex():
...     print i
...
()

        '''
        return itertools.product(*[range(0, r) for r in self.shape])  
    #--- End: def

    def sum(self, axes=None):
        '''Return the sum of an array or the sum along axes.

Missing data array elements are omitted from the calculation.

.. seealso:: `max`, `min`

:Parameters:

    axes: (sequence of) `int`, optional

:Returns:

    out: `Data`
        The sum of the data along the specified axes.

:Examples:

        '''
        # Parse the axes. By default flattened input is used.
        if axes is not None:
            axes = self._parse_axes(axes, 'sum')

        array = self.get_array()
        array = numpy.sum(array, axis=axes, keepdims=True)
            
        d = self.copy()
        d._set_master_array(NumpyArray(array))

#        if d._HDF_chunks:            
#            HDF = {}
#            for axis in axes:
#                HDF[axis] = None
#
#            d.HDF_chunks(HDF)
#        #--- End: if
        
        return d
    #--- End: def

#    def HDF_chunks(self, *chunks):
#        '''
#        '''
#        _HDF_chunks = self._HDF_chunks
#
#        org_HDF_chunks = dict([(i, _HDF_chunks.get(i))
#                               for i in range(self.ndim)])
#
#        org_HDF_chunks = _HDF_chunks.copy()
#        
#        if not chunks:
#            return org_HDF_chunks
#
##        if _HDF_chunks is None:
##            _HDF_chunks = {}
##        else:
##        _HDF_chunks = _HDF_chunks.copy()
#
##        org_HDF_chunks = _HDF_chunks.copy()
#            
# 
#        if not chunks:
#            return org_HDF_chunks
#
#        chunks = chunks[0]
#        
#        if chunks is None:
#            # Clear all chunking
#            self._HDF_chunks = {}
#            return org_HDF_chunks
#
##        for i in range(self.ndim):
#            
#
#        for axis, size in chunks.iteritems():
#            if size is not None:
#                _HDF_chunks[axis] = size
#            else:
#                _HDF_chunks.pop(axis, None)
#                
##        if _HDF_chunks.values() == [None] * len(_HDF_chunks):
##            _HDF_chunks = None
#
##        self._HDF_chunks = _HDF_chunks
#            
#        return org_HDF_chunks
#    #--- End: def

    def _parse_axes(self, axes, method):
        '''
        
:Parameters:

    axes : (sequence of) int
        The axes of the data array. May be one of, or a sequence of
        any combination of zero or more of:

            * The integer position of a dimension in the data array
              (negative indices allowed).

    method : str

:Returns:

    out: list

:Examples:

'''
        ndim = self.ndim

        if isinstance(axes, (int, long)):
            axes = (axes,)
            
        axes2 = []
        for axis in axes:
            if 0 <= axis < ndim:
                axes2.append(axis)
            elif -ndim <= axis < 0:
                axes2.append(axis + ndim)
            else:
                raise ValueError(
                    "Can't {}: Invalid axis: {!r}".format(method, axis))
        #--- End: for
            
        # Check for duplicate axes
        n = len(axes2)
        if n > 1 and n > len(set(axes2)):
            raise ValueError("Can't {}: Duplicate axis: {}".format(
                method, axes2))            
        
        return tuple(axes2)
    #--- End: def

    @classmethod
    def _set_subspace(cls, array, indices, value):
        '''
        '''
        gg = [i for i, x in enumerate(indices) if not isinstance(x, slice)]

        if len(gg) < 2: 
            # ------------------------------------------------------------
            # At most one axis has a list-of-integers index so we can do a
            # normal numpy assignment
            # ------------------------------------------------------------
            array[tuple(indices)] = value
        else:
            # ------------------------------------------------------------
            # At least two axes have list-of-integers indices so we can't
            # do a normal numpy assignment
            # ------------------------------------------------------------
            indices1 = indices[:]
            for i, x in enumerate(indices):
                if i in gg:
                    y = []
                    args = [iter(x)] * 2
                    for start, stop in itertools.izip_longest(*args):
                        if not stop:
                            y.append(slice(start, start+1))
                        else:
                            step = stop - start
                            stop += 1
                            y.append(slice(start, stop, step))
                    #--- End: for
                    indices1[i] = y
                else:
                    indices1[i] = (x,)
            #--- End: for
#            print 'indices1 =',    indices1
 
    #        if not numpy.ndim(value) :
            if numpy.size(value) == 1:
                for i in itertools.product(*indices1):
                    array[i] = value
                    
            else:
                indices2 = []
                ndim_difference = array.ndim - numpy.ndim(value)
                for i, n in enumerate(numpy.shape(value)):
                    if n == 1:
                        indices2.append((slice(None),))
                    elif i + ndim_difference in gg:
                        y = []
                        start = 0
                        while start < n:
                            stop = start + 2
                            y.append(slice(start, stop))
                            start = stop
                        #--- End: while
                        indices2.append(y)
                    else:
                        indices2.append((slice(None),))
                #--- End: for
#                print 'indices2 =',    indices2
                for i, j in zip(itertools.product(*indices1), itertools.product(*indices2)):
#                    print 'i, j =',i,j
                    array[i] = value[j]
    #--- End: def

    def squeeze(self, axes=None, copy=True):
        '''Remove size 1 axes from the data.

By default all size 1 axes are removed, but particular axes may be
selected with the keyword arguments.

.. versionadded:: 1.6

.. seealso:: `expand_dims`, `transpose`, `unsqueeze`

:Parameters:

    axes: (sequence of) `int`, optional
        Select the size 1 axes to be removed.  By default all size 1
        axes are removed. Axes are selected by their integer position
        in the dimensions of the data array. No axes are removed if
        *axes* is an empty sequence.

          *Example:*
            To remove all size 1 axes: ``d.squeeze()`` or
            ``d.squeeze(None)``.

          *Example:*
            To remove the size 1 axis in position 2 of a
            5-dimensionsal data array : ``d.squeeze(2)``
            or``d.squeeze(-3)``.

          *Example:*
            To remove the size 1 axes in positions 1 and 3:
            ``d.squeeze([1, 3])``.

    copy: `bool`, optional
        If False then update the data array in place. By default a new
        data array is created.

:Returns:

    out: `Data`
        The squeezed data.

:Examples:

>>> v.shape
(1,)
>>> v.squeeze()
>>> v.shape
()

>>> v.shape
(1, 2, 1, 3, 1, 4, 1, 5, 1, 6, 1)
>>> v.squeeze((0,))
>>> v.shape
(2, 1, 3, 1, 4, 1, 5, 1, 6, 1)
>>> v.squeeze(1)
>>> v.shape
(2, 3, 1, 4, 1, 5, 1, 6, 1)
>>> v.squeeze([2, 4])
>>> v.shape
(2, 3, 4, 5, 1, 6, 1)
>>> v.squeeze([])
>>> v.shape
(2, 3, 4, 5, 1, 6, 1)
>>> v.squeeze()
>>> v.shape
(2, 3, 4, 5, 6)

        '''
        if copy:
            d = self.copy()
        else:
            d = self

        if not d.ndim:
            if axes or axes == 0:
                raise ValueError(
"Can't squeeze: Can't remove an axis from scalar {}".format(d.__class__.__name__))
            return d
        #--- End: if

        shape = d.shape

        if axes is None:
            axes = [i for i, n in enumerate(shape) if n == 1]
        else:
            axes = d._parse_axes(axes, 'squeeze')
            
            # Check the squeeze axes
            for i in axes:
                if shape[i] > 1:
                    raise ValueError(
"Can't squeeze {}: Can't remove axis of size {}".format(d.__class__.__name__, shape[i]))
        #--- End: if

        if not axes:
            return d
        
        array = self.get_array()
        array = numpy.squeeze(array, axes)

        d._set_master_array(NumpyArray(array))

        return d
    #--- End: def

    def expand_dims(self, position=0, copy=True):
        '''Expand the shape of the data array.

Insert a new size 1 axis, corresponding to a given position in the
data array shape.

.. versionadded:: 1.6

.. seealso:: `squeeze`, `transpose`, `unsqueeze`

:Parameters:

    position: `int`, optional
        Specify the position that the new axis will have in the data
        array axes. By default the new axis has position 0, the
        slowest varying position.

    copy: `bool`, optional
        If False then update the data array in place. By default a new
        data array is created.

:Returns:

    out: `Data`

:Examples:

        '''
        # Parse position
        ndim = self.ndim 
        if -ndim-1 <= position < 0:
            position += ndim + 1
        elif not 0 <= position <= ndim:
            raise ValueError(
                "Can't expand_dims: Invalid position (%d)" % position)
        #--- End: for

        if copy:
            d = self.copy()
        else:
            d = self

        array = self.get_array()
        array = numpy.expand_dims(array, position)

        d._set_master_array(NumpyArray(array))

#        if d._HDF_chunks:            
#            HDF = {}
#            for axis in axes:
#                HDF[axis] = None
#
#            d.HDF_chunks(HDF)
#        #--- End: if

        return d
    #--- End: def

    def transpose(self, axes=None, copy=True):
        '''Permute the axes of the data array.

.. versionadded:: 1.6

.. seealso:: `expand_dims`, `squeeze`, `unsqueeze`

:Parameters:

    axes: (sequence of) `int`
        The new axis order of the data array. By default the order is
        reversed. Each axis of the new order is identified by its
        original integer position.

    copy: `bool`, optional
        If False then update the data array in place. By default a new
        data array is created.

:Returns:

    out: `Data`

:Examples:

>>> d.shape
(19, 73, 96)
>>> d.transpose()
>>> d.shape
(96, 73, 19)
>>> d.transpose([1, 0, 2])
>>> d.shape
(73, 96, 19)
>>> d.transpose((-1, 0, 1))
>>> d.shape
(19, 73, 96)

        '''
        if copy:
            d = self.copy()
        else:
            d = self

        ndim = d.ndim    
        
        # Parse the axes. By default, reverse the order of the axes.
        if axes is None:
            if ndim <= 1:
                return d

            axes = range(ndim-1, -1, -1)
        else:
            axes = d._parse_axes(axes, 'transpose')

            # Return unchanged if axes are in the same order as the data
            if axes == range(ndim):
                return d

            if len(axes) != ndim:
                raise ValueError(
                    "Can't transpose: Axes don't match array: {}".format(axes))
        #--- End: if

        array = self.get_array()
        array = numpy.transpose(array, axes=axes)
        
        d._set_master_array(NumpyArray(array))

        return d
    #--- End: def

    def unique(self):
        '''The unique elements of the data.

The unique elements are sorted into a one dimensional array. with no
missing values.

.. versionadded:: 1.6

:Returns:

    out: `Data`
        The unique elements.

:Examples:

>>> d = Data([[4, 2, 1], [1, 2, 3]], 'metre')
>>> d.unique()
<Data: [1, 2, 3, 4] metre>
>>> d[1, -1] = masked
>>> d.unique()
<Data: [1, 2, 4] metre>

        '''
        array = self.get_array()
        array = numpy.unique(array)

        if numpy.ma.is_masked(array):
            array = array.compressed()

        return type(self)(array, units=self.get_units(None),
                          calendar=self.get_calendar(None),
                          fill_value=self.get_fill_value(None))
    #--- End: def

    def dump(self, display=True, prefix=None):
        '''

Return a string containing a full description of the instance.

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``d.dump()`` is equivalent to
        ``print d.dump(display=False)``.

    prefix: `str`, optional
       Set the common prefix of component names. By default the
       instance's class name is used.

:Returns:

    out: `None` or `str`
        A string containing the description.

:Examples:

'''
        if prefix is None:
            prefix = self.__class__.__name__
            
        string = []
        for attr in ('ndim', 'shape', 'size', 'dtype', 'fill_value', 'array'):
            string.append('{0}.{1} = {2!r}'.format(prefix, attr, getattr(self, attr)))

        string = '\n'.join(string)
       
        if display:
            print string
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None,
               ignore_data_type=False, ignore_fill_value=False,
               traceback=False, _check_values=True):
        '''True if two `Data` objects are equal.

Two `Data` objects are equal if

  * The have the same shape

  * They have the same data type (unless *ignore_data_type* is True)

  * They have the same fill value (unless *ignore_fill_value* is True)

  * They have the same missing data mask

  * They have the same array values

:Parameters:

    other : 
        The object to compare for equality.

    atol: `float`, optional
        The absolute tolerance for all numerical comparisons. By
        default the value returned by the `ATOL` function is used.

    rtol: `float`, optional
        The relative tolerance for all numerical comparisons. By
        default the value returned by the `RTOL` function is used.

    ignore_fill_value: `bool`, optional
        If True then data with different fill values are considered
        equal. By default they are considered unequal.

    ignore_data_type: `bool`, optional
        If True then data with different data types are considered
        equal. By default they are considered unequal.

    traceback: `bool`, optional
        If True then print a traceback highlighting where the two
        instances differ.

:Returns: 

    out: bool
        Whether or not the two `Data` objects are equals.

:Examples:

>>> d.equals(d)
True
>>> d.equals(d + 1)
False
>>> d.equals(d.expand_dims())
False

        '''
        # Check each instance's id
        if self is other:
            return True
 
        # Check that each instance is the same type
        if self.__class__ != other.__class__:
            if traceback:
                print("{0}: Different type: {1}".format(
                    self.__class__.__name__, other.__class__.__name__))
            return False
        #--- End: if

        # Check that each instance has the same shape
        if self.shape != other.shape:
            if traceback:
                print("{0}: Different shapes: {1}, {2}".format(
                    self.__class__.__name__, self.shape, other.shape))
            return False
        #--- End: if

        # Check that each instance has the same units
        for attr in ('units', 'calendar'):
            x = getattr(self, 'get_'+attr)(None)
            y = getattr(other, 'get_'+attr)(None)
            if x != y:
                if traceback:
                    print("{0}: Different {1}: {2!r}, {3!r}".format(
                        self.__class__.__name__, attr, x, y))
                return False
        #--- End: for
           
        # Check that each instance has the same fill value
        if (not ignore_fill_value and
            self.get_fill_value(None) != other.get_fill_value(None)):
            if traceback:
                print("{0}: Different fill value: {1}, {2}".format(
                    self.__class__.__name__, 
                    self.get_fill_value(None), other.get_fill_value(None)))
            return False
        #--- End: if

        # Check that each instance has the same data type
        if not ignore_data_type and self.dtype != other.dtype:
            if traceback:
                print("{0}: Different data types: {1}, {2}".format(
                    self.__class__.__name__, self.dtype, other.dtype))
            return False
        #--- End: if

        # Return now if we have been asked to not check the array
        # values
        if not _check_values:
            return True

        # ------------------------------------------------------------
        # Check that each instance has equal array values
        # ------------------------------------------------------------
        # Set default tolerances
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()        

        if not _numpy_allclose(self.get_array(), other.get_array(),
                               rtol=rtol, atol=atol):
            if traceback:
                print("{0}: Different data array values".format(
                    self.__class__.__name__))
            return False

        # ------------------------------------------------------------
        # Still here? Then the two instances are equal.
        # ------------------------------------------------------------
        return True            
    #--- End: def

    def element(self, *index):
        '''
        '''
        if index:
            n_index = len(index)
            if n_index == 1:
                index = index[0]
                if index == 0:
                    # This also works for scalar arrays
                    index = (slice(0, 1),) * self.ndim
                elif index == -1:
                    # This also works for scalar arrays
                    index = (slice(-1, None),) * self.ndim
                elif isinstance(index, (int, long)):
                    if index < 0:
                        index += self.size

                    index = numpy.unravel_index(index, self.shape)
                elif len(index) != self.ndim:
                    raise ValueError(
                        "Incorrect number of indices for %s array" %
                        self.__class__.__name__)
                #--- End: if
            elif n_index != self.ndim:
                raise ValueError(
                    "Incorrect number of indices for %s array" %
                    self.__class__.__name__)

            array = self[index].get_array()

        elif self.size == 1:
            array = self.get_array()

        else:
            raise ValueError(
"Can only convert a {} array of size 1 to a Python scalar".format(
    self.__class__.__name__))

        if not numpy.ma.isMA(array):
            return array.item()
        
        mask = array.mask
        if mask is numpy.ma.nomask or not mask.item():
            return array.item()

        return numpy.ma.masked
    #--- End: def
    
    def first_element(self):
        '''
        '''
        d = self[(slice(0, 1),)*self.ndim]
        array = d.get_array()
        
        if not numpy.ma.isMA(array):
            return array.item()

        mask = array.mask
        if mask is numpy.ma.nomask or not mask.item():
            return array.item()

        return numpy.ma.masked        
    #--- End: def
    
    def last_element(self):
        '''
        '''
        d = self[(slice(-1, None),)*self.ndim]
        array = d.get_array()
        
        if not numpy.ma.isMA(array):
            return array.item()

        mask = array.mask
        if mask is numpy.ma.nomask or not mask.item():
            return array.item()

        return numpy.ma.masked
    #--- End: def
    
    def second_element(self):
        '''
        '''
        index = (slice(0, 1),)*(self.ndim-1) + (slice(1, 2),)
      
        array = self[index].get_array()

        if not numpy.ma.isMA(array):
            return array.item()

        mask = array.mask
        if mask is numpy.ma.nomask or not mask.item():
            return array.item()

        return numpy.ma.masked
    #--- End: def

    def set_dtype(self, value):
        '''
        '''
        value = numpy.dtype(value)
        if value != self.dtype:
            array = numpy.asanyarray(self.get_array(), dtype=value)
            self._set_master_array(NumpyArray(array))
    #--- End: def

#    # ----------------------------------------------------------------
#    # Compression class methods
#    # ----------------------------------------------------------------
#    @classmethod
#    def compression_initialize_gathered(cls, dtype,
#                                        uncompressed_shape):
#        '''Create an empty Data array
#        
#:Parameters:
#
#:Returns:
# 
#    out: `Data`
#
#        '''
#        array = numpy.ma.masked_all(uncompressed_shape, dtype=dtype)
#                   
#        return cls(array)
#    #--- End: def
#
#    @classmethod
#    def compression_initialize_indexed_contiguous(cls, dtype,
#                                                  instance_dimension_size,
#                                                  element_dimension_1_size,
#                                                  element_dimension_2_size,
#                                                  profiles_per_instance,
#                                                  elements_per_profile,
#                                                  profile_indices):
#        '''Create an empty Data array which has dimensions
#        (instance_dimension_size, element_dimension_1_size,
#        element_dimension_2_size)
#        
#:Parameters:
#
#    instance: `Data`
#        Number of instances
#
#    features_per_instance: `Data`
#        Number of features per instance
#
#    elements_per_feature: `Data`
#        Number of elements per feature
#
#    profile_indices: `Data`
#        The indices of the sample dimension which define the start
#        position of each profile of each instance.
#
#:Returns:
# 
#    out: `Data`
#
#        '''
#        array = numpy.ma.masked_all((instance_dimension_size,
#                                     element_dimension_1_size,
#                                     element_dimension_2_size), dtype=dtype)
#                   
#        return cls(array)
#    #--- End: def
#
#    @classmethod
#    def compression_initialize_contiguous(cls, dtype,
#                                          instance_dimension_size,
#                                          element_dimension_size,
#                                          elements_per_instance):
#        '''Create an empty Data array which has dimensions
#        (instance_dimension_size, element_dimension_size)
#
#:Parameters:
#
#    instance_dimension_size: `int`
#
#    element_dimension_size: `int`
#
#    elements_per_instance: data-like
#
#:Returns:
# 
#    out: `Data`
#
#        '''
#        array = numpy.ma.masked_all((instance_dimension_size,
#                                     element_dimension_size),
#                                    dtype=dtype)
#        
#        return cls(array)
#    #--- End: def
#
#    @classmethod
#    def compression_initialize_indexed(cls, dtype, instance_dimension_size,
#                                       element_dimension_size, index):
#        '''Create an empty Data array which has shape
#        (instance_dimension_size, element_dimension_size)
#
#:Parameters:
#
#    instance_dimension_size: `int`
#
#    element_dimension_size: `int`
#
#    index: data-like
#
#:Returns:
# 
#    out: `Data`
#
#        '''
#        array = numpy.ma.masked_all((instance_dimension_size,
#                                     element_dimension_size),
#                                    dtype=dtype)
#        
#        return cls(array)
#    #--- End: def
#
#    @classmethod
#    def compression_fill_gathered(cls, data, dtype, units, fill_value,
#                                  gathered_array, sample_axis, indices):
#        '''
#        
#    data: `Data`
#
#    gathered_array:
#        
#    sample_axes: `int`
#
#    indices: `Data`
#
#        '''
#        data.dtype = dtype
#
#        data.set_units(units)
#        data.set_calendar(calendar)
#        data.set_fill_value(fill_value)
#
#        uncompressed_array = data.varray 
#       
#        compressed_axes = range(sample_axis,
#                                uncompressed_array.ndim - (gathered_array.ndim - sample_axis - 1))
#        
#        zzz = [reduce(operator.mul, [uncompressed_array.shape[i]
#                                     for i in compressed_axes[i:]], 1)
#               for i in range(1, len(compressed_axes))]
#        
#        xxx = [[0] * indices.size for i in compressed_axes]
#
#
#        for n, b in enumerate(indices.varray):
#            if not zzz or b < zzz[-1]:
#                xxx[-1][n] = b
#                continue
#            
#            for i, z in enumerate(zzz):
#                if b >= z:
#                    (a, b) = divmod(b, z)
#                    xxx[i][n] = a
#                    xxx[-1][n] = b
#        #--- End: for
#
#        uncompressed_indices = [slice(None)] * uncompressed_array.ndim        
#        for i, x in enumerate(xxx):
#            uncompressed_indices[sample_axis+i] = x
#
#        uncompressed_array[tuple(uncompressed_indices)] = gathered_array[...]
#
#        return data
#    #--- End: def
#
#    @classmethod
#    def compression_fill_indexed(cls, data, dtype, units, fill_value,
#                                 ragged_array, index):
#        '''sdfsdfsd
#
#:Parameters:
#
#    data: `Data`
#        The `Data` object to filled as an incomplete orthogonal
#        array. The instance dimension must be in position 0 and the
#        element dimension must be in position 1.
# 
#    ragged_array: 
#        
#    index: `Data`
#
#        '''
#        data.dtype = dtype
#        data.Units = units
#        data.fill_value = fill_value
#
#        uncompressed_array = data.varray
#
#        for i in range(uncompressed_array.shape[0]): #index.unique():
#            sample_dimension_indices = numpy.where(index == i)[0]
#            
#            indices = (slice(i, i+1),
#                       slice(0, len(sample_dimension_indices)))
#
#            uncompressed_array[indices] = ragged_array[sample_dimension_indices]
#        #--- End: for
#
#        return data
#    #--- End: def
#
#    @classmethod
#    def compression_fill_contiguous(cls, data, dtype, units,
#                                    fill_value, ragged_array,
#                                    elements_per_feature):
#        '''
#        
#    data: `Data`
#
#    ragged_array:
#        
#    elements_per_feature: `Data`
#
#        '''
#        data.dtype = dtype
#        data.Units = units
#        data.fill_value = fill_value
#
#        uncompressed_array = data.varray 
#
#        start = 0 
#        for i, n in enumerate(elements_per_feature):
#            n = int(n)
#            sample_indices = slice(start, start + n)
#
#            indices = (slice(i, i+1),
#                       slice(0, sample_indices.stop - sample_indices.start))
#                             
#            uncompressed_array[indices ] = ragged_array[sample_indices]
#                             
#            start += n
#        #--- End: for
#
#        return data
#    #--- End: def
#
#    @classmethod
#    def compression_fill_indexed_contiguous(cls, data, dtype, units,
#                                            fill_value, ragged_array,
#                                            profiles_per_instance,
#                                            elements_per_profile,
#                                            profile_indices):
#        '''
#        
#    data: `Data`
#
#    ragged_array: array-like
#        
#    profiles_per_instance: `Data`
#
#    elements_per_profile: `Data`
#
#    profile_indices: `Data`
#        The indices of the sample dimension which define the start
#        position of each profile of each instance.
#
#        '''
#        print 'elements_per_profile.shape =',elements_per_profile.shape
#        data.dtype = dtype
#        data.Units = units
#        data.fill_value = fill_value
#
#        uncompressed_array = data.varray 
#
#        # Loop over instances
#        for i in range(uncompressed_array.shape[0]):
#
#            # For all of the profiles in ths instance, find the
#            # locations in the elements_per_profile array of the
#            # number of elements in the profile
#            xprofile_indices = numpy.where(profile_indices == i)[0]
#
#            # Find the number of profiles in this instance
#            n_profiles = xprofile_indices.size
#
#            # Loop over profiles in this instance
#            for j in range(uncompressed_array.shape[1]):
#                print 'j=',j
#                if j >= n_profiles:
#                    continue
#                
#                # Find the location in the elements_per_profile array
#                # of the number of elements in this profile
#                profile_index = xprofile_indices[j]
#
#                if profile_index == 0:
#                    start = 0
#                else:                    
#                    start = int(elements_per_profile[:profile_index].sum())
#
#                print profile_index, elements_per_profile.shape,  elements_per_profile[j, profile_index], elements_per_profile
#                stop  = start + int(elements_per_profile[j, profile_index])
#                
#                sample_indices = slice(start, stop)
#                
#                indices = (slice(i, i+1),
#                           slice(j, j+1), 
#                           slice(0, sample_indices.stop - sample_indices.start))
#                
#                uncompressed_array[indices] = ragged_array[sample_indices]
#        #--- End: for
#
#        return data
#    #--- End: def

#--- End: class

