from collections import abc

from .propertiesdata import PropertiesData

# ====================================================================
#
# CFDM Bounded variable object
#
# ====================================================================

class BoundedPropertiesData(PropertiesData):
    '''Base class for CFDM dimension coordinate, auxiliary coordinate and
domain ancillary objects.

    '''
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, properties={}, data=None, source=None,
                 bounds=None, ancillary_parameters=None,
                 ancillary_arrays=None, copy=True, _use_data=True):
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
        super(AbstractBoundedArray, self).__init__(
            properties=properties,
            data=data,
            source=source,
            copy=copy,
            _use_data=_use_data)

        # Set bounds and ancillary parameters and properties
        self._parameters = {'extent': {}, 'topology': {}}
        self._arrays     = {'extent': {}, 'topology': {}}
        
        self.invalid_parameters = {'extent': {}, 'topology': {}}
        self.invalid_arrays     = {'extent': {}, 'topology': {}}
        self.invalid_           = {'extent': {}, 'topology': {}}
        
        if source is not None and isinstance(source, AbstractBoundedArray):
            if bounds is None and source.has_bounds():
                bounds = source.bounds
                    
            source_ancillary_arrays = source.ancillary_arrays()
            if ancillary_arrays is None and source_ancillary_arrays):
                ancillary_arrays = source_ancillary_arrays
                
            source_ancillary_parameters = source.ancillary_parameters()
            if ancillary_parameters is None and source_ancillary_parameters:
                ancillary_parameters = source_ancillary_parameters
        #--- End: if

        self.invalid_bounds = False
        if bounds is not None:
            if not _use_data:
                bounds = bounds.copy(data=False)
                copy = False
                
            self.set_bounds(bounds, copy=copy)
        else:
            self._bounds = None
            
        if ancillary_arrays:
            for name, array in ancillary_arrays.iteritems():
                if not _use_data:
                    array = array.copy(data=False)
                    copy = False
                    
                self.set_ancillary_array(name, array, copy=copy)
    
        if ancillary_parameters:
            for name, parameter in ancillary_parameters.iteritems():
                if copy:
                    parameter = deepcopy(parameter)
                    
                self.set_ancillary_parameter(name, parameter)

        if extent_properties:
            for name, parameter in extent_properties.iteritems():
                if copy:
                    parameter = deepcopy(parameter)
                    
                self.set_extent_property(name, parameter, copy=True)
    #--- End: def


    def _get_parameters(self, parameter_type):
        '''
        '''
        return self._parameters[parameter_type]
    #--- End: def

    def _get_arrays(self, array_type):
        '''
        '''
        return self._arrays[array_type]
    #--- End: def

    def ancillary_parameters(self):
        '''
        '''
        out = {}
        for key, value in self._parameters.iteritems():
            out.update(value.copy()) 

        return out
    #--- End: def

    def ancillary_arrays(self):
        '''
        '''
        out = {}
        for key, value in self._arrays.iteritems():
            out.update(value.copy()) 

        return out
    #--- End: def

    def extent_parameters(self):
        '''
        '''
        return self._get_parameters('extent').copy()
    #--- End: def

    def extent_arrays(self):
        '''
        '''
        return self._get_arrays('extent').copy()
    #--- End: def

    def get_extent_parameter(self, name, *default):
        '''
        '''
        d = self._get_parameters('extent')
        if default:
            return d.get(name, default[0])

        try:
            return d[name]
        except KeyError:
            raise AttributeError("acj s;do8h po;iln 1")
    #--- End: def

        self._get_parameters('extent')[name] = value
    #--- End: def
    
    def get_extent_array(self, name, *default):
        '''
        '''
        d = self._get_arrays('extent')
        if default:
            return d.get(name, default[0])

        try:
            return d[name]
        except KeyError:
            raise AttributeError("acj s;do8h po;iln 2")
    #--- End: def

    def set_extent_parameter(self, name, value):
        '''
        '''
        self._get_parameters('extent')[name] = value
    #--- End: def
    
    def set_extent_array(self, name, value, copy=True):
        '''
        '''
        if copy:
            array = array.copy()
            
        self._get_arrays('extent')[name] = value
    #--- End: def
    
    def del_extent_parameter(self, name):
        '''
        '''
        return self._get_parameters('extent').pop(name, None)
    #--- End: def

    def del_extent_array(self, name):
        '''
        '''
        return self._get_arrays('extent').pop(name, None)
    #--- End: def

    def topology_parameters(self):
        '''
        '''
        return self._get_parameters('topology').copy()
    #--- End: def

    def topology_arrays(self):
        '''
        '''
        return self._get_arrays('topology').copy()
    #--- End: def

    def get_topology_parameter(self, name, *default):
        '''
        '''
        d = self._get_parameters('topology')
        if default:
            return d.get(name, default[0])

        try:
            return d[name]
        except KeyError:
            raise AttributeError("acj s;do8h po;iln 3")
    #--- End: def

        self._parameters('extent')[name] = value
    #--- End: def
    
    def get_topology_array(self, name, *default):
        '''
        '''
        d = self._get_arrays('topology')
        if default:
            return d.get(name, default[0])

        try:
            return d[name]
        except KeyError:
            raise AttributeError("acj s;do8h po;iln 4")
    #--- End: def

    def set_topology_parameter(self, name, value):
        '''
        '''
        self._get_parameters('topology')[name] = value
    #--- End: def
    
    def set_topology_array(self, name, value, copy=True):
        '''
        '''
        if copy:
            array = array.copy()
            
        self._get_arrays('topology')[name] = value
    #--- End: def
    
    def del_topology_parameter(self, name):
        '''
        '''
        return self._get_parameters('topology').pop(name, None)
    #--- End: def

    def del_topology_array(self, name):
        '''
        '''
        return self._get_arrays('topology').pop(name, None)
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
        bounds = self._bounds
        if bounds is None:
            if default:
                return default[0]

            raise AttributeError("bounds aascas 34r34 5iln ")

        return bounds
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
        if isinstance(bounds, Bounds):
            if copy:
                bounds = bounds.copy(data=data)    
        else:
            self.invalid_bounds = True

        self._bounds = bounds        
    #--- End: def

    def del_bounds(self):
        '''Remove cell bounds.

.. versionadded:: 1.6

.. seealso , `insert_bounds`, `insert_data`, `remove_data`

:Returns:

    out: `None` or `Bounds`

        '''
        bounds = self._bounds
        if bounds is None:
            return

        self._bounds = None
        return bounds
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
        return self._bounds is not None
    #--- End: def
    
#--- End: class
