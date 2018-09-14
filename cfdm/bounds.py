from builtins import super

#from . import abstract
from . import mixin
from . import structure


class Bounds(mixin.NetCDFVariable,
             mixin.PropertiesData,
             structure.Bounds):
        #with_metaclass(
        #abc.ABCMeta,
        #type('NewBase', (mixin.PropertiesData, structure.Bounds), {}))):
    '''
    '''
    def __init__(self, properties={}, data=None, source=None,
                 copy=True, _use_data=True):
        '''
        '''
        super().__init__(properties=properties, data=data,
                         source=source, copy=copy,
                         _use_data=_use_data)
        
        if source is not None:
            self._intialise_ncvar_from(source)
    #--- End: def
    
    def dump(self, display=True, field=None, key=None, _title=None,
             _create_title=True, _prefix=None, _level=0,
             _omit_properties=None):
        '''
        '''
        if _create_title and _title is None: 
            _title = 'Bounds: ' + self.name(default='')

        return super().dump(
            display=display,
            field=field, key=key,
            _omit_properties=_omit_properties, 
            _prefix=_prefix, _level=_level, _title=_title,
            _create_title=_create_title)
    #--- End: def
    
#--- End: class
