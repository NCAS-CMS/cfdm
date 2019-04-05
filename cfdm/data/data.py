from __future__ import print_function
from builtins import (range, super, zip)

import itertools

import numpy
import netCDF4

from .. import core
from .. import mixin

from ..constants  import masked

from . import abstract
from . import NumpyArray


class Data(mixin.Container,
           mixin.NetCDFHDF5,
           core.Data):
    '''An orthogonal multidimensional array with masked values and units.

.. versionadded:: 1.7.0

    '''
    def __init__(self, array=None, units=None, calendar=None,
                 fill_value=None, source=None, copy=True,
                 _use_array=True):
        '''**Initialization**

:Parameters:

    array: numpy array-like or subclass of `Array`, optional
        The array of values. Ignored if the *source* parameter is set.

        *Parameter example:*
          ``array=[34.6]``

        *Parameter example:*
          ``array=[[1, 2], [3, 4]]``

        *Parameter example:*
          ``array=numpy.ma.arange(10).reshape(2, 1, 5)``

    units: `str`, optional
        The physical units of the data. Ignored if the *source*
        parameter is set.

        *Parameter example:*
          ``units='km hr-1'``

        *Parameter example:*
          ``units='days since 2018-12-01'``

        The units may also be set after initialisation with the
        `set_units` method.

    calendar: `str`, optional
        The calendar for reference time units. Ignored if the *source*
        parameter is set.

        *Parameter example:*
          ``calendar='360_day'``
        
        The calendar may also be set after initialisation with the
        `set_calendar` method.

    fill_value: optional 
        The fill value of the data. By default, or if set to `None`,
        the `numpy` fill value appropriate to the array's data type
        will be used (see `numpy.ma.default_fill_value`). Ignored if
        the *source* parameter is set.

        *Parameter example:*
          ``fill_value=-999.``
                
        The fill value may also be set after initialisation with the
        `set_fill_value` method.

    source: optional
        Initialize the array, units, calendar and fill value from
        those of *source*.

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__(array=array, units=units, calendar=calendar,
                         fill_value=fill_value, source=source,
                         copy=copy, _use_array=_use_array)

        self._initialise_netcdf(source)
    #--- End: def
                 
    def __array__(self, *dtype):
        '''The numpy array interface.

.. versionadded:: 1.7.0

:Parameters:

    dtype: optional
        Typecode or data-type to which the array is cast.

:Returns: 

    `numpy.ndarray`
        An independent numpy array of the data.

**Examples:**

>>> import numpy
>>> d = cfdm.Data([1, 2, 3])
>>> a = numpy.array(d)
>>> print(type(a))
<type 'numpy.ndarray'>
>>> a[0] = -99
>>> d
<Data(3): [1, 2, 3]>
>>> b = numpy.array(d, float)
>>> print(b)
[ 1.  2.  3.]

        '''
        array = self.array
        if not dtype:
            return array
        else:
            return array.astype(dtype[0], copy=False)
    #--- End: def
              
    def __repr__(self):
        '''Called by the `repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        try:        
            shape = self.shape
        except AttributeError:
            shape = ''
        else:
            shape = str(shape)
            shape = shape.replace(',)', ')')
            
        return '<{0}{1}: {2}>'.format(self.__class__.__name__, shape, str(self))
    #--- End: def
   
    def __getitem__(self, indices):
        '''Return a subspace of the data defined by indices

d.__getitem__(indices) <==> d[indices]

Indexing follows rules that are very similar to the numpy indexing
rules, the only differences being:

* An integer index i takes the i-th element but does not reduce the
  rank by one.

* When two or more dimensions' indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same
  behaviour as indexing on a Variable object of the netCDF4 package.

.. versionadded:: 1.7.0

.. seealso:: `__setitem__`, `_parse_indices`

:Returns:

    `Data`
        The subspace of the data.

**Examples:**

>>> import numpy
>>> d = cfdm.Data(numpy.arange(100, 190).reshape(1, 10, 9))
>>> d.shape
(1, 10, 9)
>>> d[:, :, 1].shape
(1, 10, 1)
>>> d[:, 0].shape
(1, 1, 9)
>>> d[..., 6:3:-1, 3:6].shape
(1, 3, 3)
>>> d[0, [2, 9], [4, 8]].shape
(1, 2, 2)
>>> d[0, :, -2].shape
(1, 10, 1)

        '''
        indices = tuple(self._parse_indices(indices))

        array = self._get_Array(None)
        if array is None:
            raise ValueError("No array!!")
            
        array = array[indices]

        out = self.copy(array=False)
        out._set_Array(array, copy=False)

        if out.shape != self.shape:
            # Delete hdf5 chunksizes
            out.nc_clear_hdf5_chunksizes()
        
        return out
    #--- End: def

    def __int__(self):
        '''x.__int__() <==> int(x)

        '''
        if self.size != 1:
            raise TypeError(
"only length-1 arrays can be converted to Python scalars. Got {}".format(self))

        return int(self.array)
    #--- End: def

    def __setitem__(self, indices, value):
        '''Assign to data elements defined by indices.

d.__setitem__(indices, x) <==> d[indices]=x

Indexing follows rules that are very similar to the numpy indexing
rules, the only differences being:

* An integer index i takes the i-th element but does not reduce the
  rank by one.

* When two or more dimensions' indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same
  behaviour as indexing on a Variable object of the netCDF4 package.

**Broadcasting**

The value, or values, being assigned must be broadcastable to the
shape defined by the indices, using the numpy broadcasting rules.

**Missing data**

Data array elements may be set to missing values by assigning them to
`numpy.ma.masked`. Missing values may be unmasked by assigning them to
any other value.

.. versionadded:: 1.7.0

.. seealso:: `__getitem__`, `_parse_indices`

:Returns:

    `None`

**Examples:**

>>> import numpy
>>> d = cfdm.Data(numpy.arange(100, 190).reshape(1, 10, 9))
>>> d.shape
(10, 9)
>>> d[:, :, 1] = -10
>>> d[:, 0] = range(9)
>>> d[..., 6:3:-1, 3:6] = numpy.arange(-18, -9).reshape(3, 3)
>>> d[0, [2, 9], [4, 8]] =  cfdm.Data([[-2, -3]])
>>> d[0, :, -2] = numpy.ma.masked

        '''
        indices = self._parse_indices(indices)
                
        array = self.array

        if value is masked or numpy.ma.isMA(value):
            # The data is not masked but the assignment is masking
            # elements, so turn the non-masked array into a masked
            # one.
            array = array.view(numpy.ma.MaskedArray)        

        self._set_subspace(array, indices, numpy.asanyarray(value))

        self._set_Array(array, copy=False)
    #--- End: def

    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

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

        size  = self.size
        shape = self.shape
        ndim  = self.ndim
        open_brackets  = '[' * ndim
        close_brackets = ']' * ndim

        if size == 1:
            if isreftime:
                # Convert reference time to date-time
                try:
                    first = type(self)(
                        numpy.ma.array(first), units, calendar).datetime_array
                except (ValueError, OverflowError):
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
                        numpy.ma.array([first, last]), units, calendar).datetime_array
                except (ValueError, OverflowError):
                    first, last = ('??', '??')

            if size > 3:
                out = '{0}{1!s}, ..., {2!s}{3}'.format(open_brackets,
                                                       first, last,
                                                       close_brackets)
            elif shape[-1:] == (3,):                
                middle = self.second_element()
                if isreftime:
                    # Convert reference time to date-time
                    try:
                        middle = type(self)(
                            numpy.ma.array(middle), units, calendar).datetime_array
                    except (ValueError, OverflowError):
                        middle = '??'
                        
                out = '{0}{1!s}, {2!s}, {3!s}{4}'.format(open_brackets,
                                                         first, middle, last,
                                                         close_brackets)
            elif size == 3:
                out = '{0}{1!s}, ..., {2!s}{3}'.format(open_brackets,
                                                       first, last,
                                                       close_brackets)
            else:
                out = '{0}{1!s}, {2!s}{3}'.format(open_brackets,
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
    # Private methods
    # ----------------------------------------------------------------
    def _item(self, index):
        '''Return an element of the data as a scalar.

It is assumed, but not checked, that the given index selects exactly
one element.

:Parameters:

    index: 

:Returns:

        The selected element of the data.

**Examples:**

>>> import numpy
>>> d = Data([[1, 2, 3]], 'km')
>>> x = d._item((0, -1))
>>> print(x, type(x))
3 <type 'int'>
>>> x = d._item(1)
>>> print(x, type(x))
2 <type 'int'>
>>> d[0, 1] = numpy.ma.masked
>>> d._item((slice(None), slice(1, 2)))
masked

        '''
        array = self[index].array

        if not numpy.ma.isMA(array):
            return array.item()

        mask = array.mask
        if mask is numpy.ma.nomask or not mask.item():
            return array.item()

        return numpy.ma.masked
    #--- End: def
    
    def _parse_axes(self, axes):
        '''TODO

:Parameters:

    axes: (sequence of) `int`
        The axes of the data. May be one of, or a sequence of any
        combination of zero or more of:

          * The integer position of a dimension in the data (negative
            indices allowed).

:Returns:

    `tuple`

**Examples:**

        '''
        if axes is None:
            return axes
        
        ndim = self.ndim

        if isinstance(axes, int):
            axes = (axes,)
            
        axes2 = []
        for axis in axes:
            if 0 <= axis < ndim:
                axes2.append(axis)
            elif -ndim <= axis < 0:
                axes2.append(axis + ndim)
            else:
                raise ValueError(
                    "Invalid axis: {!r}".format(axis))
        #--- End: for
            
        # Check for duplicate axes
        n = len(axes2)
        if n > len(set(axes2)) >= 1:
            raise ValueError("Duplicate axis: {}".format(axes2))
        
        return tuple(axes2)
    #--- End: def

    def _set_Array(self, array, copy=True):
        '''Set the array.

:Parameters:

    array: numpy array-like or subclass of `Array`, optional
        The array to be inserted.

:Returns:

    `None`

**Examples:**

>>> d._set_Array(a)

        '''
        if not isinstance(array, abstract.Array):
            if not isinstance(array, numpy.ndarray):
                array = numpy.asanyarray(array)
                
            array = NumpyArray(array)

        super()._set_Array(array, copy=copy)
    #--- End: def

    @classmethod
    def _set_subspace(cls, array, indices, value):
        '''TODO
        '''
        axes_with_list_indices = [i for i, x in enumerate(indices)
                                  if not isinstance(x, slice)]

        if len(axes_with_list_indices) < 2: 
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
                if i in axes_with_list_indices:
                    # This index is a list of integers
                    y = []
                    args = [iter(x)] * 2
                    for start, stop in itertools.zip_longest(*args):
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

            if numpy.size(value) == 1:
                for i in itertools.product(*indices1):
                    array[i] = value
                    
            else:
                indices2 = []
                ndim_difference = array.ndim - numpy.ndim(value)
                for i, n in enumerate(numpy.shape(value)):
                    if n == 1:
                        indices2.append((slice(None),))
                    elif i + ndim_difference in axes_with_list_indices:
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

                for i, j in zip(itertools.product(*indices1), itertools.product(*indices2)):
                    array[i] = value[j]
    #--- End: def

    #-----------------------------------------------------------------
    # Attributes
    #-----------------------------------------------------------------
    @property
    def compressed_array(self):
        '''Return an independent numpy array containing the compressed data.

.. versionadded:: 1.7.0

.. seealso:: `get_compressed_axes`, `get_compressed_dimension`,
             `get_compression_type`

:Returns:

     `numpy.ndarray`
        An independent numpy array of the compressed data.

**Examples:**

>>> a = d.compressed_array

        '''
        ca = self._get_Array(None)

        if not ca.get_compression_type():
            raise ValueError("not compressed: can't get compressed array")

        return ca.compressed_array
    #--- End: def

    @property
    def datetime_array(self):
        '''Return an independent numpy array containing the date-time objects
corresponding to time since a reference date.

Only applicable for reference time units.

If the calendar has not been set then the CF default calendar of
"standard" (i.e. the mixed Gregorian/Julian calendar as defined by
Udunits) will be used.

Conversions are carried out with the `netCDF4.num2date` function.

.. versionadded:: 1.7.0

.. seealso:: `array`

**Examples:**

>>> d = cfdm.Data([31, 62, 90], units='days since 2018-12-01')
>>> a = d.datetime_array
>>> print(a)
[cftime.DatetimeGregorian(2019, 1, 1, 0, 0, 0, 0, 1, 1)
 cftime.DatetimeGregorian(2019, 2, 1, 0, 0, 0, 0, 4, 32)
 cftime.DatetimeGregorian(2019, 3, 1, 0, 0, 0, 0, 4, 60)]
>>> print(a[1])
2019-02-01 00:00:00

>>> d = cfdm.Data([31, 62, 90], units='days since 2018-12-01',
...               calendar='360_day')
>>> a = d.datetime_array
>>> print(a)
[cftime.Datetime360Day(2019, 1, 2, 0, 0, 0, 0, 3, 2)
 cftime.Datetime360Day(2019, 2, 3, 0, 0, 0, 0, 6, 33)
 cftime.Datetime360Day(2019, 3, 1, 0, 0, 0, 0, 6, 61)]
>>> print(a[1])
2019-02-03 00:00:00

        '''
        array = self.array

        mask = None
        if numpy.ma.isMA(array):
            # num2date has issues if the mask is nomask
            mask = array.mask
            if mask is numpy.ma.nomask or not numpy.ma.is_masked(array):
                mask = None
                array = array.view(numpy.ndarray)
        #--- End: if
        
        array = netCDF4.num2date(array, units=self.get_units(None),
                                 calendar=self.get_calendar('standard'),
                                 only_use_cftime_datetimes=True)

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

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self, array=True):
        '''Return a deep copy.

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

:Parameters:

    array: `bool`, optional
        If False then do not copy the array. By default the array is
        copied.

:Returns:

        The deep copy.

**Examples:**

>>> e = d.copy()
>>> e = d.copy(array=False)

        '''
        return super().copy(array=array)
    #--- End: def

    def insert_dimension(self, position=0):
        '''Expand the shape of the data array.

Inserts a new size 1 axis, corresponding to a given position in the
data array shape.

.. versionadded:: 1.7.0

.. seealso:: `squeeze`, `transpose`

:Parameters:

    position: `int`, optional
        Specify the position that the new axis will have in the data
        array. By default the new axis has position 0, the slowest
        varying position. Negative integers counting from the last
        position are allowed.

        *Parameter example:*
          ``position=2``

        *Parameter example:*
          ``position=-1``

:Returns:

    `Data`
        The new data array with expanded data axes.

**Examples:**

>>> d.shape
(19, 73, 96)
>>> d.insert_dimension('domainaxis3').shape
(1, 96, 73, 19)
>>> d.insert_dimension('domainaxis3', position=3).shape
(19, 73, 96, 1)
>>> d.insert_dimension('domainaxis3', position=-1).shape
(19, 73, 1, 96)

        '''
        # Parse position
        ndim = self.ndim 
        if -ndim-1 <= position < 0:
            position += ndim + 1
        elif not 0 <= position <= ndim:
            raise ValueError(
                "Can't insert dimension: Invalid position: {!r}".format(position))

        array = self.array
        array = numpy.expand_dims(array, position)

        out = self.copy(array=False)
        out._set_Array(array, copy=False)

        # Delete hdf5 chunksizes
        out.nc_clear_hdf5_chunksizes()
        
        return out
    #--- End: def

#    def compress_by_gathering(self, list_data, compressed_axes, replace_list_data=False

#    def set_list_data(self, list_data, compressed_axes=None,
#                      copy=True):
#        '''
#        '''
#        compression_type = self.compression_type
#        if compression_type == 'gathered':
#            self._set_Array().set_list_data(list_data)
##            raise ValueError("eqweqweweqw 1")
#        elif compression_type:
#            raise ValueError("eqweqweweqw 2")
#
#        compressed_array = self._compress_by_gathering(list_data, compressed_axes)
#
#        self._set_Array(GatheredArray(compressed_array=compressed_array,
#                                      shape=self.shape,
#                                      size=self.size, ndim=self.ndim,
#                                      sample_axis=compressed_axes[0],
#                                      list_array=list_data))
#    #--- End: def

    def get_count(self, default=ValueError()):
        '''Return the countcount_va variable for a compressed array.

.. versionadded:: 1.7.0

.. seealso:: `get_index`, `get_list`

:Parameters:

    default: optional
        Return the value of the *default* parameter if a count
        variable has not been set. If set to an `Exception` instance
        then it will be raised instead.

:Returns:

        The count variable.

**Examples:**

>>> c = d.get_count()

        '''
        try:
            return self._get_Array().get_count()
        except (AttributeError, ValueError):
            return self._default(default,
                                 "{!r} has no count variable".format(
                                 self.__class__.__name__))
    #--- End: def

    def get_index(self, default=ValueError()):
        '''Return the index variable for a compressed array.

.. versionadded:: 1.7.0

.. seealso:: `get_count`, `get_list`

:Parameters:

    default: optional
        Return *default* if index variable has not been set.

    default: optional
        Return the value of the *default* parameter if an index
        variable has not been set. If set to an `Exception` instance
        then it will be raised instead.

:Returns:

        The index variable.

**Examples:**

>>> i = d.get_index()

        '''
        try:
            return self._get_Array().get_index()
        except (AttributeError, ValueError):
            return self._default(default,
                                 "{!r} has no index variable".format(
                                 self.__class__.__name__))
    #--- End: def

    def get_list(self, default=ValueError()):
        '''Return the list variable for a compressed array.

.. versionadded:: 1.7.0

.. seealso:: `get_count`, `get_index`

:Parameters:

    default: optional
        Return the value of the *default* parameter if an index
        variable has not been set. If set to an `Exception` instance
        then it will be raised instead.

:Returns:

        The list variable.

**Examples:**

>>> l = d.get_list()

        '''
        try:
            return self._get_Array().get_list()
        except (AttributeError, ValueError):
            return self._default(default,
                                 "{!r} has no list variable".format(
                                     self.__class__.__name__))        
    #--- End: def

    def get_compressed_dimension(self, default=ValueError()):
        '''Return the position of the compressed dimension in the compressed
array.

. versionadded:: 1.7.0

.. seealso:: `compressed_array`, `get_compressed_axes`,
             `get_compression_type`

:Parameters:

    default: optional
        Return the value of the *default* parameter there is no
        compressed dimension. If set to an `Exception` instance then
        it will be raised instead.

:Returns:

    `int`
        The position of the compressed dimension in the compressed
        array.

**Examples:**

>>> d.get_compressed_dimension()
2

        ''' 
        try:
            return self._get_Array().get_compressed_dimension()
        except (AttributeError, ValueError):
            return self._default(default,
                                 "{!r} has no compressed dimension".format(
                                     self.__class__.__name__))
    #--- End: def

    
    def _parse_indices(self, indices):
        '''TODO
    
:Parameters:
    
    indices: `tuple` (not a `list`!)
    
:Returns:
    
    `list`
    
**Examples:**
    
    '''
        shape = self.shape
        
        parsed_indices = []
    
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
            raise IndexError(
                "Invalid indices for data with shape {}: {} ".format(
                    shape, parsed_indices))
    
        if len_parsed_indices < ndim:
            parsed_indices.extend([slice(None)]*(ndim-len_parsed_indices))
    
        if not ndim and parsed_indices:
            raise IndexError(
                "Scalar data can only be indexed with () or Ellipsis")
    
        for i, (index, size) in enumerate(zip(parsed_indices, shape)):
            if isinstance(index, slice):            
                continue
    
            if isinstance(index, int):
                # E.g. 43 -> slice(43, 44, 1)
                if index < 0: 
                    index += size
    
                index = slice(index, index+1, 1)
            else:
                if getattr(getattr(index, 'dtype', None), 'kind', None) == 'b':
                    # E.g. index is [True, False, True] -> [0, 2]
                    #
                    # Convert booleans to non-negative integers. We're
                    # assuming that anything with a dtype attribute also
                    # has a size attribute.
                    if index.size != size:
                        raise IndexError(
"Invalid indices for data with shape {}: {} ".format(
                                shape, parsed_indices))

                    index = numpy.where(index)[0]
                #--- End: if
    
                if not numpy.ndim(index):
                    if index < 0:
                        index += size
    
                    index = slice(index, index+1, 1)
                else:
                    len_index = len(index)
                    if len_index == 1:
                        # E.g. [3] -> slice(3, 4, 1)
                        index = index[0]
                        if index < 0:
                            index += size
                        
                        index = slice(index, index+1, 1)
                    else:
                        # E.g. [1, 3, 4] -> [1, 3, 4]
                        pass
            #--- End: if
            
            parsed_indices[i] = index    
        #--- End: for
    
        return parsed_indices
    #--- End: def
    
    def max(self, axes=None):
        '''Return the maximum of an array or the maximum along axes.

Missing data array elements are omitted from the calculation.

.. seealso:: `min`

:Parameters:

    axes: (sequence of) `int`, optional

:Returns:

    `Data`
        Maximum of the data along the specified axes.

**Examples:**

        '''
        # Parse the axes. By default flattened input is used.
        try:
            axes = self._parse_axes(axes)
        except ValueError as error:
            raise ValueError("Can't find maximum of data: {}".format(error))
        
        array = self.array
        array = numpy.amax(array, axis=axes, keepdims=True)

        out = self.copy(array=False)
        out._set_Array(array, copy=False)

        if out.shape != self.shape:
            # Delete hdf5 chunksizes
            out.nc_clear_hdf5_chunksizes()
        
        return out
    #--- End: def

    def min(self, axes=None):
        '''Return the minimum of an array or minimum along axes.

Missing data array elements are omitted from the calculation.

.. seealso:: `max`

:Parameters:

    axes: (sequence of) `int`, optional

:Returns:

    `Data`
        Minimum of the data along the specified axes.

**Examples:**

        '''            
        # Parse the axes. By default flattened input is used.
        try:
            axes = self._parse_axes(axes)
        except ValueError as error:
            raise ValueError("Can't find minimum of data: {}".format(error))

        array = self.array
        array = numpy.amin(array, axis=axes, keepdims=True)

        out = self.copy(array=False)
        out._set_Array(array, copy=False)

        if out.shape != self.shape:
            # Delete hdf5 chunksizes
            out.nc_clear_hdf5_chunksizes()

        return out
    #--- End: def

#    def get_HDF_chunks(self, dddd):
#        '''Set HDF5 chunks for the data array.
#    
#Chunking refers to a storage layout where the data array is
#partitioned into fixed-size multi-dimensional chunks when written to a
#netCDF4 file on disk. Chunking is ignored if the data array is written
#to a netCDF3 format file.
#    
#A chunk has the same rank as the data array, but with fewer (or no
#more) elements along each axis. The chunk is defined by a dictionary
#in which each key identifies an axis (by its index in the data array
#shape) and its value is the chunk size (i.e. number of axis elements)
#for that axis.
#    
#If a given chunk size for an axis is larger than the axis size, then
#the size of the axis at the time of writing to disk will be used
#instead.
#    
#If chunk sizes have been specified for some but not all axes, then the
#each unspecified chunk size is assumed to be the full size of its
#axis.
#
#If no chunk sizes have been set for any axes then the netCDF default
#chunk is used. See
#http://www.unidata.ucar.edu/software/netcdf/docs/netcdf_perf_chunking.html.
#
#A detailed discussion of HDF chunking and I/O performance is available
#at https://www.hdfgroup.org/HDF5/doc/H5.user/Chunking.html and
#http://www.unidata.ucar.edu/software/netcdf/workshops/2011/nc4chunking. Basically,
#you want the chunks for each dimension to match as closely as possible
#the size and shape of the data block that users will read from the
#file.
#
#        '''
#    #--- End: def

    def squeeze(self, axes=None):
        '''Remove size 1 axes from the data.

By default all size 1 axes are removed, but particular axes may be
selected with the keyword arguments.

.. versionadded:: 1.7.0

.. seealso:: `insert_dimension`, `transpose`

:Parameters:

    axes: (sequence of) `int`, optional
        The positions of the size one axes to be removed. By default
        all size one axes are removed. Each axis is identified by its
        original integer position. Negative integers counting from the
        last position are allowed.

        *Parameter example:*
          ``axes=0``

        *Parameter example:*
          ``axes=-2``

        *Parameter example:*
          ``axes=[2, 0]``

:Returns:

    `Data`
        The new data array with removed data axes.

**Examples:**

>>> d.shape
(1, 73, 1, 96)
>>> f.squeeze().shape
(73, 96)
>>> d.squeeze(0).shape
(73, 1, 96)
>>> d.squeeze([-3, 2]).shape
(73, 96)

        '''
        out = self.copy()

        if not out.ndim:
            if axes:
                raise ValueError(
"Can't squeeze data: axes {} is not allowed data with shape {}".format(
    axes, out.shape))

            return out

        shape = out.shape

        try:
            axes = self._parse_axes(axes)
        except ValueError as error:
            raise ValueError("Can't squeeze data: {}".format(error))

        if axes is None:
            axes = tuple([i for i, n in enumerate(shape) if n == 1])
        else:
            # Check the squeeze axes
            for i in axes:
                if shape[i] > 1:
                    raise ValueError(
"Can't squeeze data: Can't remove axis of size {}".format(shape[i]))
        #--- End: if

        if not axes:
            return out

        array = self.array
        array = numpy.squeeze(array, axes)

        out._set_Array(array, copy=False)

        # Delete hdf5 chunksizes
        out.nc_clear_hdf5_chunksizes()
        
        return out
    #--- End: def

    def sum(self, axes=None):
        '''Return the sum of an array or the sum along axes.

Missing data array elements are omitted from the calculation.

.. seealso:: `max`, `min`

:Parameters:

    axes: (sequence of) `int`, optional

:Returns:

    `Data`
        The sum of the data along the specified axes.

**Examples:**

        '''
        # Parse the axes. By default flattened input is used.
        try:
            axes = self._parse_axes(axes)
        except ValueError as error:
            raise ValueError("Can't sum data: {}".format(error))
        
        array = self.array
        array = numpy.sum(array, axis=axes, keepdims=True)
            
        out = self.copy()
        out._set_Array(array, copy=False)

        if out.shape != self.shape:
            # Delete hdf5 chunksizes
            out.nc_clear_hdf5_chunksizes()
        
        return out
    #--- End: def

    def transpose(self, axes=None):
        '''Permute the axes of the data array.

.. versionadded:: 1.7.0

.. seealso:: `insert_dimension`, `squeeze`

:Parameters:

    axes: (sequence of) `int`
        The new axis order. By default the order is reversed. Each
        axis in the new order is identified by its original integer
        position. Negative integers counting from the last position
        are allowed.

        *Parameter example:*
          ``axes=[2, 0, 1]``

        **Parameter example:**
          ``axes=[-1, 0, 1]``

:Returns:

    `Data`
        The new data array with permuted data axes.

**Examples:**

>>> d.shape
(19, 73, 96)
>>> d.transpose().shape
(96, 73, 19)
>>> d.transpose([1, 0, 2]).shape
(73, 19, 96)

        '''
        out = self.copy()
        
        ndim = out.ndim    
        
        # Parse the axes. By default, reverse the order of the axes.
        try:
            axes = self._parse_axes(axes)
        except ValueError as error:
            raise ValueError("Can't transpose data: {}".format(error))
        
        if axes is None:
            if ndim <= 1:
                return out

            axes = tuple(range(ndim-1, -1, -1))
        else:
            if len(axes) != ndim:
                raise ValueError(
                    "Can't transpose data: Axes don't match array: {}".format(
                        axes))
        #--- End: if

        # Return unchanged if axes are in the same order as the data
        if axes == tuple(range(ndim)):
            return out
        
        array = self.array
        array = numpy.transpose(array, axes=axes)

        out._set_Array(array, copy=False)

        # Delete hdf5 chunksizes
        out.nc_clear_hdf5_chunksizes()
        
        return out
    #--- End: def

    def get_compressed_axes(self):
        '''Return the dimensions that have compressed in the underlying array.

.. versionadded:: 1.7.0

.. seealso:: `compressed_array`, `get_compressed_dimension`,
             `get_compression_type`

:Returns:

    `list`
        The dimensions of the data that are compressed to a single
        dimension in the underlying array. If the data are not
        compressed then an empty list is returned.

**Examples:**

>>> d.shape
(2, 3, 4, 5, 6)
>>> d.compressed_array.shape
(2, 14, 6)
>>> d.get_compressed_axes()
[1, 2, 3]

>>> d.get_compression_type()
''
>>> d.get_compressed_axes()
[]

        '''
        ca = self._get_Array(None)

        if ca is None:
            return []

        return ca.get_compressed_axes()
    #--- End: def

    def get_compression_type(self):
        '''Return the type of compression applied to the underlying array.

.. versionadded:: 1.7.0

.. seealso:: `compressed_array`, `compression_axes`,
             `get_compressed_dimension`

:Returns:

    `str`
        The compression type. An empty string means that no
        compression has been applied.
        
**Examples:**

>>> d.get_compression_type()
''

>>> d.get_compression_type()
'gathered'

>>> d.get_compression_type()
'ragged contiguous'

        '''
        ma = self._get_Array(None)
        if ma is None:
            return ''

        return ma.get_compression_type()
    #--- End: def
    
    def equals(self, other, rtol=None, atol=None, verbose=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_compression=False, ignore_type=False,
               _check_values=True):
        '''Whether two data arrays are the same.

Equality is strict by default. This means that for data arrays to be
considered equal:

* the units and calendar must be the same,

..

* the fill value must be the same (see the *ignore_fill_value*
  parameter), and

..

* the arrays must have same shape and data type, the same missing data
  mask, and be element-wise equal (see the *ignore_data_type*
  parameter).

Two numerical elements ``x`` and ``y`` are considered equal if
``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
differences) and ``rtol`` (the tolerance on relative differences) are
positive, typically very small numbers. See the *atol* and *rtol*
parameters.

The compression type and, if applicable, the underlying compressed
arrays must be the same, as well as the arrays in their uncompressed
forms. See the *ignore_compression* parameter.

Any type of object may be tested but, in general, equality is only
possible with another cell measure construct, or a subclass of
one. See the *ignore_type* parameter.

.. versionadded:: 1.7.0

:Parameters:

    other: 
        The object to compare for equality.

    atol: float, optional
        The tolerance on absolute differences between real
        numbers. The default value is set by the `cfdm.ATOL` function.
        
    rtol: float, optional
        The tolerance on relative differences between real
        numbers. The default value is set by the `cfdm.RTOL` function.

    ignore_fill_value: `bool`, optional
        If True then the fill value is omitted from the comparison.

    verbose: `bool`, optional
        If True then print information about differences that lead to
        inequality.

    ignore_data_type: `bool`, optional
        If True then ignore the data types in all numerical data array
        comparisons. By default different numerical data types imply
        inequality, regardless of whether the elements are within the
        tolerance for equality.

    ignore_compression: `bool`, optional
        If True then any compression applied to the underlying arrays
        is ignored and only the uncompressed arrays are tested for
        equality. By default the compression type and, if applicable,
        the underlying compressed arrays must be the same, as well as
        the arrays in their uncompressed forms

    ignore_type: `bool`, optional
        Any type of object may be tested but, in general, equality is
        only possible with another data array, or a subclass of
        one. If *ignore_type* is True then then ``Data(source=other)``
        is tested, rather than the ``other`` defined by the *other*
        parameter.

:Returns: 
  
    `bool`
        Whether the two data arrays are equal.

**Examples:**

>>> d.equals(d)
True
>>> d.equals(d.copy())
True
>>> d.equals('not a data array')
False

        '''
        pp = super()._equals_preprocess(other, verbose=verbose,
                                        ignore_type=ignore_type)
        if pp in (True, False):
            return pp
        
        other = pp
        
        # Check that each instance has the same shape
        if self.shape != other.shape:
            if verbose:
                print("{0}: Different shapes: {1} != {2}".format(
                    self.__class__.__name__, self.shape, other.shape))
            return False

        # Check that each instance has the same units
        for attr in ('units', 'calendar'):
            x = getattr(self, 'get_'+attr)(None)
            y = getattr(other, 'get_'+attr)(None)
            if x != y:
                if verbose:
                    print("{0}: Different {1}: {2!r} != {3!r}".format(
                        self.__class__.__name__, attr, x, y))
                return False
        #--- End: for
           
        # Check that each instance has the same fill value
        if (not ignore_fill_value and
            self.get_fill_value(None) != other.get_fill_value(None)):
            if verbose:
                print("{0}: Different fill value: {1} != {2}".format(
                    self.__class__.__name__, 
                    self.get_fill_value(None), other.get_fill_value(None)))
            return False

        # Check that each instance has the same data type
        if not ignore_data_type and self.dtype != other.dtype:
            if verbose:
                print("{0}: Different data types: {1} != {2}".format(
                    self.__class__.__name__, self.dtype, other.dtype))
            return False

        # Return now if we have been asked to not check the array
        # values
        if not _check_values:
            return True

        if not ignore_compression:
            # --------------------------------------------------------
            # Check for equal compression types
            # --------------------------------------------------------
            compression_type = self.get_compression_type()
            if compression_type != other.get_compression_type():
                if verbose:
                    print("{0}: Different compression types: {1} != {2}".format(
                        self.__class__.__name__,
                        compression_type,
                        other.get_compression_type()))
                return False
            
            # --------------------------------------------------------
            # Check for equal compressed array values
            # --------------------------------------------------------
            if compression_type:
                if not self._equals(self.compressed_array,
                                    other.compressed_array,
                                    rtol=rtol, atol=atol):
                    if verbose:
                        print("{0}: Different compressed array values".format(
                            self.__class__.__name__))
                    return False
        #--- End: if
        
        # ------------------------------------------------------------
        # Check for equal (uncompressed) array values
        # ------------------------------------------------------------
        if not self._equals(self.array, other.array,
                            rtol=rtol, atol=atol):
            if verbose:
                print("{0}: Different array values".format(
                    self.__class__.__name__))
            return False

        # ------------------------------------------------------------
        # Still here? Then the two data arrays are equal.
        # ------------------------------------------------------------
        return True            
    #--- End: def

    def first_element(self):
        '''Return the first element of the data as a scalar.

.. versionadded:: 1.7.0

.. seealso:: `last_element`, `second_element`

:Returns:
        
        The first element of the data.

**Examples:**

>>> d = cfdm.Data(9.0)
>>> x = d.first_element()
>>> print(x, type(x))
(9.0, <type 'float'>)

>>> d = cfdm.Data([[1, 2], [3, 4]])
>>> x = d.first_element()
>>> print(x, type(x))
(1, <type 'int'>)
>>> d[0, 0] = numpy.ma.masked
>>> y = d.first_element()
>>> print(y, type(y))
(masked, <class 'numpy.ma.core.MaskedConstant'>)

>>> d = cfdm.Data(['foo', 'bar'])
>>> x = d.first_element()
>>> print(x, type(x))
('foo', <type 'str'>)

        '''
        return self._item((slice(0, 1),)*self.ndim)
    #--- End: def
    
    def last_element(self):
        '''Return the last element of the data as a scalar.

.. versionadded:: 1.7.0

.. seealso:: `first_element`, `second_element`

:Returns:
        
        The last element of the data.

**Examples:**

>>> d = cfdm.Data(9.0)
>>> x = d.last_element()
>>> print(x, type(x))
(9.0, <type 'float'>)

>>> d = cfdm.Data([[1, 2], [3, 4]])
>>> x = d.last_element()
>>> print(x, type(x))
(4, <type 'int'>)
>>> d[-1, -1] = numpy.ma.masked
>>> y = d.last_element()
>>> print(y, type(y))
(masked, <class 'numpy.ma.core.MaskedConstant'>)

>>> d = cfdm.Data(['foo', 'bar'])
>>> x = d.last_element()
>>> print(x, type(x))
('bar', <type 'str'>)

        '''        
        return self._item((slice(-1, None),)*self.ndim)
    #--- End: def
 
    def second_element(self):
        '''Return the second element of the data as a scalar.

.. versionadded:: 1.7.0

.. seealso:: `first_element`, `last_element`

:Returns:
        
        The second element of the data.

**Examples:**

>>> d = cfdm.Data([[1, 2], [3, 4]])
>>> x = d.second_element()
>>> print(x, type(x))
(2, <type 'int'>)
>>> d[0, 1] = numpy.ma.masked
>>> y = d.second_element()
>>> print(y, type(y))
(masked, <class 'numpy.ma.core.MaskedConstant'>)

>>> d = cfdm.Data(['foo', 'bar'])
>>> x = d.second_element()
>>> print(x, type(x))
('bar', <type 'str'>)

        '''
        return self._item((slice(0, 1),)*(self.ndim-1) + (slice(1, 2),))
    #--- End: def

#    def astype(self, dtype, casting='unsafe'):
#        '''Cast the data to a specified type.
#
#.. versionadded:: 1.7.0
#
#.. seealso:: `dtype`
#
#:Parameters:
#
#    dtype: `str` or `numpy.dtype`
#        Typecode or data-type to which the array is cast.
#
#    casting : `str`, optional
#        Controls what kind of data casting may occur. Defaults to
#        'unsafe'.
#    
#        ===============  =============================================
#        *casting*        Casting rules
#        ===============  =============================================
#        ``'no'``         The data types should not be cast at all.
#        ``'equiv'``      Only byte-order changes are allowed.
#        ``'safe'``       Only casts which can preserve values are
#                         allowed.
#        ``'same_kind'``  Only safe casts or casts within a kind, like
#                         float64 to float32, are allowed.
#        ``'unsafe'``     Any data conversions may be done.
#        ===============  =============================================
#
#:Returns:
#
#    `None`
#
#**Examples:**
#
#>>> d = cfdm.Data([1.5, 2, 2.5])
#>>> d.dtype
#dtype('float64')
#>>> print(d.array)
#[1.5 2.  2.5]
#>>> d.astype('int32')
#>>> d.dtype
#dtype('int32')
#>>> print(d.array)
#[1 2 2]
#>>> d.astype(float)
#>>> print(d.array)
#[1. 2. 2.]
#
#>>> d = cfdm.Data([1.5, 2, 2.5])
#>>> d.dtype
#dtype('float64')
#>>> d.astype('int', casting='safe')
#TypeError: Cannot cast array from dtype('float64') to dtype('int64') according to the rule 'safe'
#
#        '''
#        dtype = numpy.dtype(dtype)
#        if dtype != self.dtype:
#            array = self.array.astype(dtype, casting=casting)
#            self._set_Array(array, copy=False)
#    #--- End: def

    def underlying_array(self, default=ValueError()):
        '''Return the array object.

:Parameters:

    default: optional
        Return the value of the *default* parameter if the array
        has not been set. If set to an `Exception` instance then it
        will be raised instead.

:Returns:

        The array object.

**Examples:**

>>> TODO

        '''
        underlying_array = super().underlying_array(default=default)

        if self.get_compression_type():
            return underlying_array.underlying_array(default=default)

        return underlying_array        
    #--- End: def
        
    def unique(self):
        '''The unique elements of the data.

The unique elements are sorted into a one dimensional array. with no
missing values.

.. versionadded:: 1.7.0

:Returns:

    `Data`
        The unique elements.

**Examples:**

>>> d = Data([[4, 2, 1], [1, 2, 3]], 'metre')
>>> d.unique()
<Data(4): [1, 2, 3, 4] metre>
>>> d[1, -1] = masked
>>> d.unique()
<Data(3): [1, 2, 4] metre>

        '''
        array = self.array
        array = numpy.unique(array)

        if numpy.ma.is_masked(array):
            array = array.compressed()

        out = self.copy(array=False)
        out._set_Array(array, copy=False)

        if out.shape != self.shape:
            # Delete hdf5 chunksizes
            out.nc_clear_hdf5_chunksizes()

        return out
    #--- End: def

#--- End: class
