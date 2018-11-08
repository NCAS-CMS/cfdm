from builtins import super

from . import mixin
from . import core


class DomainAncillary(mixin.NetCDFVariable,
                      mixin.PropertiesDataBounds,
                      core.DomainAncillary):
    '''A domain ancillary construct of the CF data model.

A domain ancillary construct provides information which is needed for
computing the location of cells in an alternative coordinate
system. It is referenced by a term of a coordinate conversion formula
of a coordinate reference construct. It contains a data array which
depends on zero or more of the domain axes.

It also contains an optional array of cell bounds, stored in a
`Bounds` object, recording the extents of each cell (only applicable
if the array contains coordinate data), and properties to describe the
data.

An array of cell bounds spans the same domain axes as the data array,
with the addition of an extra dimension whose size is that of the
number of vertices of each cell.

    '''
    def __init__(self, properties={}, data=None, bounds=None,
                 geometry=None, interior_ring=None, source=None,
                 copy=True, _use_data=True):
        '''TODO
        '''
        super().__init__(properties=properties, data=data,
                         bounds=bounds, geometry=geometry,
                         interior_ring=interior_ring, source=source,
                         copy=copy, _use_data=_use_data)
        
#        if source is not None:
 #           self._intialise_ncvar_from(source)
        self._initialise_netcdf(source)
    #--- End: def
    
    def dump(self, display=True, _omit_properties=None, field=None,
             key='', _level=0, _title=None, _axes=None,
             _axis_names=None):
        '''TODO Return a string containing a full description of the domain
ancillary object.

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default

        the description is printed, i.e. ``f.dump()`` is equivalent to
        ``print f.dump(display=False)``.

    field: `Field`, optional

    key: `str`, optional

:Returns:

    out: `None` or `str`
        A string containing the description.

**Examples**

        '''
        if _title is None:
            ncvar = self.nc_get_variable(None)
            if ncvar is not None:
                ncvar = ' (ncvar%{0})'.format(ncvar)
            else:
                ncvar = ''

            _title = 'Domain Ancillary: ' + self.name(default=key) + ncvar
            

        return super().dump(display=display,
                            _omit_properties=_omit_properties,
                            field=field, key=key, _level=_level,
                            _title=_title, _axes=_axes,
                            _axis_names=_axis_names)
    #--- End: def

#--- End: class
