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
    # netCDF HDF5 chunks
    "{{netCDF HDF5 chunks}}": """The netCDF4 HDF5 chunks may be accessed with the
    `nc_hdf5_chunksizes`, `nc_set_hdf5_chunksizes`, and
    `nc_clear_hdf5_chunksizes` methods.""",
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
    # Method description substitutions (3 levels of indentation)
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
    # d
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
                this value is returned for the interpolation
                coefficient ``s``. By default ``s`` is calculated for
                each of the interpolation subarea's uncompressed
                locations.""",
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
    # hdf5 chunksizes
    "{{hdf5 chunksizes}}": """chunksizes: `None` or `str` or `int` or `float` or `dict` or a sequence
                Set the chunking strategy for writing to a netCDF4
                file. One of:

                * `None`: No HDF5 chunking strategy has been
                  defined. The chunking strategy will be determined at
                  write time by `{{package}}.write`.

                * ``'contiguous'``: The data will be written to the
                  file contiguously, i.e. no chunking.

                * `int` or `float` or `str`: The size in bytes of the
                  HDF5 chunks. A floating point value is rounded down
                  to the nearest integer, and a string represents a
                  quantity of byte units. "Square-like" chunk shapes
                  are preferred, maximising the amount of chunks that
                  are completely filled with data values (see the
                  `{{package}}.write` *hdf5_chunks* parameter for
                  details). For instance a chunksize of 1024 bytes may
                  be specified with any of ``1024``, ``1024.9``,
                  ``'1024'``, ``'1024.9'``, ``'1024 B'``, ``'1 KiB'``,
                  ``'0.0009765625 MiB'``, etc. Recognised byte units
                  are (case insensitive): ``B``, ``KiB``, ``MiB``,
                  ``GiB``, ``TiB``, ``PiB``, ``KB``, ``MB``, ``GB``,
                  ``TB``, and ``PB``. Spaces in strings are optional.

                * sequence of `int` or `None`: The maximum number of
                  array elements in a chunk along each data axis,
                  provided in the same order as the data axes. Values
                  are automatically limited to the full size of their
                  corresponding data axis, but the special values
                  `None` or ``-1`` may be used to indicate the full
                  axis size. This chunking strategy may get
                  automatically modified by methods that change the
                  data shape (such as `insert_dimension`).

                * `dict`: The maximum number of array elements in a
                  chunk along the axes specified by the dictionary
                  keys. Integer values are automatically limited to
                  the full size of their corresponding data axis, and
                  the special values `None` or ``-1`` may be used to
                  indicate the full axis size. The chunk size for an
                  unspecified axis defaults to an existing chunk size
                  for that axis, if there is one, or else the axis
                  size. This chunking strategy may get automatically
                  modified by methods that change the data shape (such
                  as `insert_dimension`).""",
    # hdf5 todict
    "{{hdf5 todict: `bool`, optional}}": """todict: `bool`, optional
                If True then the HDF5 chunk sizes are returned in a
                `dict` keyed by their axis positions. If False (the
                default) then the HDF5 chunking strategy is returned
                in the same form that it was set (i.e. as `None`,
                `int`, `str`, or `tuple`).""",
    # Returns nc_hdf5_chunksizes
    "{{Returns nc_hdf5_chunksizes}}": """`None` or `str` or `int` or `dict` or `tuple` of `int`
                The current chunking strategy when writing to a
                netCDF4 file. One of:

                * `None`: No HDF5 chunking strategy has been
                  defined. The chunking strategy will be determined at
                  write time by `{{package}}.write`.

                * ``'contiguous'``: The data will be written to the
                  file contiguously, i.e. no chunking.

                * `int` or `str`: The size in bytes of the HDF5
                  chunks. A string represents a quantity of byte
                  units. "Square-like" chunk shapes are preferred,
                  maximising the amount of chunks that are completely
                  filled with data values (see the `{{package}}.write`
                  *hdf5_chunks* parameter for details). For instance a
                  chunksize of 1024 bytes may be specified with any of
                  ``1024``, ``'1024'``, ``'1024 B'``, ``'1 KiB'``,
                  ``'0.0009765625 MiB'``, etc. Recognised byte units
                  are (case insensitive): ``B``, ``KiB``, ``MiB``,
                  ``GiB``, ``TiB``, ``PiB``, ``KB``, ``MB``, ``GB``,
                  ``TB``, and ``PB``.

                * `tuple` of `int`: The maximum number of array
                  elements in a chunk along each data axis. This
                  chunking strategy may get automatically modified by
                  methods that change the data shape (such as
                  `insert_dimension`).

                * `dict`: If *todict* is True, the maximum number of
                  array elements in a chunk along each axis. This
                  chunking strategy may get automatically modified by
                  methods that change the data shape (such as
                  `insert_dimension`).""",
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
    # _force_mask_hardness
    "{{_force_mask_hardness: `bool`, optional}}": """_force_mask_hardness: `bool`, optional
                If True (the default) then force the mask hardness of
                the returned Dask graph to be that given by the
                `hardmask` attribute. If False then the mask hardness
                may or may not be correct, depending on the nature of
                the stack of previously defined lazy operations.

                Set to False if the intention is to just inspect the
                state of the Dask graph, or is to add to the returned
                Dask graph further operations to which can correctly
                manage the mask hardness.""",
    # _force_to_memory
    "{{_force_to_memory: `bool`, optional}}": """_force_to_memory: `bool`, optional
                If True (the default) then force the data resulting
                from computing the returned Dask graph to be in
                memory. If False then the data resulting from
                computing the Dask graph may or may not be in memory,
                depending on the nature of the stack of previously
                defined lazy operations.

                Set to False if the intention is to just inspect the
                state of the Dask graph, or is to add to the returned
                Dask graph further operations to which can handle any
                required conversion to data in memory.""",
    # chunks
    "{{chunks: `int`, `tuple`, `dict` or `str`, optional}}": """chunks: `int`, `tuple`, `dict` or `str`, optional
                Specify the chunking of the underlying dask array.

                Any value accepted by the *chunks* parameter of the
                `dask.array.from_array` function is allowed.

                By default, ``"auto"`` is used to specify the array
                chunking, which uses a chunk size in bytes defined by
                the `{{package}}.chunksize` function, preferring square-like
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
                as defined by the `{{package}}.chunksize` function.""",
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
    # ----------------------------------------------------------------
    # Method description substitutions (4 levels of indentation)
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
