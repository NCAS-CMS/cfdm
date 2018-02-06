import abc

import mixin

from ..structure import FieldAncillary as structure_FieldAncillary

class FieldAncillary(structure_FieldAncillary, mixin.PropertiesData):
    '''A CF field ancillary construct.
    '''
    __metaclass__ = abc.ABCMeta

    def dump(self, display=True, _omit_properties=None, field=None,
             key=None, _level=0, _title=None):
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
            display=display,
            field=field, key=key,
             _omit_properties=_omit_properties,
            _level=_level, _title=_title)
    #--- End: def
    
#--- End: class
