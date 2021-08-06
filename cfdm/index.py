from . import core, mixin


class Index(
    mixin.NetCDFVariable,
    mixin.NetCDFDimension,
    mixin.NetCDFSampleDimension,
    mixin.PropertiesData,
    core.abstract.PropertiesData,
):
    """An index variable required to uncompress a ragged array.

    A collection of features stored using an indexed ragged array
    combines all features along a single dimension (the sample
    dimension) such that the values of each feature in the collection
    are interleaved.

    The information needed to uncompress the data is stored in an
    index variable that specifies the feature that each element of the
    sample dimension belongs to.

    **NetCDF interface**

    {{netCDF variable}}

    The name of the netCDF dimension spanned by the index variable's
    data (which does not correspond to a domain axis construct) may be
    accessed with the `nc_set_dimension`, `nc_get_dimension`,
    `nc_del_dimension` and `nc_has_dimension` methods.

    The name of the netCDF sample dimension spanned by the compressed
    data (which does not correspond to a domain axis contract) may be
    accessed with the `nc_set_sample_dimension`,
    `nc_get_sample_dimension`, `nc_del_sample_dimension` and
    `nc_has_sample_dimension` methods.

       .. note:: The netCDF sample dimension and the netCDF dimension
                 spanned by the index variable's data are should be
                 the same, unless the compressed data is an indexed
                 contiguous ragged array, in which case they must be
                 different.

    The name of the netCDF instance dimension (that is stored in the
    "instance_dimension" netCDF attribute) is accessed via the
    corresponding domain axis construct.

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
                  ``properties={'long_name': 'which station this obs is for'}``

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
        """A full description of the index variable.

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
        if _create_title and _title is None:
            _title = "Index: " + self.identity(default="")

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
