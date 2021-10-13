from . import core, mixin


class TiePointIndex(
    mixin.NetCDFVariable,
    mixin.NetCDFSubsampledDimension,
    mixin.PropertiesData,
    core.abstract.PropertiesData,
):
    """A tie point index variable with propoerties.

    Space may be saved by storing a subsample of the coordinates. The
    uncompressed coordinates can be reconstituted by interpolation
    from the tie points, i.e. the subsampled coordinate values.

    For each interpolated dimension, the locations of the tie point
    coordinates are defined by a corresponding tie point index
    variable, which also indicates the locations of the continuous
    areas.

    **NetCDF interface**

    {{netCDF variable}}

    TODO

    .. versionadded:: (cfdm) 1.9.TODO.0

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
                  ``properties={'long_name': 'uncompression indices'}``

            {{init data: data_like, optional}}

            source: optional
                Initialise the properties and data from those of
                *source*.

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
        """A full description of the tie points variable.

        Returns a description of all properties, including those of
        components, and provides selected values of all data arrays.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        if _create_title and _title is None:
            _title = "Tie point index: " + self.identity(default="")

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
