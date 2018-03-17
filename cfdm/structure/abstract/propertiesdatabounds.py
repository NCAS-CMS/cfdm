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
                 extent_parameters={}, extent_arrays={},
                 topology_parameters={}, topology_arrays={},
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


        if source is not None and isinstance(source, PropertiesDataBounds):
            if bounds is None:
                bounds = source.get_bounds(None)
                    
#1.8            if not extent_arrays:
#1.8                extent_arrays = source.extent_arrays()
#1.8            else:
#1.8                extent_arrays = extent_arrays.copy()
#1.8                extent_arrays.update(source.extent_arrays())
                                         
            if not extent_parameters:
                extent_parameters = source.extent_parameters()
            else:
                extent_parameters = extent_parameters.copy()
                extent_parameters.update(source.extent_parameters())
                                         
#1.8            if not topology_arrays:
#1.8                topology_arrays = source.topology_arrays()
#1.8            else:
#1.8                topology_arrays = topology_arrays.copy()
#1.8                topology_arrays.update(source.topology_arrays())
#1.8
#1.8            if not topology_parameters:
#1.8                topology_parameters = source.topology_parameters()
#1.8            else:
#1.8                topology_parameters = topology_parameters.copy()
#1.8                topology_parameters.update(source.topology_parameters())
        #--- End: if

        if bounds is not None:
            if copy or not _use_data:
                bounds = bounds.copy(data=_use_data)
                
            self.set_bounds(bounds, copy=False)
        #--- End: if
        
        if extent_parameters:
            if copy:
                extent_parameters = deepcopy(extent_parameters)
            else:
                extent_parameters = extent_parameters.copy()
        #--- End: if
        
#1.8        if topology_parameters:
#1.8            if copy:
#1.8                topology_parameters = deepcopy(topology_parameters)
#1.8            else:
#1.8                topology_parameters = topology_parameters.copy()
#1.8
#1.8        if extent_arrays:
#1.8            extent_arrays = extent_arrays.copy()
#1.8            if copy or not _use_data:
#1.8                for key, value in extent_arrays.items():
#1.8                    extent_arrays[key] = value.copy(data=_use_data)
#1.8
#1.8        if topology_arrays:
#1.8            topology_arrays = topology_arrays.copy()
#1.8            if copy or not _use_data:
#1.8                for key, value in topology_arrays.items():
#1.8                    topology_arrays[key] = value.copy(data=_use_data)
        
        self._set_component(3, 'extent_parameters', None, extent_parameters)
#1.8        self._set_component(3, 'topology_parameters', None, topology_parameters)
#1.8
#1.8        self._set_component(3, 'extent_arrays', None, extent_arrays)
#1.8        self._set_component(3, 'topology_arrays', None, topology_arrays)
    #--- End: def

    def del_bounds(self):
        '''Remove cell bounds.

.. versionadded:: 1.6

.. seealso , `insert_bounds`, `insert_data`, `remove_data`

:Returns:

    out: `None` or `Bounds`

        '''
        return self._del_component(3, 'bounds')
    #--- End: def

#1.8    def del_extent_array(self, name):
#1.8        '''
#1.8        '''
#1.8        return self._component(3, 'extent_arrays', name)
#1.8    #--- End: def

    def del_extent_parameter(self, name):
        '''
        '''
        return self._del_component(3, 'extent_parameters', name)
    #--- End: def

#1.8    def del_topology_parameter(self, name):
#1.8        '''
#1.8        '''
#1.8        return self._del_component(3, 'topology_parameters', name)
#1.8    #--- End: def
#1.8
#1.8    def del_topology_array(self, name):
#1.8        '''
#1.8        '''
#1.8        return self._del_component(3, 'topology_arrays', name)
#1.8    #--- End: def
#1.8
#1.8    def extent_arrays(self):
#1.8        '''
#1.8        '''
#1.8        return self._get_component(3, 'extent_arrays', None, {}).copy()
#1.8    #--- End: def
       
    def extent_parameters(self):
        '''
        '''
        return self._get_component(3, 'extent_parameters', None, {}).copy()
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
        return self._get_component(3, 'bounds', None, *default)
    #--- End: def

#1.8    def get_extent_array(self, array, *default):
#1.8        '''
#1.8        '''
#1.8        return self._get_component(3, 'extent_arrays', array, *default)
#1.8    #--- End: def

    def get_extent_parameter(self, parameter, *default):
        '''
        '''
        return self._get_component(3, 'extent_parameters', parameter, *default)
    #--- End: def

#1.8    def get_topology_array(self, name, *default):
#1.8        '''
#1.8        '''
#1.8        return self._get_component(3, 'topology_arrays', name, *default)
#1.8    #--- End: def
#1.8
#1.8    def get_topology_parameter(self, name, *default):
#1.8        '''
#1.8        '''
#1.8        return self._get_component(3, 'topology_parameters', name, *default)
#1.8    #--- End: def

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
        return self._has_component(3, 'bounds')
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

        self._set_component(3, 'bounds', None, bounds)
    #--- End: def

#1.8    def set_extent_array(self, name, value, copy=True):
#1.8        '''
#1.8        '''
#1.8        if copy:
#1.8            value = value.copy()
#1.8
#1.8        self._set_component(3, 'extent_arrays', name, value)
#1.8    #--- End: def

    def set_extent_parameter(self, parameter, value, copy=True):
        '''
        '''
        if copy:
            value = deepcopy(value)

        self._set_component(3, 'extent_parameters', parameter, value)
    #--- End: def

#1.8    def set_topology_array(self, name, value, copy=True):
#1.8        '''
#1.8        '''
#1.8        if copy:
#1.8            value = value.copy()
#1.8
#1.8        return self._set_component(3, 'topology_arrays', name, value)
#1.8    #--- End: def
#1.8
#1.8
#1.8    def set_topology_parameter(self, name, value, copy=True):
#1.8        '''
#1.8        '''
#1.8        if copy:
#1.8            value = deepcopy(value)
#1.8
#1.8        return self._set_component(3, 'topology_parameters', name, value)
#1.8    #--- End: def
#1.8
#1.8    
#1.8    def topology_arrays(self):
#1.8        '''
#1.8        '''
#1.8        return self._get_component(3, 'topology_arrays', None, {}).copy()
#1.8    #--- End: def
#1.8    
#1.8    def topology_parameters(self):
#1.8        '''
#1.8        '''
#1.8        return self._get_component(3, 'topology_parameters', None, {}).copy()
#1.8    #--- End: def

#--- End: class
