from builtins import super

from . import mixin
from . import core


class Bounds(mixin.NetCDFVariable,
             mixin.PropertiesData,
             core.Bounds):
    '''A cell bounds component of a coordinate or domain ancillary
construct of the CF data model.

An array of cell bounds spans the same domain axes as its coordinate
array, with the addition of an extra dimension whose size is that of
the number of vertices of each cell. This extra dimension does not
correspond to a domain axis construct since it does not relate to an
independent axis of the domain. Note that, for climatological time
axes, the bounds are interpreted in a special way indicated by the
cell method constructs.

In the CF data model, cell bounds do not have their own properties
because they can not logically be different to those of the coordinate
construct itself. However, it is sometimes desired to store properties
on a CF-netCDF bounds variable, so this class supports this
capability.

.. versionadded:: 1.7

    '''
    def __init__(self, properties=None, data=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

          *Example:*
             ``properties={'standard_name': 'grid_latitude'}``
        
        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.

    data: `Data`, optional
        Set the data. Ignored if the *source* parameter is set.
        
        The data also may be set after initialisation with the
        `set_data` method.
        
    source: optional
        Initialize the properties and data from those of *source*.
        
    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__(properties=properties, data=data,
                         source=source, copy=copy,
                         _use_data=_use_data)
        
        self._initialise_netcdf(source)
    #--- End: def
    
    def dump(self, display=True, field=None, key=None, _title=None,
             _create_title=True, _prefix=None, _level=0,
             _omit_properties=None, _axes=None, _axis_names=None):
        '''A full description of the bounds component.

Returns a description of all properties and provides selected values
of all data arrays.

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
        if _create_title and _title is None: 
            _title = 'Bounds: ' + self.name(default='')

        return super().dump(display=display, field=field, key=key,
                            _omit_properties=_omit_properties,
                            _prefix=_prefix, _level=_level,
                            _title=_title,
                            _create_title=_create_title, _axes=_axes,
                            _axis_names=_axis_names)
    #--- End: def
    
    def name(self, default=None, ncvar=True, custom=None,
             all_names=False):
        '''TODO

        '''
        inherited_properties = self._get_component('inherited_properties', None)
        if inherited_properties:
            properties = inherited_properties.copy()
            properties.update(self.properties())

            bounds = self.copy()
            bounds.properties(properties)
            self = bounds
            
        return super().name(default=default, ncvar=ncvar,
                            custom=custom,
                            all_names=all_names)
    #--- End: def

#--- End: class
