from builtins import (object, str)

import numpy


class Data(object):
    '''

An N-dimensional data array with units and masked values.

* Contains an N-dimensional array.

* Contains the units of the array elements.

* Supports masked arrays, regardless of whether or not it was
  initialised with a masked array.

    '''
    def __init__(self, data=None, units=None, calendar=None,
                 fill_value=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    data:
        The data array. May be any object that exposes the
        `cfdm.structure.data.abstract.Array` interface.

    units: `str`, optional
        
    calendar: `str`, optional
        
    fill_value: optional 
        The fill value of the data. By default, or if None, the numpy
        fill value appropriate to the array's data type will be used.

    source: *optional*
        Override the *data*, *units*, *calendar* and *fill_value*
        parameters with ``source.get_data(None)``,
        ``source.get_units(None)``, ``source.get_calendar(None)`` and
        ``source.get_fill_value(None)``respectively.

        If *source* does not have one of these methods then
        corresponding parameter is set to `None`.
        
    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

>>> d = Data(5)
>>> d = Data([1,2,3])
>>> import numpy   
>>> d = Data(numpy.arange(10).reshape(2, 5), fill_value=-999)
>>> d = Data(tuple('fly'))

        '''
        if source is not None:
            try:                
                data = source.get_data(None)
            except AttributeError:
                data = None

            try:
                units = source.get_units(None)
            except AttributeError:
                units = None
                
            try:
                calendar = source.get_calendar(None)
            except AttributeError:
                calendar = None

            try:
                fill_value = source.get_fill_value(None)
            except AttributeError:
                fill_value = None
        #--- End: if

        self.set_data(data)
        self.set_units(units)
        self.set_calendar(calendar)   
        self.set_fill_value(fill_value)
    #--- End: def

    def __array__(self):
        '''The numpy array interface.

:Returns: 

    out: `numpy.ndarray`
        An independent numpy array of the data.

        '''
        return self.get_array()
    #--- End: def

    def __deepcopy__(self, memo):
        '''x.__deepcopy__() -> Deep copy of data.

Used if copy.deepcopy is called on the object.

        ''' 
        return self.copy()
    #--- End: def

    def __repr__(self):
        '''x.__repr__() <==> repr(x)

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        return str(self.get_data(None))
    #--- End: def
    
    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    
    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def data(self):
        '''Return 
        '''
        return self
    #--- End: def
    
    @property
    def dtype(self):
        '''Data-type of the data elements.

:Examples:

>>> d.dtype
dtype('float64')
>>> type(d.dtype)
<type 'numpy.dtype'>

        '''
        return self.get_data().dtype        
    #--- End: def

    @property
    def ndim(self):
        '''Number of data dimensions.

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
        return self.get_data().ndim
    #--- End: def

    @property
    def shape(self):
        '''Tuple of data dimension sizes.

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
        return self.get_data().shape
    #--- End: def

    @property
    def size(self):
        '''Number of elements in the data.

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
        return self.get_data().size
    #--- End: def

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self):
        '''Return a deep copy of the data.

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

Copy-on-write is employed, so care must be taken when modifying any
attribute.

:Returns:

    out: 
        The deep copy.

:Examples:

>>> e = d.copy()

        '''
        return type(self)(source=self, copy=True)
    #--- End: def

    def del_calendar(self):
        '''Delete the calendar.

.. seealso:: `get_calendar`, `set_calendar`

:Examples 1:

>>> u = d.del_calendar()

:Returns:

    out:
        The value of the deleted calendar, or `None` if calendar was
        not set.

:Examples 2:

>>> d.set_calendar('proleptic_gregorian')
>>> d.get_calendar
'proleptic_gregorian'
>>> d.del_calendar()
>>> d.get_calendar()
AttributeError: Can't get non-existent calendar
>>> print(d.get_calendar(None))
None

        '''
        value = self._calendar
        self._calendar = None
        return value
    #--- End: def

    def del_data(self):
        '''Delete the data.

:Examples 1:

>>> d.del_data()

:Returns:

    out:

:Examples 2:

>>> old = d.del_data()

        '''
        array = self._data
        self._data = None
        return array
    #--- End: def
    
    def del_fill_value(self):
        '''Delete the fill value.

.. seealso:: `get_fill_value`, `set_fill_value`

:Examples 1:

>>> f = d.del_fill_value()

:Returns:

    out:
        The value of the deleted fill value, or `None` if fill value
        was not set.

:Examples 2:

>>> f.set_fill_value(-9999)
>>> f.get_fill_value()
-9999
>>> print(f.del_fill_value())
-9999
>>> f.get_fill_value()
AttributeError: Can't get non-existent fill value
>>> f.get_fill_value(10**10)
10000000000
>>> print(f.get_fill_value(None))
None
>>> f.set_fill_value(None)
>>> print(f.get_fill_value())
None

        '''
        value = self._fill_value
        self._fill_value = None        
        return value
    #--- End: def

    def del_units(self):
        '''Delete the units.

.. seealso:: `get_units`, `set_units`

:Examples 1:

>>> u = d.del_units()

:Returns:

    out:
        The value of the deleted units, or `None` if units was not
        set.

:Examples 2:

>>> d.set_units('metres')
>>> d.get_units()
'metres'
>>> d.del_units()
>>> d.get_units()
AttributeError: Can't get non-existent units
>>> print(d.get_units(None))
None

        '''
        value = self._units
        self._units = None        
        return value
    #--- End: def

    def get_array(self):
        '''Return an independent numpy array containing the data.

If a fill value has been set (see `set_fill_value`) then it will be
used, otherwise the default numpy fill value appropriate to the data
type will be used.

:Returns:

    out: `numpy.ndarray`
        An independent numpy array of the data.

:Examples:

>>> d = Data([1, 2, 3.0], 'km')
>>> n = d.get_array()
>>> isinstance(n, numpy.ndarray)
True
>>> print(n)
[ 1.,   2.,   3.]
>>> n[0] = 88
>>> print(repr(d))
<Data: [1.0, 2.0, 3.0] km>

        '''
        array = self.get_data().get_array()

        # Set the numpy array fill value
        if numpy.ma.isMA(array):
            array.set_fill_value(self.get_fill_value(None))

        return array
    #--- End: def

    def get_calendar(self, *default):
        '''Return the calendar.

.. seealso:: `del_calendar`, `set_calendar`

:Examples 1:

>>> u = d.get_calendar()

:Parameters:

    default: optional
        Return *default* if calendar has not been set.

:Returns:

    out:
        The calendar. If calendar has not been set then return the
        value of *default* parameter, if provided.

:Examples 2:

>>> d.set_calendar('julian')
>>> d.get_calendar
'metres'
>>> d.del_calendar()
>>> d.get_calendar()
AttributeError: Can't get non-existent calendar
>>> print(d.get_calendar(None))
None

        '''
        value = self._calendar
        if value is None:
            if default:
                return default[0]

            raise AttributeError("{!r} has no calendar".format(
                self.__class__.__name__))
        
        return value
    #--- End: def

    def get_data(self, *default):
        '''Return the data.

:Examples 1:

>>> a = d.get_data()

:Parameters:

    default: *optional*
        If there is no data then *default* if returned if set.

:Returns:

    out:
        The data. If the data has not been set then *default* is
        returned, if set.

:Examples 2:

>>> a = d.get_data(None)

        '''
        array = self._data
        if array is None:
            if default:
                return default[0]     

            raise AttributeError("{!r} has no data".format(
                self.__class__.__name__))
        
        return array   
    #--- End: def

    def get_fill_value(self, *default):
        '''Return the missing data value.

.. seealso:: `del_fill_value`, `set_fill_vlaue`

:Examples 1:

>>> f = d.get_fill_value()

:Parameters:

    default: optional
        Return *default* if fill value has not been set.

:Returns:

    out:
        The fill value. If fill value has not been set then return the
        value of *default* parameter, if provided.

:Examples 2:

>>> f.set_fill_value(-9999)
>>> f.get_fill_value()
-9999
>>> print(f.del_fill_value())
-9999
>>> f.get_fill_value()
AttributeError: Can't get non-existent fill value
>>> f.get_fill_value(10**10)
10000000000
>>> print(f.get_fill_value(None))
None
>>> f.set_fill_value(None)
>>> print(f.get_fill_value())
None

        '''
        value = self._fill_value
        if value is None:
            if default:
                return default[0]

            raise AttributeError("{!r} has no fill value".format(
                self.__class__.__name__))
        
        return value
    #--- End: def

    def get_units(self, *default):
        '''Return the units.

.. seealso:: `del_units`, `set_units`

:Examples 1:

>>> u = d.get_units()

:Parameters:

    default: optional
        Return *default* if units has not been set.

:Returns:

    out:
        The units. If units has not been set then return the value of
        *default* parameter, if provided.

:Examples 2:

>>> d.set_units('metres')
>>> d.get_units()
'metres'
>>> d.del_units()
>>> d.get_units()
AttributeError: Can't get non-existent units
>>> print(d.get_units(None))
None

        '''
        value = self._units
        if value is None:
            if default:
                return default[0]

            raise AttributeError("{!r} has no units".format(
                self.__class__.__name__))
        
        return value
    #--- End: def

    def set_calendar(self, calendar):
        '''Set the calendar.

.. seealso:: `del_calendar`, `get_calendar`

:Examples 1:

>>> u = d.set_calendar('365_day')

:Parameters:

    value: `str`
        The new calendar.

:Returns:

    `None`

:Examples 2:

>>> d.set_calendar('none')
>>> d.get_calendar
'none'
>>> d.del_calendar()
>>> d.get_calendar()
AttributeError: Can't get non-existent calendar
>>> print(d.get_calendar(None))
None

        '''
        self._calendar = calendar
    #--- End: def

    def set_data(self, data):
        '''Set the data.

:Parameters:

    data:
        The data to be inserted. May be any object that exposes the
        `cfdm.structure.data.abstract.Array` interface.

:Returns:

    `None`

:Examples:

>>> d.set_data(a)

        '''
        self._data = data
    #--- End: def

    def set_fill_value(self, value):
        '''Set the missing data value.

.. seealso:: `del_fill_value`, `get_fill_vlaue`

:Examples 1:

>>> f = d.set_fill_value(-256)

:Parameters:

    value: scalar
        The new fill value.

:Returns:

    `None`

:Examples 2:

>>> f.set_fill_value(-9999)
>>> f.get_fill_value()
-9999
>>> print(f.del_fill_value())
-9999
>>> f.get_fill_value()
AttributeError: Can't get non-existent fill value
>>> f.get_fill_value(10**10)
10000000000
>>> print(f.get_fill_value(None))
None
>>> f.set_fill_value(None)
>>> print(f.get_fill_value())
None

        '''
        self._fill_value = value
    #--- End: def

    def set_units(self, value):
        '''Set the units.

.. seealso:: `del_units`, `get_units`

:Examples 1:

>>> u = d.set_units('kg m-2')

:Parameters:

    value: `str`
        The new units.

:Returns:

    `None`

:Examples 2:

>>> d.set_units('watt')
>>> d.get_units()
'watt'
>>> d.del_units()
>>> d.get_units()
AttributeError: Can't get non-existent units
>>> print(d.get_units(None))
None

        '''
        self._units = value
    #--- End: def

#--- End: class

