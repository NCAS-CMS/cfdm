"""Descufine docstring substitutions.

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
    # init mask
    "{{init mask: `bool`, optional}}": """mask: `bool`, optional
                If True (the default) then mask by convention when
                reading data from disk.

                A netCDF array is masked depending on the values of
                any of the netCDF attributes ``_FillValue``,
                ``missing_value``, ``_Unsigned``, ``valid_min``,
                ``valid_max``, and ``valid_range``.""",
    # init unpack
    "{{init unpack: `bool`, optional}}": """unpack: `bool`, optional
                If True (the default) then unpack by convention when
                reading data from disk.

                A netCDF array is unpacked depending on the values of
                the netCDF attributes ``add_offset`` and
                ``scale_factor``.""",
    # init attributes
    "{{init attributes: `dict` or `None`, optional}}": """attributes: `dict` or `None`, optional
                Provide netCDF attributes for the data as a dictionary
                of key/value pairs.""",
    # init storage_options
    "{{init storage_options: `dict` or `None`, optional}}": """storage_options: `dict` or `None`, optional
                Key/value pairs to be passed on to the creation of
                `s3fs.S3FileSystem` file systems to control the
                opening of files in S3 object stores. Ignored for
                files not in an S3 object store, i.e. those whose
                names do not start with ``s3:``.

                By default, or if `None`, then *storage_options* is
                taken as ``{}``.

                If the ``'endpoint_url'`` key is not in
                *storage_options* or is not in a dictionary defined by
                the ``'client_kwargs`` key (which is always the case
                when *storage_options* is `None`), then one will be
                automatically inserted for accessing an S3 file. For
                example, for a file name of
                ``'s3://store/data/file.nc'``, an ``'endpoint_url'``
                key with value ``'https://store'`` would be created.

                *Parameter example:*
                  For a file name of ``'s3://store/data/file.nc'``,
                  the following are equivalent: ``None``, ``{}``, and
                  ``{'endpoint_url': 'https://store'}``,
                  ``{'client_kwargs': {'endpoint_url':
                  'https://store'}}``

                *Parameter example:*
                  ``{'key': 'scaleway-api-key...', 'secret':
                  'scaleway-secretkey...', 'endpoint_url':
                  'https://s3.fr-par.scw.cloud', 'client_kwargs':
                  {'region_name': 'fr-par'}}``""",
    # asanyarray
    "{{asanyarray: `bool` or `None`, optional}": """asanyarray: `bool` or `None`, optional
                If True then add a final operation (not in-place) to
                the graph of the returned Dask array that converts a
                chunk's array object to a `numpy` array if the array
                object has an `__asanyarray__` attribute that is
                `True`, or else does nothing. If False then do not add
                this operation. If `None`, the default, then the final
                operation is added only if the `Data` object's
                `__asanyarray__` attribute is `True`.

                By default or if *asanyarray* is True, the returned
                Dask array will always provide the expected result
                when computed, although if *asanyarray* is True then
                the Dask graph may have an extra null operation layer
                that is not requred. Setting *asanyarray* to False
                should only be done in the case that the returned Dask
                Array will get further operations which are guaranteed
                to negate the need for the extra layer in the Dask
                graph.""",
    # chunks
    "{{chunks: `int`, `tuple`, `dict` or `str`, optional}}": """chunks: `int`, `tuple`, `dict` or `str`, optional
                Specify the chunking of the underlying dask array.

                Any value accepted by the *chunks* parameter of the
                `dask.array.from_array` function is allowed.

                By default, ``"auto"`` is used to specify the array
                chunking, which uses a chunk size in bytes defined by
                the `cf.chunksize` function, preferring square-like
                chunk shapes.

                *Parameter example:*
                  A blocksize like ``1000``.

                *Parameter example:*
                  A blockshape like ``(1000, 1000)``.

                *Parameter example:*
                  Explicit sizes of all blocks along all dimensions
                  like ``((1000, 1000, 500), (400, 400))``.

                *Parameter example:*
                  A size in bytes, like ``"100MiB"`` which will choose
                  a uniform block-like shape, preferring square-like
                  chunk shapes.

                *Parameter example:*
                  A blocksize of ``-1`` or `None` in a tuple or
                  dictionary indicates the size of the corresponding
                  dimension.

                *Parameter example:*
                  Blocksizes of some or all dimensions mapped to
                  dimension positions, like ``{1: 200}``, or ``{0: -1,
                  1: (400, 400)}``.""",
    # threshold
    "{{threshold: `int`, optional}}": """threshold: `int`, optional
                The graph growth factor under which we don't bother
                introducing an intermediate step. See
                `dask.array.rechunk` for details.""",
    # block_size_limit
    "{{block_size_limit: `int`, optional}}": """block_size_limit: `int`, optional
                The maximum block size (in bytes) we want to produce,
                as defined by the `cf.chunksize` function.""",
    # balance
    "{{balance: `bool`, optional}}": """balance: `bool`, optional
                If True, try to make each chunk the same size. By
                default this is not attempted.

                This means ``balance=True`` will remove any small
                leftover chunks, so using ``d.rechunk(chunks=len(d) //
                N, balance=True)`` will almost certainly result in
                ``N`` chunks.""",
    # collapse keepdims
    "{{collapse keepdims: `bool`, optional}}": """keepdims: `bool`, optional
                By default, the axes which are collapsed are left in
                the result as dimensions with size one, so that the
                result will broadcast correctly against the input
                array. If set to False then collapsed axes are removed
                from the data.""",
    # collapse axes
    "{{collapse axes: (sequence of) `int`, optional}}": """axes: (sequence of) `int`, optional
                The axes to be collapsed. By default all axes are
                collapsed, resulting in output with size 1. Each axis
                is identified by its positive or negative integer
                position. If *axes* is an empty sequence then the
                collapse is applied to each scalar element and the
                result has the same shape as the input data.""",
    # collapse squeeze
    "{{collapse squeeze: `bool`, optional}}": """squeeze: `bool`, optional
                By default, the axes which are collapsed are left in
                the result as dimensions with size one, so that the
                result will broadcast correctly against the input
                array. If set to True then collapsed axes are removed
                from the data.""",
    # split_every
    "{{split_every: `int` or `dict`, optional}}": """split_every: `int` or `dict`, optional
                Determines the depth of the `dask` recursive
                aggregation. If set to or more than the number of
                input Dask chunks, the aggregation will be performed
                in two steps, one partial collapse per input chunk and
                a single aggregation at the end. If set to less than
                that, an intermediate aggregation step will be used,
                so that any of the intermediate or final aggregation
                steps operates on no more than ``split_every``
                inputs. The depth of the aggregation graph will be
                :math:`log_{split\_every}}(\textnormal{input chunks
                along reduced axes})`. Setting to a low value can
                reduce cache size and network transfers, at the cost
                of more CPU and a larger dask graph.

                By default, `dask` heuristically decides on a good
                value. A default can also be set globally with the
                ``split_every`` key in `dask.config`. See
                `dask.array.reduction` for details.""",
    # _get_array index
    "{{index: `tuple` or `None`, optional}}": """index: `tuple` or `None`, optional
               Provide the indices that define the subspace. If `None`
               then the `index` attribute is used.""",
    # pad_width
    "{{pad_width: sequence of `int`, optional}}": """pad_width: sequence of `int`, optional
                Number of values to pad before and after the edges of
                the axis.""",
    # to_size
    "{{to_size: `int`, optional}}": """to_size: `int`, optional
                Pad the axis after so that the new axis has the given
                size.""",
    # cfa substitutions
    "{{cfa substitutions: `dict`}}": """substitutions: `dict`
                The CF-netCDF aggregation file location substitution
                definitions in a dictionary whose key/value pairs are
                the file name parts to be substituted and their
                corresponding replacement text.

                Each substitution definition may be specified with or
                without the ``${...}`` syntax. For instance, the
                following are equivalent: ``{'substitution':
                'replacement'}``, ``{'${substitution}':
                'replacement'}``.""",
    # cfa base
    "{{cfa substitution: `str`}}": """substitution: `str`
                The CF-netCDF aggregation file location substitution
                definition to be removed. May be specified with or
                without the ``${...}`` syntax. For instance, the
                following are equivalent: ``'substitution'`` and
                ``'${substitution}'``.""",
    # cull_graph
    "{{cull_graph: `bool`, optional}}": """cull_graph: `bool`, optional
                If True then unnecessary tasks are removed (culled)
                from each array's dask graph before
                concatenation. This process can have a considerable
                overhead but can sometimes improve the overall
                performance of a workflow. If False (the default) then
                dask graphs are not culled. See
                `dask.optimization.cull` for details.""",
    # relaxed_units
    "{{relaxed_units: `bool`, optional}}": """relaxed_units: `bool`, optional
                If True then allow the concatenation of data with
                invalid but otherwise equal units. By default, if any
                data array has invalid units then the concatenation
                will fail. A `Units` object is considered to be
                invalid if its `!isvalid` attribute is `False`.""",
    # relaxed_units
    "{{concatenate copy: `bool`, optional}}": """copy: `bool`, optional
                If True (the default) then make copies of the
                `{{class}}` objects prior to the concatenation,
                thereby ensuring that the input constructs are not
                changed by the concatenation process. If False then
                some or all input constructs might be changed
                in-place, but the concatenation process will be
                faster.""",
    # ----------------------------------------------------------------
    # Method description susbstitutions (4 levels of indentataion)
    # ----------------------------------------------------------------
    # Returns constructs
    "{{Returns constructs}}": """The selected constructs in a new `Constructs` object,
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
    # Returns nc_clear_aggregations_substitutions
    "{{Returns nc_clear_aggregated_substitutions}}": """The removed CF-netCDF aggregation file location
                substitutions in a dictionary whose key/value pairs
                are the location name parts to be substituted and
                their corresponding replacement text.""",
    # Returns nc_del_aggregated_substitution
    "{{Returns nc_del_aggregated_substitution}}": """The removed CF-netCDF aggregation file location
                substitution in a dictionary whose key/value pairs are
                the location name part to be substituted and its
                corresponding replacement text. If the given
                substitution was not defined then an empty dictionary
                is returned.""",
    # Returns nc_aggregated_substitutions
    "{{Returns nc_aggregated_substitutions}}": """The CF-netCDF aggregation file location substitutions
                in a dictionary whose key/value pairs are the file
                name parts to be substituted and their corresponding
                replacement text.""",
}
