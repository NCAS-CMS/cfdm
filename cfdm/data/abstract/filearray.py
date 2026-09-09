from os import sep
from os.path import join

from cfdm.functions import _DEPRECATION_ERROR_METHOD, abspath, dirname

from . import Array


class FileArray(Array):
    """Abstract base class for an array in a file.

    .. versionadded:: (cfdm) 1.12.0.0

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
        filesystem=None,
        backend=None,
        backend_options=None,
        variable=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            filename: (sequence of `str`), optional
                The location of the dataset containing the array.

            address: (sequence of `str`), optional
                How to find the array in the dataset.

            dtype: `numpy.dtype`, optional
                The data type of the array. May be `None` if is not
                known. This may differ from the data type of the
                array in the dataset.

            shape: `tuple`, optional
                The shape of the dataset array.

            {{init mask: `bool`, optional}}

            {{init unpack: `bool`, optional}}

            {{init attributes: `dict` or `None`, optional}}

                If *attributes* is `None`, the default, then the
                attributes will be set from those in the dataset
                during the first `__getitem__` call.

            {{init filesystem: optional}}

                .. versionadded:: (cfdm) 1.13.1.0

            {{init backend: `None` or (sequence of) `str`, optional}}

                .. versionadded:: (cfdm) 1.13.3.0

            {{init backend_options: `None` or `dict`, optional}}

                .. versionadded:: (cfdm) 1.13.1.0

            variable: optional
                An open dataset variable object. Setting *variable*
                does not replace the need for the *filename* and
                *address* parameters, instead it complements them by
                allowing faster data access.

                .. versionadded:: (cfdm) 1.13.1.0

            {{init source: optional}}

            {{init copy: `bool`, optional}}

            storage_options: Deprecated at version (cfdm) 1.13.3.0
                Use *filesystem* instead.

            storage_protocol: Deprecated at version (cfdm) 1.13.3.0
                Use *filesystem* instead.

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
                filesystem = source._get_component("filesystem", None)
            except AttributeError:
                filesystem = None

            try:
                backend = source._get_component("backend", None)
            except AttributeError:
                backend = None

            try:
                backend_options = source._get_component(
                    "backend_options", None
                )
            except AttributeError:
                backend_options = None

            try:
                variable = source._get_component("variable", None)
            except AttributeError:
                variable = None

        if shape is not None:
            self._set_component("shape", shape, copy=False)

        if filename is not None:
            self._set_component("filename", filename, copy=False)

        if address is not None:
            self._set_component("address", address, copy=False)

        self._set_component("dtype", dtype, copy=False)
        self._set_component("mask", bool(mask), copy=False)
        self._set_component("unpack", bool(unpack), copy=False)

        if attributes is not None:
            self._set_component("attributes", attributes, copy=copy)

        if variable is not None:
            self._set_component("variable", variable, copy=False)

        if filesystem is not None:
            self._set_component("filesystem", filesystem, copy=False)

        if backend is not None:
            self._set_component("backend", backend, copy=False)

        if backend_options is not None:
            self._set_component("backend_options", backend_options, copy=False)

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

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        """
        return f"<{self.__class__.__name__}{self.shape}: {self}>"

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        """
        return f"{self.get_filename()}, {self.get_address()}"

    def __dask_tokenize__(self):
        """Return a value fully representative of the object.

        .. versionadded:: (cfdm) 1.12.0.0

        """
        return (
            self.__class__,
            self.shape,
            self.get_filename(normalise=True, default=None),
            self.get_address(),
            self.get_mask(),
            self.get_unpack(),
            self.get_attributes(copy=False),
            self.get_filesystem(),
            self.get_backend(),
            self.get_backend_options(),
        )

    def _get_array(self, index=None):
        """Returns a subspace of the dataset variable.

        The subspace is defined by the `index` attributes, and is
        applied with `cfdm.netcdf_indexer`.

        .. versionadded:: (cfdm) 1.12.0.0

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

        >>> n = {{package}}.{{class}}.array(a)
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
                Return *default* if the address has not been set.

                {{default Exception}}

        :Returns:

            `str`
                The file name.

        """
        return self._get_component("address", default)

    def get_backend(self):
        """The names of the packages for accessing the dataset.

        .. versionadded:: (cfdm) 1.13.3.0

        :Returns:

            `None` or (sequence of) `str`
                The backend name or names, or `None` if none have been
                provided, in which case the default backends for
                `xnetcdf` are assumed. When accessing the dataset, the
                backends are tried in order until one successfully
                reads the dataset.

        """
        return self._get_component("backend", None)

    def get_backend_options(self):
        """Backend options when opening a dataset.

        .. versionadded:: (cfdm) 1.13.3.0

        :Returns:

            `dict`
                The options to use with each backend when opening the
                dataset.

        """
        return self._get_component("backend_options", {})

    def file_directory(self, normalise=False, default=AttributeError()):
        """The file directory.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            {{normalise: `bool`, optional}}

            default: optional
                Return *default* if the file has not been set.

                {{default Exception}}

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

                .. versionadded:: (cfdm) 1.12.0.0

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

        if normalise and isinstance(filename, str):
            protocol = None
            filesystem = self.get_filesystem()
            if filesystem is not None:
                protocol = getattr(filesystem, "protocol", "")
                if isinstance(protocol, tuple):
                    protocol = protocol[0]

            # Only normalise a local name
            if protocol in (None, "file", "local"):
                filename = abspath(filename)

        return filename

    def get_mask(self):
        """Whether or not to automatically mask the data.

        .. versionadded:: (cfdm) 1.8.2

        **Examples**

        >>> b = a.get_mask()

        """
        return self._get_component("mask")

    def get_storage_protocol(self):
        """The file system protocol.

        .. versionadded:: (cfdm) 1.13.1.0

        .. seeaslo:: `has_remote_storage_protocol`, `get_storage_options`

        :Returns:

            `None` or `str`
                The file system protocol. If `None` the the file
                system is the local file system.

        **Examples**

        >>> a.get_storage_protocol()
        's3'
        >>> a.get_storage_protocol()
        'file'
        >>> print(a.get_storage_protocol())
        None

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "get_storage_protocol",
            version="1.13.3.0",
            removed_at="1.14.0.0",
        )  # pragma: no cover

    def get_filesystem(self):
        """Return the file system which contains the dataset.

        .. versionadded:: (cfdm) 1.13.3.0

        :Returns:

            filesystem or `None`
                The file system object. If the file system is the local
                file system, then `None` may be returned or a file
                system object.

        """
        return self._get_component("filesystem", None)

    def get_storage_options(self):
        """Return the file system options.

        .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `dict`
                The storage options.

        **Examples**

        >>> f.get_storage_options()
        {}

        >>> f.get_storage_options()
        {'key': 'scaleway-api-key...',
         'secret': 'scaleway-secretkey...',
         'endpoint_url': 'https://s3.fr-par.scw.cloud',
         'client_kwargs': {'region_name': 'fr-par'}}

        """
        fs = self.get_filesystem()
        if fs is None:
            return {}

        return fs.storage_options.copy()

    def get_variable(self, default=AttributeError()):
        """Get the open dataset variable object for the data.

        .. versionadded:: (cfdm) 1.13.1.0

        :Parameters:

            default: optional
                Return *default* if the variable has not been set.

                {{default Exception}}

        :Returns:

                The open dataset variable object.

        """
        return self._get_component("variable", default)

    def open(self, func, options=None, create_filesystem=True):
        """Return a dataset file object and address.

        .. versionadded:: (cfdm) 1.10.1.0

        :Parameters:

            func: callable
                Function that opens a file.

            options: `dict`, optional
                Arguments to *func*.

            create_filesystem: `bool`, optional
                If True (the default) then attempt to create a
                file system if one has not been provided. Note that a
                file system will not be created for a local dataset.

                If there is no file system then the dataset as
                returned by `get_filename` is passed directly to
                *func*.

                Ignored if `get_filename` does not return a string.

                .. versionadded:: (cfdm) 1.13.3.0

        :Returns:

            2-`tuple`
                The object representing the whole dataset, and the
                address of the data array within the dataset.

        """
        filename = self.get_filename(normalise=True)
        if isinstance(filename, str):
            filesystem = self.get_filesystem()
            if filesystem is None and create_filesystem:
                # No filesystem has been given, attempt to create one
                # from the dataset name. Note that a filesystem will
                # not be created for a local dataset.
                from cfdm.read_write import IORead

                filename, filesystem = IORead.create_filesystem(filename)

            if filesystem is None:
                # Local file system
                try:
                    filename = abspath(filename, uri=False)
                except ValueError:
                    filename = abspath(filename)
            else:
                # Create a file-like object for the dataset in the
                # filesystem
                from urllib.parse import urlparse

                # For an s3 file we need to strip off the scheme and
                # authority, if they're present.
                url = urlparse(filename)
                if url.scheme == "s3":
                    filename = url.path[1:]

                try:
                    filename = filesystem.open(filename, "rb")
                except AttributeError:
                    raise AttributeError(
                        f"Can't open {filename!r}. The file system object "
                        f"{filesystem!r} does not have an 'open' method. "
                        "Please provide a valid file system object, such "
                        "as a fsspec.filesystem instance."
                    )
                except Exception as error:
                    raise RuntimeError(
                        "Failed to open "
                        f"{self.get_filename(normalise=True)!r} using the "
                        f"file system object {filesystem!r}: {error}"
                    ) from error

        # Open the dataset
        if not options:
            options = {}

        dataset = func(filename, **options)

        return dataset, self.get_address()

    def replace_directory(self, old=None, new=None, normalise=False):
        """Replace the file directory.

        Modifies the name of the file.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `file_directory`, `get_filename`

        :Parameters:

            {{replace old: `str` or `None`, optional}}

            {{replace new: `str` or `None`, optional}}

            {{replace normalise: `bool`, optional}}

        :Returns:

            `{{class}}`
                A new `{{class}}` with modified file locations.

        **Examples**

        >>> a.get_filename()
        '/data/file1.nc'
        >>> b = a.replace_directory('/data', '/new/data/path/')
        >>> b.get_filename()
        '/new/data/path/file1.nc'
        >>> c = b.replace_directory('/new/data', None)
        >>> c.get_filename()
        'path/file1.nc'
        >>> c = b.replace_directory('path', '../new_path', normalise=False)
        >>> c.get_filename()
        '../new_path/file1.nc'
        >>> c = b.replace_directory(None, '/data')
        >>> c.get_filename()
        '/data/../new_path/file1.nc'
        >>> c = b.replace_directory('/new_path/', None, normalise=True)
        >>> c.get_filename()
        'file1.nc'

        """
        a = self.copy()

        filename = a.get_filename(normalise=normalise)
        if old or new:
            if normalise:
                from uritools import isuri, urisplit

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
                if filename.startswith(sep):
                    filename = filename[1:]

                filename = join(new, filename)

        a._set_component("filename", filename, copy=False)

        # Remove an obsolete variable
        a._del_component("variable", None)

        return a

    def get_missing_values(self):
        """The missing values of the data.

        Deprecated at version 1.12.0.0. Use `get_attributes` instead.

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "get_missing_values"
            f"Use {self.__class__.__name__}.get_attributes instead.",
            version="1.12.0.0",
            removed_at="1.14.0.0",
        )  # pragma: no cover

    def to_memory(self):
        """Bring data on disk into memory.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `numpy.ndarray`
                The new array.

        """
        return self.array

    def _attributes(self, var):
        """Get the variable attributes.

        If the attributes have not been set, then they are retrieved
        from the *var* and cached for fast future access.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `get_attributes`

        :Parameters:

            var: `p5netcdf.Variable`
                The variable.

        :Returns:

            `dict`
                The attributes. The returned attributes are not a copy
                of the cached dictionary.

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}._attributes"
        )  # pragma: no cover

    def get_unpack(self):
        """Whether or not to automatically unpack the data.

        .. versionadded:: (cfdm) 1.12.0.0

        **Examples**

        >>> a.get_unpack()
        True

        """
        return self._get_component("unpack")

    def has_remote_storage_protocol(self):
        """Whether or not there is a remote file system protocol.

        .. versionadded:: (cfdm)  1.13.1.0

        .. seeaslo:: `get_storage_protocol`, `get_storage_options`

        :Returns:

            `bool`
                `True` if there is a remote file system protocol,
                otherwise `False`.

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "has_remote_storage_protocol",
            version="1.13.3.0",
            removed_at="1.14.0.0",
        )  # pragma: no cover

    def replace_filename(self, filename):
        """Replace the file location.

        .. versionadded:: (cfdm) 1.12.0.0

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

        # Remove an obsolete variable
        a._del_component("variable", None)

        return a
