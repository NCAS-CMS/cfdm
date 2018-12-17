from __future__ import print_function
from builtins import (str, super)

from . import mixin
from . import core

from . import Constructs


class Domain(mixin.ConstructAccess,
             mixin.Container,
             core.Domain):
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
        def _print_item(self, cid, variable, dimension_coord):
            '''Private function called by __str__'''
            
            if dimension_coord:
                # Dimension coordinate
#                axis = self.construct_axes(cid)[0]
                name = variable.name(ncvar=True, default=cid)
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
                x = [variable.name(ncvar=True, default=cid)]

                if variable.has_data():
                    shape = [axis_names[axis] for axis in self.construct_axes(cid)]
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
        x = [_print_item(self, cid, v, False) 
             for cid, v in sorted(self.auxiliary_coordinates().items())]
        if x:
            string.append('Auxiliary coords: {}'.format(
                '\n                : '.join(x)))
        
        # Cell measures
        x = [_print_item(self, cid, v, False)
             for cid, v in sorted(self.cell_measures().items())]
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
    
**Examples:**

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

    def del_construct(self, description=None, cid=None, axes=None,
                      construct_type=None):
        '''Remove a metadata construct.

The construct is identified via optional parameters. The *unique*
construct that satisfies *all* of the given criteria is removed. An
error is raised if multiple constructs satisfy all of the given
criteria.

If a domain axis construct is to be removed then it can't be spanned
by any data arrays.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`, `has_construct`,
             `set_construct`

:Parameters:

    description: `str`, optional
        Select constructs that have the given property, or other
        attribute, value.

        The description may be one of:

        * The value of the standard name property on its own. 

            *Example:*
              ``description='air_pressure'`` will select constructs
              that have a "standard_name" property with the value
              "air_pressure".

        * The value of any property prefixed by the property name and
          a colon (``:``).

            *Example:*
              ``description='positive:up'`` will select constructs
              that have a "positive" property with the value "up".

            *Example:*
              ``description='foo:bar'`` will select constructs that
              have a "foo" property with the value "bar".

            *Example:*
              ``description='standard_name:air_pressure'`` will select
              constructs that have a "standard_name" property with the
              value "air_pressure".

        * The measure of cell measure constructs, prefixed by
          ``measure%``.

            *Example:*
              ``description='measure%area'`` will select "area" cell
              measure constructs.

        * A construct identifier, prefixed by ``cid%`` (see also the
          *cid* parameter).

            *Example:* 
              ``description='cid%domainancillary1'`` will select
              domain ancillary construct with construct identifier
              "domainancillary1". This is equivalent to
              ``cid='domainancillary1'``.

        * The netCDF variable name, prefixed by ``ncvar%``.

            *Example:*
              ``description='ncvar%lat'`` will select constructs with
              netCDF variable name "lat".

        * The netCDF dimension name of domain axis constructs,
          prefixed by ``ncdim%``.

            *Example:*
              ``description='ncdim%time'`` will select domain axis
              constructs with netCDF dimension name "time".

    cid: `str`, optional
        Select the construct with the given construct identifier.

        *Example:*
          ``cid='domainancillary0'`` will the domain ancillary
          construct with construct identifier "domainancillary1". This
          is equivalent to ``description='cid%domainancillary0'``.

    construct_type: `str`, optional
        Select constructs of the given type. Valid types are:

          ==========================  ================================
          *construct_type*            Constructs
          ==========================  ================================
          ``'domain_ancillary'``      Domain ancillary constructs
          ``'dimension_coordinate'``  Dimension coordinate constructs
          ``'domain_axis'``           Domain axis constructs
          ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
          ``'cell_measure'``          Cell measure constructs
          ``'coordinate_reference'``  Coordinate reference constructs
          ==========================  ================================

        *Example:*
          ``construct_type='dimension_coordinate'``

        *Example:*
          ``construct_type=['auxiliary_coordinate']``

        *Example:*
          ``construct_type=('domain_ancillary', 'cell_measure')``

    axes: sequence of `str`, optional
        Select constructs which have data that spans one or more of
        the given domain axes, in any order. Domain axes are specified
        by their construct identifiers.

        *Example:*
          ``axes=['domainaxis2']``

        *Example:*
          ``axes=['domainaxis0', 'domainaxis1']``

:Returns:

    out:
        The removed metadata construct.

**Examples:**

>>> c = f.del_construct('grid_latitude')
>>> c = f.del_construct('long_name:Air Pressure')
>>> c = f.del_construct('ncvar%lat)
>>> c = f.del_construct('cid%cellmeasure0')
>>> c = f.del_construct(cid='domainaxis2')
>>> c = f.del_construct(construct_type='auxiliary_coordinate',
...                     axes=['domainaxis1'])

        '''
        cid = self.get_construct_id(description=description, cid=cid,
                                    construct_type=construct_type,
                                    axes=axes)
        
        return self._get_constructs().del_construct(cid=cid)
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

.. versionadded:: 1.7.0
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
