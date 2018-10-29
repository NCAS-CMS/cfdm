from builtins import super

from . import mixin
from . import core


class FieldAncillary(mixin.NetCDFVariable,
                     mixin.PropertiesData,
                     core.FieldAncillary):
    '''A field ancillary construct of the CF data model.

The field ancillary construct provides metadata which are distributed
over the same sampling domain as the field itself. For example, if a
data variable holds a variable retrieved from a satellite instrument,
a related ancillary data variable might provide the uncertainty
estimates for those retrievals (varying over the same spatiotemporal
domain).

The field ancillary construct consists of an array of the ancillary
data, which is zero-dimensional or which depends on one or more of the
domain axes, and properties to describe the data. It is assumed that
the data do not depend on axes of the domain which are not spanned by
the array, along which the values are implicitly propagated. CF-netCDF
ancillary data variables correspond to field ancillary
constructs. Note that a field ancillary construct is constrained by
the domain definition of the parent field construct but does not
contribute to the domain's definition, unlike, for instance, an
auxiliary coordinate construct or domain ancillary construct.

    '''

    def __init__(self, properties={}, data=None, source=None,
                 copy=True, _use_data=True):
        '''
        '''
        super().__init__(properties=properties, data=data,
                         source=source, copy=copy,
                         _use_data=_use_data)
        
#        if source is not None:
        self._initialise_netcdf(source)
    #--- End: def
    
    def dump(self, display=True, _omit_properties=None, field=None,
             key=None, _level=0, _title=None, _axes=None,
             _axis_names=None):
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

**Examples**

        '''
        if _title is None:
            _title = 'Field Ancillary: ' + self.name(default='')

        return super().dump(display=display, field=field, key=key,
                            _omit_properties=_omit_properties,
                            _level=_level, _title=_title, _axes=_axes,
                            _axis_names=_axis_names)
    #--- End: def
    
#--- End: class
