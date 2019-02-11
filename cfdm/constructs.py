from __future__ import print_function
from builtins import (super, zip)
from past.builtins import basestring

from . import core


class Constructs(core.Constructs):
    '''<TODO>

.. versionadded:: 1.7.0

    ''' 
       
    def __call__(self, *names):
        '''TODO
        '''
        return self.filter_by_name(*names)
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

    def copy(self, data=True):
        '''
        '''
        out = super().copy(data=data)

        prefiltered = getattr(self, '_prefiltered', None)
        if prefiltered is not None:
            out._prefiltered = prefiltered.copy(data=data)
            
        return out
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
        domain_axes = self.filter_by_type('domain_axis')
        
        if key not in domain_axes:
            return default

        constructs_data_axes = self.data_axes()

        name = None        
        for dkey, dim in self.filter_by_type('dimension_coordinate').items():
            if constructs_data_axes[dkey] == (key,):
                # Get the name from a dimension coordinate
                name = dim.name(ncvar=False, default=None)
                break
        #--- End: for
        if name is not None:
            return name

        found = False
        for akey, aux in self.filter_by_type('auxiliary_coordinate').items():
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

    def filter_by_axis(self, *and_or, **axes):
        '''Select metadata constructs

.. versionadded:: 1.7.0

.. seealso:: `filter_by_key`, `filter_by_measure`, `filter_by_method`,
             `filter_by_name`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`, `inverse_filter`,
             `inverse_filter`

:Parameters:

    filter_by_axes:
        TODO Select constructs that have data which spans at least one of
        the given domain axes constructs. Domain axes constructs are
        specified with their construct keys.

        If an axis of `None` is provided then all constructs that have
        data are selected.

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

>>> d = c.axis('domainaxis1')

>>> d = c.axis('domainaxis0', 'domainaxis1')

Setting no keyword arguments selects no constructs:

>>> c.key()
<Constructs: >

        '''       
        out = self.shallow_copy()
        out._prefiltered = self.shallow_copy()

        _or = False
        if and_or:
            if len(and_or) > 1:
                raise ValueError("asdas")
            
            x = and_or[0]
            if x == 'or':
                _or = True
            elif x != 'and':
                raise ValueError("asdas 2")
        #--- End: if
            
        constructs_data_axes = self.data_axes()
        
        for cid in tuple(out):
            x = constructs_data_axes.get(cid)
            if x is None:
                # This construct does not have data
                out._pop(cid)
                continue

            ok = True
            for axis_key, value in axes.items():
                if value:
                    ok = axis_key in x
                else:
                    ok = axis_key not in x

                if _or:
                    if ok:
                        break
                elif not ok:
                    break
            #--- End: for

            if not ok:
                # This construct does not match any of the sets of
                # properties
                out._pop(cid)
        #--- End: for

   #    
   #    axes = set(axes)
   #
   #    constructs_data_axes = self.data_axes()
   #    for cid, construct in tuple(out.items()):
   #        x = constructs_data_axes.get(cid)
   #        if None in axes and x is not None:
   #            continue
   #        
   #        if x is None or not axes.intersection(x):
   #            # This construct does not span these axes
   #            out._pop(cid)
   #    #--- End: for
        
        return out
    #--- End: def

    def filter_by_key(self, *keys):
        '''Select metadata constructs by key.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_measure`, `filter_by_method`,
             `filter_by_name`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`, `inverse_filter`

:Parameters:

    keys:
        TODO

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

>>> d = c.key('domainancillary0')

>>> d = c.key('cellmethod2')

>>> d = c.key('dimensioncoordinate1', 'fieldancillary0')

Setting no keyword arguments selects no constructs:

>>> c.key()
<Constructs: >

        '''
        out = self.shallow_copy()
        out._prefiltered = self.shallow_copy()
        
        if None in keys:
            return out
        
        for cid in tuple(out):
            if cid not in keys:
                out._pop(cid)
        #--- End: for

        return out
    #--- End: def

    def filter_by_measure(self, *measures):
        '''Select cell measure constructs by measure.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_key`, `filter_by_method`,
             `filter_by_name`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`, `inverse_filter`

:Parameters:

    measures:
        Select cell measure constructs that have any of the given
        measure values.

        A measure is specified by a string (e.g. ``'area'``); or a
        compiled regular expression (e.g. ``re.compile('^a')``), for
        which all constructs whose measures match (via `re.search`)
        are selected.

        If no measures are provided then all cell measure constructs
        that have a measure property, with any value, are selected.

:Returns:

    `Constructs`
        The selected cell meausure constructs and their construct
        keys.
        
**Examples:**

>>> print(t.constructs.filter_by_type('measure'))
Constructs:
{'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>,
 'cellmeasure1': <CellMeasure: measure:volume(3, 9, 10) m3>}

Select cell measure constructs that have a measure of 'area':

>>> print(c.filter_by_measure('area'))
Constructs:
{'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>}

Select cell measure constructs that have a measure of 'area' or
'volume':

>>> print(c.filter_by_measure('area', 'volume'))
Constructs:
{'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>,
 'cellmeasure1': <CellMeasure: measure:volume(3, 9, 10) m3>}

Select cell measure constructs that have a measure of start with the
letter "a" or "v":

>>> print(c.filter_by_measure(re.compile('^a|v')))
Constructs:
{'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>,
 'cellmeasure1': <CellMeasure: measure:volume(3, 9, 10) m3>}

Select cell measure constructs that have a measure of any value:

>>> print(c.filer_by_measure())
Constructs:
{'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>,
 'cellmeasure1': <CellMeasure: measure:volume(3, 9, 10) m3>}

        '''
        out = self.shallow_copy()
        out._prefiltered = self.shallow_copy()
        
        for cid, construct in tuple(out.items()):
            try:
                get_measure = construct.get_measure
            except AttributeError:
                # This construct doesn't have a "get_measure" method
                out._pop(cid)
                continue

            if not measures:
                if not construct.has_measure():
                    out._pop(cid)
                    
                continue

            ok = False
            for value0 in measures:
                value1 = construct.get_measure(None)
                ok = self._matching_values(value0, construct, value1)
                if ok:
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the measures
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def filter_by_method(self, *methods):
        '''Select cell method constructs by method.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_key`, `filter_by_measure`,
             `filter_by_name`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`, `inverse_filter`

:Parameters:

    methods:
        Select cell method constructs that have any of the given
        methods.

        A method is specified by a string (e.g. ``'mean'``); or a
        compiled regular expression (e.g. ``re.compile('^m')``), for
        which all constructs whose methods match (via `re.search`) are
        selected.

        If no methods are provided then all cell method constructs
        that have a method, with any value, are selected.

:Returns:

    `Constructs`
        The selected cell method constructs and their construct keys.

**Examples:**

>>> print(c.constructs.filter_by_type('cell_method'))
Constructs:
{'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1': <CellMethod: domainaxis3: maximum>}

Select cell method constructs that have a method of 'mean':

>>> print(c.filter_by_method('mean'))
Constructs:
{'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>}

Select cell method constructs that have a method of 'mean' or
'maximum':

>>> print(c.filter_by_method('mean', 'maximum'))
Constructs:
{'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1': <CellMethod: domainaxis3: maximum>}

Select cell method constructs that have a method that contain the letter 'x':

>>> import re
>>> print(c.filter_by_method(re.compile('x')))
Constructs:
{'cellmethod1': <CellMethod: domainaxis3: maximum>}

Select cell method constructs that have a method of any value:

>>> print(c.filter_by_method())
Constructs:
{'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1': <CellMethod: domainaxis3: maximum>}

        '''
        out = self.shallow_copy()
        out._prefiltered = self.shallow_copy()
        
        for cid, construct in tuple(out.items()):
            try:
                get_method = construct.get_method
            except AttributeError:
                # This construct doesn't have a "get_method" method
                out._pop(cid)
                continue

            if not methods:
                if not construct.has_method():
                    out._pop(cid)
                    
                continue
            
            ok = False
            for value0 in methods:
                value1 = get_method(None)
                ok = self._matching_values(value0, construct, value1)
                if ok:
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the methods
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def filter_by_name(self, *names):
        '''Select metadata constructs by name.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_key`, `filter_by_measure`,
             `filter_by_method`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`, `inverse_filter`

:Parameters:

    names:

        Select constructs that have any of the given names.

        A name is specified by a string (e.g. ``'latitude'``,
        ``'long_name=time'``, etc.); or a compiled regular expression
        (e.g. ``re.compile('^atmosphere')``), for which all constructs
        whose names match (via `re.search`) are selected.

        If no names are provided then all constructs are selected.

        Each construct has a number of names, and is selected if any
        of them match any of those provided. A construct's names are
        those returned by its `!names` method. In the following
        example, the construct ``c`` has four names:

           >>> c.names()
           ['time', 'long_name=Time', 'foo=bar', 'ncvar%T']

        In addition, each construct also has a name based its
        construct key (e.g. ``'key%dimensioncoordinate2'``)

        Note that the identifiers of metadata constructs in the ouput
        of a `print` or `!dump` call are always one of its names, and
        so may always be used as a *names* argument.

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

TODO

        '''
        out = self.shallow_copy()
        out._prefiltered = self.shallow_copy()

        # Return all constructs if no names have been provided
        if not names:
            return out
        
        for cid, construct in tuple(out.items()):
            ok = False
            for value0 in names:          
                for value1 in construct.names(extra=('key%'+cid,)):
                    ok = self._matching_values(value0, construct, value1)
                    if ok:
                        break
                #--- End: for

                if ok:
                    break
            #--- End: for

            if not ok:
                # This construct does not match any of the names
                out._pop(cid)
        #--- End: for

        return out
    #--- End: def

    def filter_by_ncdim(self, *ncdims):
        '''Select domain axis constructs by netCDF dimension name.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_key`, `filter_by_measure`,
             `filter_by_method`, `filter_by_name`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`, `inverse_filter`

:Parameters:

    ncdims:
        Select domain axis constructs that have any of the given
        netCDF dimension names.

        A netCDF dimension name is specified by a string
        (e.g. ``'time'``); or a compiled regular expression
        (e.g. ``re.compile('^lat')``), for which all constructs whose
        netCDF dimension names match (via `re.search`) are selected.

        If no netCDF dimension names are provided then all domain axis
        constructs that have a netCDF dimension name, with any value,
        are selected.

:Returns:

    `Constructs`
        The selected domain axis constructs and their construct keys.

**Examples:**

TODO

        '''
        out = self.shallow_copy()
        out._prefiltered = self.shallow_copy()
        
        for cid, construct in tuple(out.items()):
            try:
                nc_get_dimension = construct.nc_get_dimension
            except AttributeError:
                # This construct doesn't have a "nc_get_dimension"
                # method
                out._pop(cid)
                continue
            
            if not ncdims:
                if not construct.nc_has_dimension():
                    out._pop(cid)
                    
                continue
            
            ok = False
            for value0 in ncdims:
                value1 = nc_get_dimension(None)
                ok = self._matching_values(value0, construct, value1)
                if ok:
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the netCDF
                # dimension names
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def filter_by_ncvar(self, *ncvars):
        '''Select domain axis constructs by netCDF variable name.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_key`, `filter_by_measure`,
             `filter_by_method`, `filter_by_name`, `filter_by_ncdim`,
             `filter_by_property`, `filter_by_type`, `inverse_filter`

:Parameters:

    ncvars:
        Select constructs that have any of the given netCDF variable
        names.

        A netCDF variable name is specified by a string
        (e.g. ``'time'``); or a compiled regular expression
        (e.g. ``re.compile('^lat')``), for which all constructs whose
        netCDF variable names match (via `re.search`) are selected.

        If no netCDF variable names are provided then all domain axis
        constructs that have a netCDF variable name, with any value,
        are selected.

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

Select constructs that have a netCDF variable name of  of 'x':

>>> print(c.filter_by_ncvar('x'))
Constructs:
{'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>}

Select cell method constructs that have a a netCDF variable name of
'x' or 'y':

>>> print(c.filter_by_ncvar('x', 'y'))
Constructs:
{'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>}

Select constructs that have a netCDF variable name that starts with
the letter 't':

>>> import re
>>> print(c.filter_by_ncvar(re.compile('^t')))
Constructs:
{'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

Select constructs that have a netCDF variable name of any value:

>>> print(c.filter_by_ncvar())
print t.constructs.filter_by_ncvar()
Constructs:
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
 'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
 'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >,
 'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
 'domainancillary1': <DomainAncillary: ncvar%b(1) >,
 'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>}

        '''
        out = self.shallow_copy()
        out._prefiltered = self.shallow_copy()
        
        for cid, construct in tuple(out.items()):            
            try:
                nc_get_variable = construct.nc_get_variable
            except AttributeError:
                # This construct doesn't have a "nc_get_variable"
                # method
                out._pop(cid)
                continue

            if not ncvars:
                if not construct.nc_has_variable():
                    out._pop(cid)
                    
                continue

            ok = False
            for value0 in ncvars:
                value1 = nc_get_variable(None)
                ok = self._matching_values(value0, construct, value1)
                if ok:
                    break
            #--- End: for

            if not ok:
                # This construct does not match any of the netCDF
                # variable names
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def _matching_values(self, value0, construct, value1):
        if value1 is not None:                        
            try:
                result = value0.search(value1)
            except (AttributeError, TypeError):
                result = construct._equals(value1, value0)
                
            if result:
                # This construct matches this property
                return True

        return False
    
    def filter_by_property(self, *and_or, **properties):
        '''Select metadata constructs by property.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_key`, `filter_by_measure`, `filter_by_method`,
             `filter_by_name`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_type`, `inverse_filter`

:Parameters:
        
    and_or:
        Define the behaviour when multiple properties are provided.

        By default (or if the *and_or* parameters is ``'and'``) a
        construct is selected if it matches all of the given
        properties, but if the *and_or* parameter is ``'or'`` then a
        construct will be selected when at least one of its properties
        matches.

    properties: 
        Select constructs that have properties with the given
        values.

        By default a construct is selected if it matches all of the
        given properties, but it may alternatively be selected when at
        least one of its properties matches (see the *and_or*
        positional parameter).

        A property value is specified by any value
        (e.g. ``'latitude'``, ``4``, ``['foo', 'bar']``); or a
        compiled regular expression (e.g. ``re.compile('^ocean')``),
        for which all constructs whose methods match (via `re.search`)
        are selected.

        If no properties are provided then all constructs that have
        properties, with any values, are selected.

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**



TODO


        '''
        out = self.shallow_copy()
        out._prefiltered = self.shallow_copy()

        _or = False
        if and_or:
            if len(and_or) > 1:
                raise ValueError("asdas444444444")
            
            x = and_or[0]
            if x == 'or':
                _or = True
            elif x != 'and':
                raise ValueError("asdas66666666666666666666 2")
        #--- End: if

        for cid, construct in tuple(out.items()):
            try:
                get_property = construct.get_property
            except AttributeError:
                # This construct doesn't have a "get_property" method
                out._pop(cid)
                continue

            if not properties:
                if not construct.properties():
                    out._pop(cid)
                    
                continue

            ok = True
            for name, value0 in properties.items():
                value1 = get_property(name, None)
                ok = self._matching_values(value0, construct, value1)

                if _or:
                    if ok:
                        break
                elif not ok:
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the sets of
                # properties
                out._pop(cid)
        #--- End: for

        return out
    #--- End: def

    def filter_by_type(self, *types):
        '''Select cell measure constructs by measure.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_key`, `filter_by_measure`,
             `filter_by_method`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_name`, `filter_by_property`, `inverse_filter`

:Parameters:

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**
TODO

        '''
        out = super().filter_by_type(*types)
        out._prefiltered = self.shallow_copy()
        return out        
    #--- End: def
    
    def inverse_filter(self):
        '''Return the inverse of the previous filtering.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_key`, `filter_by_measure`,
             `filter_by_method`, `filter_by_name`, `filter_by_ncdim`,
             `filter_by_ncvar`, `filter_by_property`, `filter_by_type`

:Returns:

    `Constructs`
        TODO

**Examples:**

TODO

        '''
        prefiltered = getattr(self, '_prefiltered', self)

        out = prefiltered.shallow_copy()

        out._prefiltered = prefiltered

        for key in self:
            out._pop(key)
        
        return out
    #--- End: def
    
    def shallow_copy(self, _ignore=None):
        '''
        '''
        out = super().shallow_copy(_ignore=_ignore)

        prefiltered = getattr(self, '_prefiltered', None)
        if prefiltered is not None:
            out._prefiltered = prefiltered.shallow_copy()
            
        return out
    #--- End: def

    def _equals_coordinate_reference(self, other, rtol=None,
                                     atol=None, verbose=False,
                                     ignore_type=False,
                                     axis1_to_axis0=None,
                                     key1_to_key0=None):
        '''
        '''
        refs0 = dict(self.filter_by_type('coordinate_reference'))
        refs1 = dict(other.filter_by_type('coordinate_reference'))

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
        cell_methods0 = self.filter_by_type('cell_method')
        cell_methods1 = other.filter_by_type('cell_method')

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
                       for d in self.filter_by_type('domain_axis').values()]
        other_sizes = [d.get_size()
                       for d in other.filter_by_type('domain_axis').values()]
      
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
