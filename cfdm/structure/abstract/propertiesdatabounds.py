import abc

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
                    
            if not extent_arrays:
                extent_arrays = source.extent_arrays()
            else:
                extent_arrays = extent_arrays.copy()
                extent_arrays.update(source.extent_arrays())
                                         
            if not extent_parameters:
                extent_parameters = source.extent_parameters()
            else:
                extent_parameters = extent_parameters.copy()
                extent_parameters.update(source.extent_parameters())
                                         
            if not topology_arrays:
                topology_arrays = source.topology_arrays()
            else:
                topology_arrays = topology_arrays.copy()
                topology_arrays.update(source.topology_arrays())

            if not topology_parameters:
                topology_parameters = source.topology_parameters()
            else:
                topology_parameters = topology_parameters.copy()
                topology_parameters.update(source.topology_parameters())
        #--- End: if

        if bounds is not None:
            if copy or not _use_data:
                bounds = bounds.copy(data=_use_data)
                
            self.set_bounds(bounds, copy=False)

        extent_parameters = extent_parameters.copy()
        if extent_parameters and copy:
            for key, value in extent_parameters.items():
                extent_arrays[key] = deepcopy(value)
        #--- End: if                

        topology_parameters = topology_parameters.copy()
        if topology_parameters and copy:
            for key, value in topology_parameters.items():
                topology_arrays[key] = deepcopy(value)
        #--- End: if                

        extent_arrays = extent_arrays.copy()
        if extent_arrays  and(copy or not _use_data):
            for key, value in extent_arrays.items():
                extent_arrays[key] = value.copy(data=_use_data)
        #--- End: if                

        topology_arrays = topology_arrays.copy()
        if topology_arrays and (copy or not _use_data):
            for key, value in topology_arrays.items():
                topology_arrays[key] = value.copy(data=_use_data)
        #--- End: if                

        self._set_attribute('extent_arrays', extent_arrays)
        self._set_attribute('extent_parameters', extent_parameters)
        self._set_attribute('topology_arrays', topology_arrays)
        self._set_attribute('topology_parameters', topology_parameters)
    #--- End: def

    def del_bounds(self):
        '''Remove cell bounds.

.. versionadded:: 1.6

.. seealso , `insert_bounds`, `insert_data`, `remove_data`

:Returns:

    out: `None` or `Bounds`

        '''
        return self._del_attribute('bounds')
    #--- End: def

    def del_extent_array(self, name):
        '''
        '''
        return self._del_attribute_term('extent_arrays', name)
    #--- End: def

    def del_extent_parameter(self, name):
        '''
        '''
        return self._del_attribute_term('extent_parameters', name)
    #--- End: def

    def del_topology_parameter(self, name):
        '''
        '''
        return self._del_attribute_term('topology_parameters', name)
    #--- End: def

    def del_topology_array(self, name):
        '''
        '''
        return self._del_attribute_term('topology_arrays', name)
    #--- End: def

    def extent_arrays(self):
        '''
        '''
        return self._get_attribute('extent_arrays', {}).copy()
    #--- End: def
       
    def extent_parameters(self):
        '''
        '''
        return self._get_attribute('extent_parameters', {}).copy()
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
        return self._get_attribute('bounds', *default)
    #--- End: def

    def get_extent_array(self, array, *default):
        '''
        '''
        return self._get_attribute_term('extent_arrays', array, *default)
    #--- End: def

    def get_extent_parameter(self, parameter, *default):
        '''
        '''
        return self._get_attribute_term('extent_parameters', parameter, *default)
    #--- End: def

        self._get_parameters('extent')[name] = value
    #--- End: def
    
    def get_topology_array(self, name, *default):
        '''
        '''
        return self._get_attribute_term('topology_arrays', name, *default)
    #--- End: def

    def get_topology_parameter(self, name, *default):
        '''
        '''
        return self._get_attribute_term('topology_parameters', name, *default)
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
        return self._has_attribute('bounds')
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

        self._set_attribute('bounds', bounds)
    #--- End: def

    def set_extent_array(self, name, value, copy=True):
        '''
        '''
        if copy:
            value = value.copy()

        self._set_attribute_term('extent_arrays', name, value)
    #--- End: def

    def set_extent_parameter(self, parameter, value, copy=True):
        '''
        '''
        if copy:
            value = deepcopy(value)

        self._set_attribute_term('extent_parameters', parameter, value)
    #--- End: def

    def set_topology_array(self, name, value, copy=True):
        '''
        '''
        if copy:
            value = value.copy()

        return self._set_attribute_term('topology_arrays', name, value)
    #--- End: def


    def set_topology_parameter(self, name, value, copy=True):
        '''
        '''
        if copy:
            value = deepcopy(value)

        return self._set_attribute_term('topology_parameters', name, value)
    #--- End: def

    
    def topology_arrays(self):
        '''
        '''
        return self._get_attribute('topology_arrays', {}).copy()
    #--- End: def
    

    def topology_parameters(self):
        '''
        '''
        return self._get_attribute('topology_parameters', {}).copy()
    #--- End: def

#--- End: class
