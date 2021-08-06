from ..data import Data
from .properties import Properties


class PropertiesData(Properties):
    """Mixin class for a data array with descriptive properties.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __new__(cls, *args, **kwargs):
        """Store component classes.

        NOTE: If a child class requires a different component classes
        than the ones defined here, then they must be redefined in the
        child class.

        """
        instance = super().__new__(cls)
        instance._Data = Data
        return instance

    def __init__(
        self,
        properties=None,
        data=None,
        source=None,
        copy=True,
        _use_data=True,
    ):
        """**Initialisation**

        :Parameters:

            {{init properties: `dict`, optional}}

                *Parameter example:*
                  ``properties={'standard_name': 'altitude'}``

            {{init data: data_like, optional}}

            source: optional
                Initialise the properties and data from those of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(properties=properties, source=source, copy=copy)

        if source is not None:
            if not _use_data:
                data = None
            else:
                try:
                    data = source.get_data(None)
                except AttributeError:
                    data = None

        if _use_data and data is not None:
            self.set_data(data, copy=copy)

    def __array__(self, *dtype):
        """The numpy array interface.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            dtype: optional
                Typecode or data-type to which the array is cast.

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        """
        data = self.get_data(None)
        if data is not None:
            return data.__array__(*dtype)

        raise ValueError(f"{self.__class__.__name__} has no data")

    def __data__(self):
        """Defines the data interface.

        Returns the data, if any.

        :Returns:

            `Data`

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_data([1, 2, 3])
        >>> f.set_property('units', 'K')
        >>> d = {{package}}.Data(f)
        >>> d
        <{{repr}}Data(3): [1, 2, 3] K>

        """
        data = self.get_data(None)
        if data is not None:
            return data

        raise ValueError(f"{self.__class__.__name__} has no data")

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def data(self):
        """Return the data.

        ``f.data`` is equivalent to ``f.get_data()``

        Note that a `Data` instance is returned. Use its `array`
        attribute to return the data as a `numpy` array.

        The units, calendar and fill value properties are, if set,
        inserted into the data.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `{{package}}.Data.array`, `del_data`, `get_data`,
                     `has_data`, `set_data`

        :Returns:

            `Data`
                The data.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_data({{package}}.Data(numpy.arange(10.)))
        >>> f.has_data()
        True
        >>> d = f.data
        >>> d
        <{{repr}}Data(10): [0.0, ..., 9.0]>
        >>> f.data.shape
        (10,)

        """
        return self.get_data()

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self, data=True):
        """Return a deep copy.

        ``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

        Arrays within `Data` instances are copied with a
        copy-on-write technique. This means that a copy takes up very
        little extra memory, even when the original contains very large
        data arrays, and the copy operation is fast.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            data: `bool`, optional
                If False then do not copy data. By default data are
                copied.

        :Returns:

            `{{class}}`
                The deep copy.

        **Examples:**

        >>> g = f.copy()
        >>> g = f.copy(data=False)
        >>> g.has_data()
        False

        """
        return type(self)(source=self, copy=True, _use_data=data)

    def del_data(self, default=ValueError()):
        """Remove the data.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `data`, `get_data`, `has_data`, `set_data`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if data have
                not been set.

                {{default Exception}}

        :Returns:

            `Data`
                The removed data.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_data([1, 2, 3])
        >>> f.has_data()
        True
        >>> f.get_data()
        <{{repr}}Data(3): [1, 2, 3]>
        >>> f.data
        <{{repr}}Data(3): [1, 2, 3]>
        >>> f.del_data()
        <{{repr}}Data(3): [1, 2, 3]>
        >>> g = f.set_data([4, 5, 6], inplace=False)
        >>> g.data
        <{{repr}}Data(3): [4, 5, 6]>
        >>> f.has_data()
        False
        >>> print(f.get_data(None))
        None
        >>> print(f.del_data(None))
        None

        """
        # data = self.get_data(None)
        # self._del_component("data", default=default)
        # return data
        return self._del_component("data", default=default)

    def get_data(self, default=ValueError(), _units=True, _fill_value=True):
        """Return the data.

        Note that a `Data` instance is returned. Use its `array` attribute
        to return the data as an independent `numpy` array.

        The units, calendar and fill value properties are, if set,
        inserted into the data.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `{{package}}.Data.array`, `data`, `del_data`,
                     `has_data`, `set_data`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if data have
                not been set.

                {{default Exception}}

        :Returns:

            `Data`
                The data.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_data([1, 2, 3])
        >>> f.has_data()
        True
        >>> f.get_data()
        <{{repr}}Data(3): [1, 2, 3]>
        >>> f.data
        <{{repr}}Data(3): [1, 2, 3]>
        >>> f.del_data()
        <{{repr}}Data(3): [1, 2, 3]>
        >>> g = f.set_data([4, 5, 6], inplace=False)
        >>> g.data
        <{{repr}}Data(3): [4, 5, 6]>
        >>> f.has_data()
        False
        >>> print(f.get_data(None))
        None
        >>> print(f.del_data(None))
        None

        """
        data = self._get_component("data", None)

        if data is None:
            if default is None:
                return

            return self._default(
                default, message=f"{self.__class__.__name__} has no data"
            )

        if _units:
            # Copy the parent units and calendar to the data
            units = self.get_property("units", None)
            if units is not None:
                data.set_units(units)
            else:
                data.del_units(default=None)

            calendar = self.get_property("calendar", None)
            if calendar is not None:
                data.set_calendar(calendar)
            else:
                data.del_calendar(default=None)

        if _fill_value:
            # Copy the fill_value to the data
            fill_value = self.get_property(
                "missing_value", self.get_property("_FillValue", None)
            )
            if fill_value is not None:
                data.set_fill_value(fill_value)
            else:
                data.del_fill_value(default=None)

        return data

    def has_bounds(self):
        """Whether or not there are cell bounds.

        This is always False.

        .. versionadded:: (cfdm) 1.7.4

        .. seealso:: `has_data`

        :Returns:

            `bool`
                Always False.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.has_bounds()
        False

        """
        return False

    def has_data(self):
        """Whether or not the construct has data.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `data`, `del_data`, `get_data`, `set_data`

        :Returns:

            `bool`
                True if data have been set, otherwise False.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_data([1, 2, 3])
        >>> f.has_data()
        True
        >>> f.get_data()
        <{{repr}}Data(3): [1, 2, 3]>
        >>> f.data
        <{{repr}}Data(3): [1, 2, 3]>
        >>> f.del_data()
        <{{repr}}Data(3): [1, 2, 3]>
        >>> g = f.set_data([4, 5, 6], inplace=False)
        >>> g.data
        <{{repr}}Data(3): [4, 5, 6]>
        >>> f.has_data()
        False
        >>> print(f.get_data(None))
        None
        >>> print(f.del_data(None))
        None

        """
        return self._has_component("data")

    def set_data(self, data, copy=True, inplace=True):
        """Set the data.

        The units, calendar and fill value of the incoming `Data` instance
        are removed prior to insertion.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `data`, `del_data`, `get_data`, `has_data`

        :Parameters:

            data: data_like
                The data to be inserted.

                {{data_like}}

            copy: `bool`, optional
                If False then do not copy the data prior to insertion. By
                default the data are copied.

            {{inplace: `bool`, optional (default True)}}

                .. versionadded:: (cfdm) 1.8.7.0

        :Returns:

            `None` or `{{class}}`
                If the operation was in-place then `None` is returned,
                otherwise return a new `{{class}}` instance containing the
                new data.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_data([1, 2, 3])
        >>> f.has_data()
        True
        >>> f.get_data()
        <{{repr}}Data(3): [1, 2, 3]>
        >>> f.data
        <{{repr}}Data(3): [1, 2, 3]>
        >>> f.del_data()
        <{{repr}}Data(3): [1, 2, 3]>
        >>> g = f.set_data([4, 5, 6], inplace=False)
        >>> g.data
        <{{repr}}Data(3): [4, 5, 6]>
        >>> f.has_data()
        False
        >>> print(f.get_data(None))
        None
        >>> print(f.del_data(None))
        None

        """
        _Data = self._Data
        if not isinstance(data, _Data):
            data = _Data(data, copy=False)

        if copy:
            data = data.copy()

        if inplace:
            f = self
        else:
            f = self.copy(data=False)

        f._set_component("data", data, copy=False)

        if inplace:
            return

        return f
