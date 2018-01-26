from collections import abc

from .arrayconstruct import AbstractVariable

# ====================================================================
#
# CFDM Bounded variable object
#
# ====================================================================

class AbstractBoundedVariable(AbstractVariable):
    '''Base class for CFDM dimension coordinate, auxiliary coordinate and
domain ancillary objects.

    '''

    __metaclass__ = abc.ABCMeta
    
    def __init__(self, properties={}, data=None, source=None,
                 bounds=None, ancillary_parameters=None,
                 ancillary_arrays=None, copy=True,
                 _use_data=True):
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

#    # ----------------------------------------------------------------
#    # Attributes
#    # ----------------------------------------------------------------
#    @property
#    def _Bounds(self):
#        '''The `Data` object containing the data array.
#
#.. versionadded:: 1.6
#
#        '''
#        return self._Bounds
#    #--- End: def
#    @_Bounds.setter
#    def _Bounds(self, value):
#        self._Bounds = value
#        self._hasbounds = True
#    @_Bounds.deleter
#    def _Bounds(self):
#        self._Bounds = None
#        self._hasbounds = False
#
#    @property
#    def bounds(self):
#        '''The `Bounds` object containing the cell bounds.
#
#.. versionadded:: 2.0
#
#.. seealso:: `lower_bounds`, `upper_bounds`
#
#:Examples:
#
#>>> c
#<CF {+Variable}: latitude(64) degrees_north>
#>>> c.bounds
#<CF Bounds: latitude(64, 2) degrees_north>
#>>> c.bounds = b
#AttributeError: Can't set 'bounds' attribute. Consider the insert_bounds method.
#>>> c.bounds.max()
#<CF Data: 90.0 degrees_north>
#>>> c.bounds -= 1
#AttributeError: Can't set 'bounds' attribute. Consider the insert_bounds method.
#>>> b = c.bounds
#>>> b -= 1
#>>> c.bounds.max()       
#<CF Data: 89.0 degrees_north>
#
#        '''
#        return self._Bounds
#    @bounds.setter
#    def bounds(self, value):
#        raise AttributeError("use insert_bounds")
#    @bounds.deleter
#    def bounds(self):  
#        raise AttributeError("use remove_bounds")
#    #--- End: def
#
#    # ----------------------------------------------------------------
#    # Cell extent properties: parameters
#    # ----------------------------------------------------------------
#    @property
#    def climatology(self):
#        '''
#        '''
#        if 'climatology' not in self._ancillary_properties:
#            return False
#
#        return self._climatology
#    @climatology.setter
#    def climatology(self, value):
#        self._climatology = value
#        self._ancillary_properties.add('climatology')
#    @climatology.deleter
#    def climatology(self):  
#        del self._climatology
#        self._ancillary_properties.discard('climatology')
#    #--- End: def
#
#    def geometry(self):
#        '''
#        '''
#        if 'geometry' not in self._ancillary_properties:
#            return False
#
#        return self._geometry
#    @geometry.setter
#    def geometry(self, value):
#        self._geometry = value
#        self._ancillary_properties.add('geometry')
#    @geometry.deleter
#    def geometry(self):  
#        del self._geometry
#        self._ancillary_properties.discard('geometry')
#    #--- End: def
#
#    # ----------------------------------------------------------------
#    # Cell extent properties: ancillary arrays
#    # ----------------------------------------------------------------
#    @property
#    def part_node_count(self):
#        '''
#        '''
#        if 'part_node_count' not in self._ancillary_arrays:
#            raise ValueError("asd asd a[114444444444440283uy8 ")
#            
#        return self._part_node_count
#    @part_node_count.setter
#    def part_node_count(self, value):
#        self._part_node_count = value
#        self._ancillary_arrays.add('part_node_count')
#    @part_node_count.deleter
#    def part_node_count(self):  
#        del self._part_node_count
#        self._ancillary_arrays.discard('part_node_count')
#    #--- End: def
#
#    @property
#    def interior_ring(self):
#        '''
#        '''
#        if 'interior_ring' not in self._ancillary_arrays:
#            raise ValueError("asd asd a[88888888800___99990283uy8 ")
#            
#        return self._interior_ring
#    @interior_ring.setter
#    def interior_ring(self, value):
#        self._interior_ring = value
#        self._ancillary_arrays.add('interior_ring')
#    @interior_ring.deleter
#    def interior_ring(self):  
#        del self._interior_ring
#        self._ancillary_arrays.discard('interior_ring')
#    #--- End: def
#
#    # ----------------------------------------------------------------
#    # Domain topology properties: parameters
#    # ----------------------------------------------------------------
#    def topology(self):
#        '''
#        '''
#        if 'topology' not in self._ancillary_properties:
#            return False
#
#        return self._topology
#    @topology.setter
#    def topology(self, value):
#        self._topology = value
#        self._ancillary_properties.add('topology')
#    @topology.deleter
#    def topology(self):  
#        del self._topology
#        self._ancillary_properties.discard('topology')
#    #--- End: def
#
#    def topology_location(self):
#        '''
#        '''
#        if 'topology_location' not in self._ancillary_properties:
#            return False
#
#        return self._topology_location
#    @topology_location.setter
#    def topology_location(self, value):
#        self._topology_location = value
#        self._ancillary_properties.add('topology_location')
#    @topology_location.deleter
#    def topology_location(self):  
#        del self._topology_location
#        self._ancillary_properties.discard('topology_location')
#    #--- End: def
#
#    def topology_dimension(self):
#        '''
#        '''
#        if 'topology_dimension' not in self._ancillary_properties:
#            return False
#
#        return self._topology_dimension
#    @topology_dimension.setter
#    def topology_dimension(self, value):
#        self._topology_dimension = value
#        self._ancillary_properties.add('topology_dimension')
#    @topology_dimension.deleter
#    def topology_dimension(self):  
#        del self._topology_dimension
#        self._ancillary_properties.discard('topology_dimension')
#    #--- End: def
#
#    # ----------------------------------------------------------------
#    # Domain topology properties: ancillary arrays
#    # ----------------------------------------------------------------
#    @property
#    def topology_connectivity(self):
#        '''
#        '''
#        if 'topology_connectivity' not in self._ancillary_arrays:
#            raise ValueError("xxxxxxxxxxxx hjko.jonl bo,n uy8 ")
#            
#        return self._topology_connectivity
#    @topology_connectivity.setter
#    def topology_connectivity(self, value):
#        self._topology_connectivity = value
#        self._ancillary_arrays.add('topology_connectivity')
#    @topology_connectivity.deleter
#    def topology_connectivity(self):  
#        del self._topology_connectivity
#        self._ancillary_arrays.discard('topology_connectivity')
#    #--- End: def

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
   
#    def dump(self, display=True, field=None, key=None,
#             _omit_properties=(), _prefix='', _title=None,
#             _create_title=True, _level=0):
#        '''Return a string containing a full description of the instance.
#
#.. versionadded:: 1.6
#
#:Parameters:
#
#    display: `bool`, optional
#        If False then return the description as a string. By default
#        the description is printed, i.e. ``f.dump()`` is equivalent to
#        ``print f.dump(display=False)``.
#
#    omit: sequence of `str`, optional
#        Omit the given CF properties from the description.
#
#    _prefix: optional
#        Ignored.
#
#:Returns:
#
#    out: `None` or `str`
#        A string containing the description.
#
#:Examples:
#
#        '''
#        string = super(AbstractBoundedArray, self).dump(
#            display=False, field=field, key=key,
#            _omit_properties=_omit_properties, _prefix=_prefix,
#            _title=_title, _create_title=_create_title, _level=_level)
#
#        string = [string]
#        
#        # ------------------------------------------------------------
#        # Bounds
#        # ------------------------------------------------------------
#        b = self.get_bounds(None)
#        if b is None:
#            continue
#        
#        if not isinstance(b, AbstractArray):
#            string.append('{0}{1}bounds = {2}'.format(indent1, attribute, b))
#            continue
#        
#        string.append(
#            b.dump(display=False, field=field, key=key,
#                   _prefix=_prefix+'bounds.',
#                   _create_title=False, _level=level+1))
#
#        #-------------------------------------------------------------
#        # Extent and topology properties
#        # ------------------------------------------------------------
#        for x in ['extent', 'topology']:
#            parameters = getattr(self, x+'_parameters')()
#            for name, parameter in sorted(parameters.items()):
#                string.append(
#                    '{0}{1}{2}.{3} = {4}'.format(indent1, _prefix, x, name, parameter))
#
#            arrays = getattr(self, x+'_arrays')()
#            for name, array in sorted(arrays.items()):
#                string.append(
#                    array.dump(display=False, field=field, key=key,
#                               _prefix=_prefix+x+'.'+name+'.',
#                               _create_title=False, _level=level+1))
#        #--- End: for
#            
#        string = '\n'.join(string)
#        
#        if display:
#            print string
#        else:
#            return string
#    #--- End: def
#
#    def equals(self, other, rtol=None, atol=None, traceback=False,
#               ignore_data_type=False, ignore_fill_value=False,
#               ignore_properties=(), ignore_construct_type=False):
#        '''
#        '''
#        if rtol is None:
#            rtol = RTOL()
#        if atol is None:
#            atol = ATOL()
#
#        if not super(AbstractBoundedArray, self).equals(
#                other,
#                rtol=rtol, atol=atol, traceback=tracback,
#                ignore_data_type=ignore_data_type,
#                ignore_fill_value=ignore_fill_value,
#                ignore_properties=ignore_properties,
#                ignore_construct_type=ignore_construct_type):
#            if traceback:
#                print("???????/")
#            return False
#        #--- End: if
#
#        # ------------------------------------------------------------
#        # Check the ancillary parameters
#        # ------------------------------------------------------------
#        if ignore_fill_value:
#            ignore_properties += ('_FillValue', 'missing_value')
#            
#        for x in ['extent', 'topology']:
#            self_parameters  = getattr(self, x+'_parameters')()
#            other_parameters = getattr(other, x+'_parameters')()
#            if set(self_parameters) != set(other_parameters):
#                if traceback:
#                    print("{0}: Different parameters: {1}, {2}".format( 
#                        self.__class__.__name__,
#                        set(self_parameters), set(other_parameters)))
#                return False
#            
#            for name, x in sorted(self_parameters.iteritems()):
#                y = other_parameters[name]
#                
#                if not cf_equals(x, y, rtol=rtol, atol=atol,
#                                 ignore_fill_value=ignore_fill_value,
#                                 traceback=traceback):
#                    if traceback:
#                        print("{0}: Different parameter {1!r}: {2!r}, {3!r}".format(
#                            self.__class__.__name__, prop, x, y))
#                    return False
#        #--- End: for
#
#        # ------------------------------------------------------------
#        # Check the bounds 
#        # ------------------------------------------------------------
#        self_hasbounds = self.has_bounds()
#        if self_has_bounds != other.has_bounds():
#            if traceback:
#                print("{0}: Different {1}".format(self.__class__.__name__, attr))
#            return False
#                
#        if self_has_bounds:            
#            if not self.get_bounds().equals(other.get_bounds(),
#                                            rtol=rtol, atol=atol,
#                                            traceback=traceback,
#                                            ignore_data_type=ignore_data_type,
#                                            ignore_construct_type=ignore_construct_type,
#                                            ignore_fill_value=ignore_fill_value):
#                if traceback:
#                    print("{0}: Different {1}".format(self.__class__.__name__, attr))
#                return False
#        #--- End: if
#
#        # ------------------------------------------------------------
#        # Check the ancillary arrays
#        # ------------------------------------------------------------
#        for x in ['extent', 'topology']:
#            self_ancillary_arrays  = getattr(self, x+'_arrays')()
#            other_ancillary_arrays = getattr(other, x+'_arrays')()
#            if set(self_ancillary_arrays) != set(other_ancillary_arrays):
#                if traceback:
#                    print("{0}: Different ancillary arrays: {1}, {2}".format( 
#                        self.__class__.__name__,
#                        set(self_ancillary_arrays), set(other_ancillary_arrays)))
#                return False
#    
#            for name, x in sorted(self_ancillary_arrays.items()):
#                y = other_arrays[name]
#                
#                if not x.equals(y rtol=rtol, atol=atol,
#                                traceback=traceback,
#                                ignore_data_type=ignore_data_type,
#                                ignore_construct_type=ignore_construct_type,
#                                ignore_fill_value=ignore_fill_value):
#                    if traceback:
#                        print("{0}: Different {1} {2}".format(self.__class__.__name__, x, name))
#                    return False
#        #--- End: for
#
#        return True
#    #--- End: def
#        
#    def expand_dims(self, position , copy=True):
#        '''
#        '''
#        position = self._parse_axes([position])[0]
#        
#        c = super(AbstractBoundedArray, self).expand_dims(position,
#                                                          copy=copy)
#        
#        bounds = c.get_bounds(None)
#        if bounds is not None:
#            bounds.expand_dims(position, copy=False)
#            
#        for array in c.ancillary_arrays().itervalues():                
#            array.expand_dims(position, copy=False)
#
#        return c
#    #--- End: def        
    
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
        if default:
            return getattr(self, '_bounds', default[0])

        try:
            return self._bounds
        except AttributeError:
            raise AttributeError("aascas 34r34 5iln ")
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
        if not self.has_bounds():
            return

        bounds = self.get_bounds()
        del self._bounds
        self.invalid_bounds = False
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
        return hasattr(self, '_bounds')
    #--- End: def

#    def squeeze(self, axes=None , copy=True):
#        '''
#        '''
#        axes = self._parse_axes(axes)
#
#        c = super(AbstractBoundedArray, self).squeeze(axes, copy=copy)
#        
#        bounds = c.get_bounds(None)
#        if bounds is not None:
#            bounds.squeeze(axes, copy=False)
#
#        for array in c.ancillary_arrays().itervalues():                
#            array.squeeze(axes, copy=False)
#        
#        return c
#    #--- End: def        
    
#--- End: class
