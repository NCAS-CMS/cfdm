from . import core, mixin


class InterpolationParameter(
    mixin.NetCDFVariable,
    mixin.PropertiesData,
    mixin.Files,
    core.abstract.PropertiesData,
):
    """An interpolation parameter variable.

    Space may be saved by storing a subsample of the coordinates. The
    uncompressed coordinates can be reconstituted by interpolation
    from the subsampled coordinate values, also called either "tie
    points" or "bounds tie points".

    An interpolation parameter variable provides values for
    coefficient terms in the interpolation equation, or for any other
    terms that configure the interpolation process.

    **NetCDF interface**

    {{netCDF variable}}

    The netCDF subsampled dimension name and the netCDF interpolation
    subarea dimension name, if required, are set on the on the
    corresponding tie point index variable.

    .. versionadded:: (cfdm) 1.10.0.0

    .. seealso:: `TiePointIndex`

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
                  ``properties={'long_name': 'interpolation parameter'}``

            {{init data: data_like, optional}}

            {{init source: optional}}

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
        """A full description of the interpolation parameter variable.

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
            _title = "Interpolation parameter: " + self.identity(default="")

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
