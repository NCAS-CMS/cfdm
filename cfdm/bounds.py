from . import core, mixin


class Bounds(
    mixin.NetCDFVariable,
    mixin.NetCDFDimension,
    mixin.PropertiesData,
    core.Bounds,
):
    """A cell bounds component.

    Specifically, a cell bounds component of a coordinate or domain
    ancillary construct of the CF data model.

    An array of cell bounds spans the same domain axes as its
    coordinate array, with the addition of an extra dimension whose
    size is that of the number of vertices of each cell. This extra
    dimension does not correspond to a domain axis construct since it
    does not relate to an independent axis of the domain. Note that,
    for climatological time axes, the bounds are interpreted in a
    special way indicated by the cell method constructs.

    In the CF data model, a bounds component does not have its own
    properties because they can not logically be different to those of
    the coordinate construct itself. However, it is sometimes desired
    to store attributes on a CF-netCDF bounds variable, so it is also
    allowed to provide properties to a bounds component.

    **NetCDF interface**

    {{netCDF variable}}

    The name of the trailing netCDF dimension spanned by bounds (which
    does not correspond to a domain axis construct) may be accessed
    with the `nc_set_dimension`, `nc_get_dimension`,
    `nc_del_dimension` and `nc_has_dimension` methods.

    {{netCDF variable group}}

    .. versionadded:: (cfdm) 1.7.0

    """

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
                     ``properties={'standard_name': 'grid_latitude'}``

            {{init data: data_like, optional}}

            source: optional
                Initialise the properties and data from those of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(
            properties=properties,
            data=data,
            source=source,
            copy=copy,
            _use_data=_use_data,
        )

        if source is not None:
            try:
                inherited_properties = source.inherited_properties()
            except AttributeError:
                inherited_properties = {}
        else:
            inherited_properties = {}

        self._set_component(
            "inherited_properties", inherited_properties, copy=False
        )

        self._initialise_netcdf(source)

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def dump(
        self,
        display=True,
        _key=None,
        _title=None,
        _create_title=True,
        _prefix="",
        _level=0,
        _omit_properties=None,
        _axes=None,
        _axis_names=None,
    ):
        """A full description of the bounds component.

        Returns a description of all properties and provides selected
        values of all data arrays.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        if _create_title and _title is None:
            _title = "Bounds: " + self.identity(default="")

        return super().dump(
            display=display,
            _key=_key,
            _omit_properties=_omit_properties,
            _prefix=_prefix,
            _level=_level,
            _title=_title,
            _create_title=_create_title,
            _axes=_axes,
            _axis_names=_axis_names,
        )

    def get_data(self, default=ValueError(), _units=True, _fill_value=True):
        """Return the data.

        Note that the data are returned in a `Data` object. Use the
        `array` attribute of the `Data` instance to return the data as an
        independent `numpy` array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `data`, `del_data`, `has_data`, `set_data`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if data have
                not been set.

                {{default Exception}}

        :Returns:

            `Data`
                The data.

        **Examples:**

        >>> f = {{package}}.Field(
        ...     properties={'standard_name': 'surface_altitude'})
        >>> d = {{package}}.Data(range(10))
        >>> f.set_data(d)
        >>> f.has_data()
        True
        >>> f.get_data()
        <{{repr}}Data(10): [0, ..., 9]>

        >>> f.del_data()
        <{{repr}}Data(10): [0, ..., 9]>
        >>> f.has_data()
        False
        >>> print(f.get_data(None))
        None
        >>> print(f.del_data(None))
        None

        """
        data = super().get_data(
            default=None, _units=_units, _fill_value=_fill_value
        )
        if data is None:
            if default is None:
                return

            return self._default(
                default, f"{self.__class__.__name__} has no data"
            )

        if _units or _fill_value:
            inherited_properties = self._get_component(
                "inherited_properties", {}
            )

            if _units:
                if not data.has_units():
                    units = inherited_properties.get("units")
                    if units is not None:
                        data.set_units(units)

                if not data.has_calendar():
                    calendar = inherited_properties.get("calendar")
                    if calendar is not None:
                        data.set_calendar(calendar)

            if _fill_value and not data.has_fill_value():
                fv = inherited_properties.get("fill_value")  # TODO
                if fv is not None:
                    data.set_fill_value(fv)

        return data

    def inherited_properties(self):
        """Return the properties inherited from a coordinate construct.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `properties`

        :Returns:

            `dict`
                The inherited properties.

        **Examples:**

        >>> f = {{package}}.example_field(6)
        >>> d = f.constructs('longitude').value()
        >>> b = d.bounds
        >>> b
        <{{repr}}Bounds: longitude(2, 3, 4) degrees_east>

        >>> b.inherited_properties()
        {'units': 'degrees_east', 'standard_name': 'longitude'}

        """
        return self._get_component("inherited_properties", {}).copy()

    def identity(self, default=""):
        """Return the canonical identity.

        By default the identity is the first found of the following:

        1. The ``standard_name`` property.
        2. The ``cf_role`` property, preceded by ``'cf_role='``.
        3. The ``long_name`` property, preceded by ``'long_name='``.
        4. The netCDF variable name, preceded by ``'ncvar%'``.
        5. The value of the *default* parameter.

        Properties include any inherited properties.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `identities`

        :Parameters:

            default: optional
                If no identity can be found then return the value of the
                default parameter.

        :Returns:

                The identity.

        **Examples:**

        >>> f = {{package}}.example_field(6)
        >>> d = f.constructs('longitude').value()
        >>> b = d.bounds
        >>> b
        <{{repr}}Bounds: longitude(2, 3, 4) degrees_east>
        >>> b.identity()
        'longitude'

        """
        inherited_properties = self._get_component(
            "inherited_properties", None
        )
        if inherited_properties:
            bounds = self.copy()
            properties = bounds.properties()
            bounds.set_properties(inherited_properties)
            bounds.set_properties(properties)
            self = bounds

        return super().identity(default=default)
