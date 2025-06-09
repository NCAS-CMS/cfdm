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
    # netCDF dataset chunks
    "{{netCDF dataset chunks}}": """The dataset chunks may be accessed with the
    `nc_dataset_chunksizes`, `nc_set_dataset_chunksizes`, and
    `nc_clear_datset_chunksizes` methods.""",
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
    # read datasets
    "{{read datasets: (arbitrarily nested sequence of) `str`}}": """dataset: (arbitrarily nested sequence of) `str`
            A string, or arbitrarily nested sequence of strings,
            giving the dataset names, or directory names, from which
            to read field or domain constructs.

            Local names may be relative paths and will have tilde and
            shell environment variables expansions applied to them,
            followed by the replacement of any UNIX wildcards (such as
            ``*``, ``?``, ``[a-z]``, etc.) with the list of matching
            names. Remote names (i.e. those with an http or s3
            schema), however, are not transformed in any way.

            Directories will be walked through to find their contents
            (recursively if *recursive* is True), unless the directory
            defines a Zarr dataset (which is ascertained by presence
            in the directory of appropriate Zarr metadata files).

            Remote datasets (i.e. those with an http or s3 schema) are
            assumed to be netCDF files, or else Zarr datasets if the
            *dataset_type* parameter is set to ``'Zarr'``.

            As a special case, if the *cdl_string* parameter is True,
            then interpretation of *datasets* changes so that each
            string is assumed to be an actual CDL representation of a
            dataset, rather than a than a file or directory name.

            *Example:*
              The local dataset ``file.nc`` in the user's home
              directory could be described by any of the following:
              ``'$HOME/file.nc'``, ``'${HOME}/file.nc'``,
              ``'~/file.nc'``, ``'~/tmp/../file.nc'``

            *Example:*
              The local datasets ``file1.nc`` and ``file2.nc`` could
              be described by any of the following: ``['file1.nc',
              'file2.nc']``, ``'file[12].nc'``""",
    # read cdl_string
    "{{read cdl_string: `bool`, optional}}": """cdl_string: `bool`, optional
            If True and the format to read is CDL then each string
            given by the *datasets* parameter is interpreted as a
            string of actual CDL rather than the name of a location
            from which field or domain constructs can be read.

            Note that when `cdl_string` is True, the `fmt` parameter
            is ignored as the format is assumed to be CDL, so in this
            case it is not necessary to also specify ``fmt='CDL'``.""",
    # read external
    "{{read external: (sequence of) `str`, optional}}": """external: (sequence of) `str`, optional
            Read external variables (i.e. variables which are named by
            attributes, but are not present, in the parent file given
            by the *filename* parameter) from the given external
            files. Ignored if the parent file does not contain a
            global ``external_variables`` attribute. Multiple external
            files may be provided, which are searched in random order
            for the required external variables.

            If an external variable is not found in any external
            files, or is found in multiple external files, then the
            relevant metadata construct is still created, but without
            any metadata or data. In this case the construct's
            `!is_external` method will return `True`.

            *Parameter example:*
              ``external='cell_measure.nc'``

            *Parameter example:*
              ``external=['cell_measure.nc']``

            *Parameter example:*
              ``external=('cell_measure_A.nc', 'cell_measure_O.nc')``""",
    # read extra
    "{{read extra: (sequence of) `str`, optional}}": """extra: (sequence of) `str`, optional
            Create extra, independent fields from netCDF variables
            that correspond to particular types of metadata constructs.
            Ignored if *domain* is True.

            The *extra* parameter may be one, or a sequence, of:

            ==========================  ===============================
            *extra*                     Metadata constructs
            ==========================  ===============================
            ``'field_ancillary'``       Field ancillary constructs
            ``'domain_ancillary'``      Domain ancillary constructs
            ``'dimension_coordinate'``  Dimension coordinate constructs
            ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
            ``'cell_measure'``          Cell measure constructs
            ==========================  ===============================

            *Parameter example:*
              To create fields from auxiliary coordinate constructs:
              ``extra='auxiliary_coordinate'`` or
              ``extra=['auxiliary_coordinate']``.

            *Parameter example:*
              To create fields from domain ancillary and cell measure
              constructs: ``extra=['domain_ancillary',
              'cell_measure']``.

            An extra field construct created via the *extra* parameter
            will have a domain limited to that which can be inferred
            from the corresponding netCDF variable, but without the
            connections that are defined by the parent netCDF data
            variable. It is possible to create independent fields from
            metadata constructs that do incorporate as much of the
            parent field construct's domain as possible by using the
            `~{{package}}.Field.convert` method of a returned field
            construct, instead of setting the *extra* parameter.""",
    # read verbose
    "{{read verbose: `int` or `str` or `None`, optional}}": """verbose: `int` or `str` or `None`, optional
            If an integer from ``-1`` to ``3``, or an equivalent string
            equal ignoring case to one of:

            * ``'DISABLE'`` (``0``)
            * ``'WARNING'`` (``1``)
            * ``'INFO'`` (``2``)
            * ``'DETAIL'`` (``3``)
            * ``'DEBUG'`` (``-1``)

            set for the duration of the method call only as the
            minimum cut-off for the verboseness level of displayed
            output (log) messages, regardless of the
            globally-configured `{{package}}.log_level`.  Note that
            increasing numerical value corresponds to increasing
            verbosity, with the exception of ``-1`` as a special case
            of maximal and extreme verbosity.

            Otherwise, if `None` (the default value), output messages
            will be shown according to the value of the
            `{{package}}.log_level` setting.

            Overall, the higher a non-negative integer or equivalent string
            that is set (up to a maximum of ``3``/``'DETAIL'``) for
            increasing verbosity, the more description that is printed to
            convey how the contents of the netCDF file were parsed and
            mapped to CF data model constructs.""",
    # read warnings
    "{{read warnings: `bool`, optional}}": """warnings: `bool`, optional
            If True then print warnings when an output field construct
            is incomplete due to structural non-compliance of the
            dataset. By default such warnings are not displayed.""",
    # read warn_valid
    "{{read warn_valid: `bool`, optional}}": """warn_valid: `bool`, optional
            If True then print a warning for the presence of
            ``valid_min``, ``valid_max`` or ``valid_range`` properties
            on field constructs and metadata constructs that have
            data. By default no such warning is issued.

            "Out-of-range" data values in the file, as defined by any
            of these properties, are automatically masked by default,
            which may not be as intended. See the *mask* parameter for
            turning off all automatic masking.""",
    # read mask
    "{{read mask: `bool`, optional}}": """mask: `bool`, optional
            If True (the default) then mask by convention the data of
            field and metadata constructs.

            A netCDF array is masked depending on the values of any of
            the netCDF attributes ``_FillValue``, ``missing_value``,
            ``_Unsigned``, ``valid_min``, ``valid_max``, and
            ``valid_range``.""",
    # read unpack
    "{{read unpack: `bool`}}": """unpack: `bool`
            If True, the default, then unpack arrays by convention
            when the data is read from disk.

            Unpacking is determined by netCDF conventions for the
            following variable attributes: ``add_offset``,
            ``scale_factor``, and ``_Unsigned``.""",
    # read domain
    "{{read domain: `bool`, optional}}": """domain: `bool`, optional
            If True then return only the domain constructs that are
            explicitly defined by CF-netCDF domain variables, ignoring
            all CF-netCDF data variables. By default only the field
            constructs defined by CF-netCDF data variables are
            returned.

            CF-netCDF domain variables are only defined from CF-1.9,
            so older datasets automatically contain no CF-netCDF
            domain variables.

            The unique domain constructs of the dataset are
            found with the `{{package}}.unique_constructs`
            function. For example::

               >>> d = {{package}}.read('file.nc', domain=True)
               >>> ud = {{package}}.unique_constructs(d)
               >>> f = {{package}}.read('file.nc')
               >>> ufd = {{package}}.unique_constructs(x.domain for x in f)""",
    # read netcdf_backend
    "{{read netcdf_backend: `None` or (sequence of) `str`, optional}": """netcdf_backend: `None` or (sequence of) `str`, optional
            Specify which library, or libraries, to use for opening
            and reading netCDF files. By default, or if `None`, then
            the first one of `h5netcdf` and `netCDF4` to successfully
            open the netCDF file is used. The libraries will be used
            in the order given, until a file is successfully
            opened.""",
    # read  storage_options
    "{{read storage_options: `dict` or `None`, optional}}": """storage_options: `dict` or `None`, optional
            Pass parameters to the backend file system driver, such as
            username, password, server, port, etc. How the storage
            options are interpreted depends on the location of the
            file:

            * **Local File System**: Storage options are ignored for
              local files.

            * **HTTP(S)**: Storage options are ignored for files
              available across the network via OPeNDAP.

            * **S3-compatible services**: The backend used is `s3fs`,
              and the storage options are used to initialise an
              `s3fs.S3FileSystem` file system object. By default, or
              if `None`, then *storage_options* is taken as ``{}``.

              If the ``'endpoint_url'`` key is not in
              *storage_options*, nor in a dictionary defined by the
              ``'client_kwargs'`` key (both of which are the case when
              *storage_options* is `None`), then one will be
              automatically inserted for accessing an S3 file. For
              instance, with a file name of
              ``'s3://store/data/file.nc'``, an ``'endpoint_url'`` key
              with value ``'https://store'`` would be created. To
              disable this, set the ``'endpoint_url'`` key to `None`.

              *Parameter example:*
                For a file name of ``'s3://store/data/file.nc'``, the
                following are equivalent: ``None``, ``{}``,
                ``{'endpoint_url': 'https://store'}``, and
                ``{'client_kwargs': {'endpoint_url':
                'https://store'}}``

              *Parameter example:*
                ``{'key': 'scaleway-api-key...', 'secret':
                'scaleway-secretkey...', 'endpoint_url':
                'https://s3.fr-par.scw.cloud', 'client_kwargs':
                {'region_name': 'fr-par'}}``""",
    # read cache
    "{{read cache: `bool`, optional}}": """cache: `bool`, optional
            If True, the default, then cache the first and last array
            elements of metadata constructs (not field constructs) for
            fast future access. In addition, the second and
            penultimate array elements will be cached from coordinate
            bounds when there are two bounds per cell. For remote
            data, setting *cache* to False may speed up the parsing of
            the file.""",
    # read dask_chunks
    "{{read dask_chunks: `str`, `int`, `None`, or `dict`, optional}}": """dask_chunks: `str`, `int`, `None`, or `dict`, optional
            Specify the Dask chunking for data. May be one of the
            following:

            * ``'storage-aligned'``

              This is the default. The Dask chunk size in bytes will
              be as close as possible the size given by
              `{{package}}.chunksize`, favouring square-like chunk
              shapes, with the added guarantee that the entirety of
              each storage chunk lies within exactly one Dask
              chunk. This strategy is general the most performant, as
              it ensures that when accessing the data, each storage
              chunk is read from disk at most once (as opposed to once
              per Dask chunk in which it lies).

              For instance, consider a file variable that has an array
              of 64-bit floats with shape (400, 300, 60) and a storage
              chunk shape of (100, 5, 60). This has an overall size of
              54.93 MiB, partitioned into 240 storage chunks each of
              size 100*5*60*8 bytes = 0.23 MiB. Then:

              * If `{{package}}.chunksize` returns 134217728 (i.e. 128
                MiB), then the storage-aligned Dask chunks will have
                shape (400, 300, 60), giving 1 Dask chunk with size of
                54.93 MiB (compare with a Dask chunk shape of (400,
                300, 60) and size 54.93 MiB when *dask_chunks* is
                ``'auto'``.)

              * If `{{package}}.chunksize` returns 33554432 (i.e. 32
                MiB), then the storage-aligned Dask chunks will have
                shape (200, 260, 60), giving 4 Dask chunks with a
                maximum size of 23.80 MiB (compare with a Dask chunk
                shape of (264, 264, 60) and maximum size 31.90 MiB
                when *dask_chunks* is ``'auto'``.)

              * If `{{package}}.chunksize` returns 4194304 (i.e. 4
                MiB), then the storage-aligned Dask chunks will have
                shape (100, 85, 60), giving 16 Dask chunks with a
                maximum size of 3.89 MiB (compare with a Dask chunk
                shape of (93, 93, 60) and maximum size 3.96 MiB when
                *dask_chunks* is ``'auto'``.)

              There are, however, some occasions when, for particular
              data arrays in the file, the ``'auto'`` option will
              automatically be used instead of storage-aligned Dask
              chunks. This occurs when:

              * The data array in the file is stored contiguously.

              * The data array in the file is compressed by convention
                (e.g. ragged array representations, compression by
                gathering, subsampled coordinates, etc.). In this case
                the Dask chunks are for the uncompressed data, and so
                cannot be aligned with the storage chunks of the
                compressed array in the file.

            * ``'storage-exact'``

              Each Dask chunk will contain exactly one storage chunk
              and each storage chunk will lie entirely within exactly
              one Dask chunk.

              For instance, consider a file variable that has an array
              of 64-bit floats with shape (400, 300, 60) and a storage
              chunk shape of (100, 5, 60). This has an overall size of
              54.93 MiB, partitioned into 240 storage chunks each of
              size 100*5*60*8 bytes = 0.23 MiB. The corresponding
              storage-exact Dask chunks will also have shape (100, 5,
              60), giving 240 Dask chunks with a maximum size of 0.23
              MiB.

              There are, however, some occasions when, for particular
              data arrays in the file, the ``'auto'`` option will
              automatically be used instead of storage-exact Dask
              chunks. This occurs when:

              * The data array in the file is stored contiguously.

              * The data array in the file is compressed by convention
                (e.g. ragged array representations, compression by
                gathering, subsampled coordinates, etc.). In this case
                the Dask chunks are for the uncompressed data, and so
                cannot be aligned with the storage chunks of the
                compressed array in the file.

            * ``auto``

              The Dask chunk size in bytes will be as close as
              possible to the size given by `{{package}}.chunksize`,
              favouring square-like chunk shapes. This may give
              similar Dask chunk shapes as the ``'storage-aligned'``
              option, but without the guarantee that each storage
              chunk will lie entirely within exactly one Dask chunk.

            * A byte-size given by a `str`

              The Dask chunk size in bytes will be as close as
              possible to the given byte-size, favouring square-like
              chunk shapes. Any string value, accepted by the *chunks*
              parameter of the `dask.array.from_array` function is
              permitted. There is no guarantee that a storage chunk
              lies entirely within one Dask chunk.

              *Example:*
                A Dask chunksize of 2 MiB may be specified as
                ``'2097152'`` or ``'2 MiB'``.

            * `-1` or `None`

              There is no Dask chunking, i.e. every data array has one
              Dask chunk regardless of its size. In this case each
              storage chunk is guaranteed to lie entirely within the
              one Dask chunk.

            * Positive `int`

              Every dimension of all Dask chunks has this number of
              elements. There is no guarantee that a storage chunk
              lies entirely within one Dask chunk.

              *Example:*
                For 3-dimensional data, *dask_chunks* of `10` will
                give Dask chunks with shape (10, 10, 10).

            * `dict`

              Each of dictionary key identifies a file dimension, with
              a value that defines the Dask chunking for that
              dimension whenever it is spanned by a data array. A file
              dimension is identified in one of three ways:

              1. the netCDF dimension name, preceded by ``ncdim%``
                (e.g. ``'ncdim%lat'``);

              2. the value of the "standard name" attribute of a
                 CF-netCDF coordinate variable that spans the
                 dimension (e.g. ``'latitude'``);

              3. the value of the "axis" attribute of a CF-netCDF
                 coordinate variable that spans the dimension
                 (e.g. ``'Y'``).

              The dictionary values may be a byte-size string,
              ``'auto'``, `int` or `None`, with the same meanings as
              those types for the *dask_chunks* parameter itself, but
              applying only to the specified dimension. In addition, a
              dictionary value may be a `tuple` or `list` of integers
              that sum to the dimension size.

              Not specifying a file dimension in the dictionary is
              equivalent to it being defined with a value of
              ``'auto'``.

              *Example:*
                ``{'T': '0.5 MiB', 'Z': 'auto', 'Y': [36, 37], 'X':
                None}``

              *Example:*
                If a netCDF file contains dimensions ``time``, ``z``,
                ``lat``, and ``lon``, then ``{'ncdim%time': 12,
                'ncdim%lat', None, 'ncdim%lon': None}`` will ensure
                that all ``time`` axes have a Dask chunksize of 12;
                all ``lat`` and ``lon`` axes are not Dask chunked; and
                all ``z`` axes are Dask chunked to comply as closely
                as possible with the default Dask chunk size.

                If the netCDF file also contains a ``time`` coordinate
                variable with a "standard_name" attribute of
                ``'time'`` or "axis" attribute of ``'T'``, then the
                same `dask` chunking could be specified with either
                ``{'time': 12, 'ncdim%lat', None, 'ncdim%lon': None}``
                or ``{'T': 12, 'ncdim%lat', None, 'ncdim%lon':
                None}``.""",
    # read store_dataset_chunks
    "{{read store_dataset_chunks: `bool`, optional}}": """store_dataset_chunks: `bool`, optional

            If True (the default) then store the dataset chunking
            strategy for each returned data array. The dataset
            chunking strategy is then accessible via an object's
            `nc_dataset_chunksizes` method. When the dataset chunking
            strategy is stored, it will be used when the data is
            written to a new netCDF file with `{{package}}.write`
            (unless the strategy is modified prior to writing).

            If False, or if the dataset being read does not support
            chunking (such as a netCDF-3 dataset), then no dataset
            chunking strategy is stored (i.e. an
            `nc_dataset_chunksizes` method will return `None` for all
            `Data` objects). In this case, when the data is written to
            a new netCDF file, the dataset chunking strategy will be
            determined by `{{package}}.write`.

            See the `{{package}}.write` *dataset_chunks* parameter for
            details on how the dataset chunking strategy is determined
            at the time of writing.""",
    # read cfa
    "{{read cfa: `dict`, optional}}": """cfa: `dict`, optional
            Configure the reading of CF-netCDF aggregation files.

            The dictionary may have any subset of the following
            key/value pairs that supplement or override the
            information read from the file:

            * ``'replace_directory'``: `dict`

              A dictionary whose key/value pairs define modifications
              to be applied to the directories of the fragment file
              locations. The dictionary comprises keyword arguments to
              the {{package}}.Data.replace_directory` method, which is
              used to make the the changes. The aggregation file being
              read is unaltered. An empty dictionary results in no
              modifications.

              *Example:*
                Replace a leading ``data/model`` with ``home``,
                wherever it occurs: ``{'replace_directory': {'old':
                'data/model', 'new': 'home'}}``

              *Example:*
                Normalise all file locations and replace a leading
                ``/archive`` with ``/data/obs``, wherever it occurs:
                ``{'replace_directory': {'old': '/archive', 'new':
                '/data/obs', 'normalise': True}}``

              *Example:*
                Normalise all file locations and remove a leading
                ``/data`, wherever it occurs: ``{'replace_directory':
                {'old': '/data', 'normalise': True}}``.""",
    # read cfa_write
    "{{read cfa_write: (sequence of) `str`, optional}}": """cfa_write: (sequence of) `str`, optional
            Register the intention for named construct types to be
            subsequently written as CF-netCDF aggregation variables.

            This makes no difference to the logical content of any
            construct, but ensures that the data of each of specified
            construct types will have only one Dask chunk, regardless
            of the setting of *dask_chunks*, which is a requirement
            for the creation CF-netCDF aggregation variables.

            The *cfa_write* parameter may be one, or a sequence, of:

            ==========================  ===============================
            *cfa_write*                 Construct types
            ==========================  ===============================
            ``'field'``                 Field constructs
            ``'field_ancillary'``       Field ancillary constructs
            ``'domain_ancillary'``      Domain ancillary constructs
            ``'dimension_coordinate'``  Dimension coordinate constructs
            ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
            ``'cell_measure'``          Cell measure constructs
            ``'domain_topology'``       Domain topology constructs
            ``'cell_connectivity'``     Cell connectivity constructs
            ``'all'``                   All constructs
            ==========================  ===============================

            .. note:: If the *dask_chunks* parameter is set to `None`
                      or ``-1`` then the data of all constructs will
                      already have only one Dask chunk, so in this
                      case setting *cfa_write* will have no further
                      effect.

            *Example:*
              To register field constructs to be written as CF-netCDF
              aggregation variables: ``cfa_write='field'`` or
              ``cfa_write=['field']``.

            *Example:*
              To register field and auxiliary coordinate constructs to
              be written as CF-netCDF aggregation variables:
              ``cfa_write=['field', 'auxiliary_coordinate']``.""",
    # read to_memory
    "{{read to_memory: (sequence of) `str`, optional}}": """to_memory: (sequence of) `str`, optional
            Read all data arrays of the named construct types into
            memory. By default, lazy loading is employed for all data
            arrays.

            The *to_memory* parameter may be one, or a sequence, of:

            ==========================  ===============================
            *to_memory*                 Construct types
            ==========================  ===============================
            ``'all'``                   All constructs
            ``'metadata'``              All metadata constructs (i.e.
                                        all constructs except Field
                                        constructs)

            ``'field'``                 Field constructs
            ``'field_ancillary'``       Field ancillary constructs
            ``'domain_ancillary'``      Domain ancillary constructs
            ``'dimension_coordinate'``  Dimension coordinate constructs
            ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
            ``'cell_measure'``          Cell measure constructs
            ``'domain_topology'``       Domain topology constructs
            ``'cell_connectivity'``     Cell connectivity constructs
            ==========================  ===============================

            *Example:*
              To read field construct data arrays into memory:
              ``to_memory='field'`` or ``to_memory=['field']``.

            *Example:*
              To read field and auxiliary coordinate construct data
              arrays into memory: ``to_memory=['field',
              'auxiliary_coordinate']``.""",
    # read squeeze
    "{{read squeeze: `bool`, optional}}": """squeeze: `bool`, optional
            If True then remove all size 1 dimensions from field
            construct data arrays, regardless of how the data are
            stored in the dataset. If False (the default) then the
            presence or not of size 1 dimensions is determined by how
            the data are stored in its dataset.""",
    # read unsqueeze
    "{{read unsqueeze: `bool`, optional}}": """unsqueeze: `bool`, optional
            If True then ensure that field construct data arrays span
            all of the size 1 dimensions, regardless of how the data
            are stored in the dataset. If False (the default) then the
            presence or not of size 1 dimensions is determined by how
            the data are stored in its dataset.""",
    # read dataset_type
    "{{read dataset_type: `None` or (sequence of) `str`, optional}}": """dataset_type: `None` or (sequence of) `str`, optional
            Only read datasets of the given type or types, ignoring
            others. If there are no dataset of the given types, or
            *dataset_type* is empty sequence, then an empty list is
            returned. If `None` (the default) all datasets defined by
            the *dataset* parameter are read, and an exception is
            raised for any invalid dataset type.""",
    # read recursive
    "{{read recursive: `bool`, optional}}": """recursive: `bool`, optional
            If True then recursively read sub-directories of any
            directories specified with the *datasets* parameter.""",
    # read followlinks
    "{{read followlinks: `bool`, optional}}": """followlinks: `bool`, optional
            If True, and *recursive* is True, then also search for
            datasets in sub-directories which resolve to symbolic
            links. By default directories which resolve to symbolic
            links are ignored. Ignored of *recursive* is
            False. Datasets which are symbolic links are always
            followed.

            Note that setting ``recursive=True, followlinks=True`` can
            lead to infinite recursion if a symbolic link points to a
            parent directory of itself.""",
    # persist
    "{{persist description}}": """Persisting turns an underlying lazy dask array into an
        equivalent chunked dask array, but now with the results fully
        computed and in memory. This can avoid the expense of
        re-reading the data from disk, or re-computing it, when the
        data is accessed on multiple occasions.""",
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
                the returned commands.""",
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
                returned commands.""",
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
    # chunk chunksizes
    "{{chunk chunksizes}}": """chunksizes: `None` or `str` or `int` or `float` or `dict` or a sequence
                Set the chunking strategy for writing to a netCDF4
                file. One of:

                * `None`: No dataset chunking strategy has been
                  defined. The chunking strategy will be determined at
                  write time by `{{package}}.write`.

                * ``'contiguous'``

                  The data will be written to the file contiguously,
                  i.e. no chunking.

                * `int` or `float` or `str`

                  The size in bytes of the dataset chunks. A floating
                  point value is rounded down to the nearest integer,
                  and a string represents a quantity of byte
                  units. "Square-like" chunk shapes are preferred,
                  maximising the amount of chunks that are completely
                  filled with data values (see the `{{package}}.write`
                  *dataset_chunks* parameter for details). For
                  instance a chunksize of 1024 bytes may be specified
                  with any of ``1024``, ``1024.9``, ``'1024'``,
                  ``'1024.9'``, ``'1024 B'``, ``'1 KiB'``,
                  ``'0.0009765625 MiB'``, etc. Recognised byte units
                  are (case insensitive): ``B``, ``KiB``, ``MiB``,
                  ``GiB``, ``TiB``, ``PiB``, ``KB``, ``MB``, ``GB``,
                  ``TB``, and ``PB``. Spaces in strings are optional.

                * sequence of `int` or `None`

                  The maximum number of array elements in a chunk
                  along each data axis, provided in the same order as
                  the data axes. Values are automatically limited to
                  the full size of their corresponding data axis, but
                  the special values `None` or ``-1`` may be used to
                  indicate the full axis size. This chunking strategy
                  may get automatically modified by methods that
                  change the data shape (such as `insert_dimension`).

                * `dict`

                  The maximum number of array elements in a chunk
                  along the axes specified by the dictionary
                  keys. Integer values are automatically limited to
                  the full size of their corresponding data axis, and
                  the special values `None` or ``-1`` may be used to
                  indicate the full axis size. The chunk size for an
                  unspecified axis defaults to an existing chunk size
                  for that axis, if there is one, or else the axis
                  size. This chunking strategy may get automatically
                  modified by methods that change the data shape (such
                  as `insert_dimension`).""",
    # chunk todict
    "{{chunk todict: `bool`, optional}}": """todict: `bool`, optional
                If True then the dataset chunk sizes are returned in a
                `dict` keyed by their axis positions. If False (the
                default) then the dataset chunking strategy is
                returned in the same form that it was set (i.e. as
                `None`, `int`, `str`, or `tuple`).""",
    # Returns nc_dataset_chunksizes
    "{{Returns nc_dataset_chunksizes}}": """`None` or `str` or `int` or `dict` or `tuple` of `int`
                The current chunking strategy when writing to a
                netCDF4 file. One of:

                * `None`: No dataset chunking strategy has been
                  defined. The chunking strategy will be determined at
                  write time by `{{package}}.write`.

                * ``'contiguous'``: The data will be written to the
                  file contiguously, i.e. no chunking.

                * `int` or `str`: The size in bytes of the dataset
                  chunks. A string represents a quantity of byte
                  units. "Square-like" chunk shapes are preferred,
                  maximising the amount of chunks that are completely
                  filled with data values (see the `{{package}}.write`
                  *dataset_chunks* parameter for details). For
                  instance a chunksize of 1024 bytes may be specified
                  with any of ``1024``, ``'1024'``, ``'1024 B'``, ``'1
                  KiB'``, ``'0.0009765625 MiB'``, etc. Recognised byte
                  units are (case insensitive): ``B``, ``KiB``,
                  ``MiB``, ``GiB``, ``TiB``, ``PiB``, ``KB``, ``MB``,
                  ``GB``, ``TB``, and ``PB``.

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
                reading data from disk.""",
    # init unpack
    "{{init unpack: `bool`, optional}}": """unpack: `bool`, optional
                If True (the default) then unpack by convention when
                reading data from disk.""",
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
                steps operates on no more than *split_every*
                inputs. The depth of the aggregation graph will be the
                logarithm to the base *split_every* of *N*, the number
                input chunks along reduced axes.  Setting to a low
                value can reduce cache size and network transfers, at
                the cost of more CPU and a larger dask graph. See
                `dask.array.reduction` for details.

                By default, `dask` heuristically decides on a good
                value. A default can also be set globally with the
                ``split_every`` key in `dask.config`.""",
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
    # normalise
    "{{normalise: `bool`, optional}}": """normalise: `bool`, optional
                If True then normalise to an absolute path. If False
                (the default) then no normalisation is done.""",
    # replace old
    "{{replace old: `str` or `None`, optional}}": """old: `str` or `None`, optional
                The base directory structure to be replaced by
                *new*. If `None` (the default) or an empty string, and
                *normalise* is False, then *new* (if set) is prepended
                to each file name.""",
    # replace new
    "{{replace new: `str` or `None`, optional}}": """new: `str` or `None`, optional
                The new directory that replaces the base directory
                structure identified by *old*. If `None` (the default)
                or an empty string, then *old* (if set) is replaced
                with an empty string.""",
    # replace normalise
    "{{replace normalise: `bool`, optional}}": """normalise: `bool`, optional
                If True then *old* and *new* directories, and the file
                names, are normalised to absolute paths prior to the
                replacement. If False (the default) then no
                normalisation is done.""",
    # ----------------------------------------------------------------
    # Method description substitutions (4 levels of indentation)
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
}
