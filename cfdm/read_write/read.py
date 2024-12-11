from glob import iglob
from os import walk
from os.path import expanduser, expandvars, isdir, join

from uritools import urisplit

from .abstract import ReadWrite
from .exceptions import FileTypeError
from .netcdf import NetCDFRead


class read(ReadWrite):
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
    `~{{package}}.DomainAxis.nc_is_unlimited` and
    `~{{package}}.DomainAxis.nc_set_unlimited` methods of a domain
    axis construct.

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
    `~{{package}}.Field.dataset_compliance` method of the returned
    constructs, as well as optionally displayed when the dataset is
    read by setting the *warnings* parameter.


    **Performance**

    Descriptive properties are always read into memory, but lazy
    loading is employed for all data arrays, unless the *to_memory*
    parameter has been set.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `{{package}}.write`, `{{package}}.Field`,
                 `{{package}}.Domain`, `{{package}}.unique_constructs`

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

        {{read external: (sequence of) `str`, optional}}

        {{read extra: (sequence of) `str`, optional}}

        {{read verbose: `int` or `str` or `None`, optional}}

        {{read warnings: `bool`, optional}}

        {{read warn_valid: `bool`, optional}}

            .. versionadded:: (cfdm) 1.8.3

        {{read mask: `bool`, optional}}

            .. versionadded:: (cfdm) 1.8.2

        {{read unpack: `bool`}}

            .. versionadded:: (cfdm) NEXTVERSION

        {{read domain: `bool`, optional}}

            .. versionadded:: (cfdm) 1.9.0.0

        {{read netcdf_backend: `None` or (sequence of) `str`, optional}}

            .. versionadded:: (cfdm) NEXTVERSION

        {{read storage_options: `dict` or `None`, optional}}

            .. versionadded:: (cfdm) NEXTVERSION

        {{read cache: `bool`, optional}}

            .. versionadded:: (cfdm) NEXTVERSION

        {{read dask_chunks: `str`, `int`, `None`, or `dict`, optional}}

              .. versionadded:: (cfdm) NEXTVERSION

        {{read store_hdf5_chunks: `bool`, optional}}

            .. versionadded:: (cfdm) NEXTVERSION

        {{read cfa: `dict`, optional}}

            .. versionadded:: (cfdm) NEXTVERSION

        {{read cfa_write: (sequence of) `str`, optional}}

            .. versionadded:: (cfdm) NEXTVERSION

        {{read to_memory: (sequence of) `str`, optional}}

            .. versionadded:: (cfdm) NEXTVERSION

        {{read squeeze: `bool`, optional}}

            .. versionadded:: (cfdm) NEXTVERSION

        {{read unsqueeze: `bool`, optional}}

            .. versionadded:: (cfdm) NEXTVERSION

        {{read file_type: `None` or (sequence of) `str`, optional}}

            Valid file types are:

            ============  ============================================
            file type     Description
            ============  ============================================
            ``'netCDF'``  Binary netCDF-3 or netCDF-4 files
            ``'CDL'``     Text CDL representations of netCDF files
            ============  ============================================

            .. versionadded:: (cfdm) NEXTVERSION

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

    def __new__(
        cls,
        datasets,
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
        cache=True,
        dask_chunks="storage-aligned",
        store_hdf5_chunks=True,
        cfa=None,
        cfa_write=None,
        to_memory=False,
        squeeze=False,
        unsqueeze=False,
        file_type=None,
        recursive=False,
        followlinks=False,
        extra_read_vars=None,
    ):
        """Read field or domain constructs from datasets.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        kwargs = locals()
        self = super().__new__(cls)

        self.kwargs = kwargs

        self._initialise()

        for dataset in self._datasets():
            self._pre_read_dataset(dataset)
            self._read_dataset(dataset)
            self._post_read_dataset(dataset)

            # Add this dataset's contents to that already read from
            # other files.
            #
            # Note that `self.out` is defined in `_initialise`; and
            # `self.file_contents` is defined in `_pre_read_dataset`
            # and updated in `_read_dataset`
            self.out.extend(self.file_contents)

        self._finalise()

        # Return the field or domain constructs
        return self.out

    def _datasets(self):
        """TODOREAD.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        kwargs = self.kwargs
        recursive = kwargs.get("recursive", False)
        followlinks = kwargs.get("followlinks", False)

        if followlinks and not recursive:
            raise ValueError(
                f"Can't set followlinks={followlinks!r} when "
                f"recursive={recursive!r}"
            )

        for datasets1 in self._flat(kwargs["datasets"]):
            datasets1 = expanduser(expandvars(datasets1))

            u = urisplit(datasets1)
            scheme = u.scheme
            if scheme not in (None, "file"):
                # Assume that remote URIs are not directories, and do
                # not glob them.
                yield datasets1
                continue

            # Glob files/directories on disk
            if scheme == "file":
                datasets1 = u.path

            n_datasets = 0
            for x in iglob(datasets1):
                if isdir(x):
                    # Walk through directories, possibly recursively
                    for path, _, filenames in walk(x, followlinks=followlinks):
                        for f in filenames:
                            # File in this directory
                            n_datasets += 1
                            yield join(path, f)

                        if not recursive:
                            break
                else:
                    # File, not a directory
                    n_datasets += 1
                    yield x

            if not n_datasets:
                raise FileNotFoundError(f"No such dataset(s): {datasets1}")

    def _finalise(self):
        """TODOREAD.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        # Sort by netCDF variable name
        out = self.out
        if len(out) > 1:
            out.sort(key=lambda f: f.nc_get_variable(""))

    def _initialise(self):
        """TODOREAD.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        kwargs = self.kwargs

        # ------------------------------------------------------------
        # Parse the 'file_type' keyword parameter
        # ------------------------------------------------------------
        file_type = kwargs.get("file_type")
        if file_type is not None:
            if isinstance(file_type, str):
                file_type = (file_type,)

            self.file_type = set(file_type)
        else:
            self.file_type = file_type

        # Set the netCDF read function and its keyword arguments
        self.netCDF_file_types = set(("netCDF", "CDL"))
        self.netcdf_read = NetCDFRead(self.implementation).read
        self.netcdf_kwargs = {
            key: kwargs[key]
            for key in (
                "external",
                "extra",
                "verbose",
                "warnings",
                "warn_valid",
                "mask",
                "unpack",
                "domain",
                "storage_options",
                "netcdf_backend",
                "cache",
                "dask_chunks",
                "store_hdf5_chunks",
                "cfa",
                "cfa_write",
                "to_memory",
                "squeeze",
                "unsqueeze",
                "file_type",
                "extra_read_vars",
            )
        }

        # Initialise the list of output fields/domains
        self.out = []

    @staticmethod
    def _plural(n):
        """Return a suffix which reflects a word's plural.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return "s" if n != 1 else ""

    def _pre_read_dataset(self, dataset):
        """TODOREAD.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        self.file_contents = []
        self.file_format_errors = []
        self.ftype = None

    def _read_dataset(self, dataset):
        """TODOREAD.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        # Try to read as netCDF dataset
        file_type = self.file_type
        if file_type is None or file_type.intersection(self.netCDF_file_types):
            try:
                self.file_contents = self.netcdf_read(
                    dataset, **self.netcdf_kwargs
                )
            except FileTypeError as error:
                if file_type is None:
                    self.file_format_errors.append(error)
            else:
                self.file_format_errors = []
                self.ftype = "netCDF"

    def _post_read_dataset(self, dataset):
        """TODOREAD.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        if self.file_format_errors:
            error = "\n".join(map(str, self.file_format_errors))
            raise FileTypeError(f"\n{error}")
