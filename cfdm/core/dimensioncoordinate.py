import numpy

from . import abstract


class DimensionCoordinate(abstract.Coordinate):
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

    .. versionadded:: (cfdm) 1.7.0

    """

    @property
    def construct_type(self):
        """Return a description of the construct type.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `str`
                The construct type.

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.construct_type
        'dimension_coordinate'

        """
        return "dimension_coordinate"

    def set_data(self, data, copy=True, inplace=True):
        """Set the data.

        The units, calendar and fill value of the incoming `Data` instance
        are removed prior to insertion.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `data`, `del_data`, `get_data`, `has_data`

        :Parameters:

            data: data_like
                The data to be inserted. Must be 1-dimensional,
                i.e. scalar or multidimensional data is not allowed.

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
        if numpy.ndim(data) != 1:
            raise ValueError(
                "Dimension coordinate construct must have 1-dimensional data. "
                f"Got {data!r}"
            )

        return super().set_data(data, copy=copy, inplace=inplace)
