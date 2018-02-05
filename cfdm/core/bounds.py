import abc

import mixin

from ..structure import Bounds as structure_Bounds

class Bounds(structure_Bounds, mixin.PropertiesData):
    '''
    '''
    __metaclass__ = abc.ABCMeta

    def dump(self, display=True, field=None, key=None, _title=None,
             _create_title=True, _prefix=None, _level=0):
        '''
        '''
        if _create_title and _title is None: 
            _title = 'Coordinate bounds: ' + self.name(default='')

        return super(CoordinateAncillary, self).dump(
            display=display, omit=omit, field=field, key=key, _prefix=_prefix,
             _level=_level, _title=title, _create_title=_create_title)
    #--- End: def
#--- End: class
