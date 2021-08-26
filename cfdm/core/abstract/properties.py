from ..functions import deepcopy
from .container import Container


class Properties(Container):
    """Mixin class for an object with descriptive properties.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(self, properties=None, source=None, copy=True):
        """**Initialisation**

        :Parameters:

            {{init properties: `dict`, optional}}

                *Parameter example:*
                   ``properties={'standard_name': 'altitude'}``

            source: optional
                Initialise the properties from those of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(source=source, copy=copy)

        if source is not None:
            try:
                properties = source.properties()
            except AttributeError:
                properties = None

        self._set_component("properties", {}, copy=False)

        if properties is not None:
            self.set_properties(properties, copy=copy)

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def clear_properties(self):
        """Remove all properties.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_property` `properties`, `set_properties`

        :Returns:

            `dict`
                The properties that have been removed.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.properties()
        {}
        >>> f.set_properties({'standard_name': 'air_pressure',
        ...                   'long_name': 'Air Pressure'})
        >>> f.properties()
        {'standard_name': 'air_pressure',
         'long_name': 'Air Pressure'}
        >>> f.set_properties({'standard_name': 'air_pressure', 'foo': 'bar'})
        >>> f.properties()
        {'standard_name': 'air_pressure',
         'long_name': 'Air Pressure',
         'foo': 'bar'}
        >>> f.clear_properties()
        {'standard_name': 'air_pressure',
         'long_name': 'Air Pressure',
         'foo': 'bar'}
        >>> f.properties()
        {}

        """
        out = self._get_component("properties")
        self._set_component("properties", {}, copy=False)
        return out

    def del_property(self, prop, default=ValueError()):
        """Remove a property.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `clear_properties`, `get_property`, `has_property`,
                     `properties`, `set_property`

        :Parameters:

            prop: `str`
                The name of the property to be removed.

                *Parameter example:*
                   ``prop='long_name'``

            default: optional
                Return the value of the *default* parameter if the
                property has not been set.

                {{default Exception}}

        :Returns:

                The removed property value.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_property('project', 'CMIP7')
        >>> f.has_property('project')
        True
        >>> f.get_property('project')
        'CMIP7'
        >>> f.del_property('project')
        'CMIP7'
        >>> f.has_property('project')
        False
        >>> print(f.del_property('project', None))
        None
        >>> print(f.get_property('project', None))
        None

        """
        try:
            return self._get_component("properties").pop(prop)
        except KeyError:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__!r} has no {prop!r} property",
            )

    def get_property(self, prop, default=ValueError()):
        """Return a property.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_property`, `has_property`, `properties`,
                     `set_property`

        :Parameters:

            prop: `str`
                The name of the property to be returned.

                *Parameter example:*
                   ``prop='standard_name'``

            default: optional
                Return the value of the *default* parameter if the
                property has not been set.

                {{default Exception}}

        :Returns:

                The value of the property.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_property('project', 'CMIP7')
        >>> f.has_property('project')
        True
        >>> f.get_property('project')
        'CMIP7'
        >>> f.del_property('project')
        'CMIP7'
        >>> f.has_property('project')
        False
        >>> print(f.del_property('project', None))
        None
        >>> print(f.get_property('project', None))
        None

        """
        try:
            return self._get_component("properties")[prop]
        except KeyError:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__!r} has no {prop!r} property",
            )

    def has_bounds(self):
        """Whether or not there are cell bounds.

        This is always False.

        .. versionadded:: (cfdm) 1.9.0.0

        .. seealso:: `has_data`

        :Returns:

            `False`

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.has_bounds()
        False

        """
        return False

    def has_data(self):
        """Whether or not the construct has data.

        `{{class}}` instances never have data.

        .. versionadded:: (cfdm) 1.9.0.0

        :Returns:

            `False`

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.has_data()
        False

        """
        return False

    def has_property(self, prop):
        """Whether a property has been set.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_property`, `get_property`, `properties`,
                     `set_property`

        :Parameters:

            prop: `str`
                The name of the property.

                *Parameter example:*
                   ``prop='long_name'``

        :Returns:

            `bool`
                True if the property has been set, otherwise False.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_property('project', 'CMIP7')
        >>> f.has_property('project')
        True
        >>> f.get_property('project')
        'CMIP7'
        >>> f.del_property('project')
        'CMIP7'
        >>> f.has_property('project')
        False
        >>> print(f.del_property('project', None))
        None
        >>> print(f.get_property('project', None))
        None

        """
        return prop in self._get_component("properties")

    def properties(self):
        """Return all properties.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `clear_properties`, `get_property`, `has_property`
                     `set_properties`

        :Returns:

            `dict`
                The properties.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.properties()
        {}
        >>> f.set_properties({'standard_name': 'air_pressure',
        ...                   'long_name': 'Air Pressure'})
        >>> f.properties()
        {'standard_name': 'air_pressure',
         'long_name': 'Air Pressure'}
        >>> f.set_properties({'standard_name': 'air_pressure', 'foo': 'bar'})
        >>> f.properties()
        {'standard_name': 'air_pressure',
         'long_name': 'Air Pressure',
         'foo': 'bar'}
        >>> f.clear_properties()
        {'standard_name': 'air_pressure',
         'long_name': 'Air Pressure',
         'foo': 'bar'}
        >>> f.properties()
        {}

        """
        return self._get_component("properties").copy()

    def set_properties(self, properties, copy=True):
        """Set properties.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `clear_properties`, `properties`, `set_property`

        :Parameters:

            properties: `dict`
                Store the properties from the dictionary supplied.

                *Parameter example:*
                  ``properties={'standard_name': 'altitude', 'foo': 'bar'}``

            copy: `bool`, optional
                If False then any property values provided by the
                *properties* parameter are not copied before insertion. By
                default they are deep copied.

        :Returns:

            `None`

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.properties()
        {}
        >>> f.set_properties({'standard_name': 'air_pressure',
        ...                   'long_name': 'Air Pressure'})
        >>> f.properties()
        {'standard_name': 'air_pressure',
         'long_name': 'Air Pressure'}
        >>> f.set_properties({'standard_name': 'air_pressure', 'foo': 'bar'})
        >>> f.properties()
        {'standard_name': 'air_pressure',
         'long_name': 'Air Pressure',
         'foo': 'bar'}
        >>> f.clear_properties()
        {'standard_name': 'air_pressure',
         'long_name': 'Air Pressure',
         'foo': 'bar'}
        >>> f.properties()
        {}

        """
        if copy:
            properties = deepcopy(properties)
        #        else:
        #            properties = properties.copy()

        self._get_component("properties").update(properties)

    def set_property(self, prop, value, copy=True):
        """Set a property.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_property`, `get_property`, `has_property`,
                     `properties`, `set_properties`

        :Parameters:

            prop: `str`
                The name of the property to be set.

            value:
                The value for the property.

            copy: `bool`, optional
                If True then set a deep copy of *value*.

        :Returns:

             `None`

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_property('project', 'CMIP7')
        >>> f.has_property('project')
        True
        >>> f.get_property('project')
        'CMIP7'
        >>> f.del_property('project')
        'CMIP7'
        >>> f.has_property('project')
        False
        >>> print(f.del_property('project', None))
        None
        >>> print(f.get_property('project', None))
        None

        """
        if copy:
            value = deepcopy(value)

        self._get_component("properties")[prop] = value
