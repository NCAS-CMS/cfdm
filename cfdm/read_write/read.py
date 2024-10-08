import os

from numpy.ma.core import MaskError

from ..cfdmimplementation import implementation
from .netcdf import NetCDFRead

_implementation = implementation()


def read(
    filename,
    external=None,
    extra=None,
    verbose=None,
    warnings=False,
    warn_valid=False,
    mask=True,
    unpack=True,
    domain=False,
    netcdf_backend=None,
    storage_options=None,
    store_hdf5_chunks=True,
    _implementation=_implementation,
):
    """Read field or domain constructs from a dataset.

    The following file formats are supported: netCDF and CDL.

    NetCDF files may be on local disk, on an OPeNDAP server, or in an
    S3 object store.

    The returned constructs are sorted by the netCDF variable names of
    their corresponding data or domain variables.

    **CDL files**

    A file is considered to be a CDL representation of a netCDF
    dataset if it is a text file whose first non-comment line starts
    with the seven characters "netcdf " (six letters followed by a
    space). A comment line is identified as one which starts with any
    amount white space (including none) followed by "//" (two
    slashes). It is converted to a temporary netCDF4 file using the
    external ``ncgen`` command, and the temporary file persists until
    the end of the Python session, at which time it is automatically
    deleted. The CDL file may omit data array values (as would be the
    case, for example, if the file was created with the ``-h`` or
    ``-c`` option to ``ncdump``), in which case the the relevant
    constructs in memory will be created with data with all missing
    values.

    **NetCDF unlimited dimensions**

    Domain axis constructs that correspond to NetCDF unlimited
    dimensions may be accessed with the
    `~cfdm.DomainAxis.nc_is_unlimited` and
    `~cfdm.DomainAxis.nc_set_unlimited` methods of a domain axis
    construct.

    **NetCDF hierarchical groups**

    Hierarchical groups in CF provide a mechanism to structure
    variables within netCDF4 datasets. Field constructs are
    constructed from grouped datasets by applying the well defined
    rules in the CF conventions for resolving references to
    out-of-group netCDF variables and dimensions. The group structure
    is preserved in the field construct's netCDF interface. Groups
    were incorporated into CF-1.8. For files with groups that state
    compliance to earlier versions of the CF conventions, the groups
    will be interpreted as per the latest release of the CF
    conventions.

    **CF-compliance**

    If the dataset is partially CF-compliant to the extent that it is
    not possible to unambiguously map an element of the netCDF dataset
    to an element of the CF data model, then a field construct is
    still returned, but may be incomplete. This is so that datasets
    which are partially conformant may nonetheless be modified in
    memory and written to new datasets.

    Such "structural" non-compliance would occur, for example, if the
    "coordinates" attribute of a CF-netCDF data variable refers to
    another variable that does not exist, or refers to a variable that
    spans a netCDF dimension that does not apply to the data
    variable. Other types of non-compliance are not checked, such
    whether or not controlled vocabularies have been adhered to. The
    structural compliance of the dataset may be checked with the
    `~cfdm.Field.dataset_compliance` method of the returned
    constructs, as well as optionally displayed when the dataset is
    read by setting the *warnings* parameter.


    **Performance**

    Descriptive properties are always read into memory, but lazy
    loading is employed for all data arrays, which means that no data
    is read into memory until the data is required for inspection or
    to modify the array contents. This maximises the number of field
    constructs that may be read within a session, and makes the read
    operation fast.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `cfdm.write`, `cfdm.Field`, `cfdm.Domain`,
                 `cfdm.unique_constructs`

    :Parameters:

        filename: `str`
            The file name or OPenDAP URL of the dataset.

            Relative paths are allowed, and standard tilde and shell
            parameter expansions are applied to the string.

            *Parameter example:*
              The file ``file.nc`` in the user's home directory could
              be described by any of the following:
              ``'$HOME/file.nc'``, ``'${HOME}/file.nc'``,
              ``'~/file.nc'``, ``'~/tmp/../file.nc'``.

        external: (sequence of) `str`, optional
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
              ``external=('cell_measure_A.nc', 'cell_measure_O.nc')``

        extra: (sequence of) `str`, optional
            Create extra, independent fields from netCDF variables
            that correspond to particular types metadata constructs.
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
            `~cfdm.Field.convert` method of a returned field
            construct, instead of setting the *extra* parameter.

        verbose: `int` or `str` or `None`, optional
            If an integer from ``-1`` to ``3``, or an equivalent string
            equal ignoring case to one of:

            * ``'DISABLE'`` (``0``)
            * ``'WARNING'`` (``1``)
            * ``'INFO'`` (``2``)
            * ``'DETAIL'`` (``3``)
            * ``'DEBUG'`` (``-1``)

            set for the duration of the method call only as the minimum
            cut-off for the verboseness level of displayed output (log)
            messages, regardless of the globally-configured `cfdm.log_level`.
            Note that increasing numerical value corresponds to increasing
            verbosity, with the exception of ``-1`` as a special case of
            maximal and extreme verbosity.

            Otherwise, if `None` (the default value), output messages will
            be shown according to the value of the `cfdm.log_level` setting.

            Overall, the higher a non-negative integer or equivalent string
            that is set (up to a maximum of ``3``/``'DETAIL'``) for
            increasing verbosity, the more description that is printed to
            convey how the contents of the netCDF file were parsed and
            mapped to CF data model constructs.

        warnings: `bool`, optional
            If True then print warnings when an output field construct
            is incomplete due to structural non-compliance of the
            dataset. By default such warnings are not displayed.

        warn_valid: `bool`, optional
            If True then print a warning for the presence of
            ``valid_min``, ``valid_max`` or ``valid_range`` properties
            on field constructs and metadata constructs that have
            data. By default no such warning is issued.

            "Out-of-range" data values in the file, as defined by any
            of these properties, are automatically masked by default,
            which may not be as intended. See the *mask* parameter for
            turning off all automatic masking.

            See
            https://ncas-cms.github.io/cfdm/tutorial.html#data-mask
            for details.

            .. versionadded:: (cfdm) 1.8.3

        mask: `bool`, optional
            If True (the default) then mask by convention the data of
            field and metadata constructs.

            A netCDF array is masked depending on the values of any of
            the netCDF attributes ``_FillValue``, ``missing_value``,
            ``_Unsigned``, ``valid_min``, ``valid_max``, and
            ``valid_range``.

            See
            https://ncas-cms.github.io/cfdm/tutorial.html#data-mask
            for details.

            .. versionadded:: (cfdm) 1.8.2

        unpack: `bool`
            If True, the default, then unpack arrays by convention
            when the data is read from disk.

            Unpacking is determined by netCDF conventions for the
            following variable attributes: ``add_offset``,
            ``scale_factor``, and ``_Unsigned``.

            .. versionadded:: (cfdm) NEXTVERSION

        domain: `bool`, optional
            If True then return only the domain constructs that are
            explicitly defined by CF-netCDF domain variables, ignoring
            all CF-netCDF data variables. By default only the field
            constructs defined by CF-netCDF data variables are
            returned.

            CF-netCDF domain variables are only defined from CF-1.9,
            so older datasets automatically contain no CF-netCDF
            domain variables.

            The unique domain constructs of the dataset are easily
            found with the `cfdm.unique_constructs` function. For
            example::

               >>> d = cfdm.read('file.nc', domain=True)
               >>> ud = cfdm.unique_constructs(d)
               >>> f = cfdm.read('file.nc')
               >>> ufd = cfdm.unique_constructs(x.domain for x in f)

            .. versionadded:: (cfdm) 1.9.0.0

        netcdf_eninge: `None` or `str`, optional
            Specify which library to use for opening and reading
            netCDF files. By default, or if `None`, then the first one
            of `netCDF4` and `h5netcdf` to successfully open the
            netCDF file is used. Setting *netcdf_backend* to one of
            ``'netCDF4'`` and ``'h5netcdf'`` will force the use of
            that library.

            .. versionadded:: (cfdm) NEXTVERSION

        storage_options: `dict` or `None`, optional
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
                {'region_name': 'fr-par'}}``

            .. versionadded:: (cfdm) NEXTVERSION

        store_hdf5_chunks: `bool`, optional
            If True (the default) then store the HDF5 chunking
            strategy for each returned data array. The HDF5 chunking
            strategy is then accessible via an object's
            `nc_hdf5_chunksizes` method. When the HDF5 chunking
            strategy is stored, it will be used when the data is
            written to a new netCDF4 file with `cfdm.write` (unless
            the strategy was modified prior to writing).

            If False, or if the file being read is not in netCDF4
            format, then no HDF5 chunking strategy is stored.
            (i.e. an `nc_hdf5_chunksizes` method will return `None`
            for all `Data` objects). In this case, when the data is
            written to a new netCDF4 file, the HDF5 chunking strategy
            will be determined by `cfdm.write`.

            See the `cfdm.write` *hdf5_chunks* parameter for details
            on how the HDF5 chunking strategy is determined at the
            time of writing.

            .. versionadded:: (cfdm) NEXTVERSION

        _implementation: (subclass of) `CFDMImplementation`, optional
            Define the CF data model implementation that provides the
            returned field constructs.

    :Returns:

        `list` of `Field` or `Domain`
            The field constructs found in the dataset, or the domain
            constructs if *domain* is True. The list may be empty.

    **Examples**

    >>> x = cfdm.read('file.nc')
    >>> print(type(x))
    <type 'list'>

    Read a file and create field constructs from CF-netCDF data
    variables as well as from the netCDF variables that correspond to
    particular types metadata constructs:

    >>> f = cfdm.read('file.nc', extra='domain_ancillary')
    >>> g = cfdm.read('file.nc', extra=['dimension_coordinate',
    ...                                 'auxiliary_coordinate'])

    Read a file that contains external variables:

    >>> h = cfdm.read('parent.nc')
    >>> i = cfdm.read('parent.nc', external='external.nc')
    >>> j = cfdm.read('parent.nc', external=['external1.nc', 'external2.nc'])

    """
    # Initialise a netCDF read object
    netcdf = NetCDFRead(_implementation)

    # Parse the field parameter
    if extra is None:
        extra = ()
    elif isinstance(extra, str):
        extra = (extra,)

    filename = os.path.expanduser(os.path.expandvars(filename))

    if netcdf.is_dir(filename):
        raise IOError(f"Can't read directory {filename}")

    if not netcdf.is_file(filename):
        raise IOError(f"Can't read non-existent file {filename}")

    # ----------------------------------------------------------------
    # Read the file into field/domain contructs
    # ----------------------------------------------------------------
    cdl = False
    if netcdf.is_cdl_file(filename):
        # Create a temporary netCDF file from input CDL
        cdl = True
        cdl_filename = filename
        filename = netcdf.cdl_to_netcdf(filename)

    if netcdf.is_netcdf_file(filename):
        # See https://github.com/NCAS-CMS/cfdm/issues/128 for context
        # on the try/except here, which acts as a temporary fix
        # pending decisions on the best way to handle CDL with only
        # header or coordinate info.
        try:
            fields = netcdf.read(
                filename,
                external=external,
                extra=extra,
                verbose=verbose,
                warnings=warnings,
                warn_valid=warn_valid,
                mask=mask,
                unpack=unpack,
                domain=domain,
                storage_options=storage_options,
                netcdf_backend=netcdf_backend,
                store_hdf5_chunks=store_hdf5_chunks,
                extra_read_vars=None,
            )
        except MaskError:
            # Some data required for field interpretation is missing,
            # manifesting downstream as a NumPy MaskError.
            if cdl:
                raise ValueError(
                    "Unable to convert CDL without data to field construct(s) "
                    "because there is insufficient information provided by "
                    "the header and/or coordinates alone in this case."
                )
            else:
                raise ValueError(
                    "Unable to convert netCDF to field construct(s) because "
                    "there is missing data."
                )
    elif cdl:
        raise IOError(
            f"Can't determine format of file {filename} "
            f"generated from CDL file {cdl_filename}"
        )
    else:
        raise IOError(f"Can't determine format of file {filename}")

    # ----------------------------------------------------------------
    # Return the field or domain constructs
    # ----------------------------------------------------------------
    return fields
