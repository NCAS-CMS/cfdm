import abc


class IO(metaclass=abc.ABCMeta):
    """Abstract base class for reading and writing Fields."""

    def __init__(self, implementation):
        """**Initialisation**

        :Parameters:

            implementation: `Implementation'
                The objects required to represent a Field.

        """
        self.implementation = implementation

    @abc.abstractmethod
    def dataset_close(self, *args, **kwargs):
        """Close the dataset."""
        raise NotImplementedError()  # pragma: no cover

    @abc.abstractmethod
    def dataset_open(self, *args, **kwargs):
        """Open the dataset."""
        raise NotImplementedError()  # pragma: no cover


class IORead(IO, metaclass=abc.ABCMeta):
    """Abstract base class for instantiating Fields from a dataset."""

    @classmethod
    def create_filesystem(cls, path, storage_options=None):
        """Create a file system for a path.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            path: `str`
                The path of the directory or file to be opened.

                The protocol of the created file system is taken as the
                URI schema of the *path*.

            storage_options: `None` or dict`, optional
                `fsspec.filesystem` keyword arguments to be used
                during file system creation.

                For a local path (e.g. ``'/homa/data/x.nc'``), `None`
                will prevent a file system from being created.

                For a remote path (e.g. ``'http://home/data/x.nc'``),
                `None` is equivalent to an empty `dict`.

                For a remote S3 path
                (e.g. ``'s3://authority/data/x.nc'``), the
                "endpoint_url" key is automatically added to the
                storage options.

        :Returns:

            (path, file system) or (path, `None`)
                The path of the directory or file, and its file
                system.

                The file system will be `None` if one wasn't created
                (see *storage_options*).

                For an input remote S3 path, the schema and authority
                are removed from the output path (e.g. for a *path* of
                ``'s3://authority/data/x.nc'``, ``'data/x.nc'`` is
                returned).

        """
        from uritools import urisplit

        u = urisplit(path)
        scheme = u.scheme

        if scheme in (None, "file"):
            # --------------------------------------------------------
            # Path is, e.g. ' file://...' or '/data/...'
            # --------------------------------------------------------
            if storage_options is None:
                filesystem = None
            else:
                import fsspec

                filesystem = fsspec.filesystem(
                    protocol="local", **storage_options
                )

        elif scheme == "s3":
            # --------------------------------------------------------
            # Path is 's3://...'
            # --------------------------------------------------------
            import fsspec

            if storage_options is None:
                storage_options = {}

            client_kwargs = storage_options.get("client_kwargs", {})
            if (
                "endpoint_url" not in storage_options
                and "endpoint_url" not in client_kwargs
            ):
                authority = u.authority
                if not authority:
                    authority = ""

                storage_options = storage_options.copy()
                storage_options["endpoint_url"] = f"https://{authority}"

            filesystem = fsspec.filesystem(protocol=scheme, **storage_options)

            path = u.path[1:]

        else:
            # --------------------------------------------------------
            # Path is, e.g. 'http://...', 'myschema://...'
            # --------------------------------------------------------
            import fsspec

            if storage_options is None:
                storage_options = {}

            filesystem = fsspec.filesystem(protocol=scheme, **storage_options)

        return path, filesystem

    @classmethod
    def filesystem_open(cls, filesystem, dataset, open_options=None):
        """Open a dataset on a file system.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            filesystem: file system
                A pre-authenticated file system, such as
                `fsspec.filesystem`.

            dataset: `str`
                The file system path to be opened.

            open_options: `dict` or `None`, optional
                The *filesystem* `open` method keyword
                arguments. `None` is equivalent to an empty `dict`.
                If the "mode" key is not set, then it defaults to
                ``'rb'``.

        :Returns:

            file-like object
                The open file handle for the dataset.

        """
        if open_options is None:
            open_options = {"mode": "rb"}

        if "mode" not in open_options:
            open_options = open_options.copy()
            open_options["mode"] = "rb"

        try:
            fh = filesystem.open(dataset, **open_options)
        except AttributeError:
            raise AttributeError(
                f"The file system object {filesystem!r} does not have "
                "an 'open' method. Please provide a valid file system "
                "object (e.g. an fsspec.filesystem instance)."
            )
        except Exception as error:
            raise RuntimeError(
                f"Failed to open {dataset!r} using the file system object "
                f" object {filesystem!r}: {error}"
            ) from error

        return fh

    @abc.abstractmethod
    def read(self, *args, **kwargs):
        """Read fields from a netCDF dataset."""
        raise NotImplementedError()  # pragma: no cover


class IOWrite(IO, metaclass=abc.ABCMeta):
    """Abstract base class for writing Fields to a dataset."""

    @abc.abstractmethod
    def write(self, *args, **kwargs):
        """Write fields to a netCDF dataset."""
        raise NotImplementedError()  # pragma: no cover
