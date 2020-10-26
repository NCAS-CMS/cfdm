import logging
import re

from ..decorators import (
    _manage_log_level_via_verbosity,
)

logger = logging.getLogger(__name__)


class FieldDomain:
    '''Mixin class for methods common to both field and domain constructs

    .. versionadded:: (cfdm) 1.9.0.0

    '''
    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _apply_masking_constructs(self):
        '''Apply masking to metadata constructs in-place as, defined by the CF
    conventions.

    Masking is applied to all metadata constructs with data.

    See `Field.apply_masking` or `Domain.apply_masking` for details

    .. versionadded:: (cfdm) 1.9.0.0

    :Returns:

        `None`

        '''
        # Apply masking to the metadata constructs
        for c in self.constructs.filter_by_data().values():
            c.apply_masking(inplace=True)

    def _get_data_compression_variables(self, component):
        '''TODO

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
    def construct(self, identity=None, default=ValueError()):
        '''Return a metadata construct, or its key.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `construct_key`, `constructs`,
                 `Constructs.filter_by_identity`, `Constructs.value`

    :Parameters:

        identity: optional
            Select the construct by one of

            * A metadata construct identity.

              {{construct selection identity}}

            * The key of a metadata construct

            * `None`. This is the default, which selects the metadata
              construct when there is only one of them.

            *Parameter example:*
              ``identity='latitude'``

            *Parameter example:*
              ``identity='long_name=Cell Area'``

            *Parameter example:*
              ``identity='cellmeasure1'``

            *Parameter example:*
              ``identity='measure:area'``

            *Parameter example:*
              ``identity=re.compile('^lat')``

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
        if identity is None:            
            c = self.constructs
        else:
            c = self.constructs.filter_by_identity(identity)

        return c.value(default=default)

    def construct_key(self, identity=None, default=ValueError()):
        '''Return the key of a metadata construct.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `construct`, `constructs`,
                 `Constructs.filter_by_identity`, `Constructs.key`

    :Parameters:

        identity: optional
            Select the construct by one of

            * A metadata construct identity.

              {{construct selection identity}}

            * The key of a metadata construct

            * `None`. This is the default, which selects the metadata
              construct when there is only one of them.

            *Parameter example:*
              ``identity='latitude'``

            *Parameter example:*
              ``identity='long_name=Cell Area'``

            *Parameter example:*
              ``identity='cellmeasure1'``

            *Parameter example:*
              ``identity='measure:area'``

            *Parameter example:*
              ``identity=re.compile('^lat')``

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
        if identity is None:            
            c = self.constructs
        else:
            c = self.constructs.filter_by_identity(identity)
            
        return c.key(default=default)

    def domain_axis_key(self, identity=None, default=ValueError()):
        '''Return the key of the domain axis construct that is spanned by 1-d
    coordinate constructs.

    :Parameters:

        identity: optional
            Select the domain axis construct by one of:

            * An identity or key of a 1-d dimension or auxiliary
              coordinate construct that whose data spans the domain
              axis construct.

              {{construct selection identity}}
       
            * `None`. This is the default, which selects the dimension
              or 1-d auxiliary coordinate construct when there is only
              one of them.

            *Parameter example:*
              ``identity='time'``

            *Parameter example:*
              ``identity='ncvar%y'``

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

    @_manage_log_level_via_verbosity
    def equals(self, other, rtol=None, atol=None, verbose=None,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_compression=True,
               ignore_type=False):
        '''Whether two constructs are the same.

    Equality is strict by default. This means that for two constructs
    to be considered equal they must have corresponding metadata
    constructs and for each pair of constructs:

    * the same descriptive properties must be present, with the same
      values and data types, and vector-valued properties must also
      have same the size and be element-wise equal (see the
      *ignore_properties* and *ignore_data_type* parameters), and

    ..

    * if there are data arrays then they must have same shape and data
      type, the same missing data mask, and be element-wise equal (see
      the *ignore_data_type* parameter).

    {{equals tolerance}}

    {{equals compression}}

    Any type of object may be tested but, in general, equality is only
    possible with another field construct, or a subclass of one. See
    the *ignore_type* parameter.

    {{equals netCDF}}

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        other:
            The object to compare for equality.

        {{atol: number, optional}}

        {{rtol: number, optional}}

        {{ignore_fill_value: `bool`, optional}}

        ignore_properties: sequence of `str`, optional
            The names of properties of the construct (not the metadata
            constructs) to omit from the comparison. Note that the
            ``Conventions`` property is always omitted.

        {{ignore_data_type: `bool`, optional}}

        {{ignore_compression: `bool`, optional}}

        {{ignore_type: `bool`, optional}}

        {{verbose: `int` or `str` or `None`, optional}}

    :Returns:

        `bool`
            Whether the two constructs are equal.

    **Examples:**

    >>> f.equals(f)
    True
    >>> f.equals(f.copy())
    True
    >>> f.equals(f[...])
    True
    >>> f.equals('a string, not a construct')
    False

    >>> g = f.copy()
    >>> g.set_property('foo', 'bar')
    >>> f.equals(g)
    False
    >>> f.equals(g, verbose=3)
    {{class}}: Non-common property name: foo
    {{class}}: Different properties
    False

        '''
        # ------------------------------------------------------------
        # Check the properties and data
        # ------------------------------------------------------------
        ignore_properties = tuple(ignore_properties) + ('Conventions',)

        if not super().equals(
                other,
                rtol=rtol, atol=atol, verbose=verbose,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_properties=ignore_properties,
                ignore_compression=ignore_compression,
                ignore_type=ignore_type):
            return False

        # ------------------------------------------------------------
        # Check the constructs
        # ------------------------------------------------------------
        if not self._equals(self.constructs, other.constructs,
                            rtol=rtol, atol=atol, verbose=verbose,
                            ignore_data_type=ignore_data_type,
                            ignore_fill_value=ignore_fill_value,
                            ignore_compression=ignore_compression,
                            _ignore_type=False):
            logger.info(
                "{0}: Different metadata constructs".format(
                    self.__class__.__name__)
            )
            return False

        return True

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

# --- End: class
