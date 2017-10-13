from .boundedvariable import BoundedVariable
'''

**Initialization**

:Parameters:

    properties: `dict`, optional
        Initialize a new instance with CF properties from a
        dictionary's key/value pairs.

    attributes: `dict`, optional
        Provide the new instance with attributes from a dictionary's
        key/value pairs.

    data: `Data`, optional
        Provide the new instance with an N-dimensional data array.

    bounds: `Data` or `Bounds`, optional
        Provide the new instance with cell bounds.

    copy: `bool`, optional
        If False then do not copy arguments prior to
        initialization. By default arguments are deep copied.

'''         

class DomainAncillary(BoundedVariable):
    '''A CF domain ancillary construct.

A domain ancillary construct provides information which is needed for
computing the location of cells in an alternative coordinate
system. It is the value of a term of a coordinate conversion formula
that contains a data array which depends on one or more of the domain
axes.

It also contains an optional array of cell bounds recording the
extents of each cell (only applicable if the array contains coordinate
data), and properties to describe the data (in the same sense as for
the field construct).

An array of cell bounds spans the same domain axes as the data array,
with the addition of an extra dimension whose size is that of the
number of vertices of each cell.

    '''
    def __init__(self, properties={}, attributes={}, data=None,
                 bounds=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Initialize a new instance with CF properties from a
        dictionary's key/value pairs.

    attributes: `dict`, optional
        Provide the new instance with attributes from a dictionary's
        key/value pairs.

    data: `Data`, optional
        Provide the new instance with an N-dimensional data array.

    bounds: `Data` or `Bounds`, optional
        Provide the new instance with cell bounds.

    source: `DomainAncillary`, optional
        Take the attributes, CF properties and data array from the
        source object. Any attributes, CF properties or data array
        specified with other parameters are set after initialisation
        from the source instance.

    copy: `bool`, optional
        If False then do not copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        super(DomainAncillary, self).__init__(properties=properties,
                                              attributes=attributes,
                                              data=data,
                                              bounds=bounds,
                                              source=source,
                                              copy=copy)
        
#        if self.hasdata and not self.ndim:
#            # Turn a scalar object into 1-d
#            self.expand_dims(0, copy=False)
    #--- End: def
    
    @property
    def isdomainancillary(self):
        '''True, denoting that the variable is a domain ancillary object.

.. versionadded:: 2.0

:Examples:

>>> f.isdomainancillary
True
        '''
        return True
    #--- End: def
    
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
            _title = 'Domain Ancillary: ' + self.name(default='')

        return super(DomainAncillary, self).dump(
            display=display, omit=omit, field=field, key=key, _level=_level,
            _title=_title)
    #--- End: def

#--- End: class
