from collections import abc

from .abstract import AbstractCoordinate

# ====================================================================
#
# AuxiliaryCoordinate object
#
# ====================================================================

class AuxiliaryCoordinate(AbstractCoordinate):
    '''A CF auxiliary coordinate construct.


**Attributes**

===============  ========  ===================================================
Attribute        Type      Description
===============  ========  ===================================================
`!climatology`   ``bool``  Whether or not the bounds are intervals of
                           climatological time. Presumed to be False if unset.
===============  ========  ===================================================

    '''
    __metaclass__ = abc.ABCMeta

    @property
    def role(self):
        '''ancillary property
        '''
        out = self._role
        if out is None:
            raise ValueError("adasd")

        return out
    @role.setter
    def role(self, value):
        self._role = value
        self._ancillary_properties.add('role')
    @role.setter
    def role(self, value):
        self._role = None
        self._ancillary_properties.discard('role')
    #--- End: def
    
    @property
    def interior_ring(self):
        '''ancillary array
        '''
        out = self._interior_ring
        if out is None:
            raise ValueError("adasdssd")

        return out
    @interior_ring.setter
    def interior_ring(self, value):
        self._interior_ring = value
        self._ancillary_arrays.add('interior_ring')
    @interior_ring.setter
    def interior_ring(self, value):
        self._interior_ring = None
        self._ancillary_array.discard('rinterior_ring')
    #--- End: def
    
    @property
    def part_node_count(self):
        '''ancillary array
        '''
        out = self._part_node_count
        if out is None:
            raise ValueError("adasdssd")

        return out
    @part_node_count.setter
    def part_node_count(self, value):
        self._part_node_count = value
        self._ancillary_arrays.add('part_node_count')
    @part_node_count.setter
    def part_node_count(self, value):
        self._part_node_count = None
        self._ancillary_array.discard('rpart_node_count')
    #--- End: def


    def ancillary_arrays(self):
        '''
        '''
        out = {}
        for ancillary in self._ancillary_arrays:
            out[ancillary] = getattr(self, ancillary)

        return out
    #--- End: def

    def ancillary_properties(self):
        '''
        '''
        out = {}
        for ancillary in self._ancillary_properties:
            out[ancillary] = getattr(self, ancillary)

        return out
    #--- End: def
                         
    def dump(self, display=True, omit=(), field=None, key=None,
             _level=0, _title=None):
        '''Return a string containing a full description of the auxiliary
coordinate object.

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
            _title = 'Auxiliary coordinate: ' + self.name(default='')

        return super(AuxiliaryCoordinate, self).dump(
            display=display, omit=omit, field=field, key=key,
             _level=_level, _title=_title)
    #--- End: def

    
#--- End: class
