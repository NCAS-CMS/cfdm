from future.utils import with_metaclass
from builtins import super

import abc

from . import Properties


class PropertiesData(with_metaclass(abc.ABCMeta, Properties)):
    '''Abstract base class for a data array with descriptive properties.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, properties=None, data=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

    :Parameters:

        properties: `dict`, optional
            Set descriptive properties. The dictionary keys are
            property names, with corresponding values. Ignored if the
            *source* parameter is set.

            Properties may also be set after initialisation with the
            `set_properties` and `set_property` methods.

            *Parameter example:*
              ``properties={'standard_name': 'altitude'}``

        data: `Data`, optional
            Set the data. Ignored if the *source* parameter is set.

            The data also may be set after initialisation with the
            `set_data` method.

        source: optional
            Initialize the properties and data from those of *source*.

        copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization. By default arguments are deep copied.

        '''
        super().__init__(properties=properties, source=source,
                         copy=copy)

        if source is not None:
            if not _use_data:
                data = None
            else:
                try:
                    data = source.get_data(None)
                except AttributeError:
                    data = None
        # --- End: if

        if _use_data and data is not None:
            self.set_data(data, copy=copy)

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def data(self):
        '''Return the data.

    ``f.data`` is equivalent to ``f.get_data()``

    Note that a `Data` instance is returned. Use its `array` attribute
    to return the data as a `numpy` array.

    The units, calendar and fill value properties are, if set,
    inserted into the data.

    .. versionadded:: 1.7.0

    .. seealso:: `Data.array`, `del_data`, `get_data`, `has_data`,
                 `set_data`

    :Returns:

        `Data`
            The data.

    **Examples:**

    >>> d = cfdm.Data(range(10))
    >>> f.set_data(d)
    >>> f.has_data()
    True
    >>> d = f.data
    >>> d
    <Data(10): [0, ..., 9]>
    >>> f.data.shape
    (10,)

        '''
        return self.get_data()

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self, data=True):
        '''Return a deep copy.

    ``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

    Arrays within `Data` instances are copied with a copy-on-write
    technique. This means that a copy takes up very little extra
    memory, even when the original contains very large data arrays,
    and the copy operation is fast.

    .. versionadded:: 1.7.0

    :Parameters:

        data: `bool`, optional
            If False then do not copy data. By default data are
            copied.

    :Returns:

            The deep copy.

    **Examples:**

    >>> g = f.copy()
    >>> g = f.copy(data=False)
    >>> g.has_data()
    False

        '''
        return type(self)(source=self, copy=True, _use_data=data)

    def del_data(self, default=ValueError()):
        '''Remove the data.

    .. versionadded:: 1.7.0

    .. seealso:: `data`, `get_data`, `has_data`, `set_data`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if data have
            not been set. If set to an `Exception` instance then it
            will be raised instead.

    :Returns:

            The removed data.

    **Examples:**

    >>> d = cfdm.Data(range(10))
    >>> f.set_data(d)
    >>> f.has_data()
    True
    >>> f.get_data()
    <Data(10): [0, ..., 9]>
    >>> f.del_data()
    <Data(10): [0, ..., 9]>
    >>> f.has_data()
    False
    >>> print(f.get_data(None))
    None
    >>> print(f.del_data(None))
    None

        '''
        data = self.get_data(None)
        self._del_component('data', default=default)
        return data

    def get_data(self, default=ValueError(), _units=True,
                 _fill_value=True):
        '''Return the data.

    Note that a `Data` instance is returned. Use its `array` attribute
    to return the data as an independent `numpy` array.

    The units, calendar and fill value properties are, if set,
    inserted into the data.

    .. versionadded:: 1.7.0

    .. seealso:: `Data.array`, `data`, `del_data`, `has_data`,
                 `set_data`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if data have
            not been set. If set to an `Exception` instance then it
            will be raised instead.

    :Returns:

            The data.

    **Examples:**

    >>> d = cfdm.Data(range(10))
    >>> f.set_data(d)
    >>> f.has_data()
    True
    >>> f.get_data()
    <Data(10): [0, ..., 9]>
    >>> f.del_data()
    <Data(10): [0, ..., 9]>
    >>> f.has_data()
    False
    >>> print(f.get_data(None))
    None
    >>> print(f.del_data(None))
    None

        '''
        data = self._get_component('data', None)

        if data is None:
            return self._default(default,
                                 message="{!r} has no data".format(
                                     self.__class__.__name__))

        if _units:
            # Copy the parent units and calendar to the data
            units = self.get_property('units', None)
            if units is not None:
                data.set_units(units)
            else:
                data.del_units(default=None)

            calendar = self.get_property('calendar', None)
            if calendar is not None:
                data.set_calendar(calendar)
            else:
                data.del_calendar(default=None)
        # --- End: if

        if _fill_value:
            # Copy the fill_value to the data
            fill_value = self.get_property(
                'missing_value',
                self.get_property('_FillValue', None))
            if fill_value is not None:
                data.set_fill_value(fill_value)
            else:
                data.del_fill_value(default=None)
        # --- End: if

        return data

    def has_bounds(self):
        '''Whether or not there are cell bounds.

    This is always False.

    .. versionadded:: 1.7.4

    .. seealso:: `has_data`

    :Returns:

        `bool`
            Always False.

    **Examples:**

    >>> f.has_bounds()
    False

        '''
        return False

    def has_data(self):
        '''Whether a data has been set.

    .. versionadded:: 1.7.0

    .. seealso:: `data`, `del_data`, `get_data`, `set_data`

    :Returns:

        `bool`
            True if a data have been set, otherwise False.

    **Examples:**

    >>> d = cfdm.Data(range(10))
    >>> f.set_data(d)
    >>> f.has_data()
    True
    >>> f.get_data()
    <Data(10): [0, ..., 9]>
    >>> f.del_data()
    <Data(10): [0, ..., 9]>
    >>> f.has_data()
    False
    >>> print(f.get_data(None))
    None
    >>> print(f.del_data(None))
    None

        '''
        return self._has_component('data')

    def set_data(self, data, copy=True):
        '''Set the data.

    The units, calendar and fill value of the incoming `Data` instance
    are removed prior to insertion.

    .. versionadded:: 1.7.0

    .. seealso:: `data`, `del_data`, `get_data`, `has_data`

    :Parameters:

        data: `Data`
            The data to be inserted.

        copy: `bool`, optional
            If False then do not copy the data prior to insertion. By
            default the data are copied.

    :Returns:

        `None`

    **Examples:**

    >>> d = Data(range(10))
    >>> f.set_data(d)
    >>> f.has_data()
    True
    >>> f.get_data()
    <Data(10): [0, ..., 9]>
    >>> f.del_data()
    <Data(10): [0, ..., 9]>
    >>> f.has_data()
    False
    >>> print(f.get_data(None))
    None
    >>> print(f.del_data(None))
    None

        '''
        if copy:
            data = data.copy()

#        data.set_units(None) # TODO
#        data.set_calendar(None) # TODO

        self._set_component('data', data, copy=False)

# --- End: class
