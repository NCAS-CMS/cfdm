from . import core, mixin


class NodeCountProperties(
    mixin.NetCDFVariable,
    mixin.Properties,
    mixin.Files,
    core.abstract.Properties,
):
    """Properties for a netCDF node count variable.

    **NetCDF interface**

    {{netCDF variable}}

    .. versionadded:: (cfdm) 1.8.0

    """

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
        """A full description of the node count variable.

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
            _title = "Node Count: " + self.identity(default="")

        return super().dump(
            display=display,
            _key=_key,
            _omit_properties=_omit_properties,
            _prefix=_prefix,
            _level=_level,
            _title=_title,
            _create_title=_create_title,
        )
