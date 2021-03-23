from . import abstract


class DomainAxis(abstract.Container):
    """A domain axis construct of the CF data model.

    A domain axis construct specifies the number of points along an
    independent axis of the domain. It comprises a positive integer
    representing the size of the axis. In CF-netCDF it is usually
    defined either by a netCDF dimension or by a scalar coordinate
    variable, which implies a domain axis of size one. The field
    construct's data array spans the domain axis constructs of the
    domain, with the optional exception of size one axes, because
    their presence makes no difference to the order of the elements.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(self, size=None, source=None, copy=True):
        """**Initialisation**

        :Parameters:

            size: `int`, optional
                The size of the domain axis.

                *Parameter example:*
                  ``size=192``

                The size may also be set after initialisation with the
                `set_size` method.

            source:
                Initialise the size from that of source.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(source=source, copy=copy)

        if source is not None:
            try:
                size = source.get_size(None)
            except AttributeError:
                size = None

        if size is not None:
            self.set_size(size)

    @property
    def construct_type(self):
        """Return a description of the construct type.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `str`
                The construct type.

        **Examples:**

        >>> d = {{package}}.{{class}}()
        >>> d.construct_type
        'domain_axis'

        """
        return "domain_axis"

    def del_size(self, default=ValueError()):
        """Remove the size.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_size`, `has_size`, `set_size`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                size has not been set.

                {{default Exception}}

        :Returns:

                The removed size.

        **Examples:**

        >>> d = {{package}}.{{class}}(size=50)
        >>> d.has_size()
        True
        >>> d.get_size()
        50

        >>> d.set_size(100)
        >>> d.get_size()
        100
        >>> d.del_size()
        100
        >>> d.has_size()
        False
        >>> print(d.del_size(None))
        None

        """
        return self._del_component("size", default=default)

    def has_size(self):
        """Whether the size has been set.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_size`, `get_size`, `set_size`

        :Returns:

             `bool`
                True if the size has been set, otherwise False.

        **Examples:**

        >>> d = {{package}}.{{class}}(size=50)
        >>> d.has_size()
        True
        >>> d.get_size()
        50

        >>> d.set_size(100)
        >>> d.get_size()
        100
        >>> d.del_size()
        100
        >>> d.has_size()
        False
        >>> print(d.del_size(None))
        None

        """
        return self._has_component("size")

    def get_size(self, default=ValueError()):
        """Return the size.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_size`, `has_size`, `set_size`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                size has not been set.

                {{default Exception}}

        :Returns:

                The size.

        **Examples:**

        >>> d = {{package}}.{{class}}(size=50)
        >>> d.has_size()
        True
        >>> d.get_size()
        50

        >>> d.set_size(100)
        >>> d.get_size()
        100
        >>> d.del_size()
        100
        >>> d.has_size()
        False
        >>> print(d.del_size(None))
        None

        """
        return self._get_component("size", default=default)

    def set_size(self, size):
        """Set the size.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_size`, `get_size`, `has_size`

        :Parameters:

            value: `int`
                The size.

        :Returns:

             `None`

        **Examples:**

        >>> d = {{package}}.{{class}}(size=50)
        >>> d.has_size()
        True
        >>> d.get_size()
        50

        >>> d.set_size(100)
        >>> d.get_size()
        100
        >>> d.del_size()
        100
        >>> d.has_size()
        False
        >>> print(d.del_size(None))
        None

        """
        self._set_component("size", size, copy=False)
