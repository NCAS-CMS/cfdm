from __future__ import absolute_import
from builtins import super

from . import mixin
from . import core


class DimensionCoordinate(mixin.NetCDFVariable,
                          mixin.Coordinate,
                          core.DimensionCoordinate):
    '''A dimension coordinate construct of the CF data model.

A dimension coordinate construct provides information which locate the
cells of the domain and which depend on a subset of the domain axis
constructs. The dimension coordinate construct is able to
unambiguously describe cell locations because a domain axis can be
associated with at most one dimension coordinate construct, whose data
array values must all be non-missing and strictly monotonically
increasing or decreasing. They must also all be of the same numeric
data type. If cell bounds are provided, then each cell must have
exactly two vertices. CF-netCDF coordinate variables and numeric
scalar coordinate variables correspond to dimension coordinate
constructs.

The dimension coordinate construct consists of a data array of the
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

.. versionadded:: 1.7

    '''
    def __init__(self, properties=None, data=None, bounds=None,
                 geometry=None, interior_ring=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialisation**

:Parameters:

    properties: `dict`, optional
       Set descriptive properties. The dictionary keys are property
       names, with corresponding values. Ignored if the *source*
       parameter is set.

       *Example:*
          ``properties={'standard_name': 'time'}``

       Properties may also be set after initialisation with the
       `properties` and `set_property` methods.

    data: `Data`, optional
        Set the data array. Ignored if the *source* parameter is set.

        The data array may also be set after initialisation with the
        `set_data` method.

    bounds: `Bounds`, optional
        Set the bounds array. Ignored if the *source* parameter is
        set.

        The bounds array may also be set after initialisation with the
        `set_bounds` method.

    source: optional
        Initialize the properties, data and bounds from those of
        *source*.

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

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
        '''A full description of the dimension coordinate construct.

Returns a description of all properties, including those of
components, and provides selected values of all data arrays.

.. versionadded:: 1.7

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed.

:Returns:

    out: `None` or `str`
        The description. If *display* is True then the description is
        printed and `None` is returned. Otherwise the description is
        returned as a string.

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
