from .arrayconstruct import AbstractArrayConstruct

# ====================================================================
#
# CFDM Bounded variable object
#
# ====================================================================

class AbstractBoundedArrayConstruct(AbstractArrayConstruct):
    '''Base class for CF dimension coordinate, auxiliary coordinate and
domain ancillary objects.
    '''
    def __init__(self, properties={}, data=None, bounds=None,
                 source=None, copy=True):
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
        if source is not None:
            if bounds is None:
                if isinstance(source, BoundedVariable):
                    bounds = getattr(self, 'bounds', None)
                
        # Set attributes, CF properties and data
        super(BoundedVariable, self).__init__(properties=properties,
#                                              attributes=attributes,
                                              data=data,
                                              source=source,
                                              copy=copy)
  
        # Bounds
        if bounds is not None:
            self.insert_bounds(bounds, copy=copy)
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

        new = self.copy(_omit_data=True)

        data = self.data

        if _debug:
            cname = self.__class__.__name__
            print '{}.__getitem__: shape    = {}'.format(cname, self.shape)
            print '{}.__getitem__: indices  = {}'.format(cname, indices)

        new._Data = data[tuple(indices)]

        # Subspace the bounds, if there are any
        if not new.hasbounds:
            bounds = None
        else:
            bounds = self.bounds
            if bounds.hasdata:
                indices = list(indices)
                if data.ndim <= 1:
                    index = indices[0]
                    if isinstance(index, slice):
                        if index.step < 0:
                            # This scalar or 1-d variable has been
                            # reversed so reverse its bounds (as per
                            # 7.1 of the conventions)
                            indices.append(slice(None, None, -1))
                    elif data.size > 1 and index[-1] < index[0]:
                        # This 1-d variable has been reversed so
                        # reverse its bounds (as per 7.1 of the
                        # conventions)
                        indices.append(slice(None, None, -1))                    
                #--- End: if

                if _debug:
                    print '{}.__getitem__: indices for bounds ='.format(self.__class__.__name__, indices)
                
                new.bounds._Data = bounds.data[tuple(indices)]
        #--- End: if

#        new._direction = None

        # Return the new bounded variable
        return new
    #--- End: def

    def expand_dims(self, position , copy=True):
        '''
        '''
        c = super(AbstractBoundedArrayConstruct, self).expand_dims(
            position, copy=copy)

        if c.hasbounds:
            position = self._parse_axes([position])[0]
            c.bounds.expand_dims(position, copy=False)

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
#        c = Variable.transpose.fget(self, axes, copy)

        c = super(BoundedVariable, self).transpose(axes, copy=copy)

        ndim = c.ndim
        if c.hasbounds and ndim > 1 and c.bounds.hasdata:
            # Transpose the bounds
            if axes is None:
                axes = range(ndim-1, -1, -1) + [-1]
            else:
                axes = self._parse_axes(axes) + [-1]
                
            bounds = c.bounds
            bounds.transpose(axes, copy=False)

            if (ndim == 2 and
                bounds.shape[-1] == 4 and 
                axes[0] == 1 and 
                (c.Units.islongitude or c.Units.islatitude or
                 c.getprop('standard_name', None) in ('grid_longitude' or
                                                      'grid_latitude'))):
                # Swap columns 1 and 3 so that the values are still
                # contiguous (if they ever were). See section 7.1 of
                # the CF conventions.
                bounds[..., [1, 3]] = bounds[..., [3, 1]]
        #--- End: if

        return c
    #--- End: def
    
#    def _infer_direction(self):
#        '''Return True if a coordinate is increasing, otherwise return False.
#
#A coordinate is considered to be increasing if its *raw* data array
#values are increasing in index space or if it has no data not bounds
#data.
#
#If the direction can not be inferred from the coordinate's data then
#the coordinate's units are used.
#
#The direction is inferred from the coordinate's data array values or
#its from coordinates. It is not taken directly from its `Data` object.
#
#:Returns:
#
#    out : bool
#        Whether or not the coordinate is increasing.
#        
#:Examples:
#
#>>> c.array
#array([  0  30  60])
#>>> c._infer_direction()
#True
#>>> c.array
#array([15])
#>>> c.bounds.array
#array([  30  0])
#>>> c._infer_direction()
#False
#
#        '''
#        ndim = getattr(self, 'ndim', 2)
#        if ndim > 1:
#            return
#
#        if self.hasdata:
#            # Infer the direction from the dimension coordinate's data
#            # array
#            c = self.data
#            if c.size > 1:
#                c = c[0:2].array
#                return c.item(0,) < c.item(1,)
#        #--- End: if
#
#        # Still here? 
#        if self.hasbounds:
#            # Infer the direction from the dimension coordinate's
#            # bounds
#            b = self.bounds
#            if b.hasdata:
#                b = b.data
#                b = b[(0,)*(b.ndim-1)].array
#                return b.item(0,) < b.item(1,)
#        #--- End: if
#
#        # Still here? Then infer the direction from the units.
#        pressure = self.Units.ispressure
#        if pressure:
#            return True
#
#        return
#    #--- End: def
#
#    @property
#    def decreasing(self): 
#        '''
#
#True if the dimension coordinate is increasing, otherwise
#False.
#
#A dimension coordinate is increasing if its coordinate values are
#increasing in index space.
#
#The direction is inferred from one of, in order of precedence:
#
#* The data array
#* The bounds data array
#* The `units` CF property
#
#:Returns:
#
#    out : bool
#        Whether or not the coordinate is increasing.
#        
#True for dimension coordinate constructs, False otherwise.
#
#>>> c.decreasing
#False
#>>> c.flip().increasing
#True
#
#'''
#        direction = self._infer_direction()
#        if direction is False:
#            return True
#
#        return
#    #--- End: def
#
#    @property
#    def increasing(self): 
#        '''
#
#True for dimension coordinate constructs, False otherwise.
#
#>>> c.increasing
#True
#>>> c.flip().increasing
#False
#
#'''
#        direction = self._infer_direction()
#        if direction is True:
#            return True
#
#        return
#    #--- End: def

    @property
    def isboundedvariable(self): 
        '''True DCH

>>> c.isboundedvariable
True

'''
        return True
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute (a special attribute)
    # ----------------------------------------------------------------
    @property
    def bounds(self):
        '''

The `Bounds` object containing the cell bounds.

.. versionadded:: 2.0

.. seealso:: `lower_bounds`, `upper_bounds`

:Examples:

>>> c
<CF {+Variable}: latitude(64) degrees_north>
>>> c.bounds
<CF Bounds: latitude(64, 2) degrees_north>
>>> c.bounds = b
AttributeError: Can't set 'bounds' attribute. Consider the insert_bounds method.
>>> c.bounds.max()
<CF Data: 90.0 degrees_north>
>>> c.bounds -= 1
AttributeError: Can't set 'bounds' attribute. Consider the insert_bounds method.
>>> b = c.bounds
>>> b -= 1
>>> c.bounds.max()       
<CF Data: 89.0 degrees_north>

'''
        return self._get_special_attr('bounds')
    #--- End: def
    @bounds.setter
    def bounds(self, value):
        raise AttributeError(
            "Can't set 'bounds' attribute. Use the insert_bounds method.")
    #--- End: def
    @bounds.deleter
    def bounds(self):  
        self._del_special_attr('bounds')
        self._hasbounds = False
    #--- End: def

    def dump(self, display=True, omit=(), field=None, key=None,
             _level=0, _title=None): 
        '''Return a string containing a full description of the variable.

.. versionadded:: 1.6

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``c.dump()`` is equivalent to
        ``print c.dump(display=False)``.

    omit: sequence of `str`
        Omit the given CF properties from the description.

:Returns:

    out : None or str
        A string containing the description.

:Examples:

        '''
        string = super(AbstractBoundedArrayConstruct, self).dump(
            display=display,
            omit=omit,
            field=field,
            key=key,
            _level=_level,
            _title=_title)
        
        if self.hasbounds and self.bounds.hasdata::
            if field and key:
                x = ['{0}({1})'.format(field.domain_axis_name(axis),
                                       field.domain_axes()[axis].size)
                     for axis in field.construct_axes(key)]

                x.append(str(self.bounds.data.shape[self.data.ndim:]))
            else:
                x = [str(s) for s in self.bounds.data.shape]
                    
            bstring = '{0}Bounds({1}) = {2}'.format(indent1,
                                                    ', '.join(x),
                                                    str(self.bounds.data))
        #--- End: if

        if display:
            print bstring
        else:
            return string + '\n{0}'.format(bstring)
    #--- End: def

    def insert_bounds(self, bounds, copy=True):
        '''Insert cell bounds.

.. versionadded:: 1.6

.. seealso , `insert_data`, `remove_bounds`, `remove_data`

:Parameters:

    bounds: `Bounds`

    copy: `bool`, optional

:Returns:

    `None`

        '''
        if not getattr(bounds, 'isbounds', False):
            raise ValueError("bounds must be a 'Bounds' object")

        if copy:            
            bounds = bounds.copy()

        self._set_special_attr('bounds', bounds)        

        self._hasbounds = True
    #--- End: def

#    def direction(self):
#        '''Return True if the dimension coordinate values are increasing,
#otherwise return False.
#
#Dimension coordinates values are increasing if its coordinate values
#are increasing in index space.
#
#The direction is inferred from one of, in order of precedence:
#
#* The data array
#* The bounds data array
#* The `units` CF property
#
#:Returns:
#
#    out : bool
#        Whether or not the coordinate is increasing.
#        
#:Examples:
#
#>>> c.array
#array([  0  30  60])
#>>> c.direction()
#True
#
#>>> c.bounds.array
#array([  30  0])
#>>> c.direction()
#False
#
#        '''
#        return self._infer_direction()
#    #--- End: def

#--- End: class
