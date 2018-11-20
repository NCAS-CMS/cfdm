from builtins import super
from future.utils import with_metaclass

import abc

from . import PropertiesData


class PropertiesDataBounds(with_metaclass(abc.ABCMeta, PropertiesData)):
    '''Abstract base class for a data array with bounds and descriptive
properties.

.. versionadded:: 1.7

    '''    
    def __init__(self, properties=None, data=None, bounds=None,
                 geometry=None, interior_ring=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

          *Example:*
             ``properties={'standard_name': 'longitude'}``
        
        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.
  
    data: `Data`, optional
        Set the data array. Ignored if the *source* parameter is set.
        
        The data array may also be set after initialisation with the
        `set_data` method.
  
    bounds: `Bounds`, optional
        Set the bounds array. Ignored if the *source* parameter is
        set.
        
        The bounds array may also be set after initialisation with the
        `set_bounds` method.
  
    geometry: `str`, optional
        Set the geometry type. Ignored if the *source* parameter is
        set.
        
          *Example:*
             ``geometry='polygon'``
        
        The geometry type may also be set after initialisation with
        the `set_geometry` method.
  
    interior_ring: `InteriorRing`, optional
        Set the interior ring array. Ignored if the *source* parameter
        is set.
        
        The interior ring array may also be set after initialisation
        with the `set_interior_ring` method.
  
    source: optional
        Initialize the properties, data and bounds from those of
        *source*.
 
    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        # Initialise properties and data
        super().__init__(properties=properties, data=data,
                         source=source, copy=copy,
                         _use_data=_use_data)

        # Get bounds, geometry type and interior ring from source
        if source is not None:
            try:
                bounds = source.get_bounds(None)
            except AttributeError:
                bounds = None
                
            try:
                geometry = source.get_geometry(None)
            except AttributeError:
                geometry = None
                
            try:
                interior_ring = source.get_interior_ring(None)
            except AttributeError:
                interior_ring = None
        #--- End: if

        # Initialise bounds
        if bounds is not None:
            if copy or not _use_data:
                bounds = bounds.copy(data=_use_data)
                
            self.set_bounds(bounds, copy=False)

        # Initialise interior ring
        if interior_ring is not None:
            if copy or not _use_data:
                interior_ring = interior_ring.copy(data=_use_data)
                
            self.set_interior_ring(interior_ring, copy=False)
            
        # Initialise the geometry type
        if geometry is not None:
            self.set_geometry(geometry)
    #--- End: def

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def bounds(self):
        '''Return the bounds.

``f.bounds`` is equivalent to ``f.get_bounds()`` 

Note that a `Bounds` instance is returned. Use the `get_array` method
of the `Bounds` instance to return the bounds as a `numpy` array.

.. versionadded:: 1.7

.. seealso:: `data`, `del_bounds`, `get_bounds`, `has_bounds`,
             `set_bounds`

:Returns:

    out: `Bounds`
        The bounds.

**Examples:**

TODO

        '''
        return self.get_bounds()
    #--- End: def

    @property
    def interior_ring(self):
        '''TODO

.. versionadded:: 1.8
        '''
        return self.get_interior_ring()
    #--- End: def

#    # ----------------------------------------------------------------
#    # Methods
#    # ----------------------------------------------------------------
#    def copy(self, data=True):
#        '''Return a deep copy.
#
#``c.copy()`` is equivalent to ``copy.deepcopy(c)``.
#
#`Data` instances contained within are copied with a copy-on-write
#technique. This means that a copy takes up very little extra memory,
#even when the original contains very large data arrays, and the copy
#operation is fast.
#
#.. versionadded:: 1.7
#
#:Parameters:
#
#    data: `bool`, optional
#        If False then do not copy the data, bounds nor interior ring
#        arrays. By default they are copied.
#
#:Returns:
#
#    out:
#        The deep copy.
#
#**Examples:**
#
#>>> g = f.copy()
#>>> g = f.copy(data=False)
#>>> g.has_data()
#False
#>>> g.bounds.has_data()
#False
#
#        '''
#        return super().copy(data=data)
#    #--- End: def

    def del_bounds(self, *default):
        '''Remove the bounds.

.. versionadded:: 1.7

.. seealso:: `del_data`, `get_bounds`, `has_bounds`, `set_bounds`

:Parameters:

    default: optional
        Return *default* if the bounds has not been set.

:Returns:

     out:
        The removed bounds. If the bounds has not been set then the
        *default* is returned, if provided.

**Examples:**

>>> b = cfdm.Bounds(data=cfdm.Data(range(10).reshape(5, 2)))
>>> c.set_bounds(b)
>>> c.has_bounds()
True
>>> c.get_bounds()
<Bounds: (5, 2) >
>>> b = c.del_bounds()
>>> b
<Bounds: (5, 2) >
>>> c.has_bounds()
False
>>> print(c.get_bounds(None))
None
>>> print(c.del_bounds(None))
None

        '''
        return self._del_component('bounds', *default)
    #--- End: def

    def del_geometry(self, *default):
        '''Delete the geometry type. TODO

.. versionadd:: 1.8

.. seealso:: `get_geometry`, `has_geometry`, `set_geometry`

:Parameters:

    default: optional
        Return *default* if the geometry type has not been set.

:Returns:

     out:

        The removed geometry type. If the geometry type has not been
        set then the *default* is returned, if provided.

**Examples:**

        '''
        return self._del_component('geometry', *default)
    #--- End: def

    def get_bounds(self, *default):
        '''Return the bounds.

.. versionadd:: 1.7

.. seealso:: `get_array`, `get_data`, `has_bounds`, `set_bounds`

:Parameters:

    default: optional
        Return *default* if and only if the bounds have not been set.

:Returns:

    out:
        The bounds. If the bounds have not been set, then return the
        value of *default* parameter if provided.

**Examples:**

>>> b = cfdm.Bounds(data=cfdm.Data(range(10).reshape(5, 2)))
>>> c.set_bounds(b)
>>> c.has_bounds()
True
>>> c.get_bounds()
<Bounds: (5, 2) >
>>> b = c.del_bounds()
>>> b
<Bounds: (5, 2) >
>>> c.has_bounds()
False
>>> print(c.get_bounds(None))
None
>>> print(c.del_bounds(None))
None

        '''
        bounds = self._get_component('bounds', None)
        if bounds is None:
            return self._get_component('bounds', *default)

        properties = self.properties()
        bounds_properties = bounds.properties()

        inherited_properties = {}
        for prop, value in properties.items():
            if prop not in bounds_properties:
                inherited_properties[prop] = value
        #--- End: for
        
        bounds._set_component('inherited_properties', inherited_properties)
        
        return bounds
    #--- End: def

    def get_geometry(self, *default):
        '''Return the geometry type.

.. versionadded:: 1.8

.. seealso:: `get_array`, `get_data`, `has_bounds`, `set_bounds`

:Parameters:

    default: optional
        Return *default* if and only if the bounds have not been set.

:Returns:

    out:

**Examples:**

        '''
        return self._get_component('geometry', *default)
    #--- End: def

    def get_interior_ring(self, *default):
        '''Return the interior_ring.

.. versionadded:: 1.8

.. seealso:: `del_interior_ring`, `get_bounds`, `has_interior_ring`,
             `set_interior_ring`

:Parameters:

    default: optional
        Return *default* if and only if the HHHh have not been set.

:Returns:

    out:
    
**Examples:**

>>> i = c.get_interior_ring()
        '''
        return self._get_component('interior_ring', *default)
    #--- End: def

    def has_bounds(self):
        '''Whether or not there are bounds.
        
.. versionadded:: 1.7

.. seealso:: `del_bounds`, `get_bounds`, `has_data`, `set_bounds`

:Returns:

    out: `bool`
        True if there are bounds, otherwise False.

**Examples:**

>>> b = cfdm.Bounds(data=cfdm.Data(range(10).reshape(5, 2)))
>>> c.set_bounds(b)
>>> c.has_bounds()
True
>>> c.get_bounds()
<Bounds: (5, 2) >
>>> b = c.del_bounds()
>>> b
<Bounds: (5, 2) >
>>> c.has_bounds()
False
>>> print(c.get_bounds(None))
None
>>> print(c.del_bounds(None))
None

        '''
        return self._has_component('bounds')
    #--- End: def

    def has_geometry(self):
        '''True if there is a goemetry type. TODO
        
.. versionadded:: 1.8

.. seealso:: `del_bounds`, `get_bounds`, `has_data`, `set_bounds`

:Returns:

    out: `bool`

**Examples:**

>>> x = c.has_geometry()

        '''
        return self._has_component('geometry')
    #--- End: def

    def has_interior_ring(self):
        '''True if there are interior_ring. TODO
        
.. versionadded:: 1.8

.. seealso:: `del_interior_ring`, `get_interior_ring`, `has_data`, `set_interior_ring`

:Returns:

    out: `bool`
        True if there are interior_ring, otherwise False.

**Examples:**

>>> x = f.has_interior_ring()
>>> if c.has_interior_ring():
...     print 'Has interior_ring'

        '''
        return self._has_component('interior_ring')
    #--- End: def

    def set_bounds(self, bounds, copy=True):
        '''Set the bounds.

.. versionadded:: 1.7

.. seealso: `del_bounds`, `get_bounds`, `has_bounds`, `set_data`

:Parameters:

    data: `Bounds`
        The bounds to be inserted.

    copy: `bool`, optional
        If False then do not copy the bounds prior to insertion. By
        default the bounds are copied.

:Returns:

    `None`

**Examples:**

>>> b = cfdm.Bounds(data=cfdm.Data(range(10).reshape(5, 2)))
>>> c.set_bounds(b)
>>> c.has_bounds()
True
>>> c.get_bounds()
<Bounds: (5, 2) >
>>> b = c.del_bounds()
>>> b
<Bounds: (5, 2) >
>>> c.has_bounds()
False
>>> print(c.get_bounds(None))
None
>>> print(c.del_bounds(None))
None

        '''
        if copy:
            bounds = bounds.copy()

        self._set_component('bounds', bounds, copy=False)
    #--- End: def

    def set_geometry(self, value, copy=True):
        '''Set the geometry type.

.. versionadded:: 1.8

.. seealso: `del_bounds`, `get_bounds`, `has_bounds`, `set_data`

:Parameters:

    value: `str`

:Returns:

    `None`

**Examples:**
        '''
        self._set_component('geometry', value, copy=copy)
    #--- End: def

    def set_interior_ring(self, interior_ring, copy=True):
        '''Set the interior_ring.

.. versionadded:: 1.8

.. seealso: `del_interior_ring`, `get_interior_ring`,
            `has_interior_ring`

:Parameters:

    interior_ring: `InteriorRing`
        The interior_ring to be inserted.

    copy: `bool`, optional
        If False then do not copy the interior_ring prior to insertion. By
        default the interior_ring are copied.

:Returns:

    `None`

**Examples:**

>>> c.set_interior_ring(b)
        '''
        if copy:
            interior_ring = interior_ring.copy()

        self._set_component('interior_ring', interior_ring, copy=False)
    #--- End: def

#--- End: class
