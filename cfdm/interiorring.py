from builtins import super

from . import mixin
from . import core


class InteriorRing(mixin.NetCDFVariable,
                   mixin.PropertiesData,
                   core.InteriorRing):
#        with_metaclass(
#        abc.ABCMeta,
#        type('NewBase', (mixin.PropertiesData, structure.InteriorRing), {}))):
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

    '''
    def __init__(self, properties={}, data=None, source=None,
                 copy=True, _use_data=True):
        '''TODO
        '''
        super().__init__(properties=properties, data=data,
                         source=source, copy=copy,
                         _use_data=_use_data)
        
        self._initialise_netcdf(source)
    #--- End: def
    
    def dump(self, display=True, field=None, key=None, _title=None,
             _create_title=True, _prefix=None, _level=0,
             _omit_properties=None):
        '''TODO
        '''
        if _create_title and _title is None: 
            _title = 'Interior Ring: ' + self.name(default='')

        return super().dump(display=display, field=field, key=key,
                            _omit_properties=_omit_properties,
                            _prefix=_prefix, _level=_level,
                            _title=_title,
                            _create_title=_create_title)
    #--- End: def
    
#--- End: class
