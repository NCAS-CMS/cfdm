"""Define docstring substitutions.

Text to be replaced is specified as a key in the returned dictionary,
with the replacement text defined by the corresponding value.

Special docstring substitutions, as defined by a class's
`_docstring_special_substitutions` method, may be used in the
replacement text, and will be substituted as usual.

Replacement text may not contain other non-special substitutions.

Keys must be a `str` or `re.Pattern` object:

* If a key is a `str` then the corresponding value must be a string.

* If a key is a `re.Pattern` object then the corresponding value must
  be a string or a callable, as accepted by the `re.Pattern.sub`
  method.

.. versionaddedd:: (cfdm) 1.8.7.0

"""


_docstring_substitution_definitions = {
    # ----------------------------------------------------------------
    # General substitutions (not indent-dependent)
    # ----------------------------------------------------------------
    #
    # ----------------------------------------------------------------
    # Class description substitutions (1 level of indentation)
    # ----------------------------------------------------------------
    # netCDF variable
    "{{netCDF variable}}": """The netCDF variable name may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_del_variable`, and
    `nc_has_variable` methods.

    The netCDF variable group structure may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_variable_groups`,
    `nc_clear_variable_groups`, and `nc_set_variable_groups`
    methods.""",
    # netCDF global attributes
    "{{netCDF global attributes}}": """The selection of properties to be written as netCDF global
    attributes may be accessed with the `nc_global_attributes`,
    `nc_clear_global_attributes`, and `nc_set_global_attribute`
    methods.""",
    # netCDF group attributes
    "{{netCDF group attributes}}": """The netCDF group attributes may be accessed with the
    `nc_group_attributes`, `nc_clear_group_attributes`,
    `nc_set_group_attribute`, and `nc_set_group_attributes` methods.""",
    # netCDF geometry group
    "{{netCDF geometry group}}": """The netCDF geometry variable name and group structure may be
    accessed with the `nc_set_geometry_variable`,
    `nc_get_geometry_variable`, `nc_geometry_variable_groups`,
    `nc_clear_variable_groups`, and `nc_set_geometry_variable_groups`
    methods.""",
    # netCDF UGRID node coordinate
    "{{netCDF UGRID node coordinate}}": """The netCDF UGRID node coordinate variable name may be accessed
    with the `nc_set_node_coordinate_variable`,
    `nc_get_node_coordinate_variable`,
    `nc_del_node_coordinate_variable`, and
    `nc_has_node_coordinate_variable` methods.

    The netCDF UGRID node coordinate variable group structure may be
    accessed with the `nc_set_node_coordinate_variable`,
    `nc_get_node_coordinate_variable`,
    `nc_variable_node_coordinate_groups`,
    `nc_clear_node_coordinate_variable_groups`, and
    `nc_set_node_coordinate_variable_groups` methods.""",
    # ----------------------------------------------------------------
    # Method description substitutions (2 levels of indentation)
    # ----------------------------------------------------------------
    # equals tolerance
    "{{equals tolerance}}": """Two real numbers ``x`` and ``y`` are considered equal if
        ``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on
        absolute differences) and ``rtol`` (the tolerance on relative
        differences) are positive, typically very small numbers. See
        the *atol* and *rtol* parameters.""",
    # equals compression
    "{{equals compression}}": """Any compression is ignored by default, with only the arrays in
        their uncompressed forms being compared. See the
        *ignore_compression* parameter.""",
    # equals netCDF
    "{{equals netCDF}}": """NetCDF elements, such as netCDF variable and dimension names,
        do not constitute part of the CF data model and so are not
        checked.""",
    # netcdf global
    "{{netcdf global}}": """When multiple field or domain constructs are being written to
        the same file, it is only possible to create a netCDF global
        attribute from a property that has identical values for each
        construct. If any field or domain construct's property has a
        different value then the property will not be written as a
        netCDF global attribute, even if it has been selected as such,
        but will appear instead as attributes on the netCDF data
        variables corresponding to each construct.

        The standard description-of-file-contents properties are
        always written as netCDF global attributes, if possible, so
        selecting them is optional.""",
    # unique construct
    "{{unique construct}}": """If zero or two or more constructs are selected then an
        exception is raised, or the *default* parameter is returned.""",
    # original filenames
    "{{original filenames}}": """The original files are those that contain some or all of the
        data and metadata when it was first instantiated, and are
        necessary (but perhaps not sufficient) to recreate the
        `{{class}}` should the need arise. The `{{package}}.read`
        function automatically records the original file names on all
        data that it creates.

        The original files of any constituent components are also
        included.

        In-place changes to the `{{class}}` will not generally change
        the collection of original files. However if the `{{class}}`
        was produced by combining other objects that also store their
        original file names, then the returned files will be the
        collection of original files from all contributing sources.""",
    # ----------------------------------------------------------------
    # Method description substitutions (3 levels of indentataion)
    # ------------------------1----------------------------------------
    # atol: number, optional
    "{{atol: number, optional}}": """atol: number, optional
                The tolerance on absolute differences between real
                numbers. The default value is set by the
                `{{package}}.atol` function.""",
    # data_name: `str`, optional
    "{{data_name: `str`, optional}}": """data_name: `str`, optional
                The name of the construct's `Data` instance created by
                the returned commands.

                *Parameter example:*
                  ``name='data1'``""",
    # header: `bool`, optional
    "{{header: `bool`, optional}}": """header: `bool`, optional
                If True (the default) output a comment describing the
                components. If False no such comment is returned.""",
    # ignore_compression: `bool`, optional
    "{{ignore_compression: `bool`, optional}}": """ignore_compression: `bool`, optional
                If False then the compression type and, if applicable,
                the underlying compressed arrays must be the same, as
                well as the arrays in their uncompressed forms. By
                default only the the arrays in their uncompressed
                forms are compared.""",
    # ignore_data_type: `bool`, optional
    "{{ignore_data_type: `bool`, optional}}": """ignore_data_type: `bool`, optional
                If True then ignore the data types in all numerical
                comparisons. By default different numerical data types
                imply inequality, regardless of whether the elements
                are within the tolerance for equality.""",
    # ignore_fill_value
    "{{ignore_fill_value: `bool`, optional}}": """ignore_fill_value: `bool`, optional
                If True then all ``_FillValue`` and ``missing_value``
                properties are omitted from the comparison.""",
    # ignore_properties
    "{{ignore_properties: (sequence of) `str`, optional}}": """ignore_properties: (sequence of) `str`, optional
                The names of properties to omit from the
                comparison.""",
    # inplace
    "{{inplace: `bool`, optional}}": """inplace: `bool`, optional
                If True then do the operation in-place and return
                `None`.""",
    # ignore_type
    "{{ignore_type: `bool`, optional}}": """ignore_type: `bool`, optional
                Any type of object may be tested but, in general,
                equality is only possible with another `{{class}}`
                instance, or a subclass of one. If *ignore_type* is
                True then ``{{package}}.{{class}}(source=other)`` is
                tested, rather than the ``other`` defined by the
                *other* parameter.""",
    # indent
    "{{indent: `int`, optional}}": """indent: `int`, optional
                Indent each line by this many spaces. By default no
                indentation is applied. Ignored if *string* is
                False.""",
    # name
    "{{name: `str`, optional}}": """name: `str`, optional
                The name of the `{{class}}` instance created by the
                returned commands.

                *Parameter example:*
                  ``name='var1'``""",
    # namespace
    "{{namespace: `str`, optional}}": """namespace: `str`, optional
                The name space containing classes of the {{package}}
                package. This is prefixed to the class name in
                commands that instantiate instances of {{package}}
                objects. By default, or if `None`, the name space is
                assumed to be consistent with {{package}} being
                imported as ``import {{package}}``.

                *Parameter example:*
                  If {{package}} was imported as ``import {{package}}
                  as xyz`` then set ``namespace='xyz'``

                *Parameter example:*
                  If {{package}} was imported as ``from {{package}}
                  import *`` then set ``namespace=''``""",
    # representative_data
    "{{representative_data: `bool`, optional}}": """representative_data: `bool`, optional
                Return one-line representations of `Data` instances,
                which are not executable code but prevent the data
                being converted in its entirety to a string
                representation.""",
    # rtol
    "{{rtol: number, optional}}": """rtol: number, optional
                The tolerance on relative differences between real
                numbers. The default value is set by the
                `{{package}}.rtol` function.""",
    # string
    "{{string: `bool`, optional}}": """string: `bool`, optional
                If False then return each command as an element of a
                `list`. By default the commands are concatenated into
                a string, with a new line inserted between each
                command.""",
    # verbose
    "{{verbose: `int` or `str` or `None`, optional}}": """verbose: `int` or `str` or `None`, optional
                If an integer from ``-1`` to ``3``, or an equivalent
                string equal ignoring case to one of:

                * ``'DISABLE'`` (``0``)
                * ``'WARNING'`` (``1``)
                * ``'INFO'`` (``2``)
                * ``'DETAIL'`` (``3``)
                * ``'DEBUG'`` (``-1``)

                set for the duration of the method call only as the
                minimum cut-off for the verboseness level of displayed
                output (log) messages, regardless of the
                globally-configured `{{package}}.log_level`. Note that
                increasing numerical value corresponds to increasing
                verbosity, with the exception of ``-1`` as a special
                case of maximal and extreme verbosity.

                Otherwise, if `None` (the default value), output
                messages will be shown according to the value of the
                `{{package}}.log_level` setting.

                Overall, the higher a non-negative integer or
                equivalent string that is set (up to a maximum of
                ``3``/``'DETAIL'``) for increasing verbosity, the more
                description that is printed to convey information
                about the operation.""",
    "{{d: `int`}}": """d: `int`
                The position in the tie points array of the subsampled
                dimension being interpolated.""",
    # d1
    "{{d1: `int`}}": """d1: `int`
                The position of subsampled dimension 1 (in the sense
                of CF Appendix J Figure J.2) in the full tie points
                array.""",
    # d2
    "{{d2: `int`}}": """d2: `int`
                The position of subsampled dimension 2 (in the sense
                of CF Appendix J Figure J.2) in the full tie points
                array.""",
    # s
    "{{s: array_like, optional}}": """s: array_like, optional
                If set to a single number in the range [0, 1] then
                this value is returned for the interpolation coeficient
                ``s``. By default ``s`` is calculated for each of the
                interpolation subararea's uncompressed locations.""",
    # s_i
    "{{s_i: array_like}}": """s_i: array_like
                A value for the interpolation coefficient ``s`` for
                the subsampled dimension that corresponds to a
                particular uncompressed location between the two tie
                points.

                *Parameter example:*
                  ``0.5``""",
    # location_use_3d_cartesian
    "{{location_use_3d_cartesian: `numpy.ndarray` or `None`}}": """location_use_3d_cartesian: `numpy.ndarray` or `None`
                The boolean interpolation parameter
                ``location_use_3d_cartesian``, with the same number of
                dimensions in the same order as the full tie points
                array. True values indicate that interpolation is
                carried out in three-dimensional cartesian
                coordinates, as opposed to latitude-longitude
                coordinates. If `None` then an exception is raised.""",
    # construct selection identity
    "{{construct selection identity}}": """A construct has a number of string-valued identities
                defined by its `!identities` method, and is selected
                if any of them match the *identity*
                parameter. *identity* may be a string that equals one
                of a construct's identities; or a `re.Pattern` object
                that matches one of a construct's identities via
                `re.search`.

                Note that in the output of a `dump` method or `print`
                call, a metadata construct is always described by one
                of its identities, and so this description may always
                be used as an *identity* value.""",
    # domain axis selection identity
    "{{domain axis selection identity}}": """A domain axis construct has a number of string-valued
                identities (defined by its `!identities` method) and
                is selected if any of them match the *identity*
                parameter.  *identity* may be a string that equals one
                of a construct's identities; or a `re.Pattern` object
                that matches one of a construct's identities via
                `re.search`.""",
    # returns creation_commands
    "{{returns creation_commands}}": """`str` or `list`
                The commands in a string, with a new line inserted
                between each command. If *string* is False then the
                separate commands are returned as each element of a
                `list`.""",
    # returns dump
    "{{returns dump}}": """`str` or `None`
                The description. If *display* is True then the
                description is printed and `None` is
                returned. Otherwise the description is returned as a
                string.""",
    # generator: `bool`, optional
    "{{generator: `bool`, optional}}": """generator: `bool`, optional
                If True then return a generator for the identities,
                rather than a list. This can give improved performance
                if iteration through the generator can be stopped
                before all identities have been computed.

                .. versionadded:: (cfdm) 1.8.9.0""",
    # filter_kwargs: optional
    "{{filter_kwargs: optional}}": """filter_kwargs: optional
                Keyword arguments as accepted by `Constructs.filter`
                that define additional construct selection
                criteria.""",
    # key: `bool`, optional
    "{{key: `bool`, optional}}": """key: `bool`, optional
                If True then return the selected construct
                identifier. By default the construct itself is
                returned.""",
    # item: `bool`, optional
    "{{item: `bool`, optional}}": """item: `bool`, optional
                If True then return as a tuple the selected construct identifier
                and the construct itself. By default only the construct
                itself is returned. If *key* is True then *item* is
                ignored.""",
    # chunks subarrays
    "{{subarrays chunks: ``-1`` or sequence, optional}}": """chunks: ``-1`` or sequence, optional
                Define the subarray shapes.

                Must be either ``-1``, the default, meaning that all
                non-compressed dimensions in each subarray have the
                maximum possible size; or a sequence of `tuple`. In
                the latter case *chunks* must be allowed as an input
                to `subarray_shapes`.

                A valid *chunks* specification may always be found by
                normalising an output of `subarray_shapes` with
                `dask.array.core.normalize_chunks` as follows:
                ``chunks =
                dask.array.core.normalize_chunks(a.subarray_shapes(...),
                shape=a.shape, dtype=a.dtype)``.""",
    # chunks subarray_shapes
    "{{subarray_shapes chunks: `int`, sequence, `dict`, or `str`, optional}}": """chunks: `int`, sequence, `dict` or `str`, optional
                Define the subarray shapes.

                Any value accepted by the *chunks* parameter of the
                `dask.array.from_array` function is allowed.

                The subarray sizes implied by *chunks* for a dimension
                that has been compressed are ignored and replaced with
                values that are implied by the decompression algorithm, so
                their specification is arbitrary.

                By default, *chunks* is ``-1``, meaning that all
                non-compressed dimensions in each subarray have the
                maximum possible size.""",
    # clear
    "{{clear: `bool` optional}}": """clear: `bool` optional
                If True then remove any stored original file
                names. This will also clear original file names from
                any ancillary data information, such as a count
                variable required for compressed data.""",
    # define
    "{{define: (sequence of) `str`, optional}}": """define: (sequence of) `str`, optional
                Set these original file names, removing any already
                stored.  The original file names of any constituent
                parts are not set. Can't be used with the *update*
                parameter.""",
    # update
    "{{update: (sequence of) `str`, optional}": """update: (sequence of) `str`, optional
                Add these original file names to those already
                stored. The original file names of any constituent
                parts are not updated. Can't be used with the *define*
                parameter.""",
    # init source
    "{{init compressed_dimensions: `dict`}}": """compressed_dimensions: `dict`
                Mapping of compressed to uncompressed dimensions.

                A dictionary key is a position of a dimension in the
                compressed data, with a value of the positions of the
                corresponding dimensions in the uncompressed
                data. Compressed array dimensions that are not
                compressed must be omitted from the mapping.""",
    # init start_index
    "{{init start_index: `int`}}": """start_index: `int`
                The base of the indices provided by the integer index
                array. Must be ``0`` or ``1`` for zero- or one-based
                indices respectively.""",
    # init cell_dimension
    "{{init cell_dimension: `int`}}": """cell_dimension: `int`
                The position of the *data* dimension that indexes the
                cells, either ``0`` or ``1``.""",
    # ----------------------------------------------------------------
    # Method description susbstitutions (4 levels of indentataion)
    # ----------------------------------------------------------------
    # Returns constructs
    "{{Returns constructs}}": """
                The selected constructs in a new `Constructs` object,
                unless modified by any *filter_kwargs* parameters. The
                returned object will contain no constructs if none
                were selected.""",
    # Returns construct
    "{{Returns construct}}": """The selected construct, or its identifier if *key* is
                True, or a tuple of both if *item* is True.""",
    # string value match
    "{{value match}}": """A value may be any object that can match via the
                ``==`` operator, or a `re.Pattern` object that matches
                via its `~re.Pattern.search` method.""",
    # displayed identity
    "{{displayed identity}}": """Note that in the output of a `dump` method or `print`
                call, a construct is always described by an identity
                that will select it.""",
    # auto:
    "{{shapes auto}}": """If ``'auto'`` then the shapes along non-compressed
                dimensions are not created, those dimensions' elements
                being replaced with ``'auto'`` instead.""",
    # Returns original filenames
    "{{Returns original filenames}}": """The original file names in normalised absolute
                form. If there are no original files then an empty
                `set` will be returned.""",
}
