from collections import abc

from .constructs import Constructs

import ..structure

# ====================================================================
#
# Domain object
#
# ====================================================================

class Domain(structure.Domain):
    '''A CF Domain construct.

The domain is defined collectively by teh following constructs, all of
which are optional:

====================  ================================================
Construct             Description
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

    '''
    __metaclass__ = abc.ABCMeta
    
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
       
        obj._Constructs = Constructs

        return obj
    #--- End: def
    
    def __init__(self, constructs=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    source: 

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        # Domain axes and items
        if constructs is None:
            constructs = self._Constructs(
                array_constructs=('dimensioncoordinate',
                                  'auxiliarycoordinate',
                                  'cellmeasure',
                                  'domainancillary'),
                non_array_constructs=('coordinatereference',
                                      'domainaxis')
            )
        else:
            constructs = constructs.subset(
                array_constructs=('dimensioncoordinate',
                                  'auxiliarycoordinate',
                                  'cellmeasure',
                                  'domainancillary'),
                non_array_constructs=('coordinatereference',
                                      'domainaxis'),
                copy=copy)
                
        if source is not None:
            constructs = source.Constructs            
            if copy:
                constructs = constructs.copy()

        self._private = {'properties' : {},
                         'special_attributes': {'constructs': constructs}
        }
    #--- End: def
    
    def __repr__(self):
        '''Called by the :py:obj:`repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        shape = sorted([domain_axis.size for domain_axis in self.domain_axes().values()])

        return '<{0}: {1}>'.format(self.__class__.__name__, shape)
    #--- End: def

    def __str__(self):
        '''Called by the :py:obj:`str` built-in function.

x.__str__() <==> str(x)

        '''
#        title = "Field: {0}".format(self.name(''))
#
#        # Append the netCDF variable name
#        ncvar = self.ncvar()
#        if ncvar is not None:
#            title += " (ncvar%{0})".format(ncvar)
#        
#        string = [title]
#        string.append(''.ljust(len(string[0]), '-'))

        string = []
        
        axis_name = self.domain_axis_name

        # Axes
#        data_axes = self.data_axes()
#        if data_axes is None:
#            data_axes = ()
#        non_spanning_axes = set(self.domain_axes()).difference(data_axes)

        axis_names = {}
        for key, domain_axis in self.domain_axes().iteritems():
            axis_names[key] = '{0}({1})'.format(axis_name(key),
                                                domain_axis.size)
        
        axis_to_name = {}
        def _print_item(self, key, variable, dimension_coord):
            '''Private function called by __str__'''
            
            if dimension_coord:
                # Dimension coordinate
                name = "{0}({1})".format(axis_name(key), self.domain_axes()[key].size)
                axis_to_name[key] = name
                
                variable = self.constructs().get(key, None)
                
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
                x = [variable.name(key)]
                x.append(shape)
            #--- End: if
                    
            if variable.hasdata:
#                if variable.isreftime:
#                    x.append(' = {}'.format(variable.data.asdata(variable.dtarray)))
#                else:
                x.append(' = {}'.format(variable.data))
                
            return ''.join(x)
        #--- End: def
                          
        # Dimension coordinates
        x = []
        for key in self.domain_axes():
            for k, dim in self.dimension_coordinates().items():
                if self.construct_axes()[k] == (key,):
                    name = dim.name(default='id%{0}'.format(k))
                    y = '{0}({1})'.format(name, dim.size)
                    if y != axis_names[key]:
                        y = '{0}({1})'.format(name, axis_names[key])
                    if dim.hasdata:
                        y += ' = {0}'.format(dim.data)
                    x.append(y)   
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
        x = sorted([ref.name(default='')
                    for ref in self.coordinate_references().values()])
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
                          
    @property
    def Constructs(self):
        return self._private['special_attributes']['constructs']
    
    def constructs(self, copy=False):
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

    def auxiliary_coordinates(self, copy=False):
        return self.Constructs.constructs('auxiliarycoordinate', copy=copy)

    def domain_axis_name(self, axis):
        '''
'''
        return self.Constructs.domain_axis_name(axis)
    #--- End: for
    
    def dimension_coordinates(self, copy=False):
        return self.Constructs.constructs('dimensioncoordinate', copy=copy)
    
    def domain_axes(self, copy=False):
        return self.Constructs.domain_axes(copy=copy)
    
    def domain_ancillaries(self, copy=False):
        return self.Constructs.constructs('domainancillary', copy=copy)
    
    def field_ancillaries(self, copy=False):
        return self.Constructs.constructs('fieldancillary', copy=copy)
    
    def cell_methods(self, copy=False):
        return self.Constructs.cell_methods(copy=copy)
    
    def cell_measures(self, copy=False):
        return self.Constructs.constructs('cellmeasure', copy=copy)
    
    def coordinate_references(self, copy=False):
        return self.Constructs.coordinate_references(copy=copy)
    
    def construct_axes(self, key=None):
        return self.Constructs.construct_axes(key=key)
    #--- End: def

    @property
    def isdomain(self): 
        '''True, denoting that the variable is a Domain object

:Examples:

>>> f.isfield
True

        '''
        return True
    #--- End: def

    def _dump_axes(self, display=True, _level=0):
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

        data_axes = self.data_axes()
        if data_axes is None:
            data_axes = ()

        axes = self.domain_axes()
        axis_name = self.domain_axis_name

        w = sorted(["{0}Domain Axis: {1}({2})".format(indent1, axis_name(axis), axes[axis].size)
                    for axis in axes
                    if axis not in data_axes])

        x = ["{0}Domain Axis: {1}({2})".format(indent1, axis_name(axis), axes[axis].size)
             for axis in data_axes]

        string = '\n'.join(w+x)

        if display:
            print string
        else:
            return string
    #--- End: def

    def dump(self, display=True, _level=0, _title='Field', _q='-'):
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

        title = '{0}{1}: {2}'.format(indent0, _title, self.name(''))

        # Append the netCDF variable name
        ncvar = getattr(self, 'ncvar', None)
        if ncvar is not None:
            title += " (ncvar%{0})".format(ncvar)

        line  = '{0}{1}'.format(indent0, ''.ljust(len(title)-_level*4, '-'))

        # Title
        string = [line, title, line]

        # Simple properties
        if self._simple_properties():
            string.append(
                self._dump_simple_properties(_level=_level,
                                             omit=('Conventions',
                                                   '_FillValue',
                                                   'missing_value',
                                                   'flag_values',
                                                   'flag_meanings',
                                                   'flag_masks')))
            
        # Flags
        flags = []
        for attr in ('flag_values', 'flag_meanings', 'flag_masks'):
            value = getattr(self, attr, None)
            if value is not None:
                flags.append('{0}{1} = {2}'.format(indent0, attr, value))
        #--- End: for
        if flags:
            string.append('')
            string.extend(flags)
            
        # Axes
        axes = self._dump_axes(display=False, _level=_level)
        if axes:
            string.extend(('', axes))
           
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

    def insert_auxiliary_coordinate(self, item, key=None, axes=None,
                                    copy=True, replace=True):
        '''Insert an auxiliary coordinate object.

.. versionadded:: 1.6

.. seealso:: `insert_cell_measure`, `insert_coordinate_reference`,
             `insert_dimension_coordinate`, `insert_domain_ancillary`,
             `insert_domain_axis`
             
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

        return self.Constructs.insert('auxiliarycoordinate', item,
                                      key=key, axes=axes, copy=copy)
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

        return self.Constructs.insert('domainaxis', domain_axis, key=key, copy=copy)
    #--- End: def

    def insert_domain_ancillary(self, item, key=None, axes=None,
                                copy=True, replace=True):
        '''Insert a domain ancillary object into the {+variable}.
      
    {+copy_item_in}
        '''       
        if not replace and key in self.domain_ancillaries():
            raise ValueError(
"Can't insert domain ancillary object: Identifier {0!r} already exists".format(key))

        return self.Constructs.insert('domainancillary', item, key=key, axes=axes,
                                      copy=copy)
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

#--- End: class
