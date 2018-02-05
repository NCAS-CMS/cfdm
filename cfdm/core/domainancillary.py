import abc

import mixin

from ..structure import DomainAncillary as structure_DomainAncillary

class DomainAncillary(structure_DomainAncillary, mixin.PropertiesDataBounds):
    '''A CF domain ancillary construct.

A domain ancillary construct provides information which is needed for
computing the location of cells in an alternative coordinate
system. It is the value of a term of a coordinate conversion formula
that contains a data array which depends on zero or more of the domain
axes.

It also contains an optional array of cell bounds recording the
extents of each cell (only applicable if the array contains coordinate
data), and properties to describe the data (in the same sense as for
the field construct).

An array of cell bounds spans the same domain axes as the data array,
with the addition of an extra dimension whose size is that of the
number of vertices of each cell.

    '''
    __metaclass__ = abc.ABCMeta
    
    def dump(self, display=True, omit=(), field=None, key=None,
             _level=0, _title=None):
        '''Return a string containing a full description of the domain
ancillary object.

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default

        the description is printed, i.e. ``f.dump()`` is equivalent to
        ``print f.dump(display=False)``.

    field: `Field`, optional

    key: `str`, optional

:Returns:

    out: `None` or `str`
        A string containing the description.

:Examples:

        '''
        if _title is None:
            ncvar = self.ncvar()
            if ncvar is not None:
                ncvar = ' (ncvar%{0})'.format(ncvar)
            else:
                ncvar = ''

            _title = 'Domain Ancillary: ' + self.name(default='') + ncvar
            

        return super(DomainAncillary, self).dump(
            display=display, omit=omit, field=field, key=key, _level=_level,
            _title=_title)
    #--- End: def

#--- End: class
