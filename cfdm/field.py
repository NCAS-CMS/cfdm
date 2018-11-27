from __future__ import print_function
from builtins import (str, super, zip)
#primordial Kadavar - Come Back Life
import re
from . import mixin
from . import core

from . import Constructs
from . import Domain

_debug = False
       

class Field(mixin.NetCDFDataVariable,
            mixin.NetCDFVariable,
            mixin.ConstructAccess,
            mixin.PropertiesData,
            core.Field):
    '''A field construct of the CF data model.

The field construct is central to the CF data model, and includes all
the other constructs. A field corresponds to a CF-netCDF data variable
with all of its metadata. All CF-netCDF elements are mapped to a field
construct or some element of the CF field construct. The field
construct contains all the data and metadata which can be extracted
from the file using the CF conventions.

The field construct consists of a data array and the definition of its
domain (that describes the locations of each cell of the data array),
field ancillary constructs containing metadata defined over the same
domain, and cell method constructs to describe how the cell values
represent the variation of the physical quantity within the cells of
the domain. The domain is defined collectively by the following
constructs of the CF data model: domain axis, dimension coordinate,
auxiliary coordinate, cell measure, coordinate reference and domain
ancillary constructs.

The field construct also has optional properties to describe aspects
of the data that are independent of the domain. These correspond to
some netCDF attributes of variables (e.g. units, long_name and
standard_name), and some netCDF global file attributes (e.g. history
and institution).

.. versionadded:: 1.7

    '''
    def __new__(cls, *args, **kwargs):
        '''
        '''
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        instance._Domain     = Domain
        return instance
    #--- End: def

    def __init__(self, properties=None, source=None, copy=True,
                 _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

        *Example:*
           ``properties={'standard_name': 'air_temperature'}``
        
        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.

    source: optional
        Initialize the properties, data and metadata constructs from
        those of *source*.
        
    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''        
        # Initialize the new field with attributes and CF properties
        core.Field.__init__(self, properties=properties,
                            source=source, copy=copy,
                            _use_data=_use_data)
        
        self._initialise_netcdf(source)
    
        self._set_component('HDFgubbins', 'TO DO', copy=False)
    #--- End: def

    def __repr__(self):
        '''Called by the `repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__,
                                   self._one_line_description())
    #--- End: def

    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

        '''
        title = "Field: {0}".format(self.name(''))

        # Append the netCDF variable name
        ncvar = self.nc_get_variable(None)
        if ncvar is not None:
            title += " (ncvar%{0})".format(ncvar)
        
        string = [title]
        string.append(''.ljust(len(string[0]), '-'))

        # Units
        units = getattr(self, 'units', '')
        calendar = getattr(self, 'calendar', None)
        if calendar is not None:
            units += ' {0} {1}'.format(calendar)
            
        axis_name = self.domain_axis_name

        # Axes
        data_axes = self.get_data_axes(())
        non_spanning_axes = set(self.domain_axes()).difference(data_axes)

        axis_names = self._unique_domain_axis_names()
        
        # Data
        string.append(
            'Data            : {0}'.format(self._one_line_description(axis_names)))

        # Cell methods
        cell_methods = self.cell_methods()
        if cell_methods:
            x = []
            for cm in list(cell_methods.values()):
                cm = cm.copy()
                cm.set_axes(tuple([axis_names.get(axis, axis)
                                   for axis in cm.get_axes(())]))                
                x.append(str(cm))
                
            c = ' '.join(x)
            
            string.append('Cell methods    : {0}'.format(c))
        #--- End: if
        
        def _print_item(self, key, variable, dimension_coord):
            '''Private function called by __str__'''
            
            if dimension_coord:
                # Dimension coordinate
                axis = self.construct_axes(key)[0]
                name = variable.name(ncvar=True, default=key)
                if variable.has_data():
                    name += '({0})'.format(variable.get_data().size)
                elif hasattr(variable, 'nc_get_external'):
                    if variable.nc_get_external():
                        ncvar = variable.nc_get_variable(None)
                        if ncvar is not None:
                            x.append(' (external variable: ncvar%{})'.format(ncvar))
                        else:
                            x.append(' (external variable)')
                            
                if variable is None:
                    return name
                          
                x = [name]
                
            else:
                # Auxiliary coordinate
                # Cell measure
                # Field ancillary
                # Domain ancillary
                x = [variable.name(ncvar=True, default=key)]

                if variable.has_data():
                    shape = [axis_names[axis] for axis in self.construct_axes(key)]
                    shape = str(tuple(shape)).replace("'", "")
                    shape = shape.replace(',)', ')')
                    x.append(shape)
                elif hasattr(variable, 'nc_get_external'):
                    if variable.nc_get_external():
                        ncvar = variable.nc_get_variable(None)
                        if ncvar is not None:
                            x.append(' (external variable: ncvar%{})'.format(ncvar))
                        else:
                            x.append(' (external variable)')
            #--- End: if
                
            if variable.has_data():
                x.append(' = {0}'.format(variable.get_data()))
                
            return ''.join(x)
        #--- End: def
                          
        # Field ancillary variables
        x = [_print_item(self, key, anc, False)
             for key, anc in sorted(self.field_ancillaries().items())]
        if x:
            string.append('Field ancils    : {}'.format(
                '\n                : '.join(x)))

        

        string.append(str(self.domain))
#        x = []
#        for key in tuple(non_spanning_axes) + data_axes:
#            for dc_key, dim in list(self.dimension_coordinates().items()):
#                if self.construct_axes()[dc_key] == (key,):
#                    name = dim.name(default='id%{0}'.format(dc_key), ncvar=True)
#                    y = '{0}({1})'.format(name, dim.get_data().size)
#                    if y != axis_names[key]:
#                        y = '{0}({1})'.format(name, axis_names[key])
#                    if dim.has_data():
#                        y += ' = {0}'.format(dim.get_data())
#                        
#                    x.append(y)
#        #--- End: for
#        string.append('Dimension coords: {}'.format('\n                : '.join(x)))
#
#        # Auxiliary coordinates
#        x = [_print_item(self, aux, v, False) 
#             for aux, v in sorted(self.auxiliary_coordinates().items())]
#        if x:
#            string.append('Auxiliary coords: {}'.format(
#                '\n                : '.join(x)))
#        
#        # Cell measures
#        x = [_print_item(self, msr, v, False)
#             for msr, v in sorted(self.cell_measures().items())]
#        if x:
#            string.append('Cell measures   : {}'.format(
#                '\n                : '.join(x)))
#            
#        # Coordinate references
#        x = sorted([str(ref) for ref in list(self.coordinate_references().values())])
#        if x:
#            string.append('Coord references: {}'.format(
#                '\n                : '.join(x)))
#            
#        # Domain ancillary variables
#        x = [_print_item(self, cid, anc, False)
#             for cid, anc in sorted(self.domain_ancillaries().items())]
#        if x:
#            string.append('Domain ancils   : {}'.format(
#                '\n                : '.join(x)))
#                                      
        string.append('')
        
        return '\n'.join(string)
    #--- End def

    def __getitem__(self, indices):
        '''Return a subspace of the field defined by indices.

f.__getitem__(indices) <==> f[indices]

The new subspace contains the same properties and similar metadata
constructs to the original field, but the latter are also subspaced
when they span domain axis constructs that have been changed.

Indexing follows rules that are very similar to the numpy indexing
rules, the only differences being:

* An integer index i takes the i-th element but does not reduce the
  rank by one.

* When two or more dimensions' indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same
  behaviour as indexing on a Variable object of the netCDF4 package.

:Returns:

    out: `Field`
        The subspace of the field construct.

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
        data  = self.get_data()
        shape = data.shape

        indices = data.parse_indices(indices)
        indices = tuple(indices)
        
        new = self.copy(data=False)

        data_axes = new.get_data_axes()
        
        # Open any files that contained the original data (this not
        # necessary, is an optimsation)
        
        # ------------------------------------------------------------
        # Subspace the field's data
        # ------------------------------------------------------------
        new.set_data(data[tuple(indices)], data_axes)

        # ------------------------------------------------------------
        # Subspace other constructs that contain arrays
        # ------------------------------------------------------------
        self_constructs = self._get_constructs()
        for cid, construct in new.array_constructs().items():
            data = self.get_construct(cid=cid).get_data(None)
            if data is None:
                # This construct has no data
                continue

            needs_slicing = False
            dice = []
            for axis in new.construct_axes(cid):
                if axis in data_axes:
                    needs_slicing = True
                    dice.append(indices[data_axes.index(axis)])
                else:
                    dice.append(slice(None))
            #--- End: for

            if needs_slicing:
                new_data = data[tuple(dice)]
            else:
                new_data = data.copy()

            construct.set_data(new_data, copy=False)
        #--- End: for

        # Replace domain axes
        domain_axes = new.domain_axes()
        new_constructs = new._get_constructs()
        for cid, size in zip(data_axes, new.get_data().shape):
            domain_axis = domain_axes[cid].copy()
            domain_axis.set_size(size)
            new_constructs.replace(cid, domain_axis)

        return new
    #--- End: def

#    def _unique_construct_names(self, constructs):
#        '''
#
#        '''    
#        key_to_name = {}
#        name_to_keys = {}
#
#        for key, construct in getattr(self, constructs)().items():
#            name = construct.name(default='cfdm%'+key)
#            name_to_keys.setdefault(name, []).append(key)
#            key_to_name[key] = name
#
#        for name, keys in name_to_keys.items():
#            if len(keys) <= 1:
#                continue
#            
#            for key in keys:
#                key_to_name[key] = '{0}{{{1}}}'.format(
#                    name,
#                    re.findall('\d+$', key)[0])
#        #--- End: for
#        
#        return key_to_name
#    #--- End: def
    
#    def _unique_domain_axis_names(self):
#        '''
#        '''    
#        key_to_name = {}
#        name_to_keys = {}
#
#        for key, value in self.domain_axes().items():
#            name_size = (self.domain_axis_name(key), value.get_size(''))
#            name_to_keys.setdefault(name_size, []).append(key)
#            key_to_name[key] = name_size
#
#        for (name, size), keys in name_to_keys.items():
#            if len(keys) == 1:
#                key_to_name[keys[0]] = '{0}({1})'.format(name, size)
#            else:
#                for key in keys:                    
#                    key_to_name[key] = '{0}{{{1}}}({2})'.format(name,
#                                                                re.findall('\d+$', key)[0],
#                                                                size)
#        #--- End: for
#        
#        return key_to_name
#    #--- End: def
    
    def _one_line_description(self, axis_names_sizes=None):
        '''TODO'''
        if axis_names_sizes is None:
            axis_names_sizes = self._unique_domain_axis_names()
            
        x = [axis_names_sizes[axis] for axis in self.get_data_axes(())]
        axis_names = ', '.join(x)
        if axis_names:
            axis_names = '({0})'.format(axis_names)
            
        # Field units        
        units    = self.get_property('units', None)
        calendar = self.get_property('calendar', None)
        if units is not None:
            units = ' {0}'.format(units)
        else:
            units = ''
            
        if calendar is not None:
            units += ' {0}'.format(calendar)
            
        return "{0}{1}{2}".format(self.name(''), axis_names, units)
    #--- End: def

    def _dump_axes(self, axis_names, display=True, _level=0):
        '''TODO Return a string containing a description of the domain axes of the
field.
    
:Parameters:
    
    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed.
    
    _level: `int`, optional

:Returns:
    
    out: `str`
        A string containing the description.
    
**Examples:**

        '''
        indent1 = '    ' * _level
        indent2 = '    ' * (_level+1)

        data_axes = self.get_data_axes(())

        axes = self.domain_axes()

        w = sorted(["{0}Domain Axis: {1}".format(indent1, axis_names[axis])
                    for axis in axes
                    if axis not in data_axes])

        x = ["{0}Domain Axis: {1}".format(indent1, axis_names[axis])
             for axis in data_axes]

        string = '\n'.join(w+x)

        if display:
            print(string)
        else:
            return string
    #--- End: def


#    def domain_axis_name(self, key):
#        '''
#        '''
#        constructs = self._get_constructs()
#        return constructs.domain_axis_name(key)
#    #--- End: def

    def copy(self, data=True):
        '''Return a deep copy of the field construct.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.7

:Parameters:

    data: `bool`, optional
        If False then do not copy the data field construct, nor that
        of any of its metadata constructs. By default all data are
        copied.

:Returns:

    out:
        The deep copy.

**Examples:**

>>> g = f.copy()
>>> g = f.copy(data=False)
>>> g.has_data()
False

        '''
        new = super().copy(data=data)

        new.set_read_report(self.get_read_report({}))

        return new
    #--- End: def
    
    def dump(self, display=True, _level=0, _title=None):
        '''A full description of the field construct.

Returns a description of all properties, including those of metadata
constructs and their components, and provides selected values of all
data arrays.

.. versionadded:: 1.7

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed.

:Returns:

    out: `None` or `str`
        The description. If *display* is True then the description is
        printed and `None` is returned. Otherwise the description is
        returned as a string.

        '''
        indent = '    '      
        indent0 = indent * _level
        indent1 = indent0 + indent

        if _title is None:
            ncvar = self.nc_get_variable(None)
            _title = self.name(default=None)
            if ncvar is not None:
                if _title is None:
                    _title = "ncvar%{0}".format(ncvar)
                else:
                    _title += " (ncvar%{0})".format(ncvar)
            #--- End: if
            if _title is None:
                _title = ''
                
            _title = 'Field: {0}'.format(_title)
        #--- End: if

        line  = '{0}{1}'.format(indent0, ''.ljust(len(_title), '-'))

        # Title
        string = [line, indent0+_title, line]

        axis_to_name = self._unique_domain_axis_names()

        name = self._unique_construct_names()

        # Simple properties
        properties = self.properties()
        if properties:
           string.append(self._dump_properties(_level=_level))
               
        # Data
        data = self.get_data(None)
        if data is not None:
            x = [axis_to_name[axis] for axis in self.get_data_axes(())]

            units = self.get_property('units', None)
            if units is None:
                isreftime = bool(self.get_property('calendar', False))
            else:
                isreftime = 'since' in units
    
            if isreftime:
                data = data.asdata(data.get_dtarray())
                
            string.append('')
            string.append('{0}Data({1}) = {2}'.format(indent0,
                                                      ', '.join(x),
                                                      str(data)))
            string.append('')

        # Cell methods
        cell_methods = self.cell_methods()
        if cell_methods:
            for cm in list(cell_methods.values()):
                cm = cm.copy()
                cm.set_axes(tuple([axis_to_name.get(axis, axis)
                                   for axis in cm.get_axes(())]))
                string.append(cm.dump(display=False,  _level=_level))

            string.append('') 
        #--- End: if

        # Field ancillaries
        for key, value in sorted(self.field_ancillaries().items()):
            string.append(value.dump(display=False,
                                     _axes=self.construct_axes(key),
                                     _axis_names=axis_to_name,
                                     _level=_level))
            string.append('') 

        string.append(self.get_domain().dump(display=False))
        
        string = '\n'.join(string)
       
        if display:
            print(string)
        else:
            return string
    #--- End: def

#    def equal_datums(self, coordinate_reference0,
#                     coordinate_reference1, rtol=None, atol=None,
#                     traceback=False, ignore_data_type=False,
#                     ignore_fill_value=False,
#                     ignore_type=False):
#        '''
#        '''
#        coordinate_references = self.coordinate_references()
#        
#        datum0 = coordinate_references[coordinate_reference0].get_datum()
#        datum1 = coordinate_references[coordinate_reference1].get_datum()
#        
#    #--- End: def
    
    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_compression=False,
               ignore_type=False):
        '''Whether two field constructs are the same.

Equality is strict by default. This means that for two field
constructs to be considered equal they must have corresponding
metadata constructs and for each pair of constructs:

* the descriptive properties must be the same, and vector-valued
  properties must have same the size and be element-wise equal (see
  the *ignore_properties* parameter), and

..

* if there are data arrays then they must have same shape and data
  type, the same missing data mask, and be element-wise equal (see the
  *ignore_data_type* parameter).

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
constitute part of the CF data model and so are not checked on any
construct.

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
        are omitted from the comparison, for the field construct and
        metadata constructs.

    traceback: `bool`, optional
        If True then print information about differences that lead to
        inequality.

    ignore_properties: sequence of `str`, optional
        The names of properties of the field construct (not the
        metadata constructs) to omit from the comparison. Note that
        the "Conventions" property is always omitted by default.

    ignore_data_type: `bool`, optional
        If True then ignore the data types in all numerical data array
        comparisons. By default different numerical data types imply
        inequality, regardless of whether the elements are within the
        tolerance for equality.

    ignore_compression: `bool`, optional
        If True then any compression applied to underlying arrays is
        ignored and only uncompressed arrays are tested for
        equality. By default the compression type and, if appliciable,
        the underlying compressed arrays must be the same, as well as
        the arrays in their uncompressed forms

    ignore_type: `bool`, optional
        Any type of object may be tested but, in general, equality is
        only possible with another field construct, or a subclass of
        one. If *ignore_type* is True then then
        ``Field(source=other)`` is tested, rather than the ``other``
        defined by the *other* parameter.

:Returns: 
  
    out: `bool`
        Whether the two field constructs are equal.

**Examples:**

>>> f.equals(f)
True
>>> f.equals(f.copy())
True
>>> f.equals(f[...])
True
>>> f.equals('not a Field instance')
False

>>> g = f.copy()
>>> g.set_property('foo', 'bar')
>>> f.equals(g)
False
>>> f.equals(g, traceback=True)
Field: Non-common property name: foo
Field: Different properties
False

        '''
        ignore_properties = tuple(ignore_properties) + ('Conventions',)
            
        if not super().equals(
                other,
                rtol=rtol, atol=atol, traceback=traceback,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_properties=ignore_properties,
                ignore_compression=ignore_compression,
                ignore_type=ignore_type):
            return False

        # ------------------------------------------------------------
        # Check the constructs
        # ------------------------------------------------------------              
        if not self._equals(self._get_constructs(),
                            other._get_constructs(), rtol=rtol,
                            atol=atol, traceback=traceback,
                            ignore_data_type=ignore_data_type,
                            ignore_fill_value=ignore_fill_value,
                            ignore_compression=ignore_compression,
                            ignore_type=ignore_type):
            if traceback:
                print(
                    "{0}: Different {1}".format(self.__class__.__name__, 'constructs'))
            return False

        return True
    #--- End: def
        
    def expand_dims(self, axis, position=0):
        '''Expand the shape of the data array.

Insert a new size 1 axis, corresponding to an existing domain axis
construct, into the data array.

.. versionadded:: 1.7

.. seealso:: `squeeze`, `transpose`

:Parameters:

    axis: `str`
        The construct identifier of the domain axis construct
        corresponding to the inserted axis.

        *Example:*
          ``axis='domainaxis2'``

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

    out: `Field`
        The new field construct with expanded data axes.

**Examples:**

>>> f.data.shape
(19, 73, 96)
>>> f.expand_dims('domainaxis3').data.shape
(1, 96, 73, 19)
>>> f.expand_dims('domainaxis3', position=3).data.shape
(19, 73, 96, 1)
>>> f.expand_dims('domainaxis3', position=-1).data.shape
(19, 73, 1, 96)

        '''
        f = self.copy()
        
        domain_axis = self.domain_axes().get(axis)
        data_axes = list(self.get_data_axes(()))

        if domain_axis is None:
            raise ValueError("Can't insert non-existent domain axis: {}".format(axis))
        
        if domain_axis.get_size() != 1:
            raise ValueError(
"Can't insert an axis of size {}: {!r}".format(domain_axis.get_size(), axis))

        if axis in data_axes:
            raise ValueError(
                "Can't insert a duplicate data array axis: {!r}".format(axis))
       
        data_axes.insert(position, axis)
        f.set_data_axes(data_axes)

        # Expand the dims in the field's data array
        new_data = self.data.expand_dims(position)
        
        f.set_data(new_data, data_axes)

        return f
    #--- End: def

    def create_field(self, cid, domain=True):
        '''TODO

:Parameters:

    cid: `str`
        TODO

    domain: `bool`, optional
        TODO

:Returns:

    out: `Field`
        TODO

**Examples:**

TODO
        '''
        c = self.get_construct(cid=cid, copy=False)
    
        # ------------------------------------------------------------
        # Create a new field with the properties and data from the
        # construct
        # ------------------------------------------------------------
        f = type(self)(source=c, copy=True)

        # ------------------------------------------------------------
        # Add domain axes
        # ------------------------------------------------------------
        data_axes = self.construct_axes(cid)
        if data_axes:
            for domain_axis in data_axes:
                f.set_construct(self.domain_axes()[domain_axis],
                                cid=domain_axis, copy=True)
        #--- End: if

        # ------------------------------------------------------------
        # Set the data axes
        # ------------------------------------------------------------
        if data_axes is not None:
            f.set_data_axes(axes=data_axes)

        # ------------------------------------------------------------
        # Add a more complete domain
        # ------------------------------------------------------------
        if domain:
            for construct_type in ('dimensioncoordinate', 'auxiliarycoordinate', 'cellmeasure'):
                for ccid, con in self.constructs(construct_type=construct_type,
                                                 axes=data_axes,
                                                 copy=False).items():
                    axes = self.construct_axes().get(ccid)
                    if axes is None:
                        continue

                    if set(axes).issubset(data_axes):
                        f.set_construct(self.construct_type(ccid),
                                        con, cid=ccid, axes=axes,
                                        copy=True)
            #--- End: for
        
            # Add coordinate references which span a subset of the item's
            # axes
            for rcid, ref in self.coordinate_references().items():
                ok = True
                for ccid in (tuple(ref.coordinates()) +
                             tuple(ref.datum.ancillaries().values()),
                             tuple(ref.coordinate_conversion.ancillaries().values())):
                    axes = self.construct_axes()[ccid]
                    if not set(axes).issubset(data_axes):
                        ok = False
                        break
                #--- End: for
                
                if ok:
                    f.set_construct(ref, cid=rcid, copy=True)
            #--- End: for
        #--- End: if
              
        return f
    #--- End: def
    
#    def field_ancillaries(self, axes=None, copy=False):
#        '''TODO
#        '''
#        return self._get_constructs().constructs(
#            construct_type='field_ancillary',
#            axes=axes, copy=copy)
#    #--- End: def

    def get_read_report(self, *default):
        '''TODO
        '''
        return self._get_component('read_report', *default)
    #--- End: def
   
    def print_read_report(self, *default):
        '''TODO
        '''
        d = self.get_read_report({'dimensions': None, 
                                  'components': {}})
        
        for key0, value0 in d.items():
            print('{{{0!r}:'.format(key0))
            print('    dimensions: {0!r},'.format(value0['dimensions']))
            print('    components: {')
            for key1, value1 in sorted(value0['components'].items()):
                for x in value1:
                    print('        {!r}: ['.format(key1))
                    print('            {{{0}}},'.format(
                        '\n             '.join(['{0!r}: {1!r},'.format(key2, value2)
                                                for key2, value2 in sorted(x.items())])))
                #--- End: for
                print('        ],')
            #--- End: for
            print('    },')
            print('}\n')
        #--- End: for
    #--- End: def
   
    def set_read_report(self, value, copy=True):
        '''TODO
        '''
        self._set_component('read_report', value, copy=copy)
    #--- End: def    
   
    def squeeze(self, axes=None):
        '''Remove size one axes from the data array.

By default all size one axes are removed, but particular size one axes
may be selected for removal.

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

    out: `Field`
        The new field construct with removed data axes.

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
        f = self.copy()


        if axes is None:
            axes = [i for i, n in enumerate(f.data.shape) if n == 1]
        else:
            try:
                axes = self.data._parse_axes(axes)
            except ValueError as error:
                raise ValueError("Can't squeeze data: {}".format(error))

        data_axes = self.get_data_axes(())
        
#        domain_axes = self.domain_axes()
#            
#        if axes is None:
#            axes = [axis for axis in data_axes if domain_axes[axis].get_size(None) == 1]
#        else:
#            for axis in axes:
#                if domain_axes[axis].get_size() != 1:
#                    raise ValueError(
#"Can't squeeze domain axis with size {}".format(domain_axes[axis].get_size(None)))
#            #--- End: for
#            
#            axes = [axis for axis in axes if axis in data_axes]
#        #--- End: if

        new_data_axes = [data_axes[i] for i in range(self.data.ndim) if i not in axes]
        
#        new_data_axes = [axis for axis in data_axes if axis not in axes]
#        f.set_data_axes(new_data_axes)

        # Squeeze the field's data array
 #       iaxes = [data_axes.index(axis) for axis in axes]
        new_data = self.data.squeeze(axes)

        f.set_data(new_data, new_data_axes)

        return f
    #--- End: def

    def transpose(self, axes=None):
        '''Permute the axes of the data array.

.. versionadded:: 1.7

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

    out: `Field`
         The new field construct with permuted data axes.

**Examples:**

>>> f.data.shape
(19, 73, 96)
>>> f.tranpose().data.shape
(96, 73, 19)
>>> f.tranpose([1, 0, 2]).data.shape
(73, 19, 96)

        '''
        f = self.copy()
        try:
            axes = self.data._parse_axes(axes)
        except ValueError as error:
            raise ValueError("Can't transpose data: {}".format(error))

        data_axes = self.get_data_axes(())

        new_data_axes = [data_axes[i] for i in axes]
        
        # Transpose the field's data array
        new_data = self.data.transpose(axes)

        f.set_data(new_data, new_data_axes)

        return f
    #--- End: def

    def field_ancillaries(self, axes=None, copy=False):
        '''Return field ancillary constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    out: `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.field_ancillaries()
{}

>>> f.field_ancillaries()
{'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}

        '''
        return self._get_constructs().constructs(
            construct_type='field_ancillary', axes=axes, copy=copy)
    #--- End: def
    
    def cell_methods(self, copy=False):
        '''Return cell method constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`, `set_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    out: `collections.OrderDict`
        Constructs are returned as values of an ordered dictionary,
        keyed by their construct identifiers. The order is determined
        by the order in which the cell method constructs were added to
        the field construct.

**Examples:**

>>> f.cell_methods()
OrderedDict()

>>> f.cell_methods()
OrderedDict([('cellmethod0', <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>),
             ('cellmethod1', <CellMethod: domainaxis3: maximum>)])

        '''
        return self._get_constructs().constructs(
            construct_type='cell_method', copy=copy)
    #--- End: def
    
#    def cell_methods(self, copy=False):
#        '''
#        '''
#        out = self.Constructs.cell_methods(copy=copy)
#
#        if not description:
#            return self.Constructs.cell_methods()
#        
#        if not isinstance(description, (list, tuple)):
#            description = (description,)
#            
#        cms = []
#        for d in description:
#            if isinstance(d, dict):
#                cms.append([self._CellMethod(**d)])
#            elif isinstance(d, basestring):
#                cms.append(self._CellMethod.parse(d))
#            elif isinstance(d, self._CellMethod):
#                cms.append([d])
#            else:
#                raise ValueError("asd 123948u m  BAD DESCRIPTION TYPE")
#        #--- End: for
#
#        keys = self.cell_methods().keys()                    
#        f_cell_methods = self.cell_methods().values()
#        nf = len(f_cell_methods)
#
#        out = {}
#        
#        for d in cms:
#            c = self._conform_cell_methods(d)
#
#            n = len(c)
#            for j in range(nf-n+1):
#                found_match = True
#                for i in range(0, n):
#                    if not f_cell_methods[j+i].match(c[i].properties()):
#                        found_match = False
#                        break
#                #--- End: for
#            
#                if not found_match:
#                    continue
#
#                # Still here?
#                key = tuple(keys[j:j+n])
#                if len(key) == 1:
#                    key = key[0]
#
#                if key not in out:
#                    value = f_cell_methods[j:j+n]
#                    if copy:
#                    value = [cm.copy() for cm in value]                        
#
#                out[key] = value
#            #--- End: for
#        #--- End: for
#        
#        return out
#    #--- End: def

#    def set_cell_method(self, cell_method, cid=None, copy=True):
#        '''Set a cell method construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `CellMethod`
#        TODO
#        
#    cid: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``cid='cellmethod0'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples:**
#
#TODO
#
#        '''
#        self.set_construct(cell_method, cid=cid, copy=copy)
#    #--- End: def

#    def set_field_ancillary(self, construct, axes=None, cid=None,
#                            copy=True):
#        '''Set a field ancillary construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `FieldAncillary`
#        TODO
#
#    axes: sequence of `str`, optional
#        The identifiers of the domain axes spanned by the data array.
#
#        The axes may also be set afterwards with the
#        `set_construct_axes` method.
#
#        *Example:*
#          ``axes=['domainaxis0', 'domainaxis1']``
#
#    cid: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``cid='fieldancillary0'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples:**
#
#TODO
#        
#        '''
#        return self.set_construct(construct, cid=cid,
#                                  axes=axes, copy=copy)
#    #--- End: def
    
#--- End: class
