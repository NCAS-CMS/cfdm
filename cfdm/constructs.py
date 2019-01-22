from __future__ import print_function
from builtins import (super, zip)
from past.builtins import basestring

from . import core


class Constructs(core.Constructs):
    '''TODO

.. versionadded:: 1.7.0

    '''    
    def constructs(self, name=None, properties=None, measure=None,
                   ncvar=None, ncdim=None, key=None, axis=None,
                   construct_type=None, copy=False):
        '''Return metadata constructs

By default all metadata constructs are returned, but a subset may be
selected via the optional parameters. If multiple parameters are
specified, then the constructs that satisfy *all* of the criteria are
returned. 

.. versionadded:: 1.7.0

.. seealso:: `del_construct`, `get_construct`,
             `get_construct_data_axes`, `get_construct_id`,
             `has_construct`, `set_construct`

:Parameters:

    name: (sequence of) `str`, optional
        Select constructs that have the given name. If a sequence of
        names has been given then the constructs that have any of the
        names are selected.
       
        In general, a construct is selected if any of the given names
        is the same as one of the possible constuct names, as returned
        by the construct's `!name` method with the ``all_names``
        parameter set to True. For example, the following construct,
        ``c``, has three default names:

           >>> c.name(all_names=True)
           ['longitude', 'long_name:Longitude', 'ncvar%lon']

        Note that the names used to identify metadata constructs in
        the ouput of a `print` or `!dump` call may always be used to
        select constructs.

        A name may be one of:

        * The value of the standard name property.

          *Parameter example:*
            ``name='air_pressure'`` will select constructs that have a
            "standard_name" property with the value "air_pressure".

        * The value of any property prefixed by the property name and
          a colon (``:``).

          *Parameter example:*
            ``name='long_name:Air Temperature'`` will select
            constructs that have a "long_name" property with the value
            "Air Temperature".

          *Parameter example:*
            ``name='positive:up'`` will select constructs that have a
            "positive" property with the value "up".

          *Parameter example:*
            ``name='foo:bar'`` will select constructs that have a
            "foo" property with the value "bar".

          *Parameter example:*
            ``name='standard_name:air_pressure'`` will select
            constructs that have a "standard_name" property with the
            value "air_pressure". Note this selection could also be
            made with ``name='air_pressure'``.

        * The measure of cell measure constructs, prefixed by
          ``measure%``. Constructs may also be selected by their
          meaure with the *measure* parameter.

          *Parameter example:*
            ``name='measure%area'`` will select "area" cell measure
            constructs. Note this selection could also be made with
            ``measure='area'``.


        * A construct identifier, prefixed by ``key%`` (see also the
          *key* parameter). Constructs may also be selected by their
          *construct identifier with the *key* parameter.


          *Parameter example:* 
            ``name='key%cellmethod1'`` will select cell method
            construct with construct identifier "cellmethod1".

        * The netCDF variable name, prefixed by ``ncvar%``.
          Constructs may also be selected by their netCDF variable
          name with the *ncvar* parameter.

          *Parameter example:*
            ``name='ncvar%lat'`` will select constructs with netCDF
            variable name "lat".

        * The netCDF dimension name of domain axis constructs,
          prefixed by ``ncdim%``. Constructs may also be selected by
          their netCDF dimension name with the *ncdim* parameter.

          *Parameter example:*
            ``name='ncdim%time'`` will select domain axis constructs
            with netCDF dimension name "time".

    construct_type: (sequence of) `str`, optional
        Select constructs of the given type. If a sequence of types
        has been given then the constructs of each type are
        selected. Valid types are:

          ==========================  ================================
          *construct_type*            Selected constructs
          ==========================  ================================
          ``'domain_ancillary'``      Domain ancillary constructs
          ``'dimension_coordinate'``  Dimension coordinate constructs
          ``'domain_axis'``           Domain axis constructs
          ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
          ``'cell_measure'``          Cell measure constructs
          ``'coordinate_reference'``  Coordinate reference constructs
          ``'cell_method'``           Cell method constructs
          ``'field_ancillary'``       Field ancillary constructs
          ==========================  ================================

        *Parameter example:*
          ``construct_type='dimension_coordinate'``

        *Parameter example:*
          ``construct_type=['auxiliary_coordinate']``

        *Parameter example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    measure: (sequence of) `str`, optional
        Select cell measure constructs which have the given
        measure. If multiple measures are specified then select the
        cell measure constructs which have any of the given measures.

        *Parameter example:*
          ``meausure='area'``

        *Parameter example:*
          ``measure=['area']``

        *Parameter example:*
          ``measure=['area', 'volume']``

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

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.
        
        If cell method contructs, and no other construct types, have
        been selected with the *construct_type* parameter then the
        constructs are returned in an ordered dictionary
        (`collections.OrderedDict`). The order is determined by the
        order in which the cell method constructs were originally
        added.

**Examples:**

>>> f.constructs()
{}

>>> f.constructs()
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
 'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >,
 'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>,
 'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1': <CellMethod: domainaxis3: maximum>,
 'coordinatereference0': <CoordinateReference: atmosphere_hybrid_height_coordinate>,
 'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>,
 'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
 'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >,
 'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
 'domainancillary1': <DomainAncillary: ncvar%b(1) >,
 'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>,
 'domainaxis0': <DomainAxis: 1>,
 'domainaxis1': <DomainAxis: 10>,
 'domainaxis2': <DomainAxis: 9>,
 'domainaxis3': <DomainAxis: 1>,
 'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}
>>> f.constructs('grid_latitude')
{'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>}
>>> f.constructs('long_name:Grid latitude name')
{'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >}
>>> f.constructs('ncvar%b')
{'domainancillary1': <DomainAncillary: ncvar%b(1) >}
>>> f.constructs(construct_type='coordinate_reference')
{'coordinatereference0': <CoordinateReference: atmosphere_hybrid_height_coordinate>,
 'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>}
>>> f.constructs(construct_type='cell_method')
OrderedDict([('cellmethod0', <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>),
             ('cellmethod1', <CellMethod: domainaxis3: maximum>)])
>>> f.constructs(construct_type=['cell_method', 'field_ancillary'])
{'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1': <CellMethod: domainaxis3: maximum>,
 'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}
>>> f.constructs(axes=['domainaxis0'])
{'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
 'domainancillary1': <DomainAncillary: ncvar%b(1) >}
>>> f.constructs(axes=['domainaxis0', 'domainaxis1'])
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
 'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >,
 'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>,
 'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
 'domainancillary1': <DomainAncillary: ncvar%b(1) >,
 'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>,
 'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}
>>> f.constructs('longitude',
...              construct_type='auxiliary_coordinate', 
...              axes=['domainaxis1'])
{'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>}
>>> f.constructs('air_pressure')
{}

        '''
        out = super().constructs(construct_type=construct_type, copy=copy)

        if key is not None:
            if isinstance(key, basestring):
                key = (key,)

            out = {cid: out[cid] for cid in key if cid in out}
            if not out:
                return out
        #--- End: if

        if axis is not None:
            if isinstance(axis, basestring):
                axis = (axis,)

            axis = set(axis)
            
            constructs_data_axes = self.constructs_data_axes()
            for cid in tuple(out):
                x = constructs_data_axes.get(cid)
                if x is None or not axis.intersection(x):
                    # This construct does not span these axes
                    del out[cid]
            #--- End: for
                        
            if not out:
                return out
        #--- End: if

        if name is not None:
            if isinstance(name, basestring):
                name = (name,)

            for cid, construct in tuple(out.items()):
                ok = False                
                for n in name:
                    (prefix, _, value) = n.partition('%')
                    if prefix == 'key':
                        if value == cid:
                            # This construct matches this name
                            ok = True
                            break
                    else:
                        (prefix, _, value) = n.partition(':')
                        custom = (prefix,) if value else None
                        if n in construct.name(custom=custom,
                                               all_names=True):
                            # This construct matches this name
                            ok = True
                            break
                #--- End: for
                
                if not ok:
                    # This construct does not match any of the names
                    del out[cid]
            #--- End: for

            if not out:
                return out
        #--- End: if

        if properties is not None:
            if isinstance(properties, dict):
                properties = (properties,)

            for cid, construct in tuple(out.items()):
                try:
                    get_property = construct.get_property
                except AttributeError:
                    del out[cid]
                    continue
                
                ok = False
                for props in properties:
                    ok = False
                    for p, value0 in props.items():
                        value1 = get_property(p, None)
                        if value1 is None or not construct._equals(value1, value0):
                            # This construct does not match this set
                            # of properties
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
                    del out[cid]
            #--- End: for
            
            if not out:
                return out
        #--- End: if

        if measure is not None:
            if isinstance(measure , basestring):
                measure = (measure,)

            for cid, construct in tuple(out.items()):
                try:
                    get_measure = construct.get_measure
                except AttributeError:
                    del out[cid]
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
                    # This construct does not match any of the
                    # measures
                    del out[cid]
            #--- End: for
            
            if not out:
                return out
        #--- End: if
        
        if ncvar is not None:
            if isinstance(ncvar , basestring):
                ncvar = (ncvar,)

            for cid, construct in tuple(out.items()):
                try:
                    nc_get_variable = construct.nc_get_variable
                except AttributeError:
                    del out[cid]
                    continue

                ok = False
                for x0 in ncvar:
                    x1 = nc_get_variable(None)
                    if x1 is not None and construct._equals(x1, x0):
                        # This construct matches this netCDF variable
                        # name
                        ok = True
                        break
                #--- End: for
                
                if not ok:
                    # This construct does not match any of the netCDF
                    # variable names
                    del out[cid]
            #--- End: for
            
            if not out:
                return out
        #--- End: if
                
        if ncdim is not None:
            if isinstance(ncdim , basestring):
                ncdim = (ncdim,)
                
            for cid, construct in tuple(out.items()):
                try:
                    nc_get_dimension = construct.nc_get_dimension
                except AttributeError:
                    del out[cid]
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
                    del out[cid]
            #--- End: for
            
            if not out:
                return out
        #--- End: if
        
        return out
    #--- End: def

    def domain_axis_name(self, axis):
        '''Return the canonical name for an axis.

:Parameters:

    axis: `str`
        The identifier of the axis.

        *Parameter example:*
          ``axis='domainaxis2'``

:Returns:

    `str`
        The canonical name for the axis.

**Examples:**

>>> f.domain_axis_name('domainaxis1')
'longitude'


        '''
        domain_axes = self.constructs(construct_type='domain_axis')
        
        if axis not in domain_axes:
            return default

        constructs_data_axes = self.constructs_data_axes()

        dimension_coordinates = self.constructs(construct_type='dimension_coordinate')

        name = None        
        for key, dim in dimension_coordinates.items():
            if constructs_data_axes[key] == (axis,):
                # Get the name from a dimension coordinate
                name = dim.name(ncvar=False, default=None)
                break
        #--- End: for
        if name is not None:
            return name

        auxiliary_coordinates = self.constructs(construct_type='auxiliary_coordinate')
        
        found = False
        for key, aux in auxiliary_coordinates.items():
            if constructs_data_axes[key] == (axis,):
                if found:
                    name = None
                    break
                
                # Get the name from an auxiliary coordinate
                name = aux.name(ncvar=False, default=None)
                found = True
        #--- End: for
        if name is not None:
            return name

        ncdim = domain_axes[axis].nc_get_dimension(None)
        if ncdim is not None:
            # Get the name from a netCDF dimension
            return 'ncdim%{0}'.format(ncdim)

        # Get the name from the identifier
        return 'key%{0}'.format(axis)
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
    
    def _equals_coordinate_reference(self, other, rtol=None, atol=None,
                                     verbose=False,
                                     ignore_type=False,
                                     axis1_to_axis0=None,
                                     key1_to_key0=None):
        '''
        '''
        refs0 = self.constructs(construct_type='coordinate_reference')
        refs1 = other.constructs(construct_type='coordinate_reference')

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
#                    terms1 = {}
#                    for term, key in tuple(ref1.coordinate_conversion.domain_ancillaries().items()):
#                        terms1[term] = key1_to_key0.get(key, key)

                    terms1 = {term: key1_to_key0.get(key, key)
                              for term, key in ref1.coordinate_conversion.domain_ancillaries().items()}
#                    print(terms1)

                    if terms0 != terms1:
                        continue
    
#                    # Domain ancillary-valued datum terms
#                    terms0 = ref0.datum.domain_ancillaries()
#                    terms1 = {}
#                    for term, key in ref1.datum.domain_ancillaries().items():
#                        terms1[term] = key1_to_key0.get(key, key)
#    
#                    if terms0 != terms1:
#                        continue
    
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
        cell_methods0 = self.constructs(construct_type='cell_method')
        cell_methods1 = other.constructs(construct_type='cell_method')

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
                       for d in self.constructs(construct_type='domain_axis').values()]
        other_sizes = [d.get_size()
                       for d in other.constructs(construct_type='domain_axis').values()]
        
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
