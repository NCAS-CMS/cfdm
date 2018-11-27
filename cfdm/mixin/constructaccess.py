from builtins import object

import re


class ConstructAccess(object):
    '''Mixin class for manipulating constructs stored in a `Constructs`
object.

    '''

    def _unique_construct_names(self):
        '''TODO 

        '''    
        key_to_name = {}
        name_to_keys = {}


        for d in self._get_constructs()._constructs.values():
            name_to_keys = {}
        
            for key, construct in d.items():
                name = construct.name(default='cid%'+key)
                name_to_keys.setdefault(name, []).append(key)
                key_to_name[key] = name
    
            for name, keys in name_to_keys.items():
                if len(keys) <= 1:
                    continue
                
                for key in keys:
                    key_to_name[key] = '{0}{{{1}}}'.format(
                        name,
                        re.findall('\d+$', key)[0])
        #--- End: for
        
        return key_to_name
    #--- End: def
    
    def _unique_domain_axis_names(self):
        '''TODO 
        '''
        key_to_name = {}
        name_to_keys = {}

        for key, value in self.domain_axes().items():
            name_size = (self.domain_axis_name(key), value.get_size(''))
            name_to_keys.setdefault(name_size, []).append(key)
            key_to_name[key] = name_size

        for (name, size), keys in name_to_keys.items():
            if len(keys) == 1:
                key_to_name[keys[0]] = '{0}({1})'.format(name, size)
            else:
                for key in keys:                    
                    key_to_name[key] = '{0}{{{1}}}({2})'.format(name,
                                                                re.findall('\d+$', key)[0],
                                                                size)
        #--- End: for
        
        return key_to_name
    #--- End: def
    
    def coordinate_references(self, copy=False):
        '''Return coordinate reference constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    out: `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.


**Examples:**

>>> f.coordinate_references()
{}

>>> f.coordinate_references()
{'coordinatereference0': <CoordinateReference: atmosphere_hybrid_height_coordinate>,
 'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>}

        '''
        return self._get_constructs().constructs(
            construct_type='coordinate_reference', copy=copy)
    #--- End: def

    def coordinates(self, copy=False):
        '''Return dimension and auxiliary coordinate constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    out: `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.coordinates()
{}

>>> f.coordinates()
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
 'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >,
 'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
 'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

        '''
        out = self.dimension_coordinates(copy=copy)
        out.update(self.auxiliary_coordinates(copy=copy))
        return out
    #--- End: def

    def domain_ancillaries(self, copy=False):
        '''Return domain ancillary constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    out: `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.domain_ancillaries()
{}

>>> f.domain_ancillaries()
{'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
 'domainancillary1': <DomainAncillary: ncvar%b(1) >,
 'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>}

        '''
        return self._get_constructs().constructs(
            construct_type='domain_ancillary', copy=copy)
    #--- End: def
    
    def cell_measures(self, copy=False):
        '''Return cell measure constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    out: `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.cell_measures()
{}

>>> f.cell_measures()
{'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>}

        '''
        return self._get_constructs().constructs(
            construct_type='cell_measure', copy=copy)
    #--- End: def

    def del_construct(self, description=None, cid=None, axes=None,
                      construct_type=None):
        '''Remove a metadata construct.

The construct is identified via optional parameters. The *unique*
construct that satisfies *all* of the given criteria is removed. An
error is raised if multiple constructs satisfy all of the given
criteria.

.. versionadded:: 1.7

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
              ``description='cid%cellmethod1'`` will select cell
              method construct with construct identifier
              "cellmethod1". This is equivalent to
              ``cid='cellmethod1'``.

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
          ``'cell_method'``           Cell method constructs
          ``'field_ancillary'``       Field ancillary constructs
          ==========================  ================================

        *Example:*
          ``construct_type='dimension_coordinate'``

        *Example:*
          ``construct_type=['auxiliary_coordinate']``

        *Example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    axes: sequence of `str`, optional
        Select constructs which have data that spans any one or more
        of the given domain axes, in any order. Domain axes are
        specified by their construct identifiers.

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
        c = self.constructs(description=description, cid=cid,
                            construct_type=construct_type, axes=axes,
                            copy=False)
        if len(c) == 1:
            cid, _ = c.popitem()
            return self._get_constructs().del_construct(cid=cid)

        self.get_construct(description=description, cid=cid,
                           construct_type=construct_type, axes=axes,
                           copy=False)
    #--- End: def

    def get_construct(self, description=None, cid=None, axes=None,
                      construct_type=None, copy=False):
        '''Return a metadata construct.

The construct is selected via optional parameters. The *unique*
construct that satisfies *all* of the given criteria is returned. An
error is raised if multiple constructs satisfy all of the given
criteria.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `has_construct`,
             `set_construct`

:Parameters:

    description: `str`, optional
        Select the construct that have the given property, or other
        attribute, value.

        The description may be one of:

        * The value of the standard name property on its own. 

          *Example:*
            ``description='air_pressure'`` will select constructs that
            have a "standard_name" property with the value
            "air_pressure".

        * The value of any property prefixed by the property name and
          a colon (``:``).

          *Example:*
            ``description='positive:up'`` will select constructs that
            have a "positive" property with the value "up".

          *Example:*
            ``description='foo:bar'`` will select constructs that have
            a "foo" property with the value "bar".

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
            ``description='cid%cellmethod1'`` will select cell method
            construct with construct identifier "cellmethod1". This is
            equivalent to ``cid='cellmethod1'``.

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
          construct with construct identifier "domainancillary0". This
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
          ``'cell_method'``           Cell method constructs
          ``'field_ancillary'``       Field ancillary constructs
          ==========================  ================================

        *Example:*
          ``construct_type='dimension_coordinate'``


        *Example:*
          ``construct_type=['auxiliary_coordinate']``

        *Example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    axes: sequence of `str`, optional
        Select constructs which have data that spans any one or more
        of the given domain axes, in any order. Domain axes are
        specified by their construct identifiers.

        *Example:*
          ``axes=['domainaxis2']``

        *Example:*
          ``axes=['domainaxis0', 'domainaxis1']``

    copy: `bool`, optional
        If True then return a copy of the unique selected
        construct. By default the construct is not copied.

:Returns:

    out: `dict`

        True if a unique construct has been identified, otherwise
        False.

**Examples:**

>>> c = f.get_construct('grid_latitude')
>>> c = f.get_construct('long_name:Air Pressure')
>>> c = f.get_construct('ncvar%lat)
>>> c = f.get_construct('cid%cellmeasure0')
>>> c = f.get_construct(cid='domainaxis2')
>>> c = f.get_construct(construct_type='auxiliary_coordinate',
...                     axes=['domainaxis1'])

        '''
        return self._get_constructs().get_construct(
            description=description, cid=cid,
            construct_type=construct_type,
            axes=axes,
            copy=copy)
    #--- End: def

    def has_construct(self, description=None, cid=None, axes=None,
                      construct_type=None):
        '''Whether a metadata construct has been set.

The construct is identified via optional parameters. If, and only if,
there is a *unique* construct that satisfies *all* of the given
criteria, then `True` is returned.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
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
              ``description='cid%cellmethod1'`` will select cell
              method construct with construct identifier
              "cellmethod1". This is equivalent to
              ``cid='cellmethod1'``.

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
          ``'cell_method'``           Cell method constructs
          ``'field_ancillary'``       Field ancillary constructs
          ==========================  ================================

        *Example:*
          ``construct_type='dimension_coordinate'``

        *Example:*
          ``construct_type=['auxiliary_coordinate']``

        *Example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    axes: sequence of `str`, optional
        Select constructs which have data that spans any one or more
        of the given domain axes, in any order. Domain axes are
        specified by their construct identifiers.

        *Example:*
          ``axes=['domainaxis2']``

        *Example:*
          ``axes=['domainaxis0', 'domainaxis1']``

:Returns:

    out: `bool`
        True if a unique construct has been identified, otherwise
        False.

**Examples:**

>>> x = f.has_construct('grid_latitude')
>>> x = f.has_construct('long_name:Air Pressure')
>>> x = f.has_construct('ncvar%lat)
>>> x = f.has_construct('cid%cellmeasure0')
>>> x = f.has_construct(cid='domainaxis2')
>>> x = f.has_construct(construct_type='auxiliary_coordinate',
...                     axes=['domainaxis1'])

        '''
        out = self.constructs(description=description, cid=cid,
                              construct_type=construct_type,
                              axes=axes, copy=False)
        return len(out) == 1
    #--- End: def

    def constructs(self, description=None, cid=None, axes=None,
                   construct_type=None, copy=False):
        '''Return metadata constructs

By default all metadata constructs are returned, but a subset may be
selected via the optional parameters. If multiple parameters are
specified, then the constructs that satisfy *all* of the criteria are
returned.

.. versionadded:: 1.7

.. seealso:: `del_construct`, `get_construct`, `has_construct`,
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
              ``description='cid%cellmethod1'`` will select cell
              method construct with construct identifier
              "cellmethod1". This is equivalent to
              ``cid='cellmethod1'``.

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

    construct_type: (sequence of) `str`, optional
        Select constructs of the given type, or types. Valid types
        are:

          ==========================  ================================
          *construct_type*            Constructs
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

        *Example:*
          ``construct_type='dimension_coordinate'``

        *Example:*
          ``construct_type=['auxiliary_coordinate']``

        *Example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    axes: sequence of `str`, optional
        Select constructs which have data that spans any one or more
        of the given domain axes, in any order. Domain axes are
        specified by their construct identifiers.

        *Example:*
          ``axes=['domainaxis2']``

        *Example:*
          ``axes=['domainaxis0', 'domainaxis1']``

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    out: `dict`
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
        return self._get_constructs().constructs(
            description=description, cid=cid,
            construct_type=construct_type, axes=axes, copy=copy)
    #--- End: def

    def domain_axes(self, copy=False):
        '''Return domain axis constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    out: `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**


>>> f.domain_axes()
{}

>>> f.domain_axes()
{'domainaxis0': <DomainAxis: 1>,
 'domainaxis1': <DomainAxis: 10>,
 'domainaxis2': <DomainAxis: 9>,
 'domainaxis3': <DomainAxis: 1>}

        '''
        return self._get_constructs().constructs(
            construct_type='domain_axis', copy=copy)
    #--- End: def
        
    def auxiliary_coordinates(self, copy=False):
        '''Return auxiliary coordinate constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    out: `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.auxiliary_coordinates()
{}

>>> f.auxiliary_coordinates()
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
 'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >}

        '''
        return self._get_constructs().constructs(
            construct_type='auxiliary_coordinate', copy=copy)
    #--- End: def
 
    def dimension_coordinates(self, copy=False):
        '''Return dimension coordinate constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    out: `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.dimension_coordinates()
{}

>>> f.dimension_coordinates()
{'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
 'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

        '''
        return self._get_constructs().constructs(
            construct_type='dimension_coordinate', copy=copy)
    #--- End: def
    
    def domain_axis_name(self, axis):
        '''TODO 
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: def
    
#    def set_cell_measure(self, item, axes=None, cid=None, copy=True):
#        '''Set a cell measure construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `CellMeasure`
#        TODO
#
#    axes: sequence of `str`, optional
#        The identifiers of the domain axes spanned by the data array.
#
#        The axes may also be set afterwards with the
#        `set_construct_axes` method.
#
#        *Example:*
#          ``axes=['domainaxis1']``
#        
#    cid: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``cid='cellmeasure0'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples:**
#
#TODO
#        '''
#        return self.set_construct(item, cid=cid,
#                                  axes=axes, copy=copy)
##        return self.set_construct('cell_measure', item, cid=cid,
##                                  axes=axes, copy=copy)
#    #--- End: def
#
#    def set_coordinate_reference(self, item, cid=None, copy=True):
#        '''Set a coordinate reference construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `CoordinateReference`
#        TODO
#
#    cid: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``cid='coordinatereference0'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples:**
#
#TODO
#
#        '''
#        return self.set_construct(item, cid=cid, copy=copy)
##        return self.set_construct('coordinate_reference',
##                                  item, cid=cid, copy=copy)
#    #--- End: def
#
#    def set_dimension_coordinate(self, item, axes=None, cid=None,
#                                 copy=True):
#        '''Set a dimension coordinate construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `DimensionCoordinate`
#        TODO
#
#    axes: sequence of `str`, optional
#        The identifiers of the domain axes spanned by the data array.
#
#        The axes may also be set afterwards with the
#        `set_construct_axes` method.
#
#        *Example:*
#          ``axes=['domainaxis1']``
#        
#    cid: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``cid='dimensioncoordinate1'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples:**
#
#TODO
#
#        '''
#        return self.set_construct(item, cid=cid,
#                                  axes=axes, copy=copy)
#    #--- End: def
#    
#    def set_auxiliary_coordinate(self, item, axes=None, cid=None,
#                                 copy=True):
#        '''Set an auxiliary coordinate construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `AuxiliaryCoordinate`
#        TODO
#
#    axes: sequence of `str`, optional
#        The identifiers of the domain axes spanned by the data array.
#
#        The axes may also be set afterwards with the
#        `set_construct_axes` method.
#
#        *Example:*
#          ``axes=['domainaxis1']``
#        
#    cid: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``cid='auxiliarycoordinate0'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples:**
#
#TODO
#
#    '''
#        return self.set_construct(item,
#                                  cid=cid, axes=axes, copy=copy)
#    #--- End: def
#
#    def set_domain_axis(self, domain_axis, cid=None, copy=True):
#        '''Set a domain axis construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`
#
#:Parameters:
#
#    item: `DomainAxis`
#        TODO
#        
#    cid: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``cid='domainaxis2'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples:**
#
#TODO
#
#        '''
#        return self.set_construct(domain_axis, cid=cid,
#                                  copy=copy)
#    #--- End: def
#
#    def set_domain_ancillary(self, item, axes=None, cid=None, copy=True):
##                             extra_axes=0, copy=True):
#        '''Set a domain ancillary construct.
#
#.. versionadded:: 1.7
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct_axes`
#
#:Parameters:
#
#    item: `DomainAncillary`
#        TODO
#
#    axes: sequence of `str`, optional
#        The identifiers of the domain axes spanned by the data array.
#
#        The axes may also be set afterwards with the
#        `set_construct_axes` method.
#
#        *Example:*
#          ``axes=['domainaxis1', 'domainaxis0']``
#        
#    cid: `str`, optional
#        The identifier of the construct. If not set then a new, unique
#        identifier is created. If the identifier already exisits then
#        the exisiting construct will be replaced.
#
#        *Example:*
#          ``cid='domainancillary0'``
#        
#    copy: `bool`, optional
#        If False then do not copy the construct prior to insertion. By
#        default it is copied.
#        
#:Returns:
#
#     out: `str`
#        The identifier of the construct.
#    
#**Examples:**
#
#TODO
#
#        ''' 
#        return self.set_construct(item, cid=cid,
#                                  axes=axes, #extra_axes=extra_axes,
#                                  copy=copy)
#    #--- End: def

#--- End: class
