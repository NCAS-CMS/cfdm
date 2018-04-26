import abc

from .properties import Properties


class PropertiesData(Properties):
    '''Base class for a data array with descriptive properties.

    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, properties={}, data=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

          *Example:*
             ``properties={'standard_name': 'altitude'}``
        
        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.

    data: `Data`, optional
        Set the data. Ignored if the *source* parameter is set.
        
        The data also may be set after initialisation with the
        `set_data` method.
        
    source: optional  
        Initialise the *properties* and *data* parameters from the
        object given by *source*.

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        # Initialise properties
        super(PropertiesData, self).__init__(properties=properties,
                                             source=source, copy=copy)

        if source is not None:
            if not _use_data:
                data = None
            else:
                try:
                    data = source.get_data(None)
                except AttributeError:
                    data = None
        #--- End: if

        if _use_data and data is not None:
            self.set_data(data, copy=copy)
    #--- End: def

    def __array__(self):
        '''The numpy array interface.

:Returns: 

    out: `numpy.ndarray`
        A numpy array of the data.

        '''
        return self.get_array()
    #--- End: def

#    def __data__(self):
#        '''
#        '''
#        data = self.get_data(None)
#        if data is None:
#            raise ValueError("sdif n;ujnr42[ 4890yh 8u;jkb")
#
#        return data
#    #--- End: def
    
    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def data(self):
        '''
        '''
        return self.get_data()
    #--- End: def

    @property
    def dtype(self):
        '''Describes the format of the elements in the data.

:Examples:

>>> f.dtype
dtype('float64')

        '''
        return self.get_data().dtype
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def ndim(self):
        '''The number of dimensions of the data.

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

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def shape(self):
        '''Shape of the data.

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

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
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

    def copy(self, data=True):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.6

:Examples 1:

>>> g = f.copy()

:Parameters:

    data: `bool`, optional
        If False then do not copy the data. By default the data is
        copied.

:Returns:

    out:
        The deep copy.

:Examples 2:

>>> g = f.copy(data=False)

        '''
        return type(self)(source=self, copy=True, _use_data=data)
    #--- End: def

    def del_data(self):
        '''Delete the data.

.. versionadded:: 1.6

.. seealso:: `get_data`, `has_data`, `set_data`

:Examples 1:

>>> f.del_data()

:Returns: 

    out: `Data` or `None`
        The removed data, or `None` if the data was not set.

:Examples 2:

>>> f.has_data()
True
>>> print f.get_data()
[0, ..., 9] m
>>> d = f.del_data()
>>> print d
[0, ..., 9] m
>>> f.has_data()
False
>>> print f.del_data()
None

        '''
        return self._del_component('data')
    #--- End: def

#    def fill_value(self, default=None):
#        '''Return the data missing data value.
#
#This is the value of the `missing_value` CF property, or if that is
#not set, the value of the `_FillValue` CF property, else if that is
#not set, ``None``. In the last case the default `numpy` missing data
#value for the array's data type is assumed if a missing data value is
#required.
#
#.. versionadded:: 1.6
#
#:Parameters:
#
#    default: optional
#        If the missing value is unset then return this value. By
#        default, *default* is `None`. If *default* is the special
#        value ``'netCDF'`` then return the netCDF default value
#        appropriate to the data array's data type is used. These may
#        be found as follows:
#
#        >>> import netCDF4
#        >>> print netCDF4.default_fillvals    
#
#:Returns:
#
#    out:
#        The missing data value, or the value specified by *default* if
#        one has not been set.
#
#:Examples:
#
#>>> f.{+name}()
#None
#>>> f._FillValue = -1e30
#>>> f.{+name}()
#-1e30
#>>> f.missing_value = 1073741824
#>>> f.{+name}()
#1073741824
#>>> del f.missing_value
#>>> f.{+name}()
#-1e30
#>>> del f._FillValue
#>>> f.{+name}()
#None
#>>> f,dtype
#dtype('float64')
#>>> f.{+name}(default='netCDF')
#9.969209968386869e+36
#>>> f._FillValue = -999
#>>> f.{+name}(default='netCDF')
#-999
#
#        '''
#        fillval = self.get_property('_FillValue', None)
#
#        if fillval is None:
#            if default == 'netCDF':
#                d = self.get_data().dtype
#                fillval = netCDF4.default_fillvals[d.kind + str(d.itemsize)]
#            else:
#                fillval = default 
#        #--- End: if
#
#        return fillval
#    #--- End: def

    def get_array(self):
        '''Return a numpy array copy the data.

Use the `get_data` method to return the data as a ``Data` object.

.. seealso:: `get_data`

:Examples 1:

>>> a = f.get_array()

:Returns:

    out: `numpy.ndarray`
        An independent numpy array of the data.

:Examples 2:

>>> d = Data([1, 2, 3.0], 'km')
>>> array = d.get_array()
>>> isinstance(array, numpy.ndarray)
True
>>> print array
[ 1.  2.  3.]
>>> d[0] = -99 
>>> print array[0] 
1.0
>>> array[0] = 88
>>> print d[0]
-99.0 km

        '''
        data = self.get_data(None)
        if data is None:
            raise ValueError("{!r} has no data".format(self.__class__.__name__))
        
        return data.get_array()
    #--- End: def

    def get_data(self, *default):
        '''Return the data.

Note that the data are returned in a `Data` object. Use the `get_array`
method to return the data as a `numpy` array.

.. seealso:: `del_data`, `get_array`, `has_data`, `set_data`

:Examples 1:

>>> d = f.get_data()

:Parameters:

    default: optional
        Return *default* if and only if the data have not been set.

:Returns:

    out:
        The data. If the data has not been set, then return the value
        of *default* parameter if provided.

:Examples 2:

>>> f.del_data()
>>> f.get_data('No data')
'No data'

        '''
        try:
            data = self._get_component('data', None, None)
        except AttributeError:
            raise AttributeError("There is no data")

        if data is None:
            if  default:
                return default[0]

            raise ValueError("{!r} has no data".format(self.__class__.__name__))
        
        units = self.get_property('units', None)
        if units is not None:
            data.set_units(units)

        calendar = self.get_property('calendar', None)
        if calendar is not None:
            data.set_calendar(calendar)

        return data        
    #--- End: def

    def has_data(self):
        '''True if there are data.
        
.. versionadded:: 1.6

.. seealso:: `del_data`, `get_data`, `set_data`

:Examples 1:

>>> x = f.has_data()

:Returns:

    out: `bool`
        True if there are data, otherwise False.

:Examples 2:

>>> if f.has_data():
...     print 'Has data'

        '''     
        return self._has_component('data')
    #--- End: def

    def set_data(self, data, copy=True):
        '''Set the data.

If the data has units or calendar properties then they are removed
prior to insertion.

.. versionadded:: 1.6


.. seealso:: `del_data`, `get_data`, `has_data`

:Examples 1:

>>> f.set_data(d)

:Parameters:

    data: `Data`
        The data to be inserted.

    copy: `bool`, optional
        If False then do not copy the data prior to insertion. By
        default the data are copied.

:Returns:

    `None`

:Examples 2:

>>> f.set_data(d, copy=False)

        '''
        if copy:
            data = data.copy()

        data.set_units(None)
        data.set_calendar(None)
        
        self._set_component('data', None, data)
    #--- End: def

#--- End: class
