from __future__ import print_function
from builtins import (range, super)

from . import PropertiesData

from ..functions import RTOL, ATOL


class PropertiesDataBounds(PropertiesData):
    '''Mixin class for a data array with descriptive properties and cell
bounds.

    '''
    
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

    out:
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

#        # Parse the index
        if not isinstance(indices, tuple):
            indices = (indices,)

#        indices = parse_indices(self.shape, indices)

        new = super().__getitem__(indices)
        
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
             _create_title=True, _level=0, _axes=None,
             _axis_names=None):
        '''TODO Return a string containing a full description of the instance.

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
        string = super().dump(display=False, field=field, key=key,
                              _omit_properties=_omit_properties,
                              _prefix=_prefix, _title=_title,
                              _create_title=_create_title,
                              _level=_level, _axes=_axes,
                              _axis_names=_axis_names)

        string = [string]
        
        # ------------------------------------------------------------
        # Bounds
        # ------------------------------------------------------------
        bounds = self.get_bounds(None)
        if bounds is not None:
            string.append(bounds.dump(display=False, field=field,
                                      key=key,
                                      _prefix=_prefix+'Bounds:',
                                      _create_title=False,
                                      _level=_level, _axes=_axes,
                                      _axis_names=_axis_names))

        # ------------------------------------------------------------
        # Geometry type
        # ------------------------------------------------------------
        geometry = self.get_geometry(None)
        if geometry is not None:
            indent1 = '    ' * (_level + 1)
            string.append(
                '{0}{1}Geometry: {2}'.format(indent1, _prefix, geometry))

        #-------------------------------------------------------------
        # Interior ring
        # ------------------------------------------------------------
        interior_ring = self.get_interior_ring(None)
        if interior_ring is not None:
            string.append(interior_ring.dump(display=False,
                                             field=field, key=key,
                                             _prefix=_prefix+'Interior ring:',
                                             _create_title=False,
                                             _level=_level,
                                             _axes=_axes,
                                             _axis_names=_axis_names))
            
        string = '\n'.join(string)
        
        if display:
            print(string)
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_compression=False,
               ignore_type=False):
        '''Whether two data arrays with descriptive properties and cell bounds
are the same.

Equality is strict by default. This means that:

* the descriptive properties must be the same, and vector-valued
  properties must have same the size and be element-wise equal (see
  the *ignore_properties* parameter), and

..

* vector-valued properties must have same size and be element-wise
  equal,

..

* if there are data arrays then they must have same shape and data
  type, the same missing data mask, and be element-wise equal (see the
  *ignore_data_type* parameter).

..

* if there are bounds then their descriptive properties (if any) must
  be the same and their data arrays must have same shape and data
  type, the same missing data mask, and be element-wise equal (see the
  *ignore_properties* and *ignore_data_type* parameters).

Two numerical elements ``a`` and ``b`` are considered equal if
``|a-b|<=atol+rtol|b|``, where ``atol`` (the tolerance on absolute
differences) and ``rtol`` (the tolerance on relative differences) are
positive, typically very small numbers. See the *atol* and *rtol*
parameters.

If data arrays are compressed then the compression type and the
underlying compressed arrays must be the same, as well as the arrays
in their uncompressed forms. See the *ignore_compression* parameter.

Any type of object may be tested but, in general, equality is only
possible with another field construct, or a subclass of one. See the
*ignore_type* parameter.

NetCDF elements, such as netCDF variable and dimension names, do not
constitute part of the CF data model and so are not checked.

.. versionadded:: 1.7

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

    traceback: `bool`, optional
        If True then print information about differences that lead to
        inequality.

    ignore_properties: sequence of `str`, optional
        The names of properties to omit from the comparison.

    ignore_data_type: `bool`, optional
        If True then ignore the data types in all numerical data array
        comparisons. By default different numerical data types imply
        inequality, regardless of whether the elements are within the
        tolerance for equality.

    ignore_compression: `bool`, optional
        If True then any compression applied to the underlying arrays
        is ignored and only the uncompressed arrays are tested for
        equality. By default the compression type and, if appliciable,
        the underlying compressed arrays must be the same, as well as
        the arrays in their uncompressed forms

    ignore_type: `bool`, optional
         Any type of object may be tested but, in general, equality is
        only possible with another TODO, or a subclass of one. If
        *ignore_type* is True then then
        ``PropertiesDataBounds(source=other)`` is tested, rather than
        the ``other`` defined by the *other* parameter.

:Returns: 
  
    out: `bool`
        TODO

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
                              traceback=traceback,
                              ignore_data_type=ignore_data_type,
                              ignore_fill_value=ignore_fill_value,
                              ignore_properties=ignore_properties,
                              ignore_type=ignore_type,
                              ignore_compression=ignore_compression):
            if traceback:
                print("???????/")
            return False
    
        # ------------------------------------------------------------
        # Check the geometry type
        # ------------------------------------------------------------
        if self.get_geometry(None) != other.get_geometry(None):
            if traceback:
                print(
"{0}: Different geometry types: {1}, {2}".format(
    self.__class__.__name__, self.get_geometry(None), other.get_geometry(None)))
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
                                ignore_type=ignore_type,
                                ignore_fill_value=ignore_fill_value,
                                ignore_compression=ignore_compression):
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
                                ignore_type=ignore_type,
                                ignore_fill_value=ignore_fill_value,
                                ignore_compression=ignore_compression):
                if traceback:
                    print("{0}: Different {1}".format(self.__class__.__name__, attr))
                return False
        #--- End: if

        return True
    #--- End: def
    
    def del_part_ncdim(self):
        '''TODO
        '''        
        return self._del_component('part_ncdim')
    #--- End: def

    def expand_dims(self, position):
        '''Expand the shape of the data array.

Insert a new size 1 axis into the data array. A corresponding axis is
also inserted into the bounds data array, if present.

.. versionadded:: 1.7

.. seealso:: `squeeze`, `transpose`

:Parameters:

    position: `int`, optional
        Specify the position that the new axis will have in the data
        array. By default the new axis has position 0, the slowest
        varying position. Negative integers counting from the last
        position are allowed.

        *Example:*
          ``position=2``

        *Example:*
          ``position=-1``

:Returns:

    out:
        The new construct with expanded data axes.

**Examples:**

>>> f.data.shape
(19, 73, 96)
>>> f.expand_dims(position=3).data.shape
(96, 73, 19, 1)
>>> g = f.expand_dims(position=-1)
>>> g.data.shape
(19, 73, 1, 96)
>>> f.bounds.data.shape
(19, 73, 96, 4)
>>> g.bounds.data.shape
(19, 73, 1, 96, 4)

        '''
        position = self._parse_axes([position])[0]
        
        c = super().expand_dims(position)
        
        # ------------------------------------------------------------
        # Expand the dims of the bounds
        # ------------------------------------------------------------
        bounds = c.get_bounds(None)
        if bounds is not None:
            c.set_bounds(bounds.expand_dims(position), copy=False)

        # ------------------------------------------------------------
        # Expand the dims of the interior_ring
        # ------------------------------------------------------------
        interior_ring = c.get_interior_ring(None)
        if interior_ring is not None:
            c.set_interior_ring(interior_ring.expand_dims(position), copy=False)

        return c
    #--- End: def
    
    def get_node_ncdim(self, *default):
        '''TODO
        '''        
        return self._get_component('node_ncdim', *default)
    #--- End: def

    def get_part_ncdim(self, *default):
        '''TODO
        '''        
        return self._get_component('part_ncdim', *default)
    #--- End: def

    def has_part_ncdim(self):
        '''TODO
        '''        
        return self._has_component('part_ncdim')
    #--- End: def

    def set_node_ncdim(self, value):
        '''TODO Set the netCDF name of the dimension of a node coordinate variable.

        '''
        return self._set_component('node_ncdim', value)
    #--- End: def

    def set_part_ncdim(self, value):
        '''TODO Set the netCDF name of the dimension of the part_node_count
variable.

        '''
        return self._set_component('part_ncdim', value)
    #--- End: def

    def squeeze(self, axes=None):
        '''Remove size one axes from the data array.

By default all size one axes are removed, but particular size one axes
may be selected for removal. Corresponding axes are also removed from
the bounds data array, if present.

.. versionadded:: 1.7

.. seealso:: `expand_dims`, `transpose`

:Parameters:

    axes: (sequence of) `int`
        The positions of the size one axes to be removed. By default
        all size one axes are removed. Each axis is identified by its
        original integer position. Negative integers counting from the
        last position are allowed.

        *Example:*
          ``axes=0``

        *Example:*
          ``axes=-2``

        *Example:*
          ``axes=[2, 0]``

:Returns:

    out:
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
            c.set_bounds(interior_ring.squeeze(axes), copy=False)

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

.. seealso:: `expand_dims`, `squeeze`

:Parameters:

    axes: (sequence of) `int`
        The new axis order. By default the order is reversed. Each
        axis in the new order is identified by its original integer
        position. Negative integers counting from the last position
        are allowed.

        *Example:*
          ``axes=[2, 0, 1]``

        *Example:*
          ``axes=[-1, 0, 1]``

:Returns:

    out: 
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

        c = super().transpose(axes)

        # ------------------------------------------------------------
        # Transpose the bounds
        # ------------------------------------------------------------        
        bounds = c.get_bounds(None)
        if bounds is not None:
            data = bounds.get_data(None)
            if data is not None:            
                b_axes = axes[:]
                b_axes.extend.extend(list(range(c.ndim, data.ndim)))
                
                bounds = bounds.transpose(b_axes)
                c.set_bounds(bounds, copy=False)
                
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
            interior_ring_axes.extend(list(range(c.ndim, interior_ring.ndim)))
            c.set_interior_ring(interior_ring.transpose(interior_ring_axes),
                                copy=False)

        return c
    #--- End: def

#--- End: class
