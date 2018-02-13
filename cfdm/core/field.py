import abc

import mixin

from .constructs import Constructs
#from .domain      import Domain
from .functions import RTOL, ATOL
from .functions import equals as cfdm_equals

from ..structure import Field as structure_Field


_debug = False
       

# ====================================================================
#
# Field object
#
# ====================================================================

class Field(structure_Field, mixin.PropertiesData):
    '''A CF field construct.

The field construct is central to the CF data model, and includes all
the other constructs. A field corresponds to a CF-netCDF data variable
with all of its metadata. All CF-netCDF elements are mapped to some
element of the CF field construct and the field constructs completely
contain all the data and metadata which can be extracted from the file
using the CF conventions.

The field construct consists of a data array (stored in a `Data`
object) and the definition of its domain, ancillary metadata fields
defined over the same domain (stored in `FieldAncillary` objects), and
cell methods constructs to describe how the cell values represent the
variation of the physical quantity within the cells of the domain
(stored in `CellMethod` objects).

The domain is defined collectively by various other constructs
included in the field:

====================  ================================================
Domain construct      Description
====================  ================================================
Domain axis           Independent axes of the domain stored in
                      `DomainAxis` objects

Dimension coordinate  Domain cell locations stored in
                      `DimensionCoordinate` objects

Auxiliary coordinate  Domain cell locations stored in
                      `AuxiliaryCoordinate` objects

Coordinate reference  Domain coordinate systems stored in
                      `CoordinateReference` objects

Domain ancillary      Cell locations in alternative coordinate systems
                      stored in `DomainAncillary` objects

Cell measure          Domain cell size or shape stored in
                      `CellMeasure` objects
====================  ================================================

All of the constructs contained by the field construct are optional.

The field construct also has optional properties to describe aspects
of the data that are independent of the domain. These correspond to
some netCDF attributes of variables (e.g. units, long_name and
standard_name), and some netCDF global file attributes (e.g. history
and institution).

**Miscellaneous**

Field objects are picklable.

    '''
    __metaclass__ = abc.ABCMeta
 
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
        
        obj._Constructs = Constructs
#        obj._Domain     = Domain

        return obj
    #--- End: def

    def __init__(self, properties={}, source=None, copy=True,
                 _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Provide the new field with CF properties from the dictionary's
        key/value pairs.

    source: 

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''        
        # Initialize the new field with attributes and CF properties
        super(Field, self).__init__(properties=properties,
                                    source=source, copy=copy,
                                    _use_data=_use_data) 
               
        self._set_attribute('unlimited', None)
        self._set_attribute('HDFgubbins', None)
    #--- End: def

    def unlimited(self, *args, **kwargs):
        return {}
    
    def __repr__(self):
        '''Called by the :py:obj:`repr` built-in function.

x.__repr__() <==> repr(x)

:Examples:

>>> f
<CF Field: air_temperature(latitude(73), longitude(96) K>

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__,
                                   self._one_line_description())
    #--- End: def

    def __str__(self):
        '''Called by the :py:obj:`str` built-in function.

x.__str__() <==> str(x)

        '''
        title = "Field: {0}".format(self.name(''))

        # Append the netCDF variable name
        ncvar = self.get_ncvar(None)
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

        axis_names = self._axis_names_sizes()
        
        # Data
        string.append(
            'Data            : {0}'.format(self._one_line_description(axis_names)))

        # Cell methods
        cell_methods = self.cell_methods()
        if cell_methods:
            x = []
            for cm in cell_methods.values():
                cm = cm.copy()
                cm.axes = tuple([axis_names.get(axis, axis)
                                 for axis in cm.get_axes(())])
                x.append(str(cm))
                
            c = ' '.join(x)
            
            string.append('Cell methods    : {0}'.format(c))
        #--- End: if
        
#        axis_to_name = {}
        def _print_item(self, key, variable, dimension_coord):
            '''Private function called by __str__'''
            
            if dimension_coord:
                # Dimension coordinate
                axis = self.construct_axes(key)[0]
                name = variable.name(ncvar=True, default=key)
                name += '({0})'.format(variable.get_data().size)

#                axis_to_name[key] = name
                
                #variable = self.constructs().get(key, None)
                
                if variable is None:
                    return name
                          
                x = [name]
                
            else:
                # Auxiliary coordinate
                # Cell measure
                # Field ancillary
                # Domain ancillary
                shape = [axis_names[axis] for axis in self.construct_axes(key)]
                shape = str(tuple(shape)).replace("'", "")
                shape = shape.replace(',)', ')')
                x = [variable.name(ncvar=True, default=key)]
                x.append(shape)
            #--- End: if
                    
            if variable.has_data():
#                if variable.isreftime:
#                    x.append(' = {}'.format(variable.data.asdata(variable.dtarray)))
#                else:
                x.append(' = {0}'.format(variable.get_data()))
                
            return ''.join(x)
        #--- End: def
                          
        # Axes and dimension coordinates
#        data_axes = self.get_data_axes()
#        if data_axes is None:
#            data_axes = ()
#        non_spanning_axes = set(self.domain_axes()).difference(data_axes)
#
#        x = ['{0}({1})'.format(self.domain_axis_name(axis),
#                               self.domain_axes()[axis].get_size(''))
#            for axis in list(non_spanning_axes) + data_axes]
#        string.append('Domain axes: {}'.format(', '.join(x)))

        # Field ancillary variables
        x = [_print_item(self, key, anc, False)
             for key, anc in sorted(self.field_ancillaries().items())]
        if x:
            string.append('Field ancils    : {}'.format(
                '\n                : '.join(x)))

        x = []
        for key in tuple(non_spanning_axes) + data_axes:
            for dc_key, dim in self.dimension_coordinates().items():
                if self.construct_axes()[dc_key] == (key,):
                    name = dim.name(default='id%{0}'.format(dc_key), ncvar=True)
                    y = '{0}({1})'.format(name, dim.get_data().size)
                    if y != axis_names[key]:
                        y = '{0}({1})'.format(name, axis_names[key])
                    if dim.has_data():
                        y += ' = {0}'.format(dim.get_data())
                        
                    x.append(y)
        #--- End: for
        string.append('Dimension coords: {}'.format('\n                : '.join(x)))

        
#        x1 = [_print_item(self, dim, None, True)
#              for dim in sorted(non_spanning_axes)]
#        x2 = [_print_item(self, dim, None, True)
#              for dim in data_axes]
#        x = x1 + x2
#        if x:
#            string.append('Axes           : {}'.format(
#                '\n               : '.join(x)))
                          
        # Auxiliary coordinates
        x = [_print_item(self, aux, v, False) 
             for aux, v in sorted(self.auxiliary_coordinates().items())]
        if x:
            string.append('Auxiliary coords: {}'.format(
                '\n                : '.join(x)))
        
        # Cell measures
        x = [_print_item(self, msr, v, False)
             for msr, v in sorted(self.cell_measures().items())]
        if x:
            string.append('Cell measures   : {}'.format(
                '\n                : '.join(x)))
            
        # Coordinate references
        x = sorted([str(ref) for ref in self.coordinate_references().values()])
        if x:
            string.append('Coord references: {}'.format(
                '\n                : '.join(x)))
            
        # Domain ancillary variables
        x = [_print_item(self, key, anc, False)
             for key, anc in sorted(self.domain_ancillaries().items())]
        if x:
            string.append('Domain ancils   : {}'.format(
                '\n                : '.join(x)))
                                      
        string.append('')
        
        return '\n'.join(string)
    #--- End def

    def __getitem__(self, indices):
        '''f.__getitem__(indices) <==> f[indices]

Return a subspace of the field defined by index values

Subspacing by axis indices uses an extended Python slicing syntax,
which is similar to :ref:`numpy array indexing
<numpy:arrays.indexing>`. There are extensions to the numpy indexing
functionality:

* Size 1 axes are never removed.

  An integer index *i* takes the *i*-th element but does not reduce
  the rank of the output array by one:

  >>> f.shape
  (12, 73, 96)
  >>> f[0].shape
  (1, 73, 96)
  >>> f[3, slice(10, 0, -2), 95:93:-1].shape
  (1, 5, 2)

* The indices for each axis work independently.

  When more than one axis's slice is a 1-d boolean sequence or 1-d
  sequence of integers, then these indices work independently along
  each axis (similar to the way vector subscripts work in Fortran),
  rather than by their elements:

  >>> f.shape
  (12, 73, 96)
  >>> f[:, [0, 72], [5, 4, 3]].shape
  (12, 2, 3)

  Note that the indices of the last example would raise an error when
  given to a numpy array.

* Boolean indices may be any object which exposes the numpy array
  interface, such as the field's coordinate objects:

  >>> f[:, f.coord('latitude')<0].shape
  (12, 36, 96)

>>> f.shape
(12, 73, 96)
>>> f[...].shape
(12, 73, 96)

.. versionadded:: 1.6

.. seealso:: `__setitem__`

:Examples 1:

>>> g = f[..., 0, :6, 9:1:-2, [1, 3, 4]]

:Returns:

    out: `Field`

:Examples 2:

>>> f.shape
(12, 73, 96)
>>> f[...].shape
(12, 73, 96)

        ''' 
        data  = self.get_data()
        shape = data.shape

        indices = data.parse_indices(indices)

        new = self.copy(data=False)

        data_axes = new.get_data_axes()
        
        # Open any files that contained the original data (this not
        # necessary, is an optimsation)
        
        # ------------------------------------------------------------
        # Subspace the field's data
        # ------------------------------------------------------------
        new.set_data(data[indices], data_axes)

        # ------------------------------------------------------------
        # Subspace constructs
        # ------------------------------------------------------------
        self_constructs = self._get_constructs()

        for key, construct in new.array_constructs().iteritems():
            data = self.get_construct(key).get_data(None)
            if data is None:
                # This construct has no data array
                continue

            # Still here?
            needs_slicing = False
            dice = []
            for axis in new.construct_axes(key):
                if axis in data_axes:
                    needs_slicing = True
                    dice.append(indices[data_axes.index(axis)])
                else:
                    dice.append(slice(None))
            #--- End: for

            if _debug:
                print '    item:', repr(item)
                print '    dice = ', dice

            # Set construct data
            if needs_slicing:
                new_data = data[tuple(dice)]
            else:
                new_data = data.copy()

            construct.set_data(new_data, copy=False)
        #--- End: for

        # Replace domain axes
        domain_axes = new.domain_axes()
        new_constructs = new._get_constructs()
        for key, size in zip(data_axes, new.get_data().shape):
            domain_axis = domain_axes[key].copy()
            domain_axis.set_size(size)
            new_constructs.replace(key, domain_axis)

        return new
    #--- End: def

    def _axis_names_sizes(self):
        '''
        '''    
        axis_names = {}
        for key, domain_axis in self.domain_axes().iteritems():
            axis_names[key] = '{0}({1})'.format(self.domain_axis_name(key),
                                                domain_axis.get_size(''))
           
        return axis_names
    #--- End: def
    
    def _one_line_description(self, axis_names_sizes=None):
        '''
        '''
        if axis_names_sizes is None:
            axis_names_sizes = self._axis_names_sizes()
            
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
        '''Return a string containing a description of the domain axes of the
field.
    
:Parameters:
    
    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed.
    
    _level: `int`, optional

:Returns:
    
    out: `str`
        A string containing the description.
    
:Examples:

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
            print string
        else:
            return string
    #--- End: def

    def auxiliary_coordinates(self, axes=None, copy=False):
        '''
        '''    
        return self._get_constructs().constructs('auxiliarycoordinate',
                                                 axes=axes, copy=copy)
    #--- End: def

    def cell_measures(self, axes=None, copy=False):
        '''
        '''    
        return self._get_constructs().constructs('cellmeasure',
                                                 axes=axes, copy=copy)
    #--- End: def

    def constructs(self, axes=None, copy=False):
        '''
        '''
        return self._get_constructs().constructs(axes=axes, copy=copy)
    #--- End: def
    
    def dimension_coordinates(self, axes=None, copy=False):
        '''
        '''    
        return self._get_constructs().constructs('dimensioncoordinate',
                                                 axes=axes, copy=copy)
    #--- End: def

    def domain_ancillaries(self, axes=None, copy=False):
        '''
        '''    
        return self._get_constructs().constructs('domainancillary',
                                                 axes=axes, copy=copy)
    #--- End: def

    def domain_axis_name(self, key):
        '''
        '''
        constructs = self._get_constructs()
        return constructs.domain_axis_name(key)
    #--- End: def
    
    def dump(self, display=True, _level=0, _title='Field'):
        '''A full description of the field.

The field and its components are described without abbreviation with
the exception of data arrays, which are abbreviated to their first and
last values.

:Examples 1:
        
>>> f.{+name}()

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed.

          *Example:*
            ``f.dump()`` is equivalent to ``print
            f.dump(display=False)``.

:Returns:

    out: `None` or `str`
        If *display* is True then the description is printed and
        `None` is returned. Otherwise the description is returned as a
        string.

        '''
        indent = '    '      
        indent0 = indent * _level
        indent1 = indent0 + indent

        if _title is None:
            ncvar = self.get_ncvar(None)
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

        # Simple properties
        properties = self.properties()
        if properties:
            string.append(
                self._dump_properties(_level=_level))

        axis_names = self._axis_names_sizes()
           
        # Data
        data = self.get_data(None)
        if data is not None:
            axes = self.domain_axes()
            axis_name = self.domain_axis_name
            x = ['{0}({1})'.format(axis_name(axis), axes[axis].get_size(''))
                 for axis in self.get_data_axes(())]
            if self.isreftime:
                data = data.asdata(data.dtarray)
                
            string.extend(('', '{0}Data({1}) = {2}'.format(indent0,
                                                           ', '.join(x),
                                                           str(data))))
            
        # Cell methods
        # Axes
        axes = self._dump_axes(axis_names, display=False, _level=_level)
        if axes:
            string.extend(('', axes))
           
        cell_methods = self.cell_methods()
        if cell_methods:
            string.append('')
            for cm in cell_methods.values():
                cm = cm.copy()
                cm.set_axes(tuple([axis_names.get(axis, axis)
                                   for axis in cm.get_axes(())]))
                string.append(cm.dump(display=False,  _level=_level))
        #--- End: if

        # Field ancillaries
        for key, value in sorted(self.field_ancillaries().iteritems()):
            string.append('') 
            string.append(
                value.dump(display=False, field=self, key=key, _level=_level))

        # Dimension coordinates
        for key, value in sorted(self.dimension_coordinates().iteritems()):
            string.append('')
            string.append(value.dump(display=False, 
                                     field=self, key=key, _level=_level))
             
        # Auxiliary coordinates
        for key, value in sorted(self.auxiliary_coordinates().iteritems()):
            string.append('')
            string.append(value.dump(display=False, field=self, 
                                     key=key, _level=_level))
        # Domain ancillaries
        for key, value in sorted(self.domain_ancillaries().iteritems()):
            string.append('') 
            string.append(
                value.dump(display=False, field=self, key=key, _level=_level))
            
        # Coordinate references
        for key, value in sorted(self.coordinate_references().iteritems()):
            string.append('')
            string.append(
                value.dump(display=False, field=self, key=key, _level=_level))

        # Cell measures
        for key, value in sorted(self.cell_measures().iteritems()):
            string.append('')
            string.append(
                value.dump(display=False, field=self, key=key, _level=_level))

        string.append('')
        
        string = '\n'.join(string)
       
        if display:
            print string
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_construct_type=False):
        '''True if two {+variable}s are equal, False otherwise.

Two fields are equal if ...

Note that a {+variable} may be equal to a single element field list,
for example ``f.equals(f[0:1])`` and ``f[0:1].equals(f)`` are always
True.

.. seealso:: `cf.FieldList.equals`, `cf.FieldList.set_equals`

:Examples 1:

>>> b = f.{+name}(g)

:Parameters:

    other: `object`
        The object to compare for equality.

    {+atol}

    {+rtol}

    ignore_fill_value: `bool`, optional
        If True then data arrays with different fill values are
        considered equal. By default they are considered unequal.

    traceback: `bool`, optional
        If True then print a traceback highlighting where the two
        {+variable}s differ.

    ignore: `tuple`, optional
        The names of CF properties to omit from the comparison. By
        default, the CF Conventions property is omitted.

:Returns: 
  
    out: `bool`
        Whether or not the two {+variable}s are equal.

:Examples 2:

>>> f.Conventions
'CF-1.0'
>>> g = f.copy()
>>> g.Conventions = 'CF-1.6'
>>> f.equals(g)
True

In the following example, two fields differ only by the long name of
their time coordinates. The traceback shows that they differ in their
domains, that they differ in their time coordinates and that the long
name could not be matched.

>>> g = f.copy()
>>> g.coord('time').long_name += ' different'
>>> f.equals(g, traceback=True)
Domain: Different coordinate: <CF Coordinate: time(12)>
Field: Different domain properties: <CF Domain: (128, 1, 12, 64)>, <CF Domain: (128, 1, 12, 64)>
False

        '''
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        ignore_properties = tuple(ignore_properties) + ('Conventions',)
            
        if not super(Field, self).equals(
                other,
                rtol=rtol, atol=atol, traceback=traceback,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_properties=ignore_properties,
                ignore_construct_type=ignore_construct_type):
            return False

        # ------------------------------------------------------------
        # Check the constructs
        # ------------------------------------------------------------              
        if not cfdm_equals(self._get_constructs(),
                           other._get_constructs(),
                           rtol=rtol, atol=atol,
                           traceback=traceback,
                           ignore_data_type=ignore_data_type,
                           ignore_construct_type=ignore_construct_type,
                           ignore_fill_value=ignore_fill_value):
            if traceback:
                print(
                    "{0}: Different {1}".format(self.__class__.__name__, 'constructs'))
            return False

        return True
    #--- End: def
        
    def expand_dims(self, position=0, axis=None, copy=True):
        '''Insert a size 1 axis into the data array.

By default default a new size 1 axis is inserted which doesn't yet
exist, but a unique existing size 1 axis which is not already spanned
by the data array may be selected.

.. seealso:: `axes`, `squeeze`, `transpose`

:Examples 1:

>>> g = f.{+name}()
>>> g = f.{+name}(2, axes='T')

:Parameters:

    position: `int`, optional
        Specify the position that the new axis will have in the data
        array. By default the new axis has position 0, the slowest
        varying position.

    {+axes, kwargs}

    {+copy}

:Returns:

    out: `{+Variable}`
        The expanded field.

:Examples 2:

        '''
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
       
        # Expand the dims in the field's data array
        f = super(Field, self).expand_dims(position, copy=copy)

        data_axes.insert(position, axis)
        f.set_data_axes(data_axes)

        return f
    #--- End: def

    def field_ancillaries(self, axes=None, copy=False):
        '''
        '''
        return self._get_constructs().constructs('fieldancillary',
                                                 axes=axes, copy=copy)

    def squeeze(self, axes=None, copy=True):
        '''Remove size-1 axes from the data array.

By default all size 1 axes are removed, but particular size 1 axes may
be selected for removal.

The axes are selected with the *axes* parameter.

Squeezed axes are not removed from the coordinate and cell measure
objects, nor are they removed from the domain. To completely remove
axes, use the `remove_axes` method.

.. seealso:: `expand_dims`, `remove_axes`, `transpose`, `unsqueeze`


:Examples 1:

>>> g = f.{+name}()
>>> g = f.{+name}('T')

:Parameters:

    {+axes, kwargs}

    {+copy}

:Returns:

    out: `{+Variable}`
        The squeezed field.

:Examples 2:

        '''     
        data_axes = self.get_data_axes(())
        domain_axes = self.domain_axes()
            
        if axes is None:
            axes = [axis for axis in data_axes if domain_axes[axis].get_size(None) == 1]
        else:
            for axis in axes:
                if domain_axes[axis].get_size() != 1:
                    raise ValueError(
"Can't squeeze domain axis with size {}".format(domain_axes[axis].get_size(None)))
            #--- End: for
            
            axes = [axis for axis in axes if axis in data_axes]
        #--- End: if
        
        iaxes = [data_axes.index(axis) for axis in axes]
        
        # Squeeze the field's data array
        f = super(Field, self).squeeze(iaxes, copy=copy)

        new_data_axes = [axis for axis in data_axes if axis not in axes]
        f.set_data_axes(new_data_axes)

        return f
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
    
#--- End: class
