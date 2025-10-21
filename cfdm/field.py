import logging

import numpy as np

from . import (
    AuxiliaryCoordinate,
    Constructs,
    Count,
    Domain,
    DomainAxis,
    Index,
    List,
    Quantization,
    core,
    mixin,
)
from .data import (
    GatheredArray,
    RaggedContiguousArray,
    RaggedIndexedArray,
    RaggedIndexedContiguousArray,
)
from .decorators import (
    _display_or_return,
    _inplace_enabled,
    _inplace_enabled_define_and_cleanup,
    _manage_log_level_via_verbosity,
    _test_decorator_args,
)
from .functions import _DEPRECATION_ERROR_METHOD, parse_indices

logger = logging.getLogger(__name__)


class Field(
    mixin.QuantizationMixin,
    mixin.NetCDFVariable,
    mixin.NetCDFGeometry,
    mixin.NetCDFGlobalAttributes,
    mixin.NetCDFGroupAttributes,
    mixin.NetCDFComponents,
    mixin.NetCDFUnreferenced,
    mixin.FieldDomain,
    mixin.PropertiesData,
    mixin.Files,
    core.Field,
):
    """A field construct of the CF data model.

    The field construct is central to the CF data model, and includes
    all the other constructs. A field corresponds to a CF-netCDF data
    variable with all of its metadata. All CF-netCDF elements are
    mapped to a field construct or some element of the CF field
    construct. The field construct contains all the data and metadata
    which can be extracted from the file using the CF conventions.

    The field construct consists of a data array and the definition of
    its domain (that describes the locations of each cell of the data
    array), field ancillary constructs containing metadata defined
    over the same domain, and cell method constructs to describe how
    the cell values represent the variation of the physical quantity
    within the cells of the domain. The domain is defined collectively
    by the following constructs of the CF data model: domain axis,
    dimension coordinate, auxiliary coordinate, cell measure,
    coordinate reference and domain ancillary constructs.

    The field construct also has optional properties to describe
    aspects of the data that are independent of the domain. These
    correspond to some netCDF attributes of variables (e.g. units,
    long_name and standard_name), and some netCDF global file
    attributes (e.g. history and institution).

    **NetCDF interface**

    {{netCDF variable}}

    {{netCDF global attributes}}

    {{netCDF group attributes}}

    {{netCDF geometry group}}

    {{netCDF dataset chunks}}

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

    CF-compliance issues for field constructs read from a netCDF
    dataset may be accessed with the `dataset_compliance` method.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __new__(cls, *args, **kwargs):
        """Store component classes."""
        instance = super().__new__(cls)
        instance._AuxiliaryCoordinate = AuxiliaryCoordinate
        instance._Constructs = Constructs
        instance._Domain = Domain
        instance._DomainAxis = DomainAxis
        instance._Quantization = Quantization
        instance._RaggedContiguousArray = RaggedContiguousArray
        instance._RaggedIndexedArray = RaggedIndexedArray
        instance._RaggedIndexedContiguousArray = RaggedIndexedContiguousArray
        instance._GatheredArray = GatheredArray
        instance._Count = Count
        instance._Index = Index
        instance._List = List
        return instance

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        return f"<{self.__class__.__name__}: {self._one_line_description()}>"

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        title = f"Field: {self.identity('')}"

        # Append the netCDF variable name
        ncvar = self.nc_get_variable(None)
        if ncvar is not None:
            title += f" (ncvar%{ncvar})"

        string = [title]
        string.append("".ljust(len(string[0]), "-"))

        # Units
        units = getattr(self, "units", "")
        calendar = getattr(self, "calendar", None)
        if calendar is not None:
            units += f" {calendar}"

        # Axes
        axis_names = self._unique_domain_axis_identities()

        # Data
        if self.has_data():
            string.append(
                f"Data            : {self._one_line_description(axis_names)}"
            )

        # Cell methods
        cell_methods = self.cell_methods(todict=True)
        if cell_methods:
            x = []
            for cm in cell_methods.values():
                cm = cm.copy()
                cm.set_axes(
                    tuple(
                        [
                            axis_names.get(axis, axis)
                            for axis in cm.get_axes(())
                        ]
                    )
                )
                x.append(str(cm))

            c = " ".join(x)

            string.append(f"Cell methods    : {c}")

        def _print_item(self, key, variable, axes):
            """Private function called by __str__."""
            # Field ancillary
            x = [variable.identity(default=key)]

            if variable.has_data():
                shape = [axis_names[axis] for axis in axes]
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
                x.append(f" = {variable.get_data()}")

            return "".join(x)

        # Field ancillary variables
        x = [
            _print_item(self, key, anc, self.constructs.data_axes()[key])
            for key, anc in sorted(self.field_ancillaries(todict=True).items())
        ]
        if x:
            field_ancils = "\n                : ".join(x)
            string.append(f"Field ancils    : {field_ancils}")

        string.append(str(self.domain))

        return "\n".join(string)

    def __getitem__(self, indices):
        """Return a subspace of the field defined by indices.

        f.__getitem__(indices) <==> f[indices]

        The new subspace contains the same properties and similar
        metadata constructs to the original field, but the latter are
        also subspaced when they span domain axis constructs that have
        been changed.

        Indexing follows rules that are very similar to the numpy
        indexing rules, the only differences being:

        * An integer index i takes the i-th element but does not
          reduce the rank by one.

        * When two or more dimensions' indices are sequences of
          integers then these indices work independently along each
          dimension (similar to the way vector subscripts work in
          Fortran). This is the same behaviour as indexing on a
          Variable object of the netCDF4 package.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `Field`
                The subspace of the field construct.

        **Examples**

        >>> f.data.shape
        (1, 10, 9)
        >>> f[:, :, 1].data.shape
        (1, 10, 1)
        >>> f[:, 0].data.shape
        (1, 1, 9)
        >>> f[..., 6:3:-1, 3:6].data.shape
        (1, 3, 3)
        >>> f[0, [2, 9], [4, 8]].data.shape
        (1, 2, 2)
        >>> f[0, :, -2].data.shape
        (1, 10, 1)

        """
        new = self.copy()
        if indices is Ellipsis:
            return new

        # Remove a mesh id, on the assumption that the subspaced
        # domain will be different to the original.
        new.del_mesh_id(None)

        data = self.get_data(_fill_value=False)

        indices = parse_indices(data.shape, indices)
        indices = tuple(indices)

        data_axes = self.get_data_axes()

        # ------------------------------------------------------------
        # Subspace the field's data
        # ------------------------------------------------------------
        new_data = data[tuple(indices)]

        # Replace domain axes
        domain_axes = new.domain_axes(todict=True)
        for key, size in zip(data_axes, new_data.shape):
            domain_axis = domain_axes[key]
            domain_axis.set_size(size)
            new.set_construct(domain_axis, key=key)

        # ------------------------------------------------------------
        # Subspace other constructs that contain arrays
        # ------------------------------------------------------------
        new_constructs_data_axes = new.constructs.data_axes()

        if data_axes:
            for key, construct in new.constructs.filter_by_axis(
                *data_axes, axis_mode="or", todict=True
            ).items():
                needs_slicing = False
                dice = []
                for axis in new_constructs_data_axes[key]:
                    if axis in data_axes:
                        needs_slicing = True
                        dice.append(indices[data_axes.index(axis)])
                    else:
                        dice.append(slice(None))

                if needs_slicing:
                    new.set_construct(
                        construct[tuple(dice)], key=key, copy=False
                    )

        new.set_data(new_data, copy=False)

        return new

    def _one_line_description(self, axis_names_sizes=None):
        """Returns a one-line description of the field."""
        if axis_names_sizes is None:
            axis_names_sizes = self._unique_domain_axis_identities()

        x = [axis_names_sizes[axis] for axis in self.get_data_axes(default=())]

        axis_names = ", ".join(x)
        if axis_names:
            axis_names = f"({axis_names})"

        # Field units
        units = self.get_property("units", None)
        calendar = self.get_property("calendar", None)
        if units is not None:
            units = f" {units}"
        else:
            units = ""

        if calendar is not None:
            units += f" {calendar}"

        return f"{self.identity('')}{axis_names}{units}"

    @property
    def _test_docstring_substitution_property_Field(self):
        """Test docstring substitution on {{class}} with @property.

            {{inplace: `bool`, optional}}

        {{package}}.{{class}}

        """
        print("_test_docstring_substitution_property_Field")

    @property
    @_test_decorator_args("i")
    def _test_docstring_substitution_decorator_property(self):
        """Tests docstring substitution with a property and decorator.

        The substitution is tested on {{class}} with @property and a
        decorator.

            {{inplace: `bool`, optional}}

        {{package}}.{{class}}

        """
        print("_test_docstring_substitution_decorator_property_Field")

    @staticmethod
    def _test_docstring_substitution_staticmethod_Field():
        """Test docstring substitution on {{class}} with @staticmethod.

            {{inplace: `bool`, optional}}

        {{package}}.{{class}}

        """
        print("_test_docstring_substitution_staticmethod_Field")

    @_test_decorator_args("i")
    @_manage_log_level_via_verbosity
    @_inplace_enabled(default=False)
    def _test_docstring_substitution_Field(self, inplace=False, verbose=None):
        """Test docstring substitution on {{class}} with two decorators.

            {{inplace: `bool`, optional}}

        {{package}}.{{class}}

        """
        print("_test_docstring_substitution_Field")

    def field_ancillary(
        self,
        *identity,
        default=ValueError(),
        key=False,
        item=False,
        **filter_kwargs,
    ):
        """Select a field ancillary construct.

        {{unique construct}}

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `construct`, `field_ancillaries`

        :Parameters:

            identity: optional
                Select field ancillary constructs that have an
                identity, defined by their `!identities` methods, that
                matches any of the given values.

                Additionally, the values are matched against construct
                identifiers, with or without the ``'key%'`` prefix.

                If no values are provided then all field ancillary
                constructs are selected.

                {{value match}}

                {{displayed identity}}

            {{key: `bool`, optional}}

            {{item: `bool`, optional}}

            default: optional
                Return the value of the *default* parameter if there
                is no unique construct.

                {{default Exception}}

            {{filter_kwargs: optional}}

        :Returns:

                {{Returns construct}}

        **Examples**

        """
        return self._construct(
            "field_ancillary",
            "field_ancillaries",
            identity,
            key=key,
            item=item,
            default=default,
            **filter_kwargs,
        )

    def field_ancillaries(self, *identities, **filter_kwargs):
        """Return field ancillary constructs.

        ``f.field_ancillaries(*identities, **filter_kwargs)`` is
        equivalent to
        ``f.constructs.filter(filter_by_type=["field_ancillary"],
        filter_by_identity=identities, **filter_kwargs)``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`, `field_ancillary`

        :Parameters:

            identities: optional
                Select field ancillary constructs that have an
                identity, defined by their `!identities` methods, that
                matches any of the given values.

                {{value match}}

                {{displayed identity}}

            {{filter_kwargs: optional}} Also to configure the returned value.

                 .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                {{Returns constructs}}

        **Examples**

        >>> print(f.field_ancillaries())
        Constructs:
        {}

        >>> print(f.field_ancillaries())
        Constructs:
        {'cellmethod1': <{{repr}}CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
         'cellmethod0': <{{repr}}CellMethod: domainaxis3: maximum>}

        """
        return self._filter_interface(
            ("field_ancillary",),
            "field_ancillaries",
            identities,
            **filter_kwargs,
        )

    def cell_method(
        self,
        *identity,
        default=ValueError(),
        key=False,
        item=False,
        **filter_kwargs,
    ):
        """Select a cell method construct.

        {{unique construct}}

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `construct`, `cell_methods`

        :Parameters:

            identity: optional
                Select cell method constructs that have an identity,
                defined by their `!identities` methods, that matches
                any of the given values.

                Additionally, the values are matched against construct
                identifiers, with or without the ``'key%'`` prefix.

                Additionally, if for a given value
                ``f.domain_axes(value)`` returns a unique domain axis
                construct then any cell method constructs that span
                exactly that axis are selected. See `domain_axes` for
                details.

                If no values are provided then all cell method
                constructs are selected.

                {{value match}}

                {{displayed identity}}

            {{key: `bool`, optional}}

            {{item: `bool`, optional}}

            default: optional
                Return the value of the *default* parameter if there
                is no unique construct.

                {{default Exception}}

            {{filter_kwargs: optional}}

        :Returns:

                {{Returns construct}}

        **Examples**

        """
        return self._construct(
            "cell_method",
            "cell_methods",
            identity,
            key=key,
            item=item,
            default=default,
            **filter_kwargs,
        )

    def cell_methods(self, *identities, **filter_kwargs):
        """Return cell method constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`, `cell_method`

        :Parameters:

             identities: optional
                 Select cell method constructs that have an identity,
                 defined by their `!identities` methods, that matches
                 any of the given values.

                 Additionally, the values are matched against
                 construct identifiers, with or without the ``'key%'``
                 prefix.

                 Additionally, if for a given ``value``,
                 ``f.domain_axes(value)`` returns a unique domain axis
                 construct then any cell method constructs that span
                 exactly that axis are selected. See `domain_axes` for
                 details.

                 If no values are provided then all cell method
                 constructs are selected.

                 {{value match}}

                 {{displayed identity}}

             {{filter_kwargs: optional}} Also to configure the returned value.

                 .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                 {{Returns constructs}}

        **Examples**

        >>> f = {{package}}.example_field(1)
        >>> print(f.cell_methods())
        Constructs:
        {'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
         'cellmethod1': <CellMethod: domainaxis3: maximum>}
        >>> print(f.cell_methods('time'))
        Constructs:
        {'cellmethod1': <CellMethod: domainaxis3: maximum>}
        >>> print(f.cell_methods('bad identifier'))
        Constructs:
        {}

        """
        cached = filter_kwargs.get("cached")
        if cached is not None:
            return cached

        if identities:
            if "filter_by_identity" in filter_kwargs:
                raise TypeError(
                    f"Can't set {self.__class__.__name__}.cell_method() "
                    "keyword argument 'filter_by_identity' when "
                    "positional *identities arguments are also set"
                )
        else:
            identities = filter_kwargs.pop("filter_by_identity", ())

        if identities:
            out, keys, hits, misses = self._filter_interface(
                ("cell_method",),
                "cell_method",
                identities,
                _identity_config={"return_matched": True},
                **filter_kwargs,
            )
            if out is not None:
                return out

            # Additionally, if for a given ``value``,
            # ``f.domain_axes(value)`` returns a unique domain axis
            # construct then any cell method constructs that span
            # exactly that axis are selected. See `domain_axes` for
            # details.
            domain_axes = self.domain_axes(*misses, todict=True)
            if domain_axes:
                c = self.constructs._construct_dict("cell_method")
                for cm_key, cm in c.items():
                    cm_axes = cm.get_axes(None)
                    if len(cm_axes) == 1 and cm_axes[0] in domain_axes:
                        keys.add(cm_key)

            identities = ()
            if not keys:
                # Specify a key of None to ensure that no cell methods
                # are selected. (If keys is an empty set then all cell
                # methods are selected, which is not what we want,
                # here.)
                keys = (None,)

            filter_kwargs = {
                "filter_by_key": keys,
                "todict": filter_kwargs.pop("todict", False),
            }

        return self._filter_interface(
            ("cell_method",), "cell_method", identities, **filter_kwargs
        )

    @_inplace_enabled(default=False)
    def apply_masking(self, inplace=False):
        """Apply masking as defined by the CF conventions.

        Masking is applied to the field construct data as well as
        metadata constructs' data.

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

        .. versionadded:: (cfdm) 1.8.3

        .. seealso:: `Data.apply_masking`, `read`, `write`

        :Parameters:

            {{inplace: `bool`, optional}}

        :Returns:

            `Field` or `None`
                A new field construct with masked values, or `None` if
                the operation was in-place.

        **Examples**

        >>> f = {{package}}.example_field(0)
        >>> f.data[[0, -1]] = numpy.ma.masked
        >>> print(f.data.array)
        [[   --    --    --    --    --    --    --    --]
         [0.023 0.036 0.045 0.062 0.046 0.073 0.006 0.066]
         [0.11  0.131 0.124 0.146 0.087 0.103 0.057 0.011]
         [0.029 0.059 0.039 0.07  0.058 0.072 0.009 0.017]
         [   --    --    --    --    --    --    --    --]]
        >>> {{package}}.write(f, 'masked.nc')
        >>> no_mask = {{package}}.read('masked.nc', mask=False)[0]
        >>> print(no_mask.data.array)
        [9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36,
         9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36],
         [0.023 0.036 0.045 0.062 0.046 0.073 0.006 0.066]
         [0.11  0.131 0.124 0.146 0.087 0.103 0.057 0.011]
         [0.029 0.059 0.039 0.07  0.058 0.072 0.009 0.017]
        [9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36,
         9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36]])
        >>> masked = no_mask.apply_masking()
        >>> print(masked.data.array)
        [[   --    --    --    --    --    --    --    --]
         [0.023 0.036 0.045 0.062 0.046 0.073 0.006 0.066]
         [0.11  0.131 0.124 0.146 0.087 0.103 0.057 0.011]
         [0.029 0.059 0.039 0.07  0.058 0.072 0.009 0.017]
         [   --    --    --    --    --    --    --    --]]

        """
        f = _inplace_enabled_define_and_cleanup(self)

        # Apply masking to the field construct
        super(Field, f).apply_masking(inplace=True)

        # Apply masking to the metadata constructs
        self._apply_masking_constructs()

        return f

    def climatological_time_axes(self):
        """Return all axes which are climatological time axes.

        This is ascertained by inspecting the axes of any cell methods
        constructs.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `set`
                The axes on the field which are climatological time
                axes. If there are none, this will be an empty set.

        **Examples**

        >>> f
        <{{repr}}Field: air_temperature(time(12), latitude(145), longitude(192)) K>
        >>> print(f.cell_methods())
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: domainaxis0: minimum within days>,
         'cellmethod1': <{{repr}}CellMethod: domainaxis0: mean over days>}
        >>> f.climatological_time_axes()
        {'domainaxis0'}
        >>> g
        <Field: air_potential_temperature(time(120), latitude(5), longitude(8)) K>
        >>> print(g.cell_methods())
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: area: mean>}
        >>> g.climatological_time_axes()
        set()

        """
        out = set()

        domain_axes = self.domain_axes(todict=True)

        for key, cm in self.cell_methods(todict=True).items():
            qualifiers = cm.qualifiers()
            if not ("within" in qualifiers or "over" in qualifiers):
                continue

            axes = cm.get_axes(default=())
            if len(axes) != 1:
                continue

            axis = axes[0]
            if axis not in domain_axes:
                continue

            # Still here? Then this axis is a climatological time axis
            out.add(axis)

        return out

    @_inplace_enabled(default=False)
    def compress(
        self,
        method,
        axes=None,
        count_properties=None,
        index_properties=None,
        list_properties=None,
        inplace=False,
    ):
        """Compress the field construct.

        Compression can save space by identifying and removing
        unwanted missing data. Such compression techniques store the
        data more efficiently and result in no precision loss.

        The field construct data is compressed, along with any
        applicable metadata constructs.

        Whether or not the field construct is compressed does not
        alter its functionality nor external appearance.

        A field that is already compressed will be returned compressed
        by the chosen method.

        When writing a compressed field construct to a dataset,
        compressed netCDF variables are written, along with the
        supplementary netCDF variables and attributes that are
        required for the encoding.

        The following type of compression are available (see the
        *method* parameter):

            * Ragged arrays for discrete sampling geometries
              (DSG). Three different types of ragged array
              representation are supported.

            ..

            * Compression by gathering.

        .. versionadded:: (cfdm) 1.7.11

        .. seealso:: `uncompress`

        :Parameters:

            method: `str`
                The compression method. One of:

                * ``'contiguous'``

                  Contiguous ragged array representation for DSG
                  "point", "timeSeries", "trajectory" or "profile"
                  features.

                  The field construct data must have exactly 2
                  dimensions for which the first (leftmost) dimension
                  indexes each feature and the second (rightmost)
                  dimension contains the elements for the
                  features. Trailing missing data values in the second
                  dimension are removed to created the compressed
                  data.

                * ``'indexed'``

                  Indexed ragged array representation for DSG "point",
                  "timeSeries", "trajectory", or "profile" features.

                  The field construct data must have exactly 2
                  dimensions for which the first (leftmost) dimension
                  indexes each feature and the second (rightmost)
                  dimension contains the elements for the
                  features. Trailing missing data values in the second
                  dimension are removed to created the compressed
                  data.

                * ``'indexed_contiguous'``

                  Indexed contiguous ragged array representation for
                  DSG "timeSeriesProfile", or "trajectoryProfile"
                  features.

                  The field construct data must have exactly 3
                  dimensions for which the first (leftmost) dimension
                  indexes each feature; the second (middle) dimension
                  indexes each timeseries or trajectory; and the third
                  (rightmost) dimension contains the elements for the
                  timeseries or trajectories. Trailing missing data
                  values in the third dimension are removed to created
                  the compressed data.

                * ``'gathered'``

                  Compression by gathering over any subset of the
                  field construct data dimensions.

                  *Not yet available.*

            count_properties: `dict`, optional
                Provide properties to the count variable for
                contiguous ragged array representation or indexed
                contiguous ragged array representation.

                *Parameter example:*
                  ``count_properties={'long_name': 'number of timeseries'}``

            index_properties: `dict`, optional
                Provide properties to the index variable for indexed
                ragged array representation or indexed contiguous
                ragged array representation.

                *Parameter example:*
                  ``index_properties={'long_name': 'station of profile'}``

            list_properties: `dict`, optional
                Provide properties to the list variable for
                compression by gathering.

                *Parameter example:*
                  ``list_properties={'long_name': 'uncompression indices'}``

            {{inplace: `bool`, optional}}

        :Returns:

            `Field` or `None`
                The compressed field construct, or `None` if the
                operation was in-place.

        **Examples**

        >>> f.data.get_compression_type()
        ''
        >>> print(f.array)
        [[3.98  0.0  0.0  --    --   --   --  --  --]
         [ 0.0  0.0  0.0  3.4  0.0  0.0 4.61  --  --]
         [0.86  0.8 0.75  0.0 4.56   --   --  --  --]
         [ 0.0 0.09  0.0 0.91 2.96 1.14 3.86 0.0 0.0]]
        >>> g = f.compress('contiguous')
        >>> g.equals(f)
        True

        >>> {{package}}.write(g, 'compressed_file_contiguous.nc')
        >>> h = {{package}}.read( 'compressed_file_contiguous.nc')[0]
        >>> h.equals(f)
        True

        >>> g.data.get_compression_type()
        'ragged contiguous'
        >>> g.data.get_count()
        <{{repr}}Count: (4) >
        >>> print(g.data.get_count().array)
        [3 7 5 9]
        >>> g.compress('indexed', inplace=True)
        >>> g.data.get_index()
        <{{repr}}Index: (24) >
        >>> print(g.data.get_index().array)
        [0 0 0 1 1 1 1 1 1 1 2 2 2 2 2 3 3 3 3 3 3 3 3 3]
        >>> {{package}}.write(g, 'compressed_file_indexed.nc')

        """

        def _empty_compressed_data(data, shape):
            return data.empty(
                shape=shape,
                dtype=data.dtype,
                units=data.get_units(None),
                calendar=data.get_calendar(None),
            )

        def _RaggedContiguousArray(
            self, compressed_data, data, count_variable
        ):
            return self._RaggedContiguousArray(
                compressed_data,
                shape=data.shape,
                count_variable=count_variable,
            )

        def _RaggedIndexedArray(self, compressed_data, data, index_variable):
            return self._RaggedIndexedArray(
                compressed_data,
                shape=data.shape,
                index_variable=index_variable,
            )

        def _RaggedIndexedContiguousArray(
            self, compressed_data, data, count_variable, index_variable
        ):
            return self._RaggedIndexedContiguousArray(
                compressed_data,
                shape=data.shape,
                count_variable=count_variable,
                index_variable=index_variable,
            )

        def _compress_metadata(
            f, method, count, N, axes, Array_func, **kwargs
        ):
            """Compresses constructs for a field by a chosen method.

            :Parameters:

                f: `Field`

                count: sequence of `int`

                N: `int`
                    The number of elements in the compressed array.

                axes: sequence of `str`

                Array_func:

                kwargs:

            :Returns:

                `None`

            """
            if method == "indexed_contiguous":
                shape1 = f.data.shape[1]

            for key, c in f.constructs.filter_by_axis(
                *axes, axis_mode="or", todict=True
            ).items():
                c_axes = f.get_data_axes(key)
                if c_axes != axes:
                    # Skip metadata constructs which don't span
                    # exactly the same axes in the same order
                    continue

                # Initialise the compressed data for the metadata
                # construct
                data = c.get_data(None)
                if data is not None:
                    compressed_data = _empty_compressed_data(data, (N,))

                    # Populate the compressed data for the metadata
                    # construct
                    start = 0
                    if method == "indexed_contiguous" and c.data.ndim == 2:
                        c_start = 0
                        for i, d in enumerate(
                            data.flatten(range(data.ndim - 1))
                        ):
                            c_start = shape1 * i
                            c_end = c_start + shape1
                            last = sum(n > 0 for n in count[c_start:c_end])

                            end = start + last
                            compressed_data[start:end] = d[:last]
                            start += last
                    else:
                        for last, d in zip(
                            count, data.flatten(range(data.ndim - 1))
                        ):
                            if not last:
                                continue

                            end = start + last
                            compressed_data[start:end] = d[:last]
                            start += last

                # Insert the compressed data into the metadata
                # construct
                y = Array_func(f, compressed_data, data=data, **kwargs)
                data._set_CompressedArray(y, copy=False)

                if c.has_bounds():
                    data = c.get_bounds_data(None)
                    if data is None:
                        continue

                    b_shape = data.shape[c.data.ndim :]
                    compressed_data = _empty_compressed_data(
                        data, (N,) + b_shape
                    )

                    # Populate the compressed data for the metadata
                    # construct
                    start = 0
                    if method == "indexed_contiguous" and c.data.ndim == 2:
                        c_start = 0
                        for i, d in enumerate(
                            data.flatten(range(c.data.ndim - 1))
                        ):
                            c_start = shape1 * i
                            c_end = c_start + shape1
                            last = sum(n > 0 for n in count[c_start:c_end])

                            end = start + last
                            compressed_data[start:end] = d[:last]
                            start += last
                    else:
                        for last, d in zip(
                            count, data.flatten(range(c.data.ndim - 1))
                        ):
                            if not last:
                                continue

                            end = start + last
                            compressed_data[start:end] = d[:last]
                            start += last

                    # Insert the compressed data into the metadata
                    # construct
                    y = Array_func(f, compressed_data, data=data, **kwargs)
                    data._set_CompressedArray(y, copy=False)

        def _derive_count(flattened_data):
            """Derive the DSG count for each feature.

            :Parameters:

                flattened_data: array_like
                    The 2-d flattened array from which to derive the
                    counts. The leading dimension is the number of
                    features.

            :Returns:

                `list`
                    The count for each feature.

            """
            count = []
            masked = np.ma.masked
            for d in flattened_data:
                d = d.array
                last = d.size
                for i in d[::-1]:
                    if i is not masked:
                        break

                    last -= 1

                count.append(last)

            return count

        f = _inplace_enabled_define_and_cleanup(self)

        data = f.get_data(None)
        if data is None:
            return f

        current_compression_type = data.get_compression_type().replace(
            " ", "_"
        )
        if (
            current_compression_type
            and current_compression_type == "ragged_" + method
        ):
            # The field is already compressed by the correct method
            return f

        if method == "contiguous":
            if self.data.ndim != 2:
                raise ValueError(
                    "The field data must have exactly 2 dimensions for "
                    f"DSG ragged contiguous compression. Got {self.data.ndim}"
                )
        elif method == "indexed":
            if self.data.ndim != 2:
                raise ValueError(
                    "The field data must have exactly 2 dimensions for "
                    f"DSG ragged indexed compression. Got {self.data.ndim}"
                )
        elif method == "indexed_contiguous":
            if self.data.ndim != 3:
                raise ValueError(
                    "The field data must have exactly 3 dimensions for "
                    "DSG ragged indexed contiguous compression. Got "
                    f"{self.data.ndim}"
                )

        # Make sure that the metadata constructs have the same
        # relative axis order as the field's data
        f.transpose(range(self.data.ndim), constructs=True, inplace=True)

        if method == "gathered":
            # --------------------------------------------------------
            # Compression by gathering
            # --------------------------------------------------------
            pass
        else:
            # --------------------------------------------------------
            # DSG compression
            # --------------------------------------------------------
            flattened_data = data.flatten(range(data.ndim - 1))

            # Try to get the counts from an auxiliary coordinate
            # construct that spans the same axes as the field data
            count = None
            data_axes = f.get_data_axes()
            construct_axes = f.constructs.data_axes()
            for key, c in (
                f.auxiliary_coordinates().filter_by_data(todict=True).items()
            ):
                if construct_axes[key] != data_axes:
                    continue

                count = _derive_count(c.data.flatten(range(c.ndim - 1)))
                break

            if count is None:
                # When no auxiliary coordinate constructs span the
                # field data dimensions, get the counts from the field
                # data.
                count = _derive_count(flattened_data)

            N = sum(count)
            compressed_field_data = _empty_compressed_data(data, (N,))

            start = 0
            for last, d in zip(count, flattened_data):
                if not last:
                    continue

                end = start + last
                compressed_field_data[start:end] = d[:last]
                start += last

        if method == "contiguous":
            # --------------------------------------------------------
            # Ragged contiguous
            # --------------------------------------------------------
            count_variable = self._Count(
                properties=count_properties,
                data=self._Data([n for n in count if n]),
            )

            x = _RaggedContiguousArray(
                self,
                compressed_field_data,
                data,
                count_variable=count_variable,
            )

            _compress_metadata(
                f,
                method,
                count,
                N,
                f.get_data_axes(),
                _RaggedContiguousArray,
                count_variable=count_variable,
            )

        elif method == "indexed":
            # --------------------------------------------------------
            # Ragged indexed
            # --------------------------------------------------------
            index_variable = self._Index(
                properties=index_properties,
                data=self._Data.empty(shape=(N,), dtype=int),
            )

            start = 0
            for i, (last, d) in enumerate(zip(count, flattened_data)):
                if not last:
                    continue

                end = start + last
                index_variable.data[start:end] = i
                start += last

            x = _RaggedIndexedArray(
                self, compressed_field_data, data, index_variable
            )

            _compress_metadata(
                f,
                method,
                count,
                N,
                f.get_data_axes(),
                _RaggedIndexedArray,
                index_variable=index_variable,
            )

        elif method == "indexed_contiguous":
            # --------------------------------------------------------
            # Ragged indexed contiguous
            # --------------------------------------------------------
            index = []
            shape1 = f.data.shape[1]
            for i in range(f.data.shape[0]):
                start = shape1 * i
                end = start + shape1
                index.extend([i] * sum(n > 0 for n in count[start:end]))

            count_variable = self._Count(
                properties=count_properties,
                data=self._Data([n for n in count if n]),
            )
            index_variable = self._Index(
                properties=index_properties, data=self._Data(index)
            )

            x = _RaggedIndexedContiguousArray(
                self,
                compressed_field_data,
                data,
                count_variable,
                index_variable,
            )

            _compress_metadata(
                f,
                method,
                count,
                N,
                f.get_data_axes(),
                _RaggedIndexedContiguousArray,
                count_variable=count_variable,
                index_variable=index_variable,
            )

            # Compress metadata constructs that span the index axis,
            # but not the count axis.
            _compress_metadata(
                f,
                method,
                count,
                len(index),
                f.get_data_axes()[:-1],
                _RaggedIndexedArray,
                index_variable=index_variable,
            )

        elif method == "gathered":
            # --------------------------------------------------------
            # Gathered
            # --------------------------------------------------------
            raise ValueError(
                "Compression by gathering is not yet available - sorry!"
            )

        else:
            raise ValueError(f"Unknown compression method: {method!r}")

        f.data._set_CompressedArray(x, copy=False)

        return f

    @classmethod
    def concatenate(
        cls, fields, axis, cull_graph=False, relaxed_units=False, copy=True
    ):
        """Join together a sequence of Field constructs.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `Data.concatenate`, `Data.cull_graph`

        :Parameters:

            fields: sequence of `{{class}}`
                The fields to concatenate.

            axis:
                Select the domain axis to along which to concatenate,
                defined by that which would be selected by passing
                *axis* to a call of the field construct's
                `domain_axis` method. For example, for a value of
                'time', the domain axis construct returned by
                ``f.domain_axis('time')`` is selected.

            {{cull_graph: `bool`, optional}}

            {{relaxed_units: `bool`, optional}}

            {{concatenate copy: `bool`, optional}}

        :Returns:

            `{{class}}`
                The concatenated construct.

        """
        if isinstance(fields, cls):
            raise ValueError("Must provide a sequence of Field constructs")

        fields = tuple(fields)
        field0 = fields[0]
        data_axes = field0.get_data_axes()
        axis_key = field0.domain_axis(
            axis,
            key=True,
            default=ValueError(
                f"Can't identify a unique concatenation axis from {axis!r}"
            ),
        )
        try:
            axis = data_axes.index(axis_key)
        except ValueError:
            raise ValueError(
                "The field's data must span the concatenation axis"
            )

        out = field0
        if copy:
            out = out.copy()

        if len(fields) == 1:
            return out

        new_data = out._Data.concatenate(
            [f.get_data(_fill_value=False) for f in fields],
            axis=axis,
            cull_graph=cull_graph,
            relaxed_units=relaxed_units,
            copy=copy,
        )

        # Change the domain axis size
        out.set_construct(
            out._DomainAxis(size=new_data.shape[axis]), key=axis_key
        )

        # Insert the concatenated data
        out.set_data(new_data, axes=data_axes, copy=False)

        # ------------------------------------------------------------
        # Concatenate constructs with data
        # ------------------------------------------------------------
        for key, construct in field0.constructs.filter_by_data(
            todict=True
        ).items():
            construct_axes = field0.get_data_axes(key)

            if axis_key not in construct_axes:
                # This construct does not span the concatenating axis
                # in the first field
                continue

            constructs = [construct]
            for f in fields[1:]:
                c = f.constructs.get(key)
                if c is None:
                    # This field does not have this construct
                    constructs = None
                    break

                constructs.append(c)

            if not constructs:
                # Not every field has this construct, so remove it
                # from the output field.
                out.del_construct(key)
                continue

            # Still here? Then try concatenating the constructs from
            # each field.
            try:
                construct = construct.concatenate(
                    constructs,
                    axis=construct_axes.index(axis_key),
                    cull_graph=cull_graph,
                    relaxed_units=relaxed_units,
                    copy=copy,
                )
            except ValueError:
                # Couldn't concatenate this construct, so remove it from
                # the output field.
                out.del_construct(key)
            else:
                # Successfully concatenated this construct, so insert
                # it into the output field.
                out.set_construct(
                    construct, key=key, axes=construct_axes, copy=False
                )

        return out

    def creation_commands(
        self,
        representative_data=False,
        namespace=None,
        indent=0,
        string=True,
        name="field",
        data_name="data",
        header=True,
    ):
        """Return the commands that would create the field construct.

        **Construct keys**

        The *key* parameter of the output `set_construct` commands is
        utilised in order minimise the number of commands needed to
        implement cross-referencing between constructs (e.g. between a
        coordinate reference construct and coordinate
        constructs). This is usually not necessary when building field
        constructs, as by default the `set_construct` method returns a
        unique construct key for the construct being set.

        .. versionadded:: (cfdm) 1.8.7.0

        .. seealso:: `set_construct`,
                     `{{package}}.Data.creation_commands`,
                     `{{package}}.Domain.creation_commands`,
                     `{{package}}.example_field`

        :Parameters:

            {{representative_data: `bool`, optional}}

            {{namespace: `str`, optional}}

            {{indent: `int`, optional}}

            {{string: `bool`, optional}}

            {{name: `str`, optional}}

            {{data_name: `str`, optional}}

            {{header: `bool`, optional}}

        :Returns:

            {{returns creation_commands}}

        **Examples**

        >>> q = {{package}}.example_field(0)
        >>> print(q)
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(latitude(5), longitude(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(8) = [22.5, ..., 337.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]
        >>> print(q.creation_commands())
        #
        # field: specific_humidity
        field = {{package}}.Field()
        field.set_properties({'Conventions': 'CF-1.12', 'project': 'research', 'standard_name': 'specific_humidity', 'units': '1'})
        field.nc_set_variable('q')
        data = {{package}}.Data([[0.007, 0.034, 0.003, 0.014, 0.018, 0.037, 0.024, 0.029], [0.023, 0.036, 0.045, 0.062, 0.046, 0.073, 0.006, 0.066], [0.11, 0.131, 0.124, 0.146, 0.087, 0.103, 0.057, 0.011], [0.029, 0.059, 0.039, 0.07, 0.058, 0.072, 0.009, 0.017], [0.006, 0.036, 0.019, 0.035, 0.018, 0.037, 0.034, 0.013]], units='1', dtype='f8')
        field.set_data(data)
        #
        # domain_axis: ncdim%lat
        c = {{package}}.DomainAxis()
        c.set_size(5)
        c.nc_set_dimension('lat')
        field.set_construct(c, key='domainaxis0', copy=False)
        #
        # domain_axis: ncdim%lon
        c = {{package}}.DomainAxis()
        c.set_size(8)
        c.nc_set_dimension('lon')
        field.set_construct(c, key='domainaxis1', copy=False)
        #
        # domain_axis:
        c = {{package}}.DomainAxis()
        c.set_size(1)
        field.set_construct(c, key='domainaxis2', copy=False)
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
        field.set_construct(c, axes=('domainaxis0',), key='dimensioncoordinate0', copy=False)
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
        field.set_construct(c, axes=('domainaxis1',), key='dimensioncoordinate1', copy=False)
        #
        # dimension_coordinate: time
        c = {{package}}.DimensionCoordinate()
        c.set_properties({'units': 'days since 2018-12-01', 'standard_name': 'time'})
        c.nc_set_variable('time')
        data = {{package}}.Data([31.0], units='days since 2018-12-01', dtype='f8')
        c.set_data(data)
        field.set_construct(c, axes=('domainaxis2',), key='dimensioncoordinate2', copy=False)
        #
        # cell_method: mean
        c = {{package}}.CellMethod()
        c.set_method('mean')
        c.set_axes(('area',))
        field.set_construct(c)
        #
        # field data axes
        field.set_data_axes(('domainaxis0', 'domainaxis1'))

        >>> print(q.creation_commands(representative_data=True, namespace='',
        ...                           indent=4, header=False))
            field = Field()
            field.set_properties({'Conventions': 'CF-1.12', 'project': 'research', 'standard_name': 'specific_humidity', 'units': '1'})
            field.nc_set_variable('q')
            data = <Data(5, 8): [[0.007, ..., 0.013]] 1>  # Representative data
            field.set_data(data)
            c = DomainAxis()
            c.set_size(5)
            c.nc_set_dimension('lat')
            field.set_construct(c, key='domainaxis0', copy=False)
            c = DomainAxis()
            c.set_size(8)
            c.nc_set_dimension('lon')
            field.set_construct(c, key='domainaxis1', copy=False)
            c = DomainAxis()
            c.set_size(1)
            field.set_construct(c, key='domainaxis2', copy=False)
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
            field.set_construct(c, axes=('domainaxis0',), key='dimensioncoordinate0', copy=False)
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
            field.set_construct(c, axes=('domainaxis1',), key='dimensioncoordinate1', copy=False)
            c = DimensionCoordinate()
            c.set_properties({'units': 'days since 2018-12-01', 'standard_name': 'time'})
            c.nc_set_variable('time')
            data = <Data(1): [2019-01-01 00:00:00]>  # Representative data
            c.set_data(data)
            field.set_construct(c, axes=('domainaxis2',), key='dimensioncoordinate2', copy=False)
            c = CellMethod()
            c.set_method('mean')
            c.set_axes(('area',))
            field.set_construct(c)
            field.set_data_axes(('domainaxis0', 'domainaxis1'))

        """
        if name in ("b", "c", "d", "f", "i", "q", "mask"):
            raise ValueError(
                f"The 'name' parameter can not have the value {name!r}"
            )

        namespace0 = namespace
        if namespace is None:
            namespace = self._package() + "."
        elif namespace and not namespace.endswith("."):
            namespace += "."

        out = super().creation_commands(
            representative_data=representative_data,
            indent=indent,
            namespace=namespace,
            string=False,
            name=name,
            data_name=data_name,
            header=header,
        )

        mesh_id = self.get_mesh_id(None)
        if mesh_id is not None:
            out.append(f"{name}.set_mesh_id({mesh_id!r})")

        nc_global_attributes = self.nc_global_attributes()
        if nc_global_attributes:
            out.append("#")
            out.append("# netCDF global attributes")
            out.append(
                f"{name}.nc_set_global_attributes({nc_global_attributes!r})"
            )

        # Domain
        out.extend(
            self.domain.creation_commands(
                representative_data=representative_data,
                string=False,
                indent=indent,
                namespace=namespace0,
                name=name,
                data_name=data_name,
                header=header,
                _domain=False,
            )
        )

        # Field ancillary constructs
        for key, c in self.field_ancillaries().items():
            out.extend(
                c.creation_commands(
                    representative_data=representative_data,
                    string=False,
                    indent=indent,
                    namespace=namespace0,
                    name="c",
                    data_name=data_name,
                    header=header,
                )
            )
            out.append(
                f"{name}.set_construct(c, axes={self.get_data_axes(key)}, "
                f"key={key!r}, copy=False)"
            )

        # Cell method constructs
        for key, c in self.cell_methods(todict=True).items():
            out.extend(
                c.creation_commands(
                    namespace=namespace0,
                    indent=indent,
                    string=False,
                    header=header,
                    name="c",
                )
            )
            out.append(f"{name}.set_construct(c)")

        # Field data axes
        data_axes = self.get_data_axes(default=None)
        if data_axes is not None:
            if header:
                out.append("#")
                out.append("# field data axes")

            out.append(f"{name}.set_data_axes({data_axes})")

        if string:
            indent = " " * indent
            out[0] = indent + out[0]
            out = ("\n" + indent).join(out)

        return out

    @_display_or_return
    def dump(self, data=True, display=True, _level=0, _title=None):
        """A full description of the field construct.

        Returns a description of all properties, including those of
        metadata constructs and their components, and provides
        selected values of all data arrays.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            data: `bool`, optional
                If True (the default) then display the first and last
                Field data values. This can take a long time if the
                data needs an expensive computation (possibly
                including a slow read from local or remote disk), in
                which case setting *data* to False will not display
                these values, thereby avoiding the computational
                cost. This only applies to the Field's data - the
                first and last values of data arrays stored in
                metadata constructs are always displayed.

                Note that when the first and last values are
                displayed, they are cached for fast future retrieval.

                .. versionadded:: (cfdm) 1.12.3.0

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        indent = "    "
        indent0 = indent * _level

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

            _title = f"Field: {_title}"

        line = f"{indent0}{''.ljust(len(_title), '-')}"

        # Title
        string = [line, indent0 + _title, line]

        axis_to_name = self._unique_domain_axis_identities()

        constructs_data_axes = self.constructs.data_axes()

        # Simple properties
        properties = self.properties()
        if properties:
            string.append(self._dump_properties(_level=_level))

        # Data
        d = self.get_data(None)
        if d is not None:
            x = [axis_to_name[axis] for axis in self.get_data_axes(default=())]
            x = f"{indent0}Data({', '.join(x)})"
            if data:
                # Show selected data values
                x += f" = {d}"
            else:
                # Don't show any data values
                units = d.Units
                if units.isreftime:
                    calendar = getattr(units, "calendar", None)
                    if calendar is not None:
                        x += f" {calendar}"
                else:
                    units = getattr(units, "units", None)
                    if units is not None:
                        x += f" {units}"

            string.append("")
            string.append(x)
            string.append("")

        # Quantization
        q = self.get_quantization(None)
        if q is not None:
            string.append(q.dump(display=False, _level=_level))
            string.append("")

        # Cell methods
        cell_methods = self.cell_methods(todict=True)
        if cell_methods:
            for cm in cell_methods.values():
                cm = cm.copy()
                cm.set_axes(
                    tuple(
                        [
                            axis_to_name.get(axis, axis)
                            for axis in cm.get_axes(())
                        ]
                    )
                )
                string.append(cm.dump(display=False, _level=_level))

            string.append("")

        # Field ancillaries
        for cid, value in sorted(self.field_ancillaries(todict=True).items()):
            string.append(
                value.dump(
                    display=False,
                    _axes=constructs_data_axes[cid],
                    _axis_names=axis_to_name,
                    _level=_level,
                )
            )
            string.append("")

        string.append(
            self.get_domain().dump(display=False, _create_title=False)
        )

        return "\n".join(string)

    def file_directories(self, constructs=True):
        """The directories of files containing parts of the data.

        Returns the locations of any files referenced by the data.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `replace_directory`

        :Parameters:

            constructs: `bool`, optional
                If True (the default) then add also the directory to
                the data of metadata constructs. If False then don't
                do this.

        :Returns:

            `set`
                The unique set of file directories as absolute paths.

        **Examples**

        >>> d.file_directories()
        {'/home/data1', 'file:///data2'}

        """
        directories = super().file_directories()
        if constructs:
            for c in self.constructs.filter_by_data(todict=True).values():
                directories.update(c.file_directories())

        return directories

    def get_data_axes(self, *identity, default=ValueError(), **filter_kwargs):
        """Gets the keys of the axes spanned by the construct data.

        Specifically, returns the keys of the domain axis constructs
        spanned by the data of the field or of a metadata construct.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_data_axes`, `get_data`, `set_data_axes`

        :Parameters:

            identity, filter_kwargs: optional
                Select the unique construct returned by
                ``f.construct(*identity, **filter_kwargs)``. See
                `construct` for details.

                If neither *identity* nor *filter_kwargs* are set then
                the domain of the field construct's data are
                returned.

                .. versionadded:: (cfdm) 1.10.0.0

            default: optional
                Return the value of the *default* parameter if the data
                axes have not been set.

                {{default Exception}}

            {{filter_kwargs: optional}}

                .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `tuple`
                The keys of the domain axis constructs spanned by the
                data.

        **Examples**

        >>> f = {{package}}.example_field(0)
        >>> f.get_data_axes()
        ('domainaxis0', 'domainaxis1')
        >>> f.get_data_axes('latitude')
        ('domainaxis0',)
        >>> f.get_data_axes('time')
        ('domainaxis2',)
        >>> f.has_data_axes()
        True
        >>> f.del_data_axes()
        ('domainaxis0', 'domainaxis1')
        >>> f.has_data_axes()
        False
        >>> f.get_data_axes(default='no axes')
        'no axes'

        """
        if not identity and not filter_kwargs:
            # Get axes of the Field data array
            return super().get_data_axes(default=default)

        key = self.construct(
            *identity, key=True, default=None, **filter_kwargs
        )
        if key is None:
            if default is None:
                return default

            return self._default(
                default, "Can't get axes for non-existent construct"
            )

        axes = super().get_data_axes(key, default=None)
        if axes is None:
            if default is None:
                return default

            return self._default(
                default, f"Construct {key!r} has not had axes set"
            )

        return axes

    def get_domain(self):
        """Return the domain.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `domain`

        :Returns:

            `Domain`
                 The domain.

        **Examples**

        >>> d = f.get_domain()

        """
        domain = self._Domain.fromconstructs(self.constructs)

        # Set climatological time axes for the domain
        climatological_time_axes = self.climatological_time_axes()
        if climatological_time_axes:
            coordinates = self.coordinates()
            for key, c in coordinates.items():
                axes = self.get_data_axes(key, default=())
                if len(axes) == 1 and axes[0] in climatological_time_axes:
                    c.set_climatology(True)

        return domain

    def get_filenames(self, normalise=True):
        """Return the names of the files containing the data.

        The names of the files containing the data of the field
        constructs and of any metadata constructs are returned.

        :Parameters:

            {{normalise: `bool`, optional}}

                .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `set`
                The file names in normalised, absolute form. If all of
                the data are in memory then an empty `set` is
                returned.

        **Examples**

        >>> f = {{package}}.example_field(0)
        >>> {{package}}.write(f, 'temp_file.nc')
        >>> g = {{package}}.read('temp_file.nc')[0]
        >>> g.get_filenames()
        {'temp_file.nc'}

        """
        out = super().get_filenames(normalise=normalise)

        for c in self.constructs.filter_by_data(todict=True).values():
            out.update(c.get_filenames(normalise=normalise))

        return out

    def indices(self, **kwargs):
        """Create indices that define a subspace of the field construct.

        The subspace is defined by defining indices based on the
        positions of the given data values of 1-d metadata constructs.

        The returned tuple of indices may be used to created a subspace by
        indexing the original field construct with them.

        Metadata constructs and the conditions on their data are defined
        by keyword parameters.

        * Any domain axes that have not been identified remain unchanged.

        * Multiple domain axes may be subspaced simultaneously, and it
          doesn't matter which order they are specified in.

        * Subspace criteria may be provided for size 1 domain axes that
          are not spanned by the field construct's data.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `__getitem__`, `__setitem__`

        :Parameters:

            kwargs: *optional*
                Each keyword parameter specifies a value or values
                whose positions in the 1-d metadata construct's data,
                identified by the parameter name, define the indices
                for that dimension.

        :Returns:

            `tuple`
                The indices meeting the conditions.

        **Examples**

        >>> f = {{package}}.example_field(0)
        >>> print(f)
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(latitude(5), longitude(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(8) = [22.5, ..., 337.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]

        >>> indices = f.indices(longitude=112.5)
        >>> indices
        (slice(None, None, None),
         array([False, False,  True, False, False, False, False, False]))
        >>> print(f[indices])
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(latitude(5), longitude(1)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(1) = [112.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]

        >>> indices = f.indices(longitude=112.5, latitude=[-45, 75])
        >>> indices
        (array([False,  True, False, False,  True]),
         array([False, False,  True, False, False, False, False, False]))
        >>> print(f[indices])
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(latitude(2), longitude(1)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(2) = [-45.0, 75.0] degrees_north
                        : longitude(1) = [112.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]

        >>> indices = f.indices(time=31)
        >>> indices
        (slice(None, None, None), slice(None, None, None))
        >>> print(f[indices])
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(latitude(5), longitude(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(8) = [22.5, ..., 337.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]

        """
        # Initialise indices dictionary
        indices = {axis: slice(None) for axis in self.domain_axes(todict=True)}

        parsed = {}
        unique_axes = set()
        n_axes = 0

        for identity, value in kwargs.items():
            key, construct = self.construct(
                identity,
                filter_by_data=True,
                item=True,
                default=(None, None),
                filter_by_naxes=(1,),
            )
            if construct is not None:
                axes = self.get_data_axes(key)
            else:
                da_key = self.domain_axis(identity, key=True, default=None)
                if da_key is not None:
                    axes = (da_key,)
                    key = None
                    construct = None
                else:
                    raise ValueError(
                        f"Can't find indices. Ambiguous axis or axes "
                        f"defined by {identity!r}"
                    )

            if axes in parsed:
                # The axes are the same as an existing key
                parsed[axes].append((axes, key, construct, value, identity))
            else:
                new_key = True
                y = set(axes)
                for x in parsed:
                    if set(x) == set(y):
                        # The axes are the same but in a different
                        # order, so we don't need a new key.
                        parsed[x].append(
                            (axes, key, construct, value, identity)
                        )
                        new_key = False
                        break

                if new_key:
                    # The axes, taken in any order, are not the same
                    # as any keys, so create an new key.
                    n_axes += len(axes)
                    parsed[axes] = [(axes, key, construct, value, identity)]

            unique_axes.update(axes)

        if len(unique_axes) < n_axes:
            raise ValueError(
                "Can't find indices: Multiple constructs with incompatible "
                "domain axes"
            )

        for canonical_axes, axes_key_construct_value in parsed.items():
            axes, keys, constructs, points, identities = list(
                zip(*axes_key_construct_value)
            )

            n_items = len(constructs)
            n_axes = len(canonical_axes)

            if n_axes != 1:
                raise ValueError("TODO")

            if n_items > n_axes:
                raise ValueError(
                    "Can't specify the same axis more than once. Got: "
                    f"{identities}"
                )

            axis = axes[0][0]
            item = constructs[0]
            value = points[0]

            if item is None:
                raise ValueError(
                    "Can only specify 1-d metadata constructs from which "
                    f"to create indices. Got: {identities[0]!r}"
                )

            index = np.isin(item, np.asanyarray(value).astype(item.dtype))
            if np.ma.is_masked(index):
                index = index.filled(False)

            if not index.any():
                raise ValueError(
                    f"{value!r} does not match any {item!r} data values"
                )

            indices[axis] = index

        # Return indices tuple
        return tuple([indices[axis] for axis in self.get_data_axes()])

    @_inplace_enabled(default=False)
    def insert_dimension(
        self, axis, position=0, constructs=False, inplace=False
    ):
        """Expand the shape of the data array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `squeeze`, `transpose`, `unsqueeze`

        :Parameters:

            axis:
                Select the domain axis to insert, generally defined by that
                which would be selected by passing the given axis description
                to a call of the field construct's `domain_axis` method. For
                example, for a value of ``'time'``, the domain axis construct
                returned by ``f.domain_axis('time')`` is selected.

                If *axis* is `None` then a new domain axis construct
                will be created for the inserted dimension.

            position: `int`, optional
                Specify the position that the new axis will have in
                the data array. By default the new axis has position
                0, the slowest varying position. Negative integers
                counting from the last position are allowed.

            constructs: `bool`
                If True then also insert the new axis into all
                metadata constructs that don't already include it. By
                default, metadata constructs are not changed.

                .. versionadded:: (cfdm) 1.11.1.0

            {{inplace: `bool`, optional}}

        :Returns:

            `{{class}}` or `None`
                The field construct with expanded data, or `None` if the
                operation was in-place.

        **Examples**

        >>> f = {{package}}.example_field(0)
        >>> print(f)
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(latitude(5), longitude(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(8) = [22.5, ..., 337.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]
        >>> g = f.insert_dimension('time', 0)
        >>> print(g)
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(time(1), latitude(5), longitude(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(8) = [22.5, ..., 337.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]

        A previously non-existent size 1 axis must be created prior to
        insertion:

        >>> f.insert_dimension(None, 1, inplace=True)
        >>> print(f)
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(time(1), key%domainaxis3(1), latitude(5), longitude(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(8) = [22.5, ..., 337.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]

        """
        f = _inplace_enabled_define_and_cleanup(self)

        if axis is None:
            axis = f.set_construct(self._DomainAxis(1))
        else:
            axis, domain_axis = f.domain_axis(
                axis,
                item=True,
                default=ValueError("Can't identify a unique axis to insert"),
            )

            if domain_axis.get_size() != 1:
                raise ValueError(
                    f"Can only insert axis of size 1. Axis {axis!r} has size "
                    f"{domain_axis.get_size()}"
                )

        if position < 0:
            position = position + f.ndim + 1

        data_axes = f.get_data_axes(default=None)
        if data_axes is not None:
            data_axes0 = data_axes[:]
            if axis in data_axes:
                raise ValueError(
                    f"Can't insert a duplicate data array axis: {axis!r}"
                )

            data_axes = list(data_axes)
            data_axes.insert(position, axis)

        # Expand the dims in the field's data array
        super(Field, f).insert_dimension(position, inplace=True)

        # Update the axes
        if data_axes is not None:
            f.set_data_axes(data_axes)

        if constructs:
            if data_axes is None:
                data_axes0 = []
                position = 0

            for key, construct in f.constructs.filter_by_data(
                todict=True
            ).items():
                data = construct.get_data(
                    None, _units=False, _fill_value=False
                )
                if data is None:
                    continue

                construct_axes = list(f.get_data_axes(key))
                if axis in construct_axes:
                    continue

                # Find the position of the new axis
                c_position = position
                for a in data_axes0:
                    if a not in construct_axes:
                        c_position -= 1

                if c_position < 0:
                    c_position = 0

                # Expand the dims in the construct's data array
                construct.insert_dimension(c_position, inplace=True)

                # Update the construct axes
                construct_axes.insert(c_position, axis)
                f.set_data_axes(axes=construct_axes, key=key)

        return f

    def convert(self, *identity, full_domain=True, **filter_kwargs):
        """Convert a metadata construct into a new field construct.

        The new field construct has the properties and data of the
        metadata construct, and domain axis constructs corresponding
        to the data. By default it also contains other metadata
        constructs (such as dimension coordinate and coordinate
        reference constructs) that define its domain.

        Only metadata constructs that can have data may be converted
        and they can be converted even if they do not actually have
        any data. Constructs such as cell methods which cannot have
        data cannot be converted.

        The `{{package}}.read` function allows a field construct to be
        derived directly from a netCDF variable that corresponds to a
        metadata construct. In this case, the new field construct will
        have a domain limited to that which can be inferred from the
        corresponding netCDF variable - typically only domain axis and
        dimension coordinate constructs. This will usually result in a
        different field construct to that created with the `convert`
        method.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `{{package}}.read`

        :Parameters:

            identity: `str`, optional
                Convert the metadata construct with the given
                construct key.

            full_domain: `bool`, optional
                If False then only create domain axis constructs for
                the domain of the new field construct. By default as
                much of the domain as possible is copied to the new
                field construct.

            {{filter_kwargs: optional}} Also to configure the returned value.

                 .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Field`
                The new field construct.

        **Examples**

        >>> f = {{package}}.read('file.nc')[0]
        >>> print(f)
        Field: air_temperature (ncvar%ta)
        ---------------------------------
        Data            : air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K
        Cell methods    : grid_latitude(10): grid_longitude(9): mean where land (interval: 0.1 degrees) time(1): maximum
        Field ancils    : air_temperature standard_error(grid_latitude(10), grid_longitude(9)) = [[0.76, ..., 0.32]] K
        Dimension coords: atmosphere_hybrid_height_coordinate(1) = [1.5]
                        : grid_latitude(10) = [2.2, ..., -1.76] degrees
                        : grid_longitude(9) = [-4.7, ..., -1.18] degrees
                        : time(1) = [2019-01-01 00:00:00]
        Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[53.941, ..., 50.225]] degrees_N
                        : longitude(grid_longitude(9), grid_latitude(10)) = [[2.004, ..., 8.156]] degrees_E
                        : long_name:Grid latitude name(grid_latitude(10)) = [--, ..., kappa]
        Cell measures   : measure%area(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2
        Coord references: atmosphere_hybrid_height_coordinate
                        : rotated_latitude_longitude
        Domain ancils   : ncvar%a(atmosphere_hybrid_height_coordinate(1)) = [10.0] m
                        : ncvar%b(atmosphere_hybrid_height_coordinate(1)) = [20.0]
                        : surface_altitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 270.0]] m
        >>> x = f.convert('domainancillary2')
        >>> print(x)
        Field: surface_altitude (ncvar%surface_altitude)
        ------------------------------------------------
        Data            : surface_altitude(grid_latitude(10), grid_longitude(9)) m
        Dimension coords: grid_latitude(10) = [2.2, ..., -1.76] degrees
                        : grid_longitude(9) = [-4.7, ..., -1.18] degrees
        Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[53.941, ..., 50.225]] degrees_N
                        : longitude(grid_longitude(9), grid_latitude(10)) = [[2.004, ..., 8.156]] degrees_E
                        : long_name:Grid latitude name(grid_latitude(10)) = [--, ..., kappa]
        Cell measures   : measure%area(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2
        Coord references: rotated_latitude_longitude
        >>> y = f.convert('domainancillary2', full_domain=False)
        >>> print(y)
        Field: surface_altitude (ncvar%surface_altitude)
        ------------------------------------------------
        Data            : surface_altitude(grid_latitude(10), grid_longitude(9)) m

        """
        filter_kwargs.pop("item", None)
        key, c = self.construct(*identity, item=True, **filter_kwargs)
        if c is None:
            raise ValueError("Can't return zero constructs")

        if not hasattr(c, "has_data"):  # i.e. a construct that never has data
            raise ValueError("Can't convert a construct that cannot have data")

        # ------------------------------------------------------------
        # Create a new field with the properties and data from the
        # construct
        # ------------------------------------------------------------
        c = c.copy()
        data = c.del_data()

        f = type(self)(source=c, copy=False)

        # ------------------------------------------------------------
        # Add domain axes
        # ------------------------------------------------------------
        constructs_data_axes = self.constructs.data_axes()
        data_axes = constructs_data_axes.get(key)
        if data_axes is not None:
            domain_axes = self.domain_axes(todict=True)
            for domain_axis in data_axes:
                f.set_construct(
                    domain_axes[domain_axis], key=domain_axis, copy=True
                )

        # ------------------------------------------------------------
        # Set data axes
        # ------------------------------------------------------------
        if data_axes is not None:
            f.set_data(data, axes=data_axes)

        # ------------------------------------------------------------
        # Add a more complete domain
        # ------------------------------------------------------------
        if full_domain:
            for ccid, construct in self.constructs.filter_by_type(
                "dimension_coordinate",
                "auxiliary_coordinate",
                "cell_measure",
                "domain_topology",
                "cell_connectivity",
                todict=True,
            ).items():
                axes = constructs_data_axes.get(ccid)
                if axes is None:
                    continue

                if set(axes).issubset(data_axes):
                    f.set_construct(construct, key=ccid, axes=axes, copy=True)

            # Add coordinate references which span a subset of the item's
            # axes
            domain_ancillaries = self.domain_ancillaries(todict=True)

            for rcid, ref in self.coordinate_references(todict=True).items():
                new_coordinates = [
                    ccid
                    for ccid in ref.coordinates()
                    if set(constructs_data_axes[ccid]).issubset(data_axes)
                ]

                if not new_coordinates:
                    continue

                # Still here?
                ok = True
                for (
                    ccid
                ) in ref.coordinate_conversion.domain_ancillaries().values():
                    axes = constructs_data_axes[ccid]
                    if not set(axes).issubset(data_axes):
                        ok = False
                        break

                if ok:
                    ref = ref.copy()
                    ref.clear_coordinates()
                    ref.set_coordinates(new_coordinates)
                    f.set_construct(ref, key=rcid, copy=False)

                    # Copy domain ancillary constructs
                    for (
                        dakey
                    ) in (
                        ref.coordinate_conversion.domain_ancillaries().values()
                    ):
                        construct = domain_ancillaries.get(dakey)
                        if construct is not None:
                            axes = constructs_data_axes.get(dakey)
                            f.set_construct(
                                construct, key=dakey, axes=axes, copy=True
                            )

        return f

    @_inplace_enabled(default=False)
    def persist(self, metadata=False, inplace=False):
        """Persist the data into memory.

        This turns the underlying lazy dask array into an equivalent
        chunked dask array, but now with the results fully computed
        and in memory. This can avoid the expense of re-reading the
        data from disk, or re-computing it, when the data is accessed
        on multiple occasions.

        **Performance**

        `persist` causes delayed operations to be computed.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `persist_metadata`, `array`, `datetime_array`,
                     `{{package}}.Data.persist`

        :Parameters:

            metadata: `bool`
                If True then also persist the metadata constructs. By
                default, metadata constructs are not changed.

            {{inplace: `bool`, optional}}

        :Returns:

            `Field` or `None`
                The field construct with persisted data. If the
                operation was in-place then `None` is returned.

        """
        f = _inplace_enabled_define_and_cleanup(self)

        super(Field, f).persist(inplace=True)
        if metadata:
            f.persist_metadata(inplace=True)

        return f

    @_inplace_enabled(default=False)
    def persist_metadata(self, inplace=False):
        """Persist the data of metadata constructs into memory.

        {{persist description}}

        **Performance**

        `persist_metadata` causes delayed operations to be computed.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `persist`, `array`, `datetime_array`,
                     `dask.array.Array.persist`

        :Parameters:

            {{inplace: `bool`, optional}}

        :Returns:

            `Field` or `None`
                The field construct with persisted metadata. If the
                operation was in-place then `None` is returned.

        """
        f = _inplace_enabled_define_and_cleanup(self)

        for c in f.constructs.filter_by_data(todict=True).values():
            c.persist(inplace=True)

        return f

    def replace_directory(
        self,
        old=None,
        new=None,
        normalise=False,
        common=False,
        constructs=True,
    ):
        """Replace a file directory in-place.

        Every file in *old_directory* that is referenced by the data
        is redefined to be in *new*.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `file_directories`, `get_filenames`

        :Parameters:

            {{replace old: `str` or `None`, optional}}

            {{replace new: `str` or `None`, optional}}

            {{replace normalise: `bool`, optional}}

            common: `bool`, optional
                If True the base directory structure that is common to
                all files with *new*.

            constructs: `bool`, optional
                If True (the default) then add also the directory to
                the data of metadata constructs. If False then don't
                do this.

        :Returns:

            `None`

        **Examples**

        >>> d.get_filenames()
        {'/data/file1.nc', '/home/file2.nc'}
        >>> d.replace_directory('/data', '/new/data/path/')
        '/new/data/path'
        >>> d.get_filenames()
        {'/new/data/path/file1.nc', '/home/file2.nc'}

        """
        super().replace_directory(
            old=old, new=new, normalise=normalise, common=common
        )
        if constructs:
            for c in self.constructs.filter_by_data(todict=True).values():
                c.replace_directory(
                    old=old, new=new, normalise=normalise, common=common
                )

    def nc_hdf5_chunksizes(self, todict=False):
        """Get the HDF5 chunking strategy for the data.

        Deprecated at version 1.12.2.0 and is no longer
        available. Use `nc_dataset_chunksizes` instead.

        .. versionadded:: (cfdm) 1.11.2.0

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "nc_hdf5_chunksizes",
            "Use `nc_dataset_chunksizes` instead.",
            version="1.12.2.0",
            removed_at="5.0.0",
        )  # pragma: no cover

    def nc_dataset_chunksizes(self, todict=False):
        """Get the dataset chunking strategy for the data.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `nc_clear_dataset_chunksizes`,
                     `nc_set_dataset_chunksizes`, `{{package}}.read`,
                     `{{package}}.write`

        :Parameters:

            {{chunk todict: `bool`, optional}}

        :Returns:

            {{Returns nc_dataset_chunksizes}}

        """
        chunksizes = super().nc_dataset_chunksizes()

        if todict:
            if not isinstance(chunksizes, tuple):
                raise ValueError(
                    "Can only set todict=True when the HDF chunking strategy "
                    "comprises the maximum number of array elements in a "
                    f"chunk along each data axis. Got: {chunksizes!r}"
                )

            # Convert a tuple to a dict
            data_axes = self.get_data_axes()
            domain_axis_identity = self.constructs.domain_axis_identity
            c = {
                domain_axis_identity(axis): 1
                for axis in self.domain_axes(todict=True)
                if axis not in data_axes
            }

            for axis, value in zip(data_axes, chunksizes):
                c[domain_axis_identity(axis)] = value

            chunksizes = c

        return chunksizes

    def nc_clear_hdf5_chunksizes(self, constructs=False):
        """Clear the HDF5 chunking strategy.

        Deprecated at version 1.12.2.0 and is no longer
        available. Use `nc_clear_dataset_chunksizes` instead.

        .. versionadded:: (cfdm) 1.11.2.0

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "nc_clear_hdf5_chunksizes",
            "Use `nc_clear_dataset_chunksizes` instead.",
            version="1.12.2.0",
            removed_at="5.0.0",
        )  # pragma: no cover

    def nc_clear_dataset_chunksizes(self, constructs=False):
        """Clear the dataset chunking strategy.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `nc_dataset_chunksizes`,
                     `nc_set_hdataset_chunksizes`, `{{package}}.read`,
                     `{{package}}.write`

        :Parameters:

            constructs: `dict` or `bool`, optional
                Also clear the dataset chunking strategy from selected
                metadata constructs. The chunking strategies of
                unselected metadata constructs are unchanged.

                If *constructs* is a `dict` then the selected metadata
                constructs are those that would be returned by
                ``f.constructs.filter(**constructs,
                filter_by_data=True)``. Note that an empty dictionary
                will therefore select all metadata constructs that
                have data. See `~Constructs.filter` for details.

                For *constructs* being anything other than a
                dictionary, if it evaluates to True then all metadata
                constructs that have data are selected, and if it
                evaluates to False (the default) then no metadata
                are constructs selected.

        :Returns:

            `None` or `str` or `int` or `tuple` of `int`
                The chunking strategy prior to being cleared, as would
                be returned by `nc_dataset_chunksizes`.

        """
        # Clear dataset chunksizes from the metadata
        if isinstance(constructs, dict):
            constructs = constructs.copy()
        elif constructs:
            constructs = {}
        else:
            constructs = None

        if constructs is not None:
            constructs["filter_by_data"] = True
            constructs["todict"] = True
            for key, construct in self.constructs.filter(**constructs).items():
                construct.nc_clear_dataset_chunksizes()

        return super().nc_clear_dataset_chunksizes()

    def nc_set_hdf5_chunksizes(
        self,
        chunksizes,
        ignore=False,
        constructs=False,
        **filter_kwargs,
    ):
        """Set the HDF5 chunking strategy.

        Deprecated at version 1.12.2.0 and is no longer
        available. Use `nc_set_dataset_chunksizes` instead.

        .. versionadded:: (cfdm) 1.11.2.0

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "nc_set_hdf5_chunksizes",
            "Use `nc_set_dataset_chunksizes` instead.",
            version="1.12.2.0",
            removed_at="5.0.0",
        )  # pragma: no cover

    def nc_set_dataset_chunksizes(
        self,
        chunksizes,
        ignore=False,
        constructs=False,
        **filter_kwargs,
    ):
        """Set the dataset chunking strategy.

        .. seealso:: `nc_dataset_chunksizes`,
                     `nc_clear_dataset_chunksizes`,
                     `{{package}}.read`, `{{package}}.write`

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            {{chunk chunksizes}}

                  Each dictionary key, ``k``, specifies the unique
                  axis that would be identified by ``f.domain_axis(k,
                  **filter_kwargs)``, and it is allowed to specify a
                  domain axis that is not spanned by the data
                  array. See `domain_axis` for details.

            constructs: `dict` or `bool`, optional
                Also apply the dataset chunking strategy of the field
                construct data to the applicable axes of selected
                metadata constructs. The chunking strategies of
                unselected metadata constructs are unchanged.

                If *constructs* is a `dict` then the selected metadata
                constructs are those that would be returned by
                ``f.constructs.filter(**constructs,
                filter_by_data=True)``. Note that an empty dictionary
                will therefore select all metadata constructs that
                have data. See `~Constructs.filter` for details.

                For *constructs* being anything other than a
                dictionary, if it evaluates to True then all metadata
                constructs that have data are selected, and if it
                evaluates to False (the default) then no metadata
                constructs selected.

            ignore: `bool`, optional
                If True and *chunksizes* is a `dict` then ignore any
                dictionary keys that do not identify a unique axis of
                the field construct's data. If False, the default,
                then an exception will be raised when such keys are
                encountered.

            filter_kwargs: optional
                When *chunksizes* is a `dict`, provide additional
                keyword arguments to `domain_axis` to customise axis
                selection criteria.

        :Returns:

            `None`

        **Examples**

        >>> f = {{package}}.example_field(0)
        >>> print(f)
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(latitude(5), longitude(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(8) = [22.5, ..., 337.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]
        >>> f.shape
        (5, 8)
        >>> print(f.nc_dataset_chunksizes())
        None
        >>> f.nc_set_dataset_chunksizes({'latitude': 1})
        >>> f.nc_dataset_chunksizes()
        (1, 8)
        >>> f.nc_set_dataset_chunksizes({'longitude': 7})
        >>> f.nc_dataset_chunksizes()
        (1, 7)
        >>> f.nc_set_dataset_chunksizes({'latitude': 4, 'longitude': 2})
        >>> f.nc_dataset_chunksizes()
        (4, 2)
        >>> f.nc_set_dataset_chunksizes([1, 7])
        >>> f.nc_dataset_chunksizes()
        (1, 7)
        >>> f.nc_set_dataset_chunksizes(64)
        >>> f.nc_dataset_chunksizes()
        64
        >>> f.nc_set_dataset_chunksizes('128 B')
        >>> f.nc_dataset_chunksizes()
        128
        >>> f.nc_set_dataset_chunksizes('contiguous')
        >>> f.nc_dataset_chunksizes()
        'contiguous'
        >>> f.nc_set_dataset_chunksizes(None)
        >>> print(f.nc_dataset_chunksizes())
        None

        >>> f.nc_set_dataset_chunksizes([-1, None])
        >>> f.nc_dataset_chunksizes()
        (5, 8)
        >>> f.nc_set_dataset_chunksizes({'latitude': 999})
        >>> f.nc_dataset_chunksizes()
        (5, 8)

        >>> f.nc_set_dataset_chunksizes({'latitude': 4, 'time': 1})
        >>> f.nc_dataset_chunksizes()
        (4, 8)
        >>> print(f.dimension_coordinate('time').nc_dataset_chunksizes())
        None
        >>> print(f.dimension_coordinate('latitude').nc_dataset_chunksizes())
        None
        >>> print(f.dimension_coordinate('longitude').nc_dataset_chunksizes())
        None

        >>> f.nc_set_dataset_chunksizes({'latitude': 4, 'time': 1}, constructs=True)
        >>> f.dimension_coordinate('time').nc_dataset_chunksizes()
        (1,)
        >>> f.dimension_coordinate('latitude').nc_dataset_chunksizes()
        (4,)
        >>> f.dimension_coordinate('longitude').nc_dataset_chunksizes()
        (8,)
        >>> f.nc_set_dataset_chunksizes('contiguous', constructs={'filter_by_axis': ('longitude',)})
        >>> f.nc_dataset_chunksizes()
        'contiguous'
         >>> f.dimension_coordinate('time').nc_dataset_chunksizes()
        (1,)
        >>> f.dimension_coordinate('latitude').nc_dataset_chunksizes()
        (4,)
        >>> f.dimension_coordinate('longitude').nc_dataset_chunksizes()
        'contiguous'

        >>> f.nc_set_dataset_chunksizes({'height': 19, 'latitude': 3})
        Traceback
            ...
        ValueError: Can't find unique 'height' axis. Consider setting ignore=True
        >>> f.nc_set_dataset_chunksizes({'height': 19, 'latitude': 3}, ignore=True)
        >>> f.nc_dataset_chunksizes(todict=True)
        {'time': 1, 'latitude': 3, 'longitude': 8}

        """
        data_axes = self.get_data_axes()

        chunksizes_keys = {}
        if isinstance(chunksizes, dict):
            # 'chunksizes' is a dictionary: Create a dictionary keyed
            # by integer axis positions, and one keyed by domain axis
            # identifiers.
            chunksizes_positions = {}
            for identity, value in chunksizes.items():
                axis = self.domain_axis(identity, key=True, default=None)
                if axis is None:
                    if ignore:
                        continue

                    raise ValueError(
                        f"Can't find unique {identity!r} axis. "
                        "Consider setting ignore=True"
                    )

                chunksizes_keys[axis] = value
                try:
                    chunksizes_positions[data_axes.index(axis)] = value
                except ValueError:
                    pass

            chunksizes = chunksizes_positions
        elif constructs and not (
            chunksizes is None or isinstance(chunksizes, (int, str))
        ):
            # 'chunksizes' is not None, not an integer, nor a string;
            # so it must be a sequence => Create a dictionary keyed by
            # domain axis identifiers for use with the metadata
            # constructs.
            chunksizes_keys = {
                data_axes[n]: value for n, value in enumerate(chunksizes)
            }

        super().nc_set_dataset_chunksizes(chunksizes)

        # Set dataset chunksizes on the metadata
        if isinstance(constructs, dict):
            constructs = constructs.copy()
        elif constructs:
            constructs = {}
        else:
            constructs = None

        if constructs is not None:
            constructs["filter_by_data"] = True
            constructs["todict"] = True
            for key, construct in self.constructs.filter(**constructs).items():
                if chunksizes_keys:
                    construct_axes = self.get_data_axes(key)
                    c = {
                        n: chunksizes_keys[axis]
                        for n, axis in enumerate(construct_axes)
                        if axis in chunksizes_keys
                    }
                else:
                    c = chunksizes

                construct.nc_set_dataset_chunksizes(c)

    @_inplace_enabled(default=False)
    def squeeze(self, axes=None, inplace=False):
        """Remove size 1 axes from the data.

        By default all size one axes are removed, but particular size
        one axes may be selected for removal.

        Squeezed domain axis constructs are not removed from the metadata
        constructs, nor from the domain of the field construct.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `insert_dimension`, `transpose`, `unsqueeze`

        :Parameters:

            axes:
                Select the domain axes to squeeze, defined by the
                domain axes that would be selected by passing each
                given axis description to a call of the field
                construct's `domain_axis` method. For example, for a
                value of ``'time'``, the domain axis construct
                returned by ``f.domain_axis('time')`` is selected.

                If *axes* is `None` (the default) then all size 1 axes
                are removed.

            {{inplace: `bool`, optional}}

        :Returns:

            `{{class}}` or `None`
                The field construct with squeezed data, or `None` if the
                operation was in-place.

        **Examples**

        >>> g = f.squeeze()
        >>> g = f.squeeze('time')
        >>> g = f.squeeze(1)
        >>> g = f.squeeze(['time', 1, 'dim2'])
        >>> f.squeeze(['dim2'], inplace=True)

        """
        f = _inplace_enabled_define_and_cleanup(self)

        data_axes = f.get_data_axes(default=None)
        if data_axes is None:
            return f

        if axes is None:
            domain_axes = f.domain_axes(todict=True)
            axes = [
                axis
                for axis in data_axes
                if domain_axes[axis].get_size(None) == 1
            ]
        else:
            if isinstance(axes, (str, int)):
                axes = (axes,)

            axes = [f.domain_axis(x, key=True) for x in axes]
            axes = set(axes).intersection(data_axes)

        iaxes = [data_axes.index(axis) for axis in axes]

        new_data_axes = [
            data_axes[i] for i in range(f.data.ndim) if i not in iaxes
        ]

        # Squeeze the field's data array
        super(Field, f).squeeze(iaxes, inplace=True)

        if data_axes is not None:
            f.set_data_axes(new_data_axes)

        return f

    @_inplace_enabled(default=False)
    def transpose(self, axes=None, constructs=False, inplace=False):
        """Permute the axes of the data array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `insert_dimension`, `squeeze`, `unsqueeze`

        :Parameters:

            axes: sequence or `None`
                Select the domain axis order, defined by the domain
                axes that would be selected by passing each given axis
                description to a call of the field construct's
                `domain_axis` method. For example, for a value of
                ``'time'``, the domain axis construct returned by
                ``f.domain_axis('time')`` is selected.

                Each dimension of the field construct's data must be
                provided, or if *axes* is `None` (the default) then
                the axis order is reversed.

            constructs: `bool`
                If True then transpose the metadata constructs to have
                the same relative domain axis order as the data of
                transposed field construct. By default, metadata
                constructs are not changed.

            {{inplace: `bool`, optional}}

        :Returns:

            `Field` or `None`
                The field construct with permuted data axes. If the
                operation was in-place then `None` is returned.

        **Examples**

        >>> f.data.shape
        (19, 73, 96)
        >>> f.transpose().data.shape
        (96, 73, 19)
        >>> f.transpose([1, 0, 2]).data.shape
        (73, 19, 96)
        >>> f.transpose(inplace=True)
        >>> f.data.shape
        (96, 19, 73)

        """
        f = _inplace_enabled_define_and_cleanup(self)

        if axes is None:
            iaxes = tuple(range(f.data.ndim - 1, -1, -1))
        else:
            data_axes = self.get_data_axes(default=())
            if isinstance(axes, (str, int)):
                axes = (axes,)

            axes2 = [f.domain_axis(axis, key=True) for axis in axes]

            if sorted(axes2) != sorted(data_axes):
                raise ValueError(
                    f"Can't transpose {self.__class__.__name__}: "
                    f"Bad axis specification: {axes!r}"
                )

            iaxes = [data_axes.index(axis) for axis in axes2]

        data_axes = f.get_data_axes(default=None)

        # Transpose the field's data array
        super(Field, f).transpose(iaxes, inplace=True)

        if data_axes is not None:
            new_data_axes = [data_axes[i] for i in iaxes]
            f.set_data_axes(new_data_axes)

        if constructs:
            for key, construct in f.constructs.filter_by_data(
                todict=True
            ).items():
                data = construct.get_data(
                    None, _units=False, _fill_value=False
                )
                if data is None:
                    continue

                if data.ndim < 2:
                    # No need to transpose 1-d constructs
                    continue

                construct_axes = f.get_data_axes(key)

                new_construct_axes = [
                    axis for axis in new_data_axes if axis in construct_axes
                ]

                for i, axis in enumerate(construct_axes):
                    if axis not in new_construct_axes:
                        new_construct_axes.insert(i, axis)

                iaxes = [
                    construct_axes.index(axis) for axis in new_construct_axes
                ]

                # Transpose the construct
                construct.transpose(iaxes, inplace=True)

                f.set_data_axes(axes=new_construct_axes, key=key)

        return f

    @_inplace_enabled(default=False)
    def uncompress(self, inplace=False):
        """Uncompress the field construct.

        Compression saves space by identifying and removing unwanted
        missing data. Such compression techniques store the data more
        efficiently and result in no precision loss. Whether or not
        the construct is compressed does not alter its functionality
        nor external appearance.

        The field construct data is uncompressed, along with any
        applicable metadata constructs.

        A field construct that is already uncompressed will be returned
        uncompressed.

        The compression type can be discovered by the
        `~Data.get_compression_type` method  of the data:

        The following types of compression can be uncompressed:

          * Compression type ``'ragged_contiguous'``: Contiguous ragged
            array representation for DSG "point", "timeSeries",
            "trajectory" or "profile" features.

          * Compression type ``'ragged_indexed'``: Indexed ragged array
            representation for DSG "point", "timeSeries", "trajectory", or
            "profile" features.

          * Compression type ``'ragged_indexed_contiguous'``: Indexed
            contiguous ragged array representation for DSG
            "timeSeriesProfile", or "trajectoryProfile" features.

          * Compression type ``'gathered'``: Compression by gathering over
            any subset of the field construct data dimensions.

        .. versionadded:: (cfdm) 1.7.11

        .. seealso:: `compress`

        :Parameters:

            {{inplace: `bool`, optional}}

        :Returns:

            `Field` or `None`
                The uncompressed field construct, or `None` if the
                operation was in-place.

        **Examples**

        >>> f.data.get_compression_type()
        'ragged contiguous'
        >>> g = f.uncompress()
        >>> g.data.get_compression_type()
        ''
        >>> g.equals(f)
        True

        """
        f = _inplace_enabled_define_and_cleanup(self)
        super(Field, f).uncompress(inplace=True)

        # Uncompress the domain
        f.domain.uncompress(inplace=True)

        # Uncompress any field ancillaries
        for c in f.constructs.filter_by_type(
            "field_ancillary", todict=True
        ).values():
            c.uncompress(inplace=True)

        return f

    @_inplace_enabled(default=False)
    def unsqueeze(self, inplace=None):
        """Insert size 1 axes into the data array.

        All size 1 domain axes which are not spanned by the field
        construct's data are inserted.

        The axes are inserted into the slowest varying data array positions.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `insert_dimension`, `squeeze`, `transpose`

        :Parameters:

            {{inplace: `bool`, optional}}

        :Returns:

            `Field` or `None`
                The field construct with size-1 axes inserted in its
                data, or `None` if the operation was in-place.

        **Examples**

        >>> f = {{package}}.example_field(0)
        >>> print(f)
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(latitude(5), longitude(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(8) = [22.5, ..., 337.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]
        >>> g = f.unsqueeze()
        >>> print(g)
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(time(1), latitude(5), longitude(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(8) = [22.5, ..., 337.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]

        """
        f = _inplace_enabled_define_and_cleanup(self)

        size_1_axes = self.domain_axes(filter_by_size=(1,), todict=True)
        for axis in set(size_1_axes).difference(self.get_data_axes()):
            f.insert_dimension(axis, position=0, inplace=True)

        return f
