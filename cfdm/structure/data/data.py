import abc

import numpy

#from .array import Array, NumpyArray

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
                 fill_value=None):
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
        self._array   = data
        self._units    = units
        self._calendar = calendar
        
        self._fill_value  = fill_value
#        self._array       = None
#
#        if data is None:
#            return
#
#        if isinstance(data, self.__class__):
#            data = data._array
#            
#        if not isinstance(data, Array) and not isinstance(data, numpy.ndarray):
#            data = numpy.asanyarray(data)
#        
#        if isinstance(data, Array):
#            self._array = data
#        else:
#            self._array = NumpyArray(data)
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
        return repr(self._array)
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
#    @dtype.setter
#    def dtype(self, value):
#        value = numpy.dtype(value)
#        if value != self.dtype:
#            self._array = NumpyArray(numpy.asanyarray(self.array, dtype=value))

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
        '''Number of dimensions in the data array.

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
        '''Tuple of the data array's dimension sizes.

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
        '''Number of elements in the data array.

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

    def copy(self):
        '''Return a deep copy.

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

:Returns:

    out: 
        The deep copy.

:Examples:

>>> e = d.copy()

        '''        
        return type(self)(data=self.get_array(copy=True),
                          units=self.units, calendar=self.calendar,
                          fill_value=self.fill_value)
    #--- End: def

    def get_array(self, copy=True):
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
        array = self._array

        if copy:
            if numpy.ma.isMA(array) and not array.ndim:
                # This is because numpy.ma.copy doesn't work for
                # scalar arrays (at the moment, at least)
                array = numpy.ma.masked_all((), dtype=array.dtype)
                array[...] = array
            else:
                array = array.copy()
        #--- End: if
        
        return array
    #--- End: def

#--- End: class

