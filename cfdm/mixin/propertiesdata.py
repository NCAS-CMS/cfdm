from __future__ import print_function
from builtins import (str, super)

from . import Container
from . import Properties


class PropertiesData(Properties):
    '''Mixin class for a data array with descriptive properties.

.. versionadded:: 1.7.0

    '''
    def __getitem__(self, indices):
        '''Return a subspace defined by indices

f.__getitem__(indices) <==> f[indices]

Indexing follows rules that are very similar to the numpy indexing
rules, the only differences being:

* An integer index i takes the i-th element but does not reduce the
  rank by one.

* When two or more dimensions' indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same
  behaviour as indexing on a Variable object of the netCDF4 package.

:Returns:

        The subspace.

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
        new = self.copy(data=False)
        
        data = self.get_data(None)
        if data is not None:
            new.set_data(data[indices], copy=False)
        
        return new
    #--- End: def

    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

.. versionadded:: 1.7.0

        '''
        name = self.name('')

        data = self.get_data(None)
        if data is not None:
            dims = ', '.join([str(x) for x in data.shape])
            dims = '({0})'.format(dims)
        else:
            dims = ''

        # Units
        units = self.get_property('units', '')
        if units is None:
            isreftime = bool(self.get_property('calendar', False))
        else:
            isreftime = 'since' in units
            
        if isreftime:
            units += ' '+self.get_property('calendar', '')
            
        return '{0}{1} {2}'.format(self.name(''), dims, units)
    #--- End: def

    def dump(self, display=True, field=None, key=None,
             _omit_properties=(), _prefix='', _title=None,
             _create_title=True, _level=0, _axes=None,
             _axis_names=None):
        '''TODO

Return a string containing a full description of the instance.

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

    `None` or `str`
        A string containing the description. TODO

'''
        indent0 = '    ' * _level
        indent1 = '    ' * (_level+1)

        string = []

        # ------------------------------------------------------------
        # Title
        # ------------------------------------------------------------
        if _create_title:
            if _title is None:
                if field and key:
                    default = key
                else:
                    default = ''
                    
                string.append('{0}{1}: {2}'.format(indent0,
                                                   self.__class__.__name__,
                                                   self.name(default=default)))
            else:
                string.append(indent0 + _title)
        #--- End: if
        
        # ------------------------------------------------------------
        # Properties
        # ------------------------------------------------------------
        properties = self._dump_properties(_prefix=_prefix,
                                           _level=_level+1,
                                           _omit_properties=_omit_properties)
        if properties:
            string.append(properties)

        # ------------------------------------------------------------
        # Data
        # ------------------------------------------------------------
        data = self.get_data(None)
        if data is not None:
            if _axes and _axis_names:
                x = [_axis_names[axis] for axis in _axes]
                ndim = data.ndim
                x = x[:ndim]                    
                if len(x) < ndim:
                    x.extend([str(size) for size in data.shape[len(x):]])
            else:
                x = [str(size) for size in data.shape]

            shape = ', '.join(x)
            
            string.append('{0}{1}Data({2}) = {3}'.format(indent1,
                                                         _prefix,
                                                         shape,
                                                         str(data)))
        
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

>>> x.equals(x)
True
>>> x.equals(x.copy())
True
>>> x.equals('something else')
False

        '''
        pp = super()._equals_preprocess(other, verbose=verbose,
                                        ignore_type=ignore_type)
        if pp in (True, False):
            return pp
        
        other = pp

        # ------------------------------------------------------------
        # Check external variables (returning True if both are
        # external with the same netCDF variable name)
        # ------------------------------------------------------------
        external0 = self._get_component('external', False)
        external1 = other._get_component('external', False)
        if external0 != external1:
            if verbose:
                print("{0}: Only one external variable)".format(
                    self.__class__.__name__))
            return False
        elif external0:
            # Both variables are external
            if self.nc_get_variable(None) != other.nc_get_variable(None):
                if verbose:
                    print(
"{0}: External variable have different netCDF variable names: {} != {})".format(
    self.__class__.__name__, self.nc_get_variable(None), other.nc_get_variable(None)))
                return False

            return True
                
        # ------------------------------------------------------------
        # Check the properties
        # ------------------------------------------------------------
        if not super().equals(
                other, rtol=rtol, atol=atol,
                verbose=verbose,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_properties=ignore_properties,
                ignore_type=ignore_type):
            if verbose:
                print(
"{0}: Different properties".format(self.__class__.__name__))
            return False

        # ------------------------------------------------------------
        # Check the data
        # ------------------------------------------------------------
        if self.has_data() != other.has_data():
            if verbose:
                print(
"{0}: Different data: Only one {0} has data".format(self.__class__.__name__))
            return False
            
        if self.has_data():
            if not self._equals(self.get_data(), other.get_data(),
                                rtol=rtol, atol=atol,
                                verbose=verbose,
                                ignore_data_type=ignore_data_type,
                                ignore_fill_value=ignore_fill_value,
                                ignore_compression=ignore_compression):
                if verbose:
                    print("{0}: Different data".format(self.__class__.__name__))
                return False
        #--- End: if

        return True
    #--- End: def

    def insert_dimension(self, position=0):
        '''Expand the shape of the data array.

Inserts a new size 1 axis into the data array.

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

        A new instance with expanded data axes.

**Examples:**

>>> f.data.shape
(19, 73, 96)
>>> f.insert_dimension(position=3).data.shape
(19, 73, 96, 1)
>>> f.insert_dimension(position=-1).data.shape
(19, 73, 1, 96)

        '''       
        v = self.copy()

        data = v.get_data(None)
        if data is not None:
            v.set_data(data.insert_dimension(position))
        
        return v
    #--- End: def
    
#    def HDF_chunks(self, *chunksizes):
#        '''TODO {+HDF_chunks}
#        
#.. versionadded:: 1.6
#
#:Parameters:
#
#    {+chunksizes}
#
#:Returns:
#
#    `dict`
#        The chunk sizes prior to the new setting, or the current
#        current sizes if no new values are specified.
#
#        '''
#        if self.has_data():
#            old_chunks = self.get_data().HDF_chunks(*chunksizes)
#        else:
#            old_chunks = None
#
##        if self.hasbounds:
##            self.bounds.HDF_chunks(*chunksizes)
#
#        return old_chunks
#    #--- End: def

    def name(self, default=None, ncvar=True, custom=None,
             all_names=False):
        '''Return a name.

By default the name is the first found of the following:

1. The "standard_name" property.
2. The "cf_role" property, preceeded by ``'cf_role:'``.
3. The "long_name" property, preceeded by ``'long_name:'``.
4. The netCDF variable name, preceeded by ``'ncvar%'``.
5. The value of the *default* parameter.

.. versionadded:: 1.7.0

:Parameters:

    default: optional
        If no other name can be found then return the value of the
        *default* parameter. By default `None` is returned in this
        case.

    ncvar: `bool`, optional
        If False then do not consider the netCDF variable name.

    all_names: `bool`, optional
        If True then return a list of all possible names.

    custom: sequence of `str`, optional
        Replace the ordered list of properties from which to seatch
        for a name. The default list is ``['standard_name', 'cf_role',
        'long_name']``.

        *Parameter example:*
          ``custom=['project']``

        *Parameter example:*
          ``custom=['project', 'long_name']``

:Returns:

        The name. If the *all_names* parameter is True then a list of
        all possible names.

**Examples:**

>>> f.properties()
{'foo': 'bar',
 'long_name': 'Air Temperature',
 'standard_name': 'air_temperature'}
>>> f.nc_get_variable()
'tas'
>>> f.name()
'air_temperature'
>>> f.name(all_names=True)
['air_temperature', 'long_name:Air Temperature', 'ncvar:tas']
>>> x = f.del_property('standard_name')
>>> f.name()
'long_name:Air Temperature'
>>> x = f.del_property('long_name')
>>> f.name()
'ncvar:tas'
>>> f.name(custom=['foo'])
'foo:bar'
>>> f.name(default='no name', custom=['foo'])
['foo:bar', 'no name']

        '''
        out = []

        if custom is None:
            n = self.get_property('standard_name', None)
            if n is not None:
                out.append(n)

            custom = ('cf_role', 'long_name')
            
        if all_names or not out:
            for prop in custom:
                n = self.get_property(prop, None)
                if n is not None:
                    out.append('{0}:{1}'.format(prop, n))
                    if not all_names:
                        break
        #--- End: if
        
        if ncvar and (all_names or not out):
            n = self.nc_get_variable(None)
            if n is not None:
                out.append('ncvar%{0}'.format(n))
        #--- End: if

        if all_names:
            if default is not None:
                out.append(default)
                
            return out
        
        if out:
            return out[-1]

        return default
    #--- End: def

    def squeeze(self, axes=None):
        '''Remove size one axes from the data array.

By default all size one axes are removed, but particular size one axes
may be selected for removal.

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

        A new instance with removed data axes.

**Examples:**

>>> f.data.shape
(1, 73, 1, 96)
>>> f.squeeze().data.shape
(73, 96)
>>> f.squeeze(0).data.shape
(73, 1, 96)
>>> f.squeeze([-3, 2]).data.shape
(73, 96)

        '''
        v = self.copy()

        data = v.get_data(None)
        if data is not None:
            v.set_data(data.squeeze(axes))

        return v
    #--- End: def

    def transpose(self, axes=None):
        '''Permute the axes of the data array.

.. versionadded:: 1.7.0

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

         A new instance with permuted data axes.

**Examples:**

>>> f.data.shape
(19, 73, 96)
>>> f.tranpose().data.shape
(96, 73, 19)
>>> f.tranpose([1, 0, 2]).data.shape
(73, 19, 96)

        '''       
        v = self.copy()

        data = v.get_data(None)
        if data is not None:
            v.set_data(data.transpose(axes))
        
        return v
    #--- End: def
    
    def _parse_axes(self, axes): #, ndim=None):
        '''TODO
        '''
        if axes is None:
            return axes

        ndim = self.data.ndim
        
        if isinstance(axes, (int, int)):
            axes = (axes,)
            
        return [(i + ndim if i < 0 else i) for i in axes]
    #--- End: def
    
#--- End: class
