from builtins import (str, super)

import numpy

from .. import abstract


class Data(abstract.Container):
    '''An orthogonal multidimensional array with masked values and units.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, array=None, units=None, calendar=None,
                 fill_value=None, source=None, copy=True,
                 _use_array=True, _custom_deep_copy=False):
        '''**Initialization**

    :Parameters:

        array: subclass of `Array`
            The array of values. Ignored if the *source* parameter is
            set.

        units: `str`, optional
            The physical units of the data. Ignored if the *source*
            parameter is set.

            The units may also be set after initialisation with the
            `set_units` method.

            *Parameter example:*
              ``units='km hr-1'``

            *Parameter example:*
              ``units='days since 2018-12-01'``

        calendar: `str`, optional
            The calendar for reference time units. Ignored if the
            *source* parameter is set.

            The calendar may also be set after initialisation with the
            `set_calendar` method.

            *Parameter example:*
              ``calendar='360_day'``

        fill_value: optional
            The fill value of the data. By default, or if set to
            `None`, the `numpy` fill value appropriate to the array's
            data type will be used (see
            `numpy.ma.default_fill_value`). Ignored if the *source*
            parameter is set.

            The fill value may also be set after initialisation with
            the `set_fill_value` method.

            *Parameter example:*
              ``fill_value=-999.``

        source: *optional*
            Initialize the data, units, calendar and fill value from
            those of *source*.

        source: optional

            Initialize the array, units, calendar and fill value from
            those of *source*.

        copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization. By default arguments are deep copied.

        '''
        super().__init__(source=source)

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
        # --- End: if

        if units is not None:
            self.set_units(units)

        if calendar is not None:
            self.set_calendar(calendar)

        if fill_value is not None:
            self.set_fill_value(fill_value)

        if _use_array and array is not None:
            self._set_Array(array, copy=copy)

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def array(self):
        '''Return an independent numpy array containing the data.

    If a fill value has been set (see `set_fill_value`) then it will
    be used, otherwise the default numpy fill value appropriate to the
    data type will be used.

    :Returns:

        `numpy.ndarray`
            An independent numpy array of the data.

    **Examples:**

    >>> d = Data([1, 2, 3.0], 'km')
    >>> n = d.array
    >>> isinstance(n, numpy.ndarray)
    True
    >>> print(n)
    [ 1.,   2.,   3.]
    >>> n[0] = 88
    >>> print(repr(d))
    <Data: [1.0, 2.0, 3.0] km>

        '''
        array = self._get_Array().array

        # Set the numpy array fill value
        if numpy.ma.isMA(array):
            array.set_fill_value(self.get_fill_value(None))

        return array

    @property
    def dtype(self):
        '''Data-type of the data elements.

    **Examples:**

    >>> d.dtype
    dtype('float64')
    >>> type(d.dtype)
    <type 'numpy.dtype'>

        '''
        datatype = self._get_Array().dtype
        if datatype is None:
            # The datatype is not known, so get the numpy array and
            # get it off that.
            datatype = self.array.dtype

        return datatype

    @property
    def ndim(self):
        '''Number of data dimensions.

    **Examples:**

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

    @property
    def shape(self):
        '''Tuple of data dimension sizes.

    **Examples:**

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

    @property
    def size(self):
        '''Number of elements in the data.

    **Examples:**

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

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self, array=True):
        '''Return a deep copy of the data.

    ``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

    Copy-on-write is employed, so care must be taken when modifying
    any attribute.

    :Parameters:

        array: `bool`, optional
            If False then do not copy the array. By default the array
            is copied.

    :Returns:

        `Data`
            The deep copy.

    **Examples:**

    >>> e = d.copy()
    >>> e = d.copy(array=False)

        '''
        return type(self)(source=self, copy=True, _use_array=array)

    def _del_Array(self, default=ValueError()):
        '''Delete the underlying array.

    :Returns:

            The array.

    **Examples:**

    >>> old = d.del_data()

        '''
        return self._del_component('array', default=default)

    def del_calendar(self, default=ValueError()):
        '''Delete the calendar.

    .. seealso:: `get_calendar`, `has_calendar`, `set_calendar`,
                 `del_units`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the
            calendar has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The value of the deleted calendar.

    **Examples:**

    >>> d.set_calendar('360_day')
    >>> d.has_calendar()
    True
    >>> d.get_calendar()
    '360_day'
    >>> d.del_calendar()
    >>> d.has_calendar()
    False
    >>> d.get_calendar()
    ValueError: Can't get non-existent calendar
    >>> print(d.get_calendar(None))
    None
    >>> print(d.del_calendar(None))
    None

        '''
        try:
            return self._del_component('calendar')
        except ValueError:
            return self._default(default,
                                 "{!r} has no calendar".format(
                                     self.__class__.__name__))

    def del_fill_value(self, default=ValueError()):
        '''Delete the fill value.

    .. seealso:: `get_fill_value`, `has_fill_value`, `set_fill_value`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the fill
            value has not been set. If set to an `Exception` instance
            then it will be raised instead.

    :Returns:

            The value of the deleted fill value.

    **Examples:**

    >>> f.set_fill_value(-9999)
    >>> f.has_fill_value()
    True
    >>> f.get_fill_value()
    -9999
    >>> print(f.del_fill_value())
    -9999
    >>> f.get_fill_value()
    ValueError: Can't get non-existent fill value
    >>> f.get_fill_value(10**10)
    10000000000
    >>> print(f.get_fill_value(None))
    None
    >>> f.set_fill_value(None)
    >>> print(f.get_fill_value())
    None
    >>> f.has_fill_value()
    False

        '''
        try:
            return self._del_component('fill_value')
        except ValueError:
            return self._default(default,
                                 "{!r} has no fill value".format(
                                     self.__class__.__name__))

    def del_units(self, default=ValueError()):
        '''Delete the units.

    .. seealso:: `get_units`, `has_units`, `set_units`, `del_calendar`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the units
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

            The value of the deleted units.

    **Examples:**

    >>> d.set_units('metres')
    >>> d.has_units()
    True
    >>> d.get_units()
    'metres'
    >>> d.del_units()
    >>> d.has_units()
    False
    >>> d.get_units()
    ValueError: Can't get non-existent units
    >>> print(d.get_units(None))
    None
    >>> print(d.del_units(None))
    None

        '''
        try:
            return self._del_component('units')
        except ValueError:
            return self._default(default,
                                 "{!r} has no units".format(
                                     self.__class__.__name__))

    def get_calendar(self, default=ValueError()):
        '''Return the calendar.

    .. seealso:: `del_calendar`, `has_calendar`, `set_calendar`,
                 `get_units`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the
            calendar has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The calendar.

    **Examples:**

    >>> d.set_calendar('360_day')
    >>> d.has_calendar()
    True
    >>> d.get_calendar()
    '360_day'
    >>> d.del_calendar()
    >>> d.has_calendar()
    False
    >>> d.get_calendar()
    ValueError: Can't get non-existent calendar
    >>> print(d.get_calendar(None))
    None
    >>> print(d.del_calendar(None))
    None

        '''
        try:
            return self._get_component('calendar')
        except ValueError:
            return self._default(default,
                                 "{!r} has no calendar".format(
                                     self.__class__.__name__))

    def _get_Array(self, default=ValueError()):
        '''Return the array object.

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the array
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

            The array object.

    **Examples:**

    >>> a = d._get_Array(None)

        '''
        try:
            return self._get_component('array')
        except ValueError:
            return self._default(default,
                                 "{!r} has no array".format(
                                     self.__class__.__name__))

    def get_fill_value(self, default=ValueError()):
        '''Return the missing data value.

    .. seealso:: `del_fill_value`, `has_fill_value`, `set_fill_value`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the fill
            value has not been set. If set to an `Exception` instance
            then it will be raised instead.

    :Returns:

            The fill value.

    **Examples:**

    >>> f.set_fill_value(-9999)
    >>> f.has_fill_value()
    True
    >>> f.get_fill_value()
    -9999
    >>> print(f.del_fill_value())
    -9999
    >>> f.get_fill_value()
    ValueError: Can't get non-existent fill value
    >>> f.get_fill_value(10**10)
    10000000000
    >>> print(f.get_fill_value(None))
    None
    >>> f.set_fill_value(None)
    >>> print(f.get_fill_value())
    None
    >>> f.has_fill_value()
    False

        '''
        try:
            return self._get_component('fill_value')
        except ValueError:
            return self._default(default,
                                 "{!r} has no fill value".format(
                                     self.__class__.__name__))

    def get_units(self, default=ValueError()):
        '''Return the units.

    .. seealso:: `del_units`, `has_units`, `set_units`, `get_calendar`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the units
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

            The units.

    **Examples:**

    >>> d.set_units('metres')
    >>> d.has_units()
    True
    >>> d.get_units()
    'metres'
    >>> d.del_units()
    >>> d.has_units()
    False
    >>> d.get_units()
    ValueError: Can't get non-existent units
    >>> print(d.get_units(None))
    None
    >>> print(d.del_units(None))
    None

        '''
        try:
            return self._get_component('units')
        except ValueError:
            return self._default(default,
                                 "{!r} has no units".format(
                                     self.__class__.__name__))

    def has_units(self):
        '''Whether units have been set.

    .. seealso:: `del_units`, `get_units`, `set_units`, `has_calendar`

    :Returns:

        `bool`
            True if units have been set, otherwise False.

    **Examples:**

    >>> d.set_units('metres')
    >>> d.has_units()
    True
    >>> d.get_units()
    'metres'
    >>> d.del_units()
    >>> d.has_units()
    False
    >>> d.get_units()
    ValueError: Can't get non-existent units
    >>> print(d.get_units(None))
    None
    >>> print(d.del_units(None))
    None

        '''
        return self._has_component('units')

    def has_calendar(self):
        '''Whether a calendar has been set.

    .. seealso:: `del_calendar`, `get_calendar`, `set_calendar`,
                 `has_units`

    :Returns:

        `bool`
            True if the calendar has been set, otherwise False.

    **Examples:**

    >>> d.set_calendar('360_day')
    >>> d.has_calendar()
    True
    >>> d.get_calendar()
    '360_day'
    >>> d.del_calendar()
    >>> d.has_calendar()
    False
    >>> d.get_calendar()
    ValueError: Can't get non-existent calendar
    >>> print(d.get_calendar(None))
    None
    >>> print(d.del_calendar(None))
    None

        '''
        return self._has_component('calendar')

    def has_fill_value(self):
        '''Whether a fill value has been set.

    .. seealso:: `del_fill_value`, `get_fill_value`, `set_fill_value`

    :Returns:

        `bool`
            True if a fill value has been set, otherwise False.

    **Examples:**

    >>> f.set_fill_value(-9999)
    >>> f.has_fill_value()
    True
    >>> f.get_fill_value()
    -9999
    >>> print(f.del_fill_value())
    -9999
    >>> f.get_fill_value()
    ValueError: Can't get non-existent fill value
    >>> f.get_fill_value(10**10)
    10000000000
    >>> print(f.get_fill_value(None))
    None
    >>> f.set_fill_value(None)
    >>> print(f.get_fill_value())
    None
    >>> f.has_fill_value()
    False

        '''
        return self._has_component('fill_value')

    def set_calendar(self, value):
        '''Set the calendar.

    .. seealso:: `del_calendar`, `get_calendar`, `has_calendar`,
                 `set_units`

    :Parameters:

        value: `str`
            The new calendar.

    :Returns:

        `None`

    **Examples:**

    >>> d.set_calendar('360_day')
    >>> d.has_calendar()
    True
    >>> d.get_calendar()
    '360_day'
    >>> d.del_calendar()
    >>> d.has_calendar()
    False
    >>> d.get_calendar()
    ValueError: Can't get non-existent calendar
    >>> print(d.get_calendar(None))
    None
    >>> print(d.del_calendar(None))
    None

        '''
        return self._set_component('calendar', value, copy=False)

    def _set_Array(self, array, copy=True):
        '''Set the array.

    :Parameters:

        array: subclass of `Array`
            The array to be inserted.

    :Returns:

        `None`

    **Examples:**

    >>> d._set_Array(a)

        '''
        if copy:
            array = array.copy()

        self._set_component('array', array, copy=False)

    def set_fill_value(self, value):
        '''Set the missing data value.

    .. seealso:: `del_fill_value`, `has_fill_value`, `get_fill_value`

    :Parameters:

        value: scalar
            The new fill value.

    :Returns:

        `None`

    **Examples:**

    >>> f.set_fill_value(-9999)
    >>> f.has_fill_value()
    True
    >>> f.get_fill_value()
    -9999
    >>> print(f.del_fill_value())
    -9999
    >>> f.get_fill_value()
    ValueError: Can't get non-existent fill value
    >>> f.get_fill_value(10**10)
    10000000000
    >>> print(f.get_fill_value(None))
    None
    >>> f.set_fill_value(None)
    >>> print(f.get_fill_value())
    None
    >>> f.has_fill_value()
    False

        '''
        if value is None:
            self.del_fill_value(None)

        self._set_component('fill_value', value, copy=False)

    def set_units(self, value):
        '''Set the units.

    .. seealso:: `del_units`, `get_units`, `has_units`, `set_calendar`

    :Parameters:

        value: `str`
            The new units.

    :Returns:

        `None`

    **Examples:**

    >>> d.set_units('metres')
    >>> d.has_units()
    True
    >>> d.get_units()
    'metres'
    >>> d.del_units()
    >>> d.has_units()
    False
    >>> d.get_units()
    ValueError: Can't get non-existent units
    >>> print(d.get_units(None))
    None
    >>> print(d.del_units(None))
    None

        '''
        self._set_component('units', value, copy=False)

    def source(self, default=ValueError()):
        '''Return the underlying array object.

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the array
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

        subclass of `Array`
            The underlying array object.

    **Examples:**

    TODO

        '''
        return  self._get_component('array', default=default)

# --- End: class

