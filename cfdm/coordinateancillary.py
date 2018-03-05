import abc

import mixin

from .structure import CoordinateAncillary as structure_CoordinateAncillary

# ====================================================================
#
# CFDM
#
# ====================================================================

class CoordinateAncillary(mixin.PropertiesData, structure_CoordinateAncillary):
    '''
    '''
    __metaclass__ = abc.ABCMeta

    def dump(self, display=True, field=None, key=None, _title=None,
             _create_title=True, _prefix=None, _level=0,
             _omit_properties=None):
        '''
        '''
        if _create_title and _title is None: 
            _title = 'Coordinate ancillary: ' + self.name(default='')

        return super(CoordinateAncillary, self).dump(
            display=display,
            _omit_properties=_omit_properties, field=field,
            key=key, _prefix=_prefix, _level=_level, _title=_title,
            _create_title=_create_title)
    #--- End: def

#--- End: class
