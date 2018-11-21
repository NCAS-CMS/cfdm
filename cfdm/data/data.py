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
    def __init__(self, data=None, units=None, calendar=None,
                 fill_value=None, source=None, copy=True,
                 _use_data=True):
        '''**Initialization**

:Parameters:

    array: numpy array-like or subclass of `Array`, optional
        The array of values. Ignored if the *source* parameter is set.

        *Example:*
          ``data=[34.6]``

        *Example:*
          ``data=[[1, 2], [3, 4]]``

        *Example:*
          ``data=numpy.ma.arange(10).reshape(2, 1, 5)``

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
        Initialize the data the array, units, calendar and fill value
        from those of *source*.

    copy: bool, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__(data=data, units=units, calendar=calendar,
                         fill_value=fill_value, source=source,
                         copy=copy, _use_data=_use_data)
                                   
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

:Returns:

    out: `Data`
        The subspace of the data.

**Examples:**

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
        indices = tuple(self.parse_indices(indices))

        array = self._get_Array(None)
        if array is None:
            raise ValueError("No data!!")
            
        array = array[indices]

        out = self.copy(data=False)
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
        '''x.__setitem__(indices, y) <==> x[indices]=y

Assignment to data array elements defined by indices.

Indexing is similar to `numpy` indexing. The only difference to
`numpy` indexing is:

  * When two or more dimension's indices are sequences of integers
    then these indices work independently along each dimension
    (similar to the way vector subscripts work in Fortran).

For example:

   >>> d = cfdm.Data([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
   >>> d
   >>> d.get_array()
   array([[1, 2, 3],
          [4, 5, 6],
          [7, 8, 9]])
   >>> d[[0, 2], [1, 2]].get_array()
   array([[2, 3],
          [8, 9]])
   >>> d.get_array()[[0, 2], [1, 2]]
   array([2, 9])

**Broadcasting**

The value being assigned must be broadcastable (in the `numpy` sense)
to the subspace defined by the indices. For example:

   >>> d = cfdm.Data([1, 2, 3])
   >>> d
   <Data: [1, 2, 3]>
   >>> d[:] = 99
   <Data: [99, 99, 99]>
   >>> d[1:] = [-2, -1]
   <Data: [99, -2, -1]>

**Missing data**

Data array elements may be set to missing values by assigning them to
`cfdm.masked` (or, equivalently, `numpy.ma.masked`). Missing values
may be unmasked by simple assignment. For example:

   >>> d = cfdm.Data([1, 2, 3])
   >>> d
   <Data: [1, 2, 3]>
   >>> d[1:] = cfdm.masked
   >>> d
   <Data: [1, --, --]>
   >>> d[:2] = 99
   >>> d
   <Data: [99, 99, --]>

.. seealso:: `__getitem__`, `masked`, `parse_indices`, `_set_subspace`

**Examples:**

TODO
        '''
        indices = self.parse_indices(indices)
                
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
        '''asdasdasdasds

:Parameters:

    axes: (sequence of) `int`
        The axes of the data array. May be one of, or a sequence of
        any combination of zero or more of:

          * The integer position of a dimension in the data array
            (negative indices allowed).

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

    def _set_Array(self, data, copy=True):
        '''Set the data.

:Parameters:

    data: `numpy` array_like or subclass of `cfdm.data.Array`
        The data to be inserted.

:Returns:

    `None`

**Examples:**

>>> d._set_Array(a)

        '''
        if not isinstance(data, abstract.Array):
            if not isinstance(data, numpy.ndarray):
                data = numpy.asanyarray(data)
                
            data = NumpyArray(data)

        super()._set_Array(data, copy=copy)
    #--- End: def

    @classmethod
    def _set_subspace(cls, array, indices, value):
        '''
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
    def copy(self, data=True):
        '''Return a deep copy.

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

:Returns:

    out: 
        The deep copy.

**Examples:**

>>> e = d.copy()

        '''
        new = super().copy(data=data)
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

        d = self.copy(data=False)
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
        '''
        :Returns:

        out: `Data` or `None`

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
        '''
        :Returns:

        out: `Data` or `None`

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
        '''
        :Returns:

        out: `Data` or `None`

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

    def get_compressed_dimension(self):
        '''
        '''        
        a = self._get_Array(None)

        compressed_dimension = a.get_compressed_dimension()
        if compressed_dimension is None:
            raise ValueError("not compressed: can't get compressed dimension")

        return compressed_dimension
    #--- End: def

    
    def parse_indices(self, indices):
        '''
    
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

        d = self.copy(data=False)
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

        d = self.copy(data=False)
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
        '''asd s

.. seealso:: `compression_type`, `list_indices`

:Examples 1:

>>> a = d.compression_axes()

:Returns:

    out: `list`
        The axes of the data that are compressed to a single axis in the internal array.

:Examples 2:

>>> d.compression_axes()
[0, 1]

>>> d.compression_axes()
[1, 2, 3]

>>> d.compression_axes()
[]

        '''
        ca = self._get_Array(None)

        if not ca.get_compressed_axes():
            raise ValueError("not compressed: can't get compressed array")

        return ca.get_compressed_array()
    #--- End: def

    def get_compressed_axes(self):
        '''asd s

.. seealso:: `compression_type`, `list_indices`

:Examples 1:

>>> a = d.compression_axes()

:Returns:

    out: `list`
        The axes of the data that are compressed to a single axis in the internal array.

:Examples 2:

>>> d.compression_axes()
[0, 1]

>>> d.compression_axes()
[1, 2, 3]

>>> d.compression_axes()
[]

        '''
        ca = self._get_Array(None)

        if ca is None:
            return []

        return ca.get_compressed_axes()
    #--- End: def

    def get_compression_type(self):
        '''Return the type of compression applied to the internal array.

.. seealso:: `compression_axes`, `list_indices`

:Examples 1:

>>> t = d.compression_type()

:Returns:

    out: `str` or `None`
        The compression type. An empty string means that no
        compression has been applied.
        
:Examples 2:

>>> d.compression_type()
''

>>> d.compression_type()
'gathered'

>>> d.compression_type()
'ragged contiguous'

        '''
        ma = self._get_Array(None)
        if ma is None:
            return ''

        return ma.get_compression_type()
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

**Examples:**

'''
        if prefix is None:
            prefix = self.__class__.__name__
            
        string = []
        for attr in ('ndim', 'shape', 'size', 'dtype', 'fill_value', 'array'):
            string.append('{0}.{1} = {2!r}'.format(prefix, attr, getattr(self, attr)))

        string = '\n'.join(string)
       
        if display:
            print(string)
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_construct_type=False,
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

**Examples:**

>>> d.equals(d)
True
>>> d.equals(d + 1)
False
>>> d.equals(d.expand_dims())
False

        '''
        if not super().equals(other, traceback=traceback,
                              ignore_construct_type=ignore_construct_type):
            if traceback:
                print(
                    "{0}: Different ??/".format(self.__class__.__name__))
            return False

#        # Check for object identity
#        if self is other:
#            return True
#
#        # Check each instance's id
#        if self is other:
#            return True
#
#        # Check that each instance is of the same type
#        if not ignore_construct_type and not isinstance(other, self.__class__):
#            if traceback:
#                print("{0}: Incompatible types: {0}, {1}".format(#
#			self.__class__.__name__#,#
#			other.__class__.__name__)a#)
#            return False

        # Check that each instance has the same shape
        if self.shape != other.shape:
            if traceback:
                print("{0}: Different shapes: {1}, {2}".format(
                    self.__class__.__name__, self.shape, other.shape))
            return False

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

        # Check that each instance has the same data type
        if not ignore_data_type and self.dtype != other.dtype:
            if traceback:
                print("{0}: Different data types: {1}, {2}".format(
                    self.__class__.__name__, self.dtype, other.dtype))
            return False

        # Return now if we have been asked to not check the array
        # values
        if not _check_values:
            return True

        # ------------------------------------------------------------
        # Check that each instance has equal array values
        # ------------------------------------------------------------
#        # Set default tolerances
#        if rtol is None:
#            rtol = RTOL()
#        if atol is None:
#            atol = ATOL()        

        if not self._equals(self.get_array(), other.get_array(),
                            rtol=rtol, atol=atol):

#        if not _numpy_allclose(self.get_array(), other.get_array(),
#                               rtol=rtol, atol=atol):
            if traceback:
                print("{0}: Different data values".format(
                    self.__class__.__name__))
                print(repr(self.get_array()))
                print(repr(other.get_array()))
            return False

        # ------------------------------------------------------------
        # Still here? Then the two instances are equal.
        # ------------------------------------------------------------
        return True            
    #--- End: def

    def first_element(self):
        '''
        '''
        return self._item((slice(0, 1),)*self.ndim)
    #--- End: def
    
    def last_element(self):
        '''
        '''
        
        return self._item((slice(-1, None),)*self.ndim)
    #--- End: def
 
    def second_element(self):
        '''
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
<Data: [1, 2, 3, 4] metre>
>>> d[1, -1] = masked
>>> d.unique()
<Data: [1, 2, 4] metre>

        '''
        array = self.get_array()
        array = numpy.unique(array)

        if numpy.ma.is_masked(array):
            array = array.compressed()

        out = self.copy(data=False)
        out._set_Array(array, copy=False)

        return out
    #--- End: def

#--- End: class

