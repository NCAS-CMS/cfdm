from . import core, mixin


class DimensionCoordinate(
    mixin.NetCDFVariable,
    mixin.Coordinate,
    mixin.Files,
    core.DimensionCoordinate,
):
    """A dimension coordinate construct of the CF data model.

    A dimension coordinate construct provides information which locate
    the cells of the domain and which depend on a subset of the domain
    axis constructs. The dimension coordinate construct is able to
    unambiguously describe cell locations because a domain axis can be
    associated with at most one dimension coordinate construct, whose
    data array values must all be non-missing and strictly
    monotonically increasing or decreasing. They must also all be of
    the same numeric data type. If cell bounds are provided, then each
    cell must have exactly two vertices. CF-netCDF coordinate
    variables and numeric scalar coordinate variables correspond to
    dimension coordinate constructs.

    The dimension coordinate construct consists of a data array of the
    coordinate values which spans a subset of the domain axis
    constructs, an optional array of cell bounds recording the extents
    of each cell (stored in a `Bounds` object), and properties to
    describe the coordinates. An array of cell bounds spans the same
    domain axes as its coordinate array, with the addition of an extra
    dimension whose size is that of the number of vertices of each
    cell. This extra dimension does not correspond to a domain axis
    construct since it does not relate to an independent axis of the
    domain. Note that, for climatological time axes, the bounds are
    interpreted in a special way indicated by the cell method
    constructs.

    **NetCDF interface**

    {{netCDF variable}}

    {{netCDF dataset chunks}}

    .. versionadded:: (cfdm) 1.7.0

    """

    def dump(
        self,
        display=True,
        _omit_properties=None,
        _key=None,
        _level=0,
        _title=None,
        _axes=None,
        _axis_names=None,
    ):
        """A full description of the dimension coordinate construct.

        Returns a description of all properties, including those of
        components, and provides selected values of all data arrays.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        if _title is None:
            if _key is None:
                default = ""
            else:
                default = f"key%{_key}"

            _title = "Dimension coordinate: " + self.identity(default=default)

        return super().dump(
            display=display,
            _omit_properties=_omit_properties,
            _key=_key,
            _level=_level,
            _title=_title,
            _axes=_axes,
            _axis_names=_axis_names,
        )
