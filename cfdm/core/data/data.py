from builtins import (str, super)

import numpy

from .. import abstract


class Data(abstract.Container):
    '''An orthogonal multidimensional array with masked values and units.

.. versionadded:: 1.7

    '''
    def __init__(self, array=None, units=None, calendar=None,
                 fill_value=None, source=None, copy=True,
                 _use_array=True):
        '''**Initialization**

:Parameters:

    array: subclass of `Array`
        The array of values. Ignored if the *source* parameter is set.

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

    source: *optional*
        Initialize the data, units, calendar and fill value from those
        of *source*.
        
    source: optional
        Initialize the array, units, calendar and fill value from
        those of *source*.

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__()
        
        if source is not None:
            try:                
                array = source._get_Array(None)
            except AttributeError:
                array = None

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

        self.set_units(units)
        self.set_calendar(calendar)   
        self.set_fill_value(fill_value)

        if _use_array:
            self._set_Array(array, copy=copy)
    #--- End: def

#    def __array__(self, *dtype):
#        '''The numpy array interface.
#
#:Returns: 
#
#    out: `numpy.ndarray`
#        An independent numpy array of the data.
#
#        '''
#        array = self.get_array()
#        if not dtype:
#            return array
#        else:
#            return array.astype(dtype[0], copy=False)
#    #--- End: def

#    def __deepcopy__(self, memo):
#        '''x.__deepcopy__() -> Deep copy of data.
#
#Used if copy.deepcopy is called on the object.
#
#        ''' 
#        return self.copy()
#    #--- End: def

#    def __repr__(self):
#        '''x.__repr__() <==> repr(x)
#
#        '''
#        try:        
#            shape = self.shape
#        except AttributeError:
#            shape = ''
#        else:
#            shape = str(shape)
#            shape = shape.replace(',)', ')')
#            
#        return '<{0}{1}: {2}>'.format(self.__class__.__name__, shape, str(self))
#    #--- End: def
#
#    def __str__(self):
#        '''x.__str__() <==> str(x)
#
#        '''
#        return str(self._get_Array(None))
#    #--- End: def
    
    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def dtype(self):
        '''Data-type of the data elements.

:Examples:

>>> d.dtype
dtype('float64')
>>> type(d.dtype)
<type 'numpy.dtype'>

        '''
        return self._get_Array().dtype        
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
        return self._get_Array().ndim
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
        return self._get_Array().shape
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
        return self._get_Array().size
    #--- End: def

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self, array=True):
        '''Return a deep copy of the data.

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

Copy-on-write is employed, so care must be taken when modifying any
attribute.

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
        return type(self)(source=self, copy=True, _use_array=array)
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
        return self._del_component('calendar')
#        value = self._calendar
#        self._calendar = None
#        return value
    #--- End: def

    def _del_Array(self):
        '''Delete the data.

:Examples 1:

>>> d.del_data()

:Returns:

    out:

:Examples 2:

>>> old = d.del_data()

        '''
        return self._del_component('data')
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
        return self._del_component('fill_value')
#        value = self._fill_value
#        self._fill_value = None        
#        return value
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
        return self._del_component('units')
#        value = self._units
#        self._units = None        
#        return value
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
        array = self._get_Array().get_array()

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
        value = self._get_component('calendar', *default)
#        value = self._calendar
        if value is None:
            if default:
                return default[0]

            raise AttributeError("{!r} has no calendar".format(
                self.__class__.__name__))
        
        return value
    #--- End: def

    def _get_Array(self, *default):
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
        array = self._get_component('array', *default)

        if array is None:
            if default:
                return default[0]     

            raise AttributeError("{!r} has no array".format(
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
        value = self._get_component('fill_value', *default)
#        value = self._fill_value
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
        value = self._get_component('units', *default)
#        value = self._units
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
        return self._set_component('calendar', calendar, copy=False)
#        self._calendar = calendar
    #--- End: def

    def _set_Array(self, array, copy=True):
        '''Set the array.

:Parameters:

    array: subclass of `Array`
        The array to be inserted.

:Returns:

    `None`

:Examples:

>>> d._set_Array(a)

        '''
        if copy:
            array = array.copy()
            
        self._set_component('array', array, copy=False)
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
#        self._fill_value = value
        self._set_component('fill_value', value, copy=False)
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
        self._set_component('units', value, copy=False)
#        self._units = value
    #--- End: def

#--- End: class

