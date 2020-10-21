import logging

from . import mixin
from . import core

from . import Constructs

from .decorators import _manage_log_level_via_verbosity


logger = logging.getLogger(__name__)


class Domain(mixin.FieldDomainMixin,
             mixin.NetCDFVariable,
             mixin.NetCDFGeometry,
             mixin.NetCDFGlobalAttributes,
             mixin.NetCDFGroupAttributes,
             mixin.NetCDFComponents,
             mixin.NetCDFUnreferenced,
             mixin.Properties,
             core.Domain):
    '''A domain construct of the CF data model.

    The domain represents a set of discrete "locations" in what
    generally would be a multi-dimensional space, either in the real
    world or in a model's simulated world. The data array elements of
    a field construct correspond to individual location of a domain.

    The domain construct is defined collectively by the following
    constructs of the CF data model: domain axis, dimension
    coordinate, auxiliary coordinate, cell measure, coordinate
    reference, and domain ancillary constructs; as well as properties
    to describe the domain.

    **NetCDF interface**

    The netCDF variable name of the construct may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_del_variable` and
    `nc_has_variable` methods.

    The selection of properties to be written as netCDF global
    attributes may be accessed with the `nc_global_attributes`,
    `nc_clear_global_attributes` and `nc_set_global_attribute`
    methods.

    The netCDF variable group structure may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_variable_groups`,
    `nc_clear_variable_groups` and `nc_set_variable_groups` methods.

    The netCDF group attributes may be accessed with the
    `nc_group_attributes`, `nc_clear_group_attributes`,
    `nc_set_group_attribute` and `nc_set_group_attributes` methods.

    The netCDF geometry variable group structure may be accessed with
    the `nc_set_geometry_variable`, `nc_get_geometry_variable`,
    `nc_geometry_variable_groups`, `nc_clear_variable_groups` and
    `nc_set_geometry_variable_groups` methods.

    Some components exist within multiple constructs, but when written
    to a netCDF dataset the netCDF names associated with such
    components will be arbitrarily taken from one of them. The netCDF
    variable, dimension and sample dimension names and group
    structures for such components may be set or removed consistently
    across all such components with the `nc_del_component_variable`,
    `nc_set_component_variable`, `nc_set_component_variable_groups`,
    `nc_clear_component_variable_groups`,
    `nc_del_component_dimension`, `nc_set_component_dimension`,
    `nc_set_component_dimension_groups`,
    `nc_clear_component_dimension_groups`,
    `nc_del_component_sample_dimension`,
    `nc_set_component_sample_dimension`,
    `nc_set_component_sample_dimension_groups`,
    `nc_clear_component_sample_dimension_groups` methods.

    .. versionadded:: (cfdm) 1.7.0

    '''
    def __new__(cls, *args, **kwargs):
        '''This must be overridden in subclasses.

    .. versionadded:: (cfdm) 1.7.0

        '''
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        return instance

    def __init__(self, properties=None, source=None, copy=True,
                 _use_data=True):
        '''**Initialization**

    :Parameters:

        {{init properties: `dict`, optional}}

            *Parameter example:*
               ``properties={'long_name': 'Domain for model'}``

        source: optional
            Initialize the metadata constructs from those of *source*.

            {{init source}}

            A new domain may also be instantiated with the
            `fromconstructs` class method.

        {{init copy: `bool`, optional}}

        '''
        super().__init__(properties=properties, source=source,
                         copy=copy, _use_data=_use_data)

        self._initialise_netcdf(source)

    def __repr__(self):
        '''Called by the `repr` built-in function.

    x.__repr__() <==> repr(x)

        '''
        shape = sorted([domain_axis.get_size()
                        for domain_axis in list(self.domain_axes.values())])
        shape = str(shape)
        shape = shape[1:-1]

        return '<{0}: {1}>'.format(self.__class__.__name__,
                                   self._one_line_description())

    def __str__(self):
        '''Called by the `str` built-in function.

    x.__str__() <==> str(x)

        '''
        def _print_item(self, cid, variable, axes):
            '''Private function called by __str__

            '''
            x = [variable.identity(default='key%{0}'.format(cid))]

            if variable.has_data():
                shape = [axis_names[axis] for axis in axes]
                shape = str(tuple(shape)).replace("'", "")
                shape = shape.replace(',)', ')')
                x.append(shape)
            elif (variable.construct_type in ('auxiliary_coordinate',
                                              'domain_ancillary')
                  and variable.has_bounds()
                  and variable.bounds.has_data()):
                # Construct has no data but it does have bounds
                shape = [axis_names[axis] for axis in axes]
                shape.extend(
                    [str(n)
                     for n in variable.bounds.data.shape[len(axes):]]
                )
                shape = str(tuple(shape)).replace("'", "")
                shape = shape.replace(',)', ')')
                x.append(shape)
            elif (hasattr(variable, 'nc_get_external')
                  and variable.nc_get_external()):
                ncvar = variable.nc_get_variable(None)
                if ncvar is not None:
                    x.append(' (external variable: ncvar%{})'.format(ncvar))
                else:
                    x.append(' (external variable)')
            # --- End: if

            if variable.has_data():
                x.append(' = {0}'.format(variable.data))
            elif (variable.construct_type in ('auxiliary_coordinate',
                                              'domain_ancillary')
                  and variable.has_bounds()
                  and variable.bounds.has_data()):
                # Construct has no data but it does have bounds data
                x.append(' = {0}'.format(variable.bounds.data))

            return ''.join(x)
        # --- End: def

        string = []

        axis_names = self._unique_domain_axis_identities()

        constructs_data_axes = self.constructs.data_axes()

        x = []
        for axis_cid in sorted(self.domain_axes):
            for cid, dim in list(self.dimension_coordinates.items()):
                if constructs_data_axes[cid] == (axis_cid,):
                    name = dim.identity(default='key%{0}'.format(cid))
                    y = '{0}({1})'.format(name, dim.get_data().size)
                    if y != axis_names[axis_cid]:
                        y = '{0}({1})'.format(name, axis_names[axis_cid])
                    if dim.has_data():
                        y += ' = {0}'.format(dim.get_data())

                    x.append(y)
        # --- End: for
        if x:
            string.append('Dimension coords: {}'.format(
                '\n                : '.join(x))
            )

        # Auxiliary coordinates
        x = [_print_item(self, cid, v, constructs_data_axes[cid])
             for cid, v in sorted(self.auxiliary_coordinates.items())]
        if x:
            string.append('Auxiliary coords: {}'.format(
                '\n                : '.join(x))
            )

        # Cell measures
        x = [_print_item(self, cid, v, constructs_data_axes[cid])
             for cid, v in sorted(self.cell_measures.items())]
        if x:
            string.append('Cell measures   : {}'.format(
                '\n                : '.join(x))
            )

        # Coordinate references
        x = sorted([str(ref)
                    for ref in list(self.coordinate_references.values())])
        if x:
            string.append('Coord references: {}'.format(
                '\n                : '.join(x))
            )

        # Domain ancillary variables
        x = [_print_item(self, cid, anc, constructs_data_axes[cid])
             for cid, anc in sorted(self.domain_ancillaries.items())]
        if x:
            string.append('Domain ancils   : {}'.format(
                '\n                : '.join(x))
            )

        return '\n'.join(string)

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _dump_axes(self, axis_names, display=True, _level=0):
        '''Return a string containing a description of the domain axes of the
    field.

    :Parameters:

        display: `bool`, optional
            If False then return the description as a string. By
            default the description is printed.

        _level: `int`, optional

    :Returns:

        `str`
            A string containing the description.

        '''
        indent1 = '    ' * _level

        axes = self.domain_axes

        w = sorted(["{0}Domain Axis: {1}".format(indent1, axis_names[axis])
                    for axis in axes])

        string = '\n'.join(w)

        if display:
            print(string)  # pragma: no cover
        else:
            return string

    def _one_line_description(self, axis_names_sizes=None):
        '''
        '''
        if axis_names_sizes is None:
            axis_names_sizes = self._unique_domain_axis_identities()

        axis_names = ', '.join(sorted(axis_names_sizes.values()))

        return "{0}{{{1}}}".format(self.identity(''), axis_names)

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def dump(self, display=True, _omit_properties=(), _prefix='',
             _title=None, _create_title=True, _level=0):
        '''A full description of the domain construct.

    Returns a description of all properties, including those of
    metadata constructs and their components, and provides selected
    values of all data arrays.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        display: `bool`, optional
            If False then return the description as a string. By
            default the description is printed.

    :Returns:

        {{returns dump}}

        '''
        indent = '    '
        indent0 = indent * _level
        indent1 = indent0 + indent

        if _create_title:
            if _title is None:
                ncvar = self.nc_get_variable(None)
                _title = self.identity(default=None)
                if ncvar is not None:
                    if _title is None:
                        _title = "ncvar%{0}".format(ncvar)
                    else:
                        _title += " (ncvar%{0})".format(ncvar)
                # --- End: if
                if _title is None:
                    _title = ''

                _title = '{0}: {1}'.format(self.__class__.__name__, _title)

            line = '{0}{1}'.format(indent0, ''.ljust(len(_title), '-'))

            # Title
            string = [
                line,
                indent0 + _title,
                line
            ]

            properties = super().dump(display=False,
                                      _create_title=False,
                                      _omit_properties=_omit_properties,
                                      _prefix=_prefix, _title=_title,
                                      _level=_level-1)
            string.append(properties)
            string.append('')
        else:
            string = []

        axis_to_name = self._unique_domain_axis_identities()

        construct_name = self._unique_construct_names()

        constructs_data_axes = self.constructs.data_axes()

        # Domain axes
        axes = self._dump_axes(axis_to_name, display=False, _level=_level)
        if axes:
            string.append(axes)

        # Dimension coordinates
        for cid, value in sorted(self.dimension_coordinates.items()):
            string.append('')
            string.append(
                value.dump(display=False, _level=_level,
                           _title='Dimension coordinate: {0}'.format(
                               construct_name[cid]),
                           _axes=constructs_data_axes[cid],
                           _axis_names=axis_to_name))

        # Auxiliary coordinates
        for cid, value in sorted(self.auxiliary_coordinates.items()):
            string.append('')
            string.append(
                value.dump(display=False, _level=_level,
                           _title='Auxiliary coordinate: {0}'.format(
                               construct_name[cid]),
                           _axes=constructs_data_axes[cid],
                           _axis_names=axis_to_name))

        # Domain ancillaries
        for cid, value in sorted(self.domain_ancillaries.items()):
            string.append('')
            string.append(value.dump(display=False, _level=_level,
                                     _title='Domain ancillary: {0}'.format(
                                         construct_name[cid]),
                                     _axes=constructs_data_axes[cid],
                                     _axis_names=axis_to_name))

        # Coordinate references
        for cid, value in sorted(self.coordinate_references.items()):
            string.append('')
            string.append(
                value.dump(
                    display=False, _level=_level,
                    _title='Coordinate reference: {0}'.format(
                        construct_name[cid]),
                    _construct_names=construct_name,
                    _auxiliary_coordinates=tuple(self.auxiliary_coordinates),
                    _dimension_coordinates=tuple(self.dimension_coordinates)))

        # Cell measures
        for cid, value in sorted(self.cell_measures.items()):
            string.append('')
            string.append(value.dump(
                display=False, _key=cid,
                _level=_level, _title='Cell measure: {0}'.format(
                    construct_name[cid]),
                _axes=constructs_data_axes[cid],
                _axis_names=axis_to_name))

        string.append('')

        string = '\n'.join(string)

        if display:
            print(string)  # pragma: no cover
        else:
            return string

#    def climatological_time_axes(self):
#        '''Return all axes which are climatological time axes.
#
#    .. versionadded:: (cfdm) 1.9.0.0
#
#    :Returns:
#
#        `set`
#            The set of all domain axes which are climatological time
#            axes. If there are none, this will be an empty set.
#
#    **Examples:**
#
#    TODO
#
#        '''
#        out = []
#
#        for ckey, c in self.constructs.filter_by_type(
#                'dimension_coordinate',
#                'auxiliary_coordinate').items():
#            if not c.is_climatology():
#                continue
#
#            out.extend(self.data_axes().get(ckey, ()))
#
#        return set(out)

    def creation_commands(self, representative_data=False,
                          namespace=None, indent=0, string=True,
                          name='domain', data_name='data',
                          header=True, _domain=True):
        '''Return the commands that would create the domain construct.

    **Construct keys**

    The *key* parameter of the output `set_construct` commands is
    utilised in order minimise the number of commands needed to
    implement cross-referencing between constructs (e.g. between a
    coordinate reference construct and coordinate constructs). This is
    usually not necessary when building domain constructs, as by
    default the `set_construct` method returns a unique construct key
    for the construct being set.

    .. versionadded:: (cfdm) 1.9.0.0

    .. seealso:: `set_construct`,
                 `{{package}}.Data.creation_commands`,
                 `{{package}}.example_field`

    :Parameters:

        {{representative_data: `bool`, optional}}

        {{namespace: `str`, optional}}

        {{indent: `int`, optional}}

        {{string: `bool`, optional}}

        {{header: `bool`, optional}}

    :Returns:

        {{returns creation_commands}}

    **Examples:**

    >>> f = {{package}}.example_field(0)
    >>> d = f.domain
    >>> print(d.creation_commands())
    #
    # domain:
    domain = {{package}}.Domain()
    #
    # domain_axis: ncdim%lat
    c = {{package}}.DomainAxis()
    c.set_size(5)
    c.nc_set_dimension('lat')
    domain.set_construct(c, key='domainaxis0', copy=False)
    #
    # domain_axis: ncdim%lon
    c = {{package}}.DomainAxis()
    c.set_size(8)
    c.nc_set_dimension('lon')
    domain.set_construct(c, key='domainaxis1', copy=False)
    #
    # domain_axis:
    c = {{package}}.DomainAxis()
    c.set_size(1)
    domain.set_construct(c, key='domainaxis2', copy=False)
    #
    # dimension_coordinate: latitude
    c = {{package}}.DimensionCoordinate()
    c.set_properties({'units': 'degrees_north', 'standard_name': 'latitude'})
    c.nc_set_variable('lat')
    data = {{package}}.Data([-75.0, -45.0, 0.0, 45.0, 75.0], units='degrees_north', dtype='f8')
    c.set_data(data)
    b = {{package}}.Bounds()
    b.nc_set_variable('lat_bnds')
    data = {{package}}.Data([[-90.0, -60.0], [-60.0, -30.0], [-30.0, 30.0], [30.0, 60.0], [60.0, 90.0]], units='degrees_north', dtype='f8')
    b.set_data(data)
    c.set_bounds(b)
    domain.set_construct(c, axes=('domainaxis0',), key='dimensioncoordinate0', copy=False)
    #
    # dimension_coordinate: longitude
    c = {{package}}.DimensionCoordinate()
    c.set_properties({'units': 'degrees_east', 'standard_name': 'longitude'})
    c.nc_set_variable('lon')
    data = {{package}}.Data([22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5], units='degrees_east', dtype='f8')
    c.set_data(data)
    b = {{package}}.Bounds()
    b.nc_set_variable('lon_bnds')
    data = {{package}}.Data([[0.0, 45.0], [45.0, 90.0], [90.0, 135.0], [135.0, 180.0], [180.0, 225.0], [225.0, 270.0], [270.0, 315.0], [315.0, 360.0]], units='degrees_east', dtype='f8')
    b.set_data(data)
    c.set_bounds(b)
    domain.set_construct(c, axes=('domainaxis1',), key='dimensioncoordinate1', copy=False)
    #
    # dimension_coordinate: time
    c = {{package}}.DimensionCoordinate()
    c.set_properties({'units': 'days since 2018-12-01', 'standard_name': 'time'})
    c.nc_set_variable('time')
    data = {{package}}.Data([31.0], units='days since 2018-12-01', dtype='f8')
    c.set_data(data)
    domain.set_construct(c, axes=('domainaxis2',), key='dimensioncoordinate2', copy=False)
    >>> print(d.creation_commands(representative_data=True, namespace='',
    ...                           indent=4, header=False))
        domain = Domain()
        c = DomainAxis()
        c.set_size(5)
        c.nc_set_dimension('lat')
        domain.set_construct(c, key='domainaxis0', copy=False)
        c = DomainAxis()
        c.set_size(8)
        c.nc_set_dimension('lon')
        domain.set_construct(c, key='domainaxis1', copy=False)
        c = DomainAxis()
        c.set_size(1)
        domain.set_construct(c, key='domainaxis2', copy=False)
        c = DimensionCoordinate()
        c.set_properties({'units': 'degrees_north', 'standard_name': 'latitude'})
        c.nc_set_variable('lat')
        data = <Data(5): [-75.0, ..., 75.0] degrees_north>  # Representative data
        c.set_data(data)
        b = Bounds()
        b.nc_set_variable('lat_bnds')
        data = <Data(5, 2): [[-90.0, ..., 90.0]] degrees_north>  # Representative data
        b.set_data(data)
        c.set_bounds(b)
        domain.set_construct(c, axes=('domainaxis0',), key='dimensioncoordinate0', copy=False)
        c = DimensionCoordinate()
        c.set_properties({'units': 'degrees_east', 'standard_name': 'longitude'})
        c.nc_set_variable('lon')
        data = <Data(8): [22.5, ..., 337.5] degrees_east>  # Representative data
        c.set_data(data)
        b = Bounds()
        b.nc_set_variable('lon_bnds')
        data = <Data(8, 2): [[0.0, ..., 360.0]] degrees_east>  # Representative data
        b.set_data(data)
        c.set_bounds(b)
        domain.set_construct(c, axes=('domainaxis1',), key='dimensioncoordinate1', copy=False)
        c = DimensionCoordinate()
        c.set_properties({'units': 'days since 2018-12-01', 'standard_name': 'time'})
        c.nc_set_variable('time')
        data = <Data(1): [2019-01-01 00:00:00]>  # Representative data
        c.set_data(data)
        domain.set_construct(c, axes=('domainaxis2',), key='dimensioncoordinate2', copy=False)

        '''
        if name in ('b', 'c', 'mask', 'i'):
            raise ValueError(
                "The 'name' parameter can not have the value {!r}".format(
                    name)
            )

        if name == data_name:
            raise ValueError(
                "The 'name' parameter can not have the same value as "
                "the 'data_name' parameter: {!r}".format(
                    name)
            )

        namespace0 = namespace
        if namespace is None:
            namespace = self._package() + '.'
        elif namespace and not namespace.endswith('.'):
            namespace += '.'

        if _domain:
            out = super().creation_commands(
                indent=indent, namespace=namespace, string=False,
                name=name, header=header
            )

            nc_global_attributes = self.nc_global_attributes()
            if nc_global_attributes:
                if header:
                    out.append('#')
                    out.append('# netCDF global attributes')

                out.append(
                    "{}.nc_set_global_attributes({!r})".format(
                        name, nc_global_attributes)
                )
        else:
            out = []

        # Domain axis constructs
        for key, c in self.domain_axes.items():
            out.extend(
                c.creation_commands(
                    indent=0, string=False,
                    namespace=namespace0, name='c',
                    header=header)
            )
            out.append(
                "{}.set_construct(c, key={!r}, copy=False)".format(
                    name, key)
            )

        # Metadata constructs with data
        for key, c in self.constructs.filter_by_type(
                'dimension_coordinate',
                'auxiliary_coordinate',
                'cell_measure',
                'domain_ancillary').items():
            out.extend(
                c.creation_commands(
                    representative_data=representative_data, string=False,
                    indent=0, namespace=namespace0, name='c',
                    data_name=data_name,
                    header=header)
            )
            out.append(
                "{}.set_construct(c, axes={}, key={!r}, copy=False)".format(
                    name, self.get_data_axes(key), key)
            )

        # Coordinate reference constructs
        for key, c in self.coordinate_references.items():
            out.extend(
                c.creation_commands(
                    namespace=namespace0,
                    indent=0, string=False,
                    name='c',
                    header=header)
            )
            out.append("{}.set_construct(c)".format(name))

        if string:
            indent = ' ' * indent
            out[0] = indent + out[0]
            out = ('\n' + indent).join(out)

        return out

    @_manage_log_level_via_verbosity
    def equals(self, other, rtol=None, atol=None, verbose=None,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_compression=True, ignore_properties=(),
               ignore_type=False):
        '''Whether two domains are the same.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        other:
            The object to compare for equality.

        {[atol: number, optional}}

        {{rtol: number, optional}}

        ignore_fill_value: `bool`, optional
            If True then the ``_FillValue`` and ``missing_value``
            properties are omitted from the comparison for the
            metadata constructs.

        ignore_properties: sequence of `str`, optional
            The names of properties of the domain construct (not the
            metadata constructs) to omit from the comparison. Note
            that the ``Conventions`` property is always omitted.

        {{ignore_compression: `bool`, optional}}

        {{ignore_data_type: `bool`, optional}}

        {{ignore_type: `bool`, optional}}

        {{verbose: `int` or `str` or `None`, optional}}

    :Returns:

        `bool`

    **Examples:**

    >>> d.equals(d)
    True
    >>> d.equals(d.copy())
    True
    >>> d.equals('not a domain')
    False

        '''
        # ------------------------------------------------------------
        # Check the properties
        # ------------------------------------------------------------
        ignore_properties = tuple(ignore_properties) + ('Conventions',)

        if not super().equals(
                other,
                rtol=rtol, atol=atol, verbose=verbose,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_properties=ignore_properties,
                ignore_type=ignore_type):
            return False

#        pp = super()._equals_preprocess(other, verbose=verbose,
#                                        ignore_type=ignore_type)
#        if pp is True or pp is False:
#            return pp
#
#        other = pp

        # ------------------------------------------------------------
        # Check the constructs
        # ------------------------------------------------------------
        if not self._equals(self.constructs, other.constructs,
                            rtol=rtol, atol=atol, verbose=verbose,
                            ignore_data_type=ignore_data_type,
                            ignore_fill_value=ignore_fill_value,
                            ignore_compression=ignore_compression):
            logger.info(
                "{0}: Different metadata constructs".format(
                    self.__class__.__name__)
            )
            return False

        return True

    def get_filenames(self):
        '''Return TODO the name of the file or files containing the data of
    metadata constructs.

    The names of the file or files containing the data of metadata
    constructs are also returned.

    :Returns:

        `set`
            The file names in normalized, absolute form. If all of the
            data are in memory then an empty `set` is returned.

    **Examples:**

    >>> f = {{package}}.example_field(0)
    >>> {{package}}.write(f, 'temp_file.nc')
    >>> g = {{package}}.read('temp_file.nc')[0]
    >>> g.get_filenames()
    {'temp_file.nc'}

        '''
        out = set()

        for c in self.constructs.filter_by_data().values():
            out.update(c.get_filenames())

        return out

    def identity(self, default=''):
        '''Return the canonical identity.

    By default the identity is the first found of the following:

    * The ``cf_role`` property, preceeded by ``'cf_role='``.
    * The ``long_name`` property, preceeded by ``'long_name='``.
    * The netCDF variable name, preceeded by ``'ncvar%'``.
    * The value of the *default* parameter.

    .. versionadded:: (cfdm) 1.9.0.0

    .. seealso:: `identities`

    :Parameters:

        default: optional
            If no identity can be found then return the value of the
            default parameter.

    :Returns:

            The identity.

    **Examples:**

    >>> d = {{package}}.Domain()
    >>> d.set_properties({'foo': 'bar',
    ...                   'long_name': 'Domain for model'})
    >>> d.nc_set_variable('dom1')
    >>> d.identity()
    'long_name=Domain for model'
    >>> d.del_property('long_name')
    'long_name=Domain for model'
    >>> d.identity(default='no identity')
    'ncvar%dom1'
    >>> d.identity()
    'ncvar%dom1'
    >>> d.nc_del_variable()
    'dom1'
    >>> d.identity()
    ''
    >>> d.identity(default='no identity')
    'no identity'

        '''
        for prop in ('cf_role', 'long_name'):
            n = self.get_property(prop, None)
            if n is not None:
                return '{0}={1}'.format(prop, n)
        # --- End: for

        n = self.nc_get_variable(None)
        if n is not None:
            return 'ncvar%{0}'.format(n)

        return default

    def identities(self):
        '''Return all possible identities.

    The identities comprise:

    * The ``cf_role`` property, preceeded by ``'cf_role='``.
    * The ``long_name`` property, preceeded by ``'long_name='``.
    * All other properties, preceeded by the property name and a
      equals e.g. ``'foo=bar'``.
    * The netCDF variable name, preceeded by ``'ncvar%'``.

    .. versionadded:: (cfdm) 1.9.0.0

    .. seealso:: `identity`

    :Returns:

        `list`
            The identities.

    **Examples:**

    >>> d = {{package}}.Domain()
    >>> d.set_properties({'foo': 'bar',
    ...                   'long_name': 'Domain for model'})
    >>> d.nc_set_variable('dom1')
    >>> d.identities()
    ['long_name=Domain for model', 'foo=bar', 'ncvar%dom1']

        '''
        properties = self.properties()
        cf_role = properties.pop('cf_role', None)
        long_name = properties.pop('long_name', None)

        out = []

        if cf_role is not None:
            out.append('cf_role={}'.format(cf_role))

        if long_name is not None:
            out.append('long_name={}'.format(long_name))

        out += ['{0}={1}'.format(prop, value)
                for prop, value in sorted(properties.items())]

        n = self.nc_get_variable(None)
        if n is not None:
            out.append('ncvar%{0}'.format(n))

        return out

# --- End: class
