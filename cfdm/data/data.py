import itertools

import numpy

from ..constants  import masked
from ..cfdatetime import rt2dt, st2rt, st2dt
from ..units      import Units
from ..functions  import RTOL, ATOL, parse_indices, set_subspace, _numpy_allclose

from .array import Array, NumpyArray

_units_None = Units()
_units_1    = Units('1')


# ====================================================================
#
# Data object
#
# ====================================================================

class Data(object):
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

    def __init__(self, data=None, units=None, fill_value=None,
                 dt=False):
        '''**Initialization**

:Parameters:

    data: array-like, optional
        The data for the array.

    units: `str` or `Units`, optional
        The units of the data. By default the array elements are
        dimensionless.

    fill_value: optional 
        The fill value of the data. By default, or if None, the numpy
        fill value appropriate to the array's data type will be used.

    dt: `bool`, optional
        If True then strings (such as ``'1990-12-01 12:00'``) given by
        the *data* argument are interpreted as date-times. By default
        they are not interpreted as arbitrary strings.

:Examples:

>>> d = Data(5)
>>> d = Data([1,2,3], units='K')
>>> import numpy   
>>> d = Data(numpy.arange(10).reshape(2,5), units=Units('m/s'), fill_value=-999)
>>> d = Data(tuple('fly'))

        '''      
        units = Units(units)
        
        self._Units       = units
        self._fill_value  = fill_value
        self._array       = None

        # The _HDF_chunks attribute is.... Is either None or a
        # dictionary. DO NOT CHANGE IN PLACE.
        self._HDF_chunks = {}

        if data is None:
            return

        if isinstance(data, self.__class__):
            data = data._array
            
        if not isinstance(data, Array):
            if not isinstance(data, numpy.ndarray):
                data = numpy.asanyarray(data)

            if (data.dtype.kind == 'O' and not dt and 
                hasattr(data.item((0,)*data.ndim), 'timetuple')):
                # We've been given one or more date-time objects
                dt = True
        #--- End: if
        
        # ------------------------------------------------------------
        # Deal with date-times
        # ------------------------------------------------------------
        if dt or units.isreftime:
            kind = data.dtype.kind
            first = (0,)*data.ndim
            if kind == 'S':
                # Convert date-time strings to reference time floats
                if not units:
                    x = st2dt(data[first]).item()
                    YMD = '-'.join(map(str, (x.year, x.month, x.day)))
                    units = Units('days since '+YMD, units._calendar)
                    self._Units = units
            
                data = st2rt(data, None, units)
            elif kind == 'O':
                # Convert date-time objects to reference time floats
                if not units:
                    # Set the units to something that is (hopefully)
                    # close to all of the datetimes, in an attempt to
                    # reduce errors arising from the conversion to
                    # reference times
                    x = data.item(first)
                    YMD = '-'.join(map(str, (x.year, x.month, x.day)))
                    units = Units('days since '+YMD, units._calendar)
                    self._Units = units
                    
                data = dt2rt(data, None, units)
        #--- End: if

        if isinstance(data, Array):
            self._array = data
        else:
            self._array = NumpyArray(data)
    #--- End: def

    def __array__(self, *dtype):
        '''

Returns a numpy array copy the data array.

If the data array is stored as date-time objects then a numpy array of
numeric reference times will be returned.

:Returns:

    out: `numpy.ndarray`
        The numpy array copy the data array.

:Examples:

>>> (d.array == numpy.array(d)).all()
True
 
'''
        if not dtype:
            return self.array
        else:
            return self.array.astype(dtype[0])
    #--- End: def

    def __deepcopy__(self, memo):
        '''Used if `copy.deepcopy` is called.

        ''' 
        return self.copy()
    #--- End: def

    def __repr__(self):
        '''The built-in function `repr`

x.__repr__() <==> repr(x)

        '''
        return '<CFDM {0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    def __str__(self):
        '''The built-in function `str`

x.__str__() <==> str(x)

        '''
        self_units = self.Units
        isreftime = self_units.isreftime

        if not self_units or self_units.equals(_units_1):
            units = None
        elif not isreftime:
            units = self_units.units
        else:
            units = getattr(self_units, 'calendar', '')
                     
        size = self.size
        ndim = self.ndim
        open_brackets  = '[' * ndim
        close_brackets = ']' * ndim

        try:
            first = self.datum(0)
        except:            
            out = ''
            if units:
                out += ' {0}'.format(units)
                
            return out
        #--- End: try
        
        if size == 1:
            if isreftime:
                # Convert reference time to date-time
                first = rt2dt(first, self_units).item()

            out = '{0}{1}{2}'.format(open_brackets, first, close_brackets)
        else:
            last = self.datum(-1)
            if isreftime:
                # Convert reference times to date-times
                first, last = rt2dt(numpy.ma.array((first, last)), self_units)

            if size >= 3:
                out = '{0}{1}, ..., {2}{3}'.format(open_brackets, first,
                                                   last, close_brackets)

            else:
                out = '{0}{1}, {2}{3}'.format(open_brackets, first,
                                              last, close_brackets)
        #--- End: if
        
        if units:
            out += ' {0}'.format(units)
            
        return out
    #--- End: def

    def __getitem__(self, indices):
        '''Implement indexing

x.__getitem__(indices) <==> x[indices]

        '''
        return type(self)(self._array[indices],
                          self.Units,
                          self.fill_value)
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
        # If value has Units then make sure that they're the same
        # as self.Units
        if (isinstance(value, self.__class__) and
            self.Units and
            value.Units and
            value.Units != self.Units):
            raise ValueError(
"Can't set to values with different units: {!r}".format(value.Units))

        array = self._array[...]

        if value is masked and not numpy.ma.isMA(array):
            # The assignment is masking elements, so turn a
            # non-masked array into a masked one.
            array = array.view(numpy.ma.MaskedArray)
        else:
            value = numpy.asanyarray(value)

        indices = parse_indices(array.shape, indices)
        
        set_subspace(array, indices, value)
        
        self._array = NumpyArray(array)
    #--- End: def

    def __int__(self):
        if self.size != 1:
            raise TypeError(
                "only length-1 arrays can be converted to Python scalars")
        return int(self.datum())
    #--- End: def

    def __iter__(self):
        '''

Efficient iteration.

x.__iter__() <==> iter(x)

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
<CF Data: [1, 2] metres>
<CF Data: [4, 5] metres>

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
            i = iter(self.array)
            while 1:
                yield i.next()
        else:
            # ndim > 1
            for n in xrange(self.shape[0]):
                yield self[n, ...].squeeze(0, copy=False)
    #--- End: def

    def __eq__(self, y):
        return type(self)(self.varray == y)

    def __ne__(self, y):
        return type(self)(self.varray != y)
    
    @property
    def isscalar(self):
        '''

True if the data array is a 0-d scalar array.

:Examples:

>>> d.ndim
0
>>> d.isscalar
True

>>> d.ndim >= 1
True
>>> d.isscalar
False

'''
        return not self.ndim
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute
    # ----------------------------------------------------------------
    @property
    def Units(self):
        '''The `Units` object containing the units of the data array.

..versionadded:: 1.6

:Examples:

>>> d.Units = Units('m')
>>> d.Units
<CF Units: m>
>>> del d.Units
>>> d.Units
<CF Units: >

        '''
        return self._Units
    #--- End: def
    @Units.setter    
    def Units(self, value):
        self._Units = Units(value)

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def data(self):
        '''

The data array object as an object identity.

:Examples:

>>> d.data is d
True

'''
        return self
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
        return self._array.dtype
    #--- End: def
    @dtype.setter
    def dtype(self, value):
        value = numpy.dtype(value)
        if value != self.dtype:
            self._array = NumpyArray(numpy.asanyarray(self.array, dtype=value))

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
    def ndim(self):
        '''

Number of dimensions in the data array.

:Examples:

>>> d.shape
(73, 96)
>>> d.ndim
2

>>> d.shape
()
>>> d.ndim
0

'''
        return self._array.ndim
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def shape(self):
        '''

Tuple of the data array's dimension sizes.

:Examples:

>>> d.shape
(73, 96)

>>> d.ndim
0
>>> d.shape
()

'''
        return self._array.shape
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def size(self):
        '''

Number of elements in the data array.

:Examples:

>>> d.shape
(73, 96)
>>> d.size
7008

>>> d.shape
(1, 1, 1)
>>> d.size
1

>>> d.ndim
0
>>> d.shape
()
>>> d.size
1

'''
        return self._array.size
    #--- End: def

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
        return self.varray.copy()
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def varray(self):
        '''A numpy array view the data.

.. note:: If the data array is stored as date-time objects then a
          numpy array of numeric reference times will be returned. A
          numpy array of date-time objects may be returned by the
          `dtarray` attribute.

.. seealso:: `array`, `dtarray`

:Examples:

        '''
        array = self._array[...]

        if self.fill_value is not None and numpy.ma.isMA(array):
            array.set_fill_value(self.fill_value)

        self._array = NumpyArray(array)

        return array
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def dtarray(self):
        '''
        '''
        return rt2dt(self.array, self.Units)
    #--- End: def

    @property
    def mask(self):
        '''The boolean missing data mask of the data.

The boolean mask has True where the data has missing values and False
otherwise.

:Examples:

>>> d.shape
(12, 73, 96)
>>> m = d.mask
>>> m
<CF Data: [[[False, ..., True]]]>
>>> m.dtype
dtype('bool')
>>> m.shape
(12, 73, 96)

        '''
        array = self.array
        
        if not numpy.ma.is_masked(array):
            mask = numpy.zeros(self.shape, dtype=bool)
        else:
            mask = array.mask
            
        return type(self)(mask)
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
<CF Data: [1, 2]>

>>> Data.asdata(numpy.array([1, 2]))
<CF Data: [1, 2]>

        '''
        data = getattr(d, '__data__', None)
        if data is None:
            return cls(d)

        data = data()
        if copy:
            return data.copy()
        else:
            return data
    #--- End: def

    def close(self):
        '''
'''
        self._array.close()
    #--- End: def
    
    def open(self):
        '''
'''
        self._array.open(keep_open=True)
    #--- End: def

    def copy(self):
        '''Return a deep copy.

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

:Returns:

    out: 
        The deep copy.

:Examples:

>>> e = d.copy()

        '''        
        new = type(self)(self._array, self.Units, self.fill_value)

        new.HDF_chunks(self.HDF_chunks())

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

        array = numpy.amax(self.varray, axis=axes, keepdims=True)

        d = self.copy()
        d._array = NumpyArray(array)
        
        if d._HDF_chunks:            
            HDF = {}
            for axis in axes:
                HDF[axis] = None

            d.HDF_chunks(HDF)
        #--- End: if

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

        array = numpy.amin(self.varray, axis=axes, keepdims=True)
            
        d = self.copy()
        d._array = NumpyArray(array)

        if d._HDF_chunks:            
            HDF = {}
            for axis in axes:
                HDF[axis] = None

            d.HDF_chunks(HDF)
        #--- End: if

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
        return itertools.product(*[xrange(0, r) for r in self.shape])  
    #--- End: def

#    def override_units(self, units, copy=True):
#        '''Override the data array units.
#
#Not to be confused with setting the `Units` attribute to units which
#are equivalent to the original units. This is different because in
#this case the new units need not be equivalent to the original ones
#and the data array elements will not be changed to reflect the new
#units.
#
#..versionadded:: 1.6
#
#.. seealso:: `Units`
#
#:Parameters:
#
#    units: `str` or `Units`
#        The new units for the data array.
#
#    copy: `bool`, optional
#        If False then update the data array in place. By default a new
#        data array is created.
#
#:Returns:
#
#    out: `Data`
#
#:Examples:
#
#>>> d = Data(1012.0, 'hPa')
#>>> d.override_units('km')
#>>> d.Units
#<CF Units: km>
#>>> d.datum(0)
#1012.0
#>>> d.override_units(Units('watts'))
#>>> d.Units
#<CF Units: watts>
#>>> d.datum(0)
#1012.0
#
#        '''
#        if copy:
#            d = self.copy()
#        else:
#            d = self
#
#        d._Units = Units(units)
#
#        return d
#    #--- End: def

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

        array = numpy.sum(self.varray, axis=axes, keepdims=True)
            
        d = self.copy()
        d._array = NumpyArray(array)

        if d._HDF_chunks:            
            HDF = {}
            for axis in axes:
                HDF[axis] = None

            d.HDF_chunks(HDF)
        #--- End: if
        
        return d
    #--- End: def

    def HDF_chunks(self, *chunks):
        '''
        '''
        _HDF_chunks = self._HDF_chunks

        org_HDF_chunks = dict([(i, _HDF_chunks.get(i))
                               for i in range(self.ndim)])

        org_HDF_chunks = _HDF_chunks.copy()
        
        if not chunks:
            return org_HDF_chunks

#        if _HDF_chunks is None:
#            _HDF_chunks = {}
#        else:
#        _HDF_chunks = _HDF_chunks.copy()

#        org_HDF_chunks = _HDF_chunks.copy()
            
 
        if not chunks:
            return org_HDF_chunks

        chunks = chunks[0]
        
        if chunks is None:
            # Clear all chunking
            self._HDF_chunks = {}
            return org_HDF_chunks

#        for i in range(self.ndim):
            

        for axis, size in chunks.iteritems():
            if size is not None:
                _HDF_chunks[axis] = size
            else:
                _HDF_chunks.pop(axis, None)
                
#        if _HDF_chunks.values() == [None] * len(_HDF_chunks):
#            _HDF_chunks = None

#        self._HDF_chunks = _HDF_chunks
            
        return org_HDF_chunks
    #--- End: def

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
        
        array = numpy.squeeze(self.varray, axes)

        d._array = NumpyArray(array)

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

        array = numpy.expand_dims(self.varray, position)

        d._array = NumpyArray(array)

        if d._HDF_chunks:            
            HDF = {}
            for axis in axes:
                HDF[axis] = None

            d.HDF_chunks(HDF)
        #--- End: if

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

        array = numpy.transpose(self.varray, axes=axes)
        
        d._array = NumpyArray(array)

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
<CF Data: [1, 2, 3, 4] metre>
>>> d[1, -1] = masked
>>> d.unique()
<CF Data: [1, 2, 4] metre>

        '''
        array = numpy.unique(self.array)

        if numpy.ma.is_masked(array):
            array = array.compressed()
            
        return type(self)(array, self.Units, self.fill_value)
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
        for attr in ('ndim', 'shape', 'size', 'dtype', 'fill_value', 'Units', 'array'):
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

  * The have the same units

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
        self_Units  = self.Units
        other_Units = other.Units
        if self_Units != other_Units:
            if traceback:
                print("{0}: Different units: {!r}, {!r}".format(
                    self.__class__.__name__, self.Units, other.Units))
            return False
        #--- End: if

        # Check that each instance has the same fill value
        if not ignore_fill_value and self.fill_value != other.fill_value:
            if traceback:
                print("{0}: Different fill values: {1}, {2}".format(
                    self.__class__.__name__, 
                    self.fill_value, other.fill_value))
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

        if not _numpy_allclose(self.array, other.array, rtol=rtol, atol=atol):
            if traceback:
                print("{0}: Different data array values".format(
                    self.__class__.__name__))
            return False

        # ------------------------------------------------------------
        # Still here? Then the two instances are equal.
        # ------------------------------------------------------------
        return True            
    #--- End: def

    def datum(self, *index):
        '''Return an element of the data array as a standard Python scalar.

The first and last elements are always returned with ``d.datum(0)``
and ``d.datum(-1)`` respectively, even if the data array is a scalar
array or has two or more dimensions.

The returned object is of the same type as is stored internally.

.. seealso:: `array`, `dtarray`, `varray`

:Parameters:

    index: *optional*
        Specify which element to return. When no positional arguments
        are provided, the method only works for data arrays with one
        element (but any number of dimensions), and the single element
        is returned. If positional arguments are given then they must
        be one of the following:

          * An integer. This argument is interpreted as a flat index
            into the array, specifying which element to copy and
            return.
         
              Example: If the data aray shape is ``(2, 3, 6)`` then:
                * ``d.datum(0)`` is equivalent to ``d.datum(0, 0, 0)``.
                * ``d.datum(-1)`` is equivalent to ``d.datum(1, 2, 5)``.
                * ``d.datum(16)`` is equivalent to ``d.datum(0, 2, 4)``.

            If *index* is ``0`` or ``-1`` then the first or last data
            array element respecitively will be returned, even if the
            data array is a scalar array.
        ..
         
          * Two or more integers. These arguments are interpreted as a
            multidimensionsal index to the array. There must be the
            same number of integers as data array dimensions.
        ..
         
          * A tuple of integers. This argument is interpreted as a
            multidimensionsal index to the array. There must be the
            same number of integers as data array dimensions.
         
              Example:
                ``d.datum((0, 2, 4))`` is equivalent to ``d.datum(0,
                2, 4)``; and ``d.datum(())`` is equivalent to
                ``d.datum()``.

:Returns:

    out: scalar
        A copy of the specified element of the array as a suitable
        Python scalar.

:Examples:

>>> d = Data(2)
>>> d.datum()
2
>>> 2 == d.datum(0) == d.datum(-1) == d.datum(())
True

>>> d = Data([[2]])
>>> 2 == d.datum() == d.datum(0) == d.datum(-1)
True
>>> 2 == d.datum(0, 0) == d.datum((-1, -1)) == d.datum(-1, 0)
True

>>> d = Data([[4, 5, 6], [1, 2, 3]], 'metre')
>>> d[0, 1] = masked
>>> print d
[[4 -- 6]
 [1 2 3]]
>>> d.datum(0)
4
>>> d.datum(-1)
3
>>> d.datum(1)
masked
>>> d.datum(4)
2
>>> d.datum(-2)
2
>>> d.datum(0, 0)
4
>>> d.datum(-2, -1)
6
>>> d.datum(1, 2)
3
>>> d.datum((0, 2))
6

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
                    # e.g. index=345
                    if index < 0:
                        index += self.size

                    index = numpy.unravel_index(index, self.shape)
                elif len(index) == self.ndim:
                    # e.g. index=[0, 3]
                    index = tuple(index)
                else:
                    raise ValueError(
                        "Incorrect number of indices for {} array".format(
                            self.__class__.__name__))
                #--- End: if
            elif n_index == self.ndim:
                index = tuple(index)
            else:
                raise ValueError(
                    "Incorrect number of indices for {} array".format(
                        self.__class__.__name__))

            array = self[index].array

        elif self.size == 1:
            array = self.array
        else:
            raise ValueError(
                "Can't convert {} with size {} to a Python scalar".format(
                    self.__class__.__name__, self.size))

        if not numpy.ma.isMA(array):
            return array.item()
        
        mask = array.mask
        if mask is numpy.ma.nomask or not mask.item():
            return array.item()

        return numpy.ma.masked
    #--- End: def

    # ----------------------------------------------------------------
    # Compression class methods
    # ----------------------------------------------------------------
    @classmethod
    def compression_initialize_gathered(cls, uncompressed_shape):
        '''Create an empty Data array
        
:Parameters:

:Returns:
 
    out: `Data`

        '''
        array = numpy.ma.masked_all(uncompressed_shape)
                   
        return cls(array)
    #--- End: def

    @classmethod
    def DSG_initialize_indexed_contiguous(cls,
                                          instance_dimension_size,
                                          element_dimension_1_size,
                                          element_dimension_2_size,
                                          profiles_per_instance,
                                          elements_per_profile,
                                          profile_indices):
        '''Create an empty Data array which has dimensions
        (instance_dimension_size, element_dimension_1_size,
        element_dimension_2_size)
        
:Parameters:

    instance: `Data`
        Number of instances

    features_per_instance: `Data`
        Number of features per instance

    elements_per_feature: `Data`
        Number of elements per feature

    profile_indices: `Data`
        The indices of the sample dimension which define the start
        position of each profile of each instance.

:Returns:
 
    out: `Data`

        '''
        array = numpy.ma.masked_all((instance_dimension_size,
                                     element_dimension_1_size,
                                     element_dimension_2_size))
                   
        return cls(array)
    #--- End: def

    @classmethod
    def DSG_initialize_contiguous(cls,
                                  instance_dimension_size,
                                  element_dimension_size,
                                  elements_per_instance):
        '''Create an empty Data array which has dimensions
        (instance_dimension_size, element_dimension_size)

instance_dimension_size = count.size

element_dimension_size  = count.max()


:Parameters:

    count: `Data`

:Returns:
 
    out: `Data`

        '''
        array = numpy.ma.masked_all((instance_dimension_size,
                                     element_dimension_size))
        
        return cls(array)
    #--- End: def

    @classmethod
    def DSG_initialize_indexed(cls,
                               instance_dimension_size,
                               element_dimension_size,
                               index):
        '''Create an empty Data array which has shape
        (instance_dimension_size, element_dimension_size)

:Parameters:

    instance_dimension_size: `int`

    element_dimension_size: `int`

    index: data-like

:Returns:
 
    out: `Data`

        '''
        array = numpy.ma.masked_all((instance_dimension_size,
                                     element_dimension_size))
        
        return cls(array)
    #--- End: def

    @classmethod
    def compression_fill_gathered(cls, data, dtype, units, fill_value,
                                  gathered_array, sample_axis, indices):
        '''
        
    data: `Data`

    gathered_array:
        
    sample_axes: `int`

    indices: `Data`

        '''
        data.dtype = dtype
        data.Units = units
        data.fill_value = fill_value

        uncompressed_array = data.varray 

        # The gathered array
        gathered_array = gathered_array.array
        
#        # Initialize the full, uncompressed output array with missing
#        # data everywhere
#        uarray = numpy.ma.masked_all(self.shape, dtype=array.dtype)

        gathered_indices     = [slice(None)] * gathered_array.ndim
        uncompressed_indices = [slice(None)] * uncompressed_array.ndim        
        
#        sample_axis           = uncompression['axis']
#        uncompression_indices = uncompression['indices']
        
        compressed_axes = range(sample_axis, data.ndim - (gathered_array.ndim - sample_axis - 1))
        n_compressed_axes = len(compressed_axes)
        
        zzz = [reduce(mul, [uncompressed_array.shape[i] for i in compressed_axes[i:]], 1)
               for i in range(1, n_compressed_axes)]
        
        xxx = [[0] * indices.size] * n_compressed_axes

        for n, b in enumerate(indices):
            xxx = zeros[:]
            for i, z in enumerate(zzz):                
                if b >= z:
                    (a, b) = divmod(b, z)
                    xxx[i][n] = a
                    xxx[-1][n] = b
            #--- End: for
                        
            for j, x in izip(compressed_axes, xxx):
                p_indices[j] = x
                    
        #--- End: for

        uncompressed_array[tuple(uncompressed_indices)] = gathered_array.varray

        return data
    #--- End: def

    @classmethod
    def DSG_fill_indexed(cls, data, dtype, units, fill_value,
                         ragged_array, index):
        '''sdfsdfsd

:Parameters:

    data: `Data`
        The `Data` object to filled as an incomplete orthogonal
        array. The instance dimension must be in position 0 and the
        element dimension must be in position 1.
 
    ragged_array: 
        
    index: `Data`

        '''
        data.dtype = dtype
        data.Units = units
        data.fill_value = fill_value

        array = data.varray

        for i in range(data.shape[1]): #index.unique():
            sample_dimension_indices = numpy.where(index == i)[0]
            
            indices = (slice(i, i+1),
                       slice(0, len(sample_dimension_indices)))

            array[indices] = ragged_array[sample_dimension_indices]
        #--- End: for

        return data
    #--- End: def

    @classmethod
    def DSG_fill_contiguous(cls, data, dtype, units, fill_value,
                            ragged_array, elements_per_feature):
        '''
        
    data: `Data`

    ragged_array:
        
    elements_per_feature: `Data`

        '''
        data.dtype = dtype
        data.Units = units
        data.fill_value = fill_value

        array = data.varray 

        start = 0 
        for i, n in enumerate(elements_per_feature):
            n = int(n)
            sample_indices = slice(start, start + n)

            indices = (slice(i, i+1),
                       slice(0, sample_indices.stop - sample_indices.start))
                             
            array[indices ] = ragged_array[sample_indices]
                             
            start += n
        #--- End: for

        return data
    #--- End: def

    @classmethod
    def DSG_fill_indexed_contiguous(cls, data, dtype, units,
                                    fill_value, ragged_array,
                                    profiles_per_instance,
                                    elements_per_profile,
                                    profile_indices):
        '''
        
    data: `Data`

    ragged_array: array-like
        
    profiles_per_instance: `Data`

    elements_per_profile: `Data`

    profile_indices: `Data`
        The indices of the sample dimension which define the start
        position of each profile of each instance.

        '''
        data.dtype = dtype
        data.Units = units
        data.fill_value = fill_value

        array = data.varray 

        # Loop over instances
        for i in range(array.shape[0]):

            # For all of the profiles in ths instance, find the
            # locations in the elements_per_profile array of the
            # number of elements in the profile
            xprofile_indices = numpy.where(profile_indices == i)[0]

            # Find the number of profiles in this instance
            n_profiles = xprofile_indices.size

            # Loop over profiles in this instance
            for j in range(array.shape[1]):
                if j >= n_profiles:
                    continue
                
                # Find the location in the elements_per_profile array
                # of the number of elements in this profile
                profile_index = xprofile_indices[j]

                if profile_index == 0:
                    start = 0
                else:                    
                    start = int(elements_per_profile[:profile_index].sum())
                    
                stop  = start + int(elements_per_profile[profile_index])
                
                sample_indices = slice(start, stop)
                
                indices = (slice(i, i+1),
                           slice(j, j+1), 
                           slice(0, sample_indices.stop - sample_indices.start))
                
                array[indices] = ragged_array[sample_indices]
        #--- End: for

        return data
    #--- End: def

#--- End: class

