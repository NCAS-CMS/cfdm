import abc

from .propertiesdata import PropertiesData

from ..functions import RTOL, ATOL
from ..functions import equals as cfdm_equals


# ====================================================================
#
# CFDM Bounded variable mixin 
#
# ====================================================================

class PropertiesDataBounds(PropertiesData):
    '''Base class for CF dimension coordinate, auxiliary coordinate and
domain ancillary objects.

    '''
    __metaclass__ = abc.ABCMeta
    
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

        new = super(PropertiesDataBounds, self).__getitem__(indices)
        
        data = self.get_data(None)

        if _debug:
            cname = self.__class__.__name__
            print '{}.__getitem__: shape    = {}'.format(cname, self.shape)
            print '{}.__getitem__: indices  = {}'.format(cname, indices)

        if data is not None:
            new.set_data(data[tuple(indices)], copy=False)

        # Subspace the bounds, if there are any
        self_bounds = self.get_bounds(None)
        if self_bounds is not None:
            data = self_bounds.get_data(None)
            if data is not None:
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

                bounds = new.get_bounds()
                bounds.set_data(data[tuple(bounds_indices)], copy=False)
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

    def dump(self, display=True, field=None, key=None,
             _omit_properties=None, _prefix='', _title=None,
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
        string = super(PropertiesDataBounds, self).dump(
            display=False, field=field, key=key,
            _omit_properties=_omit_properties, _prefix=_prefix,
            _title=_title, _create_title=_create_title, _level=_level)

        string = [string]
        
        # ------------------------------------------------------------
        # Bounds
        # ------------------------------------------------------------
        bounds = self.get_bounds(None)
        if bounds is not None:
            string.append(bounds.dump(display=False, field=field, key=key,
                                      _prefix=_prefix+'bounds.',
                                      _create_title=False, _level=_level))
        
        #-------------------------------------------------------------
        # Extent and topology properties
        # ------------------------------------------------------------
        for x in ['extent', 'topology']:
            parameters = getattr(self, x+'_parameters')()
            for name, parameter in sorted(parameters.items()):
                string.append(
                    '{0}{1}{2}.{3} = {4}'.format(indent1, _prefix, x, name, parameter))

            arrays = getattr(self, x+'_arrays')()
            for name, array in sorted(arrays.items()):
                string.append(
                    array.dump(display=False, field=field, key=key,
                               _prefix=_prefix+x+'.'+name+'.',
                               _create_title=False, _level=_level))
        #--- End: for
            
        string = '\n'.join(string)
        
        if display:
            print string
        else:
            return string
    #--- End: def

#Domain Ancillary: 
#    Data = 'asdasdasdas'
#    units = 'm'
#    Data(catchement(10)) = [10.0, ..., 78.9]
#    bounds.long_name = 'Why on earth do I have  long name?'
#    bounds.Data(catchement(10), 2) = [[5.0, ..., 15.0]]
#    extent.climatology = True
#    extent.geometry_type = 'polygon'
#    extent.part_node_count.long_name = 'this is a part node count'
#    extent.part_node_count.Data(catchement(10), 4) = [[2, ..., 4]]
#    extent.interior_ring.Data(catchement(10), 4) = [[1, ..., 0]]

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_construct_type=False):
        '''
        '''
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        if not super(PropertiesDataBounds, self).equals(
                other,
                rtol=rtol, atol=atol, traceback=traceback,
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
            
        for x in ['extent', 'topology']:
            self_parameters  = getattr(self, x+'_parameters')()
            other_parameters = getattr(other, x+'_parameters')()
            if set(self_parameters) != set(other_parameters):
                if traceback:
                    print("{0}: Different parameters: {1}, {2}".format( 
                        self.__class__.__name__,
                        set(self_parameters), set(other_parameters)))
                return False
            
            for name, x in sorted(self_parameters.iteritems()):
                y = other_parameters[name]
                
                if not cfdm_equals(x, y, rtol=rtol, atol=atol,
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
        self_has_bounds = self.has_bounds()
        if self_has_bounds != other.has_bounds():
            if traceback:
                print("{0}: Different {1}".format(self.__class__.__name__, attr))
            return False
                
        if self_has_bounds:            
            if not cfdm_equals(self.get_bounds(), other.get_bounds(),
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
        for x in ['extent', 'topology']:
            self_ancillary_arrays  = getattr(self, x+'_arrays')()
            other_ancillary_arrays = getattr(other, x+'_arrays')()
            if set(self_ancillary_arrays) != set(other_ancillary_arrays):
                if traceback:
                    print("{0}: Different ancillary arrays: {1}, {2}".format( 
                        self.__class__.__name__,
                        set(self_ancillary_arrays), set(other_ancillary_arrays)))
                return False
    
            for name, x in sorted(self_ancillary_arrays.items()):
                y = other_arrays[name]
                
                if not cfdm_equals(x, y, rtol=rtol, atol=atol,
                                 traceback=traceback,
                                 ignore_data_type=ignore_data_type,
                                 ignore_construct_type=ignore_construct_type,
                                 ignore_fill_value=ignore_fill_value):
                    if traceback:
                        print("{0}: Different {1} {2}".format(self.__class__.__name__, x, name))
                    return False
        #--- End: for

        return True
    #--- End: def
    
    def expand_dims(self, position , copy=True):
        '''
        '''
        position = self._parse_axes([position])[0]
        
        c = super(PropertiesDataBounds, self).expand_dims(position,
                                                          copy=copy)
        
        bounds = c.get_bounds(None)
        if bounds is not None:
            bounds.expand_dims(position, copy=False)
            
        for array in c.ancillary_arrays().itervalues():                
            array.expand_dims(position, copy=False)

        return c
    #--- End: def        
    
    def squeeze(self, axes=None , copy=True):
        '''
        '''
        axes = self._parse_axes(axes)

        c = super(PropertiesDataBounds, self).squeeze(axes, copy=copy)
        
        bounds = c.get_bounds(None)
        if bounds is not None:
            bounds.squeeze(axes, copy=False)

        for array in c.ancillary_arrays().itervalues():                
            array.squeeze(axes, copy=False)
        
        return c
    #--- End: def
    
    def transpose(self, axes=None, copy=True):
        '''Permute the dimensions of the data.

.. versionadded:: 2.0 

.. seealso:: `expand_dims`, `squeeze`

:Parameters:

    axes: (sequence of) `int`, optional
        The new order of the data array. By default, reverse the
        dimensions' order, otherwise the axes are permuted according
        to the values given. The values of the sequence comprise the
        integer positions of the dimensions in the data array in the
        desired order.

    {+copy}

:Returns:

    out : `{+Variable}`

:Examples:

>>> c.ndim
3
>>> c.{+name}()
>>> c.{+name}([1, 2, 0])

        '''
        if axes is None:
            axes = range(ndim-1, -1, -1)
        else:
            axes = self._parse_axes(axes)

        c = super(PropertiesDataBounds, self).transpose(axes,
                                                        copy=copy)

        axes.append(-1)
        
        bounds = c.get_bounds(None)
        if bounds is not None:
            bounds.transpose(axes, copy=False)
            
            data = bounds.get_data(None)
            if (data is not None and
                data.ndim == 3 and
                data.shape[-1] == 4 and 
                axes[0:2] == [1, 0]):
                # Swap columns 1 and 3 so that the values are still
                # contiguous (if they ever were). See section 7.1 of
                # the CF conventions.
                data[..., [1, 3]] = data[..., [3, 1]]
                bounds.set_data(data, copy=False)
        #--- End: if

        for array in c.ancillary_arrays().itervalues():                
            array.transpose(axes, copy=False)
        
        return c
    #--- End: def

#--- End: class
