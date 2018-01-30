from collections import abc

from .mixin

import ..structure

class FieldAncillary(structure.FieldAncillary, mixin.PropertiesData):
    '''A CF field ancillary construct.
    '''
    __metaclass__ abc.ABCMeta

    def dump(self, display=True, omit=(), field=None, key=None,
             _level=0, _title=None):
        '''Return a string containing a full description of the field ancillary
object.

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``f.dump()`` is equivalent to
        ``print f.dump(display=False)``.

:Returns:

    out: `None` or `str`
        A string containing the description.

:Examples:

        '''
        if _title is None:
            _title = 'Field Ancillary: ' + self.name(default='')

        return super(FieldAncillary, self).dump(
            display=display, omit=omit, field=field, key=key,
             _level=_level, _title=_title)
    #--- End: def
    
#--- End: class
