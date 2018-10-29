from builtins import super

from . import mixin
from . import core


class AuxiliaryCoordinate(mixin.NetCDFVariable,
                          mixin.Coordinate,
                          core.AuxiliaryCoordinate):
    '''An auxiliary coordinate construct of the CF data model.

An auxiliary coordinate construct provides information which locate
the cells of the domain and which depend on a subset of the domain
axis constructs. Auxiliary coordinate constructs have to be used,
instead of dimension coordinate constructs, when a single domain axis
requires more then one set of coordinate values, when coordinate
values are not numeric, strictly monotonic, or contain missing values,
or when they vary along more than one domain axis construct
simultaneously. CF-netCDF auxiliary coordinate variables and
non-numeric scalar coordinate variables correspond to auxiliary
coordinate constructs.

The auxiliary coordinate construct consists of a data array of the
coordinate values which spans a subset of the domain axis constructs,
an optional array of cell bounds recording the extents of each cell
(stored in a `Bounds` object), and properties to describe the
coordinates. An array of cell bounds spans the same domain axes as its
coordinate array, with the addition of an extra dimension whose size
is that of the number of vertices of each cell. This extra dimension
does not correspond to a domain axis construct since it does not
relate to an independent axis of the domain. Note that, for
climatological time axes, the bounds are interpreted in a special way
indicated by the cell method constructs.

    '''
    def __init__(self, properties={}, data=None, bounds=None,
                 geometry=None, interior_ring=None, source=None,
                 copy=True, _use_data=True):
        '''
        '''
        super().__init__(properties=properties, data=data,
                         bounds=bounds, geometry=geometry,
                         interior_ring=interior_ring, source=source,
                         copy=copy, _use_data=_use_data)
        
#        if source is not None:
        self._initialise_netcdf(source)
    #--- End: def

    
    def dump(self, display=True, _omit_properties=None, field=None,
             key=None, _level=0, _title=None, _axes=None,
             _axis_names=None):
        '''Return a string containing a full description of the auxiliary
coordinate object.

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``f.dump()`` is equivalent to
        ``print f.dump(display=False)``.

:Returns:

    out: `None` or `str`
        A string containing the description.

**Examples**

        '''
        if _title is None:
            _title = 'Auxiliary coordinate: ' + self.name(default='')

        return super().dump(display=display, field=field, key=key,
                            _level=_level, _title=_title,
                            _omit_properties=_omit_properties,
                            _axes=_axes, _axis_names=_axis_names)
    #--- End: def

    
#--- End: class
