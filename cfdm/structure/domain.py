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
    
    def __init__(self, source=None, copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    source: 

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
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
#--- End: class
