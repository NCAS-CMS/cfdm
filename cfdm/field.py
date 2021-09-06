import logging

from . import Constructs, Count, Domain, Index, List, core, mixin
from .constants import masked as cfdm_masked
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

logger = logging.getLogger(__name__)


class Field(
    mixin.NetCDFVariable,
    mixin.NetCDFGeometry,
    mixin.NetCDFGlobalAttributes,
    mixin.NetCDFGroupAttributes,
    mixin.NetCDFComponents,
    mixin.NetCDFUnreferenced,
    mixin.FieldDomain,
    mixin.PropertiesData,
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
        """Store component classes.

        .. note:: If a child class requires a different component
        classes           than the ones defined here, then they must be
        redefined           in the child class.

        """
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        instance._Domain = Domain
        instance._RaggedContiguousArray = RaggedContiguousArray
        instance._RaggedIndexedArray = RaggedIndexedArray
        instance._RaggedIndexedContiguousArray = RaggedIndexedContiguousArray
        instance._GatheredArray = GatheredArray
        instance._Count = Count
        instance._Index = Index
        instance._List = List
        return instance

    def __init__(
        self, properties=None, source=None, copy=True, _use_data=True
    ):
        """**Initialisation**

        :Parameters:

            {{init properties: `dict`, optional}}

                *Parameter example:*
                  ``properties={'standard_name': 'air_temperature'}``

            source: optional
                Initialise the properties, data and metadata constructs
                from those of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        # Initialise the new field with attributes and CF properties
        core.Field.__init__(
            self,
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

        **Examples:**

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
        data = self.get_data(_fill_value=False)

        indices = data._parse_indices(indices)
        indices = tuple(indices)

        new = self.copy()  # data=False)

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

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    def field_ancillaries(self, *identities, **filter_kwargs):
        """Return field ancillary constructs.

        ``f.field_ancillaries(*identities, **filter_kwargs)`` is
        equivalent to
        ``f.constructs.filter(filter_by_type=["field_ancillary"],
        filter_by_identity=identities, **filter_kwargs)``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

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

        **Examples:**

        >>> print(f.field_ancillaries())
        Constructs:
        {}

        >>> print(f.field_ancillaries())
        Constructs:
        {'cellmethod1': <{{repr}}CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
         'cellmethod0': <{{repr}}CellMethod: domainaxis3: maximum>}

        >>> f.cell_methods.ordered()
        OrderedDict([('cellmethod0', <{{repr}}CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>),
                     ('cellmethod1', <{{repr}}CellMethod: domainaxis3: maximum>)])

        """
        return self._filter_interface(
            ("field_ancillary",),
            "field_ancillaries",
            identities,
            **filter_kwargs,
        )

    def cell_methods(self, *identities, **filter_kwargs):
        """Return cell method constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

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

        **Examples:**

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
            filter_kwargs = {
                "filter_by_key": keys,
                "todict": filter_kwargs.pop("todict", False),
            }

        return self._filter_interface(
            ("cell_method",), "cell_method", identities, **filter_kwargs
        )

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
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

        **Examples:**

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

        **Examples:**

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
            #            out.append((axis,))
            out.add(axis)

        return out

    #        out = []
    #
    #        domain_axes = None
    #
    #        for key, cm in self.cell_methods(todict=True).items():
    #            qualifiers = cm.qualifiers()
    #            if not ("within" in qualifiers or "over" in qualifiers):
    #                continue
    #
    #            axes = cm.get_axes(default=())
    #            if len(axes) != 1:
    #                continue
    #
    #            domain_axes = self.domain_axes(cached=domain_axes, todict=True)
    #
    #            axis = axes[0]
    #            if axis not in domain_axes:
    #                continue
    #
    #            # Still here? Then this axis is a climatological time axis
    #            out.append((axis,))
    #
    #        return out

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

        **Examples:**

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
                size=data.size,
                ndim=data.ndim,
                count_variable=count_variable,
            )

        def _RaggedIndexedArray(self, compressed_data, data, index_variable):
            return self._RaggedIndexedArray(
                compressed_data,
                shape=data.shape,
                size=data.size,
                ndim=data.ndim,
                index_variable=index_variable,
            )

        def _RaggedIndexedContiguousArray(
            self, compressed_data, data, count_variable, index_variable
        ):
            return self._RaggedIndexedContiguousArray(
                compressed_data,
                shape=data.shape,
                size=data.size,
                ndim=data.ndim,
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

            count = []
            for d in flattened_data:
                last = d.size
                for i in d[::-1]:
                    if i is not cfdm_masked:
                        break
                    else:
                        last -= 1

                count.append(last)

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

        **Examples:**

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
        field.set_properties({'Conventions': 'CF-1.9', 'project': 'research', 'standard_name': 'specific_humidity', 'units': '1'})
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
            field.set_properties({'Conventions': 'CF-1.9', 'project': 'research', 'standard_name': 'specific_humidity', 'units': '1'})
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

        out = super().creation_commands(
            representative_data=representative_data,
            indent=0,
            namespace=namespace,
            string=False,
            name=name,
            data_name=data_name,
            header=header,
        )

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
                indent=0,
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
                    indent=0,
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
                    indent=0,
                    string=False,
                    name="c",
                    header=header,
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
    def dump(self, display=True, _level=0, _title=None):
        """A full description of the field construct.

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
        data = self.get_data(None)
        if data is not None:
            x = [axis_to_name[axis] for axis in self.get_data_axes(default=())]

            string.append("")
            string.append(f"{indent0}Data({', '.join(x)}) = {data}")
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

    def get_data_axes(self, key=None, default=ValueError()):
        """Gets the keys of the axes spanned by the construct data.

        Specifically, returns the keys of the domain axis constructs
        spanned by the data of the field or of a metadata construct.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_data_axes`, `get_data`, `set_data_axes`

        :Parameters:

            key: `str`, optional
                Specify a metadata construct, instead of the field
                construct.

                *Parameter example:*
                  ``key='auxiliarycoordinate0'``

            default: optional
                Return the value of the *default* parameter if the data
                axes have not been set.

                {{default Exception}}

        :Returns:

            `tuple`
                The keys of the domain axis constructs spanned by the
                data.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> f.get_data_axes()
        ('domainaxis0', 'domainaxis1')
        >>> f.get_data_axes(key='dimensioncoordinate2')
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
        if key is not None:
            return super().get_data_axes(key, default=default)

        try:
            return self._get_component("data_axes")
        except ValueError:
            return self._default(
                default,
                "{!r} has no data axes".format(self.__class__.__name__),
            )

    def get_domain(self):
        """Return the domain.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `domain`

        :Returns:

            `Domain`
                 The domain.

        **Examples:**

        >>> d = f.get_domain()

        """
        domain = self._Domain.fromconstructs(self.constructs)

        # Set climatological time axes for the domain
        climatological_time_axes = self.climatological_time_axes()
        if climatological_time_axes:
            coordinates = self.coordinates
            for key, c in coordinates.items():
                axes = self.get_data_axes(key, default=())
                if len(axes) == 1 and axes[0] in climatological_time_axes:
                    c.set_climatology(True)

        return domain

    def get_filenames(self):
        """Return the names of the files containing the data.

        The names of the files containing the data of the field
        constructs and of any metadata constructs are returned.

        :Returns:

            `set`
                The file names in normalised, absolute form. If all of
                the data are in memory then an empty `set` is
                returned.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> {{package}}.write(f, 'temp_file.nc')
        >>> g = {{package}}.read('temp_file.nc')[0]
        >>> g.get_filenames()
        {'temp_file.nc'}

        """
        out = super().get_filenames()

        for c in self.constructs.filter_by_data(todict=True).values():
            out.update(c.get_filenames())

        return out

    #    def has_geometry(self):
    #        """Whether any coordinate constructs have cell geometries.
    #
    #        .. versionadded:: (cfdm) 1.8.7.0
    #
    #        :Returns:
    #
    #            `bool`
    #                Whether or not there is a geometry type on any coordinate
    #                construct.
    #
    #        **Examples:**
    #
    #        >>> f = {{package}}.Field()
    #        >>> f.has_geometry()
    #        False
    #
    #        """
    #        for c in self.coordinates(todict=True).values():
    #            if c.has_geometry():
    #                return True
    #
    #        return False

    @_inplace_enabled(default=False)
    def insert_dimension(self, axis, position=0, inplace=False):
        """Expand the shape of the data array.

        Inserts a new size 1 axis, corresponding to an existing domain
        axis construct, into the data array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `squeeze`, `transpose`

        :Parameters:

            axis: `str`
                The identifier of the domain axis construct
                corresponding to the inserted axis.

                *Parameter example:*
                  ``axis='domainaxis2'``

            position: `int`, optional
                Specify the position that the new axis will have in
                the data array. By default the new axis has position
                0, the slowest varying position. Negative integers
                counting from the last position are allowed.

                *Parameter example:*
                  ``position=2``

                *Parameter example:*
                  ``position=-1``

            {{inplace: `bool`, optional}}

        :Returns:

            `Field` or `None`
                The new field construct with expanded data axes. If
                the operation was in-place then `None` is returned.

        **Examples:**

        >>> f.data.shape
        (19, 73, 96)
        >>> f.insert_dimension('domainaxis3').data.shape
        (1, 96, 73, 19)
        >>> f.insert_dimension('domainaxis3', position=3).data.shape
        (19, 73, 96, 1)
        >>> f.insert_dimension('domainaxis3', position=-1, inplace=True)
        (19, 73, 1, 96)
        >>> f.data.shape
        (19, 73, 1, 96)

        """
        f = _inplace_enabled_define_and_cleanup(self)

        domain_axis = f.domain_axes(todict=True).get(axis)
        if domain_axis is None:
            raise ValueError(f"Can't insert non-existent domain axis: {axis}")

        if domain_axis.get_size() != 1:
            raise ValueError(
                f"Can only insert axis of size 1. Axis {axis!r} has size "
                f"{domain_axis.get_size()}"
            )

        data_axes = f.get_data_axes(default=None)
        if data_axes is not None:
            if axis in data_axes:
                raise ValueError(
                    f"Can't insert a duplicate data array axis: {axis!r}"
                )

            data_axes = list(data_axes)
            data_axes.insert(position, axis)

        # Expand the dims in the field's data array
        super(Field, f).insert_dimension(position, inplace=True)

        if data_axes is not None:
            f.set_data_axes(data_axes)

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

        **Examples:**

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
        key, c = self.construct_item(*identity, **filter_kwargs)
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
    def squeeze(self, axes=None, inplace=False):
        """Remove size one axes from the data.

        By default all size one axes are removed, but particular size
        one axes may be selected for removal.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `insert_dimension`, `transpose`

        :Parameters:

            axes: (sequence of) `int`, optional
                The positions of the size one axes to be removed. By
                default all size one axes are removed.

                {{axes int examples}}

            {{inplace: `bool`, optional}}

        :Returns:

            `Field` or `None`
                The field construct with removed data axes. If the
                operation was in-place then `None` is returned.

        **Examples:**

        >>> f.data.shape
        (1, 73, 1, 96)
        >>> f.squeeze().data.shape
        (73, 96)
        >>> f.squeeze(0).data.shape
        (73, 1, 96)
        >>> f.squeeze([-3, 2], inplace=True)
        >>> f.data.shape
        (73, 96)

        """
        f = _inplace_enabled_define_and_cleanup(self)

        if axes is None:
            iaxes = [i for i, n in enumerate(f.data.shape) if n == 1]
        else:
            try:
                iaxes = f.data._parse_axes(axes)
            except ValueError as error:
                raise ValueError(f"Can't squeeze data: {error}")

        data_axes = f.get_data_axes(default=None)
        if data_axes is not None:
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

        .. seealso:: `insert_dimension`, `squeeze`

        :Parameters:

            axes: (sequence of) `int`, optional
                The new axis order. By default the order is reversed.

                {{axes int examples}}

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

        **Examples:**

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

        try:
            iaxes = f.data._parse_axes(axes)
        except ValueError as error:
            raise ValueError(f"Can't transpose data: {error}")

        if iaxes is None:
            iaxes = tuple(range(f.data.ndim - 1, -1, -1))

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
        efficiently and result in no precision loss.

        The field construct data is uncompressed, along with any
        applicable metadata constructs.

        Whether or not the construct is compressed does not alter its
        functionality nor external appearance.

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

        **Examples:**

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

        for c in f.constructs.filter_by_data(todict=True).values():
            c.uncompress(inplace=True)

        return f
