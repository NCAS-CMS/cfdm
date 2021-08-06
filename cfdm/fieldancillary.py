from . import core, mixin


class FieldAncillary(
    mixin.NetCDFVariable, mixin.PropertiesData, core.FieldAncillary
):
    """A field ancillary construct of the CF data model.

    The field ancillary construct provides metadata which are
    distributed over the same sampling domain as the field itself. For
    example, if a data variable holds a variable retrieved from a
    satellite instrument, a related ancillary data variable might
    provide the uncertainty estimates for those retrievals (varying
    over the same spatiotemporal domain).

    The field ancillary construct consists of an array of the
    ancillary data, which is zero-dimensional or which depends on one
    or more of the domain axes, and properties to describe the
    data. It is assumed that the data do not depend on axes of the
    domain which are not spanned by the array, along which the values
    are implicitly propagated. CF-netCDF ancillary data variables
    correspond to field ancillary constructs. Note that a field
    ancillary construct is constrained by the domain definition of the
    parent field construct but does not contribute to the domain's
    definition, unlike, for instance, an auxiliary coordinate
    construct or domain ancillary construct.

    **NetCDF interface**

    {{netCDF variable}}

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
                  ``properties={'standard_name': 'altitude'}``

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
        _omit_properties=None,
        _key=None,
        _level=0,
        _title=None,
        _axes=None,
        _axis_names=None,
    ):
        """A full description of the field ancillary construct.

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
            _title = "Field Ancillary: " + self.identity(default="")

        return super().dump(
            display=display,
            _key=_key,
            _omit_properties=_omit_properties,
            _level=_level,
            _title=_title,
            _axes=_axes,
            _axis_names=_axis_names,
        )
