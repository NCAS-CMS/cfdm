from __future__ import absolute_import
from builtins import super

from . import mixin
from . import core


class DimensionCoordinate(mixin.NetCDFVariable,
                          mixin.Coordinate,
                          core.DimensionCoordinate):
    '''A dimension coordinate construct of the CF data model.

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

:Examples:

        '''
        if _title is None:
            if key is None:
                default = ''
            else:
                default = key
                
            _title = 'Dimension coordinate: ' + self.name(default=default)
                
        return super().dump(display=display,
                            _omit_properties=_omit_properties,
                            field=field, key=key, _level=_level,
                            _title=_title, _axes=_axes,
                            _axis_names=_axis_names)
    #--- End: def

#--- End: class
