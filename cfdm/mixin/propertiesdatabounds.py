import abc

from .propertiesdata import PropertiesData

from ..functions import RTOL, ATOL


class PropertiesDataBounds(PropertiesData):
    '''Mixin class for a data array with bounds and with descriptive
properties.

    '''
    __metaclass__ = abc.ABCMeta
    
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

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
            bounds_data = self_bounds.get_data(None)
            if bounds_data is not None:
                # There is a bounds array
                bounds_indices = list(indices)
                if data.ndim <= 1: # and not self.is_geometry():
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
                    bounds_indices.append(Ellipsis)
    
                if _debug:
                    print '{}.__getitem__: indices for bounds ='.format(
                        self.__class__.__name__, bounds_indices)

                bounds = new.get_bounds()
                bounds.set_data(bounds_data[tuple(bounds_indices)], copy=False)
        #--- End: if

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

        #-------------------------------------------------------------
        # Cell extent parameter-valued terms
        # ------------------------------------------------------------
        indent1 = '    ' * (_level + 1)
        cell_extent = self.cell_extent
        for name, parameter in sorted(cell_extent.parameters().items()):
            string.append(
                '{0}{1}Cell:{2} = {3}'.format(indent1, _prefix, name, parameter))

        #-------------------------------------------------------------
        # Cell extent domain ancillary-valued terms
        # ------------------------------------------------------------
        for term, key in sorted(cell_extent.domain_ancillaries().items()):
            if field:
                value = field.domain_ancillaries().get(key)
                if value is not None:
                    value = 'Domain Ancillary: '+value.name(default=key)
                else:
                    value = ''
            else:
                value = key

            string.append("{0}{1}Cell:{2} = {3}".format(
                indent1, _prefix, term, str(value)))
        #--- End: for
        
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
        # Check the cell extent parameters
        # ------------------------------------------------------------
        if not self.cell_extent.equals(
                other.cell_extent,
                rtol=rtol, atol=atol,
                traceback=traceback,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,                
                ignore_construct_type=ignore_construct_type):
            if traceback:
                print(
"{}: Different cell extent".format(self.__class__.__name__))
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

        c = super(PropertiesDataBounds, self).transpose(axes,
                                                        copy=copy)

        axes.append(-1)
        
        bounds = c.get_bounds(None)
        if bounds is not None:
            bounds.transpose(axes, copy=False)
            
            data = bounds.get_data(None)
            if (data is not None and
                data.ndim == 3 and data.shape[-1] == 4 and 
                axes[0:2] == [1, 0]):
                # Swap elements 1 and 3 of the trailing dimension so
                # that the values are still contiguous (if they ever
                # were). See section 7.1 of the CF conventions.
                data[:, :, slice(1, 4, 2)] = data[:, :, slice(3, 0, -2)]
                bounds.set_data(data, copy=False)
        #--- End: if
        
        return c
    #--- End: def

#--- End: class
