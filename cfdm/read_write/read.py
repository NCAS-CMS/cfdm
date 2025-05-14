from glob import iglob
from logging import getLogger
from os import walk
from os.path import expanduser, expandvars, isdir, join

from uritools import urisplit

from ..functions import is_log_level_info

from .abstract import ReadWrite
from .exceptions import DatasetTypeError
from .netcdf import NetCDFRead

logger = getLogger(__name__)


class read(ReadWrite):
    """Read field or domain constructs from a dataset.

    The following file formats are supported: netCDF and CDL.

    NetCDF files may be on local disk, on an OPeNDAP server, or in an
    S3 object store.

    The returned constructs are sorted by the netCDF variable names of
    their corresponding data or domain variables.

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

    **Zarr files**

    TODOZARR

    **Performance**

    Descriptive properties are always read into memory, but lazy
    loading is employed for all data arrays, unless the *to_memory*
    parameter has been set.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `{{package}}.write`, `{{package}}.Field`,
                 `{{package}}.Domain`, `{{package}}.unique_constructs`

    :Parameters:

        {{read dataset: (arbitrarily nested sequence of) `str`}}

        {{read external: (sequence of) `str`, optional}}

        {{read extra: (sequence of) `str`, optional}}

        {{read verbose: `int` or `str` or `None`, optional}}

        {{read warnings: `bool`, optional}}

        {{read warn_valid: `bool`, optional}}

            .. versionadded:: (cfdm) 1.8.3

        {{read mask: `bool`, optional}}

            .. versionadded:: (cfdm) 1.8.2

        {{read unpack: `bool`}}

            .. versionadded:: (cfdm) 1.11.2.0

        {{read domain: `bool`, optional}}

            .. versionadded:: (cfdm) 1.9.0.0

        {{read netcdf_backend: `None` or (sequence of) `str`, optional}}

            .. versionadded:: (cfdm) 1.11.2.0

        {{read storage_options: `dict` or `None`, optional}}

            .. versionadded:: (cfdm) 1.11.2.0

        {{read cache: `bool`, optional}}

            .. versionadded:: (cfdm) 1.11.2.0

        {{read dask_chunks: `str`, `int`, `None`, or `dict`, optional}}

              .. versionadded:: (cfdm) 1.11.2.0

        {{read store_dataset_chunks: `bool`, optional}}

            .. versionadded:: (cfdm) 1.11.2.0

        {{read cfa: `dict`, optional}}

            .. versionadded:: (cfdm) 1.12.0.0

        {{read cfa_write: (sequence of) `str`, optional}}

            .. versionadded:: (cfdm) 1.12.0.0

        {{read to_memory: (sequence of) `str`, optional}}

            .. versionadded:: (cfdm) 1.12.0.0

        {{read squeeze: `bool`, optional}}

            .. versionadded:: (cfdm) 1.12.0.0

        {{read unsqueeze: `bool`, optional}}

            .. versionadded:: (cfdm) 1.12.0.0

        {{read dataset_type: `None` or (sequence of) `str`, optional}}

            Valid file types are:

            ============  ============================================
            file type     Description
            ============  ============================================
            ``'netCDF'``  Binary netCDF-3 or netCDF-4 files
            ``'CDL'``     Text CDL representations of netCDF files
            ============  ============================================

            .. versionadded:: (cfdm) 1.12.0.0

        {{read ignore_unknown_type: `bool`, optional}}

            .. versionadded:: (cfdm) 1.12.0.0

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
        store_dataset_chunks=True,
        cfa=None,
        cfa_write=None,
        to_memory=False,
        squeeze=False,
        unsqueeze=False,
        dataset_type=None,
        recursive=False,
        followlinks=False,
        cdl_string=False,
        extra_read_vars=None,
        **kwargs,
    ):
        """Read field or domain constructs from datasets.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        kwargs = locals()
        kwargs.update(kwargs.pop("kwargs"))

        self = super().__new__(cls)
        self.kwargs = kwargs

        # Actions to take before any datasets have been read
        self._initialise()

        # Loop round the input datasets
        for dataset in self._datasets():
            # Read the dataset
            self._pre_read(dataset)
            self._read(dataset)
            self._post_read(dataset)

            # Add its contents to the output list
            self.constructs.extend(self.dataset_contents)

        # Actions to take after all datasets have been read
        self._finalise()

        if is_log_level_info(logger):
            n = len(self.constructs)
            n_datasets = self.n_datasets
            logger.info(
                f"Read {n} {self.construct}{'s' if n != 1 else ''} "
                f"from {n_datasets} dataset{'s' if n_datasets != 1 else ''}"
            )  # pragma: no cover

        # Return the field or domain constructs
        return self.constructs

    def _datasets(self):
        """Find all of the datasets.

        The datset pathnames are defined by
        ``self.kwargs['datasets']``.

        Each pathname has tilde and environment variables exapanded,
        and is then replaced by all of the pathnames matching glob
        patterns used by the Unix shell.

        A directory is replaced the pathnames of the files it
        contains. If ``self.kwargs['recursive']`` is True then
        subdirectories are recursively searched through. If
        ``self.kwargs['followlinks']`` is True then subdirectories
        pointed to by symlinks are included.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            generator
                An iterator over the dataset pathnames.

        """
        kwargs = self.kwargs
        recursive = kwargs.get("recursive", False)
        followlinks = kwargs.get("followlinks", False)

        datasets = self._flat(kwargs["datasets"])
        if kwargs["cdl_string"]:
            # Return CDL strings as they are
            for dataset1 in datasets:
                # This is a CDL string
                yield dataset1

            return

        if followlinks and not recursive:
            raise ValueError(
                f"Can't set followlinks={followlinks!r} when "
                f"recursive={recursive!r}"
            )

        for datasets1 in datasets:
            datasets1 = expanduser(expandvars(datasets1))

            u = urisplit(datasets1)
            if u.scheme not in (None, "file"):
                # Do not glob a remote URI, and assume that it defines
                # a single dataset.
                yield datasets1
                continue

            # Glob files/directories on disk
            datasets1 = u.path

            n_datasets = 0
            for x in iglob(datasets1):
                if isdir(x):
                    if NetCDFRead._is_zarr(x):
                        # This directory is a Zarr dataset. Don't look
                        # in any subdirectories.
                        n_datasets += 1
                        yield x
                        continue

                    # Walk through directories, possibly recursively
                    for path, _, filenames in walk(x, followlinks=followlinks):
                        if NetCDFRead.is_zarr(path):
                            # This directory is a Zarr dataset. Don't
                            # look in any subdirectories.
                            n_datasets += 1
                            yield path
                            break

                        for f in filenames:
                            # This file is a dataset
                            n_datasets += 1
                            yield join(path, f)

                        if not recursive:
                            # Don't look in any subdirectories
                            break
                else:
                    # This file is a dataset
                    n_datasets += 1
                    yield x

            if not n_datasets:
                raise FileNotFoundError(
                    f"No datasets found from {kwargs['datasets']}"
                )

    def _finalise(self):
        """Actions to take after all datasets have been read.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `None`

        """
        # Sort the output contructs by netCDF variable name
        out = self.constructs
        n = len(out)
        if n > 1:
            out.sort(key=lambda f: f.nc_get_variable(""))

    def _initialise(self):
        """Actions to take before any datasets have been read.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `None`

        """
        kwargs = self.kwargs

        # Parse the 'dataset_type' keyword parameter
        dataset_type = kwargs.get("dataset_type")
        if dataset_type is None:
            self.dataset_type = None
        else:
            if isinstance(dataset_type, str):
                dataset_type = (dataset_type,)

            self.dataset_type = set(dataset_type)

        # Recognised netCDF datsets formats
        self.netCDF_dataset_types = set(("netCDF", "CDL", "Zarr"))

        # The output construct type
        self.domain = bool(kwargs["domain"])
        self.construct = "domain" if self.domain else "field"

        # Initialise the number of successfully read of datasets
        self.n_datasets = 0

        # Initialise the list of output constructs
        self.constructs = []

    def _post_read(self, dataset):
        """Actions to take immediately after reading a given dataset.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            dataset: `str`
                The pathname of the dataset that has just been read.

        :Returns:

            `None`

        """
        # Raise any unknown-format errors
        if self.dataset_format_errors:
            error = "\n".join(map(str, self.dataset_format_errors))
            raise DatasetTypeError(f"\n{error}")

    def _pre_read(self, dataset):
        """Actions to take immediately before reading a given dataset.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            dataset: `str`
                The pathname of the dataset to be read.

        :Returns:

            `None`

        """
        # Initialise the list of constructs in the dataset
        self.dataset_contents = []

        # Initialise the list of unknown-format errors arising from
        # trying to the read dataset
        self.dataset_format_errors = []

        # Initialise the dataset type
        self.dataset_type = None

    def _read(self, dataset):
        """Read a given dataset into field or domain constructs.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            dataset: `str`
                The pathname of the dataset to be read.

        :Returns:

            `None`

        """
        dataset_type = self.dataset_type
        if dataset_type is None or dataset_type.intersection(
            self.netCDF_dataset_types
        ):
            # --------------------------------------------------------
            # Try to read as a netCDF dataset
            # --------------------------------------------------------
            if not hasattr(self, "netcdf_read"):
                # Initialise the netCDF read function
                kwargs = self.kwargs
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
                        "store_dataset_chunks",
                        "cfa",
                        "cfa_write",
                        "to_memory",
                        "squeeze",
                        "unsqueeze",
                        "dataset_type",
                        "cdl_string",
                        "extra_read_vars",
                    )
                }
                self.netcdf_read = NetCDFRead(self.implementation).read

            try:
                self.dataset_contents = self.netcdf_read(
                    dataset, **self.netcdf_kwargs
                )
            except DatasetTypeError as error:
                if dataset_type is None:
                    self.dataset_format_errors.append(error)
            else:
                self.dataset_format_errors = []
                self.n_datasets += 1
                self.dataset_type = "netCDF"
