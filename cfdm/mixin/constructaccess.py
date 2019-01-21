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


        for d in self._get_constructs()._constructs.values():
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

>>> f.cell_measures()
{}

>>> f.cell_measures()
{'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>}

        '''
        return self._get_constructs().constructs(
            construct_type='cell_measure', copy=copy)
    #--- End: def

#    def del_construct(self, description=None, cid=None, axes=None,
#                      construct_type=None):
#        '''Remove a metadata construct.
#
#The construct is identified via optional parameters. The *unique*
#construct that satisfies *all* of the given criteria is removed. An
#error is raised if multiple constructs satisfy all of the given
#criteria.
#
#If a domain axis construct is to be removed then it can't be spanned
#by any data arrays.
#
#.. versionadded:: 1.7.0
#
#.. seealso:: `constructs`, `get_construct`, `has_construct`,
#             `set_construct`
#
#:Parameters:
#
#    description: `str`, optional
#        Select constructs that have the given property, or other
#        attribute, value.
#
#        The description may be one of:
#
#        * The value of the standard name property on its own. 
#
#            *Parameter example:*
#              ``description='air_pressure'`` will select constructs
#              that have a "standard_name" property with the value
#              "air_pressure".
#
#        * The value of any property prefixed by the property name and
#          a colon (``:``).
#
#            *Parameter example:*
#              ``description='positive:up'`` will select constructs
#              that have a "positive" property with the value "up".
#
#            *Parameter example:*
#              ``description='foo:bar'`` will select constructs that
#              have a "foo" property with the value "bar".
#
#            *Parameter example:*
#              ``description='standard_name:air_pressure'`` will select
#              constructs that have a "standard_name" property with the
#              value "air_pressure".
#
#        * The measure of cell measure constructs, prefixed by
#          ``measure%``.
#
#            *Parameter example:*
#              ``description='measure%area'`` will select "area" cell
#              measure constructs.
#
#        * A construct identifier, prefixed by ``cid%`` (see also the
#          *cid* parameter).
#
#            *Parameter example:* 
#              ``description='cid%cellmethod1'`` will select cell
#              method construct with construct identifier
#              "cellmethod1". This is equivalent to
#              ``cid='cellmethod1'``.
#
#        * The netCDF variable name, prefixed by ``ncvar%``.
#
#            *Parameter example:*
#              ``description='ncvar%lat'`` will select constructs with
#              netCDF variable name "lat".
#
#        * The netCDF dimension name of domain axis constructs,
#          prefixed by ``ncdim%``.
#
#            *Parameter example:*
#              ``description='ncdim%time'`` will select domain axis
#              constructs with netCDF dimension name "time".
#
#    cid: `str`, optional
#        Select the construct with the given construct identifier.
#
#        *Parameter example:*
#          ``cid='domainancillary0'`` will the domain ancillary
#          construct with construct identifier "domainancillary1". This
#          is equivalent to ``description='cid%domainancillary0'``.
#
#    construct_type: `str`, optional
#        Select constructs of the given type. Valid types are:
#
#          ==========================  ================================
#          *construct_type*            Constructs
#          ==========================  ================================
#          ``'domain_ancillary'``      Domain ancillary constructs
#          ``'dimension_coordinate'``  Dimension coordinate constructs
#          ``'domain_axis'``           Domain axis constructs
#          ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
#          ``'cell_measure'``          Cell measure constructs
#          ``'coordinate_reference'``  Coordinate reference constructs
#          ``'cell_method'``           Cell method constructs
#          ``'field_ancillary'``       Field ancillary constructs
#          ==========================  ================================
#
#        *Parameter example:*
#          ``construct_type='dimension_coordinate'``
#
#        *Parameter example:*
#          ``construct_type=['auxiliary_coordinate']``
#
#        *Parameter example:*
#          ``construct_type=('domain_ancillary', 'cell_method')``
#
#        Note that a domain never contains cell method nor field
#        ancillary constructs.
#
#    axes: sequence of `str`, optional
#        Select constructs which have data that spans one or more of
#        the given domain axes, in any order. Domain axes are specified
#        by their construct identifiers.
#
#        *Parameter example:*
#          ``axes=['domainaxis2']``
#
#        *Parameter example:*
#          ``axes=['domainaxis0', 'domainaxis1']``
#
#:Returns:
#
#        The removed metadata construct.
#
#**Examples:**
#
#>>> c = f.del_construct('grid_latitude')
#>>> c = f.del_construct('long_name:Air Pressure')
#>>> c = f.del_construct('ncvar%lat)
#>>> c = f.del_construct('cid%cellmeasure0')
#>>> c = f.del_construct(cid='domainaxis2')
#>>> c = f.del_construct(construct_type='auxiliary_coordinate',
#...                     axes=['domainaxis1'])
#
#        '''
#        key = self.get_construc_key(description=description, cid=cid,
#                                     construct_type=construct_type,
#                                    axes=axes)
#        if key is None:
#            raise ValueError("No such construct {} {} {}".format(description, construct_type, axes))
#
#        return self._get_constructs().del_construct(cid=key)
#    #--- End: def

    # parameter: name
    # parameter: properties
    # parameter: measure
    # parameter: ncvar
    # parameter: ncdim
    # parameter: key
    # parameter: axis
    # parameter: construct_type
    # parameter: default
    def get_construct(self, name=None, properties=None, measure=None,
                      ncvar=None, ncdim=None, key=None, axis=None,
                      construct_type=None, copy=False,
                      default=ValueError()):
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

    key: `str`, optional
        Select the construct with the given construct key.

        *Parameter example:*
          ``key='domainancillary0'`` will the domain ancillary
          construct with construct identifier "domainancillary1". This
          is equivalent to ``name='key%domainancillary0'``.

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

        *Parameter example:*
          ``construct_type='dimension_coordinate'``

        *Parameter example:*
          ``construct_type=['auxiliary_coordinate']``

        *Parameter example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    axis: (sequence of) `str`, optional
        Select constructs which have data that spans one or more of
        the given domain axis constructs, in any order. Domain axis
        contructs are specified by their construct keys.

        *Parameter example:*
          ``axis='domainaxis2'``

        *Parameter example:*
          ``axis=['domainaxis2']``

        *Parameter example:*
          ``axis=['domainaxis0', 'domainaxis1']``

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

    default: optional
        Return the value of the *default* parameter if no unique
        construct has been selected. By default an exception is raised
        in this case.
        
:Returns:
        The unique selected construct. If there is no such construct
        then an exception is raised, or the value of the *default*
        parameter is returned, if provided.

**Examples:**

>>> c = f.get_construct('grid_latitude')
>>> c = f.get_construct('long_name:Air Pressure')
>>> c = f.get_construct('ncvar%lat)
>>> c = f.get_construct('key%cellmeasure0')
>>> c = f.get_construct(key='domainaxis2')
>>> c = f.get_construct(construct_type='auxiliary_coordinate',
...                     axis=['domainaxis1'])

        '''
        out = self.constructs(name=name, properties=properties,
                              measure=measure, axis=axis, key=key,
                              construct_type=construct_type,
                              ncvar=ncvar, ncdim=ncdim, copy=copy)

        if not out:
            return self._default(default, "No construct meets criteria")
        
        _, construct = out.popitem()
        if out:
            return self._default(default, "More than one construct meets criteria")
            
        return construct
    #--- End: def
    
    def _default(self, default, message=None):
        '''<TODO>
        '''
        if isinstance(default, Exception):
            if message is not None and not default.args:
                default.args = (message,)

            raise default
        
        return default
    #--- End: def
    

    # parameter: name
    # parameter: properties
    # parameter: measure
    # parameter: ncvar
    # parameter: ncdim
    # parameter: key
    # parameter: axis
    # parameter: construct_type
    # parameter: default
    def get_construct_data_axes(self, name=None, properties=None,
                                measure=None, ncvar=None, key=None,
                                axis=None, construct_type=None,
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

    key: `str`, optional
        Select the construct with the given construct key.

        *Parameter example:*
          ``key='domainancillary0'`` will the domain ancillary
          construct with construct identifier "domainancillary1". This
          is equivalent to ``name='key%domainancillary0'``.

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

        *Parameter example:*
          ``construct_type='dimension_coordinate'``

        *Parameter example:*
          ``construct_type=['auxiliary_coordinate']``

        *Parameter example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    axis: (sequence of) `str`, optional
        Select constructs which have data that spans one or more of
        the given domain axis constructs, in any order. Domain axis
        contructs are specified by their construct keys.

        *Parameter example:*
          ``axis='domainaxis2'``

        *Parameter example:*
          ``axis=['domainaxis2']``

        *Parameter example:*
          ``axis=['domainaxis0', 'domainaxis1']``

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

    default: optional
        Return the value of the *default* parameter if no unique
        construct has been selected. By default an exception is raised
        in this case.
        
:Returns:

        The construct keys of the domain axis constructs spanned by the unique selected construct. If there is no such construct
        then an exception is raised, or the value of the *default*
        parameter is returned, if provided.

**Examples:**

>>> a = f.get_construct_data_axes('grid_latitude')
>>> a = f.get_construct_data_axes('long_name:Air Pressure')
>>> a = f.get_construct_data_axes('ncvar%lat)
>>> a = f.get_construct_data_axes('key%cellmeasure0')
>>> a = f.get_construct_data_axes(key='domainaxis2')
>>> a = f.get_construct_data_axes(construct_type='auxiliary_coordinate',
...                               axis=['domainaxis1'])

        '''
        cid = self.get_construct_key(name=name, key=key,
                                     measure=measure, ncvar=ncvar,
                                     construct_type=construct_type,
                                     axis=axis, default=default)

        if cid is None:
            return self._default(default, 'No unique construct meets criteria')
            
        return self.constructs_data_axes()[cid]
    #--- End: def

    # parameter: name
    # parameter: properties
    # parameter: measure
    # parameter: ncvar
    # parameter: ncdim
    # parameter: key
    # parameter: axis
    # parameter: construct_type
    # parameter: default
    def get_construct_key(self, name=None, properties=None,
                          measure=None, ncvar=None, ncdim=None,
                          key=None, axis=None, construct_type=None,
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

    key: `str`, optional
        Select the construct with the given construct key.

        *Parameter example:*
          ``key='domainancillary0'`` will the domain ancillary
          construct with construct identifier "domainancillary1". This
          is equivalent to ``name='key%domainancillary0'``.

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

        *Parameter example:*
          ``construct_type='dimension_coordinate'``

        *Parameter example:*
          ``construct_type=['auxiliary_coordinate']``

        *Parameter example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    axis: (sequence of) `str`, optional
        Select constructs which have data that spans one or more of
        the given domain axis constructs, in any order. Domain axis
        contructs are specified by their construct keys.

        *Parameter example:*
          ``axis='domainaxis2'``

        *Parameter example:*
          ``axis=['domainaxis2']``

        *Parameter example:*
          ``axis=['domainaxis0', 'domainaxis1']``

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
>>> key = f.get_construct_key('long_name:Air Pressure')
>>> key = f.get_construct_key('ncvar%lat)
>>> key = f.get_construct_key('key%cellmeasure0')
>>> key = f.get_construct_key(key='domainaxis2')
>>> key = f.get_construct_key(construct_type='auxiliary_coordinate',
...                           axis=['domainaxis1'])

        '''
        c = self.constructs(name=name, properties=properties,
                            measure=measure, axis=axis, key=key,
                            construct_type=construct_type,
                            ncvar=ncvar, ncdim=ncdim, copy=False)
        if len(c) != 1:
            return self._default(default, "No unique construct meets criteria")
        
        cid, _ = c.popitem()

        # Return the unique construct key
        return cid
    #--- End: def
    
    # parameter: name
    # parameter: properties
    # parameter: measure
    # parameter: ncvar
    # parameter: ncdim
    # parameter: key
    # parameter: axis
    # parameter: construct_type
    def has_construct(self, name=None, properties=None, measure=None,
                      ncvar=None, ncdim=None, key=None, axis=None,
                      construct_type=None):
        '''Whether a metadata construct has been set.

True is returned if, and only if, there is a *unique* construct that
satisfies *all* of the given criteria is returned. All metadata
constructs are selected if no parameters are specified.

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

    key: `str`, optional
        Select the construct with the given construct key.

        *Parameter example:*
          ``key='domainancillary0'`` will the domain ancillary
          construct with construct identifier "domainancillary1". This
          is equivalent to ``name='key%domainancillary0'``.

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

        *Parameter example:*
          ``construct_type='dimension_coordinate'``

        *Parameter example:*
          ``construct_type=['auxiliary_coordinate']``

        *Parameter example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    axis: (sequence of) `str`, optional
        Select constructs which have data that spans one or more of
        the given domain axis constructs, in any order. Domain axis
        contructs are specified by their construct keys.

        *Parameter example:*
          ``axis='domainaxis2'``

        *Parameter example:*
          ``axis=['domainaxis2']``

        *Parameter example:*
          ``axis=['domainaxis0', 'domainaxis1']``

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.
        
:Returns:

    `bool`

        Whether or not a unique construct has been selected.

**Examples:**

>>> x = f.has_construct('grid_latitude')
>>> x = f.has_construct('long_name:Air Pressure')
>>> x = f.has_construct('ncvar%lat)
>>> x = f.has_construct('key%cellmeasure0')
>>> x = f.has_construct(key='domainaxis2')
>>> x = f.has_construct(construct_type='auxiliary_coordinate',
...                     axis=['domainaxis1'])

        '''
        out = self.constructs(name=name, properties=properties,
                              measure=measure, axis=axis, key=key,
                              construct_type=construct_type,
                              ncvar=ncvar, ncdim=ncdim, copy=False)

        return len(out) == 1
    #--- End: def

    # parameter: name
    # parameter: properties
    # parameter: measure
    # parameter: ncvar
    # parameter: ncdim
    # parameter: key
    # parameter: axis
    # parameter: construct_type
    # parameter: copy
    def constructs(self, name=None, properties=None, measure=None,
                   ncvar=None, ncdim=None, key=None, axis=None,
                   construct_type=None, copy=False):
        '''Return metadata constructs

By default all metadata constructs are returned, but a subset may be
selected via the optional parameters. If multiple parameters are
specified, then the constructs that satisfy *all* of the criteria are
returned.

.. versionadded:: 1.7.0

.. seealso:: `constructs_data_axes`, `del_construct`, `get_construct`
             `get_construct_key`, `has_construct`, `set_construct`

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

    key: `str`, optional
        Select the construct with the given construct key.

        *Parameter example:*
          ``key='domainancillary0'`` will the domain ancillary
          construct with construct identifier "domainancillary1". This
          is equivalent to ``name='key%domainancillary0'``.

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

        *Parameter example:*
          ``construct_type='dimension_coordinate'``

        *Parameter example:*
          ``construct_type=['auxiliary_coordinate']``

        *Parameter example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    axis: (sequence of) `str`, optional
        Select constructs which have data that spans one or more of
        the given domain axis constructs, in any order. Domain axis
        contructs are specified by their construct keys.

        *Parameter example:*
          ``axis='domainaxis2'``

        *Parameter example:*
          ``axis=['domainaxis2']``

        *Parameter example:*
          ``axis=['domainaxis0', 'domainaxis1']``

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `dict`
        The selected constructs, in a dictionary keyed by their
        construct keys. All constructs are returned if no selection
        criteria are given. An empty dictionary is returned if no
        constructs meet the given criteria.

**Examples:**

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
{'cellmethod0', <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1', <CellMethod: domainaxis3: maximum>}
>>> f.constructs(construct_type=['cell_method', 'field_ancillary'])
{'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1': <CellMethod: domainaxis3: maximum>,
 'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}
>>> f.constructs(axis='domainaxis0')
{'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
 'domainancillary1': <DomainAncillary: ncvar%b(1) >}
>>> f.constructs(axis=['domainaxis0', 'domainaxis1'])
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
...              axis=['domainaxis1'])
{'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>}
>>> f.constructs('air_pressure')
{}

        '''
        return self._get_constructs().constructs(name=name,
                                                 properties=properties,
                                                 measure=measure,
                                                 ncvar=ncvar,
                                                 ncdim=ncdim, key=key,
                                                 construct_type=construct_type,
                                                 axis=axis, copy=copy)
    #--- End: def

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
    
#--- End: class
