from .propertiesdatabounds import PropertiesDataBounds


class Coordinate(PropertiesDataBounds):
    """Mixin for CF data model dimension and auxiliary coordinates.

    .. versionadded:: (cfdm) 1.7.0

    """

    def del_climatology(self, default=ValueError()):
        """Remove the climatology setting.

        .. versionadded:: (cfdm) 1.8.9.0

        .. seealso:: `get_climatology`, `is_climatology`,
                     `set_climatology`,

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                climatology status has not been set.

                {{default Exception}}

        :Returns:

            `str`
                The removed climatology value.

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.set_climatology(True)
        >>> c.is_climatology()
        True
        >>>  c.get_climatology()
        True
        >>> c.del_climatology()
        True
        >>> c.is_climatology()
        False
        >>> print(c.get_climatology(None))
        None
        >>> print(c.del_climatology(None))
        None
        >>> c.set_climatology(False)
        >>> c.is_climatology()
        False

        """
        out = self._del_component("climatology", None)
        if out is not None:
            return out

        if default is None:
            return

        return self._default(
            default,
            f"{self.__class__.__name__!r} has no climatology set",
        )

    def get_climatology(self, default=ValueError()):
        """Return the climatology setting.

        .. versionadded:: (cfdm) 1.8.9.0

        .. seealso:: `del_climatology`, `is_climatology`,
                     `set_climatology`,

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                climatology status has not been set.

                {{default Exception}}

        :Returns:

            `str`

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.set_climatology(True)
        >>> c.is_climatology()
        True
        >>>  c.get_climatology()
        True
        >>> c.del_climatology()
        True
        >>> c.is_climatology()
        False
        >>> print(c.get_climatology(None))
        None
        >>> print(c.del_climatology(None))
        None
        >>> c.set_climatology(False)
        >>> c.is_climatology()
        False

        """
        out = self._get_component("climatology", None)
        if out is not None:
            return out

        if default is None:
            return

        return self._default(
            default,
            f"{self.__class__.__name__!r} has no climatology set",
        )

    def is_climatology(self):
        """True if the coordinates are climatological.

        .. versionadded:: (cfdm) 1.8.9.0

        .. seealso:: `del_climatology`, `get_climatology`,
                     `set_climatology`,

        :Returns:

            `bool`
                Whether or not the coordinates are climatological.

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.set_climatology(True)
        >>> c.is_climatology()
        True
        >>>  c.get_climatology()
        True
        >>> c.del_climatology()
        True
        >>> c.is_climatology()
        False
        >>> print(c.get_climatology(None))
        None
        >>> print(c.del_climatology(None))
        None
        >>> c.set_climatology(False)
        >>> c.is_climatology()
        False

        """
        return bool(self._get_component("climatology", None))

    def set_climatology(self, climatology):
        """Set whether or not coordinates are climatological.

        Only coordinate constructs with units of reference time (or unset
        units) can be set as climatological.

        .. versionadded:: (cfdm) 1.8.9.0

        .. seealso:: `del_climatology`, `get_climatology`,
                     `is_climatology`, `set_climatology`,

        :Parameters:

            climatology: `bool`
                Whether or not the coordinates are climatological.

        :Returns:

            `None`

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.set_climatology(True)
        >>> c.is_climatology()
        True
        >>>  c.get_climatology()
        True
        >>> c.del_climatology()
        True
        >>> c.is_climatology()
        False
        >>> print(c.get_climatology(None))
        None
        >>> print(c.del_climatology(None))
        None
        >>> c.set_climatology(False)
        >>> c.is_climatology()
        False

        """
        climatology = bool(climatology)

        if climatology:
            units = self.get_property("units", None)
            if units is not None and " since " not in units:
                # Construct does not have reference time units
                raise ValueError(
                    f"Can't set {self!r} as climatological: "
                    f"Non-reference time units {units!r}"
                )

        self._set_component("climatology", climatology, copy=False)
