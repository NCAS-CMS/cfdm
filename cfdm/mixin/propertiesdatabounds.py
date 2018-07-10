import abc

from .propertiesdata import PropertiesData

from ..functions import RTOL, ATOL


class PropertiesDataBounds(PropertiesData):
    '''Mixin class for a data array with descriptive properties and cell
bounds.

    '''
    __metaclass__ = abc.ABCMeta
    
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

        '''
        if indices is Ellipsis:
            return self.copy()

#        # Parse the index
        if not isinstance(indices, tuple):
            indices = (indices,)

#        indices = parse_indices(self.shape, indices)

        new = super(PropertiesDataBounds, self).__getitem__(indices)
        
        data = self.get_data(None)

        if data is not None:
            new.set_data(data[indices], copy=False)

        # Subspace the bounds, if there are any.
        self_bounds = self.get_bounds(None)
        if self_bounds is not None:
            data = self_bounds.get_data(None)
            if data is not None:
                # There is a bounds array
                bounds_indices = list(indices)
                bounds_indices.append(Ellipsis)
                if data.ndim <= 1 and not self.has_geometry_type():
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
                #-- End: if
#                    else:
#                        bounds_indices.append(slice(None))
#                else:
#                    bounds_indices.append(Ellipsis)
    
                new_bounds = new.get_bounds()
                new_bounds.set_data(data[tuple(bounds_indices)], copy=False)
        #--- End: if

        # Subspace the interior ring array, if there are one.
        interior_ring = self.get_interior_ring(None)
        if interior_ring is not None:
            data = interior_ring.get_data(None)
            if data is not None:
                new_interior_ring = new.get_interior_ring()
                new_interior_ring.set_data(data[indices], copy=False)
        #--- End: if

#       # Subspace the ancillary arrays, if there are any.
#       new_ancillaries = new.ancillaries()
#       if new_ancillaries:
#           ancillary_indices = tuple(indices) + (Ellipsis,)
#           
#           for name, ancillary in self.ancillaries.iteritems():
#               data = ancillary.get_data(None)
#               if data is None:
#                   continue
#
#               new_ancillary = new_ancillaries[name]
#               new_ancillary.set_data(data[ancillary_indices], copy=False)
#       #--- End: if

        # Return the new bounded variable
        return new
    #--- End: def

    def dump(self, display=True, field=None, key=None,
             _omit_properties=None, _prefix='', _title=None,
             _create_title=True, _level=0):
        '''Return a string containing a full description of the instance.

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
        # ------------------------------------------------------------
        # Properties and Data
        # ------------------------------------------------------------
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
                                      _prefix=_prefix+'Bounds:',
                                      _create_title=False, _level=_level))

        # ------------------------------------------------------------
        # Geometry type
        # ------------------------------------------------------------
        geometry_type = self.get_geometry_type(None)
        if geometry_type is not None:
            indent1 = '    ' * (_level + 1)
            string.append(
                '{0}{1}Geometry type: {2}'.format(indent1, _prefix, geometry_type))

        #-------------------------------------------------------------
        # Interior ring
        # ------------------------------------------------------------
        interior_ring = self.get_interior_ring(None)
        if interior_ring is not None:
            string.append(interior_ring.dump(display=False, field=field, key=key,
                                             _prefix=_prefix+'Interior ring:',
                                             _create_title=False, _level=_level))
            
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
    
        # ------------------------------------------------------------
        # Check the properties and data
        # ------------------------------------------------------------
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
    
        # ------------------------------------------------------------
        # Check the geometry type
        # ------------------------------------------------------------
        if self.get_geometry_type(None) != other.get_geometry_type(None):
            if traceback:
                print(
"{0}: Different geometry types: {1}, {2}".format(
    self.__class__.__name__, self.get_geometry_type(None), other.get_geometry_type(None)))
	    return False

        # ------------------------------------------------------------
        # Check the bounds 
        # ------------------------------------------------------------
        self_has_bounds = self.has_bounds()
        if self_has_bounds != other.has_bounds():
            if traceback:
                print("{0}: Different {1}".format(self.__class__.__name__, attr))
            return False
                
        if self_has_bounds:            
            if not self._equals(self.get_bounds(), other.get_bounds(),
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
        # Check the interior ring
        # ------------------------------------------------------------
        self_has_interior_ring = self.has_interior_ring()
        if self_has_interior_ring != other.has_interior_ring():
            if traceback:
                print("{0}: Different {1}".format(self.__class__.__name__, attr))
            return False
                
        if self_has_interior_ring:            
            if not self._equals(self.get_interior_ring(), other.get_interior_ring(),
                                rtol=rtol, atol=atol,
                                traceback=traceback,
                                ignore_data_type=ignore_data_type,
                                ignore_construct_type=ignore_construct_type,
                                ignore_fill_value=ignore_fill_value):
                if traceback:
                    print("{0}: Different {1}".format(self.__class__.__name__, attr))
                return False
        #--- End: if

#        # ------------------------------------------------------------
#        # Check the coordinate ancillaries
#        # ------------------------------------------------------------
#        ancillaries0 = self.ancillaries()
#        ancillaries1 = other.ancillaries()
#        if set(ancillaries0) != set(ancillaries1):
#            if traceback:
#                print(
#"{0}: Different coordinate ancillaries ({1} != {2})".format(
#    self.__class__.__name__,
#    set(ancillaries0). set(ancillaries1)))
#            return False
#
#        for name, value0 in ancillaries0.iteritems():            
#            value1 = ancillaries1[term]                
#            if not self._equals(value0, value1, rtol=rtol, atol=atol,
#                                traceback=traceback,
#                                ignore_data_type=ignore_data_type,
#                                ignore_fill_value=ignore_fill_value,
#                                ignore_construct_type=ignore_construct_type):
#                if traceback:
#                    print(
#"{}: Unequal {!r} ancillaries ({!r} != {!r})".format( 
#    self.__class__.__name__, name, value0, value1))
#                return False
#        #--- End: for
        
        return True
#    #--- End: def
    
    def expand_dims(self, position , copy=True):
        '''
        '''
        position = self._parse_axes([position])[0]
        
        c = super(PropertiesDataBounds, self).expand_dims(position,
                                                          copy=copy)
        
        # ------------------------------------------------------------
        # Expand the dims of the bounds
        # ------------------------------------------------------------
        bounds = c.get_bounds(None)
        if bounds is not None:
            bounds.expand_dims(position, copy=False)

        # ------------------------------------------------------------
        # Expand the dims of the interior_ring
        # ------------------------------------------------------------
        interior_ring = c.get_interior_ring(None)
        if interior_ring is not None:
            interior_ring.expand_dims(position, copy=False)

        return c
    #--- End: def
    
    def squeeze(self, axes=None , copy=True):
        '''
        '''
        axes = self._parse_axes(axes)

        c = super(PropertiesDataBounds, self).squeeze(axes, copy=copy)
        

        # ------------------------------------------------------------
        # Squeeze the bounds
        # ------------------------------------------------------------
        bounds = c.get_bounds(None)
        if bounds is not None:
            bounds.squeeze(axes, copy=False)

        # ------------------------------------------------------------
        # Squeeze the interior_ring
        # ------------------------------------------------------------
        interior_ring = c.get_interior_ring(None)
        if interior_ring is not None:
            interior_ring.squeeze(axes, copy=False)

        return c
    #--- End: def
    
    def transpose(self, axes=None, copy=True):
        '''Permute the dimensions of the data.

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

        c = super(PropertiesDataBounds, self).transpose(axes, copy=copy)

        # ------------------------------------------------------------
        # Transpose the bounds
        # ------------------------------------------------------------        
        bounds = c.get_bounds(None)
        if bounds is not None:
            data = bounds.get_data(None)
            if data is not None:            
                b_axes = axes[:]
                b_axes.extend.extend(range(c.ndim, data.ndim))
                
                bounds.transpose(b_axes, copy=False)
                
                if (c.ndim == 2 and data.ndim == 3 and data.shape[-1] == 4 and 
                    b_axes[0:2] == [1, 0]):
                    # Swap elements 1 and 3 of the trailing dimension
                    # so that the values are still contiguous (if they
                    # ever were). See section 7.1 of the CF
                    # conventions.
                    data[:, :, slice(1, 4, 2)] = data[:, :, slice(3, 0, -2)]
                    bounds.set_data(data, copy=False)
        #--- End: if

        a_axes = axes
        a_axes.append(-1)

        # ------------------------------------------------------------
        # Transpose the interior_ring
        # ------------------------------------------------------------
        interior_ring = c.get_interior_ring(None)
        if interior_ring is not None:
            interior_ring_axes = axes[:]
            interior_ring_axes.extend(range(c.ndim, interior_ring.ndim))
            interior_ring.transpose(interior_ring_axes, copy=False)

        return c
    #--- End: def

#--- End: class
