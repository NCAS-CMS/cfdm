from collections import abc
from itertools   import izip_longest

import numpy

#from .domainaxis import DomainAxis
from .flags      import Flags

from .constructs2 import Constructs
from .domain      import Domain

from .variable   import docstring
from .variable   import Variable
_debug = False



docstring['{+item_definition}'] = '''\
\
An item of the field is one of the following field components:

  * dimension coordinate
  * auxiliary coordinate
  * cell measure
  * domain ancillary
  * field ancillary
  * coordinate reference'''

docstring['{+item_selection}'] = '''\
\
Items are selected with the criteria specified by the keyword
parameters. If no parameters are set then all items are selected. If
multiple criteria are given then items that meet all of them are
selected.'''
    
docstring['{+items_criteria}'] = '''\
\
Item selection criteria have the following categories:
    
==================  ==================================  ==================
Selection criteria  Description                         Keyword parameters
==================  ==================================  ==================
CF properties       Items with given CF properties      *description*
                                               
Attributes          Items with given attributes         *description*
                                               
Domain axes         Items which span given domain axes  *axes*,
                                                        *axes_all*,
                                                        *axes_subset*,
                                                        *axes_superset*,
                                                        *ndim*
                                               
Role                Items of the given component type   *role*
==================  ==================================  =================='''

docstring['{+axes}'] = '''\
\
axes: optional
        Select items which span at least one of the specified axes,
        taken in any order, and possibly others. Axes are defined by
        identfiying items of the field (such as dimension coordinate
        objects) or by specifying axis sizes. In the former case the
        selected axes are those which span the identified items. The
        axes are interpreted as those that would be returned by the
        field's `~Field.axes` method, i.e. by ``f.axes(axes)`` or,
        if *axes* is a dictionary, ``f.axes(**axes)``. See
        `axes` for details.
  
          *Example:*
            To select items which span a time axis, and possibly
            others, you could set ``axes='T'``, or equivalently:
            ``axes=['T']``.
            
          *Example:*
            To select items which span a latitude and/or longitude
            axes, and possibly others, you could set: ``axes=['X',
            'Y']``.
            
          *Example:*
            To specify axes with size 19 you could set ``axes={'size':
            19}``. To specify depth axes with size 40 you could set:
            ``axes={'axes': 'depth', 'size': 40}``.'''

docstring['{+axes_subset}'] = '''\
\
axes_subset: optional 
        Select items whose data array spans all of the specified axes,
        taken in any order, and possibly others. The axes are those
        that would be selected by this call of the field's
        `~Field.axes` method: ``f.axes(axes_subset)`` or, if
        *axes_subset* is a dictionary of parameters ,
        ``f.axes(**axes_subset)``. Axes are defined by identfiying
        items of the field (such as dimension coordinate objects) or
        by specifying axis sizes. In the former case the selected axes
        are those which span the identified field items. See
        `Field.axes` for details.
    
          *Example:*            
            To select items which span a time axes, and possibly
            others, you could set: ``axes_subset='T'``.
            
          *Example:*
            To select items which span latitude and longitude axes,
            and possibly others, you could set: ``axes_subset=['X',
            'Y']``.
            
          *Example:*
            To specify axes with size 19 you could set
            ``axes_subset={'size': 19}``. To specify depth axes with
            size 40 or more, you could set: ``axes_subset={'axes':
            'depth', 'size': cf.ge(40)}`` (see `cf.ge`).'''
    
docstring['{+axes_superset}'] = '''\
\
axes_superset: optional
        Select items whose data arrays span a subset of the specified
        axes, taken in any order, and no others. The axes are those
        that would be selected by this call of the field's
        `~Field.axes` method: ``f.axes(axes_superset)`` or, if
        *axes_superset* is a dictionary of parameters,
        ``f.axes(**axes_superset)``. Axes are defined by identfiying
        items of the field (such as dimension coordinate objects) or
        by specifying axis sizes. In the former case the selected axes
        are those which span the identified field items. See
        `Field.axes` for details.
    
          *Example:*
            To select items which span a time axis, and no others, you
            could set: ``axes_superset='T'``.
            
          *Example:*
            To select items which span latitude and/or longitude axes,
            and no others, you could set: ``axes_superset=['X',
            'Y']``.
            
          *Example:*
            To specify axes with size 19 you could set
            ``axes_superset={'size': 19}``. To specify depth axes with
            size 40 or more, you could set: ``axes_superset={'axes':
            'depth', 'size': cf.ge(40)}`` (see `cf.ge`).'''

docstring['{+axes_all}'] = '''\
\
axes_all: optional
        Select items whose data arrays span all of the specified axes,
        taken in any order, and no others. The axes are those that
        would be selected by this call of the field's `~Field.axes`
        method: ``f.axes(axes_all)`` or, if *axes_all* is a dictionary
        of parameters, ``f.axes(**axes_all)``. Axes are defined by
        identfiying items of the field (such as dimension coordinate
        objects) or by specifying axis sizes. In the former case the
        selected axes are those which span the identified field
        items. See `Field.axes` for details.
    
          *Example:*
            To select items which span a time axis, and no others, you
            could set: ``axes_all='T'``.
            
          *Example:*
            To select items which span latitude and longitude axes,
            and no others, you could set: ``axes_all=['X', 'Y']``.
            
          *Example:*
            To specify axes with size 19 you could set
            ``axes_all={'size': 19}``. To specify depth axes with size
            40 or more, you could set: ``axes_all={'axes': 'depth',
            'size': cf.ge(40)}`` (see `cf.ge`).'''

docstring['{+copy_item_in}'] = '''\
\
copy: `bool`, optional
        If False then the item is inserted without being copied. By
        default a copy of the item is inserted'''

docstring['{+role}'] = '''\
\
role: (sequence of) `str`, optional
        Select items of the given roles. Valid roles are:
    
          =======  ==========================
          Role     Items selected
          =======  ==========================
          ``'d'``  Dimension coordinate items
          ``'a'``  Auxiliary coordinate items
          ``'m'``  Cell measure items
          ``'c'``  Domain ancillary items
          ``'f'``  Field ancillary items
          ``'r'``  Coordinate reference items
          =======  ==========================
    
        Multiple roles may be specified by a sequence of role
        identifiers. By default all roles except coordinate reference
        items are considered, i.e. by default ``role=('d', 'a', 'm',
        'f', 'c')``.
    
          *Example:*
            To select dimension coordinate items: ``role='d'`` or
            ``role=['d']`.

          *Example:*
            Selecting auxiliary coordinate and cell measure items may
            be done with any of the following values of *role*:
            ``'am'``, ``'ma'``, ``('a', 'm')``, ``['m', 'a']``,
            ``set(['a', 'm'])``, etc.'''

       
# ====================================================================
#
# Field object
#
# ====================================================================

class AbstractField(Variable):
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
    
#    _DomainAxis = DomainAxis
#    _Flags      = Flags
#    _Constructs = Constructs

    _special_properties = Variable._special_properties.union(
        ('flag_values',
         'flag_masks',
         'flag_meanings',)
    )
    
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
        
        obj._Flags      = Flags
        obj._Constructs = Constructs
        obj._Domain     = Domain

        return obj
    #--- End: def
    
    def __init__(self, properties={}, #attributes={},
#                 data=None,
                 source=None, copy=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Provide the new field with CF properties from the dictionary's
        key/value pairs.

    attributes: `dict`, optional
        Provide the new field with attributes from the dictionary's
        key/value pairs.

    source: 

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        # Constructs
        constructs = self._Constructs(
            array_constructs=('dimensioncoordinate',
                              'auxiliarycoordinate',
                              'cellmeasure',
                              'domainancillary',
                              'fieldancillary'),
            non_array_constructs=('cellmethod',
                                  'coordinatereference',
                                  'domainaxis'),
            ordered_constructs=('cellmethod',)
        )
        
        self._private = {'properties' : {},
                         'special_attributes': {'constructs': constructs}
        }
        
        # Initialize the new field with attributes and CF properties
        super(Field, self).__init__(properties=properties,
#                                    attributes=attributes,
                                    source=source,
#                                    data=data,
                                    copy=copy) 

        if getattr(source, 'isfield', False):
            # Initialise constructs from a source field
            self._private['special_attributes']['constructs'] = source.Constructs.copy()

        self._unlimited = None
    #--- End: def

    def unlimited(self, *args, **kwargs):
        return {}
    
    def _no_None_dict(self, d):
        '''
        '''
        return dict((key, value) for key, value in d.iteritems() 
                    if value is not None)
    #--- End: def

    def __repr__(self):
        '''Called by the :py:obj:`repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        if self.hasdata:
            axes = self.domain_axes()
            axis_name = self.domain_axis_name
            x = ['{0}({1})'.format(axis_name(axis), axes[axis].size)
                 for axis in self.data_axes()]
            axis_names = '({0})'.format(', '.join(x))
        else:
            axis_names = ''
            
        # Field units
        units = getattr(self, 'units', '')
        calendar = getattr(self, 'calendar', None)
        if calendar is not None:
            units += '{0} {1}'.format(calendar)

        return '<{0}: {1}{2} {3}>'.format(self.__class__.__name__,
                                          self.name(default=''),
                                          axis_names, units)
    #--- End: def

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
        data  = self.data
        shape = data.shape

        # Parse the index
#        if not isinstance(indices, tuple):
#            indices = (indices,)

        indices = data.parse_indices(indices)

        new = self.copy()

        # Open any files that contained the original data (this not
        # necessary, is an optimsation)
        
        # ------------------------------------------------------------
        # Subspace the field's data
        # ------------------------------------------------------------
#        new._Data = self.data[tuple(indices)]
        new._Data = self.data[indices]

        # ------------------------------------------------------------
        # Subspace constructs
        # ------------------------------------------------------------
        new_Constructs = new.Constructs
        data_axes = new.data_axes()

        for key, construct in new.array_constructs().iteritems():
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
                
            # Replace existing construct with its subspace
            if needs_slicing:
                new_Constructs.replace(construct[tuple(dice)], key)
        #--- End: for

        # Replace domain axes
        domain_axes = new.domain_axes()
        for key, size in zip(data_axes, new.shape):
            new_domain_axis = domain_axes[key].copy()
            new_domain_axis.size = size
            new_Constructs.replace(new_domain_axis, key)

        return new
    #--- End: def

#    def __str__(self):
#        '''Called by the :py:obj:`str` built-in function.
#
#x.__str__() <==> str(x)
#
#        '''
#        title = "Field: {0}".format(self.name(''))
#
#        # Append the netCDF variable name
#        ncvar = self.ncvar()
#        if ncvar is not None:
#            title += " (ncvar%{0})".format(ncvar)
#        
#        string = [title]
#        string.append(''.ljust(len(string[0]), '-'))
#
#        # Units
#        units = getattr(self, 'units', '')
#        calendar = getattr(self, 'calendar', None)
#        if calendar is not None:
#            units += ' {0} {1}'.format(calendar)
#            
#        axis_name = self.domain_axis_name
#
#        # Axes
#        data_axes = self.data_axes()
#        if data_axes is None:
#            data_axes = ()
#        non_spanning_axes = set(self.domain_axes()).difference(data_axes)
#
#        axis_names = {}
#        for key, domain_axis in self.domain_axes().iteritems():
#            axis_names[key] = '{0}({1})'.format(axis_name(key),
#                                                domain_axis.size)
#        
#        # Data
#        if self.hasdata:
#            axes = self.domain_axes()
#            x = ['{0}'.format(axis_names[axis]) for axis in self.data_axes()]
#            string.append('Data            : {0}({1}) {2}'.format(
#                self.name(''), ', '.join(x), units))
#        elif units:
#            string.append('Data            : {0}'.format(units))
#
#        # Cell methods
#        cell_methods = self.cell_methods()
#        if cell_methods:
#            x = []
#            for cm in cell_methods.values():
#                cm = cm.copy()
#                cm.axes = tuple([axis_names.get(axis, axis) for axis in cm.axes])
#                x.append(str(cm))
#                
#            c = ' '.join(x)
#            
#            string.append('Cell methods    : {0}'.format(c))
#        #--- End: if
#        
#        axis_to_name = {}
#        def _print_item(self, key, variable, dimension_coord):
#            '''Private function called by __str__'''
#            
#            if dimension_coord:
#                # Dimension coordinate
#                name = "{0}({1})".format(axis_name(key), self.domain_axes()[key].size)
#                axis_to_name[key] = name
#                
#                variable = self.constructs().get(key, None)
#                
#                if variable is None:
#                    return name
#                          
#                x = [name]
#                
#            else:
#                # Auxiliary coordinate
#                # Cell measure
#                # Field ancillary
#                # Domain ancillary
#                shape = [axis_names[axis] for axis in self.construct_axes(key)]
#                shape = str(tuple(shape)).replace("'", "")
#                shape = shape.replace(',)', ')')
#                x = [variable.name(key)]
#                x.append(shape)
#            #--- End: if
#                    
#            if variable.hasdata:
##                if variable.isreftime:
##                    x.append(' = {}'.format(variable.data.asdata(variable.dtarray)))
##                else:
#                x.append(' = {}'.format(variable.data))
#                
#            return ''.join(x)
#        #--- End: def
#                          
#        # Axes and dimension coordinates
##        data_axes = self.data_axes()
##        if data_axes is None:
##            data_axes = ()
##        non_spanning_axes = set(self.domain_axes()).difference(data_axes)
##
##        x = ['{0}({1})'.format(self.domain_axis_name(axis),
##                               self.domain_axes()[axis].size)
##            for axis in list(non_spanning_axes) + data_axes]
##        string.append('Domain axes: {}'.format(', '.join(x)))
#
#        # Field ancillary variables
#        x = [_print_item(self, key, anc, False)
#             for key, anc in sorted(self.field_ancillaries().items())]
#        if x:
#            string.append('Field ancils    : {}'.format(
#                '\n                : '.join(x)))
#
#        x = []
#        for key in list(non_spanning_axes) + data_axes:
#            for k, dim in self.dimension_coordinates().items():
#                if self.construct_axes()[k] == (key,):
#                    name = dim.name(default='id%{0}'.format(k))
#                    y = '{0}({1})'.format(name, dim.size)
#                    if y != axis_names[key]:
#                        y = '{0}({1})'.format(name, axis_names[key])
#                    if dim.hasdata:
#                        y += ' = {0}'.format(dim.data)
#                    x.append(y)   
#        string.append('Dimension coords: {}'.format('\n                : '.join(x)))
#
#        
##        x1 = [_print_item(self, dim, None, True)
##              for dim in sorted(non_spanning_axes)]
##        x2 = [_print_item(self, dim, None, True)
##              for dim in data_axes]
##        x = x1 + x2
##        if x:
##            string.append('Axes           : {}'.format(
##                '\n               : '.join(x)))
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
#        x = sorted([ref.name(default='')
#                    for ref in self.coordinate_references().values()])
#        if x:
#            string.append('Coord references: {}'.format(
#                '\n                : '.join(x)))
#            
#        # Domain ancillary variables
#        x = [_print_item(self, key, anc, False)
#             for key, anc in sorted(self.domain_ancillaries().items())]
#        if x:
#            string.append('Domain ancils   : {}'.format(
#                '\n                : '.join(x)))
#                                      
#        string.append('')
#        
#        return '\n'.join(string)
#    #--- End def
                          
    @property
    def Flags(self):
        '''A `Flags` object containing self-describing CF flag values.
        
        A `Flags` object stores the `flag_values`, `flag_meanings` and
        `flag_masks` CF properties in an internally consistent manner.
        
        '''
        return self._get_special_attr('Flags')
    @Flags.setter
    def Flags(self, value):
        self._set_special_attr('Flags', value)
    @Flags.deleter
    def Flags(self):
        self._del_special_attr('Flags')
        
    @property
    def Constructs(self):
        return self._private['special_attributes']['constructs']
    
    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def flag_values(self):
        '''The flag_values CF property.
        
Provides a list of the flag values. Use in conjunction with
`flag_meanings`. See http://cfconventions.org/latest.html for details.

Stored as a 1-d `Data` array but may be set as any array-like object.

:Examples:

>>> f.flag_values = ['a', 'b', 'c']
>>> f.flag_values
array(['a', 'b', 'c'], dtype='|S1')
>>> f.flag_values = numpy.arange(4)
>>> f.flag_values
array([1, 2, 3, 4])
>>> del f.flag_values

>>> f.setprop('flag_values', 1)
>>> f.getprop('flag_values')
array([1])
>>> f.delprop('flag_values')

        '''
        try:
            return self.Flags.flag_values.array
        except AttributeError:
            raise AttributeError("{} doesn't have CF property 'flag_values'".format(self.__class__.__name__))
    #--- End: def
    @flag_values.setter
    def flag_values(self, value):
        flags = getattr(self, 'Flags', None)
        if flags is None:
            self.Flags = self._Flags(flag_values=value)
        else:
            flags.flag_values = value
            #--- End: def
    @flag_values.deleter
    def flag_values(self):
        try:
            del self.Flags.flag_values
        except AttributeError:
            raise AttributeError("Can't delete non-existent CF property 'flag_values'")
        #--- End: def
    
    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def flag_masks(self):
        '''The flag_masks CF property.
    
Provides a list of bit fields expressing Boolean or enumerated
flags. See http://cfconventions.org/latest.html for details.

Stored as a 1-d numpy array but may be set as array-like object.

:Examples:

>>> f.flag_masks = numpy.array([1, 2, 4], dtype='int8')
>>> f.flag_masks
array([1, 2, 4], dtype=int8)
>>> f.flag_masks = (1, 2, 4, 8)
>>> f.flag_masks
array([1, 2, 4, 8], dtype=int8)
>>> del f.flag_masks

>>> f.setprop('flag_masks', 1)
>>> f.getprop('flag_masks')
array([1])
>>> f.delprop('flag_masks')

'''
        try:
            return self.Flags.flag_masks.array
        except AttributeError:
            raise AttributeError("{} doesn't have CF property 'flag_masks'".format(self.__class__.__name__))
    #--- End: def
    @flag_masks.setter
    def flag_masks(self, value):
        flags = getattr(self, 'Flags', None)
        if flags is None:
            self.Flags = self._Flags(flag_masks=value)
        else:
            flags.flag_masks = value
    #--- End: def
    @flag_masks.deleter
    def flag_masks(self):
        try:
            del self.Flags.flag_masks
        except AttributeError:
            raise AttributeError("Can't delete non-existent CF property 'flag_masks'")
    #--- End: def
                          
    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def flag_meanings(self):
        '''The flag_meanings CF property.
    
Use in conjunction with `flag_values` to provide descriptive words or
phrases for each flag value. See
http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#flags
for details.

:Examples:

>>> f.flag_meanings = 'low medium high'
>>> f.flag_meanings
'low medium high'
>>> del flag_meanings

>>> f.setprop('flag_meanings', 'a b')
>>> f.getprop('flag_meanings')
'a b'
>>> f.delprop('flag_meanings')
    
        '''
        try:
            meanings = self.Flags.flag_meanings
        except AttributeError:
            raise AttributeError("{} doesn't have CF property 'flag_meanings'".format(self.__class__.__name__))
    
        return ' '.join(meanings)
    #--- End: def
    @flag_meanings.setter
    def flag_meanings(self, value):
        if isinstance(value , basestring):
            value = value.split()
    
        flags = getattr(self, 'Flags', None)
        if flags is None:
            self.Flags = self._Flags(flag_meanings=value)
        else:
            flags.flag_meanings = value
    #--- End: def
    @flag_meanings.deleter
    def flag_meanings(self):
        try:
            del self.Flags.flag_meanings
        except AttributeError:
            raise AttributeError("Can't delete non-existent CF property 'flag_meanings'")
    #--- End: def

    def array_constructs(self, axes=None, copy=False):
        return self.Constructs.array_constructs(axes=axes, copy=copy)

    def auxiliary_coordinates(self, axes=None, copy=False):
        return self.Constructs.constructs('auxiliarycoordinate', copy=copy)
    
    def cell_measures(self, axes=None, copy=False):
        return self.Constructs.constructs('cellmeasure', copy=copy)
    
    def cell_methods(self, copy=False):
        return self.Constructs.cell_methods(copy=copy)
    
    def construct_axes(self, key=None):
        return self.Constructs.construct_axes(key=key)
    
    def constructs(self, axes=None,copy=False):
        '''Return all of the data model constructs of the field.

.. versionadded:: 1.6

.. seealso:: `dump`

:Examples 1:

>>> f.{+name}()

:Returns:

    out: `list`
        The objects correposnding CF data model constructs.

:Examples 2:

>>> print f
eastward_wind field summary
---------------------------
Data           : eastward_wind(air_pressure(15), latitude(72), longitude(96)) m s-1
Cell methods   : time: mean
Axes           : time(1) = [2057-06-01T00:00:00Z] 360_day
               : air_pressure(15) = [1000.0, ..., 10.0] hPa
               : latitude(72) = [88.75, ..., -88.75] degrees_north
               : longitude(96) = [1.875, ..., 358.125] degrees_east
>>> f.{+name}()
[<Field: eastward_wind(air_pressure(15), latitude(72), longitude(96)) m s-1>,
 <DomainAxis: 96>,
 <DomainAxis: 1>,
 <DomainAxis: 15>,
 <DomainAxis: 72>,
 <CellMethod: dim3: mean>,
 <DimensionCoordinate: longitude(96) degrees_east>,
 <DimensionCoordinate: time(1) 360_day>,
 <DimensionCoordinate: air_pressure(15) hPa>,
 <DimensionCoordinate: latitude(72) degrees_north>]

        '''
        return self.Constructs.constructs(copy=copy)
    #--- End: def

    def coordinate_references(self, copy=False):
        return self.Constructs.coordinate_references(copy=copy)

    def coordinates(self, copy=False):
        '''
'''
        out = self.dimension_coordinates(copy=copy)
        out.update(self.auxiliary_coordinates(copy=copy))
        return out
    #--- End: def

    def data_axes(self):
        '''Return the domain axes for the data array dimensions.

.. seealso:: `axes`, `axis`, `item_axes`

:Examples 1:

>>> d = f.{+name}()

:Returns:

    out: list or None
        The ordered axes of the data array. If there is no data array
        then `None` is returned.

:Examples 2:

>>> f.ndim
3
>>> f.{+name}()
['dim2', 'dim0', 'dim1']
>>> f.remove_data()
>>> print f.{+name}()
None

>>> f.ndim
0
>>> f.{+name}()
[]

        '''    
        if not self.hasdata:
            return None
        
        return self._data_axes[:]
    #--- End: def

    def dimension_coordinates(self, axes=None, copy=False):
        return self.Constructs.constructs('dimensioncoordinate', axes=axes, copy=copy)
    
    def domain(self, copy=False):
        return self._Domain(constructs=self.Constructs, copy=copy)
    
    def domain_ancillaries(self, copy=False):
        return self.Constructs.constructs('domainancillary', copy=copy)
    
    def domain_axes(self, copy=False):
        return self.Constructs.domain_axes(copy=copy)
    
    def domain_axis_name(self, axis):
        '''
        '''
        return self.Constructs.domain_axis_name(axis)
    #--- End: for
    
    def field_ancillaries(self, copy=False):
        return self.Constructs.constructs('fieldancillary', copy=copy)

    @property
    def isfield(self): 
        '''True, denoting that the variable is a field object

:Examples:

>>> f.isfield
True

        '''
        return True
    #--- End: def

#    def _dump_axes(self, axis_names, display=True, _level=0):
#        '''Return a string containing a description of the domain axes of the
#field.
#    
#:Parameters:
#    
#    display: `bool`, optional
#        If False then return the description as a string. By default
#        the description is printed.
#    
#    _level: `int`, optional
#
#:Returns:
#    
#    out: `str`
#        A string containing the description.
#    
#:Examples:
#
#        '''
#        indent1 = '    ' * _level
#        indent2 = '    ' * (_level+1)
#
#        data_axes = self.data_axes()
#        if data_axes is None:
#            data_axes = ()
#
#        axes = self.domain_axes()
#
#        w = sorted(["{0}Domain Axis: {1}".format(indent1, axis_names[axis])
#                    for axis in axes
#                    if axis not in data_axes])
#
#        x = ["{0}Domain Axis: {1}".format(indent1, axis_names[axis])
#             for axis in data_axes]
#
#        string = '\n'.join(w+x)
#
#        if display:
#            print string
#        else:
#            return string
#    #--- End: def
#
#    def dump(self, display=True, _level=0, _title='Field', _q='-'):
#        '''A full description of the field.
#
#The field and its components are described without abbreviation with
#the exception of data arrays, which are abbreviated to their first and
#last values.
#
#:Examples 1:
#        
#>>> f.{+name}()
#
#:Parameters:
#
#    display: `bool`, optional
#        If False then return the description as a string. By default
#        the description is printed.
#
#          *Example:*
#            ``f.dump()`` is equivalent to ``print
#            f.dump(display=False)``.
#
#:Returns:
#
#    out: `None` or `str`
#        If *display* is True then the description is printed and
#        `None` is returned. Otherwise the description is returned as a
#        string.
#
#        '''
#        indent = '    '      
#        indent0 = indent * _level
#        indent1 = indent0 + indent
#
#        title = '{0}{1}: {2}'.format(indent0, _title, self.name(''))
#
#        # Append the netCDF variable name
#        ncvar = self.ncvar()
#        if ncvar is not None:
#            title += " (ncvar%{0})".format(ncvar)
#
#        line  = '{0}{1}'.format(indent0, ''.ljust(len(title)-_level*4, '-'))
#
#        # Title
#        string = [line, title, line]
#
#        # Simple properties
#        if self.properties():
#            string.append(
#                self._dump_properties(_level=_level,
#                                      omit=('Conventions',
#                                            '_FillValue',
#                                            'missing_value',
#                                            'flag_values',
#                                            'flag_meanings',
#                                            'flag_masks')))
#            
#
#        axis_names = {}
#        for key, domain_axis in self.domain_axes().iteritems():
#            axis_names[key] = '{0}({1})'.format(self.domain_axis_name(key),
#                                                domain_axis.size)
#
#        # Flags
#        flags = []
#        for attr in ('flag_values', 'flag_meanings', 'flag_masks'):
#            value = getattr(self, attr, None)
#            if value is not None:
#                flags.append('{0}{1} = {2}'.format(indent0, attr, value))
#        #--- End: for
#        if flags:
#            string.append('')
#            string.extend(flags)
#            
#        # Axes
#        axes = self._dump_axes(axis_names, display=False, _level=_level)
#        if axes:
#            string.extend(('', axes))
#           
#        # Data
#        if self.hasdata:
#            axes = self.domain_axes()
#            axis_name = self.domain_axis_name
#            x = ['{0}({1})'.format(axis_name(axis), axes[axis].size)
#                 for axis in self.data_axes()]
#            data = self.data
#            if self.isreftime:
#                print 'lkkkk'
#                data = data.asdata(self.dtarray)
#                
#            string.extend(('', '{0}Data({1}) = {2}'.format(indent0,
#                                                           ', '.join(x),
#                                                           str(data))))
#        # Cell methods
#        cell_methods = self.cell_methods()
#        if cell_methods:
#            string.append('')
#            for cm in cell_methods.values():
#                cm = cm.copy()
#                cm.axes = tuple([axis_names.get(axis, axis) for axis in cm.axes])
#                string.append(cm.dump(display=False, _level=_level))
#        #--- End: if
#
##        cell_methods = self.cell_methods()
##        if cell_methods:
##            cell_methods = cell_methods.values()
##            string.append('')
##            for cm in cell_methods:
##                string.append(cm.dump(display=False, _level=_level))
#
#        # Field ancillaries
#        for key, value in sorted(self.field_ancillaries().iteritems()):
#            string.append('') 
#            string.append(
#                value.dump(display=False, field=self, key=key, _level=_level))
#
#        # Dimension coordinates
#        for key, value in sorted(self.dimension_coordinates().iteritems()):
#            string.append('')
#            string.append(value.dump(display=False, 
#                                     field=self, key=key, _level=_level))
#             
#        # Auxiliary coordinates
#        for key, value in sorted(self.auxiliary_coordinates().iteritems()):
#            string.append('')
#            string.append(value.dump(display=False, field=self, 
#                                     key=key, _level=_level))
#        # Domain ancillaries
#        for key, value in sorted(self.domain_ancillaries().iteritems()):
#            string.append('') 
#            string.append(
#                value.dump(display=False, field=self, key=key, _level=_level))
#            
#        # Coordinate references
#        for key, value in sorted(self.coordinate_references().iteritems()):
#            string.append('')
#            string.append(
#                value.dump(display=False, field=self, key=key, _level=_level))
#
#        # Cell measures
#        for key, value in sorted(self.cell_measures().iteritems()):
#            string.append('')
#            string.append(
#                value.dump(display=False, field=self, key=key, _level=_level))
#
#        string.append('')
#        
#        string = '\n'.join(string)
#       
#        if display:
#            print string
#        else:
#            return string
#    #--- End: def

    def _insert_construct_check_axes(self, item, axes, allow_scalar=True):
        '''
        '''
        ndim = item.ndim
        if not ndim and not allow_scalar:
            ndim = 1
            
        if len(set(axes)) != len(axes):
            raise ValueError("Can't insert {!r}: Duplicate axis".format(item))

        if len(axes) != ndim:
            raise ValueError(
"Can't insert {!r}: Mismatched axis size (got {}, expected {})".format(
    item, len(axes), ndim))

        domain_axes = self.domain_axes()
        for axis, size in izip_longest(axes, item.shape, fillvalue=1):
            if size != domain_axes[axis].size:
                raise ValueError(
"Can't insert {!r}: Mismatched axis size (got {}, expected {})".format(
    item, size, domain_axes[axis].size))
        #--- End: for

        return axes
    #--- End: def

    def equals(self, other, rtol=None, atol=None,
               ignore_fill_value=False, traceback=False,
               ignore=('Conventions',), **kwargs):
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

        kwargs2 = self._parameters(locals())
        return super(Field, self).equals(**kwargs2)
    #---End: def

    @abc.abstractmethod
    def expand_dims(self, position=0, axis=None, copy=True):
        '''Insert a size 1 axis into the data array.

:Parameters:

    position: `int`, optional
        Specify the position that the new axis will have in the data
        array. By default the new axis has position 0, the slowest
        varying position.

    {+axis}

    {+copy}

:Returns:

    out: `{+Variable}`
        The expanded field.

:Examples 2:

        '''
        pass
    #--- End: def

    @abc.abstractmethod
    def squeeze(self, axes=None, copy=True):
        '''Remove size-1 axes from the data array.

By default all size 1 axes are removed, but particular size 1 axes may
be selected for removal.

The axes are selected with the *axes* parameter.

Squeezed axes are not removed from the other obkjects (such as cell
measure objects) objects, nor are they removed from the domain
:Parameters:

    {+axes}

    {+copy}

:Returns:

    out: `{+Variable}`
        The squeezed field.

:Examples 2:

        '''
        pass
    #--- End: def

    def insert_auxiliary_coordinate(self, item, key=None, axes=None,
                                    copy=True, replace=True):
        '''Insert an auxiliary coordinate object into the {+variable}.

.. seealso:: `insert_domain_axis`, `insert_measure`, `insert_data`,
             `insert_dim`, `insert_ref`

:Parameters:

    item: `AuxiliaryCoordinate`
        The new auxiliary coordinate object. If it is not already a
        auxiliary coordinate object then it will be converted to one.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    axes: sequence of `str`, optional
        The ordered list of axes for the *item*. Each axis is given by
        its identifier. By default the axes are assumed to be
        ``'dim0'`` up to ``'dimM-1'``, where ``M-1`` is the number of
        axes spanned by the *item*.

    {+copy_item_in}
      
    replace: `bool`, optional
        If False then do not replace an existing auxiliary coordinate
        object of domain which has the same identifier. By default an
        existing auxiliary coordinate object with the same identifier
        is replaced with *item*.
    
:Returns:

    out: `str`
        The identifier for the inserted *item*.

:Examples:

>>>

        '''
        if not replace and key in self.auxiliary_coordinates():
            raise ValueError(
"Can't insert auxiliary coordinate object: Identifier {!r} already exists".format(key))

#        axes = self._insert_construct_check_axes(item, axes, allow_scalar=False)

        return self.Constructs.insert('auxiliarycoordinate', item,
                                      key=key, axes=axes, copy=copy)
    #--- End: def

    def insert_data(self, data, axes, copy=True, replace=True,
                    force=False):
        '''Insert a data array into the {+variable}.

:Examples 1:

>>> f.insert_data(d)

:Parameters:

    data: `Data`
        The data array to be inserted.

    axes: sequence of `str`
        A list of axis identifiers (``'dimN'``), stating the axes, in
        order, of the data array.

        The ``N`` part of each identifier should be replaced by an
        integer greater then or equal to zero such that either a) each
        axis identifier is the same as one in the field's domain, or
        b) if the domain has no axes, arbitrary integers greater then
        or equal to zero may be used, the only restriction being that
        the resulting identifiers are unique.

        If an axis of the data array already exists in the domain then
        the it must have the same size as the domain axis. If it does
        not exist in the domain then a new axis will be created.

        By default the axes will either be those defined for the data
        array by the domain or, if these do not exist, the domain axis
        identifiers whose sizes unambiguously match the data array.

    copy: `bool`, optional
        If False then the new data array is not deep copied prior to
        insertion. By default the new data array is deep copied.

    replace: `bool`, optional
        If False then raise an exception if there is an existing data
        array. By default an existing data array is replaced with
        *data*.
   
:Returns:

    `None`

:Examples 2:

>>> f.axes()
{'dim0': 1, 'dim1': 3}
>>> f.insert_data(Data([[0, 1, 2]]))

>>> f.axes()
{'dim0': 1, 'dim1': 3}
>>> f.insert_data(Data([[0, 1, 2]]), axes=['dim0', 'dim1'])

>>> f.axes()
{}
>>> f.insert_data(Data([[0, 1], [2, 3, 4]]))
>>> f.axes()
{'dim0': 2, 'dim1': 3}

>>> f.insert_data(Data(4))

>>> f.insert_data(Data(4), axes=[])

>>> f.axes()
{'dim0': 3, 'dim1': 2}
>>> data = Data([[0, 1], [2, 3, 4]])
>>> f.insert_data(data, axes=['dim1', 'dim0'], copy=False)

>>> f.insert_data(Data([0, 1, 2]))
>>> f.insert_data(Data([3, 4, 5]), replace=False)
ValueError: Can't initialize data: Data already exists
>>> f.insert_data(Data([3, 4, 5]))

        '''
        for axis in axes:
            if axis not in self.domain_axes():
                raise ValueError("asdajns dpunpuewnd p9wun lun 0[9io3jed pjn j nn jk")

        self._data_axes = list(axes)

        super(Field, self).insert_data(data, copy=copy)
    #--- End: def

    def remove_data(self):
        '''Docstring copied from Variable.remove_data

        '''
        self._data_axes = None
        return super(Field, self).remove_data()
    #--- End: def
    remove_data.__doc__ = Variable.remove_data.__doc__
    
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
    
    def insert_cell_method(self, cell_method, key=None, copy=True):
        '''Insert cell method objects into the {+variable}.

.. seealso:: `insert_aux`, `insert_measure`, `insert_ref`,
             `insert_data`, `insert_dim`

:Parameters:

    cell_method: `CellMethod`

:Returns:

    `None`

:Examples:

        '''
        self.Constructs.insert('cellmethod', cell_method, key=key, copy=copy)
    #--- End: def

    def insert_domain_axis(self, domain_axis, key=None, replace=True, copy=True):
        '''Insert a domain axis into the {+variable}.

.. seealso:: `insert_aux`, `insert_measure`, `insert_ref`,
             `insert_data`, `insert_dim`

:Parameters:

    axis: `DomainAxis`
        The new domain axis.

    key: `str`, optional
        The identifier for the new axis. By default a new,
        unique identifier is generated.
  
    replace: `bool`, optional
        If False then do not replace an existing axis with the same
        identifier but a different size. By default an existing axis
        with the same identifier is changed to have the new size.

:Returns:

    out: `str`
        The identifier of the new domain axis.


:Examples:

>>> f.insert_domain_axis(DomainAxis(1))
>>> f.insert_domain_axis(DomainAxis(90), key='dim4')
>>> f.insert_domain_axis(DomainAxis(23), key='dim0', replace=False)

        '''
        axes = self.domain_axes()
        if not replace and key in axes and axes[key].size != domain_axis.size:
            raise ValueError(
"Can't insert domain axis: Existing domain axis {!r} has different size (got {}, expected {})".format(
    key, domain_axis.size, axes[key].size))

        if copy:
            domain_axis = domain_axis.copy()

        return self.Constructs.insert('domainaxis', domain_axis, key=key)
    #--- End: def

    def insert_field_ancillary(self, construct, key=None, axes=None,
                               copy=True, replace=False):
        '''Insert a field ancillary object into the {+variable}.
        
    {+copy_item_in}
      
        '''
#        if not replace and key in self.field_ancillaries():
 #           raise ValueError(
#"Can't insert field ancillary object: Identifier {0!r} already exists".format(key))

        if replace:
            if key is None:
                raise ValueError("Must specify which construct to replace")

            return self.Constructs.replace(construct, key, axes=axes,
                                           copy=copy)
        #--- End: if
        
        return self.Constructs.insert('fieldancillary', construct, key=key,
                                      axes=axes, copy=copy)
    #--- End: def

    def insert_domain_ancillary(self, item, key=None, axes=None,
                                copy=True, replace=True):
        '''Insert a domain ancillary object into the {+variable}.
      
    {+copy_item_in}
        '''       
        if not replace and key in self.domain_ancillaries():
            raise ValueError(
"Can't insert domain ancillary object: Identifier {0!r} already exists".format(key))

#        axes = self._insert_construct_check_axes(item, axes, allow_scalar=False)

        return self.Constructs.insert('domainancillary', item, key=key, axes=axes,
                                      copy=copy)
    #--- End: def

    def _parameters(self, d):
        '''
.. versionadded:: 1.6
'''
        del d['self']
        if 'kwargs' in d:
            d.update(d.pop('kwargs'))
        return d
    #--- End: def

    def insert_item(self, role, item, key=None, axes=None,
                    copy=True, replace=True):
        '''Insert an item into the {+variable}.

.. seealso:: `insert_domain_axis`, `insert_measure`, `insert_data`,
             `insert_dim`, `insert_ref`

:Parameters:

    role: `str`

    item: `AuxiliaryCoordinate` or `cf.Coordinate` or `cf.DimensionCoordinate`
        The new auxiliary coordinate object. If it is not already a
        auxiliary coordinate object then it will be converted to one.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    axes: sequence of `str`, optional
        The ordered list of axes for the *item*. Each axis is given by
        its identifier. By default the axes are assumed to be
        ``'dim0'`` up to ``'dimM-1'``, where ``M-1`` is the number of
        axes spanned by the *item*.

    copy: `bool`, optional
        If False then the *item* is not copied before insertion. By
        default it is copied.
      
    replace: `bool`, optional
        If False then do not replace an existing auxiliary coordinate
        object of domain which has the same identifier. By default an
        existing auxiliary coordinate object with the same identifier
        is replaced with *item*.
    
:Returns:

    out: `str`
        The identifier for the inserted *item*.

:Examples:

>>>

        '''
        kwargs2 = self._parameters(locals())
        del kwargs2['role']

        if role == 'd':
            return self.insert_dim(**kwargs2)
        if role == 'a':
            return self.insert_aux(**kwargs2)
        if role == 'm':
            return self.insert_measure(**kwargs2)
        if role == 'c':
            return self.insert_domain_anc(**kwargs2)
        if role == 'f':
            return self.insert_field_anc(**kwargs2)
        if role == 'r':
            return self.insert_ref(**kwargs2)
    #--- End: def

    def insert_cell_measure(self, item, key=None, axes=None, copy=True, replace=True):
        '''Insert a cell measure object into the {+variable}.

.. seealso:: `insert_domain_axis`, `insert_aux`, `insert_data`,
             `insert_dim`, `insert_ref`

:Parameters:

    item: `CellMeasure`
        The new cell measure object.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    axes: sequence of `str`, optional
        The ordered list of axes for the *item*. Each axis is given by
        its identifier. By default the axes are assumed to be
        ``'dim0'`` up to ``'dimM-1'``, where ``M-1`` is the number of
        axes spanned by the *item*.

    {+copy_item_in}
      
    replace: `bool`, optional
        If False then do not replace an existing cell measure object
        of domain which has the same identifier. By default an
        existing cell measure object with the same identifier is
        replaced with *item*.
    
:Returns:

    out: 
        The identifier for the *item*.

:Examples:

>>>

        '''
        if not replace and key in self.cell_measures():
            raise ValueError(
"Can't insert cell measure object: Identifier {0!r} already exists".format(key))

#        axes = self._insert_construct_check_axes(item, axes, allow_scalar=False)

        return self.Constructs.insert('cellmeasure', item, key=key,
                                      axes=axes, copy=copy)
    #--- End: def

    def insert_dimension_coordinate(self, item, key=None, axes=None, copy=True, replace=True):
        '''Insert a dimension coordinate object into the {+variable}.

.. seealso:: `insert_aux`, `insert_domain_axis`, `insert_item`,
             `insert_measure`, `insert_data`, `insert_ref`,
             `remove_item`

:Parameters:

    item: `DimensionCoordinate` or `cf.Coordinate` or `cf.AuxiliaryCoordinate`
        The new dimension coordinate object. If it is not already a
        dimension coordinate object then it will be converted to one.

    axes: sequence of `str`, optional
        The axis for the *item*. The axis is given by its domain
        identifier. By default the axis will be the same as the given
        by the *key* parameter.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    {+copy_item_in}

    replace: `bool`, optional
        If False then do not replace an existing dimension coordinate
        object of domain which has the same identifier. By default an
        existing dimension coordinate object with the same identifier
        is replaced with *item*.
    
:Returns:

    out: 
        The identifier for the inserted *item*.

:Examples:

>>>

        '''
        if copy:
            item = item.copy()
            
#        if key is None and axes is None:
#            # Key is not set and axes is not set
#            item_size = item.size
#            c = [axis for axis, domain_axis in self.Axes.iteritems() 
#                 if domain_axis == item_size]
#            if len(c) == 1:
#                key = c[0]
#                if self.items(role='d', axes_all=key):
#                    key = self.insert_domain_axis(self._DomainAxis(item_size))
#                axes = [key]
#            elif not c:
#                key = self.insert_domain_axis(self._DomainAxis(item_size))
#                axes = [key]
#            else:
#                raise ValueError(
#"Ambiguous dimension coordinate object size. Condsider setting the key or axes parameter")

#        if key is not None:
#            if axes is None:
#                # Key is set, axes is not set
#                axes = [key]
#                if key not in self.Axes:
#                    key = self.insert_domain_axis(self._DomainAxis(item.size), key=key)
#            if axes != [key]:
#                # Key is set, axes is set
#                raise ValueError(
#                    "Incompatible key and axes parameters: {0!r}, {1!r}".format(
#                        key, axes))

#        axes = self._insert_construct_check_axes(item, axes, allow_scalar=False)
        
#        else:
#            # Key is not set, axes is set
#            key = axes[0]
#            axes = self._insert_construct_check_axes(item, axes, allow_scalar=False)    

        if not replace and key in self.dimension_coordinates():
            raise ValueError(
"Can't insert dimension coordinate object: Identifier {!r} already exists".format(key))

        return self.Constructs.insert('dimensioncoordinate', item, key=key, axes=axes,
                                      copy=copy)
    #--- End: def

    def insert_coordinate_reference(self, item, key=None, axes=None,
                                    copy=True, replace=True):
        '''Insert a coordinate reference object into the {+variable}.

.. seealso:: `insert_domain_axis`, `insert_aux`, `insert_measure`,
             `insert_data`, `insert_dim`
             
:Parameters:

    item: `CoordinateReference`
        The new coordinate reference object.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    axes: *optional*
        *Ignored*

    {+copy_item_in}

    replace: `bool`, optional
        If False then do not replace an existing coordinate reference object of
        domain which has the same identifier. By default an existing
        coordinate reference object with the same identifier is replaced with
        *item*.
    
:Returns:

    out: 
        The identifier for the *item*.


:Examples:

>>>

        '''
        return self.Constructs.insert('coordinatereference', item, key=key, copy=copy)
    #--- End: def

    def remove_item(self, description=None, role=None, axes=None,
                    axes_all=None, axes_subset=None,
                    axes_superset=None, ndim=None, inverse=False,
                    copy=True, key=False):
        '''Remove and return an item from the field.

{+item_definition}

By default all items of the domain are removed, but particular items
may be selected with the keyword arguments.

{+item_selection}

.. seealso:: `items`, `remove_axes`, `remove_axis`, `remove_item`

:Parameters:

    {+description}

    {+role}

    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+inverse}

    {+copy}

:Returns:

    out: 
        The removed item.

:Examples:

        '''
        kwargs2 = self._parameters(locals())

#        kwargs2['items'] = kwargs2.pop('item')

        del kwargs2['key']

        # Include coordinate references by default
        if kwargs2['role'] is None:
            kwargs2['role'] = ('d', 'a', 'm', 'c', 'f', 'r')

        items = self.items(**kwargs2)
        if len(items) == 1:
            out = self.remove_items(**kwargs2)
            if key:
                return out.popitem()[0]

            return out.popitem()[1]
        #--- End: if

        if not len(items):
            raise ValueError(
"Can't remove non-existent item defined by parameters {0}".format(kwargs2))
        else:
            raise ValueError(
"Can't remove non-unique item defined by parameters {0}".format(kwargs2))
    #--- End: def

    def remove_items(self, description=None, role=None, axes=None,
                     axes_all=None, axes_subset=None,
                     axes_superset=None, ndim=None, inverse=False,
                     copy=True):
        '''Remove and return items from the field.

An item is either a dimension coordinate, an auxiliary coordinate, a
cell measure or a coordinate reference object.

By default all items of the domain are removed, but particular items
may be selected with the keyword arguments.

.. seealso:: `items`, `remove_axes`, `remove_axis`, `remove_item`

:Parameters:

    {+description}

    {+role}

    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+inverse}

:Returns:

    out: `dict`
        A dictionary whose keys are domain item identifiers with
        corresponding values of the removed items. The dictionary may
        be empty.

:Examples:

        ''' 
        # Remove coordinate reference
        coordinate_references = self.coordinate_references()
        if key in coordinate_references:
            ref = self.Constructs.remove(key)
            return ref
                
        # Remove domain axis
        domain_axes = self.domain_axes()
        if key in domain_axes:
            if key in self.data_axes():
                raise ValueError(
"Can't remove domain axis that is spanned by the field's data")

            for k, v in self.variable_axes().items():
                if key in v:
                    raise ValueError(
"Can't remove domain axis that is spanned by {!r}".format(self.construct(k)))
            #--- End: if

            return self.Constructs.remove(key).copy()
        #--- End: if

        # Remove other construct
        if coordinate_references:
            construct_type = self.Constructs.type(key)
            if construct_type in ('_dimension_coordinate',
                                  '_auxiliary_coordinate',
                                  '_domain_ancillary'):
                # The removed item is a dimension coordinate,
                # auxiliary coordinate or domain ancillary, so replace
                # its identifier in any coordinate references with its
                # identity.
                identity_map = {key: self.Constructs.get(key).identity()}
                for key, ref in coordinate_references.items():
                   ref = ref.change_identifiers(
                       identity_map,
                       coordinate=(construct_type != '_domain ancillary'),
                       ancillary=(construct_type == '_domain ancillary'),
                       copy=True)
                   self.Constructs.replace(ref, key)
        #--- End: if

        return self.Constructs.remove(key).copy()
    #--- End: def

#--- End: class
