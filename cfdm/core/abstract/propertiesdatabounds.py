import numpy

from .propertiesdata import PropertiesData

# --------------------------------------------------------------------
# See cfdm.core.mixin.container.__docstring_substitution__ for {{...}}
# docstring substitutions
# --------------------------------------------------------------------


class PropertiesDataBounds(PropertiesData):
    """Mixin for a data array with bounds and descriptive properties.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        properties=None,
        data=None,
        bounds=None,
        geometry=None,
        interior_ring=None,
        source=None,
        copy=True,
        _use_data=True,
    ):
        """**Initialisation**

        :Parameters:

            {{init properties: `dict`, optional}}

                *Parameter example:*
                   ``properties={'standard_name': 'longitude'}``

            {{init data: data_like, optional}}

            {{init bounds: `Bounds`, optional}}

            {{init geometry: `str`, optional}}

            {{init interior_ring: `InteriorRing`, optional}}

            source: optional
                Initialise the properties, geometry type, data, bounds
                and interior ring from those of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        # Initialise properties and data
        super().__init__(
            properties=properties,
            data=data,
            source=source,
            copy=copy,
            _use_data=_use_data,
        )

        # Get bounds, geometry type and interior ring from source
        if source is not None:
            try:
                bounds = source.get_bounds(None)
            except AttributeError:
                bounds = None

            try:
                geometry = source.get_geometry(None)
            except AttributeError:
                geometry = None

            try:
                interior_ring = source.get_interior_ring(None)
            except AttributeError:
                interior_ring = None

        # Initialise bounds
        if bounds is not None:
            if copy or not _use_data:
                bounds = bounds.copy(data=_use_data)

            self.set_bounds(bounds, copy=False)

        # Initialise the geometry type
        if geometry is not None:
            self.set_geometry(geometry)

        # Initialise interior ring
        if interior_ring is not None:
            if copy or not _use_data:
                interior_ring = interior_ring.copy(data=_use_data)

            self.set_interior_ring(interior_ring, copy=False)

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def bounds(self):
        """Return the bounds.

        ``f.bounds`` is equivalent to ``f.get_bounds()``

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `data`, `del_bounds`, `get_bounds`, `has_bounds`,
                     `set_bounds`

        :Returns:

            `Bounds`
                The bounds.

        **Examples:**


        >>> c = {{package}}.{{class}}()
        >>> b = {{package}}.Bounds(data={{package}}.Data(numpy.arange(10).reshape(5, 2)))
        >>> c.set_bounds(b)
        >>> c.has_bounds()
        True
        >>> b = c.bounds
        >>> b
        <{{repr}}Bounds: (5, 2) >
        >>> b.data
        <{{repr}}Data(5, 2): [[0, ..., 9]]>
        >>> b.data.shape
        (5, 2)

        """
        return self.get_bounds()

    @property
    def interior_ring(self):
        """Return the interior ring variable for polygon geometries.

        ``f.interior_ring`` is equivalent to ``f.get_interior_ring()``

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `data`, `del_interior_ring`, `get_interior_ring`,
                     `has_interior_ring`, `set_interior_ring`

        :Returns:

            `InteriorRing`
                The interior ring variable.

        **Examples:**


        >>> i = {{package}}.InteriorRing(data={{package}}.Data(numpy.arange(10).reshape(5, 2)))
        >>> c.set_interior_ring(i)
        >>> c.has_interior_ring()
        True
        >>> i = c.interior_ring
        >>> i
        <{{repr}}InteriorRing: (5, 2) >
        >>> i.data
        <{{repr}}Data(5, 2): [[0, ..., 9]]>
        >>> i.data.shape
        (5, 2)

        """
        return self.get_interior_ring()

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def del_bounds(self, default=ValueError()):
        """Remove the bounds.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_data`, `get_bounds`, `has_bounds`, `set_bounds`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if bounds
                have not been set.

                {{default Exception}}

        :Returns:

            `Bounds`
                The removed bounds.

        **Examples:**


        >>> c = {{package}}.{{class}}()
        >>> b = {{package}}.Bounds(data={{package}}.Data(numpy.arange(10).reshape(5, 2)))
        >>> c.set_bounds(b)
        >>> c.has_bounds()
        True
        >>> c.get_bounds()
        <{{repr}}Bounds: (5, 2) >
        >>> b = c.del_bounds()
        >>> b
        <{{repr}}Bounds: (5, 2) >
        >>> c.has_bounds()
        False
        >>> print(c.get_bounds(None))
        None
        >>> print(c.del_bounds(None))
        None

        """
        return self._del_component("bounds", default=default)

    #        try:
    #            return self._del_component("bounds")
    #        except ValueError:
    #            return self._default(
    #                default, "{!r} has no bounds".format(self.__class__.__name__)
    #            )

    def del_geometry(self, default=ValueError()):
        """Remove the geometry type.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `get_geometry`, `has_geometry`, `set_geometry`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                geometry type has not been set.

                {{default Exception}}

        :Returns:

            `str`
                The removed geometry type.

        **Examples:**

        >>> f = {{package}}.read('file.nc')[0]
        >>> c = f.construct('axis=X')
        >>> c.has_geometry()
        True
        >>> c.get_geometry()
        'line'
        >>> b = c.del_geometry()
        >>> c.has_geometry()
        False
        >>> print(c.get_geometry(None))
        None

        >>> c.set_geometry(b)
        >>> c.has_geometry()
        True

        """
        return self._del_component("geometry", default=default)

    #        try:
    #            return self._del_component("geometry")
    #        except ValueError:
    #            return self._default(
    #                default,
    #                "{!r} has no geometry type".format(self.__class__.__name__),
    #            )

    def del_interior_ring(self, default=ValueError()):
        """Remove the geometry type.

        .. versionadded:: (cfdm) 1.8.6.0

        .. seealso:: `data`, `del_interior_ring`, `has_interior_ring`,
                     `interior_ring`, `set_interior_ring`

        :Parameters:

           default: optional
                Return the value of the *default* parameter if the
                geometry type has not been set.

                {{default Exception}}

        :Returns:

            `ÌnteriorRing`
                The removed interior ring variable.

        **Examples:**


        >>> c = {{package}}.{{class}}()
        >>> i = {{package}}.InteriorRing(data={{package}}.Data(numpy.arange(10).reshape(5, 2)))
        >>> c.set_interior_ring(i)
        >>> c.has_interior_ring()
        True
        >>> i = c.get_interior_ring()
        >>> i
        <{{repr}}InteriorRing: (5, 2) >
        >>> i.data
        <{{repr}}Data(5, 2): [[0, ..., 9]]>
        >>> i.data.shape
        (5, 2)
        >>> c.del_interior_ring()
        <{{repr}}InteriorRing: (5, 2) >
        >>> c.has_interior_ring()
        False
        >>> print(c.del_interior_ring(None))
        None

        """
        return self._del_component("interior_ring", default=default)

    #        try:
    #            return self._del_component("interior_ring")
    #        except ValueError:
    #            return self._default(
    #                default,
    #                "{!r} has no interior ring variable".format(
    #                    self.__class__.__name__
    #                ),
    #            )

    def get_bounds(self, default=ValueError()):
        """Return the bounds.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `bounds`, `get_data`, `del_bounds`, `has_bounds`,
                     `set_bounds`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if bounds have
                not been set.

                {{default Exception}}

        :Returns:

            `Bounds`
                The bounds.

        **Examples:**


        >>> c = {{package}}.{{class}}()
        >>> b = {{package}}.Bounds(data={{package}}.Data(numpy.arange(10).reshape(5, 2)))
        >>> c.set_bounds(b)
        >>> c.has_bounds()
        True
        >>> c.get_bounds()
        <{{repr}}Bounds: (5, 2) >
        >>> b = c.del_bounds()
        >>> b
        <{{repr}}Bounds: (5, 2) >
        >>> c.has_bounds()
        False
        >>> print(c.get_bounds(None))
        None
        >>> print(c.del_bounds(None))
        None

        """
        return self._get_component("bounds", default=default)

    #        try:
    #            return self._get_component("bounds")
    #        except ValueError:
    #            return self._default(
    #                default, "{!r} has no bounds".format(self.__class__.__name__)
    #            )

    def get_geometry(self, default=ValueError()):
        """Return the geometry type.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `has_geometry`, `set_geometry`, `del_geometry`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                geometry type has not been set.

                {{default Exception}}

        :Returns:

            `str`
                The geometry type.

        **Examples:**

        >>> f = {{package}}.read('file.nc')[0]
        >>> c = f.construct('axis=X')
        >>> c.has_geometry()
        True
        >>> c.get_geometry()
        'line'
        >>> b = c.del_geometry()
        >>> c.has_geometry()
        False
        >>> print(c.get_geometry(None))
        None

        >>> c.set_geometry(b)
        >>> c.has_geometry()
        True

        """
        return self._get_component("geometry", default=default)

    #        try:
    #            return self._get_component("geometry")
    #        except ValueError:
    #            return self._default(
    #                default,
    #                "{!r} has no geometry type".format(self.__class__.__name__),
    #            )

    def get_interior_ring(self, default=ValueError()):
        """Return the interior ring variable for polygon geometries.

        ``f.get_interior_ring()`` is equivalent to ``f.interior_ring``

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `data`, `del_interior_ring`, `has_interior_ring`,
                     `interior_ring`, `set_interior_ring`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if interior
                ring data have not been set.

                {{default Exception}}

        :Returns:

            `InteriorRing`
                The interior ring variable.

        **Examples:**


        >>> c = {{package}}.{{class}}()
        >>> i = {{package}}.InteriorRing(data={{package}}.Data(numpy.arange(10).reshape(5, 2)))
        >>> c.set_interior_ring(i)
        >>> c.has_interior_ring()
        True
        >>> i = c.get_interior_ring()
        >>> i
        <{{repr}}InteriorRing: (5, 2) >
        >>> i.data
        <{{repr}}Data(5, 2): [[0, ..., 9]]>
        >>> i.data.shape
        (5, 2)
        >>> c.del_interior_ring()
        <{{repr}}InteriorRing: (5, 2) >
        >>> c.has_interior_ring()
        False
        >>> print(c.del_interior_ring(None))
        None

        """
        return self._get_component("interior_ring", default=default)

    #        try:
    #           return self._get_component("interior_ring")
    #        except ValueError:
    #           return self._default(
    #                default,
    #                "{!r} has no interior ring variable".format(
    #                    self.__class__.__name__
    #                ),
    #            )

    def has_bounds(self):
        """Whether or not there are bounds.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_bounds`, `get_bounds`, `has_data`,
                     `set_bounds`

        :Returns:

            `bool`
                True if there are bounds, otherwise False.

        **Examples:**


        >>> c = {{package}}.{{class}}()
        >>> b = {{package}}.Bounds(data={{package}}.Data(numpy.arange(10).reshape(5, 2)))
        >>> c.set_bounds(b)
        >>> c.has_bounds()
        True
        >>> c.get_bounds()
        <{{repr}}Bounds: (5, 2) >
        >>> b = c.del_bounds()
        >>> b
        <{{repr}}Bounds: (5, 2) >
        >>> c.has_bounds()
        False
        >>> print(c.get_bounds(None))
        None
        >>> print(c.del_bounds(None))
        None

        """
        return self._has_component("bounds")

    def has_geometry(self):
        """True if there is a geometry type.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `get_geometry`, `set_geometry`, `del_geometry`

        :Returns:

            `bool`
                Whether or not there is a geometry type.

        **Examples:**

        >>> f = {{package}}.read('file.nc')[0]
        >>> c = f.construct('axis=X')
        >>> c.has_geometry()
        True
        >>> c.get_geometry()
        'line'
        >>> b = c.del_geometry()
        >>> c.has_geometry()
        False
        >>> print(c.get_geometry(None))
        None

        >>> c.set_geometry(b)
        >>> c.has_geometry()
        True

        """
        return self._has_component("geometry")

    def has_interior_ring(self):
        """Whether or not there is an interior ring variable.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `del_interior_ring`, `get_interior_ring`,
                     `interior_ring`, `set_interior_ring`

        :Returns:

            `bool`
                True if there is an interior ring variable, otherwise
                False.

        **Examples:**


        >>> c = {{package}}.{{class}}()
        >>> i = {{package}}.InteriorRing(data={{package}}.Data(numpy.arange(10).reshape(5, 2)))
        >>> c.set_interior_ring(i)
        >>> c.has_interior_ring()
        True
        >>> i = c.get_interior_ring()
        >>> i
        <{{repr}}InteriorRing: (5, 2) >
        >>> i.data
        <{{repr}}Data(5, 2): [[0, ..., 9]]>
        >>> i.data.shape
        (5, 2)
        >>> c.del_interior_ring()
        <{{repr}}InteriorRing: (5, 2) >
        >>> c.has_interior_ring()
        False
        >>> print(c.del_interior_ring(None))
        None

        """
        return self._has_component("interior_ring")

    def set_bounds(self, bounds, copy=True):
        """Set the bounds.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_bounds`, `get_bounds`, `has_bounds`,
                     `set_data`

        :Parameters:

            data: `Bounds`
                The bounds to be inserted.

            copy: `bool`, optional
                If False then do not copy the bounds prior to
                insertion. By default the bounds are copied.

        :Returns:

            `None`

        **Examples:**


        >>> c = {{package}}.{{class}}()
        >>> b = {{package}}.Bounds(data={{package}}.Data(numpy.arange(10).reshape(5, 2)))
        >>> c.set_bounds(b)
        >>> c.has_bounds()
        True
        >>> c.get_bounds()
        <{{repr}}Bounds: (5, 2) >
        >>> b = c.del_bounds()
        >>> b
        <{{repr}}Bounds: (5, 2) >
        >>> c.has_bounds()
        False
        >>> print(c.get_bounds(None))
        None
        >>> print(c.del_bounds(None))
        None

        """
        data = self.get_data(None)
        if data is not None:
            bounds_data = bounds.get_data(None)
            if bounds_data is not None and numpy.ndim(
                bounds_data
            ) <= numpy.ndim(data):
                raise ValueError(
                    f"{bounds!r} must have more dimensions than "
                    f"its parent {self!r}"
                )

        if copy:
            bounds = bounds.copy()

        self._set_component("bounds", bounds, copy=False)

    def set_geometry(self, value):
        """Set the geometry type.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `get_geometry`, `set_geometry`, `del_geometry`

        :Parameters:

            value: `str`
                The geometry type to set.

        :Returns:

            `None`

        **Examples:**

        >>> f = {{package}}.read('file.nc')[0]
        >>> c = f.construct('axis=X')
        >>> c.has_geometry()
        True
        >>> c.get_geometry()
        'line'
        >>> b = c.del_geometry()
        >>> c.has_geometry()
        False
        >>> print(c.get_geometry(None))
        None

        >>> c.set_geometry(b)
        >>> c.has_geometry()
        True

        """
        self._set_component("geometry", value, copy=False)

    def set_interior_ring(self, interior_ring, copy=True):
        """Set the interior_ring.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `del_interior_ring`, `get_interior_ring`,
                     `interior_ring`, `has_interior_ring`

        :Parameters:

            interior_ring: `InteriorRing`
                The interior_ring to be inserted.

            copy: `bool`, optional
                If False then do not copy the interior_ring prior to
                insertion. By default the interior_ring are copied.

        :Returns:

            `None`

        **Examples:**


        >>> c = {{package}}.{{class}}()
        >>> i = {{package}}.InteriorRing(data={{package}}.Data(numpy.arange(10).reshape(5, 2)))
        >>> c.set_interior_ring(i)
        >>> c.has_interior_ring()
        True
        >>> i = c.get_interior_ring()
        >>> i
        <{{repr}}InteriorRing: (5, 2) >
        >>> i.data
        <{{repr}}Data(5, 2): [[0, ..., 9]]>
        >>> i.data.shape
        (5, 2)
        >>> c.del_interior_ring()
        <{{repr}}InteriorRing (5, 2) >
        >>> c.has_interior_ring()
        False
        >>> print(c.del_interior_ring(None))
        None

        """
        if copy:
            interior_ring = interior_ring.copy()

        self._set_component("interior_ring", interior_ring, copy=False)
