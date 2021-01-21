from . import mixin
from . import core


class PartNodeCountProperties(
    mixin.NetCDFVariable,
    mixin.NetCDFDimension,
    mixin.Properties,
    core.abstract.Properties,
):
    """Properties for a netCDF part node count variable.

    **NetCDF interface**

    The netCDF part node count variable name may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_del_variable` and
    `nc_has_variable` methods.

    The name of the netCDF dimension spanned by the netCDF part node
    count variable's data may be accessed with the `nc_set_dimension`,
    `nc_get_dimension`, `nc_del_dimension` and `nc_has_dimension`
    methods.

    The netCDF variable group structure may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_variable_groups`,
    `nc_clear_variable_groups` and `nc_set_variable_groups` methods.

    .. versionadded:: (cfdm) 1.8.0

    """

    def __init__(self, properties=None, source=None, copy=True):
        """**Initialization**

        :Parameters:

            {{init properties: `dict`, optional}}

                *Parameter example:*
                  ``properties={'long_name': 'number of obs for this
                  station'}``

            source: optional
                Initialize the properties from those of *source*.

            {{init copy: `bool`, optional}}

        """
        super().__init__(properties=properties, source=source, copy=copy)

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
    ):
        """A full description of the part node count variable.

        Returns a description of all properties.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        if _create_title and _title is None:
            _title = "Part Node Count: " + self.identity(default="")

        return super().dump(
            display=display,
            _key=_key,
            _omit_properties=_omit_properties,
            _prefix=_prefix,
            _level=_level,
            _title=_title,
            _create_title=_create_title,
        )


# --- End: class
