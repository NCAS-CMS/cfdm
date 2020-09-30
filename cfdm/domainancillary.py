from . import mixin
from . import core


class DomainAncillary(mixin.NetCDFVariable,
                      mixin.PropertiesDataBounds,
                      core.DomainAncillary):
    '''A domain ancillary construct of the CF data model.

    A domain ancillary construct provides information which is needed
    for computing the location of cells in an alternative coordinate
    system. It is referenced by a term of a coordinate conversion
    formula of a coordinate reference construct. It contains a data
    array which depends on zero or more of the domain axes.

    It also contains an optional array of cell bounds, stored in a
    `Bounds` object, recording the extents of each cell (only
    applicable if the array contains coordinate data), and properties
    to describe the data.

    An array of cell bounds spans the same domain axes as the data
    array, with the addition of an extra dimension whose size is that
    of the number of vertices of each cell.

    **NetCDF interface**

    The netCDF variable name of the construct may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_del_variable` and
    `nc_has_variable` methods.

    The netCDF variable group structure may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_variable_groups`,
    `nc_clear_variable_groups` and `nc_set_variable_groups` methods.

    .. versionadded:: (cfdm) 1.7.0

    '''
    def __init__(self, properties=None, data=None, bounds=None,
                 geometry=None, interior_ring=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

    :Parameters:

        {{init properties: `dict`, optional}}

           *Parameter example:*
              ``properties={'standard_name': 'altitude'}``

        {{init data: data_like, optional}}

        {{init bounds: `Bounds`, optional}}

        {{init geometry: `str`, optional}}

        {{init interior_ring: `InteriorRing`, optional}}

        source: optional
            Initialize the properties, data and bounds from those of
            *source*.

            {{init source}}

        {{init copy: `bool`, optional}}

        '''
        super().__init__(properties=properties, data=data,
                         bounds=bounds, geometry=geometry,
                         interior_ring=interior_ring, source=source,
                         copy=copy, _use_data=_use_data)

        self._initialise_netcdf(source)

    def dump(self, display=True, _omit_properties=None, _key=None,
             _level=0, _title=None, _axes=None, _axis_names=None):
        '''A full description of the domain ancillary construct.

    Returns a description of all properties, including those of
    components, and provides selected values of all data arrays.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        display: `bool`, optional
            If False then return the description as a string. By
            default the description is printed.

    :Returns:

        {{returns dump}}

        '''
        if _title is None:
            ncvar = self.nc_get_variable(None)
            if ncvar is not None:
                ncvar = ' (ncvar%{0})'.format(ncvar)
            else:
                ncvar = ''

            if _key is None:
                default = ''
            else:
                default = _key

            _title = ('Domain Ancillary: ' + self.identity(default=default) +
                      ncvar)

        return super().dump(display=display,
                            _omit_properties=_omit_properties,
                            _key=_key, _level=_level, _title=_title,
                            _axes=_axes, _axis_names=_axis_names)

# --- End: class
