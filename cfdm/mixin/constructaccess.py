from builtins import object

import re


class ConstructAccess(object):
    '''Mixin class for manipulating constructs stored in a `Constructs`
object.

.. versionadded:: 1.7.0

    '''

    def _unique_construct_names(self):
        '''TODO 

        '''    
        key_to_name = {}
        name_to_keys = {}


        for d in self.constructs._constructs.values():
            name_to_keys = {}
        
            for key, construct in d.items():
                name = construct.name(default='key%'+key)
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

        for key, value in self.domain_axes.items():
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

    @property
    def coordinate_references(self, copy=False):
        '''Return coordinate reference constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.


**Examples:**

>>> f.coordinate_references
Constructs:
{}

>>> f.coordinate_references
Constructs:
{'coordinatereference0': <CoordinateReference: atmosphere_hybrid_height_coordinate>,
 'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>}

        '''
        return self.constructs.type('coordinate_reference')
    #--- End: def

    @property
    def coordinates(self, copy=False):
        '''Return dimension and auxiliary coordinate constructs.

.. versionadded:: 1.7.0

.. seealso:: `auxiliary_coordinates`, `constructs`,
             `dimension_coordinates`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.coordinates
Constructs:
{}

>>> f.coordinates
Constructs:
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
 'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name=Grid latitude name(10) >,
 'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
 'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

        '''
        out = self.dimension_coordinates
        out._update(self.auxiliary_coordinates)        
        return out
    #--- End: def

    @property
    def domain_ancillaries(self, copy=False):
        '''Return domain ancillary constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.domain_ancillaries
Constructs:
{}

>>> f.domain_ancillaries
Constructs:
{'domainancillary0': <DomainAncillary: ncvar:a(1) m>,
 'domainancillary1': <DomainAncillary: ncvar:b(1) >,
 'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>}

        '''
        return self.constructs.type('domain_ancillary')
    #--- End: def

    @property
    def cell_measures(self):
        '''Return cell measure constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.cell_measures
Constructs:
{}

>>> f.cell_measures
Constructs:
{'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>}

        '''
        return self.constructs.type('cell_measure')
    #--- End: def

    # parameter: name
    # parameter: properties
    # parameter: measure
    # parameter: ncvar
    # parameter: ncdim
    # parameter: key
    # parameter: axis
    # parameter: construct
    # parameter: default
    def get_construct(self, key, default=ValueError()):
        '''Return a metadata construct.

The *unique* construct that satisfies *all* of the given criteria is
returned. All metadata constructs are selected if no parameters are
specified. By default an exception is raised if no unique construct is
selected.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `del_construct`, `get_construct_key`,
             `has_construct`, `set_construct`

:Parameters:

    name: (sequence of) `str`, optional
        Select constructs that have the given name. In general, a
        contruct's name is the string returned by its `!name` method.

        The name may be one of:

        * The value of the standard name property.

          *Parameter example:*
            ``name='air_pressure'`` will select constructs that
            have a "standard_name" property with the value
            "air_pressure", as will ``name=['air_pressure']``.

          *Parameter example:*
            ``name=['air_pressure'`` will select constructs that
            have a "standard_name" property with the value
            "air_pressure".

        * The value of any property prefixed by the property name and
          a colon (``:``).

          *Parameter example:*
            ``name='positive:up'`` will select constructs that
            have a "positive" property with the value "up".

          *Parameter example:*
            ``name='foo:bar'`` will select constructs that have
            a "foo" property with the value "bar".

          *Parameter example:*
            ``name='standard_name:air_pressure'`` will select
            constructs that have a "standard_name" property with the
            value "air_pressure".

          *Parameter example:*
            ``name=['air_pressure', long_name:Air Temperature']`` will
            select constructs that have a "standard_name" property
            with the value "air_pressure" or a "long_name" property
            with a value of "air Temperature".

        * The measure of cell measure constructs, prefixed by
          ``measure%``.

          *Parameter example:*
            ``name='measure%area'`` will select "area" cell
            measure constructs.

        * A construct key, prefixed by ``key%`` (see also the *key*
          parameter).

          *Parameter example:* 
            ``name='key%cellmethod1'`` will select cell method
            construct with construct key "cellmethod1". This is
            equivalent to ``key='cellmethod1'``.

        * The netCDF variable name, prefixed by ``ncvar%`` (see also
          the *ncvar* parameter).

          *Parameter example:*
            ``name='ncvar%lat'`` will select constructs with netCDF
            variable name "lat".

        * The netCDF dimension name of domain axis constructs,
          prefixed by ``ncdim%`` (see also the *ncdim* parameter).

          *Parameter example:*
            ``name='ncdim%time'`` will select domain axis constructs
            with netCDF dimension name "time".

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
          ``key='domainancillary0'`` will the domain ancillary
          construct with construct identifier "domainancillary1". This
          is equivalent to ``name='key%domainancillary0'``.

        *Parameter example:*
          ``key=['cellmethod2']``

        *Parameter example:*
          ``key=('dimensioncoordinate1', 'fieldancillary0')``

    construct: (sequence of) `str`, optional
        Select constructs of the given type, or types. Valid types
        are:

          ==========================  ================================
          *construct*                 Constructs
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
          ``construct='dimension_coordinate'``

        *Parameter example:*
          ``construct=['auxiliary_coordinate']``

        *Parameter example:*
          ``construct=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

    default: optional
        Return the value of the *default* parameter if no unique
        construct has been selected. If set to an `Exception` instance
        then it will be raised if no unique construct has been
        selected. By default an exception is raised in this case.
        
:Returns:
        The unique selected construct. If there is no such construct
        then an exception is raised, or the value of the *default*
        parameter is returned, if provided.

**Examples:**

>>> c = f.get_construct('grid_latitude')
>>> c = f.get_construct('long_name=Air Pressure')
>>> c = f.get_construct('ncvar%lat)
>>> c = f.get_construct('key%cellmeasure0')
>>> c = f.get_construct(key='domainaxis2')
>>> c = f.get_construct(construct='auxiliary_coordinate',
...                     axis=['domainaxis1'])

        '''
        return self.constructs.key(key).get(default=default)

#      out = self.constructs.select(name=name, properties=properties,
#                                    measure=measure, axis=axis,
#                                    key=key, construct=construct,
#                                    ncvar=ncvar, ncdim=ncdim)
#       if not out:
#           return self._default(default, "No construct meets criteria")
#
#       if len(out) > 1:
#           return self._default(default, "More than one construct meets criteria")
#       
#       _, construct = dict(out).popitem()
#           
#       return construct
   #--- End: def

    # parameter: name
    # parameter: properties
    # parameter: measure
    # parameter: ncvar
    # parameter: ncdim
    # parameter: key
    # parameter: axis
    # parameter: construct
    # parameter: default
    def get_construct_data_axes(self, name=None, properties=None,
                                measure=None, ncvar=None, key=None,
                                axis=None, construct=None,
                                default=ValueError()):
        '''Return the construct keys of the domain axis constructs spanned by
a metadata construct data array.

The keys of the domain axis constructs spanned by the *unique*
construct that satisfies *all* of the given criteria are returned. All
metadata constructs are selected if no parameters are specified. By
default an exception is raised if no unique construct is selected.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`, `get_construct_key`,
             `set_construct` `set_construct_data_axes`

:Parameters:

    name: (sequence of) `str`, optional
        Select constructs that have the given name. In general, a
        contruct's name is the string returned by its `!name` method.

        The name may be one of:

        * The value of the standard name property.

          *Parameter example:*
            ``name='air_pressure'`` will select constructs that
            have a "standard_name" property with the value
            "air_pressure", as will ``name=['air_pressure']``.

          *Parameter example:*
            ``name=['air_pressure'`` will select constructs that
            have a "standard_name" property with the value
            "air_pressure".

        * The value of any property prefixed by the property name and
          a colon (``:``).

          *Parameter example:*
            ``name='positive:up'`` will select constructs that
            have a "positive" property with the value "up".

          *Parameter example:*
            ``name='foo:bar'`` will select constructs that have
            a "foo" property with the value "bar".

          *Parameter example:*
            ``name='standard_name:air_pressure'`` will select
            constructs that have a "standard_name" property with the
            value "air_pressure".

          *Parameter example:*
            ``name=['air_pressure', long_name:Air Temperature']`` will
            select constructs that have a "standard_name" property
            with the value "air_pressure" or a "long_name" property
            with a value of "air Temperature".

        * The measure of cell measure constructs, prefixed by
          ``measure%``.

          *Parameter example:*
            ``name='measure%area'`` will select "area" cell
            measure constructs.

        * A construct key, prefixed by ``key%`` (see also the *key*
          parameter).

          *Parameter example:* 
            ``name='key%cellmethod1'`` will select cell method
            construct with construct key "cellmethod1". This is
            equivalent to ``key='cellmethod1'``.

        * The netCDF variable name, prefixed by ``ncvar%`` (see also
          the *ncvar* parameter).

          *Parameter example:*
            ``name='ncvar%lat'`` will select constructs with netCDF
            variable name "lat".

        * The netCDF dimension name of domain axis constructs,
          prefixed by ``ncdim%`` (see also the *ncdim* parameter).

          *Parameter example:*
            ``name='ncdim%time'`` will select domain axis constructs
            with netCDF dimension name "time".

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
          ``key='domainancillary0'`` will the domain ancillary
          construct with construct identifier "domainancillary1". This
          is equivalent to ``name='key%domainancillary0'``.

        *Parameter example:*
          ``key=['cellmethod2']``

        *Parameter example:*
          ``key=('dimensioncoordinate1', 'fieldancillary0')``

    construct: (sequence of) `str`, optional
        Select constructs of the given type, or types. Valid types
        are:

          ==========================  ================================
          *construct*                 Constructs
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
          ``construct='dimension_coordinate'``

        *Parameter example:*
          ``construct=['auxiliary_coordinate']``

        *Parameter example:*
          ``construct=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

    default: optional
        Return the value of the *default* parameter if no unique
        construct has been selected. By default an exception is raised
        in this case.
        
:Returns:

        The construct keys of the domain axis constructs spanned by
        the unique selected construct. If there is no such construct
        then an exception is raised, or the value of the *default*
        parameter is returned, if provided.

**Examples:**

>>> a = f.get_construct_data_axes('grid_latitude')
>>> a = f.get_construct_data_axes('long_name=Air Pressure')
>>> a = f.get_construct_data_axes('ncvar%lat)
>>> a = f.get_construct_data_axes('key%cellmeasure0')
>>> a = f.get_construct_data_axes(key='domainaxis2')
>>> a = f.get_construct_data_axes(construct='auxiliary_coordinate',
...                               axis=['domainaxis1'])

        '''
        cid = self.get_construct_key(name=name, key=key,
                                     measure=measure, ncvar=ncvar,
                                     construct=construct, axis=axis,
                                     default=default)
            
        return self.constructs.data_axes()[cid]
    #--- End: def

    # parameter: name
    # parameter: properties
    # parameter: measure
    # parameter: ncvar
    # parameter: ncdim
    # parameter: key
    # parameter: axis
    # parameter: construct
    # parameter: default
    def get_construct_key(self, name=None, properties=None,
                          measure=None, ncvar=None, ncdim=None,
                          key=None, axis=None, construct=None,
                          default=ValueError()):
        '''Return the key for a metadata construct.

The key for the *unique* construct that satisfies *all* of the given
criteria is returned. All metadata constructs are selected if no
parameters are specified. By default an exception is raised if no
unique construct is selected.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`, `get_construct_data_axes`

:Parameters:

    name: (sequence of) `str`, optional
        Select constructs that have the given name. In general, a
        contruct's name is the string returned by its `!name` method.

        The name may be one of:

        * The value of the standard name property.

          *Parameter example:*
            ``name='air_pressure'`` will select constructs that
            have a "standard_name" property with the value
            "air_pressure", as will ``name=['air_pressure']``.

        * The value of any property prefixed by the property name and
          a colon (``:``).

          *Parameter example:*
            ``name='positive:up'`` will select constructs that
            have a "positive" property with the value "up".

          *Parameter example:*
            ``name='foo:bar'`` will select constructs that have
            a "foo" property with the value "bar".

          *Parameter example:*
            ``name='standard_name:air_pressure'`` will select
            constructs that have a "standard_name" property with the
            value "air_pressure".

          *Parameter example:*
            ``name=['air_pressure', long_name:Air Temperature']`` will
            select constructs that have a "standard_name" property
            with the value "air_pressure" or a "long_name" property
            with a value of "air Temperature".

        * The measure of cell measure constructs, prefixed by
          ``measure%``.

          *Parameter example:*
            ``name='measure%area'`` will select "area" cell
            measure constructs.

        * A construct key, prefixed by ``key%`` (see also the *key*
          parameter).

          *Parameter example:* 
            ``name='key%cellmethod1'`` will select cell method
            construct with construct key "cellmethod1". This is
            equivalent to ``key='cellmethod1'``.

        * The netCDF variable name, prefixed by ``ncvar%`` (see also
          the *ncvar* parameter).

          *Parameter example:*
            ``name='ncvar%lat'`` will select constructs with netCDF
            variable name "lat".

        * The netCDF dimension name of domain axis constructs,
          prefixed by ``ncdim%`` (see also the *ncdim* parameter).

          *Parameter example:*
            ``name='ncdim%time'`` will select domain axis constructs
            with netCDF dimension name "time".

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
          ``key='domainancillary0'`` will the domain ancillary
          construct with construct identifier "domainancillary1". This
          is equivalent to ``name='key%domainancillary0'``.

        *Parameter example:*
          ``key=['cellmethod2']``

        *Parameter example:*
          ``key=('dimensioncoordinate1', 'fieldancillary0')``

    construct: (sequence of) `str`, optional
        Select constructs of the given type, or types. Valid types
        are:

          ==========================  ================================
          *construct* cccc            Constructs
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
          ``construct='dimension_coordinate'``

        *Parameter example:*
          ``construct=['auxiliary_coordinate']``

        *Parameter example:*
          ``construct=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

    default: optional
        Return the value of the *default* parameter if no unique
        construct has been selected. By default an exception is raised
        in this case.
        
:Returns:
        The key of the unique selected construct. If there is no such
        construct then an exception is raised, or the value of the
        *default* parameter is returned, if provided.

**Examples:**


>>> key = f.get_construct_key('grid_latitude')
>>> key = f.get_construct_key('long_name=Air Pressure')
>>> key = f.get_construct_key('ncvar%lat)
>>> key = f.get_construct_key('key%cellmeasure0')
>>> key = f.get_construct_key(key='domainaxis2')
>>> key = f.get_construct_key(construct='auxiliary_coordinate',
...                           axis=['domainaxis1'])

        '''
        out = self.constructs.select(name=name, properties=properties,
                                     measure=measure, axis=axis,
                                     key=key, construct=construct,
                                     ncvar=ncvar, ncdim=ncdim)
        if not out:
            return self._default(default, "No construct meets criteria")

        if len(out) > 1:
            return self._default(default, "More than one construct meets criteria")
        
        key, _ = dict(out).popitem()

        # Return the unique construct key
        return key
    #--- End: def
    
    @property
    def domain_axes(self, copy=False):
        '''Return domain axis constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.domain_axes
Constructs:
{}

>>> f.domain_axes
Constructs:
{'domainaxis0': <DomainAxis: size(1)>,
 'domainaxis1': <DomainAxis: size(10)>,
 'domainaxis2': <DomainAxis: size(9)>,
 'domainaxis3': <DomainAxis: size(1)>}

        '''
        return self.constructs.type('domain_axis')
    #--- End: def

    @property
    def auxiliary_coordinates(self, copy=False):
        '''Return auxiliary coordinate constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.auxiliary_coordinates
Constructs:
{}

>>> f.auxiliary_coordinates
Constructs:
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
 'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >}

        '''
        return self.constructs.type('auxiliary_coordinate')
    #--- End: def

    @property
    def dimension_coordinates(self, copy=False):
        '''Return dimension coordinate constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.dimension_coordinates
Constructs:
{}

>>> f.dimension_coordinates
Constructs:
{'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
 'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

        '''
        return self.constructs.type('dimension_coordinate')
    #--- End: def
    
    def domain_axis_name(self, axis):
        '''TODO 
        '''
        return self.constructs.domain_axis_name(axis)
    #--- End: def
    
#--- End: class
