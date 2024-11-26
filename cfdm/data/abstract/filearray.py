from copy import deepcopy
from os import sep
from os.path import join
from urllib.parse import urlparse

from s3fs import S3FileSystem
from uritools import isuri, urisplit

from ...functions import abspath, dirname
from . import Array


class FileArray(Array):
    """Abstract base class for an array in a file.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def __init__(
        self,
        filename=None,
        address=None,
        dtype=None,
        shape=None,
        mask=True,
        unpack=True,
        attributes=None,
        storage_options=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            filename: (sequence of `str`), optional
                The locations of datasets containing the array.

            address: (sequence of `str`), optional
                How to find the array in the datasets.

            dtype: `numpy.dtype`, optional
                The data type of the array. May be `None` if is not
                known. This may differ from the data type of the
                array in the datasets.

            shape: `tuple`, optional
                The shape of the dataset array.

            {{init mask: `bool`, optional}}

            {{init unpack: `bool`, optional}}

            {{init attributes: `dict` or `None`, optional}}

                If *attributes* is `None`, the default, then the
                attributes will be set during the first `__getitem__`
                call.

            {{init storage_options: `dict` or `None`, optional}}

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(source=source, copy=copy)

        if source is not None:
            try:
                shape = source._get_component("shape", None)
            except AttributeError:
                shape = None

            try:
                filename = source._get_component("filename", None)
            except AttributeError:
                filename = None

            try:
                address = source._get_component("address", None)
            except AttributeError:
                address = None

            try:
                dtype = source._get_component("dtype", None)
            except AttributeError:
                dtype = None

            try:
                mask = source._get_component("mask", True)
            except AttributeError:
                mask = True

            try:
                unpack = source._get_component("unpack", True)
            except AttributeError:
                unpack = True

            try:
                attributes = source._get_component("attributes", None)
            except AttributeError:
                attributes = None

            try:
                storage_options = source._get_component(
                    "storage_options", None
                )
            except AttributeError:
                storage_options = None

        if shape is not None:
            self._set_component("shape", shape, copy=False)

        if filename is not None:
            self._set_component("filename", filename, copy=False)

        if address is not None:
            self._set_component("address", address, copy=False)

        self._set_component("dtype", dtype, copy=False)
        self._set_component("mask", bool(mask), copy=False)
        self._set_component("unpack", bool(unpack), copy=False)

        if storage_options is not None:
            self._set_component("storage_options", storage_options, copy=copy)

        if attributes is not None:
            self._set_component("attributes", attributes, copy=copy)

        # By default, close the netCDF file after data array access
        self._set_component("close", True, copy=False)

    def __getitem__(self, indices):
        """Return a subspace of the array.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the array as an independent numpy array.

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.__getitem__"
        )  # pragma: no cover

    def __repr__(self):  # noqa: D105
        return f"<CF {self.__class__.__name__}{self.shape}: {self}>"

    def __str__(self):  # noqa: D105
        return f"{self.get_filename()}, {self.get_address()}"

    def __dask_tokenize__(self):
        """Return a value fully representative of the object.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return (
            self.__class__,
            self.shape,
            self.get_filename(normalise=True, default=None),
            self.get_address(),
            self.get_mask(),
            self.get_unpack(),
            self.get_attributes(copy=False),
            self.get_storage_options(),
        )

    def _get_array(self, index=None):
        """Returns a subspace of the dataset variable.

        The subspace is defined by the `index` attributes, and is
        applied with `cfdm.netcdf_indexer`.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `__array__`, `index`

        :Parameters:

            {{index: `tuple` or `None`, optional}}

        :Returns:

            `numpy.ndarray`
                The subspace.

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}._get_array"
        )  # pragma: no cover

    @property
    def array(self):
        """Return an independent numpy array containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples**

        >>> n = numpy.asanyarray(a)
        >>> isinstance(n, numpy.ndarray)
        True

        """
        return self[...]

    @property
    def dtype(self):
        """Data-type of the array."""
        return self._get_component("dtype")

    @property
    def shape(self):
        """Shape of the array."""
        return self._get_component("shape")

    def close(self, dataset):
        """Close the dataset containing the data."""
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.close"
        )  # pragma: no cover

    def get_address(self, default=AttributeError()):
        """The name of the file containing the array.

        If there are multiple files then an `AttributeError` is
        raised by default.

        .. versionadded:: (cfdm) 1.10.1.0

        :Parameters:

            default: optional
                Return the value of the *default* parameter if there
                is no file.

                {{default Exception}}

        :Returns:

            `str`
                The file name.

        """
        address = self._get_component("address", None)
        if address is None:
            if default is None:
                return

            return self._default(
                default, f"{self.__class__.__name__} has no address"
            )

        return address

    def file_directory(self, normalise=False, default=AttributeError()):
        """The file directory.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            {{normalise: `bool`, optional}}

        :Returns:

            `str`
                The file directory name.

        **Examples**

        >>> a.get_filename()
        '/data1/file1'

        """
        filename = self.get_filename(normalise=normalise, default=None)
        if filename is None:
            if default is None:
                return

            return self._default(
                default, f"{self.__class__.__name__} has no file name"
            )

        return dirname(filename)

    def get_filename(self, normalise=False, default=AttributeError()):
        """The name of the file containing the array.

        .. versionadded:: (cfdm) 1.10.0.2

        :Parameters:

            {{normalise: `bool`, optional}}

                .. versionadded:: (cfdm) NEXTVERSION

            default: optional
                Return the value of the *default* parameter if there
                is no file name.

                {{default Exception}}

        :Returns:

            `str`
                The file name.

        """
        filename = self._get_component("filename", None)
        if filename is None:
            if default is None:
                return

            return self._default(
                default, f"{self.__class__.__name__} has no file name"
            )

        if normalise:
            filename = abspath(filename)

        return filename

    def get_mask(self):
        """Whether or not to automatically mask the data.

        .. versionadded:: (cfdm) 1.8.2

        **Examples**

        >>> b = a.get_mask()

        """
        return self._get_component("mask")

    def get_storage_options(
        self, create_endpoint_url=True, filename=None, parsed_filename=None
    ):
        """Return `s3fs.S3FileSystem` options for accessing S3 files.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            create_endpoint_url: `bool`, optional
                If True, the default, then create an
                ``'endpoint_url'`` option if and only if one has not
                already been provided. See *filename* and
                *parsed_filename* for details.

            filename: `str`, optional
                Used to set the ``'endpoint_url'`` option if it has
                not been previously defined. Ignored if
                *parsed_filename* has been set.

            parsed_filename: `urllib.parse.ParseResult`, optional
                Used to set the ``'endpoint_url'`` option if it has
                not been previously defined. By default the
                ``'endpoint_url'`` option, if required, is set from
                the file name returned by `get_filename`.

        :Returns:

            `dict` or `None`
                The `s3fs.S3FileSystem` options.

        **Examples**

        >>> f.get_filename()
        's3://store/data/file.nc'
        >>> f.get_storage_options(create_endpoint_url=False)
        {}
        >>> f.get_storage_options()
        {'endpoint_url': 'https://store'}
        >>> f.get_storage_options(filename='s3://other-store/data/file.nc')
        {'endpoint_url': 'https://other-store'}
        >>> f.get_storage_options(create_endpoint_url=False,
        ...                       filename='s3://other-store/data/file.nc')
        {}

        >>> f.get_storage_options()
        {'key': 'scaleway-api-key...',
         'secret': 'scaleway-secretkey...',
         'endpoint_url': 'https://s3.fr-par.scw.cloud',
         'client_kwargs': {'region_name': 'fr-par'}}

        """
        storage_options = self._get_component("storage_options", None)
        if not storage_options:
            storage_options = {}
        else:
            storage_options = deepcopy(storage_options)

        client_kwargs = storage_options.get("client_kwargs", {})
        if (
            create_endpoint_url
            and "endpoint_url" not in storage_options
            and "endpoint_url" not in client_kwargs
        ):
            if parsed_filename is None:
                if filename is None:
                    try:
                        filename = self.get_filename(normalise=False)
                    except AttributeError:
                        pass
                    else:
                        parsed_filename = urlparse(filename)
                else:
                    parsed_filename = urlparse(filename)

            if parsed_filename is not None and parsed_filename.scheme == "s3":
                # Derive endpoint_url from filename
                storage_options["endpoint_url"] = (
                    f"https://{parsed_filename.netloc}"
                )

        return storage_options

    def open(self, func, *args, **kwargs):
        """Return a dataset file object and address.

        When multiple files have been provided an attempt is made to
        open each one, in the order stored, and a file object is
        returned from the first file that exists.

        .. versionadded:: (cfdm) 1.10.1.0

        :Parameters:

            func: callable
                Function that opens a file.

            args, kwargs: optional
                Optional arguments to *func*.

        :Returns:

            2-`tuple`
                The file object for the dataset, and the address of
                the data within the file.

        """
        filename = self.get_filename(normalise=True)
        url = urlparse(filename)
        if url.scheme == "file":
            # Convert a file URI into an absolute path
            filename = url.path
        elif url.scheme == "s3":
            # Create an openable S3 file object
            storage_options = self.get_storage_options(
                create_endpoint_url=True, parsed_filename=url
            )
            fs = S3FileSystem(**storage_options)
            filename = fs.open(url.path[1:], "rb")

        try:
            dataset = func(filename, *args, **kwargs)
        except FileNotFoundError:
            raise FileNotFoundError(f"No such file: {filename}")
        except RuntimeError as error:
            raise RuntimeError(f"{error}: {filename}")

        # Successfully opened a dataset, so return.
        return dataset, self.get_address()

    def replace_directory(self, old=None, new=None, normalise=False):
        """Replace the file directory in-place.

        TODOCFA Every file in *old* that is referenced by the data is
        redefined to be in *new*.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `file_directory`, `get_filename`

        :Parameters:

            old: `str` or `None`, optional
                The base directory structure to be replaced by
                *new*. If `None` (the default) or an empty string, and
                *normalise* is False, then *new* is prepended to each
                file name.

            new: `str` or `None`, optional
                The new directory that replaces the base directory
                structure identified by *old*. If `None` (the default)
                or an empty string, then *old* is replaced with an
                empty string. Otherwise,

            normalise: `bool`, optional
                If True then *old*, *new*, and the file name are
                normalised to absolute paths prior to the
                replacement. If False (the default) then no
                normalisation is done.

        :Returns:

            `{{class}}`
                A new `{{class}}` with modified file locations.

        **Examples**

        >>> a.get_filenames() TODOCFA
        {'/data/file1.nc', '/home/file2.nc'}
        >>> b = a.replace_directory('/data', '/new/data/path/')
        >>> b.get_filenames()
        {'/new/data/path/file1.nc', '/home/file2.nc'}
        >>> c = b.replace_directory('/data', '/archive/location')
        >>> c.get_filenames()
        {'/archive/location/path/file1.nc', '/home/file2.nc'}
        >>> c = b.replace_directory('/archive/location', None)
        >>> c.get_filenames()
        {'path/file1.nc', '/home/file2.nc'}
        >>> c = b.replace_directory('path', '../new_path', normalise=False)
        >>> c.get_filenames()
        {'../new_path/file1.nc', '/home/file2.nc'}
        >>> c = b.replace_directory(None, '/data')
        >>> c.get_filenames()
        {'/data/../new_path/file1.nc', '/home/file2.nc'}
        >>> c = b.replace_directory('/data/../new_path/', None, normalise=False)
        >>> c.get_filenames()
        {'file1.nc', '/home/file2.nc'}
        >>> c = b.replace_directory(None, '/base')
        >>> c.get_filenames()
        {'/base/file1.nc', '/base/home/file2.nc'}

        """
        a = self.copy()

        filename = a.get_filename(normalise=normalise)
        if old or new:
            if normalise:
                if not old:
                    raise ValueError(
                        "When 'normalise' is True and 'new' is a non-empty "
                        "string, 'old' must also be a non-empty string."
                    )

                uri = isuri(filename)
                try:
                    old = dirname(old, normalise=True, uri=uri, isdir=True)
                except ValueError:
                    old = dirname(old, normalise=True, isdir=True)

                u = urisplit(old)
                if not uri and u.scheme == "file":
                    old = u.getpath()

                if new:
                    try:
                        new = dirname(new, normalise=True, uri=uri, isdir=True)
                    except ValueError:
                        new = dirname(new, normalise=True, isdir=True)

            if old:
                if filename.startswith(old):
                    if not new:
                        new = ""
                        if old and not old.endswith(sep):
                            old += sep

                    filename = filename.replace(old, new)
            elif new:
                filename = join(new, filename)

        a._set_component("filename", filename, copy=False)
        return a

    def get_missing_values(self):
        """The missing values of the data.

        Deprecated at version NEXTVERSION. Use `get_attributes` instead.

        """

        class DeprecationError(Exception):
            """Deprecation error."""

            pass

        raise DeprecationError(
            f"{self.__class__.__name__}.get_missing_values was deprecated "
            "at version NEXTVERSION and is no longer available. "
            f"Use {self.__class__.__name__}.get_attributes instead."
        )  # pragma: no cover

    def to_memory(self):
        """Bring data on disk into memory.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `numpy.ndarray`
                The new array.

        """
        return self.array

    def _set_attributes(self, var):
        """Set the netCDF variable attributes.

        These are set from the netCDF variable attributes, but only if
        they have not already been defined, either during {{class}}
        instantiation or by a previous call to `_set_attributes`.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            var: `netCDF4.Variable` or `h5netcdf.Variable`
                The netCDF variable.

        :Returns:

            `dict`
                The attributes.

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}._set_attributes"
        )  # pragma: no cover

    def get_unpack(self):
        """Whether or not to automatically unpack the data.

        .. versionadded:: (cfdm) NEXTVERSION

        **Examples**

        >>> a.get_unpack()
        True

        """
        return self._get_component("unpack")

    def replace_filename(self, filename):
        """Replace the file location.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `file_directory`, `get_filename`,
                     `replace_directory`

        :Parameters:

            filename: `str`
                The new file location.

        :Returns:

            `{{class}}`
                A new `{{class}}` with modified file name.

        """
        a = self.copy()
        a._set_component("filename", filename, copy=False)
        return a
