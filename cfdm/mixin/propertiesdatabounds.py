from __future__ import print_function
from builtins import (range, super)

from . import PropertiesData

from ..functions import RTOL, ATOL


class PropertiesDataBounds(PropertiesData):
    '''Mixin class for a data array with descriptive properties and cell
bounds.

.. versionadded:: 1.7.0

    '''
    def __init__(self, properties=None, data=None, bounds=None,
                 geometry=None, interior_ring=None, node_count=None,
                 part_node_count=None, source=None, copy=True,
                 _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

        *Parameter example:*
           ``properties={'standard_name': 'longitude'}``
        
        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.
  
    data: `Data`, optional
        Set the data array. Ignored if the *source* parameter is set.
        
        The data array may also be set after initialisation with the
        `set_data` method.
  
    bounds: `Bounds`, optional
        Set the bounds array. Ignored if the *source* parameter is
        set.
        
        The bounds array may also be set after initialisation with the
        `set_bounds` method.
  
    geometry: `str`, optional
        Set the geometry type. Ignored if the *source* parameter is
        set.
        
        *Parameter example:*
           ``geometry='polygon'``
        
        The geometry type may also be set after initialisation with
        the `set_geometry` method.
  
    interior_ring: `InteriorRing`, optional
        Set the interior ring variable. Ignored if the *source*
        parameter is set.
        
        The interior ring variable may also be set after
        initialisation with the `set_interior_ring` method.

    node_count: `NodeCount`, optional
        Set the node count variable for geometry bounds. Ignored if
        the *source* parameter is set.
        
        The node count variable may also be set after initialisation
        with the `set_node_count` method.
    
    part_node_count: `PartNodeCount`, optional
        Set the part node count variable for geometry bounds. Ignored
        if the *source* parameter is set.
        
        The part node count variable may also be set after
        initialisation with the `set_node_count` method.
    
    source: optional
        Initialize the properties, geometry type, data, bounds,
        interior ring variable, node count variable and part node
        count variable from those of *source*.
 
    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        # Initialise properties, data, geometry and interior ring
        super().__init__(properties=properties, data=data,
                         bounds=bounds, source=source,
                         geometry=geometry,
                         interior_ring=interior_ring, copy=copy,
                         _use_data=_use_data)

        # Get node count and part node count variables from source
        if source is not None:
            try:
                node_count = source.get_node_count(None)
            except AttributeError:
                node_count = None

            try:
                part_node_count = source.get_part_node_count(None)
            except AttributeError:
                part_node_count = None
        #--- End: if

        # Initialise node count
        if node_count is not None:
            self.set_node_count(node_count, copy=copy)
            
        # Initialise part node count
        if part_node_count is not None:
            self.set_part_node_count(part_node_count, copy=copy)
    #--- End: def

    def __getitem__(self, indices):
        '''Return a subspace of the construct defined by indices

f.__getitem__(indices) <==> f[indices]

The new subspace contains the same properties and similar components
to the original construct, but the latter are also subspaced over
their corresponding axes.

Indexing follows rules that are very similar to the numpy indexing
rules, the only differences being:

* An integer index i takes the i-th element but does not reduce the
  rank by one.

* When two or more dimensions' indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same
  behaviour as indexing on a Variable object of the netCDF4 package.

:Returns:

        The subspace of the construct.

**Examples:**

>>> f.data.shape
(1, 10, 9)
>>> f[:, :, 1].data.shape
(1, 10, 1)
>>> f[:, 0].data.shape
(1, 1, 9)
>>> f[..., 6:3:-1, 3:6].data.shape
(1, 3, 3)
>>> f[0, [2, 9], [4, 8]].data.shape
(1, 2, 2)
>>> f[0, :, -2].data.shape
(1, 10, 1)

        '''
        if indices is Ellipsis:
            return self.copy()

        if not isinstance(indices, tuple):
            indices = (indices,)

#        indices = parse_indices(self.shape, indices)

        new = super().__getitem__(indices)
        
#        data = self.get_data(None)
#
#        if data is not None:
#            new.set_data(data[indices], copy=False)

        # Subspace the bounds, if there are any.
        self_bounds = self.get_bounds(None)
        if self_bounds is not None:
            data = self_bounds.get_data(None)
            if data is not None:
                # There is a bounds array
                bounds_indices = list(indices)
                bounds_indices.append(Ellipsis)
                if data.ndim <= 1 and not self.has_geometry():
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
                #--- End: if

                new.set_bounds(self_bounds[tuple(bounds_indices)], copy=False)
#                new_bounds = new.get_bounds()
#                new_bounds.set_data(data[tuple(bounds_indices)], copy=False)
        #--- End: if

        # Subspace the interior ring array, if there are one.
        interior_ring = self.get_interior_ring(None)
        if interior_ring is not None:
            new.set_interior_ring(interior_ring[indices], copy=False)
#            data = interior_ring.get_data(None)
#            if data is not None:
#                new_interior_ring = new.get_interior_ring()
#                new_interior_ring.set_data(data[indices], copy=False)
        #--- End: if

        # Return the new bounded variable
        return new
    #--- End: def

    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

.. versionadded:: 1.7.0

        '''
        name = self.identity('')
        
        shape = None        
        data = self.get_data(None)
        bounds = self.get_bounds(None)
        if data is not None:
            shape = data.shape
        else:
            pass
#            bounds_data = bounds.get_data(None)
#            if bounds_data is not None:
#                shape = bounds_data.shape[:-1] # geometry TODO
        #--- End: if
        
        if shape is not None:        
            dims = ', '.join([str(x) for x in shape])
            dims = '({0})'.format(dims)
        else:
            dims = ''
        
#        data = self.get_data(None)
#        if data is not None:
#            dims = ', '.join([str(x) for x in data.shape])
#            dims = '({0})'.format(dims)
#        else:
#            bounds = self.get_bounds(None)
#            if bounds is not None:
#                data = bounds.get_data(None)
#                if data is not None:
#                    dims = ', '.join([str(x) for x in data.shape[:-1]])
#                    dims = '({0})'.format(dims)
#                else:
#                    dims = ''
#            else:
#                dims = ''
#        #--- End: if

        # ------------------------------------------------------------
        # Units and calendar
        # ------------------------------------------------------------
        
        units = self.get_property('units', None)
        if units is None and bounds is not None:
            units = bounds.get_property('units', None)
            
        calendar = self.get_property('calendar', None)
        if calendar is None and bounds is not None:
            calendar = bounds.get_property('calendar', None)

        if units is None:
            isreftime = (calendar is not None)
            units = ''
        else:
            isreftime = 'since' in units
                        
        if isreftime:
            if calendar is None:
                calendar = ''

            units += ' ' + calendar
            
        return '{0}{1} {2}'.format(self.identity(''), dims, units)
    #--- End: def
    
    def del_node_count(self, default=ValueError()):
        '''Remove the node count variable for geometry bounds.

.. versionadded:: 1.8.0

.. seealso:: `get_node_count`, `has_node_count`, `set_node_count`

:Parameters:

    default: optional
        Return the value of the *default* parameter if the node count
        variable has not been set. If set to an `Exception` instance
        then it will be raised instead.

:Returns:

        The removed node count variable.

**Examples:**

>>> n = cfdm.NodeCount(properties={'long_name': 'node counts'})
>>> c.set_node_count(n)
>>> c.has_node_count()
True
>>> c.get_node_count()
<NodeCount: long_name=node counts>
>>> c.del_node_count()
<NodeCount: long_name=node counts>
>>> c.has_node_count()
False

        '''
        try:
            return self._del_component('node_count')
        except ValueError:
            return self._default(default,
                                 "{!r} has no node count variable".format(self.__class__.__name__))
    #--- End: def
    
    def del_part_node_count(self, default=ValueError()):
        '''Remove the part node count variable for geometry bounds.

.. versionadded:: 1.8.0

.. seealso:: `get_part_node_count`, `has_part_node_count`,
             `set_part_node_count`

:Parameters:

    default: optional
        Return the value of the *default* parameter if the part node
        count variable has not been set. If set to an `Exception`
        instance then it will be raised instead.

:Returns:

        The removed part_node count variable.

**Examples:**

>>> p = cfdm.PartNodeCount(properties={'long_name': 'part node counts'})
>>> c.set_part_node_count(p)
>>> c.has_part_node_count()
True
>>> c.get_part_node_count()
<PartNodeCount: long_name=part node counts>
>>> c.del_part_node_count()
<PartNodeCount: long_name=part node counts>
>>> c.has_part_node_count()
False

        '''
        try:
            return self._del_component('part_node_count')
        except ValueError:
            return self._default(default,
                                 "{!r} has no part node count variable".format(self.__class__.__name__))
    #--- End: def

    def dump(self, display=True, _key=None, _omit_properties=None,
             _prefix='', _title=None, _create_title=True, _level=0,
             _axes=None, _axis_names=None):
        '''A full description.

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default

:Returns:

        The description. If *display* is True then the description is
        printed and `None` is returned. Otherwise the description is
        returned as a string.

        '''
        # ------------------------------------------------------------
        # Properties and Data
        # ------------------------------------------------------------
        string = super().dump(display=False, _key=_key,
                              _omit_properties=_omit_properties,
                              _prefix=_prefix, _title=_title,
                              _create_title=_create_title,
                              _level=_level, _axes=_axes,
                              _axis_names=_axis_names)

        string = [string]
        
        # ------------------------------------------------------------
        # Geometry type
        # ------------------------------------------------------------
        geometry = self.get_geometry(None)
        if geometry is not None:
            indent1 = '    ' * (_level + 1)
            string.append(
                '{0}{1}Geometry: {2}'.format(indent1, _prefix, geometry))

        # ------------------------------------------------------------
        # Bounds
        # ------------------------------------------------------------
        bounds = self.get_bounds(None)
        if bounds is not None:
            string.append(bounds.dump(display=False, _key=_key,
                                      _prefix=_prefix+'Bounds:',
                                      _create_title=False,
                                      _level=_level, _axes=_axes,
                                      _axis_names=_axis_names))

        #-------------------------------------------------------------
        # Interior ring
        # ------------------------------------------------------------
        interior_ring = self.get_interior_ring(None)
        if interior_ring is not None:
            string.append(interior_ring.dump(display=False, _key=_key,
                                             _prefix=_prefix+'Interior Ring:',
                                             _create_title=False,
                                             _level=_level, _axes=_axes,
                                             _axis_names=_axis_names))
            
        string = '\n'.join(string)
        
        if display:
            print(string)
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None, verbose=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_compression=False,
               ignore_type=False):
        '''Whether two instances are the same.

Equality is strict by default. This means that:

* the same descriptive properties must be present, with the same
  values and data types, and vector-valued properties must also have
  same the size and be element-wise equal (see the *ignore_properties*
  and *ignore_data_type* parameters), and

..

* if there are data arrays then they must have same shape and data
  type, the same missing data mask, and be element-wise equal (see the
  *ignore_data_type* parameter).

..

* if there are bounds then their descriptive properties (if any) must
  be the same and their data arrays must have same shape and data
  type, the same missing data mask, and be element-wise equal (see the
  *ignore_properties* and *ignore_data_type* parameters).

Two real numbers ``x`` and ``y`` are considered equal if
``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
differences) and ``rtol`` (the tolerance on relative differences) are
positive, typically very small numbers. See the *atol* and *rtol*
parameters.

If data arrays are compressed then the compression type and the
underlying compressed arrays must be the same, as well as the arrays
in their uncompressed forms. See the *ignore_compression* parameter.

Any type of object may be tested but, in general, equality is only
possible with another object of the same type, or a subclass of
one. See the *ignore_type* parameter.

NetCDF elements, such as netCDF variable and dimension names, do not
constitute part of the CF data model and so are not checked.

.. versionadded:: 1.7.0

:Parameters:


    other: 
        The object to compare for equality.

    atol: float, optional
        The tolerance on absolute differences between real
        numbers. The default value is set by the `cfdm.ATOL` function.
        
    rtol: float, optional
        The tolerance on relative differences between real
        numbers. The default value is set by the `cfdm.RTOL` function.

    ignore_fill_value: `bool`, optional
        If True then the "_FillValue" and "missing_value" properties
        are omitted from the comparison.

    verbose: `bool`, optional
        If True then print information about differences that lead to
        inequality.

    ignore_properties: sequence of `str`, optional
        The names of properties to omit from the comparison.

    ignore_data_type: `bool`, optional
        If True then ignore the data types in all numerical
        comparisons. By default different numerical data types imply
        inequality, regardless of whether the elements are within the
        tolerance for equality.

    ignore_compression: `bool`, optional
        If True then any compression applied to the underlying arrays
        is ignored and only the uncompressed arrays are tested for
        equality. By default the compression type and, if appliciable,
        the underlying compressed arrays must be the same, as well as
        the arrays in their uncompressed forms.

    ignore_type: `bool`, optional
        Any type of object may be tested but, in general, equality is
        only possible with another object of the same type, or a
        subclass of one. If *ignore_type* is True then equality is
        possible for any object with a compatible API.

:Returns: 
  
    `bool`
        Whether the two instances are equal.

**Examples:**

>>> p.equals(p)
True
>>> p.equals(p.copy())
True
>>> p.equals('not a colection of properties')
False

        '''    
        # ------------------------------------------------------------
        # Check the properties and data
        # ------------------------------------------------------------
        if not super().equals(other, rtol=rtol, atol=atol,
                              verbose=verbose,
                              ignore_data_type=ignore_data_type,
                              ignore_fill_value=ignore_fill_value,
                              ignore_properties=ignore_properties,
                              ignore_type=ignore_type,
                              ignore_compression=ignore_compression):
            if verbose:
                print("???????/")
            return False
    
        # ------------------------------------------------------------
        # Check the geometry type
        # ------------------------------------------------------------
        if self.get_geometry(None) != other.get_geometry(None):
            if verbose:
                print(
"{0}: Different geometry types: {1}, {2}".format(
    self.__class__.__name__, self.get_geometry(None), other.get_geometry(None)))
            return False

        # ------------------------------------------------------------
        # Check the bounds 
        # ------------------------------------------------------------
        self_has_bounds = self.has_bounds()
        if self_has_bounds != other.has_bounds():
            if verbose:
                print("{0}: Different {1}".format(self.__class__.__name__, attr))
            return False
                
        if self_has_bounds:            
            if not self._equals(self.get_bounds(), other.get_bounds(),
                                rtol=rtol, atol=atol,
                                verbose=verbose,
                                ignore_data_type=ignore_data_type,
                                ignore_type=ignore_type,
                                ignore_fill_value=ignore_fill_value,
                                ignore_compression=ignore_compression):
                if verbose:
                    print("{0}: Different {1}".format(self.__class__.__name__, attr))
                return False
        #--- End: if

        # ------------------------------------------------------------
        # Check the interior ring
        # ------------------------------------------------------------
        self_has_interior_ring = self.has_interior_ring()
        if self_has_interior_ring != other.has_interior_ring():
            if verbose:
                print("{0}: Different {1}".format(self.__class__.__name__, attr))
            return False
                
        if self_has_interior_ring:            
            if not self._equals(self.get_interior_ring(), other.get_interior_ring(),
                                rtol=rtol, atol=atol,
                                verbose=verbose,
                                ignore_data_type=ignore_data_type,
                                ignore_type=ignore_type,
                                ignore_fill_value=ignore_fill_value,
                                ignore_compression=ignore_compression):
                if verbose:
                    print("{0}: Different {1}".format(self.__class__.__name__, attr))
                return False
        #--- End: if

        return True
    #--- End: def

    def get_node_count(self, default=ValueError()):
        '''Return the node count variable for geometry bounds.

.. versionadded:: 1.8.0

.. seealso:: del_node_count`, `has_node_count`, `set_node_count`

:Parameters:

    default: optional
        Return the value of the *default* parameter if a node count
        variable has not been set. If set to an `Exception` instance
        then it will be raised instead.

:Returns:

        The node count variable.

**Examples:**

>>> n = cfdm.NodeCount(properties={'long_name': 'node counts'})
>>> c.set_node_count(n)
>>> c.has_node_count()
True
>>> c.get_node_count()
<NodeCount: long_name=node counts>
>>> c.del_node_count()
<NodeCount: long_name=node counts>
>>> c.has_node_count()
False

        '''
        try:
            return self._get_component('node_count')
        except ValueError:
            return self._default(default,
                    "{!r} has no node count variable".format(
                        self.__class__.__name__))
    #--- End: def

    def get_part_node_count(self, default=ValueError()):
        '''Return the part node count variable for geometry bounds.

.. versionadded:: 1.8.0

.. seealso:: `del_part_node_count`, `get_node_count`,
             `has_part_node_count`, `set_part_node_count`

:Parameters:

    default: optional
        Return the value of the *default* parameter if the part node
        count variable has not been set. If set to an `Exception`
        instance then it will be raised instead.

:Returns:

        The part node count variable.

**Examples:**

>>> p = cfdm.PartNodeCount(properties={'long_name': 'part node counts'})
>>> c.set_part_node_count(p)
>>> c.has_part_node_count()
True
>>> c.get_part_node_count()
<PartNodeCount: long_name=part node counts>
>>> c.del_part_node_count()
<PartNodeCount: long_name=part node counts>
>>> c.has_part_node_count()
False

        '''
        try:
            return self._get_component('part_node_count')
        except ValueError:
            return self._default(default,
                    "{!r} has no part node count variable".format(
                        self.__class__.__name__))
    #--- End: def

    def has_node_count(self):
        '''Whether or not there is a node count variable for geometry bounds..
        
.. versionadded:: 1.8.0

.. seealso:: `del_node_count`, `get_node_count`, `set_node_count`

:Returns:

    `bool`
        True if there is a node count variable, otherwise False.

**Examples:**


>>> n = cfdm.NodeCount(properties={'long_name': 'node counts'})
>>> c.set_node_count(n)
>>> c.has_node_count()
True
>>> c.get_node_count()
<NodeCount: long_name=node counts>
>>> c.del_node_count()
<NodeCount: long_name=node counts>
>>> c.has_node_count()
False

        '''
        return self._has_component('node_count')
    #--- End: def

    def has_part_node_count(self):
        '''Whether or not there is a part node count variable for geometry
bounds..
        
.. versionadded:: 1.8.0

.. seealso:: `del_part_node_count`, `get_part_node_count`,
             `set_part_node_count`

:Returns:

    `bool`
        True if there is a part node count variable, otherwise False.

**Examples:**

>>> p = cfdm.PartNodeCount(properties={'long_name': 'part node counts'})
>>> c.set_part_node_count(p)
>>> c.has_part_node_count()
True
>>> c.get_part_node_count()
<PartNodeCount: long_name=part node counts>
>>> c.del_part_node_count()
<PartNodeCount: long_name=part node counts>
>>> c.has_part_node_count()
False

        '''
        return self._has_component('part_node_count')
    #--- End: def

    def identities(self):
        '''Return all possible identities.

The identities comprise:

* The "standard_name" property.
* All properties, preceeded by the property name and a colon,
  e.g. ``'long_name:Air temperature'``.
* The netCDF variable name, preceeded by ``'ncvar%'``.
* The identities of the bounds, if any.

.. versionadded:: 1.7.0

.. seealso:: `identity`

:Returns:

    `list`
        The identities.

**Examples:**

>>> f.properties()
{'foo': 'bar',
 'long_name': 'Air Temperature',
 'standard_name': 'air_temperature'}
>>> f.nc_get_variable()
'tas'
>>> f.identities()
['air_temperature',
 'long_name=Air Temperature',
 'foo=bar',
 'standard_name=air_temperature',
 'ncvar%tas']

>>> f.properties()
{}
>>> f.bounds.properties()
{'axis': 'Z',
 'units': 'm'}
>>> f.identities()
['axis=Z', 'units=m', 'ncvar%z']

        '''
        identities = super().identities()
        
        bounds = self.get_bounds(None)
        if bounds is not None:
            identities.extend([i for i in bounds.identities()
                               if i not in identities])
            
        return identities
    #--- End: def

    def identity(self, default=''):
        '''Return the canonical identity.

By default the identity is the first found of the following:

1. The "standard_name" property.
2. The "cf_role" property, preceeded by ``'cf_role='``.
3. The "axis" property, preceeded by ``'axis='``.
4. The "long_name" property, preceeded by ``'long_name='``.
5. The netCDF variable name, preceeded by ``'ncvar%'``.
6. The identity of the bounds, if any.
7. The value of the *default* parameter.

.. versionadded:: 1.7.0

.. seealso:: `identities`

:Parameters:

    default: optional
        If no identity can be found then return the value of the
        default parameter.

:Returns:

        The identity.

**Examples:**

>>> f.properties()
{'foo': 'bar',
 'long_name': 'Air Temperature',
 'standard_name': 'air_temperature'}
>>> f.nc_get_variable()
'tas'
>>> f.identity()
'air_temperature'
>>> f.del_property('standard_name')
'air_temperature'
>>> f.identity(default='no identity')
'air_temperature'
>>> f.identity()
'long_name=Air Temperature'
>>> f.del_property('long_name')
>>> f.identity()
'ncvar%tas'
>>> f.nc_del_variable()
'tas'
>>> f.identity()
'ncvar%tas'
>>> f.identity()
''
>>> f.identity(default='no identity')
'no identity'

>>> f.properties()
{}
>>> f.bounds.properties()
{'axis': 'Z',
 'units': 'm'}
>>> f.identity()
'axis=Z'

        '''
        identity = super().identity(default=None)
        if identity is not None:
            return identity

        bounds = self.get_bounds(None)
        if bounds is not None:
            return bounds.identity(default=default)
        
        return default
    #--- End: def            
    
    def get_bounds(self, default=ValueError()):
        '''Return the bounds.

.. versionadded:: 1.7.0

.. seealso:: `bounds`, `get_data`, `del_bounds`, `has_bounds`,
             `set_bounds`

:Parameters:

    default: optional
        Return the value of the *default* parameter if bounds have not
        been set. If set to an `Exception` instance then it will be
        raised instead.

:Returns:

        The bounds.

**Examples:**

>>> b = cfdm.Bounds(data=cfdm.Data(range(10).reshape(5, 2)))
>>> c.set_bounds(b)
>>> c.has_bounds()
True
>>> c.get_bounds()
<Bounds: (5, 2) >
>>> b = c.del_bounds()
>>> b
<Bounds: (5, 2) >
>>> c.has_bounds()
False
>>> print(c.get_bounds(None))
None
>>> print(c.del_bounds(None))
None

        '''
        bounds = super().get_bounds(default=None)

        if bounds is None:
            return super().get_bounds(default=default)
        
        properties = self.properties()
        bounds_properties = bounds.properties()

        inherited_properties = {prop: value
                                for prop, value in properties.items()}

        bounds._set_component('inherited_properties', inherited_properties)
        
        return bounds
    #--- End: def

    def get_bounds_data(self, default=ValueError()):
        '''Return the bounds data.

.. versionadded:: 1.7.0

.. seealso:: `bounds`, `get_bounds`, `get_data`

:Parameters:

    default: optional
        Return the value of the *default* parameter if there are no
        bounds data. If set to an `Exception` instance then it will be
        raised instead.

:Returns:

        The bounds data.

**Examples:**

>>> c.get_bounds_data()
<Data(96, 2): [[0, ..., 360.0]] degrees_east>

        '''
        bounds = self.get_bounds(default=None)
        if bounds is None:
            return self.get_bounds(default=default)

        return bounds.get_data(default=default)
    #--- End: def

    def insert_dimension(self, position):
        '''Expand the shape of the data array.

Inserts a new size 1 axis into the data array. A corresponding axis is
also inserted into the bounds data array, if present.

.. versionadded:: 1.7.0

.. seealso:: `squeeze`, `transpose`

:Parameters:

    position: `int`, optional
        Specify the position that the new axis will have in the data
        array. By default the new axis has position 0, the slowest
        varying position. Negative integers counting from the last
        position are allowed.

        *Parameter example:*
          ``position=2``

        *Parameter example:*
          ``position=-1``

:Returns:

        The new construct with expanded data axes.

**Examples:**

>>> f.data.shape
(19, 73, 96)
>>> f.insert_dimension(position=3).data.shape
(96, 73, 19, 1)
>>> g = f.insert_dimension(position=-1)
>>> g.data.shape
(19, 73, 1, 96)
>>> f.bounds.data.shape
(19, 73, 96, 4)
>>> g.bounds.data.shape
(19, 73, 1, 96, 4)

        '''
        position = self._parse_axes([position])[0]
        
        c = super().insert_dimension(position)
        
        # ------------------------------------------------------------
        # Expand the dims of the bounds
        # ------------------------------------------------------------
        bounds = c.get_bounds(None)
        if bounds is not None:
            c.set_bounds(bounds.insert_dimension(position), copy=False)

        # ------------------------------------------------------------
        # Expand the dims of the interior_ring
        # ------------------------------------------------------------
        interior_ring = c.get_interior_ring(None)
        if interior_ring is not None:
            c.set_interior_ring(interior_ring.insert_dimension(position), copy=False)

        return c
    #--- End: def

    def set_node_count(self, node_count, copy=True):
        '''Set the node count variable for geometry bounds.

.. versionadded:: 1.8.0

.. seealso: `del_node_count`, `get_node_count`, `has_node_count`

:Parameters:

    node_count: `NodeCount`
        The node count variable to be inserted.

    copy: `bool`, optional
        If False then do not copy the node count variable prior to
        insertion. By default it is copied.

:Returns:

    `None`

**Examples:**

TODO

        '''
        if copy:
            node_count = node_count.copy()

        self._set_component('node_count', node_count, copy=False)
    #--- End: def

    def set_part_node_count(self, part_node_count, copy=True):
        '''Set the part node count variable for geometry bounds.

.. versionadded:: 1.8.0

.. seealso: `del_part_node_count`, `get_part_node_count`,
            `has_part_node_count`

:Parameters:

    part_node_count: `PartNodeCount`
        The part node count variable to be inserted.

    copy: `bool`, optional
        If False then do not copy the part node count variable prior
        to insertion. By default it is copied.

:Returns:

    `None`

**Examples:**

TODO

        '''
        if copy:
            part_node_count = part_node_count.copy()

        self._set_component('part_node_count', part_node_count, copy=False)
    #--- End: def

    def squeeze(self, axes=None):
        '''Remove size one axes from the data array.

By default all size one axes are removed, but particular size one axes
may be selected for removal. Corresponding axes are also removed from
the bounds data array, if present.

.. versionadded:: 1.7.0

.. seealso:: `insert_dimension`, `transpose`

:Parameters:

    axes: (sequence of) `int`
        The positions of the size one axes to be removed. By default
        all size one axes are removed. Each axis is identified by its
        original integer position. Negative integers counting from the
        last position are allowed.

        *Parameter example:*
          ``axes=0``

        *Parameter example:*
          ``axes=-2``

        *Parameter example:*
          ``axes=[2, 0]``

:Returns:

        The new construct with removed data axes.

**Examples:**

>>> f.data.shape
(1, 73, 1, 96)
>>> f.squeeze().data.shape
(73, 96)
>>> f.squeeze(0).data.shape
(73, 1, 96)
>>> g = f.squeeze([-3, 2])
>>> g.data.shape
(73, 96)
>>> f.bounds.data.shape
(1, 73, 1, 96, 4)
>>> g.data.shape
(73, 96, 4)

        '''
        axes = self._parse_axes(axes)

        c = super().squeeze(axes)

        # ------------------------------------------------------------
        # Squeeze the bounds
        # ------------------------------------------------------------
        bounds = c.get_bounds(None)
        if bounds is not None:
            c.set_bounds(bounds.squeeze(axes), copy=False)

        # ------------------------------------------------------------
        # Squeeze the interior_ring
        # ------------------------------------------------------------
        interior_ring = c.get_interior_ring(None)
        if interior_ring is not None:
            c.set_interior_ring(interior_ring.squeeze(axes), copy=False)

        return c
    #--- End: def
    
    def transpose(self, axes=None):
        '''Permute the axes of the data array.

Corresponding axes of the bounds data array, if present, are also
permuted.

Note that if i) the data array is two-dimensional, ii) the two axes
have been permuted, and iii) each cell has four bounds values; then
columns 1 and 3 (counting from 0) of the bounds axis are swapped to
preserve contiguity bounds in adjacent cells. See section 7.1 "Cell
Boundaries" of the CF conventions for details.

.. seealso:: `insert_dimension`, `squeeze`

:Parameters:

    axes: (sequence of) `int`
        The new axis order. By default the order is reversed. Each
        axis in the new order is identified by its original integer
        position. Negative integers counting from the last position
        are allowed.

        *Parameter example:*
          ``axes=[2, 0, 1]``

        *Parameter example:*
          ``axes=[-1, 0, 1]``

:Returns:

         The new construct with permuted data axes.

**Examples:**

>>> f.data.shape
(19, 73, 96)
>>> f.tranpose().data.shape
(96, 73, 19)
>>> g = f.tranpose([1, 0, 2])
>>> g.data.shape
(73, 19, 96)
>>> f.bounds.data.shape
(19, 73, 96, 4)
>>> g.bounds.data.shape
(73, 19, 96, 4)

        '''
        if axes is None:
            axes = list(range(ndim-1, -1, -1))
        else:
            axes = self._parse_axes(axes)

        # ------------------------------------------------------------
        # Transpose the coordinates
        # ------------------------------------------------------------        
        c = super().transpose(axes)

        # ------------------------------------------------------------
        # Transpose the bounds
        # ------------------------------------------------------------        
        data = c.get_bounds_data(None)
        if data is not None:
            b_axes = axes[:]
            b_axes.extend.extend(list(range(c.ndim, data.ndim)))
                
            bounds = c.get_bounds()
            bounds = bounds.transpose(b_axes)
            c.set_bounds(bounds, copy=False)
                
            if (c.ndim == 2 and data.ndim == 3 and data.shape[-1] == 4 and 
                b_axes[0:2] == [1, 0]):
                # Swap elements 1 and 3 of the trailing dimension so
                # that the values are still contiguous (if they ever
                # were). See section 7.1 of the CF conventions.
                data[:, :, slice(1, 4, 2)] = data[:, :, slice(3, 0, -2)]
                bounds.set_data(data, copy=False)
        #--- End: if

        a_axes = axes
        a_axes.append(-1)

        # ------------------------------------------------------------
        # Transpose the interior ring
        # ------------------------------------------------------------
        interior_ring = c.get_interior_ring(None)
        if interior_ring is not None:
            data = interior_ring.get_data(None)
            if data is not None:
                interior_ring_axes = axes[:]
                interior_ring_axes.extend(list(range(c.ndim, interior_ring.ndim)))
                interior_ring = interior_ring.transpose(interior_ring_axes)
                c.set_interior_ring(interior_ring, copy=False)
        #--- End: if
        
        return c
    #--- End: def

#--- End: class
