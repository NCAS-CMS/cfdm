from builtins import super

from . import mixin
from . import core


class Index(mixin.NetCDFVariable,
            mixin.NetCDFDimension,
            mixin.NetCDFInstanceDimension,
            mixin.NetCDFSampleDimension,
            mixin.PropertiesData,
            core.abstract.PropertiesData):
    '''An index variable required to uncompress a ragged array.

A collection of features stored using an indexed ragged array combines
all features along a single dimension (the "sample dimension") such
that the values of each feature in the collection are interleaved.

The information needed to uncompress the data is stored in an index
variable that specifies the feature that each element of the sample
dimension belongs to.

.. versionadded:: 1.7.0

    '''
    def __init__(self, properties={}, data=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

        *Example:*
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
    
    def dump(self, display=True, field=None, key=None, _title=None,
             _create_title=True, _prefix='', _level=0,
             _omit_properties=None):
        '''TODO
        '''
        if _create_title and _title is None: 
            _title = 'Index: ' + self.name(default='')

        return super().dump(display=display, field=field, key=key,
                            _omit_properties=_omit_properties,
                            _prefix=_prefix, _level=_level,
                            _title=_title,
                            _create_title=_create_title)
    #--- End: def
    
#--- End: class
