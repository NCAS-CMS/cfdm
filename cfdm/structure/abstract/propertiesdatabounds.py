from future.utils import with_metaclass

import abc

from copy import deepcopy

#import mixin

from .propertiesdata import PropertiesData



class PropertiesDataBounds(with_metaclass(abc.ABCMeta, PropertiesData)):
    '''Abstract base class for a data array with bounds and with
descriptive properties.

    '''
    
    def __init__(self, properties={}, data=None, bounds=None,
                 geometry_type=None, interior_ring=None, source=None,
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
  
    source: optional
        Override the *properties*, *data* and *bounds* parameters with
        ``source.properties()``, ``source.get_data()`` and
        ``source.get_bounds()`` respectively.

        If *source* does not have one of these methods, or it can not
        return anything, then that parameter is not set.
        
    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        # Initialise properties and data
        super(PropertiesDataBounds, self).__init__(
            properties=properties,
            data=data,
            source=source,
            copy=copy,
            _use_data=_use_data)

        # Get bounds, geometry type and interior ring from source
        if source is not None:
            try:
                bounds = source.get_bounds(None)
            except AttributeError:
                bounds = None
                
            try:
                geometry_type = source.get_geometry_type(None)
            except AttributeError:
                geometry_type = None
                
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

        # Initialise the geometry type
        if geometry_type is not None:
            self.set_geometry_type(geometry_type)

        # Initialise interior ring
        if interior_ring is not None:
            if copy or not _use_data:
                interior_ring = interior_ring.copy(data=_use_data)
                
            self.set_interior_ring(interior_ring, copy=False)
    #--- End: def

    @property
    def bounds(self):
        '''
        '''
        return self.get_bounds()
    #--- End: def

    def copy(self, data=True):
        '''Return a deep copy.

``c.copy()`` is equivalent to ``copy.deepcopy(c)``.

:Examples 1:

>>> d = c.copy()

:Parameters:

    data: `bool`, optional
        If False then do not copy the data nor bounds. By default the
        data and bounds are copied.

:Returns:

    out:
        The deep copy.

:Examples 2:

>>> d = c.copy(data=False)

        '''
        return super(PropertiesDataBounds, self).copy(data=data)
    #--- End: def

    def del_bounds(self):
        '''Delete the bounds.

.. seealso:: `del_data`, `get_bounds`, `has_bounds`, `set_bounds`

:Examples 1:

>>> c.del_bounds()

:Returns: 

    out: `Bounds` or `None`
        The removed bounds, or `None` if the data was not set.

:Examples 2:

>>> c.has_bounds()
True
>>> print c.get_bounds()

>>> d = c.del_bounds()
>>> print d

>>> c.has_bounds()
False
>>> print c.del_bounds()
None

        '''
        return self._del_component('bounds')
    #--- End: def

    def del_bounds(self):
        '''Delete the bounds type.

.. seealso:: `del_data`, `get_bounds`, `has_bounds`, `set_bounds`

:Examples 1:

:Returns: 

    out: `str` or `None`

:Examples 2:

        '''
        return self._del_component('geometry_type')
    #--- End: def

    def get_bounds(self, *default):
        '''Return the bounds.

.. seealso:: `get_array`, `get_data`, `has_bounds`, `set_bounds`

:Examples 1:

>>> b = c.get_bounds()

:Parameters:

    default: optional
        Return *default* if and only if the bounds have not been set.

:Returns:

    out:
        The bounds. If the bounds have not been set, then return the
        value of *default* parameter if provided.

:Examples 2:

>>> b = c.del_bounds()
>>> c.get_bounds('No bounds')
'No bounds'

        '''
        return self._get_component('bounds', None, *default)
    #--- End: def

    def get_geometry_type(self, *default):
        '''Return the bounds type.

.. seealso:: `get_array`, `get_data`, `has_bounds`, `set_bounds`

:Examples 1:

:Parameters:

    default: optional
        Return *default* if and only if the bounds have not been set.

:Returns:

    out:

:Examples 2:

        '''
        return self._get_component('geometry_type', None, *default)
    #--- End: def

    def get_interior_ring(self, *default):
        '''Return the interior_ring.

.. seealso:: `del_interior_ring`, `get_bounds`, `has_interior_ring`,
             `set_interior_ring`

:Examples 1:

>>> i = c.get_interior_ring()

:Parameters:

    default: optional
        Return *default* if and only if the HHHh have not been set.

:Returns:

    out:
    
:Examples 2:

        '''
        return self._get_component('interior_ring', None, *default)
    #--- End: def

    def has_bounds(self):
        '''True if there are bounds.
        
.. seealso:: `del_bounds`, `get_bounds`, `has_data`, `set_bounds`

:Examples 1:

>>> x = f.has_bounds()

:Returns:

    out: `bool`
        True if there are bounds, otherwise False.

:Examples 2:

>>> if c.has_bounds():
...     print 'Has bounds'

        '''
        return self._has_component('bounds')
    #--- End: def

    def has_geometry_type(self):
        '''True if there is a bounds type.
        
.. seealso:: `del_bounds`, `get_bounds`, `has_data`, `set_bounds`

:Examples 1:

>>> x = f.has_geometry_type()

:Returns:

    out: `bool`

:Examples 2:

        '''
        return self._has_component('geometry_type')
    #--- End: def

    def has_interior_ring(self):
        '''True if there are interior_ring.
        
.. seealso:: `del_interior_ring`, `get_interior_ring`, `has_data`, `set_interior_ring`

:Examples 1:

>>> x = f.has_interior_ring()

:Returns:

    out: `bool`
        True if there are interior_ring, otherwise False.

:Examples 2:

>>> if c.has_interior_ring():
...     print 'Has interior_ring'

        '''
        return self._has_component('interior_ring')
    #--- End: def

    def set_bounds(self, bounds, copy=True):
        '''Set the bounds.

.. seealso: `del_bounds`, `get_bounds`, `has_bounds`, `set_data`

:Examples 1:

>>> c.set_bounds(b)

:Parameters:

    data: `Bounds`
        The bounds to be inserted.

    copy: `bool`, optional
        If False then do not copy the bounds prior to insertion. By
        default the bounds are copied.

:Returns:

    `None`

:Examples 2:

>>> c.set_data(b, copy=False)

        '''
        if copy:
            bounds = bounds.copy()

        self._set_component('bounds', None, bounds)
    #--- End: def

    def set_geometry_type(self, value):
        '''Set the bounds type.

.. seealso: `del_bounds`, `get_bounds`, `has_bounds`, `set_data`

:Examples 1:

:Parameters:

    value: `str`

:Returns:

    `None`

:Examples 2:
        '''
        self._set_component('geometry_type', None, value)
        print ('in pdb.set_geometry_type:', self.get_geometry_type(), self)
    #--- End: def

    def set_interior_ring(self, interior_ring, copy=True):
        '''Set the interior_ring.

.. seealso: `del_interior_ring`, `get_interior_ring`,
            `has_interior_ring`

:Examples 1:

>>> c.set_interior_ring(b)

:Parameters:

    interior_ring: `InteriorRing`
        The interior_ring to be inserted.

    copy: `bool`, optional
        If False then do not copy the interior_ring prior to insertion. By
        default the interior_ring are copied.

:Returns:

    `None`

:Examples 2:

        '''
        if copy:
            interior_ring = interior_ring.copy()

        self._set_component('interior_ring', None, interior_ring)
    #--- End: def

#--- End: class
