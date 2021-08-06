from . import core, mixin


class InteriorRing(
    mixin.NetCDFDimension,
    mixin.NetCDFVariable,
    mixin.PropertiesData,
    core.InteriorRing,
):
    """An interior ring array with properties.

    If a cell is composed of multiple polygon parts, an individual
    polygon may define an "interior ring", i.e. a region that is to be
    omitted from, as opposed to included in, the cell extent. In this
    case an interior ring array is required that records whether each
    polygon is to be included or excluded from the cell, and is
    supplied by an interior ring variable in CF-netCDF. The interior
    ring array spans the same domain axis constructs as its coordinate
    array, with the addition of an extra dimension that indexes the
    parts for each cell. For example, a cell describing the land area
    surrounding a lake would require two polygon parts: one defines
    the outer boundary of the land area; the other, recorded as an
    interior ring, is the lake boundary, defining the inner boundary
    of the land area.

    **NetCDF interface**

    {{netCDF variable}}

    The name of the netCDF dimension spanned by the interior ring
    variable's data (which does not correspond to a domain axis
    construct) may be accessed with the `nc_set_dimension`,
    `nc_get_dimension`, `nc_del_dimension` and `nc_has_dimension`
    methods.

    .. versionadded:: (cfdm) 1.8.0

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
                  ``properties={'long_name': 'which station this obs is
                  for'}``

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

        self._initialise_netcdf(source)

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
        """A full description of the interior ring variable.

        Returns a description of all properties, including those of
        components, and provides selected values of all data arrays.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        if _create_title and _title is None:
            _title = "Interior Ring: " + self.identity(default="")

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
