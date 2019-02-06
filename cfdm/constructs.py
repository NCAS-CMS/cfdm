from __future__ import print_function
from builtins import (super, zip)
from past.builtins import basestring

from . import core


class Constructs(core.Constructs):
    '''<TODO>

.. versionadded:: 1.7.0

    ''' 
       
    def __call__(self, name):
        '''TODO
        '''
        return self.name(name)
    #--- End: def
    
    def __repr__(self):
        '''Called by the `repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        construct_types = ['{0}({1})'.format(c, len(v))
                           for c, v in sorted(self._constructs.items())
                           if len(v) and c not in self._ignore]    
        
        return '<{0}: {1}>'.format(self.__class__.__name__, ', '.join(construct_types))
    #--- End: def

    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

        '''
        out = ['Constructs:']

        construct_types = [c
                           for c, v in sorted(self._constructs.items())
                           if len(v) and c not in self._ignore]    

        first = '{'
        for construct_type in construct_types:
            for key, value in sorted(self._constructs[construct_type].items()):
                if first:
                    out[0] = out[0] + '\n{{{!r}: {!r},'.format(key, value)
                    first = False
                else:
                    out.append('{!r}: {!r},'.format(key, value))
                
        if first:
            out[0] = out[0] + '\n{}'
        else:
            out[-1] = out[-1][:-1] + '}'

        return '\n '.join(out)
    #--- End: def

    def domain_axis_name(self, key):
        '''Return the canonical name for an axis.

:Parameters:

    key: `str`
        The key for the domain axis construct.

        *Parameter example:*
          ``key='domainaxis2'``

:Returns:

    `str`
        The canonical name for the axis.

**Examples:**

>>> f.domain_axis_name('domainaxis1')
'longitude'

        '''
        domain_axes = self.type('domain_axis')
        
        if key not in domain_axes:
            return default

        constructs_data_axes = self.data_axes()

#        dimension_coordinates = self.type('dimension_coordinate')

        name = None        
        for dkey, dim in self.type('dimension_coordinate').items():
            if constructs_data_axes[dkey] == (key,):
                # Get the name from a dimension coordinate
                name = dim.name(ncvar=False, default=None)
                break
        #--- End: for
        if name is not None:
            return name

#        auxiliary_coordinates = self.type('auxiliary_coordinate')
        
        found = False
        for akey, aux in self.type('auxiliary_coordinate').items():
            if constructs_data_axes[akey] == (key,):
                if found:
                    name = None
                    break
                
                # Get the name from an auxiliary coordinate
                name = aux.name(ncvar=False, default=None)
                found = True
        #--- End: for
        if name is not None:
            return name

        ncdim = domain_axes[key].nc_get_dimension(None)
        if ncdim is not None:
            # Get the name from a netCDF dimension
            return 'ncdim%{0}'.format(ncdim)

        # Get the name from the identifier
        return 'key%{0}'.format(key)
    #--- End: def

    def equals(self, other, rtol=None, atol=None, verbose=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_compression=False, ignore_type=False):
        '''TODO

.. versionadded:: 1.7.0
        
        '''
        if self is other:
            return True
        
        # Check that each instance is the same type
        if type(self) != type(other):
            if verbose:
                print("{0}: Different object types: {0}, {1}".format(
                    self.__class__.__name__, other.__class__.__name__))
            return False
        
        axes0_to_axes1 = {}
        axis0_to_axis1 = {}
        axis1_to_axis0 = {}
        key1_to_key0   = {}
        
        # ------------------------------------------------------------
        # Domain axis constructs
        # ------------------------------------------------------------
        if not self._equals_domain_axis(other, rtol=rtol, atol=atol,
                                        verbose=verbose,
                                        ignore_type=ignore_type,
                                        axis1_to_axis0=axis1_to_axis0,
                                        key1_to_key0=key1_to_key0):
            return False
        
        # ------------------------------------------------------------
        # Constructs with arrays
        # ------------------------------------------------------------
        axes_to_constructs0 = self.axes_to_constructs()
        axes_to_constructs1 = other.axes_to_constructs()
        for axes0, constructs0 in axes_to_constructs0.items():
            matched_all_constructs_with_these_axes = False

            log = []
            
            len_axes0 = len(axes0) 
            for axes1, constructs1 in tuple(axes_to_constructs1.items()):
                log = []
                constructs1 = constructs1.copy()

                matched_roles = False

                if len_axes0 != len(axes1):
                    # axes1 and axes0 contain differents number of
                    # domain axes.
                    continue

                for construct_type in self._array_constructs:
                    matched_role = False
                    role_constructs0 = constructs0[construct_type]
                    role_constructs1 = constructs1[construct_type].copy()

                    if len(role_constructs0) != len(role_constructs1):
                        # There are the different numbers of
                        # constructs of this type
                        matched_all_constructs_with_these_axes = False
                        log.append('Different numbers of '+construct_type)
                        break

                    # Check that there are matching pairs of equal
                    # constructs
                    for key0, item0 in role_constructs0.items():
                        matched_construct = False
                        for key1, item1 in tuple(role_constructs1.items()):
                            if item0.equals(item1,
                                            rtol=rtol, atol=atol,
                                            verbose=False,
                                            ignore_data_type=ignore_data_type,
                                            ignore_fill_value=ignore_fill_value,
                                            ignore_compression=ignore_compression,
                                            ignore_type=ignore_type):
                                del role_constructs1[key1]
                                key1_to_key0[key1] = key0
                                matched_construct = True
                                break
                        #--- End: for

                        if not matched_construct:
                            log.append("Can't match "+construct_type+" "+repr(item0))
                            break
                    #--- End: for

                    if role_constructs1:
                        # At least one construct in other is not equal
                        # to a construct in self
                        break

                    # Still here? Then all constructs of this type
                    # that spanning these axes match
                    del constructs1[construct_type]
                #--- End: for

                matched_all_constructs_with_these_axes = not constructs1

                if matched_all_constructs_with_these_axes:
                    del axes_to_constructs1[axes1]
                    break
            #--- End: for

            if not matched_all_constructs_with_these_axes:
                if verbose:
                    names = [self.domain_axis_name(axis0) for axis0 in axes0]
                    print("Can't match constructs spanning axes {0}".format(names))
                    print('\n'.join(log))
                    print()
                    print(axes_to_constructs0)
                    print()
                    print(axes_to_constructs1)
                return False

            # Map item axes in the two instances
            axes0_to_axes1[axes0] = axes1
        #--- End: for

        for axes0, axes1 in axes0_to_axes1.items():
            for axis0, axis1 in zip(axes0, axes1):
                if axis0 in axis0_to_axis1 and axis1 != axis0_to_axis1[axis0]:
                    if verbose:
                        print(
"Field: Ambiguous axis mapping ({} -> both {} and {})".format(
    self.domain_axis_name(axes0), other.domain_axis_name(axis1),
    other.domain_axis_name(axis0_to_axis1[axis0])))
                    return False
                elif axis1 in axis1_to_axis0 and axis0 != axis1_to_axis0[axis1]:
                    if verbose:
                        print(
"Field: Ambiguous axis mapping ({} -> both {} and {})".format(
    self.domain_axis_name(axis0), self.domain_axis_name(axis1_to_axis0[axis0]),
    other.domain_axis_name(axes1)))
                    return False

                axis0_to_axis1[axis0] = axis1
                axis1_to_axis0[axis1] = axis0
        #--- End: for

        # ------------------------------------------------------------
        # Constructs with no arrays
        # ------------------------------------------------------------
        for construct_type in self._non_array_constructs:
            if not getattr(self, '_equals_'+construct_type)(
                    other,
                    rtol=rtol, atol=atol,
                    verbose=verbose,
                    ignore_type=ignore_type,
                    axis1_to_axis0=axis1_to_axis0,
                    key1_to_key0=key1_to_key0):
                return False

        # ------------------------------------------------------------
        # Still here? Then the two objects are equal
        # ------------------------------------------------------------     
        return True
    #--- End: def

    def axis(self, axis):
        '''Select metadata constructs

By default all metadata constructs are selected, but a subset may be
chosen via the optional parameters. If multiple parameters are
specified, then the constructs that satisfy *all* of the criteria are
returned.

.. versionadded:: 1.7.0

.. seealso:: `get`, `keys`, 'items`, `values`

:Parameters:

    axis: (sequence of) `str`, optional
        Select constructs which have data that spans a domain axis
        construct, defined by its construct identifier. If multiple of
        domain axes are specified then select constructs whose data
        spans at least one the domain axis constructs.

        *Parameter example:*
          ``axis='domainaxis1'``

        *Parameter example:*
          ``axis=['domainaxis2']``

        *Parameter example:*
          ``axis=['domainaxis0', 'domainaxis1']``

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

TODO

        '''
        out = self.shallow_copy()

        if isinstance(axis, basestring):
            axis = (axis,)

        axis = set(axis)

        constructs_data_axes = self.data_axes()
        for cid in tuple(out):
            x = constructs_data_axes.get(cid)
            if x is None or not axis.intersection(x):
                # This construct does not span these axes
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def key(self, key):
        '''Select metadata constructs

By default all metadata constructs are selected, but a subset may be
chosen via the optional parameters. If multiple parameters are
specified, then the constructs that satisfy *all* of the criteria are
returned.

.. versionadded:: 1.7.0

.. seealso:: `get`, `keys`, 'items`, `values`

:Parameters:

    key: (sequence of) `str`, optional
        Select the construct with the given construct key. If multiple
        keys are specified then select all of the metadata constructs
        which have any of the given keys.

        *Parameter example:*
          ``key='domainancillary0'``

        *Parameter example:*
          ``key=['cellmethod2']``

        *Parameter example:*
          ``key=('dimensioncoordinate1', 'fieldancillary0')``

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

TODO

        '''
        out = self.shallow_copy()

        if isinstance(key, basestring):
            key = (key,)

        for cid in tuple(out):
            if cid not in key:
                out._pop(cid)
        #--- End: for

        return out
    #--- End: def

    def measure(self, measure):
        '''Select cell measure constructs by measure.

.. versionadded:: 1.7.0

.. seealso:: TODO

:Parameters:

    measure: (sequence of) `str`
        Select cell measure constructs which have the given
        measure. If multiple measures are specified then select the
        cell measure constructs which have any of the given measures.

        *Parameter example:*
          ``measure='area'``

        *Parameter example:*
          ``measure=['area']``

        *Parameter example:*
          ``measure=['area', 'volume']``

:Returns:

    `Constructs`
        The selected cell meausure constructs and their construct
        keys.
        
**Examples:**

TODO

        '''
        if isinstance(measure , basestring):
            measure = (measure,)

        out = self.shallow_copy()
        
        for cid, construct in tuple(out.items()):
            try:
                get_measure = construct.get_measure
            except AttributeError:
                # This construct doesn't have a "get_measure" method
                out._pop(cid)
                continue

            ok = False
            for x0 in measure:
                x1 = get_measure(None)
                if x1 is not None and construct._equals(x1, x0):
                    # This construct matches this measure
                    ok = True
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the measures
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def method(self,method):
        '''Select metadata constructs

By default all metadata constructs are selected, but a subset may be
chosen via the optional parameters. If multiple parameters are
specified, then the constructs that satisfy *all* of the criteria are
returned.

.. versionadded:: 1.7.0

.. seealso:: `get`, `keys`, 'items`, `values`

:Parameters:

TODO

:Returns:

    `Constructs`
        The selected cell method constructs and their construct keys.

**Examples:**

TODO

        '''
        out = self.shallow_copy()

        if isinstance(method, basestring):
            method = (method,)

        for cid, construct in tuple(out.items()):
            try:
                get_method = construct.get_method
            except AttributeError:
                # This construct doesn't have a "get_method" method
                out._pop(cid)
                continue

            ok = False
            for x0 in method:
                x1 = get_method(None)
                if x1 is not None and construct._equals(x1, x0):
                    # This construct matches this method
                    ok = True
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the methods
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def name(self, name):
        '''Select metadata constructs by name/

By default all metadata constructs are selected, but a subset may be
chosen via the optional parameters. If multiple parameters are
specified, then the constructs that satisfy *all* of the criteria are
returned.

Construct names are generally based on property values, or on the
netCDF names that the construct may have. A construct has a set of
default names that only consider certain properties that have
particular menings in CF. These default names may be found with the
construct's `!all_names` method, for example:

   >>> c.properties()
   {'standard_name': 'longitude',
    'long_name': Longitude',
    'units': 'degrees_east',
    'foo': 'bar'}
   >>> c.nc_get_variable()
   'lon'
   >>> c.all_names()
   ['longitude', 'long_name=Longitude', 'ncvar%lon']


names inherited from netCDF
fielsd is typically the description that is displayed when the
construct is inspected, and so it is often convienient to copy this
name when selecting metadata constructs. For example, the three
auxiliary coordinate constructs in the field construct t have names
'latitude', 'longitude' and 'long_name=Grid latitude name'. Selection
by name does not require a keyword parameter, although the keyword
name can be used:

A construct has a number of default names, and is selected if any of
them match any of the given names. The construct's default names are
returned by the construct's `!all_names` method. In the following
example, the construct ``c`` has three default names:

   >>> c.properties()
   {'standard_name': 'longitude',
    'long_name': Longitude',
    'units': 'degrees_east',
    'foo': 'bar'}
   >>> c.nc_get_variable()
   'lon'
   >>> c.all_names()
   ['longitude', 'long_name=Longitude', 'ncvar%lon']

.. versionadded:: 1.7.0

.. seealso:: TODO

:Parameters:

    name: (sequence of) `str`
        Select constructs that have the given name. If a sequence of
        names has been given then the constructs that have any of the
        names are selected.
       
        A construct has a number of default names, and is selected if
        any of them match any of the given names. The construct's
        default names are returned by the construct's `!all_names`
        method. In the followinf example, the construct ``c`` has
        three default names:

           >>> c.all_names()
           ['longitude', 'long_name=Longitude', 'ncvar%lon']

        It is also possible for a construct to be selected by a name
        based on any construct property, or the construct's key.s

        Note that the names used to identify metadata constructs in
        the ouput of a `print` or `!dump` call are one of the default
        names and so may always be used when selecting constructs by
        name.

        A name may be one of:

        * The value of the standard name property.

          *Parameter example:*
            ``name='air_pressure'`` will select constructs that have a
            "standard_name" property with the value
            "air_pressure". This selection could also be made with
            ``name='standard_name=air_pressure'``.

        * The value of any property prefixed by the property name and
          an equals (``=``).

          *Parameter example:*
            ``name='long_name=Air Temperature'`` will select
            constructs that have a "long_name" property with the value
            "Air Temperature".

          *Parameter example:*
            ``name='positive=up'`` will select constructs that have a
            "positive" property with the value "up".

          *Parameter example:*
            ``name='foo=bar'`` will select constructs that have a
            "foo" property with the value "bar".

          *Parameter example:*

            ``name='standard_name=air_pressure'`` will select
            constructs that have a "standard_name" property with the
            value "air_pressure". This selection could also be made
            with ``name='air_pressure'``.

        * The measure of cell measure constructs, prefixed by
          ``measure:``.

          *Parameter example:*
            ``name='measure:area'`` will select "area" cell measure
            constructs.

        * The method of cell method constructs, prefixed by
          ``method:``.

          *Parameter example:*
            ``name='method:maximum'`` will select cell method
            constructs with methods of "maximum".

        * The netCDF variable name, prefixed by ``ncvar%``.
          
          *Parameter example:*
            ``name='ncvar%lat'`` will select constructs with netCDF
            variable name "lat".

        * The netCDF dimension name of domain axis constructs,
          prefixed by ``ncdim%``.

          *Parameter example:*
            ``name='ncdim%time'`` will select domain axis constructs
            with netCDF dimension name "time".

        * A construct identifier, prefixed by ``key%``.

          *Parameter example:* 
            ``name='key%dimensioncoordinate1'`` will select dimension
            coordanate constructs with construct identifier
            "dimensioncoordinate1".

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

TODO

        '''
        out = self.shallow_copy()
        
        if isinstance(name, basestring):
            name = (name,)

        for cid, construct in tuple(out.items()):
            ok = False
            names = set(construct.names(extra=('key%'+cid,)))
            for n in name:
                if n in names:
                    # This construct matches this name
                    ok = True
                    break
#
#                else:
#                    (prefix, _, value) = n.partition('%')
#                    if prefix == 'key' and value == cid:
#                        # This construct matches this name
#                        ok = True
#                        break
#                elif n in names:
#                    # This construct matches this name
#                    ok = True
#                    break
#
#                    (prefix, _, value) = n.partition('=')
#                    custom = (prefix,) if value else None
#                    if n in construct.name(custom=custom,
#                                           all_names=True):
#                        # This construct matches this name
#                        ok = True
#                        break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the names
                out._pop(cid)
        #--- End: for

        return out
    #--- End: def

    def ncdim(self, ncdim):
        '''Select metadata constructs

By default all metadata constructs are selected, but a subset may be
chosen via the optional parameters. If multiple parameters are
specified, then the constructs that satisfy *all* of the criteria are
returned.

.. versionadded:: 1.7.0

.. seealso:: `get`, `keys`, 'items`, `values`

:Parameters:

    ncdim: (sequence of) `str`, optional
        Select domain axis constructs which have the given netCDF
        dimension name. If multiple netCDF dimension names are
        specified then select the domain axis constructs which have
        any of the given netCDF dimension names.

        *Parameter example:*
          ``ncdim='lon'``

        *Parameter example:*
          ``ncdim=['lat']``

        *Parameter example:*
          ``ncdim=['lon', 'lat']``

:Returns:

    `Constructs`
        The selected domain axis constructs and their construct keys.

**Examples:**

TODO
        '''
        out = self.shallow_copy()

        if isinstance(ncdim , basestring):
            ncdim = (ncdim,)
            
        for cid, construct in tuple(out.items()):
            try:
                nc_get_dimension = construct.nc_get_dimension
            except AttributeError:
                # This construct doesn't have a "nc_get_dimension"
                # method
                out._pop(cid)
                continue

            ok = False
            for x0 in ncdim:
                x1 = nc_get_dimension(None)
                if x1 is not None and construct._equals(x1, x0):
                    # This construct matches this netCDF dimension
                    # name
                    ok = True
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the netCDF
                # dimension names
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def ncvar(self, ncvar):
        '''Select metadata constructs

By default all metadata constructs are selected, but a subset may be
chosen via the optional parameters. If multiple parameters are
specified, then the constructs that satisfy *all* of the criteria are
returned.

.. versionadded:: 1.7.0

.. seealso:: `get`, `keys`, 'items`, `values`

:Parameters:

    ncvar: (sequence of) `str`, optional
        Select constructs which have the given netCDF variable
        name. If multiple netCDF variable names are specified then
        select the constructs which have any of the given netCDF
        variable names.

        *Parameter example:*
          ``ncvar='lon'``

        *Parameter example:*
          ``ncvar=['lat']``

        *Parameter example:*
          ``ncvar=['lon', 'lat']``

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**
TODO

        '''
        out = self.shallow_copy()

        if isinstance(ncvar , basestring):
            ncvar = (ncvar,)

        for cid, construct in tuple(out.items()):
            try:
                nc_get_variable = construct.nc_get_variable
            except AttributeError:
                # This construct doesn't have a "nc_get_variable"
                # method
                out._pop(cid)
                continue

            ok = False
            for x0 in ncvar:
                x1 = nc_get_variable(None)
                if x1 is not None and construct._equals(x1, x0):
                    # This construct matches this netCDF variable name
                    ok = True
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the netCDF
                # variable names
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def
    
    def property(self, **properties):
        '''Select metadata constructs

By default all metadata constructs are selected, but a subset may be
chosen via the optional parameters. If multiple parameters are
specified, then the constructs that satisfy *all* of the criteria are
returned.

.. versionadded:: 1.7.0

.. seealso:: `get`, `keys`, 'items`, `values`

:Parameters:

TODO

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

TODO

        '''
        out = self.shallow_copy()

        if isinstance(properties, dict):
            properties = (properties,)

        for cid, construct in tuple(out.items()):
            try:
                get_property = construct.get_property
            except AttributeError:
                # This construct doesn't have a "get_property" method
                out._pop(cid)
                continue
            
            ok = False
            for props in properties:
                ok = False
                for p, value0 in props.items():
                    value1 = get_property(p, None)
                    if value1 is None or not construct._equals(value1, value0):
                        # This construct does not match this property
                        ok = False                            
                        break
                    else:
                        ok = True
                #--- End: for

                if ok:
                    # This construct matches this set of properties
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the sets of
                # properties
                out._pop(cid)
        #--- End: for
               
        return out
    #--- End: def

    def _equals_coordinate_reference(self, other, rtol=None,
                                     atol=None, verbose=False,
                                     ignore_type=False,
                                     axis1_to_axis0=None,
                                     key1_to_key0=None):
        '''
        '''
        refs0 = dict(self.type('coordinate_reference'))
        refs1 = dict(other.type('coordinate_reference'))

        if len(refs0) != len(refs1):
            if verbose:
                print(
"Verbose: Different coordinate references: {0!r}, {1!r}".format(
    list(refs0.values()), list(refs1.values())))
            return False

        if refs0:
            for ref0 in refs0.values():
                found_match = False
                for key1, ref1 in tuple(refs1.items()):
                    if not ref0.equals(ref1, rtol=rtol, atol=atol,
                                       verbose=False,
                                       ignore_type=ignore_type):
                        continue

                    # Coordinates
                    coordinates0 = ref0.coordinates()
                    coordinates1 = set()
                    for value in ref1.coordinates():
                        coordinates1.add(key1_to_key0.get(value, value))
                        
                    if coordinates0 != coordinates1:
                        continue
    
                    # Domain ancillary-valued coordinate conversion terms
                    terms0 = ref0.coordinate_conversion.domain_ancillaries()

                    terms1 = {term: key1_to_key0.get(key, key)
                              for term, key in ref1.coordinate_conversion.domain_ancillaries().items()}

                    if terms0 != terms1:
                        continue
    
                    found_match = True
                    del refs1[key1]                                       
                    break
                #--- End: for
    
                if not found_match:
                    if verbose:
                        print(
"Verbose: No match for {0!r})".format(ref0))
                    return False
            #--- End: for
        #--- End: if

        return True
    #--- End: def

    def _equals_cell_method(self, other, rtol=None, atol=None,
                            verbose=False, ignore_type=False,
                            axis1_to_axis0=None, key1_to_key0=None):
        '''TODO

        '''
        cell_methods0 = self.type('cell_method')
        cell_methods1 = other.type('cell_method')

        if len(cell_methods0) != len(cell_methods1):
            if verbose:
                print(
"Verbose: Different numbers of cell methods: {0!r} != {1!r}".format(
    cell_methods0, cell_methods1))
            return False
        
#        axis0_to_axis1 = {}
#        for axis0, axis1 in axis1_to_axis0.items():
#            axis0_to_axis1[axis0] = axis1
            
        axis0_to_axis1 = {axis0: axis1
                          for axis0, axis1 in axis1_to_axis0.items()}
            
        for cm0, cm1 in zip(tuple(cell_methods0.values()),
                            tuple(cell_methods1.values())):
            
            # Check that there are the same number of axes
            axes0 = cm0.get_axes(())
            axes1 = list(cm1.get_axes(()))
            if len(axes0) != len(axes1):
                if verbose:
                    print(
"{0}: Different cell methods (mismatched axes): {1!r}, {2!r}".format(
    cm0.__class__.__name__, cell_methods0, cell_methods1))
                return False
    
            indices = []
            for axis0 in axes0:
                if axis0 is None:
                    return False
                for axis1 in axes1:
                    if axis0 in axis0_to_axis1 and axis1 in axis1_to_axis0:
                        if axis1 == axis0_to_axis1[axis0]:
                            axes1.remove(axis1)
                            indices.append(cm1.get_axes(()).index(axis1))
                            break
                    elif axis0 in axis0_to_axis1 or axis1 in axis1_to_axis0:
                        if verbose:
                            print(
"Verbose: Different cell methods (mismatched axes): {0!r}, {1!r}".format(
    cell_methods0, cell_methods1))
                        return False
                    elif axis0 == axis1:
                        # Assume that the axes are standard names
                        axes1.remove(axis1)
                        indices.append(cm1.get_axes(()).index(axis1))
                    elif axis1 is None:
                        if verbose:
                            print(
"Verbose: Different cell methods (mismatched axes): {0!r}, {1!r}".format(
    cell_methods0, cell_methods1))
                        return False
            #--- End: for

            if len(cm1.get_axes(())) != len(indices):
                if verbose:
                    print("Field: Different cell methods: {0!r}, {1!r}".format(
                        cell_methods0, cell_methods1))
                return False

            cm1 = cm1.sorted(indices=indices)
            cm1.set_axes(axes0)

            if not cm0.equals(cm1, atol=atol, rtol=rtol,
                              verbose=verbose,
                              ignore_type=ignore_type):
                if verbose:
                    print(
"Verbose: Different cell methods: {0!r}, {1!r}".format(
    cell_methods0, cell_methods1))
                return False                
        #--- End: for

        return True
    #--- End: def

    def _equals_domain_axis(self, other, rtol=None, atol=None,
                            verbose=False, ignore_type=False,
                            axis1_to_axis0=None, key1_to_key0=None):
        '''TODO
        '''
        # ------------------------------------------------------------
        # Domain axes
        # ------------------------------------------------------------  
        self_sizes  = [d.get_size()
                       for d in self.type('domain_axis').values()]
        other_sizes = [d.get_size()
                       for d in other.type('domain_axis').values()]
      
        if sorted(self_sizes) != sorted(other_sizes):
            # There is not a 1-1 correspondence between axis sizes
            if verbose:
                print("{0}: Different domain axes: {1} != {2}".format(
                    self.__class__.__name__,
                    sorted(self.values()),
                    sorted(other.values())))
            return False

        return True
    #--- End: def
    
#--- End: class
