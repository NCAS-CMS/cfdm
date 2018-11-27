from __future__ import print_function
from builtins import (next, range, super, zip)

import itertools

import numpy
import netCDF4

from .. import core
from .. import mixin

from ..constants  import masked

from . import abstract
from . import NumpyArray


class Data(mixin.Container, core.Data):
    '''An orthogonal multidimensional array with masked values and units.

.. versionadded:: 1.7

    '''
    def __init__(self, array=None, units=None, calendar=None,
                 fill_value=None, source=None, copy=True,
                 _use_array=True):
        '''**Initialization**

:Parameters:

    array: numpy array-like or subclass of `Array`, optional
        The array of values. Ignored if the *source* parameter is set.

        *Example:*
          ``array=[34.6]``

        *Example:*
          ``array=[[1, 2], [3, 4]]``

        *Example:*
          ``array=numpy.ma.arange(10).reshape(2, 1, 5)``

    units: `str`, optional
        The physical units of the data. Ignored if the *source*
        parameter is set.

        *Example:*
          ``units='km hr-1'``

        *Example:*
          ``units='days since 2018-12-01'``

        The units may also be set after initialisation with the
        `set_units` method.

    calendar: `str`, optional
        The calendar for reference time units. Ignored if the *source*
        parameter is set.

        *Example:*
          ``calendar='360_day'``
        
        The calendar may also be set after initialisation with the
        `set_calendar` method.

    fill_value: optional 
        The fill value of the data. By default, or if None, the numpy
        fill value appropriate to the array's data type will be used.
        TODO. Ignored if the *source* parameter is set.

        *Example:*
          ``fill_value=-999.``
                
        The fill value may also be set after initialisation with the
        `set_fill_value` method.

    source: optional
        Initialize the array, units, calendar and fill value from
        those of *source*.

    copy: bool, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__(array=array, units=units, calendar=calendar,
                         fill_value=fill_value, source=source,
                         copy=copy, _use_array=_use_array)
                                   
        # The _HDF_chunks attribute is.... Is either None or a
        # dictionary. DO NOT CHANGE IN PLACE.
#        self._HDF_chunks = {}
    #--- End: def
                 
    def __array__(self, *dtype):
        '''The numpy array interface.

.. versionadded:: 1.7

:Returns: 

    out: `numpy.ndarray`
        An independent numpy array of the data.

**Examples:**

TODO
        '''
        array = self.get_array()
        if not dtype:
            return array
        else:
            return array.astype(dtype[0], copy=False)
    #--- End: def
                  
    def __data__(self):
        '''TODO

Return self

        '''
        return self
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

.. versionadded:: 1.7

.. seealso:: `__setitem__`, `_parse_indices`

:Returns:

    out: `Data`
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

        return out
    #--- End: def

    def __int__(self):
        '''x.__int__() <==> int(x)

        '''
        if self.size != 1:
            raise TypeError(
"only length-1 arrays can be converted to Python scalars. Got {}".format(self))

        return int(self.get_array())
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

.. versionadded:: 1.7

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
                
        array = self.get_array()

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
                        numpy.ma.array([first, last]), units, calendar).get_dtarray()
                except (ValueError, OverflowError):
                    first, last = ('??', '??')

            if size > 3:
                out = '{0}{1!s}, ..., {2!s}{3}'.format(open_brackets,
                                                       first, last,
                                                       close_brackets)
            elif size == 3:                
                middle = self.second_element()
                if isreftime:
                    # Convert reference time to date-time
                    try:
                        middle = type(self)(
                            numpy.ma.array(middle), units, calendar).get_dtarray()
                    except (ValueError, OverflowError):
                        middle = '??'
                        
                out = '{0}{1!s}, {2!s}, {3!s}{4}'.format(open_brackets,
                                                         first, middle, last,
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
        '''Copy an element of an array to a standard Python scalar and return it.

It is assumed, but not checked, that the given index selects exactly
one element.

:Examples 1:

>>> x = d._item(8)

:Examples 2:

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
        array = self[index].get_array()

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

    out: `tuple`

**Examples:**

        '''
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

    out: 
        The deep copy.

:Examples:

>>> e = d.copy()
>>> e = d.copy(array=False)

        '''
        new = super().copy(array=array)
#        new.HDF_chunks(self.HDF_chunks())
        return new
    #--- End: def

    def expand_dims(self, position=0):
        '''Expand the shape of the data array.

Insert a new size 1 axis, corresponding to a given position in the
data array shape.

.. versionadded:: 1.7

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

**Examples:**

        '''
        # Parse position
        ndim = self.ndim 
        if -ndim-1 <= position < 0:
            position += ndim + 1
        elif not 0 <= position <= ndim:
            raise ValueError(
                "Can't expand dimension sof data: Invalid position: {!r}".format(position))

        array = self.get_array()
        array = numpy.expand_dims(array, position)

        d = self.copy(array=False)
        d._set_Array(array, copy=False)

#        if d._HDF_chunks:            
#            HDF = {}
#            for axis in axes:
#                HDF[axis] = None
#
#            d.HDF_chunks(HDF)

        return d
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

    def get_dtarray(self):
        '''An independent numpy array of date-time objects.

Only applicable for reference time units.

If the calendar has not been set then the CF default calendar of
"gregorian" will be used.

Conversions are carried out with the `netCDF4.num2date` function.

.. versionadded:: 1.7

.. seealso:: `get_array`

**Examples:**

>>> d.get_units()
'days since 2018-12-01'
>>> d.get_calendar()
'360_day'
>>> d.get_array()
30.0
>>> print(d.get_dtarray())
[2019-01-01 00:00:00]

        '''
        array = self.get_array()

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

    def get_count_variable(self, *default):
        '''Return the count variable for a compressed array.

.. versionadded:: 1.7

.. seealso:: `get_index_variable`, `get_list_variable`

:Parameters:

    default: optional
        Return *default* if a count variable has not been set.

:Returns:

    out:
        The count variable. If unset then *default* is returned, if
        provided.

**Examples:**

>>> c = d.get_count_variable(None)

        '''
        array = self._get_Array(None)
        if array is None:
            if default:
                return default

            raise AttributeError("{!r} has no count variable".format(
                self.__class__.__name__))

        variable = array.get_count_variable(None)
        if variable is None:
            if default:
                return default[0]

            raise AttributeError("{!r} has no count variable".format(
                self.__class__.__name__))
        
        return variable
    #--- End: def

    def get_index_variable(self, *default):
        '''Return the index variable for a compressed array.

.. versionadded:: 1.7

.. seealso:: `get_count_variable`, `get_list_variable`

:Parameters:

    default: optional
        Return *default* if index variable has not been set.

:Returns:

    out:
        The index variable. If unset then *default* is returned, if
        provided.

**Examples:**

>>> i = d.get_index_variable(None)

        '''
        array = self._get_Array(None)
        if array is None:
            if default:
                return default

            raise AttributeError("{!r} has no index variable".format(
                self.__class__.__name__))

        variable = array.get_index_variable(None)
        if variable is None:
            if default:
                return default[0]

            raise AttributeError("{!r} has no index variable".format(
                self.__class__.__name__))
        
        return variable
    #--- End: def

    def get_list_variable(self, *default):
        '''Return the list variable for a compressed array.

.. versionadded:: 1.7

.. seealso:: `get_count_variable`, `get_index_variable`

:Parameters:

    default: optional
        Return *default* if a list variable has not been set.

:Returns:

    out:
        The list variable. If unset then *default* is returned, if
        provided.

**Examples:**

>>> l = d.get_list_variable(None)

        '''
        array = self._get_Array(None)
        if array is None:
            if default:
                return default

            raise AttributeError("{!r} has no list variable".format(
                self.__class__.__name__))

        variable = array.get_list_variable(None)
        if variable is None:
            if default:
                return default[0]

            raise AttributeError("{!r} has no list variable".format(
                self.__class__.__name__))
        
        return variable
    #--- End: def

    def get_compressed_dimension(self, *default):
        '''Return the position of the compressed dimension in the compressed
array.

. versionadded:: 1.7

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
        a = self._get_Array(None)

        compressed_dimension = a.get_compressed_dimension()
        if compressed_dimension is None:
            raise ValueError("not compressed: can't get compressed dimension")

        return compressed_dimension
    #--- End: def

    
    def _parse_indices(self, indices):
        '''TODO
    
:Parameters:
    
    indices: `tuple` (not a `list`!)
    
:Returns:
    
    out: `list`
    
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

    out: `Data`
        Maximum of the data along the specified axes.

**Examples:**

        '''
        # Parse the axes. By default flattened input is used.
        if axes is not None:
            try:
                axes = self._parse_axes(axes)
            except ValueError as error:
                raise ValueError("Can't find maximum of data: {}".format(error))
        #--- End: if
        
        array = self.get_array()
        array = numpy.amax(array, axis=axes, keepdims=True)

        d = self.copy(array=False)
        d._set_Array(array, copy=False)
        
#        if d._HDF_chunks:            
#            HDF = {}
#            for axis in axes:
#                HDF[axis] = None
#
#            d.HDF_chunks(HDF)

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

**Examples:**

        '''            
        # Parse the axes. By default flattened input is used.
        if axes is not None:
            try:
                axes = self._parse_axes(axes)
            except ValueError as error:
                raise ValueError("Can't find minimum of data: {}".format(error))
        #--- End: if

        array = self.get_array()
        array = numpy.amin(array, axis=axes, keepdims=True)

        d = self.copy(array=False)
        d._set_Array(array, copy=False)

#        if d._HDF_chunks:            
#            HDF = {}
#            for axis in axes:
#                HDF[axis] = None
#
#            d.HDF_chunks(HDF)

        return d
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
#        self._HDF_chunks = tuplchunks.copy()
#
#        
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

    def squeeze(self, axes=None):
        '''Remove size 1 axes from the data.

By default all size 1 axes are removed, but particular axes may be
selected with the keyword arguments.

.. versionadded:: 1.7

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

**Examples:**

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
        d = self.copy()

        if not d.ndim:
            if axes:
                raise ValueError(
"Can't squeeze data: axes {} is not allowed data with shape {}".format(axes, d.shape))

            return d

        shape = d.shape

        if axes is None:
            axes = [i for i, n in enumerate(shape) if n == 1]
        else:
            try:
                axes = self._parse_axes(axes)
            except ValueError as error:
                raise ValueError("Can't squeeze data: {}".format(error))

            # Check the squeeze axes
            for i in axes:
                if shape[i] > 1:
                    raise ValueError(
"Can't squeeze data: Can't remove axis of size {}".format(shape[i]))
        #--- End: if

        if not axes:
            return d

        array = self.get_array()
        array = numpy.squeeze(array, axes)

        d._set_Array(array, copy=False)

        return d
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

**Examples:**

        '''
        # Parse the axes. By default flattened input is used.
        if axes is not None:
            try:
                axes = self._parse_axes(axes)
            except ValueError as error:
                raise ValueError("Can't sum data: {}".format(error))
        #--- End: if
        
        array = self.get_array()
        array = numpy.sum(array, axis=axes, keepdims=True)
            
        d = self.copy()
        d._set_Array(array, copy=False)

#        if d._HDF_chunks:            
#            HDF = {}
#            for axis in axes:
#                HDF[axis] = None
#
#            d.HDF_chunks(HDF)
        
        return d
    #--- End: def

    def transpose(self, axes=None):
        '''Permute the axes of the data array.

.. versionadded:: 1.7

.. seealso:: `expand_dims`, `squeeze`, `unsqueeze`

:Parameters:

    axes: (sequence of) `int`
        The new axis order of the data array. By default the order is
        reversed. Each axis of the new order is identified by its
        original integer position.

:Returns:

    out: `Data`

**Examples:**

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
        d = self.copy()
        
        ndim = d.ndim    
        
        # Parse the axes. By default, reverse the order of the axes.
        if axes is None:
            if ndim <= 1:
                return d

            axes = list(range(ndim-1, -1, -1))
        else:
            try:
                axes = self._parse_axes(axes)
            except ValueError as error:
                raise ValueError("Can't transpose data: {}".format(error))

            # Return unchanged if axes are in the same order as the data
            if axes == list(range(ndim)):
                return d

            if len(axes) != ndim:
                raise ValueError(
                    "Can't transpose data: Axes don't match array: {}".format(axes))
        #--- End: if

        array = self.get_array()
        array = numpy.transpose(array, axes=axes)

        d._set_Array(array, copy=False)

        return d
    #--- End: def

    def get_compressed_array(self):
        '''Return an independent numpy array containing the compressed data.

.. versionadded:: 1.7

.. seealso:: `get_compressed_axes`, `get_compressed_dimension`,
             `get_compression_type`,

:Returns:

     out: `numpy.ndarray`
        An independent numpy array of the compressed data.

**Examples:**

>>> a = d.get_compressed_array()

        '''
        ca = self._get_Array(None)

        if not ca.get_compressed_axes():
            raise ValueError("not compressed: can't get compressed array")

        return ca.get_compressed_array()
    #--- End: def

    def get_compressed_axes(self):
        '''Return the dimensions that are compressed.

.. versionadded:: 1.7

:Returns:

    out: `list`
        TODO The axes of the data that are compressed to a single axis
        in the internal array.

**Examples:**

TODO

        '''
        ca = self._get_Array(None)

        if ca is None:
            return []

        return ca.get_compressed_axes()
    #--- End: def

    def get_compression_type(self):
        '''Return the type of compression applied to the underlying array.

.. versionadded:: 1.7

.. seealso:: `get_compressed_array`, `compression_axes`,
             `get_compressed_dimension`

:Returns:

    out: `str` or `None`
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
    
    def equals(self, other, rtol=None, atol=None, traceback=False,
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

Two numerical elements ``a`` and ``b`` are considered equal if
``|a-b|<=atol+rtol|b|``, where ``atol`` (the tolerance on absolute
differences) and ``rtol`` (the tolerance on relative differences) are
positive, typically very small numbers. See the *atol* and *rtol*
parameters.

The compression type and, if appliciable, the underlying compressed
arrays must be the same, as well as the arrays in their uncompressed
forms. See the *ignore_compression* parameter.

Any type of object may be tested but, in general, equality is only
possible with another cell measure construct, or a subclass of
one. See the *ignore_type* parameter.

.. versionadded:: 1.7

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

    traceback: `bool`, optional
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
        equality. By default the compression type and, if appliciable,
        the underlying compressed arrays must be the same, as well as
        the arrays in their uncompressed forms

    ignore_type: `bool`, optional
        Any type of object may be tested but, in general, equality is
        only possible with another data array, or a subclass of
        one. If *ignore_type* is True then then ``Data(source=other)``
        is tested, rather than the ``other`` defined by the *other*
        parameter.

:Returns: 
  
    out: `bool`
        Whether the two data arrays are equal.

**Examples:**

>>> d.equals(d)
True
>>> d.equals(d.copy())
True
>>> d.equals('not a data array')
False

        '''
        pp = super()._equals_preprocess(other, traceback=traceback,
                                        ignore_type=ignore_type)
        if pp in (True, False):
            return pp
        
        other = pp
        
        # Check that each instance has the same shape
        if self.shape != other.shape:
            if traceback:
                print("{0}: Different shapes: {1} != {2}".format(
                    self.__class__.__name__, self.shape, other.shape))
            return False

        # Check that each instance has the same units
        for attr in ('units', 'calendar'):
            x = getattr(self, 'get_'+attr)(None)
            y = getattr(other, 'get_'+attr)(None)
            if x != y:
                if traceback:
                    print("{0}: Different {1}: {2!r} != {3!r}".format(
                        self.__class__.__name__, attr, x, y))
                return False
        #--- End: for
           
        # Check that each instance has the same fill value
        if (not ignore_fill_value and
            self.get_fill_value(None) != other.get_fill_value(None)):
            if traceback:
                print("{0}: Different fill value: {1} != {2}".format(
                    self.__class__.__name__, 
                    self.get_fill_value(None), other.get_fill_value(None)))
            return False

        # Check that each instance has the same data type
        if not ignore_data_type and self.dtype != other.dtype:
            if traceback:
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
                if traceback:
                    print("{0}: Different compression types: {1} != {2}".format(
                        self.__class__.__name__,
                        compression_type,
                        other.get_compression_type()))
                return False
            
            # --------------------------------------------------------
            # Check for equal compressed array values
            # --------------------------------------------------------
            if compression_type:
                if not self._equals(self.get_compressed_array(),
                                    other.get_compressed_array(),
                                    rtol=rtol, atol=atol):
                    if traceback:
                        print("{0}: Different compressed array values".format(
                            self.__class__.__name__))
                    return False
        #--- End: if
        
        # ------------------------------------------------------------
        # Check for equal (uncompressed) array values
        # ------------------------------------------------------------
        if not self._equals(self.get_array(), other.get_array(),
                            rtol=rtol, atol=atol):
            if traceback:
                print("{0}: Different array values".format(
                    self.__class__.__name__))
            return False

        # ------------------------------------------------------------
        # Still here? Then the two data arrays are equal.
        # ------------------------------------------------------------
        return True            
    #--- End: def

    def first_element(self):
        '''TODO
        '''
        return self._item((slice(0, 1),)*self.ndim)
    #--- End: def
    
    def last_element(self):
        '''TODO
        '''
        
        return self._item((slice(-1, None),)*self.ndim)
    #--- End: def
 
    def second_element(self):
        '''TODO
        '''
        return self._item((slice(0, 1),)*(self.ndim-1) + (slice(1, 2),))
    #--- End: def

#    def set_dtype(self, value):
#        '''
#        '''
#        value = numpy.dtype(value)
 #       if value != self.dtype:
#            array = numpy.asanyarray(self.get_array(), dtype=value)
#            self._set_Array(array, copy=False)
#    #--- End: def

    def unique(self):
        '''The unique elements of the data.

The unique elements are sorted into a one dimensional array. with no
missing values.

.. versionadded:: 1.7

:Returns:

    out: `Data`
        The unique elements.

**Examples:**

>>> d = Data([[4, 2, 1], [1, 2, 3]], 'metre')
>>> d.unique()
<Data(4): [1, 2, 3, 4] metre>
>>> d[1, -1] = masked
>>> d.unique()
<Data(3): [1, 2, 4] metre>

        '''
        array = self.get_array()
        array = numpy.unique(array)

        if numpy.ma.is_masked(array):
            array = array.compressed()

        out = self.copy(array=False)
        out._set_Array(array, copy=False)

        return out
    #--- End: def

#--- End: class
