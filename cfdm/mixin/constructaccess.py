import re


class ConstructAccess():
    '''Mixin class for manipulating constructs stored in a `Constructs`
    object.

    .. versionadded:: (cfdm) 1.7.0

    '''
#    # ----------------------------------------------------------------
#    # Private methods
#    # ----------------------------------------------------------------
#    def _set_dataset_compliance(self, value):
#        '''Set the report of problems encountered whilst reading the construct
#    from a dataset.
#
#    .. versionadded:: (cfdm) 1.7.0
#
#    .. seealso:: `dataset_compliance`
#
#    :Parameters:
#
#        value:
#           The value of the ``dataset_compliance`` component.
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#        '''
#        self._set_component('dataset_compliance', value, copy=True)

    def _unique_construct_names(self):
        '''Return unique metadata construct names.

    .. versionadded:: (cfdm) 1.7.0

    **Examples:**

    >>> f._unique_construct_names()
    {'cellmethod0': 'method:mean',
     'dimensioncoordinate0': 'latitude',
     'dimensioncoordinate1': 'longitude',
     'dimensioncoordinate2': 'time',
     'domainaxis0': 'ncdim%lat',
     'domainaxis1': 'ncdim%lon',
     'domainaxis2': 'key%domainaxis2'}

        '''
        key_to_name = {}
        name_to_keys = {}

        for d in self.constructs._constructs.values():
            name_to_keys = {}

            for key, construct in d.items():
                name = construct.identity(default='key%'+key)
                name_to_keys.setdefault(name, []).append(key)
                key_to_name[key] = name

            for name, keys in name_to_keys.items():
                if len(keys) <= 1:
                    continue

                for key in keys:
                    key_to_name[key] = '{0}{{{1}}}'.format(
                        name,
                        re.findall('\d+$', key)[0])
        # --- End: for

        return key_to_name

    def _unique_domain_axis_identities(self):
        '''Return unique domain axis construct names.

    .. versionadded:: (cfdm) 1.7.0

    **Examples:**

    >>> f._unique_domain_axis_identities()
    {'domainaxis0': 'latitude(5)',
     'domainaxis1': 'longitude(8)',
     'domainaxis2': 'time(1)'}

        '''
        key_to_name = {}
        name_to_keys = {}

        for key, value in self.domain_axes.items():
            name_size = (self.constructs.domain_axis_identity(key),
                         value.get_size(''))
            name_to_keys.setdefault(name_size, []).append(key)
            key_to_name[key] = name_size

        for (name, size), keys in name_to_keys.items():
            if len(keys) == 1:
                key_to_name[keys[0]] = '{0}({1})'.format(name, size)
            else:
                for key in keys:
                    key_to_name[key] = '{0}{{{1}}}({2})'.format(
                        name,
                        re.findall('\d+$', key)[0],
                        size)
        # --- End: for

        return key_to_name

    def _get_data_compression_variables(self, component):
        '''

        '''
        out = []
        for construct in self.constructs.filter_by_data().values():
            data = construct.get_data(None)
            if data is None:
                continue

            x = getattr(data, 'get_' + component)(None)
            if x is None:
                continue

            out.append(x)

        for construct in self.constructs.filter_by_data().values():
            if not construct.has_bounds():
                continue

            data = construct.get_bounds_data(None)
            if data is None:
                continue

            x = getattr(data, 'get_' + component)(None)
            if x is None:
                continue

            out.append(x)

        for construct in self.coordinates.values():
            interior_ring = construct.get_interior_ring(None)
            if interior_ring is None:
                continue

            data = interior_ring.get_data(None)
            if data is None:
                continue

            x = getattr(data, 'get_' + component)(None)
            if x is None:
                continue

            out.append(x)

        return out

    def _get_coordinate_geometry_variables(self, component):
        '''Return the list of variables for the geometry coordinates.

    :Parameters:

        component: `str`

    :Returns:

        `list'

        '''
        out = []
        for construct in self.coordinates.values():
            x = getattr(construct, 'get_' + component)(None)
            if x is None:
                continue

            out.append(x)

        return out

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def coordinate_references(self):
        '''Return coordinate reference constructs.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `constructs`

    :Returns:

        `Constructs`
            The constructs and their construct keys.


    **Examples:**

    >>> f.coordinate_references
    Constructs:
    {}

    >>> f.coordinate_references
    Constructs:
    {'coordinatereference0': <{{repr}}CoordinateReference: atmosphere_hybrid_height_coordinate>,
     'coordinatereference1': <{{repr}}CoordinateReference: rotated_latitude_longitude>}

        '''
        return self.constructs.filter_by_type('coordinate_reference')

    @property
    def domain_axes(self):
        '''Return domain axis constructs.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `constructs`

    :Returns:

        `Constructs`
            The domain axis constructs and their construct keys.

    **Examples:**

    >>> f.domain_axes
    Constructs:
    {}

    >>> f.domain_axes
    Constructs:
    {'domainaxis0': <{{repr}}DomainAxis: size(1)>,
     'domainaxis1': <{{repr}}DomainAxis: size(10)>,
     'domainaxis2': <{{repr}}DomainAxis: size(9)>,
     'domainaxis3': <{{repr}}DomainAxis: size(1)>}

        '''
        return self.constructs.filter_by_type('domain_axis')

    @property
    def auxiliary_coordinates(self):
        '''Return auxiliary coordinate constructs.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `constructs`

    :Returns:

        `Constructs`
            The auxiliary coordinate constructs and their construct
            keys.

    **Examples:**

    >>> f.auxiliary_coordinates
    Constructs:
    {}

    >>> f.auxiliary_coordinates
    Constructs:
    {'auxiliarycoordinate0': <{{repr}}AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
     'auxiliarycoordinate1': <{{repr}}AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
     'auxiliarycoordinate2': <{{repr}}AuxiliaryCoordinate: long_name:Grid latitude name(10) >}

        '''
        return self.constructs.filter_by_type('auxiliary_coordinate')

    @property
    def dimension_coordinates(self):
        '''Return dimension coordinate constructs.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `constructs`

    :Returns:

        `Constructs`
            The dimension coordinate constructs and their construct
            keys.

    **Examples:**

    >>> f.dimension_coordinates
    Constructs:
    {}

    >>> f.dimension_coordinates
    Constructs:
    {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
     'dimensioncoordinate1': <{{repr}}DimensionCoordinate: grid_latitude(10) degrees>,
     'dimensioncoordinate2': <{{repr}}DimensionCoordinate: grid_longitude(9) degrees>,
     'dimensioncoordinate3': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >}

        '''
        return self.constructs.filter_by_type('dimension_coordinate')

    @property
    def coordinates(self):
        '''Return dimension and auxiliary coordinate constructs.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `auxiliary_coordinates`, `constructs`,
                 `dimension_coordinates`

    :Returns:

        `Constructs`
            The auxiliary coordinate and dimension coordinate
            constructs and their construct keys.

    **Examples:**

    >>> f.coordinates
    Constructs:
    {}

    >>> f.coordinates
    Constructs:
    {'auxiliarycoordinate0': <{{repr}}AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
     'auxiliarycoordinate1': <{{repr}}AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
     'auxiliarycoordinate2': <{{repr}}AuxiliaryCoordinate: long_name=Grid latitude name(10) >,
     'dimensioncoordinate0': <{{repr}}DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
     'dimensioncoordinate1': <{{repr}}DimensionCoordinate: grid_latitude(10) degrees>,
     'dimensioncoordinate2': <{{repr}}DimensionCoordinate: grid_longitude(9) degrees>,
     'dimensioncoordinate3': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >}

        '''
        out = self.dimension_coordinates
        out._update(self.auxiliary_coordinates)
        return out

    @property
    def domain_ancillaries(self):
        '''Return domain ancillary constructs.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `constructs`

    :Returns:

        `Constructs`
            The domain ancillary constructs and their construct keys.

    **Examples:**

    >>> f.domain_ancillaries
    Constructs:
    {}

    >>> f.domain_ancillaries
    Constructs:
    {'domainancillary0': <{{repr}}DomainAncillary: ncvar%a(1) m>,
     'domainancillary1': <{{repr}}DomainAncillary: ncvar%b(1) >,
     'domainancillary2': <{{repr}}DomainAncillary: surface_altitude(10, 9) m>}

        '''
        return self.constructs.filter_by_type('domain_ancillary')

    @property
    def cell_measures(self):
        '''Return cell measure constructs.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `constructs`

    :Returns:

        `Constructs`
            The cell measure constructs and their construct keys.

    **Examples:**

    >>> f.cell_measures
    Constructs:
    {}

    >>> f.cell_measures
    Constructs:
    {'cellmeasure0': <{{repr}}CellMeasure: measure%area(9, 10) km2>}

        '''
        return self.constructs.filter_by_type('cell_measure')

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def construct(self, identity, default=ValueError()):
        '''Select a metadata construct by its identity.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `construct_key`, `constructs`,
                 `Constructs.filter_by_identity`, `Constructs.value`

    :Parameters:

        identity: optional
            Select constructs that have the given identity. If exactly
            one construct is selected then it is returned, otherwise
            an exception is raised.

            The identity is specified by a string
            (e.g. ``'latitude'``, ``'long_name=time'``, etc.); or a
            compiled regular expression
            (e.g. ``re.compile('^atmosphere')``), for which all
            constructs whose identities match (via `re.search`) are
            selected.

            Each construct has a number of identities, and is selected
            if any of them match any of those provided. A construct's
            identities are those returned by its `!identities`
            method. In the following example, the construct ``c`` has
            four identities:

               >>> c.identities()
               ['time', 'long_name=Time', 'foo=bar', 'ncvar%T']

            In addition, each construct also has an identity based its
            construct key (e.g. ``'key%dimensioncoordinate2'``)

            Note that in the output of a `print` call or `!dump`
            method, a construct is always described by one of its
            identities, and so this description may always be used as
            an *identity* argument.

        default: optional
            Return the value of the *default* parameter if the
            property has not been set.

            {{default Exception}}

    :Returns:

            The selected construct.

    **Examples:**

    >>> print(f.constructs)
    Constructs:
    {'cellmethod0': {{repr}}<CellMethod: area: mean>,
     'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
     'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
     'dimensioncoordinate2': <{{repr}}DimensionCoordinate: long_name=time(1) days since 2018-12-01 >,
     'domainaxis0': <{{repr}}DomainAxis: size(5)>,
     'domainaxis1': <{{repr}}DomainAxis: size(8)>,
     'domainaxis2': <{{repr}}DomainAxis: size(1)>}

    Select the construct that has the "standard_name" property of 'latitude':

    >>> f.construct('latitude')
    <{{repr}}DimensionCoordinate: latitude(5) degrees_north>

    Select the cell method construct that has a "method" of 'mean':

    >>> f.construct('method:mean')
    <{{repr}}CellMethod: area: mean>

    Attempt to select the construct whose "standard_name" start with the
    letter 'l':

    >>> import re
    >>> f.construct(re.compile('^l'))
    ValueError: Can't return 2 constructs
    >>> f.construct(re.compile('^l'), default='no construct')
    'no construct'

        '''
        c = self.constructs.filter_by_identity(identity)
        if len(c) == 1:
            return c.value()

        if not c:
            return self._default(default,
                                 "Can't return zero constructs")

        return self._default(default,
                             "Can't return {0} constructs".format(len(c)))

    def construct_key(self, identity, default=ValueError()):
        '''Select the key of a metadata construct by its identity.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `construct`, `constructs`,
                 `Constructs.filter_by_identity`, `Constructs.key`

    :Parameters:

        identity: optional
            Select constructs that have the given identity. If exactly
            one construct is selected then it is returned, otherwise
            an exception is raised.

            The identity is specified by a string
            (e.g. ``'latitude'``, ``'long_name=time'``, etc.); or a
            compiled regular expression
            (e.g. ``re.compile('^atmosphere')``), for which all
            constructs whose identities match (via `re.search`) are
            selected.

            Each construct has a number of identities, and is selected
            if any of them match any of those provided. A construct's
            identities are those returned by its `!identities`
            method. In the following example, the construct ``c`` has
            four identities:

               >>> c.identities()
               ['time', 'long_name=Time', 'foo=bar', 'ncvar%T']

            In addition, each construct also has an identity based its
            construct key (e.g. ``'key%dimensioncoordinate2'``)

            Note that in the output of a `print` call or `!dump`
            method, a construct is always described by one of its
            identities, and so this description may always be used as
            an *identity* argument.

        default: optional
            Return the value of the *default* parameter if the
            property has not been set

            {{default Exception}}

    :Returns:

        `str`
            The key of the selected construct.

    **Examples:**

    >>> print(f.constructs)
    Constructs:
    {'cellmethod0': <{{repr}}ellMethod: area: mean>,
     'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
     'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
     'dimensioncoordinate2': <{{repr}}DimensionCoordinate: long_name=time(1) days since 2018-12-01 >,
     'domainaxis0': <{{repr}}DomainAxis: size(5)>,
     'domainaxis1': <{{repr}}DomainAxis: size(8)>,
     'domainaxis2': <{{repr}}DomainAxis: size(1)>}

    Select the construct that has the "standard_name" property of
    'latitude':

    >>> f.construct_key('latitude')
     'dimensioncoordinate0'

    Select the cell method construct that has a "method" of 'mean':

    >>> f.construct_key('method:mean')
    'cellmethod0'

    Attempt to select the construct whose "standard_name" start with
    the letter 'l':

    >>> import re
    >>> f.construct_key(re.compile('^l'))
    ValueError: Can't return the key of 2 constructs
    >>> f.construct_key(re.compile('^l'), default='no construct')
    'no construct'

        '''
        c = self.constructs.filter_by_identity(identity)
        if len(c) == 1:
            return c.key()

        if not c:
            return self._default(default,
                                 "Can't return the key of zero constructs")

        return self._default(
            default,
            "Can't return the keys of {0} constructs".format(len(c)))

#    def dataset_compliance(self, display=False):
#        '''A report of problems encountered whilst reading the construct from
#    a dataset.
#
#    If the dataset is partially CF-compliant to the extent that it is
#    not possible to unambiguously map an element of the netCDF dataset
#    to an element of the CF data model, then a construct is still
#    returned by the `read` function, but may be incomplete.
#
#    Such "structural" non-compliance would occur, for example, if the
#    ``coordinates`` attribute of a CF-netCDF data variable refers to
#    another variable that does not exist, or refers to a variable that
#    spans a netCDF dimension that does not apply to the data variable.
#
#    Other types of non-compliance are not checked, such whether or not
#    controlled vocabularies have been adhered to.
#
#    .. versionadded:: (cfdm) 1.7.0
#
#    .. seealso:: `{{package}}.read`
#
#    :Parameters:
#
#        display: `bool`, optional
#            If True print the compliance report. By default the report
#            is returned as a dictionary.
#
#    :Returns:
#
#        `None` or `dict`
#            The report. If *display* is True then the report is
#            printed and `None` is returned. Otherwise the report is
#            returned as a dictionary.
#
#    **Examples:**
#
#    If no problems were encountered, an empty dictionary is returned:
#
#    >>> f.dataset_compliance()
#    {}
#
#        '''
#        d = self._get_component('dataset_compliance', {})
#
#        if not display:
#            return d
#
#        if not d:
#            print(d)
#            return
#
#        for key0, value0 in d.items():
#            print('{{{0!r}:'.format(key0))
#            print('    CF version: {0!r},'.format(value0['CF version']))
#            print('    dimensions: {0!r},'.format(value0['dimensions']))
#            print('    non-compliance: {')
#            for key1, value1 in sorted(value0['non-compliance'].items()):
#                for x in value1:
#                    print('        {!r}: ['.format(key1))
#                    print('            {{{0}}},'.format(
#                        '\n             '.join(
#                            ['{0!r}: {1!r},'.format(key2, value2)
#                             for key2, value2 in sorted(x.items())]
#                        )
#                    ))
#
#                print('        ],')
#
#            print('    },')

    def domain_axis_key(self, identity, default=ValueError()):
        '''Return the key of the domain axis construct that is spanned by 1-d
    coordinate constructs.

    :Parameters:

        identity:
            Select the 1-d coordinate constructs that have the given
            identity.

            An identity is specified by a string (e.g. ``'latitude'``,
            ``'long_name=time'``, etc.); or a compiled regular
            expression (e.g. ``re.compile('^atmosphere')``), for which
            all constructs whose identities match (via `re.search`)
            are selected.

            Each coordinate construct has a number of identities, and
            is selected if any of them match any of those provided. A
            construct's identities are those returned by its
            `!identities` method. In the following example, the
            construct ``x`` has four identities:

               >>> x.identities()
               ['time', 'long_name=Time', 'foo=bar', 'ncvar%T']

            In addition, each construct also has an identity based its
            construct key (e.g. ``'key%dimensioncoordinate2'``)

            Note that in the output of a `print` call or `!dump`
            method, a construct is always described by one of its
            identities, and so this description may always be used as
            an *identity* argument.

        default: optional
            Return the value of the *default* parameter if a domain
            axis construct can not be found.

            {{default Exception}}

    :Returns:

        `str`
            The key of the domain axis construct that is spanned by
            the data of the selected 1-d coordinate constructs.

    **Examples:**

    >>> print(f.constructs())
    Constructs:
    {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: time(1) days since 1964-01-21 00:00:00 >,
     'dimensioncoordinate1': <{{repr}}DimensionCoordinate: pressure(23) mbar>,
     'dimensioncoordinate2': <{{repr}}DimensionCoordinate: latitude(160) degrees_north>,
     'dimensioncoordinate3': <{{repr}}DimensionCoordinate: longitude(320) degrees_east>,
     'domainaxis0': <{{repr}}DomainAxis: size(1)>,
     'domainaxis1': <{{repr}}DomainAxis: size(23)>,
     'domainaxis2': <{{repr}}DomainAxis: size(160)>,
     'domainaxis3': <{{repr}}DomainAxis: size(320)>}
    >>> f.domain.domain_axis_key('time')
    'domainaxis0'
    >>> f.domain.domain_axis_key('longitude')
    'domainaxis3'

        '''
        constructs = self.constructs

        # Select 1-d coordinate constructs with the given identity
        c = constructs.filter_by_type('dimension_coordinate',
                                      'auxiliary_coordinate')
        c = c.filter_by_naxes(1)
        c = c.filter_by_identity(identity)

        if not len(c):
            return self._default(
                default,
                "No 1-d coordinate constructs have identity {!r}".format(
                    identity))

        data_axes = constructs.data_axes()
        domain_axes = constructs.filter_by_type('domain_axis')

        keys = []
        for ckey, coord in c.items():
            axes = data_axes.get(ckey)
            if not axes:
                continue

            key = axes[0]
            if domain_axes.get(key):
                keys.append(key)
        # --- End: for

        keys = set(keys)

        if not keys:
            return self._default(
                default,
                "1-d coordinate constructs selected with identity "
                "{!r} have not been assigned a domain axis constructs".format(
                    coord))

        if len(keys) > 1:
            return self._default(
                default,
                "Multiple 1-d coordinate constructs selected "
                "with identity {!r} span multiple domain axes: {!r}".format(
                    identity, keys))

        return keys.pop()

    def has_geometry(self):
        '''Return whether or not any coordinates have cell geometries.

    .. versionadded:: (cfdm) 1.8.0
    
    :Returns:
    
        `bool`
            True if there are geometries, otherwise False.
        
    **Examples:**

    >>> f = {{package}}.{{class}}()
    >>> f.has_geometry()
    False

        '''
        for c in self.constructs.filter_by_type(
                'auxiliary_coordinate',
                'dimension_coordinate',
                'domain_ancillary').values():
            if c.has_geometry():
                return True

        return False

#    # ----------------------------------------------------------------
#    # NetCDF interface methods
#    # ----------------------------------------------------------------
#    def nc_set_component_variable(self, component, value):
#        '''Set the netCDF variable name for all components of the given type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_del_component_variable`,
#                 `nc_set_component_variable_groups`,
#                 `nc_clear_component_variable_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'interior_ring'``    Interior ring variables for
#                                   geometry coordinates
#
#
#            ``'node_count'``       Node count variables for geometry
#                                   coordinates
#
#            ``'part_node_count'``  Part node count variables for
#                                   geometry coordinates
#
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#
#            ``'list'``             List variables for compression by
#                                   gathering
#            =====================  ===================================
#
#        value: `str`
#            The netCDF variable name to be set for each component.
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_set_component_variable('interior_ring', 'interiorring_1')
#
#        '''
#        if component in ('count', 'index', 'list'):
#            variables = self._get_data_compression_variables(component)
#        elif component in ('interior_ring', 'node_count', 'part_node_count'):
#            variables = self._get_coordinate_geometry_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_set_variable(value)
#
#    def nc_del_component_variable(self, component):
#        '''Remove the netCDF variable name for all components of the given
#    type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_set_component_variable`,
#                 `nc_set_component_variable_groups`,
#                 `nc_clear_component_variable_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'interior_ring'``    Interior ring variables for
#                                   geometry coordinates
#
#            ``'node_count'``       Node count variables for geometry
#                                   coordinates
#
#            ``'part_node_count'``  Part node count variables for
#                                   geometry coordinates
#
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#
#            ``'list'``             List variables for compression by
#                                   gathering
#
#            =====================  ===================================
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_del_component_variable('interior_ring')
#
#        '''
#        if component in ('count', 'index', 'list'):
#            variables = self._get_data_compression_variables(component)
#        elif component in ('interior_ring', 'node_count', 'part_node_count'):
#            variables = self._get_coordinate_geometry_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_del_variable(None)
#
#    def nc_set_component_variable_groups(self, component, groups):
#        '''Set the netCDF variable groups hierarchy for all components of the
#    given type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_del_component_variable`,
#                 `nc_set_component_variable`,
#                 `nc_clear_component_variable_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'interior_ring'``    Interior ring variables for
#                                   geometry coordinates
#
#            ``'node_count'``       Node count variables for geometry
#                                   coordinates
#
#            ``'part_node_count'``  Part node count variables for
#                                   geometry coordinates
#
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#
#            ``'list'``             List variables for compression by
#                                   gathering
#            =====================  ===================================
#
#        groups: sequence of `str`
#            The new group structure for each component.
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_set_component_variable_groups('interior_ring', ['forecast'])
#
#        '''
#        if component in ('count', 'index', 'list'):
#            variables = self._get_data_compression_variables(component)
#        elif component in ('interior_ring', 'node_count', 'part_node_count'):
#            variables = self._get_coordinate_geometry_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_set_variable_groups(groups)
#
#    def nc_clear_component_variable_groups(self, component):
#        '''Remove the netCDF variable groups hierarchy for all components of
#    the given type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_del_component_variable`,
#                 `nc_set_component_variable`,
#                 `nc_set_component_variable_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'interior_ring'``    Interior ring variables for
#                                   geometry coordinates
#
#            ``'node_count'``       Node count variables for geometry
#                                   coordinates
#
#            ``'part_node_count'``  Part node count variables for
#                                   geometry coordinates
#
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#
#            ``'list'``             List variables for compression by
#                                   gathering
#            =====================  ===================================
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_clear_component_variable_groups('interior_ring')
#
#        '''
#        if component in ('count', 'index', 'list'):
#            variables = self._get_data_compression_variables(component)
#        elif component in ('interior_ring', 'node_count', 'part_node_count'):
#            variables = self._get_coordinate_geometry_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_clear_variable_groups()
#
#    def nc_set_component_dimension(self, component, value):
#        '''Set the netCDF dimension name for all components of the given type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_del_component_dimension`,
#                 `nc_set_component_dimension_groups`,
#                 `nc_clear_component_dimension_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'interior_ring'``    Interior ring variables for
#                                   geometry coordinates
#
#            ``'part_node_count'``  Part node count variables for
#                                   geometry coordinates
#
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#            =====================  ===================================
#
#        value: `str`
#            The netCDF dimension name to be set for each component.
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_set_component_dimension('interior_ring', 'part')
#
#        '''
#        if component in ('count', 'index'):
#            variables = self._get_data_compression_variables(component)
#        elif component in ('interior_ring', 'part_node_count'):
#            variables = self._get_coordinate_geometry_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_set_dimension(value)
#
#    def nc_del_component_dimension(self, component):
#        '''Remove the netCDF dimension name for all components of the given
#    type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_set_component_dimension`,
#                 `nc_set_component_dimension_groups`,
#                 `nc_clear_component_dimension_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'interior_ring'``    Interior ring variables for
#                                   geometry coordinates
#
#            ``'part_node_count'``  Part node count variables for
#                                   geometry coordinates
#
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#            =====================  ===================================
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_del_component_dimension('interior_ring')
#
#        '''
#        if component in ('count', 'index'):
#            variables = self._get_data_compression_variables(component)
#        elif component in ('interior_ring', 'part_node_count'):
#            variables = self._get_coordinate_geometry_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_del_dimension(None)
#
#    def nc_set_component_dimension_groups(self, component, groups):
#        '''Set the netCDF dimension groups hierarchy for all components of the
#    given type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_del_component_dimension`,
#                 `nc_set_component_dimension`,
#                 `nc_clear_component_dimension_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'interior_ring'``    Interior ring variables for
#                                   geometry coordinates
#
#            ``'part_node_count'``  Part node count variables for
#                                   geometry coordinates
#
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#            =====================  ===================================
#
#        groups: sequence of `str`
#            The new group structure for each component.
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_set_component_dimension_groups('interior_ring', ['forecast'])
#
#        '''
#        if component in ('count', 'index'):
#            variables = self._get_data_compression_variables(component)
#        elif component in ('interior_ring', 'part_node_count'):
#            variables = self._get_coordinate_geometry_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_set_dimension_groups(groups)
#
#    def nc_clear_component_dimension_groups(self, component):
#        '''Remove the netCDF dimension groups hierarchy for all components of
#    the given type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_del_component_dimension`,
#                 `nc_set_component_dimension`,
#                 `nc_set_component_dimension_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'interior_ring'``    Interior ring variables for
#                                   geometry coordinates
#
#            ``'part_node_count'``  Part node count variables for
#                                   geometry coordinates
#
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#            =====================  ===================================
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_clear_component_dimension_groups('interior_ring')
#
#        '''
#        if component in ('count', 'index'):
#            variables = self._get_data_compression_variables(component)
#        elif component in ('interior_ring', 'part_node_count'):
#            variables = self._get_coordinate_geometry_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_clear_dimension_groups()
#
#    def nc_set_component_sample_dimension(self, component, value):
#        '''Set the netCDF sample dimension name for all components of the
#    given type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_del_component_sample_dimension`,
#                 `nc_set_component_sample_dimension_groups`,
#                 `nc_clear_component_sample_dimension_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#            =====================  ===================================
#
#        value: `str`
#            The netCDF sample_dimension name to be set for each
#            component.
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_set_component_sample_dimension('count', 'obs')
#
#        '''
#        if component in ('count', 'index'):
#            variables = self._get_data_compression_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_set_sample_dimension(value)
#
#    def nc_del_component_sample_dimension(self, component):
#        '''Remove the netCDF sample dimension name for all components of the
#    given type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_set_component_sample_dimension`,
#                 `nc_set_component_sample_dimension_groups`,
#                 `nc_clear_component_sample_dimension_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#            =====================  ===================================
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_del_component_sample_dimension('count')
#
#        '''
#        if component in ('count', 'index'):
#            variables = self._get_data_compression_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_del_sample_dimension(None)
#
#    def nc_set_component_sample_dimension_groups(self, component, groups):
#        '''Set the netCDF sample dimension groups hierarchy for all components
#    of the given type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_del_component_sample_dimension`,
#                 `nc_set_component_sample_dimension`,
#                 `nc_clear_component_sample_dimension_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#            =====================  ===================================
#
#        groups: sequence of `str`
#            The new group structure for each component.
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_set_component_sample_dimension_groups('count', ['forecast'])
#
#        '''
#        if component in ('count', 'index'):
#            variables = self._get_data_compression_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_set_sample_dimension_groups(groups)
#
#    def nc_clear_component_sample_dimension_groups(self, component):
#        '''Remove the netCDF sample dimension groups hierarchy for all
#    components of the given type.
#
#    Some components exist within multiple constructs, but when written
#    to a netCDF dataset the netCDF names associated with such
#    components will be arbitrarily taken from one of them. The netCDF
#    names can be set on all such occurences individually, or
#    preferably by using this method to ensure consistency across all
#    such components.
#
#    .. versionadded:: (cfdm) 1.8.6.0
#
#    .. seealso:: `nc_del_component_sample_dimension`,
#                 `nc_set_component_sample_dimension`,
#                 `nc_set_component_sample_dimension_groups`
#
#    :Parameters:
#
#        component: `str`
#            Specify the component type. One of:
#
#            =====================  ===================================
#            *component*            Description
#            =====================  ===================================
#            ``'count'``            Count variables for contiguous
#                                   ragged arrays
#
#            ``'index'``            Index variables for indexed
#                                   ragged arrays
#            =====================  ===================================
#
#    :Returns:
#
#        `None`
#
#    **Examples:**
#
#    >>> f.nc_del_component_sample_dimension_groups('count')
#
#        '''
#        if component in ('count', 'index'):
#            variables = self._get_data_compression_variables(component)
#        else:
#            raise ValueError("Invalid component: {!r}".format(component))
#
#        for v in variables:
#            v.nc_clear_sample_dimension_groups()

# --- End: class
