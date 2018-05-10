import abc

import numpy

# ====================================================================
#
# Data object
#
# ====================================================================

class Data(object):
    '''

An N-dimensional data array with units and masked values.

* Contains an N-dimensional array.

* Contains the units of the array elements.

* Supports masked arrays, regardless of whether or not it was
  initialised with a masked array.

    '''
    ___metaclass__ = abc.ABCMeta
    
    def __init__(self, data=None, units=None, calendar=None,
                 fill_value=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    data: numpy.ndarray, optional
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
            if data is None:
                data = source._get_master_array()
        
            if units is None:
                units = source.get_units(None)
        
            if calendar is None:
                calendar = source.get_calendar(None)
        
            if fill_value is None:
                fill_value = source.get_fill_value(None)
        #--- End: if
        
        self._units    = units
        self._calendar = calendar
        
        self._fill_value  = fill_value

        self._set_master_array(data)
    #--- End: def

    def __array__(self):
        '''The numpy array interface.

:Returns: 

    out: `numpy.ndarray`
        A numpy array of the data.

        '''
        return self.get_array()
    #--- End: def

    def __deepcopy__(self, memo):
        '''Used if `copy.deepcopy` is called.

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
        return str(self._get_master_array(None))
    #--- End: def

    def _del_master_array(self):
        '''
        '''
        self._master_array = None
    #--- End: def
    
    def _get_master_array(self, *default):
        '''
        '''
        array = self._master_array
        if array is None and default:
            return default[0]     

        return array   
    #--- End: def
    
    def _set_master_array(self, value):
        '''
:Parameters:

    value: (subclass of) `Array`

:Returns:

    `None`
        '''
        self._master_array = value
    #--- End: def
    
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
        '''Describes the format of the elements in the data array.

:Examples:

>>> f.dtype
dtype('float64')
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
    def ndim(self):
        '''The number of dimensions of the data array.

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
        return self._get_master_array().ndim
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def shape(self):
        '''Shape of the data array.

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
        return self._get_master_array().shape
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def size(self):
        '''Number of elements in the data array.

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
        return self._get_master_array().size
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
        return type(self)(source=self, copy=True)
    #--- End: def

    def get_array(self):
        '''A numpy array copy the data.

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
        array = self._get_master_array()
        array = array[...]
        
        if numpy.ma.isMA(array) and not self.ndim:
            # This is because numpy.ma.copy doesn't work for
            # scalar arrays (at the moment, at least)
            ma_array = numpy.ma.empty((), dtype=array.dtype)
            ma_array[...] = array
            array = ma_array
        else:
            array = array.copy()

        return array
    #--- End: def

    def get_calendar(self, *default):
        '''

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
        '''

        '''
        value = getattr(self, '_units', None)
        if value is None:
            if default:
                return default[0]

            raise AttributeError("Can't get non-existent property {!r}".format('units'))
        
        return value
    #--- End: def

    def set_calendar(self, calendar):
        '''

        '''
        self._calendar = calendar
    #--- End: def

    def set_fill_value(self, value):
        '''

        '''
        self._fill_value = value
    #--- End: def

    def set_units(self, value):
        '''

        '''
        self._units = value
    #--- End: def

#--- End: class

