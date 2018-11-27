from builtins import super

from . import abstract


class Bounds(abstract.PropertiesData):
    '''A cell bounds component of a coordinate or domain ancillary
construct of the CF data model.

An array of cell bounds spans the same domain axes as its coordinate
array, with the addition of an extra dimension whose size is that of
the number of vertices of each cell. This extra dimension does not
correspond to a domain axis construct since it does not relate to an
independent axis of the domain. Note that, for climatological time
axes, the bounds are interpreted in a special way indicated by the
cell method constructs.

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
           ``properties={'standard_name': 'altitude'}``
        
        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.

    data: `Data`, optional
        Set the data. Ignored if the *source* parameter is set.
        
        The data also may be set after initialisation with the
        `set_data` method.
        
    source: optional
        Override the *properties* and *data* parameters with
        ``source.properties()`` and ``source.get_data(None)``
        respectively.

        If *source* does not have one of these methods, then the
        corresponding parameter is not set.
        
    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__(properties=properties, data=data,
                         source=source, copy=copy)

        if source is not None:
            try:
                inherited_properties = source._get_component('inherited_properties')
            except AttributeError:
                inherited_properties = {}
        else:
            inherited_properties = {}

        self._set_component('inherited_properties',  inherited_properties)
    #--- End: def

    def get_data(self, *default):
        '''Return the data.

Note that the data are returned in a `Data` object. Use the
`get_array` method to return the data as an independent `numpy` array.

.. versionadded:: 1.7

.. seealso:: `data`, `del_data`, `get_array`, `has_data`, `set_data`

:Parameters:

    default: optional
        Return *default* if a data object has not been set.

:Returns:

    out: 
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
            units = self._get_component('inherited_properties', {}).get('units')
            if units is not None:
                data.set_units(units)
        #--- End: if
    
        if data.get_calendar(None) is None:
            calendar = self._get_component('inherited_properties', {}).get('calendar')
            if calendar is not None:
                data.set_calendar(calendar)
        #--- End: if

        return data
    #--- End: def

#--- End: class
