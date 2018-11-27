from __future__ import print_function
from builtins import (str, super)

from . import mixin
from . import core

from . import Constructs


class Domain(mixin.ConstructAccess,
             mixin.Container,
             core.Domain):
#        with_metaclass(
#        abc.ABCMeta,
#        type('NewBase', (mixin.ConstructAccess, mixin.Properties, structure.Domain), {}))):
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
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        return instance
    #--- End: def
    
    def __repr__(self):
        '''Called by the `repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        shape = sorted([domain_axis.get_size() for domain_axis in list(self.domain_axes().values())])
        shape = str(shape)
        shape = shape[1:-1]
        
        return '<{0}: {{{1}}}>'.format(self.__class__.__name__, shape)
    #--- End: def

    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

        '''
        def _print_item(self, key, variable, dimension_coord):
            '''Private function called by __str__'''
            
            if dimension_coord:
                # Dimension coordinate
                axis = self.construct_axes(key)[0]
                name = variable.name(ncvar=True, default=key)
                if variable.has_data():
                    name += '({0})'.format(variable.get_data().size)
                elif hasattr(variable, 'nc_external'):
                    if variable.nc_external():
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
                elif hasattr(variable, 'nc_external'):
                    if variable.nc_external():
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
                          
        string = []
        
        axis_name = self.domain_axis_name

        axis_names = self._unique_domain_axis_names()
        
        x = []
        for axis_cid in sorted(self.domain_axes()):
            for cid, dim in list(self.dimension_coordinates().items()):
                if self.construct_axes()[cid] == (axis_cid,):
                    name = dim.name(default='cid%{0}'.format(cid), ncvar=True)
                    y = '{0}({1})'.format(name, dim.get_data().size)
                    if y != axis_names[axis_cid]:
                        y = '{0}({1})'.format(name, axis_names[axis_cid])
                    if dim.has_data():
                        y += ' = {0}'.format(dim.get_data())
                        
                    x.append(y)
        #--- End: for
        if x:
            string.append('Dimension coords: {}'.format('\n                : '.join(x)))

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
        x = sorted([str(ref) for ref in list(self.coordinate_references().values())])
        if x:
            string.append('Coord references: {}'.format(
                '\n                : '.join(x)))
            
        # Domain ancillary variables
        x = [_print_item(self, cid, anc, False)
             for cid, anc in sorted(self.domain_ancillaries().items())]
        if x:
            string.append('Domain ancils   : {}'.format(
                '\n                : '.join(x)))
                                      
        string.append('')
        
        return '\n'.join(string)
    #--- End def
                          
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
    
**Examples**

        '''
        indent1 = '    ' * _level
        indent2 = '    ' * (_level+1)

        axes = self.domain_axes()

        w = sorted(["{0}Domain Axis: {1}".format(indent1, axis_names[axis])
                    for axis in axes])

        string = '\n'.join(w)

        if display:
            print(string)
        else:
            return string
    #--- End: def

    def domain_axis_name(self, key):
        '''TODO
        '''
        constructs = self._get_constructs()
        return constructs.domain_axis_name(key)
    #--- End: def

    def dump(self, display=True, _level=0, _title=None):
        '''A full description of the domain.

The domain components are described without abbreviation with the
exception of data arrays, which are abbreviated to their first and
last values.

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

        axis_to_name = self._unique_domain_axis_names()

        construct_name = self._unique_construct_names()
        
        string = []

        # Domain axes
        axes = self._dump_axes(axis_to_name, display=False, _level=_level)
        if axes:
            string.append(axes)
          
        # Dimension coordinates
        for key, value in sorted(self.dimension_coordinates().items()):
            string.append('')
            string.append(value.dump(display=False, _level=_level,
                                     _title='Dimension coordinate: {0}'.format(
                                         construct_name[key]),
                                     _axes=self.construct_axes(key),
                                     _axis_names=axis_to_name))
            
        # Auxiliary coordinates
        for key, value in sorted(self.auxiliary_coordinates().items()):
            string.append('')
            string.append(value.dump(display=False, _level=_level,
                                     _title='Auxiliary coordinate: {0}'.format(
                                         construct_name[key]),
                                     _axes=self.construct_axes(key),
                                     _axis_names=axis_to_name))

        # Domain ancillaries
        for key, value in sorted(self.domain_ancillaries().items()):
            string.append('') 
            string.append(value.dump(display=False, _level=_level,
                                     _title='Domain ancillary: {0}'.format(
                                         construct_name[key]),
                                     _axes=self.construct_axes(key),
                                     _axis_names=axis_to_name))
            
        # Coordinate references
        for key, value in sorted(self.coordinate_references().items()):
            string.append('')
            string.append(value.dump(display=False, _level=_level,
                                     _title='Coordinate reference: {0}'.format(
                                         construct_name[key]),
                                     _construct_names=construct_name,
                                     _auxiliary_coordinates=tuple(self.auxiliary_coordinates()),
                                     _dimension_coordinates=tuple(self.dimension_coordinates())))

        # Cell measures
        for key, value in sorted(self.cell_measures().items()):
            string.append('')
            string.append(value.dump(display=False, field=self,
                                     key=key, _level=_level,
                                     _title='Cell measure: {0}'.format(construct_name[key]),
                                     _axes=self.construct_axes(key),
                                     _axis_names=axis_to_name))


        string.append('')
        
        string = '\n'.join(string)
       
        if display:
            print(string)
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_type=False):
        '''TODO

.. versionadded:: 1.7
        '''
        ignore_properties = tuple(ignore_properties) + ('Conventions',)
            
        if not super().equals(other, rtol=rtol, atol=atol,
                              traceback=traceback,
                              ignore_data_type=ignore_data_type,
                              ignore_fill_value=ignore_fill_value,
                              ignore_properties=ignore_properties,
                              ignore_type=ignore_type):
            return False

        # ------------------------------------------------------------
        # Check the constructs
        # ------------------------------------------------------------              
        if not self._equals(self._get_constructs(), other._get_constructs(),
                            rtol=rtol, atol=atol,
                            traceback=traceback,
                            ignore_data_type=ignore_data_type,
                            ignore_type=ignore_type,
                            ignore_fill_value=ignore_fill_value):
            if traceback:
                print(
                    "{0}: Different {1}".format(self.__class__.__name__, 'constructs'))
            return False

        return True
    #--- End: def
        
#--- End: class
