from .functions import parse_indices
from .variable  import Variable

_debug = False

# ====================================================================
#
# CFDM Bounded variable object
#
# ====================================================================

class BoundedVariable(Variable):
    '''Base class for CF dimension coordinate, auxiliary coordinate and
domain ancillary objects.
    '''
    def __init__(self, properties={}, attributes={}, data=None,
                 bounds=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Initialize a new instance with CF properties from a
        dictionary's key/value pairs.
  
    attributes: `dict`, optional
        Provide the new instance with attributes from a dictionary's
        key/value pairs.
  
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
                                              attributes=attributes,
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
    
    def _infer_direction(self):
        '''Return True if a coordinate is increasing, otherwise return False.

A coordinate is considered to be increasing if its *raw* data array
values are increasing in index space or if it has no data not bounds
data.

If the direction can not be inferred from the coordinate's data then
the coordinate's units are used.

The direction is inferred from the coordinate's data array values or
its from coordinates. It is not taken directly from its `Data` object.

:Returns:

    out : bool
        Whether or not the coordinate is increasing.
        
:Examples:

>>> c.array
array([  0  30  60])
>>> c._infer_direction()
True
>>> c.array
array([15])
>>> c.bounds.array
array([  30  0])
>>> c._infer_direction()
False

        '''
        ndim = getattr(self, 'ndim', 2)
        if ndim > 1:
            return

        if self.hasdata:
            # Infer the direction from the dimension coordinate's data
            # array
            c = self.data
            if c.size > 1:
                c = c[0:2].array
                return c.item(0,) < c.item(1,)
        #--- End: if

        # Still here? 
        if self.hasbounds:
            # Infer the direction from the dimension coordinate's
            # bounds
            b = self.bounds
            if b.hasdata:
                b = b.data
                b = b[(0,)*(b.ndim-1)].array
                return b.item(0,) < b.item(1,)
        #--- End: if

        # Still here? Then infer the direction from the units.
        pressure = self.Units.ispressure
        if pressure:
            return True

        return
    #--- End: def

    @property
    def decreasing(self): 
        '''

True if the dimension coordinate is increasing, otherwise
False.

A dimension coordinate is increasing if its coordinate values are
increasing in index space.

The direction is inferred from one of, in order of precedence:

* The data array
* The bounds data array
* The `units` CF property

:Returns:

    out : bool
        Whether or not the coordinate is increasing.
        
True for dimension coordinate constructs, False otherwise.

>>> c.decreasing
False
>>> c.flip().increasing
True

'''
        direction = self._infer_direction()
        if direction is False:
            return True

        return
    #--- End: def

    @property
    def increasing(self): 
        '''

True for dimension coordinate constructs, False otherwise.

>>> c.increasing
True
>>> c.flip().increasing
False

'''
        direction = self._infer_direction()
        if direction is True:
            return True

        return
    #--- End: def

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

    # ----------------------------------------------------------------
    # Attribute
    # ----------------------------------------------------------------
    @property
    def dtype(self):
        '''Numpy data-type of the data array.

.. versionadded:: 2.0 

:Examples:

>>> c.dtype
dtype('float64')
>>> import numpy
>>> c.dtype = numpy.dtype('float32')

        '''
        if self.hasdata:
            return self.data.dtype
        
        if self.hasbounds:
            return self.bounds.dtype

        raise AttributeError("{} does not have attribute 'dtype'".format(
            self.__class__.__name__))
    #--- End: def
    @dtype.setter
    def dtype(self, value):
        if self.hasdata:
            self.data.dtype = value

        if self.hasbounds:
            self.bounds.dtype = value
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute
    # ----------------------------------------------------------------
    @property
    def Units(self):
        '''

The Units object containing the units of the data array.

.. versionadded:: 2.0 

'''
        return Variable.Units.fget(self)
    #--- End: def

    @Units.setter
    def Units(self, value):
        Variable.Units.fset(self, value)

        # Set the Units on the bounds
        if self.hasbounds:
            self.bounds.Units = value
    #--- End: def
    @Units.deleter
    def Units(self):
        Variable.Units.fdel(self)
        
        if self.hasbounds:
            # Delete the bounds' Units
            del self.bounds.Units
    #--- End: def

    # ----------------------------------------------------------------
    # CF property: calendar
    # ----------------------------------------------------------------
    @property
    def calendar(self):
        '''

The calendar CF property.

This property is a mirror of the calendar stored in the `Units`
attribute.

.. versionadded:: 2.0 

:Examples:

>>> c.calendar = 'noleap'
>>> c.calendar
'noleap'
>>> del c.calendar

>>> c.setprop('calendar', 'proleptic_gregorian')
>>> c.getprop('calendar')
'proleptic_gregorian'
>>> c.delprop('calendar')

'''
        return Variable.calendar.fget(self)
    #--- End: def

    @calendar.setter
    def calendar(self, value):
        Variable.calendar.fset(self, value)
        # Set the calendar of the bounds
        if self.hasbounds:
            self.bounds.setprop('calendar', value)
    #--- End: def

    @calendar.deleter
    def calendar(self):
        Variable.calendar.fdel(self)
        # Delete the calendar of the bounds
        if self.hasbounds:
            try:
                self.bounds.delprop('calendar')
            except AttributeError:
                pass
    #--- End: def

    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def standard_name(self):
        '''

The standard_name CF property.

.. versionadded:: 2.0 

:Examples:

>>> c.standard_name = 'time'
>>> c.standard_name
'time'
>>> del c.standard_name

>>> c.setprop('standard_name', 'time')
>>> c.getprop('standard_name')
'time'
>>> c.delprop('standard_name')

'''
        return self.getprop('standard_name')
    #--- End: def
    @standard_name.setter
    def standard_name(self, value): 
        self.setprop('standard_name', value)
    @standard_name.deleter
    def standard_name(self):       
        self.delprop('standard_name')

    # ----------------------------------------------------------------
    # CF property: units
    # ----------------------------------------------------------------
    # DCH possible inconsistency when setting self.Units.units ??
    @property
    def units(self):
        '''

The units CF property.

This property is a mirror of the units stored in the `Units`
attribute.

.. versionadded:: 2.0 

:Examples:

>>> c.units = 'degrees_east'
>>> c.units
'degree_east'
>>> del c.units

>>> c.setprop('units', 'days since 2004-06-01')
>>> c.getprop('units')
'days since 2004-06-01'
>>> c.delprop('units')

'''
        return Variable.units.fget(self)
    #--- End: def

    @units.setter
    def units(self, value):
        Variable.units.fset(self, value)

        if self.hasbounds:
            # Set the units on the bounds        
            self.bounds.setprop('units', value)

#        self._direction = None
    #--- End: def
    
    @units.deleter
    def units(self):
        Variable.units.fdel(self)

        if self.hasbounds:
            # Delete the units from the bounds
            try:                
                self.bounds.delprop('units')
            except AttributeError:
                pass
    #--- End: def

    def delprop(self, prop):
        '''

Delete a CF property.

.. versionadded:: 2.0 

.. seealso:: `getprop`, `hasprop`, `setprop`

:Parameters:

    prop : str
        The name of the CF property.

:Returns:

     None

:Examples:

>>> c.delprop('standard_name')
>>> c.delprop('foo')
AttributeError: {+Variable} doesn't have CF property 'foo'

'''
        # Delete a special attribute
        if prop in self._special_properties:
            delattr(self, prop)
            return

        # Still here? Then delete a simple attribute

        # Delete selected simple properties from the bounds
        if self.hasbounds and prop in ('standard_name', 'axis', 'positive',
                                       'leap_month', 'leap_year',
                                       'month_lengths'):
            try:
                self.bounds.delprop(prop)
            except AttributeError:
                pass
        #--- End: if

        d = self._private['simple_properties']
        if prop in d:
            del d[prop]
        else:
            raise AttributeError("Can't delete non-existent %s CF property %r" %
                                 (self.__class__.__name__, prop))
    #--- End: def

    def dump(self, display=True, omit=(), field=None, key=None,
             _level=0, _title=None): 
        '''

Return a string containing a full description of the variable.

.. versionadded:: 2.0 

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
        indent0 = '    ' * _level
        indent1 = '    ' * (_level+1)

        if _title is None:
            string = ['{0}Bounded Variable: {1}'.format(indent0, self.name(''))]
        else:
            string = [indent0 + _title]

        if self._simple_properties():
            string.append(self._dump_simple_properties(_level=_level+1))

        if self.hasdata:
            if field and key:
                x = ['{0}({1})'.format(field.axis_name(axis), field.axis_size(axis))
                     for axis in field.item_axes(key)]
            else:
                x = [str(s) for s in self.shape]

            string.append('{0}Data({1}) = {2}'.format(indent1,
                                                      ', '.join(x),
                                                      str(self.data)))
        #--- End: if

        if self.hasbounds:
            x.append(str(self.bounds.shape[-1]))
            string.append('{0}Bounds({1}) = {2}'.format(indent1,
                                                        ', '.join(x),
                                                        str(self.bounds.data)))
        string = '\n'.join(string)
       
        if display:
            print string
        else:
            return string
    #--- End: def

    def insert_bounds(self, bounds, copy=True):
        '''Insert cell bounds.

.. versionadded:: 1.6

:Parameters:

    bounds:  data-like

        {+data-like}

    copy: `bool`, optional

:Returns:

    `None`

        '''
        if not getattr(bounds, 'isbounds', False):
            raise ValueError("bounds must be Bounds")

        # Check dimensionality
        if bounds.ndim != self.ndim + 1:
            raise ValueError(
"Can't set bounds: Incorrect number of dimemsions: {0} (expected {1})".format(
    bounds.ndim, self.ndim+1))

        # Check shape
        if bounds.shape[:-1] != self.shape:
            raise ValueError(
                "Can't set bounds: Incorrect shape: {0} (expected {1})".format(
                    bounds.shape, self.shape+(bounds.shape[-1],)))

        if copy:            
            bounds = bounds.copy()

        # Check units
        units      = bounds.Units
        self_units = self.Units
        if units and not units.equivalent(self_units):
            raise ValueError(
"Can't set bounds: Incompatible units: {!r} (not equivalent to {!r})".format(
    bounds.Units, self.Units))
            
        bounds.Units = self_units

        # Copy selected properties to the bounds
        for prop in ('standard_name', 'axis', 'positive',
                     'leap_months', 'leap_years', 'month_lengths'):
            value = self.getprop(prop, None)
            if value is not None:
                bounds.setprop(prop, value)

        self._set_special_attr('bounds', bounds)        

        self._hasbounds = True
#        self._direction = None
    #--- End: def

    def insert_data(self, data, bounds=None, copy=True):
        '''Insert a new data array.

A bounds data array may also inserted if given with the *bounds*
keyword. Bounds may also be inserted independently with the
`insert_bounds` method.

.. versionadded:: 1.6

.. seealso `insert_bounds`, `remove_data`

:Parameters:

    data: `Data`

    bounds: `Data`, optional

    copy: `bool`, optional

:Returns:

    `None`

        '''
        if data is not None:
            super(BoundedVariable, self).insert_data(data, copy=copy)

        if bounds is not None:
            self.insert_bounds(bounds, copy=copy)
    #--- End: def

    def direction(self):
        '''Return True if the dimension coordinate values are increasing,
otherwise return False.

Dimension coordinates values are increasing if its coordinate values
are increasing in index space.

The direction is inferred from one of, in order of precedence:

* The data array
* The bounds data array
* The `units` CF property

:Returns:

    out : bool
        Whether or not the coordinate is increasing.
        
:Examples:

>>> c.array
array([  0  30  60])
>>> c.direction()
True

>>> c.bounds.array
array([  30  0])
>>> c.direction()
False

        '''
        return self._infer_direction()
    #--- End: def

    def setprop(self, prop, value):
        '''Set a CF property.

.. versionadded:: 1.6

.. seealso:: `delprop`, `getprop`, `hasprop`

:Parameters:

    prop : str
        The name of the CF property.

    value :
        The value for the property.

:Returns:

     None

:Examples:

>>> c.setprop('standard_name', 'time')
>>> c.setprop('foo', 12.5)

        '''
        # Set a special attribute
        if prop in self._special_properties:
            setattr(self, prop, value)
            return

        # Still here? Then set a simple property
        self._private['simple_properties'][prop] = value

        # Set selected simple properties on the bounds
        if self.hasbounds and prop in ('standard_name', 'axis', 'positive', 
                                       'leap_month', 'leap_year',
                                       'month_lengths'):
            self.bounds.setprop(prop, value)
    #--- End: def

#--- End: class
