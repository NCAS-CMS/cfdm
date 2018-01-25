from collections import abc

from .arrayconstruct import AbstractArray

# ====================================================================
#
# CFDM Bounded variable object
#
# ====================================================================

class AbstractBoundedArray(AbstractArray):
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
        self._ancillary_parameters = {}
        self._ancillary_arrays     = {}
        
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
    #--- End: def

    def __getitem__(self, indices):
        '''

x.__getitem__(indices) <==> x[indices]
        
        '''
        if indices is Ellipsis:
            return self.copy()

        # Parse the index
        if not isinstance(indices, tuple):
            indices = (indices,)

        indices = parse_indices(self.shape, indices)

        new = self.copy(data=False)

        data = self.get_data(None)

        if _debug:
            cname = self.__class__.__name__
            print '{}.__getitem__: shape    = {}'.format(cname, self.shape)
            print '{}.__getitem__: indices  = {}'.format(cname, indices)

        if data is not None:
            new.set_data(data[tuple(indices)], copy=False)

        # Subspace the bounds, if there are any
        if not new.has_bounds():
            bounds = None
        else:
            bounds = self.get_bounds(None)
            if bounds is not None:
                bounds_indices = list(indices)
                if data.ndim <= 1:
                    index = bounds_indices[0]
                    if isinstance(index, slice):
                        if index.step < 0:
                            # This scalar or 1-d variable has been
                            # reversed so reverse its bounds (as per
                            # 7.1 of the conventions)
                            bounds_indices.append(slice(None, None, -1))
                    elif data.size > 1 and index[-1] < index[0]:
                        # This 1-d variable has been reversed so
                        # reverse its bounds (as per 7.1 of the
                        # conventions)
                        bounds_indices.append(slice(None, None, -1))
                    else:
                        bounds_indices.append(slice(None))
                else:
                    bounds_indices.append(slice(None))

                if _debug:
                    print '{}.__getitem__: indices for bounds ='.format(
                        self.__class__.__name__, bounds_indices)

                data = bounds.get_data()
                bounds = bounds.copy(data=False)
                bounds.set_data(data[tuple(bounds_indices)], copy=False)
                new.set_bounds(bounds, copy=False)
        #--- End: if

        # Subspace the ancillary arrays
        ancillary_arrays = self.ancillary_arrays()
        if ancillary_arrays:
            for name, array in ancillary_arrays.iteritems():
                if not array.has_data():
                    new.set_ancillary_array(name, array, copy=True)
                    continue
                
                ancillary_indices = list(indices)
                ancillary_indices.append(slice(None))
                if _debug:
                    print '{0}.__getitem__: indices for ancillary array {1!r}={2}'.format(
                        self.__class__.__name__, name, ancillary_indices)

                data = array.get_data()
                array = array.copy(data=False)
                array.set_data(data[tuple(ancillary_indices)], copy=False)
                new.set_ancillary_array(name, array, copy=False)
        #--- End: if

        # Return the new bounded variable
        return new
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

    def get_extent_property(self, name, *default):
        '''
        '''
        if default:
            return self._extent_properties.get(name, default[0])

        try:
            return self._extent_properties[name]
        except KeyError:
            raise AttributeError("acj s;do8h po;iln ")
    #--- End: def

    def set_extent_property(self, name, value, copy=True):
        '''
        '''
        if isinstance(value, AbstractArray):
            if copy:
                value =value .copy()

            self._extent_ancillary_arrays.add(name)
        else:
            self._extent_parameters.add(name)
            
        self._extent_properties[name] = value
    #--- End: def
    
    def del_extent_property(self, name):
        '''
        '''
        self._extent_parameters.discard(name)
        self._extent_ancillary_arrays.discard(name)
        return self._extent_properties.pop(name, None)
    #--- End: def

    def has_extent_property(self, name):
        '''
        '''
        return name in self._extent_properties
    #--- End: def

    def extent_properties(self, copy=False):
        '''
        '''
        out = self.extent_parameters(copy=copy)
        out.update(self.extent_arrays(copy=copy))
        return out
    #--- End: def

    def _get_parameters(self, x):
        '''
        '''
        out = {}
        for name in self._parameters[x]:
            out[name] = self._properties[x][name]
        
        return out
    #--- End: def

    def _get_arrays(self, x, copy=False):
        '''
        '''
        out = {}
        for name in self._arrays[x]
            out[name] = self._arrays[x][name]
            
        if copy:
            for name, value in out.items():
                out[name] = value.copy()
        #--- End: if
        
        return out
    #--- End: def

    def extent_parameters(self):
        '''
        '''
        return self._get_parameters('extent')
    #--- End: def

    def extent_arrays(self, copy=False):
        '''
        '''
        return self._get_arrays('extent', copy=copy)
    #--- End: def

    def get_ancillary_array(self, name, *default):
        '''
        '''
        if default:
            return self._ancillary_arrays.get(name. default[0])

        try:
            return self._ancillary_arrays[name]
        except KeyError:
            raise AttributeError("acj s;do8h po;iln ")
    #--- End: def

    def set_ancillary_array(self, name, array, copy=True):
        '''
        '''
        if copy:
            array = array.copy(data=data)
            
        self._ancillary_arrays[name] = array
    #--- End: def
    
    def del_ancillary_array(self, name):
        '''
        '''
        return self._ancillary_arrays.pop(name, None)
    #--- End: def

    def has_ancillary_array(self, name):
        '''
        '''
        return name in self._ancillary_arrays
    #--- End: def

    def ancillary_arrays(self, copy=False):
        '''
        '''
        if copy:        
            out = {}
            for name, array in self._ancillary_arrays.iteritems():
                out[name] = array.copy()
        else:
            out = self._ancillary_arrays.copy()

        return out
    #--- End: def
    
    def get_ancillary_parameter(self, name, *default):
        '''
        '''
        if default:
            return self._ancillary_parameters.get(name. default[0])

        try:
            return self._ancillary_parameters[name]
        except KeyError:
            raise AttributeError("acj s;do8h po;iln ")
    #--- End: def

    def set_ancillary_parameter(self, name, parameter, copy=True):
        '''
        '''
        if copy:
            parameter = parameter.copy()
            
        self._ancillary_parameters[name] = parameter
    #--- End: def
    
    def del_ancillary_parameter(self, name):
        '''
        '''
        return self._ancillary_parameters.pop(name, None)
    #--- End: def

    def has_ancillary_parameter(self, name):
        '''
        '''
        return name in self._ancillary_parameters
    #--- End: def

    def ancillary_parameters(self, copy=False):
        '''
        '''
        if copy:        
            out = {}
            for name, parameter in self._ancillary_parameters.iteritems():
                out[name] = parameter.copy()
        else:
            out = self._ancillary_parameters.copy()

        return out
    #--- End: def
    
    def dump(self, display=True, field=None, key=None,
             _omit_properties=(), _prefix='', _title=None,
             _create_title=True, _level=0):
        '''Return a string containing a full description of the instance.

.. versionadded:: 1.6

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``f.dump()`` is equivalent to
        ``print f.dump(display=False)``.

    omit: sequence of `str`, optional
        Omit the given CF properties from the description.

    _prefix: optional
        Ignored.

:Returns:

    out: `None` or `str`
        A string containing the description.

:Examples:

        '''
        string = super(AbstractBoundedArray, self).dump(
            display=False, field=field, key=key,
            _omit_properties=_omit_properties, _prefix=_prefix,
            _title=_title, _create_title=_create_title, _level=_level)

        string = [string]
        
        # ------------------------------------------------------------
        # Bounds
        # ------------------------------------------------------------
        b = self.get_bounds(None)
        if b is None:
            continue
        
        if not isinstance(b, AbstractArray):
            string.append('{0}{1}bounds = {2}'.format(indent1, attribute, b))
            continue
        
        string.append(
            b.dump(display=False, field=field, key=key,
                   _prefix=_prefix+'bounds.',
                   _create_title=False, _level=level+1))
        
        #-------------------------------------------------------------
        # Ancillary parameters (e.g. geometry_type)
        # ------------------------------------------------------------
        for name, parameter in sorted(self.extent_parameters().items()):
            string.append('{0}{1}extent.{2} = {3}'.format(indent1, _prefix,
                                                          name, parameter))
            
        for name, a in sorted(self.extent_arrays().items()):
            if not isinstance(x, AbstractArray):
                string.append('{0}{1}{2} = {3}'.format(indent1, _prefix,
                                                       name, a))
                continue
            
            string.append(
                a.dump(display=False, field=field, key=key,
                       _prefix=_prefix+'extent.'+name+'.',
                       _create_title=False, _level=level+1))

        # ------------------------------------------------------------
        # Ancillary arrays (e.g. topology_connectivity)
        # ------------------------------------------------------------
        for name, topology in sorted(self.topology_parameters().items()):
            string.append('{0}{1}{2} = {3}'.format(indent1, _prefix,
                                                   name, parameter))
            
        for name, a in sorted(self.topology_arrays().items()):
            if not isinstance(x, AbstractArray):
                string.append('{0}{1}topology.{2} = {3}'.format(indent1, _prefix,
                                                                name, a))
                continue
            
            string.append(
                a.dump(display=False, field=field, key=key,
                       _prefix=_prefix+'topology.'+name+'.',
                       _create_title=False, _level=level+1))
            
        string = '\n'.join(string)
        
        if display:
            print string
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_construct_type=False):
        '''
        '''
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        if not super(AbstractBoundedArray, self).equals(
                other,
                rtol=rtol, atol=atol, traceback=tracback,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_properties=ignore_properties,
                ignore_construct_type=ignore_construct_type):
            if traceback:
                print("???????/")
            return False
        #--- End: if

        # ------------------------------------------------------------
        # Check the ancillary parameters
        # ------------------------------------------------------------
        if ignore_fill_value:
            ignore_properties += ('_FillValue', 'missing_value')
            
        self_parameters  = self.ancillary_parameters()
        other_parameters = other.ancillary_parameters()
        if set(self_parameters) != set(other_parameters):
            if traceback:
                print("{0}: Different parameters: {1}, {2}".format( 
                    self.__class__.__name__,
                    set(self_parameters), set(other_parameters)))
            return False
        
        for name, x in sorted(self_parameters.iteritems()):
            y = other_parameters[name]
            
            if not cf_equals(x, y, rtol=rtol, atol=atol,
                             ignore_fill_value=ignore_fill_value,
                             traceback=traceback):
                if traceback:
                    print("{0}: Different parameter {1!r}: {2!r}, {3!r}".format(
                        self.__class__.__name__, prop, x, y))
                return False
        #--- End: for

        # ------------------------------------------------------------
        # Check the bounds 
        # ------------------------------------------------------------
        self_hasbounds = self.has_bounds()
        if self_has_bounds != other.has_bounds():
            if traceback:
                print("{0}: Different {1}".format(self.__class__.__name__, attr))
            return False
                
        if self_has_bounds:            
            if not self.get_bounds().equals(other.get_bounds(),
                                            rtol=rtol, atol=atol,
                                            traceback=traceback,
                                            ignore_data_type=ignore_data_type,
                                            ignore_construct_type=ignore_construct_type,
                                            ignore_fill_value=ignore_fill_value):
                if traceback:
                    print("{0}: Different {1}".format(self.__class__.__name__, attr))
                return False
        #--- End: if

        # ------------------------------------------------------------
        # Check the ancillary arrays
        # ------------------------------------------------------------
        self_ancillary_arrays  = self.ancillary_arrays()
        other_ancillary_arrays = other.ancillary_arrays()
        if set(self_ancillary_arrays) != set(other_ancillary_arrays):
            if traceback:
                print("{0}: Different ancillary arrays: {1}, {2}".format( 
                    self.__class__.__name__,
                    set(self_ancillary_arrays), set(other_ancillary_arrays)))
            return False

        for name, x in sorted(self_ancillary_arrays.iteritems()):
            y = other_arrays[name]
            
            if not x.equals(y rtol=rtol, atol=atol,
                            traceback=traceback,
                            ignore_data_type=ignore_data_type,
                            ignore_construct_type=ignore_construct_type,
                            ignore_fill_value=ignore_fill_value):
                if traceback:
                    print("{0}: Different {1}".format(self.__class__.__name__, name))
                return False
        #--- End: for

        return True
    #--- End: def
        
    def expand_dims(self, position , copy=True):
        '''
        '''
        position = self._parse_axes([position])[0]
        
        c = super(AbstractBoundedArray, self).expand_dims(position,
                                                          copy=copy)
        
        bounds = c.get_bounds(None)
        if bounds is not None:
            bounds.expand_dims(position, copy=False)
            
        for array in c.ancillary_arrays().itervalues():                
            array.expand_dims(position, copy=False)

        return c
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
        if copy:
            bounds = bounds.copy(data=data)
        
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

    def squeeze(self, axes=None , copy=True):
        '''
        '''
        axes = self._parse_axes(axes)

        c = super(AbstractBoundedArray, self).squeeze(axes, copy=copy)
        
        bounds = c.get_bounds(None)
        if bounds is not None:
            bounds.squeeze(axes, copy=False)

        for array in c.ancillary_arrays().itervalues():                
            array.squeeze(axes, copy=False)
        
        return c
    #--- End: def        
    
#--- End: class
