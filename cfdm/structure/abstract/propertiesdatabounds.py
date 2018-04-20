import abc

from copy import deepcopy

from .propertiesdata import PropertiesData


# ====================================================================
#
# CFDM
#
# ====================================================================

class PropertiesDataBounds(PropertiesData):
    '''Base class for CFDM dimension coordinate, auxiliary coordinate and
domain ancillary objects.

    '''
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, properties={}, data=None, bounds=None,
                 extent_parameters=None,
#                 extent_arrays=None,
#                 topology_parameters=None,
#                 topology_arrays=None,
                 source=None, copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Initialize a new instance with CF properties from a
        dictionary's key/value pairs.
  
    data: `Data`, optional
        Provide the new instance with an N-dimensional data array.
  
    bounds: `Data` or `Bounds`, optional
        Provide the new instance with cell bounds.
  
    source: `Variable`, optional
        Take the attributes, CF properties and data array from the
        source object. Any attributes, CF properties or data array
        specified with other parameters are set after initialisation
        from the source instance.
  
    copy: `bool`, optional
        If False then do not copy arguments prior to
        initialization. By default arguments are deep copied.
  
        '''
        # Set properties and data
        super(PropertiesDataBounds, self).__init__(
            properties=properties,
            data=data,
            source=source,
            copy=copy,
            _use_data=_use_data)

        if source is not None:
            try:
                bounds = source.get_bounds(None)
            except AttributeError:
                bounds = None
                
            try:
                extent_parameters = source.extent_parameters()
            except AttributeError:
                extent_parameters = None

#            try:
#                extent_arrays = source.extent_arrays()
#            except AttributeError:
#                extent_arrays = None
        #--- End: if

        if bounds is not None:
            if copy or not _use_data:
                bounds = bounds.copy(data=_use_data)
                
            self.set_bounds(bounds, copy=False)

        if extent_parameters:
            if copy:
                extent_parameters = deepcopy(extent_parameters)
        else:
            extent_parameters = {}
            
#        if extent_arrays:
#            if copy or not _use_data:
#                extent_arrays = extent_arrays.copy()
#                for key, value in extent_arrays.iteritems():
#                    extent_arrays[key] = value.copy(data=_use_data)


        self.extent_parameters(extent_parameters, copy=False)
#        self.extent_arrays(extent_arrays, copy=False)
    #--- End: def

    def del_bounds(self):
        '''Remove cell bounds.

.. versionadded:: 1.6

.. seealso , `insert_bounds`, `insert_data`, `remove_data`

:Returns:

    out: `None` or `Bounds`

        '''
        return self._del_component('bounds')
    #--- End: def

    def del_extent_array(self, name):
        '''
        '''
        return self._component('extent_arrays', name)
    #--- End: def

    def del_extent_parameter(self, name):
        '''
        '''
        return self._del_component('extent_parameters', name)
    #--- End: def

    def del_topology_parameter(self, name):
        '''
        '''
        return self._del_component('topology_parameters', name)
    #--- End: def

    def del_topology_array(self, name):
        '''
        '''
        return self._del_component('topology_arrays', name)
    #--- End: def

#    def extent_arrays(self):
#        '''
#        '''
#        return self._get_component('extent_arrays', None, {}).copy()
#    #--- End: def
#      
#    def extent_parameters(self):
#        '''
#        '''
#        return self._get_component('extent_parameters', None, {}).copy()
#    #--- End: def

    def extent_arrays(self, extent_arrays=None, copy=True):
        '''Return or replace the identifiers of the coordinate objects that
define the coordinate system.

.. versionadded:: 1.6

.. seealso:: `del_coordinate`

:Examples 1:

>>> extent_arrays = c.extent_arrays()

:Returns:

    out: `set`
        The identifiers of the coordinate objects.

:Examples 2:

>>> c.extent_arrays()
{}

        '''
        existing = self._get_component('extent_arrays', None, None)

        if existing is None:
            existing = {}
            self._set_component('extent_arrays', None, existing)

        out = existing.copy()

        if not extent_arrays:
            return out

        # Still here?
        if copy:
            extent_arrays = extent_arrays.copy()
            for key, value in extent_arrays.iteritems():                
                extent_arrays[key] = value.copy()
        #--- End: if
        
        # Still here?
        existing.clear()
        existing.update(extent_arrays)

        return out
    #--- End: def
            
    def extent_parameters(self, extent_parameters=None, copy=True):
        '''Return or replace the identifiers of the coordinate objects that
define the coordinate system.

.. versionadded:: 1.6

.. seealso:: `del_coordinate`

:Examples 1:

>>> extent_parameters = c.extent_parameters()

:Returns:

    out: `set`
        The identifiers of the coordinate objects.

:Examples 2:

>>> c.extent_parameters()
{}

        '''
        existing = self._get_component('extent_parameters', None, None)

        if existing is None:
            existing = {}
            self._set_component('extent_parameters', None, existing)

        out = existing.copy()

        if not extent_parameters:
            return out

        # Still here?
        if copy:
            extent_parameters = deepcopy(extent_parameters)

        # Still here?
        existing.clear()
        existing.update(extent_parameters)

        return out
    #--- End: def
            
    def get_bounds(self, *default):
        '''Insert cell bounds.

.. versionadded:: 1.6

.. seealso , `insert_data`, `remove_bounds`, `remove_data`

:Parameters:

    bounds: `Bounds`

    copy: `bool`, optional

:Returns:

    `None`

        '''
        return self._get_component('bounds', None, *default)
    #--- End: def

    def get_extent_array(self, array, *default):
        '''
        '''
        return self._get_component('extent_arrays', array, *default)
    #--- End: def

    def get_extent_parameter(self, parameter, *default):
        '''
        '''
        return self._get_component('extent_parameters', parameter, *default)
    #--- End: def
    
    def get_topology_array(self, name, *default):
        '''
        '''
        return self._get_component('topology_arrays', name, *default)
    #--- End: def

    def get_topology_parameter(self, name, *default):
        '''
        '''
        return self._get_component('topology_parameters', name, *default)
    #--- End: def

    def has_bounds(self):
        '''Insert cell bounds.

.. versionadded:: 1.6

.. seealso , `insert_data`, `remove_bounds`, `remove_data`

:Parameters:

    bounds: `Bounds`

    copy: `bool`, optional

:Returns:

    `None`

        '''
        return self._has_component('bounds')
    #--- End: def

    def set_bounds(self, bounds, copy=True):
        '''Insert cell bounds.

.. versionadded:: 1.6

.. seealso , `insert_data`, `remove_bounds`, `remove_data`

:Parameters:

    bounds: `Bounds`

    copy: `bool`, optional

:Returns:

    `None`

        '''
        if copy:
            bounds = bounds.copy()

        self._set_component('bounds', None, bounds)
    #--- End: def

    def set_extent_array(self, name, value, copy=True):
        '''
        '''
        if copy:
            value = value.copy()

        self._set_component('extent_arrays', name, value)
    #--- End: def

    def set_extent_parameter(self, parameter, value, copy=True):
        '''
        '''
        if copy:
            value = deepcopy(value)

        self._set_component('extent_parameters', parameter, value)
    #--- End: def

    def set_topology_array(self, name, value, copy=True):
        '''
        '''
        if copy:
            value = value.copy()

        return self._set_component('topology_arrays', name, value)
    #--- End: def


    def set_topology_parameter(self, name, value, copy=True):
        '''
        '''
        if copy:
            value = deepcopy(value)

        return self._set_component('topology_parameters', name, value)
    #--- End: def

    
    def topology_arrays(self):
        '''
        '''
        return self._get_component('topology_arrays', None, {}).copy()
    #--- End: def
    

    def topology_parameters(self):
        '''
        '''
        return self._get_component('topology_parameters', None, {}).copy()
    #--- End: def

#--- End: class
