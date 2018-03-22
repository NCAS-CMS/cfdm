import abc

import abstract
import mixin

from .constructs import Constructs
from .con_con import ConCon




# ====================================================================
#
# Domain object
#
# ====================================================================

class Domain(mixin.DomainConstructMethods, abstract.Properties):
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

    # Define the base of the identity keys for each construct type
    _construct_key_base = {'auxiliary_coordinate': 'auxiliarycoordinate',
                           'cell_measure'        : 'cellmeasure',
                           'coordinate_reference': 'coordinatereference',
                           'dimension_coordinate': 'dimensioncoordinate',
                           'domain_ancillary'    : 'domainancillary',
                           'domain_axis'         : 'domainaxis',
    }
    

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
       
        obj._Constructs = Constructs

        return obj
    #--- End: def
    
    def __init__(self, source=None, copy=True, _use_data=True, _constructs=None):
        '''**Initialization**

:Parameters:

    source: 

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        self._ignore = ('cell_method', 'field_ancillary')
        
        if _constructs is not None:
            super(Domain, self).__init__()
            self._set_component(3, 'constructs', None, _constructs)
            return
        
        super(Domain, self).__init__(source=source, copy=copy)
        
        if source is None:
            constructs = self._Constructs(**self._construct_key_base)
        else:
            constructs = source._get_constructs()
            constructs = constructs.subset(self._construct_key_base.keys(), copy=False)
            if copy or not _use_data:
                constructs = constructs.copy(data=_use_data)
        # --- End: if

        self._set_component(3, 'constructs', None, constructs)
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
                          
    def _get_constructs(self, *default):
        '''
.. versionadded:: 1.6
        
        '''
        return self._get_component(3, 'constructs', None, *default)
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

    def auxiliary_coordinates(self, copy=False):
        return self._get_constructs().constructs('auxiliary_coordinate', copy=copy)
    
    def cell_measures(self, copy=False):
        return self._get_constructs().constructs('cell_measure', copy=copy)

    def construct_axes(self, key=None):
        return self._get_constructs().construct_axes(key=key, ignore=self._ignore)
    
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

    def del_construct(self, key):
        '''
        '''
        return super(Domain, self).del_construct(key)

    def array_constructs(self, copy=False):
        return self._get_constructs().array_constructs(copy=copy, ignore=self._ignore)
    
    def auxiliary_coordinates(self, copy=False):
        return self._get_constructs().constructs('auxiliary_coordinate', copy=copy)
    
    def cell_measures(self, copy=False):
        return self._get_constructs().constructs('cell_measure', copy=copy)
    
    def construct_axes(self, key=None):
        return self._get_constructs().construct_axes(key=key, ignore=self._ignore)
    
    def construct_type(self, key):
        return self._get_constructs().construct_type(key)
       
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

>>> f.constructs()
[<DomainAxis: 96>,
 <DomainAxis: 1>,
 <DomainAxis: 15>,
 <DomainAxis: 72>,
 <CellMethod: dim3: mean>,
 <DimensionCoordinate: longitude(96) degrees_east>,
 <DimensionCoordinate: time(1) 360_day>,
 <DimensionCoordinate: air_pressure(15) hPa>,
 <DimensionCoordinate: latitude(72) degrees_north>]

        '''
        return self._get_constructs().constructs(copy=copy)
    #--- End: def
    
    def coordinate_references(self, copy=False):
        return self._get_constructs().constructs('coordinate_reference', copy=copy)
    
    def coordinates(self, copy=False):
        '''
        '''
        out = self.dimension_coordinates(copy=copy)
        out.update(self.auxiliary_coordinates(copy=copy))
        return out
    #--- End: def

    def get_construct(self, key, *default):
        '''
        '''
        constructs = self._get_constructs()
        if constructs.construct_type(key) in self._ignore:
            key = None

        return constructs.get_construct(key, *default)
    #--- End: def

    def dimension_coordinates(self, copy=False):
        return self._get_constructs().constructs('dimension_coordinate', copy=copy)
    
    def domain_ancillaries(self, copy=False):
        return self._get_constructs().constructs('domain_ancillary', copy=copy)
    
    def domain_axes(self, copy=False):
        return self._get_constructs().domain_axes(copy=copy)
    
    def domain_axis_name(self, axis):
        '''
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: for
    
#    def field_ancillaries(self, copy=False):
#        return self._get_constructs().constructs('field_ancillary', copy=copy)

    @abc.abstractmethod
    def del_construct(self, key):
        '''
        '''
        constructs = self._get_constructs()
        
#        if key in constructs.domain_axes():
#            # Remove a domain axis
#            domain_axis = True
#            
#            for k, value in self.construct_axes().iteritems():
#                if key in value:
#                    raise ValueError(
#"Can't remove domain axis that is spanned by {}: {!r}".format(
#    k, self.get_construct(k)))##
#
#        else:
#            domain_axis = False
#
#        if domain_axis:

#        # Remove reference to removed domain axis construct in
#        # cell method constructs
#        for cm_key, cm in self.cell_methods().iteritems():
#            axes = cm.get_axes()
#            if key not in axes:
#                continue
#            
#            axes = list(axes)
#            axes.remove(key)
#                cm.set_axes(axes)
#        else:

        # Remove reference to removed construct in coordinate
        # reference constructs
        for ref in self.coordinate_references().itervalues():
            for term, value in ref.domain_ancillaries().iteritems():
                if key == value:
                    ref.set_domain_ancillary(term, None)
                    
            for coord_key in ref.coordinates():
                if key == coord_key:
                    ref.del_coordinate(coord_key)
                    break
        #--- End: for
        
        return constructs.del_construct(key)
    #--- End: def

    def set_auxiliary_coordinate(self, item, key=None, axes=None,
                                 copy=True, replace=True):
        '''Insert an auxiliary coordinate object into the {+variable}.

.. seealso:: `set_domain_axis`, `set_measure`, `set_data`,
             `set_dim`, `set_ref`

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

        return self.set_construct('auxiliary_coordinate', item,
                                  key=key, axes=axes, copy=copy)
    #--- End: def

#    def set_cell_method(self, cell_method, key=None, copy=True):
#        '''Insert cell method objects into the {+variable}.
#
#.. seealso:: `set_aux`, `set_measure`, `set_ref`,
#             `set_data`, `set_dim`
#
#:Parameters:
#
#    cell_method: `CellMethod`
#
#:Returns:
#
#    `None`
#
#:Examples:
#
#        '''
#        self.set_construct('cell_method', cell_method, key=key,
#                           copy=copy)
#    #--- End: def

    def set_domain_axis(self, domain_axis, key=None, replace=True, copy=True):
        '''Insert a domain axis into the {+variable}.

.. seealso:: `set_aux`, `set_measure`, `set_ref`,
             `set_data`, `set_dim`

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

>>> f.set_domain_axis(DomainAxis(1))
>>> f.set_domain_axis(DomainAxis(90), key='dim4')
>>> f.set_domain_axis(DomainAxis(23), key='dim0', replace=False)

        '''
        axes = self.domain_axes()
        if not replace and key in axes and axes[key].size != domain_axis.size:
            raise ValueError(
"Can't insert domain axis: Existing domain axis {!r} has different size (got {}, expected {})".format(
    key, domain_axis.size, axes[key].size))

        return self.set_construct('domain_axis',
                                  domain_axis, key=key, copy=copy)
    #--- End: def

#    def set_field_ancillary(self, construct, key=None, axes=None,
#                            copy=True, replace=False):
#        '''Insert a field ancillary object into the {+variable}.
#        
#    {+copy_item_in}
#      
#        '''
#        if replace:
#            if key is None:
#                raise ValueError("Must specify which construct to replace")
#
#            return self._get_constructs().replace(construct, key, axes=axes,
#                                                 copy=copy)
#        #--- End: if
#        
#        return self.set_construct('field_ancillary', construct,
#                                  key=key, axes=axes,
#                                  copy=copy)
#    #--- End: def

    def set_domain_ancillary(self, item, key=None, axes=None,
                                copy=True, replace=True):
        '''Insert a domain ancillary object into the {+variable}.
      
    {+copy_item_in}
        '''       
        if not replace and key in self.domain_ancillaries():
            raise ValueError(
"Can't insert domain ancillary object: Identifier {0!r} already exists".format(key))

        return self.set_construct('domain_ancillary', item, key=key,
                                  axes=axes,
                                  copy=copy)
    #--- End: def

    def set_construct(self, construct_type, construct, key=None, axes=None,
                      copy=True):
        '''
        '''
        if construct_type in self._ignore:
            raise ValueError("asdas")
        
        return self._get_constructs().set_construct(construct_type,
                                                    construct,
                                                    key=key,
                                                    axes=axes,
                                                    copy=copy,
                                                    ignore=self._ignore)
    #--- End: def

    def set_construct_axes(self, key, axes):
        '''
        '''
        return self._get_constructs().set_construct_axes(key, axes)
    #--- End: def

    def set_cell_measure(self, item, key=None, axes=None, copy=True, replace=True):
        '''Insert a cell measure object into the {+variable}.

.. seealso:: `set_domain_axis`, `set_aux`, `set_data`,
             `set_dim`, `set_ref`

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

        return self.set_construct('cell_measure', item, key=key,
                                  axes=axes, copy=copy)
    #--- End: def

    def set_coordinate_reference(self, item, key=None, axes=None,
                                    copy=True, replace=True):
        '''Insert a coordinate reference object into the {+variable}.

.. seealso:: `set_domain_axis`, `set_aux`, `set_measure`,
             `set_data`, `set_dim`
             
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
        return self.set_construct('coordinate_reference',
                                  item, key=key, copy=copy)
    #--- End: def

    def set_dimension_coordinate(self, item, key=None, axes=None, copy=True, replace=True):
        '''Insert a dimension coordinate object into the {+variable}.

.. seealso:: `set_aux`, `set_domain_axis`, `set_item`,
             `set_measure`, `set_data`, `set_ref`,
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

        return self.set_construct('dimension_coordinate',
                                  item, key=key, axes=axes, copy=copy)
    #--- End: def

#--- End: class
