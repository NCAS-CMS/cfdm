import abc

import mixin
import structure

from .constructs import Constructs

# ====================================================================
#
# Domain object
#
# ====================================================================

class Domain(mixin.Properties, structure.Domain):
    '''A CF Domain construct.

The domain is defined collectively by the following constructs, all of
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
    
    def __repr__(self):
        '''Called by the :py:obj:`repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        shape = sorted([domain_axis.get_size() for domain_axis in self.domain_axes().values()])

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
                                                domain_axis.get_size())
        
        axis_to_name = {}
        def _print_item(self, key, variable, dimension_coord):
            '''Private function called by __str__'''
            
            if dimension_coord:
                # Dimension coordinate
                name = "{0}({1})".format(axis_name(key), self.domain_axes()[key].get_size())
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
        ignore_properties = tuple(ignore_properties) + ('Conventions',)
            
        if not super(Domain, self).equals(
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
        if not self._equals(self._get_constructs(), other._get_constructs(),
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
        
#--- End: class
