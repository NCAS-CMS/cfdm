from . import core, mixin


class AuxiliaryCoordinate(
    mixin.NetCDFVariable, mixin.Coordinate, core.AuxiliaryCoordinate
):
    """An auxiliary coordinate construct of the CF data model.

    An auxiliary coordinate construct provides information which
    locate the cells of the domain and which depend on a subset of the
    domain axis constructs. Auxiliary coordinate constructs have to be
    used, instead of dimension coordinate constructs, when a single
    domain axis requires more then one set of coordinate values, when
    coordinate values are not numeric, strictly monotonic, or contain
    missing values, or when they vary along more than one domain axis
    construct simultaneously. CF-netCDF auxiliary coordinate variables
    and non-numeric scalar coordinate variables correspond to
    auxiliary coordinate constructs.

    The auxiliary coordinate construct consists of a data array of the
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

    {{netCDF variable group}}

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
                  ``properties={'standard_name': 'latitude'}``

            {{init data: data_like, optional}}

            {{init bounds: `Bounds`, optional}}

            {{init geometry: `str`, optional}}

            {{init interior_ring: `InteriorRing`, optional}}

            source: optional
                Initialise the properties, data and bounds from those of
                *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(
            properties=properties,
            data=data,
            bounds=bounds,
            geometry=geometry,
            interior_ring=interior_ring,
            source=source,
            copy=copy,
            _use_data=_use_data,
        )

        self._initialise_netcdf(source)

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
        """A full description of the auxiliary coordinate construct.

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
            _title = "Auxiliary coordinate: " + self.identity(default="")

        return super().dump(
            display=display,
            _key=_key,
            _level=_level,
            _title=_title,
            _omit_properties=_omit_properties,
            _axes=_axes,
            _axis_names=_axis_names,
        )
