from . import core, mixin


class TiePointIndex(
    mixin.NetCDFVariable,
    mixin.NetCDFSubsampledDimension,
    mixin.NetCDFInterpolationSubareaDimension,
    mixin.PropertiesData,
    mixin.Files,
    core.abstract.PropertiesData,
):
    """A tie point index variable with properties.

    Space may be saved by storing a subsample of the coordinates. The
    uncompressed coordinates can be reconstituted by interpolation
    from the subsampled coordinate values, also called either "tie
    points" or "bounds tie points".

    For each interpolated dimension, the locations of the (bounds) tie
    points are defined by a corresponding tie point index variable,
    which also indicates the extent of each continuous area.

    **NetCDF interface**

    {{netCDF variable}}

    The netCDF subsampled dimension name may be accessed with the
    `nc_set_subsampled_dimension`, `nc_get_subsampled_dimension`,
    `nc_del_subsampled_dimension` and `nc_has_subsampled_dimension`
    methods.

    The netCDF subsampled dimension group structure may be accessed
    with the `nc_set_subsampled_dimension`,
    `nc_get_subsampled_dimension`, `nc_subsampled_dimension_groups`,
    `nc_clear_subsampled_dimension_groups`, and
    `nc_set_subsampled_dimension_groups` methods.

    The netCDF interpolation subarea dimension name may be accessed
    with the `nc_set_interpolation_subarea_dimension`,
    `nc_get_interpolation_subarea_dimension`,
    `nc_del_interpolation_subarea_dimension`, and
    `nc_has_interpolation_subarea_dimension` methods.

    The netCDF interpolation subarea dimension group structure may be
    accessed with the `nc_set_interpolation_subarea_dimension`,
    `nc_get_interpolation_subarea_dimension`,
    `nc_interpolation_subarea_dimension_groups`,
    `nc_clear_interpolation_subarea_dimension_groups` and
    `nc_set_interpolation_subarea_dimension_groups` methods.

    .. versionadded:: (cfdm) 1.10.0.0

    .. seealso:: `InterpolationParameter`

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
        self._initialise_original_filenames(source)

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
        """A full description of the tie point index variable.

        Returns a description of all properties, including those of
        components, and provides selected values of all data arrays.

        .. versionadded:: (cfdm) 1.10.0.0

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
