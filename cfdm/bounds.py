#from __future__ import absolute_import
#from future.utils import with_metaclass

#import abc

from . import mixin
from . import structure


class Bounds(mixin.PropertiesData, structure.Bounds):
        #with_metaclass(
        #abc.ABCMeta,
        #type('NewBase', (mixin.PropertiesData, structure.Bounds), {}))):
    '''
    '''

    def dump(self, display=True, field=None, key=None, _title=None,
             _create_title=True, _prefix=None, _level=0,
             _omit_properties=None):
        '''
        '''
        if _create_title and _title is None: 
            _title = 'Bounds: ' + self.name(default='')

        return super(Bounds, self).dump(
            display=display,
            field=field, key=key,
            _omit_properties=_omit_properties, 
            _prefix=_prefix, _level=_level, _title=_title,
            _create_title=_create_title)
    #--- End: def
    
#--- End: class
