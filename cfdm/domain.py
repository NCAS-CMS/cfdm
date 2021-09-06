import logging

from . import Constructs, core, mixin
from .decorators import (
    _display_or_return,
    _inplace_enabled,
    _inplace_enabled_define_and_cleanup,
)

logger = logging.getLogger(__name__)


class Domain(
    mixin.FieldDomain,
    mixin.NetCDFVariable,
    mixin.NetCDFGeometry,
    mixin.NetCDFGlobalAttributes,
    mixin.NetCDFGroupAttributes,
    mixin.NetCDFComponents,
    mixin.NetCDFUnreferenced,
    mixin.Properties,
    core.Domain,
):
    """A domain construct of the CF data model.

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

    {{netCDF variable}}

    {{netCDF global attributes}}

    {{netCDF variable group}}

    {{netCDF group attributes}}

    {{netCDF geometry group}}

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

    """

    def __new__(cls, *args, **kwargs):
        """This must be overridden in subclasses.

        .. versionadded:: (cfdm) 1.7.0

        """
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        return instance

    def __init__(
        self, properties=None, source=None, copy=True, _use_data=True
    ):
        """**Initialisation**

        :Parameters:

            {{init properties: `dict`, optional}}

                *Parameter example:*
                   ``properties={'long_name': 'Domain for model'}``

            source: optional
                Initialise the metadata constructs from those of
                *source*.

                {{init source}}

                A new domain may also be instantiated with the
                `fromconstructs` class method.

            {{init copy: `bool`, optional}}

        """
        super().__init__(
            properties=properties,
            source=source,
            copy=copy,
            _use_data=_use_data,
        )

        self._initialise_netcdf(source)

        self._set_dataset_compliance(self.dataset_compliance(), copy=True)

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        """
        shape = sorted(
            [
                domain_axis.get_size(None)
                for domain_axis in self.domain_axes(todict=True).values()
            ]
        )
        shape = str(shape)
        shape = shape[1:-1]

        return f"<{self.__class__.__name__}: {self._one_line_description()}>"

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        """

        def _print_item(self, cid, variable, axes):
            """Private function called by __str__."""
            x = [variable.identity(default=f"key%{cid}")]

            if variable.has_data():
                shape = [axis_names[axis] for axis in axes]
                shape = str(tuple(shape)).replace("'", "")
                shape = shape.replace(",)", ")")
                x.append(shape)
            elif (
                variable.construct_type
                in ("auxiliary_coordinate", "domain_ancillary")
                and variable.has_bounds()
                and variable.bounds.has_data()
            ):
                # Construct has no data but it does have bounds
                shape = [axis_names[axis] for axis in axes]
                shape.extend(
                    [str(n) for n in variable.bounds.data.shape[len(axes) :]]
                )
                shape = str(tuple(shape)).replace("'", "")
                shape = shape.replace(",)", ")")
                x.append(shape)
            elif (
                hasattr(variable, "nc_get_external")
                and variable.nc_get_external()
            ):
                ncvar = variable.nc_get_variable(None)
                if ncvar is not None:
                    x.append(f" (external variable: ncvar%{ncvar})")
                else:
                    x.append(" (external variable)")

            if variable.has_data():
                x.append(f" = {variable.data}")
            elif (
                variable.construct_type
                in ("auxiliary_coordinate", "domain_ancillary")
                and variable.has_bounds()
                and variable.bounds.has_data()
            ):
                # Construct has no data but it does have bounds data
                x.append(f" = {variable.bounds.data}")

            return "".join(x)

        string = []

        axis_names = self._unique_domain_axis_identities()

        construct_data_axes = self.constructs.data_axes()

        x = []
        dimension_coordinates = self.dimension_coordinates(todict=True)
        for axis_cid in sorted(self.domain_axes(todict=True)):
            for cid, dim in dimension_coordinates.items():
                if construct_data_axes[cid] == (axis_cid,):
                    name = dim.identity(default=f"key%{0}")
                    y = f"{name}({dim.get_data().size})"
                    if y != axis_names[axis_cid]:
                        y = f"{name}({axis_names[axis_cid]})"
                    if dim.has_data():
                        y += f" = {dim.get_data()}"

                    x.append(y)

        if x:
            x = "\n                : ".join(x)
            string.append(f"Dimension coords: {x}")

        # Auxiliary coordinates
        x = [
            _print_item(self, cid, v, construct_data_axes[cid])
            for cid, v in sorted(
                self.auxiliary_coordinates(todict=True).items()
            )
        ]
        if x:
            x = "\n                : ".join(x)
            string.append(f"Auxiliary coords: {x}")

        # Cell measures
        x = [
            _print_item(self, cid, v, construct_data_axes[cid])
            for cid, v in sorted(self.cell_measures(todict=True).items())
        ]
        if x:
            x = "\n                : ".join(x)
            string.append(f"Cell measures   : {x}")

        # Coordinate references
        x = sorted(
            [
                str(ref)
                for ref in list(
                    self.coordinate_references(todict=True).values()
                )
            ]
        )
        if x:
            x = "\n                : ".join(x)
            string.append(f"Coord references: {x}")

        # Domain ancillary variables
        x = [
            _print_item(self, cid, anc, construct_data_axes[cid])
            for cid, anc in sorted(
                self.domain_ancillaries(todict=True).items()
            )
        ]
        if x:
            x = "\n                : ".join(x)
            string.append(f"Domain ancils   : {x}")

        return "\n".join(string)

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    @_display_or_return
    def _dump_axes(self, axis_names, display=True, _level=0):
        """Returns a string description of the field's domain axes.

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

            _level: `int`, optional

        :Returns:

            `str`
                A string containing the description.

        """
        indent1 = "    " * _level

        w = sorted(
            [
                f"{indent1}Domain Axis: {axis_names[axis]}"
                for axis in self.domain_axes(todict=True)
            ]
        )

        return "\n".join(w)

    def _one_line_description(self, axis_names_sizes=None):
        """Return a one-line description of the domain.

        :Returns:

            `str`
                The description.

        """
        if axis_names_sizes is None:
            axis_names_sizes = self._unique_domain_axis_identities()

        axis_names = ", ".join(sorted(axis_names_sizes.values()))

        return f"{self.identity('')}{{{axis_names}}}"

    @_inplace_enabled(default=False)
    def apply_masking(self, inplace=False):
        """Apply masking as defined by the CF conventions.

        Masking is applied to all metadata constructs with data.

        Masking is applied according to any of the following criteria
        that are applicable:

        * where data elements are equal to the value of the
          ``missing_value`` property;

        * where data elements are equal to the value of the
          ``_FillValue`` property;

        * where data elements are strictly less than the value of the
          ``valid_min`` property;

        * where data elements are strictly greater than the value of
          the ``valid_max`` property;

        * where data elements are within the inclusive range specified
          by the two values of ``valid_range`` property.

        If any of the above properties have not been set the no
        masking is applied for that method.

        Elements that are already masked remain so.

        .. note:: If using the `apply_masking` method on a construct
                  that has been read from a dataset with the
                  ``mask=False`` parameter to the `read` function,
                  then the mask defined in the dataset can only be
                  recreated if the ``missing_value``, ``_FillValue``,
                  ``valid_min``, ``valid_max``, and ``valid_range``
                  properties have not been updated.

        .. versionadded:: (cfdm) 1.8.9.0

        .. seealso:: `{{package}}.Data.apply_masking`, `read`, `write`

        :Parameters:

            {{inplace: `bool`, optional}}

        :Returns:

            `Domain` or `None`
                A new domain construct with masked values, or `None`
                if the operation was in-place.

        **Examples:**

        >>> d = cfdm.example_field(0).domain
        >>> x = d.construct('longitude')
        >>> x.data[[0, -1]] = cfdm.masked
        >>> print(x.data.array)
        [-- 67.5 112.5 157.5 202.5 247.5 292.5 --]
        >>> cfdm.write(d, 'masked.nc')
        >>> no_mask = {{package}}.read('masked.nc', domain=True, mask=False)[0]
        >>> no_mask_x = no_mask.construct('longitude')
        >>> print(no_mask_x.data.array)
        [9.96920997e+36 6.75000000e+01 1.12500000e+02 1.57500000e+02
         2.02500000e+02 2.47500000e+02 2.92500000e+02 9.96920997e+36]
        >>> masked = no_mask.apply_masking()
        >>> masked_x = masked.construct('longitude')
        >>> print(masked_x.data.array)
        [-- 67.5 112.5 157.5 202.5 247.5

        """
        d = _inplace_enabled_define_and_cleanup(self)

        # Apply masking to the metadata constructs
        d._apply_masking_constructs()

        return d

    def climatological_time_axes(self):
        """Return all axes which are climatological time axes.

        This is ascertained by inspecting the values returned by each
        coordinate construct's `is_climatology` method.

        .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `set`
                The keys of the domain axis constructs that are
                climatological time axes.

        **Examples:**

        >>> d = cfdm.example_field(0)
        >>> d.climatological_time_axes()
        set()

        """
        data_axes = self.constructs.data_axes()

        out = []

        for ckey, c in self.coordinates(todict=True).items():
            if not c.is_climatology():
                continue

            out.extend(data_axes.get(ckey, ()))

        return set(out)

    def creation_commands(
        self,
        representative_data=False,
        namespace=None,
        indent=0,
        string=True,
        name="domain",
        data_name="data",
        header=True,
        _domain=True,
    ):
        """Return the commands that would create the domain construct.

        **Construct keys**

        The *key* parameter of the output `set_construct` commands is
        utilised in order minimise the number of commands needed to
        implement cross-referencing between constructs (e.g. between a
        coordinate reference construct and coordinate
        constructs). This is usually not necessary when building
        domain constructs, as by default the `set_construct` method
        returns a unique construct key for the construct being set.

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
            data = <{{repr}}Data(5): [-75.0, ..., 75.0] degrees_north>  # Representative data
            c.set_data(data)
            b = Bounds()
            b.nc_set_variable('lat_bnds')
            data = <{{repr}}Data(5, 2): [[-90.0, ..., 90.0]] degrees_north>  # Representative data
            b.set_data(data)
            c.set_bounds(b)
            domain.set_construct(c, axes=('domainaxis0',), key='dimensioncoordinate0', copy=False)
            c = DimensionCoordinate()
            c.set_properties({'units': 'degrees_east', 'standard_name': 'longitude'})
            c.nc_set_variable('lon')
            data = <{{repr}}Data(8): [22.5, ..., 337.5] degrees_east>  # Representative data
            c.set_data(data)
            b = Bounds()
            b.nc_set_variable('lon_bnds')
            data = <{{repr}}Data(8, 2): [[0.0, ..., 360.0]] degrees_east>  # Representative data
            b.set_data(data)
            c.set_bounds(b)
            domain.set_construct(c, axes=('domainaxis1',), key='dimensioncoordinate1', copy=False)
            c = DimensionCoordinate()
            c.set_properties({'units': 'days since 2018-12-01', 'standard_name': 'time'})
            c.nc_set_variable('time')
            data = <{{repr}}Data(1): [2019-01-01 00:00:00]>  # Representative data
            c.set_data(data)
            domain.set_construct(c, axes=('domainaxis2',), key='dimensioncoordinate2', copy=False)

        """
        if name in ("b", "c", "mask", "i"):
            raise ValueError(
                f"The 'name' parameter can not have the value {name!r}"
            )

        if name == data_name:
            raise ValueError(
                "The 'name' parameter can not have the same value as "
                f"the 'data_name' parameter: {name!r}"
            )

        namespace0 = namespace
        if namespace is None:
            namespace = self._package() + "."
        elif namespace and not namespace.endswith("."):
            namespace += "."

        if _domain:
            out = super().creation_commands(
                indent=indent,
                namespace=namespace,
                string=False,
                name=name,
                header=header,
            )

            nc_global_attributes = self.nc_global_attributes()
            if nc_global_attributes:
                if header:
                    out.append("#")
                    out.append("# netCDF global attributes")

                out.append(
                    f"{name}.nc_set_global_attributes("
                    f"{nc_global_attributes!r})"
                )
        else:
            out = []

        # Domain axis constructs
        for key, c in self.domain_axes(todict=True).items():
            out.extend(
                c.creation_commands(
                    indent=0,
                    string=False,
                    namespace=namespace0,
                    name="c",
                    header=header,
                )
            )
            out.append(f"{name}.set_construct(c, key={key!r}, copy=False)")

        # Metadata constructs with data
        for key, c in self.constructs.filter_by_type(
            "dimension_coordinate",
            "auxiliary_coordinate",
            "cell_measure",
            "domain_ancillary",
        ).items():
            out.extend(
                c.creation_commands(
                    representative_data=representative_data,
                    string=False,
                    indent=0,
                    namespace=namespace0,
                    name="c",
                    data_name=data_name,
                    header=header,
                )
            )
            out.append(
                f"{name}.set_construct("
                f"c, axes={self.get_data_axes(key)}, key={key!r}, copy=False)"
            )

        # Coordinate reference constructs
        for key, c in self.coordinate_references(todict=True).items():
            out.extend(
                c.creation_commands(
                    namespace=namespace0,
                    indent=0,
                    string=False,
                    name="c",
                    header=header,
                )
            )
            out.append(f"{name}.set_construct(c)")

        if string:
            indent = " " * indent
            out[0] = indent + out[0]
            out = ("\n" + indent).join(out)

        return out

    @_display_or_return
    def dump(
        self,
        display=True,
        _omit_properties=(),
        _prefix="",
        _title=None,
        _create_title=True,
        _level=0,
    ):
        """A full description of the domain construct.

        Returns a description of all properties, including those of
        metadata constructs and their components, and provides
        selected values of all data arrays.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        indent = "    "
        indent0 = indent * _level

        if _create_title:
            if _title is None:
                ncvar = self.nc_get_variable(None)
                _title = self.identity(default=None)
                if ncvar is not None:
                    if _title is None:
                        _title = f"ncvar%{ncvar}"
                    else:
                        _title += f" (ncvar%{ncvar})"

                if _title is None:
                    _title = ""

                _title = f"{self.__class__.__name__}: {_title}"

            line = f"{indent0}{''.ljust(len(_title), '-')}"

            # Title
            string = [line, indent0 + _title, line]

            properties = super().dump(
                display=False,
                _create_title=False,
                _omit_properties=_omit_properties,
                _prefix=_prefix,
                _title=_title,
                _level=_level - 1,
            )
            string.append(properties)
            string.append("")
        else:
            string = []

        axis_to_name = self._unique_domain_axis_identities()

        construct_name = self._unique_construct_names()

        construct_data_axes = self.constructs.data_axes()

        # Domain axes
        axes = self._dump_axes(axis_to_name, display=False, _level=_level)
        if axes:
            string.append(axes)

        # Dimension coordinates
        dimension_coordinates = self.dimension_coordinates(todict=True)
        for cid, value in sorted(dimension_coordinates.items()):
            string.append("")
            string.append(
                value.dump(
                    display=False,
                    _level=_level,
                    _title=f"Dimension coordinate: {construct_name[cid]}",
                    _axes=construct_data_axes[cid],
                    _axis_names=axis_to_name,
                )
            )

        # Auxiliary coordinates
        auxiliary_coordinates = self.auxiliary_coordinates(todict=True)
        for cid, value in sorted(auxiliary_coordinates.items()):
            string.append("")
            string.append(
                value.dump(
                    display=False,
                    _level=_level,
                    _title=f"Auxiliary coordinate: {construct_name[cid]}",
                    _axes=construct_data_axes[cid],
                    _axis_names=axis_to_name,
                )
            )

        # Domain ancillaries
        for cid, value in sorted(self.domain_ancillaries(todict=True).items()):
            string.append("")
            string.append(
                value.dump(
                    display=False,
                    _level=_level,
                    _title=f"Domain ancillary: {construct_name[cid]}",
                    _axes=construct_data_axes[cid],
                    _axis_names=axis_to_name,
                )
            )

        # Coordinate references
        for cid, value in sorted(
            self.coordinate_references(todict=True).items()
        ):
            string.append("")
            string.append(
                value.dump(
                    display=False,
                    _level=_level,
                    _title=f"Coordinate reference: {construct_name[cid]}",
                    _construct_names=construct_name,
                    _auxiliary_coordinates=tuple(auxiliary_coordinates),
                    _dimension_coordinates=tuple(dimension_coordinates),
                )
            )

        # Cell measures
        for cid, value in sorted(self.cell_measures(todict=True).items()):
            string.append("")
            string.append(
                value.dump(
                    display=False,
                    _key=cid,
                    _level=_level,
                    _title=f"Cell measure: {construct_name[cid]}",
                    _axes=construct_data_axes[cid],
                    _axis_names=axis_to_name,
                )
            )

        string.append("")

        return "\n".join(string)

    def get_filenames(self):
        """Return the file names containing the metadata construct data.

        :Returns:

            `set`
                The file names in normalized, absolute form. If all of
                the data are in memory then an empty `set` is
                returned.

        **Examples:**

        >>> d = {{package}}.example_field(0).domain
        >>> {{package}}.write(d, 'temp_file.nc')
        >>> e = {{package}}.read('temp_file.nc', domain=True)[0]
        >>> e.get_filenames()
        {'temp_file.nc'}

        """
        out = set()

        for c in self.constructs.filter_by_data().values():
            out.update(c.get_filenames())

        return out

    def identity(self, default=""):
        """Return the canonical identity.

        By default the identity is the first found of the following:

        * The ``cf_role`` property, preceded by ``'cf_role='``.
        * The ``long_name`` property, preceded by ``'long_name='``.
        * The netCDF variable name, preceded by ``'ncvar%'``.
        * The value of the *default* parameter.

        .. versionadded:: (cfdm) 1.9.0.0

        .. seealso:: `identities`

        :Parameters:

            default: optional
                If no identity can be found then return the value of
                the default parameter.

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

        """
        for prop in ("cf_role", "long_name"):
            n = self.get_property(prop, None)
            if n is not None:
                return f"{prop}={n}"

        n = self.nc_get_variable(None)
        if n is not None:
            return f"ncvar%{n}"

        return default

    def identities(self):
        """Return all possible identities.

        The identities comprise:

        * The ``cf_role`` property, preceded by ``'cf_role='``.
        * The ``long_name`` property, preceded by ``'long_name='``.
        * All other properties, preceded by the property name and a
          equals e.g. ``'foo=bar'``.
        * The netCDF variable name, preceded by ``'ncvar%'``.

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

        """
        properties = self.properties()
        cf_role = properties.pop("cf_role", None)
        long_name = properties.pop("long_name", None)

        out = []

        if cf_role is not None:
            out.append(f"cf_role={cf_role}")

        if long_name is not None:
            out.append(f"long_name={long_name}")

        out += [
            f"{prop}={value}" for prop, value in sorted(properties.items())
        ]

        n = self.nc_get_variable(None)
        if n is not None:
            out.append(f"ncvar%{n}")

        return out
