from functools import partial
from glob import iglob
from logging import getLogger
from os import walk
from os.path import expanduser, expandvars, isdir, join

from uritools import urisplit

from ..decorators import _manage_log_level_via_verbosity
from ..functions import abspath, is_log_level_info
from .abstract import ReadWrite
from .exceptions import DatasetTypeError
from .netcdf import NetCDFRead

logger = getLogger(__name__)


class read(ReadWrite):
    """Read field or domain constructs from a dataset.

    The following file formats are supported: netCDF, CDL, and Zarr.

    NetCDF and Zarr datasets may be on local disk, on an OPeNDAP
    server, or in an S3 object store.

    CDL files must be on local disk.

    Any amount of files of any combination of file types may be read.

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

    **Performance**

    Descriptive properties are always read into memory, but lazy
    loading is employed for all data arrays, unless the *to_memory*
    parameter has been set.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `{{package}}.write`, `{{package}}.Field`,
                 `{{package}}.Domain`, `{{package}}.unique_constructs`

    :Parameters:

        {{read datasets: (arbitrarily nested sequence of) `str`}}

        {{read recursive: `bool`, optional}}

            .. versionadded:: (cfdm) 1.12.2.0

        {{read followlinks: `bool`, optional}}

            .. versionadded:: (cfdm) 1.12.2.0

        {{read cdl_string: `bool`, optional}}

        {{read dataset_type: `None` or (sequence of) `str`, optional}}

            Valid file types are:

            ==============  ==========================================
            *dataset_type*  Description
            ==============  ==========================================
            ``'netCDF'``    A netCDF-3 or netCDF-4 dataset
            ``'CDL'``       A text CDL file of a netCDF dataset
            ``'Zarr'``      A Zarr v2 (xarray) or Zarr v3 dataset
            ==============  ==========================================

            .. versionadded:: (cfdm) 1.12.2.0

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

        ignore_unknown_type: Deprecated at version 1.12.2.0
            Use *dataset_type* instead.

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

    @_manage_log_level_via_verbosity
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

        .. versionadded:: (cfdm) 1.12.2.0

        """
        kwargs = locals()
        kwargs.update(kwargs.pop("kwargs"))

        self = super().__new__(cls)

        # Store the keyword arguments
        self.kwargs = kwargs

        # Actions to be taken before any datasets are been read (which
        # include initialising 'self.constructs' attribute to an empty
        # list).
        self._initialise()

        dataset_type = self.dataset_type
        if not (
            dataset_type is None
            or self.dataset_type.issubset(self.allowed_dataset_types)
        ):
            raise ValueError(
                "'dataset_type' keyword must be None, or a subset of "
                f"{self.allowed_dataset_types}"
            )

        # Loop round the input datasets
        for dataset in self._datasets():
            # Read the dataset
            self._pre_read(dataset)
            self._read(dataset)
            self._post_read(dataset)

            # Add the dataset contents to the output list
            self.n_datasets += 1
            self.constructs.extend(self.dataset_contents)

        # Actions to be taken after all datasets have been read
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

        Each pathname has its tilde and environment variables
        expanded, and is then replaced by all of the pathnames
        matching glob patterns used by the Unix shell.

        A directory is replaced the pathnames of the datasets it
        contains. Subdirectories are recursively searched through only
        if ``self.kwargs['recursive']`` is True. Subdirectories
        pointed to by symlinks are included only if
        ``self.kwargs['followlinks']`` is True.

        Called by `__new__`.

        .. versionadded:: (cfdm) 1.12.2.0

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
                f"Can only set followlinks={followlinks!r} when "
                f"recursive={True}. Got recursive={recursive!r}"
            )

        is_zarr = NetCDFRead.is_zarr

        for datasets1 in datasets:
            # Apply tilde and environment variable expansions
            datasets1 = expanduser(expandvars(datasets1))

            u = urisplit(datasets1)
            if u.scheme not in (None, "file"):
                # Do not glob a remote URI, and assume that it defines
                # a single dataset.
                yield datasets1
                continue

            # Glob files/directories on disk
            datasets1 = abspath(datasets1, uri=False)

            n_datasets = 0
            for x in iglob(datasets1):
                if isdir(x):
                    if is_zarr(x):
                        # This directory is a Zarr dataset, so don't
                        # look in any subdirectories.
                        n_datasets += 1
                        yield x
                        continue

                    # Walk through directories, possibly recursively
                    for path, _, filenames in walk(x, followlinks=followlinks):
                        if NetCDFRead.is_zarr(path):
                            # This directory is a Zarr dataset, so
                            # don't look in any subdirectories.
                            n_datasets += 1
                            yield path
                            break

                        for f in filenames:
                            # This file is a (non-Zarr) dataset
                            n_datasets += 1
                            yield join(path, f)

                        if not recursive:
                            # Don't look in any subdirectories
                            break
                else:
                    # This file is a (non-Zarr) dataset
                    n_datasets += 1
                    yield x

            if not n_datasets:
                raise FileNotFoundError(
                    f"No datasets found from datasets={kwargs['datasets']!r}"
                )

    def _finalise(self):
        """Actions to take after all datasets have been read.

        Called by `__new__`.

        .. versionadded:: (cfdm) 1.12.2.0

        :Returns:

            `None`

        """
        # Sort the output contructs in-place by their netCDF variable
        # names
        constructs = self.constructs
        if len(constructs) > 1:
            constructs.sort(key=lambda f: f.nc_get_variable(""))

    def _initialise(self):
        """Actions to take before any datasets have been read.

        Called by `__new__`.

        .. versionadded:: (cfdm) 1.12.2.0

        :Returns:

            `None`

        """
        kwargs = self.kwargs

        # Parse the 'dataset_type' keyword parameter
        dataset_type = kwargs.get("dataset_type")
        if dataset_type is not None:
            if isinstance(dataset_type, str):
                dataset_type = (dataset_type,)

            dataset_type = set(dataset_type)

        self.dataset_type = dataset_type

        # Recognised netCDF dataset formats
        self.netCDF_dataset_types = set(("netCDF", "CDL", "Zarr"))

        # Allowed dataset formats
        self.allowed_dataset_types = self.netCDF_dataset_types.copy()

        # The output construct type
        self.domain = bool(kwargs["domain"])
        self.field = not self.domain
        self.construct = "domain" if self.domain else "field"

        # Initialise the number of successfully read of datasets
        self.n_datasets = 0

        # Initialise the list of output constructs
        self.constructs = []

        # Initialise the set of different dataset categories.
        self.unique_dataset_categories = set()

    def _post_read(self, dataset):
        """Actions to take immediately after reading a dataset.

        Called by `__new__`.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            dataset: `str`
                The pathname of the dataset that has just been read.

        :Returns:

            `None`

        """
        if self.dataset_contents is None:
            # Raise any "unknown format" errors
            if self.dataset_format_errors:
                error = "\n".join(map(str, self.dataset_format_errors))
                raise DatasetTypeError(f"\n{error}")

            self.dataset_contents = []

    def _pre_read(self, dataset):
        """Actions to take immediately before reading a dataset.

        Called by `__new__`.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            dataset: `str`
                The pathname of the dataset to be read.

        :Returns:

            `None`

        """
        # Initialise the contents of the dataset. If the dataset is
        # valid then this will get replaced by a (possibly empty) list
        # of the contents.
        self.dataset_contents = None

        # Initialise the list of unknown-format errors arising from
        # trying to read the read dataset. If, after reading, there
        # are any unknown-format errors then they will get raised, but
        # only if `dataset_contents` is still None. Note that when
        # unknown-format errors arise prior to a successful
        # interpretation of the dataset, the errors are not raised
        # because `dataset_contents` will no longer be None.
        self.dataset_format_errors = []

    def _read(self, dataset):
        """Read a given dataset into field or domain constructs.

        The constructs are stored in the `dataset_contents` attribute.

        Called by `__new__`.

        .. versionadded:: (cfdm) 1.12.2.0

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
                netcdf_kwargs = {
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

                self.netcdf_read = partial(
                    NetCDFRead(self.implementation).read, **netcdf_kwargs
                )

            try:
                # Try to read the dataset
                self.dataset_contents = self.netcdf_read(dataset)
            except DatasetTypeError as error:
                if dataset_type is None:
                    self.dataset_format_errors.append(error)
            else:
                # Successfully read the dataset
                self.unique_dataset_categories.add("netCDF")

        if self.dataset_contents is not None:
            # Successfully read the dataset
            return
