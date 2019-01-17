from builtins import super

from copy import deepcopy

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

In the CF data model, a bounds component does not have its own
properties because they can not logically be different to those of the
coordinate construct itself. However, it is sometimes desired to store
attributes on a CF-netCDF bounds variable, so it is also allowed to
provide properties to a bounds component.

.. versionadded:: 1.7.0

    '''
    def __init__(self, properties=None, data=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

          *Parameter example:*
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
        
        if source is not None:
            try:
                inherited_properties = source.inherited_properties()
            except AttributeError:
                inherited_properties = {}
        else:
            inherited_properties = {}

        self._set_component('inherited_properties', inherited_properties)

        self._initialise_netcdf(source)
    #--- End: def
    
    def dump(self, display=True, field=None, key=None, _title=None,
             _create_title=True, _prefix=None, _level=0,
             _omit_properties=None, _axes=None, _axis_names=None):
        '''A full description of the bounds component.

Returns a description of all properties and provides selected values
of all data arrays.

.. versionadded:: 1.7.0

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
            _title = 'Bounds: ' + self.name(default='')

        return super().dump(display=display, field=field, key=key,
                            _omit_properties=_omit_properties,
                            _prefix=_prefix, _level=_level,
                            _title=_title,
                            _create_title=_create_title, _axes=_axes,
                            _axis_names=_axis_names)
    #--- End: def
    
    def get_data(self, *default):
        '''Return the data.

Note that the data are returned in a `Data` object. Use the
`get_array` method to return the data as an independent `numpy` array.

.. versionadded:: 1.7.0

.. seealso:: `data`, `del_data`, `get_array`, `has_data`, `set_data`

:Parameters:

    default: optional
        Return *default* if a data object has not been set.

:Returns:

        The data object. If unset then *default* is returned, if
        provided.

**Examples:**

>>> d = cfdm.Data(range(10))
>>> f.set_data(d)
>>> f.has_data()
True
>>> f.get_data()
<Data(10): [0, ..., 9]>
>>> f.del_data()
<Data(10): [0, ..., 9]>
>>> f.has_data()
False
>>> print(f.get_data(None))
None
>>> print(f.del_data(None))
None

        '''
        data = super().get_data(None)

        if data is None:
            return super().get_data(*default)

        if data.get_units(None) is None:
            units = self.inherited_properties().get('units')
            if units is not None:
                data.set_units(units)
        #--- End: if
    
        if data.get_calendar(None) is None:
            calendar = self.inherited_properties().get('calendar')
            if calendar is not None:
                data.set_calendar(calendar)
        #--- End: if

        return data
    #--- End: def

    def inherited_properties(self):
        '''Return the properties inherited from a coordinate construct.

.. versionadded:: 1.7.0

.. seealso:: `properties`

:Returns:

    `dict`
        The inherited properties.

**Examples:**

>>> b.properties()
{}
>>> b.inherited_properties()
{'standard_name': 'longitude',
 'units': 'degrees_east'}

        '''
        return deepcopy(self._get_component('inherited_properties', {}))
    #--- End: def   

    def name(self, default=None, ncvar=True, custom=None,
             all_names=False):
        '''Return a name.

By default the name is the first found of the following:

1. The "standard_name" property.
2. The "cf_role" property, preceeded by ``'cf_role:'``.
3. The "long_name" property, preceeded by ``'long_name:'``.
4. The netCDF variable name, preceeded by ``'ncvar%'``.
5. The value of the *default* parameter.

.. versionadded:: 1.7.0

:Parameters:

    default: optional
        If no other name can be found then return the value of the
        *default* parameter. By default `None` is returned in this
        case.

    ncvar: `bool`, optional
        If False then do not consider the netCDF variable name.

    all_names: `bool`, optional
        If True then return a list of all possible names.

    custom: sequence of `str`, optional
        Replace the ordered list of properties from which to seatch
        for a name. The default list is ``['standard_name', 'cf_role',
        'long_name']``.

        *Parameter example:*
          ``custom=['project']``

        *Parameter example:*
          ``custom=['project', 'long_name']``

:Returns:

        The name. If the *all_names* parameters is True then a list of
        all possible names.

**Examples:**

>>> f.properties()
{'foo': 'bar',
 'long_name': 'Air Temperature',
 'standard_name': 'air_temperature'}
>>> f.nc_get_variable()
'tas'
>>> f.name()
'air_temperature'
>>> f.name(all_names=True)
['air_temperature', 'long_name:Air Temperature', 'ncvar:tas']
>>> x = f.del_property('standard_name')
>>> f.name()
'long_name:Air Temperature'
>>> x = f.del_property('long_name')
>>> f.name()
'ncvar:tas'
>>> f.name(custom=['foo'])
'foo:bar'
>>> f.name(default='no name', custom=['foo'])
['foo:bar', 'no name']

        '''
        inherited_properties = self.inherited_properties()
        if inherited_properties:
            properties = inherited_properties.copy()
            properties.update(self.properties())

            bounds = self.copy()
            bounds.properties(properties)
            self = bounds
            
        return super().name(default=default, ncvar=ncvar,
                            custom=custom, all_names=all_names)
    #--- End: def

#--- End: class
