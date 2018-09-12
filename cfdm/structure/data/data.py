from builtins import (object, str)


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

    data: `Array`, optional
        The data array.

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
        if source is not None:
            data = source._get_Array(None)
            units = source.get_units(None)
            calendar = source.get_calendar(None)
            fill_value = source.get_fill_value(None)

        self._units    = units
        self._calendar = calendar
        
        self._fill_value  = fill_value

        self._set_Array(data)
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

Used if copy.deepcopy is called on data

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
        return str(self._get_Array(None))
    #--- End: def
    
    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _del_Array(self):
        '''Delete the data.

:Returns:

    `None`

:Examples:

>>> d._del_Array()

        '''
        self._array = None
    #--- End: def
    
    def _get_Array(self, *default):
        '''Return the data.

:Parameters:

    default: *optional*
        If there is no data then *default* if returned if set.

:Returns:

    out: `Array`
        The data stored in a subclass of an `Array` object. If the
        data has not been set then *default* is returned, if set.

:Examples:

>>> a = d._get_Array()

>>> a = d._get_Array(None)

        '''
        array = self._array
        if array is None:
            if default:
                return default[0]     

            raise AttributeError("{!r} has no data".format(self.__class__.__name__))
        
        return array   
    #--- End: def
    
    def _set_Array(self, array):
        '''Set the data.

:Parameters:

    array: `Array`
        The data to be inserted.

:Returns:

    `None`

:Examples:

>>> d._set_Array(a)

        '''
        self._array = array
    #--- End: def

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
        return self._get_Array().dtype        
    #--- End: def
    
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
    def copy(self):
        '''Return a deep copy of the data.

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

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

.. seealso:: `get_calendar`, `has_calendar`, `set_calendar`

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
AttributeError: Can't get non-existent 'calendar'
>>> print(d.get_calendar(None))
None

        '''
        value = getattr(self, '_calendar', None)
        if value is None:
            if default:
                return default[0]

            raise AttributeError("Can't get non-existent 'calendar'")
        
        return value
    #--- End: def

    def del_units(self):
        '''Delete the units.

.. seealso:: `get_units`, `has_units`, `set_units`

:Examples 1:

>>> u = d.del_units()

:Returns:

    out:
        The value of the deleted units, or `None` if units was not
        set.

:Examples 2:

>>> d.set_units('metres')
>>> d.get_units
'metres'
>>> d.del_units()
>>> d.get_units()
AttributeError: Can't get non-existent 'units'
>>> print(d.get_units(None))
None

        '''
        value = getattr(self, '_units', None)
        if value is None:
            if default:
                return default[0]

            raise AttributeError("Can't get non-existent 'units'")
        
        return value
    #--- End: def

    def get_array(self):
        '''Return an independent numpy array containing the data.

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
        return self._get_Array().get_array()
    #--- End: def

    def get_calendar(self, *default):
        '''Return the calendar.

.. seealso:: `del_calendar`, `has_calendar`, `set_calendar`

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
AttributeError: Can't get non-existent 'calendar'
>>> print(d.get_calendar(None))
None

        '''
        value = getattr(self, '_calendar', None)
        if value is None:
            if default:
                return default[0]

            raise AttributeError("Can't get non-existent property {!r}".format('calendar'))
        
        return value
    #--- End: def

    def get_fill_value(self, *default):
        '''

        '''
        value = getattr(self, '_fill_value', None)
        if value is None:
            if default:
                return default[0]

            raise AttributeError("Can't get non-existent property {!r}".format('fill_value'))
        
        return value
    #--- End: def

    def get_units(self, *default):
        '''Return the units.

.. seealso:: `del_units`, `has_units`, `set_units`

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
>>> d.get_units
'metres'
>>> d.del_units()
>>> d.get_units()
AttributeError: Can't get non-existent 'units'
>>> print(d.get_units(None))
None

        '''
        value = getattr(self, '_units', None)
        if value is None:
            if default:
                return default[0]

            raise AttributeError("Can't get non-existent 'units'")
        
        return value
    #--- End: def

    def set_calendar(self, calendar):
        '''Set the calendar.

.. seealso:: `del_calendar`, `get_calendar`, `has_calendar`

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
AttributeError: Can't get non-existent 'calendar'
>>> print(d.get_calendar(None))
None

        '''
        self._calendar = calendar
    #--- End: def

    def set_fill_value(self, value):
        '''

        '''
        self._fill_value = value
    #--- End: def

    def set_units(self, value):
        '''Set the units.

.. seealso:: `del_units`, `get_units`, `has_units`

:Examples 1:

>>> u = d.set_units('kg m-2')

:Parameters:

    value: `str`
        The new units.

:Returns:

    `None`

:Examples 2:

>>> d.set_units('watt')
>>> d.get_units
'watt'
>>> d.del_units()
>>> d.get_units()
AttributeError: Can't get non-existent 'units'
>>> print(d.get_units(None))
None

        '''
        self._units = value
    #--- End: def

#--- End: class

