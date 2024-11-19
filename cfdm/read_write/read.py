import os

from numpy.ma.core import MaskError

from ..cfdmimplementation import implementation
from ..core import DocstringRewriteMeta
from ..docstring import _docstring_substitution_definitions
from .netcdf import NetCDFRead


class read(metaclass=DocstringRewriteMeta):
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
    loading is employed for all data arrays, which means that no data
    is read into memory until the data is required for inspection or
    to modify the array contents. TODOCFA This maximises the number of field
    constructs that may be read within a session, and makes the read
    operation fast.

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

        {{read netcdf_engine: `None` or `str`, optional}}

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

    implementation = implementation()

    def __new__(
        cls,
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
        cache=True,
        dask_chunks="storage-aligned",
        store_hdf5_chunks=True,
        cfa=None,
        cfa_write=None,
        to_memory=False,
        extra_read_vars=None,
    ):
        """TODOCFA."""
        # Initialise a netCDF read object
        netcdf = NetCDFRead(cls.implementation)
        cls.netcdf = netcdf

        filename = os.path.expanduser(os.path.expandvars(filename))

        if netcdf.is_dir(filename):
            raise IOError(f"Can't read directory {filename}")

        if not netcdf.is_file(filename):
            raise IOError(f"Can't read non-existent file {filename}")

        cdl = False
        if netcdf.is_cdl_file(filename):
            # Create a temporary netCDF file from input CDL
            cdl = True
            cdl_filename = filename
            filename = netcdf.cdl_to_netcdf(filename)

        if netcdf.is_netcdf_file(filename):
            # See https://github.com/NCAS-CMS/cfdm/issues/128 for
            # context on the try/except here, which acts as a
            # temporary fix pending decisions on the best way to
            # handle CDL with only header or coordinate info.
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
                    cache=cache,
                    dask_chunks=dask_chunks,
                    store_hdf5_chunks=store_hdf5_chunks,
                    cfa=cfa,
                    cfa_write=cfa_write,
                    to_memory=to_memory,
                    extra_read_vars=extra_read_vars,
                )
            except MaskError:
                # Some data required for field interpretation is
                # missing, manifesting downstream as a NumPy
                # MaskError.
                if cdl:
                    raise ValueError(
                        "Unable to convert CDL without data to field "
                        "construct(s) because there is insufficient "
                        "information provided by the header and/or "
                        "coordinates alone in this case."
                    )
                else:
                    raise ValueError(
                        "Unable to convert netCDF to field construct(s) "
                        "because there is missing data."
                    )
        elif cdl:
            raise IOError(
                f"Can't determine format of file {filename} "
                f"generated from CDL file {cdl_filename}"
            )
        else:
            raise IOError(f"Can't determine format of file {filename}")

        # Return the field or domain constructs
        return fields

    def __docstring_substitutions__(self):
        """Defines applicable docstring substitutions.

        Substitutons are considered applicable if they apply to this
        class as well as all of its subclasses.

        These are in addtion to, and take precendence over, docstring
        substitutions defined by the base classes of this class.

        See `_docstring_substitutions` for details.

        .. versionaddedd:: (cfdm) 1.8.8.0

        :Returns:

            `dict`
                The docstring substitutions that have been applied.

        """
        return _docstring_substitution_definitions

    def __docstring_package_depth__(self):
        """Returns the package depth for {{package}} substitutions.

        See `_docstring_package_depth` for details.

        .. versionaddedd:: (cfdm) 1.8.8.0

        """
        return 0
