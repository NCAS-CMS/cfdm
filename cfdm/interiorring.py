from builtins import super

from . import mixin
from . import core


class InteriorRing(mixin.NetCDFDimension,
                   mixin.NetCDFVariable,
                   mixin.PropertiesData,
                   core.InteriorRing):
    '''An interior ring array with properties.

For polygon geometries, an individual geometry may define an "interior
ring", i.e. a hole that is to be omitted from the cell extent (as
would occur, for example, for a cell describing the land area of a
region containing a lake). In this case an interior ring array is
required that records whether each polygon is to be included or
excluded from the cell, supplied by an interior ring variable in
CF-netCDF. The interior ring array spans the same domain axes as its
coordinate array, with the addition of an extra ragged dimension that
indexes the geometries for each cell.

**NetCDF interface**

The netCDF variable name of the interior ring variable may be accessed
with the `nc_set_variable`, `nc_get_variable`, `nc_del_variable` and
`nc_has_variable` methods.

TODO dimension

.. versionadded:: 1.8.0

    '''
    def __init__(self, properties=None, data=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

        *Parameter example:*
          ``properties={'long_name': 'which station this obs is for'}``

        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.

    data: `Data`, optional
        Set the data array. Ignored if the *source* parameter is set.

        The data array may also be set after initialisation with the
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
    
    def dump(self, display=True, _key=None, _title=None,
             _create_title=True, _prefix=None, _level=0,
             _omit_properties=None, _axes=None, _axis_names=None):
        '''A full description of the interior ring variable.

Returns a description of all properties, including those of
components, and provides selected values of all data arrays.

.. versionadded:: 1.8.0

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed.

:Returns:

    `None` or `str`
        The description. If *display* is True then the description is
        printed and `None` is returned. Otherwise the description is
        returned as a string.

        '''
        if _create_title and _title is None: 
            _title = 'Interior Ring: ' + self.identity(default='')

        return super().dump(display=display, _key=_key,
                            _omit_properties=_omit_properties,
                            _prefix=_prefix, _level=_level,
                            _title=_title,
                            _create_title=_create_title, _axes=_axes,
                            _axis_names=_axis_names)
    #--- End: def
    
#--- End: class
