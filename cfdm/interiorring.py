import abc

import mixin
import structure


class InteriorRing(mixin.PropertiesData, structure.InteriorRing):
    '''An interior ring array with properties.

An interior ring array records whether each part is to be included or
excluded from the cell. The array spans the same domain axes as its
coordinate array, with the addition of an extra ragged dimension whose
size for each cell is the number of cell parts.

    '''
    __metaclass__ = abc.ABCMeta

    def dump(self, display=True, field=None, key=None, _title=None,
             _create_title=True, _prefix=None, _level=0,
             _omit_properties=None):
        '''
        '''
        if _create_title and _title is None: 
            _title = 'Interior Ring: ' + self.name(default='')

        return super(Bounds, self).dump(
            display=display,
            field=field, key=key,
            _omit_properties=_omit_properties, 
            _prefix=_prefix, _level=_level, _title=_title,
            _create_title=_create_title)
    #--- End: def
    
#--- End: class
