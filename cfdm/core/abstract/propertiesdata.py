from future.utils import with_metaclass
from builtins import super

import abc

from . import Properties


class PropertiesData(with_metaclass(abc.ABCMeta, Properties)):
    '''Abstract base class for a data array with descriptive properties.

    '''
    def __init__(self, properties=None, data=None, source=None,
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
        Override the *properties* and *data* parameters with
        ``source.properties()`` and ``source.get_data(None)``
        respectively.

        If *source* does not have one of these methods, then the
        corresponding parameter is not set.
        
    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
#        super().__init__(properties=properties, source=source,
#                         copy=copy)
        Properties.__init__(self, properties=properties,
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

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def data(self):
        '''
        '''
        return self.get_data()
    #--- End: def

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
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
>>> g.has_data()
False

        '''
        return type(self)(source=self, copy=True, _use_data=data)
    #--- End: def

    def del_data(self):
        '''Remove the data.

.. versionadded:: 1.6

.. seealso:: `get_data`, `has_data`, `set_data`

:Examples 1:

>>> d = f.del_data()

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

    def get_array(self):
        '''Return a numpy array copy the data.

Use the `get_data` method to return the data as a `Data` object.

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

    out: `Data` or *default*
        The data. If the data has not been set, then the *default*
        parameter is returned, if provided.

:Examples 2:

>>> f.has_data()
True
>>> d = f.del_data()
>>> f.has_data()
False
>> print(f.get_data(None))
None

        '''
        data = self._get_component('data', None)

        if data is None:
            if default:
                return default[0]

            raise ValueError("{!r} has no data".format(self.__class__.__name__))
        
        units = self.get_property('units', None)
        if units is not None:
            data.set_units(units)

        calendar = self.get_property('calendar', None)
        if calendar is not None:
            data.set_calendar(calendar)

        fill_value = self.get_property('fill_value', None)
        if fill_value is not None:
            data.set_fill_value(fill_value)

        return data        
    #--- End: def

    def has_data(self):
        '''Whether data has been set.
        
.. versionadded:: 1.6

.. seealso:: `del_data`, `get_data`, `set_data`

:Examples 1:

>>> x = f.has_data()

:Returns:

    out: `bool`
        True if there are data, otherwise False.

:Examples 2:

>>> f.has_data()
True
>>> d = f.del_data()
>>> f.has_data()
False
>> print(f.get_data(None))
None


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
        The data to be inserted.set.

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
        
        self._set_component('data', data, copy=False)
    #--- End: def

#--- End: class
