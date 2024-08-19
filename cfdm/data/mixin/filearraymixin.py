from copy import deepcopy
from os import sep
from os.path import basename, dirname, join
from urllib.parse import urlparse

from s3fs import S3FileSystem

from ...functions import abspath


class DeprecationError(Exception):
    """Deprecation error."""

    pass


class FileArrayMixin:
    """Mixin class for a file container of an array.

    .. versionadded:: (cfdm) 1.10.1.0

    """

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        """
        return f"<{self.__class__.__name__}{self.shape}: {self}>"

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        """
        filenames = self.get_filenames()
        addresses = self.get_addresses()
        if len(filenames) == 1:
            filenames = filenames[0]
            addresses = addresses[0]

        return f"{filenames}, {addresses}"

    def __dask_tokenize__(self):
        """Return a value fully representative of the object.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return (
            self.__class__,
            self.shape,
            self.get_filenames(),
            self.get_addresses(),
        )

    @property
    def dtype(self):
        """Data-type of the array."""
        return self._get_component("dtype")

    @property
    def shape(self):
        """Shape of the array."""
        return self._get_component("shape")

    def add_file_directory(self, directory):
        """Add a new file directory, not in-place.

        All existing files are additionally referenced from the given
        directory.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `del_file_directory`, `file_directories`

        :Parameters:

            directory: `str`
                The new directory.

        :Returns:

            `{{class}}`
                A new {{class}} with all previous files additionally
                referenced from *directory*.

        **Examples**

        >>> a.get_filenames()
        ('/data1/file1',)
        >>> a.get_addresses()
        ('tas',)
        >>> b = a.add_file_directory('/home')
        >>> b.get_filenames()
        ('/data1/file1', '/home/file1')
        >>> b.get_addresses()
        ('tas', 'tas')

        >>> a.get_filenames()
        ('/data1/file1', '/data2/file2',)
        >>> a.get_addresses()
        ('tas', 'tas')
        >>> b = a.add_file_directory('/home/')
        >>> b = get_filenames()
        ('/data1/file1', '/data2/file2', '/home/file1', '/home/file2')
        >>> b.get_addresses()
        ('tas', 'tas', 'tas', 'tas')

        >>> a.get_filenames()
        ('/data1/file1', '/data2/file1',)
        >>> a.get_addresses()
        ('tas1', 'tas2')
        >>> b = a.add_file_directory('/home/')
        >>> b.get_filenames()
        ('/data1/file1', '/data2/file1', '/home/file1')
        >>> b.get_addresses()
        ('tas1', 'tas2', 'tas1')

        >>> a.get_filenames()
        ('/data1/file1', '/data2/file1',)
        >>> a.get_addresses()
        ('tas1', 'tas2')
        >>> b = a.add_file_directory('/data1')
        >>> b.get_filenames()
        ('/data1/file1', '/data2/file1')
        >>> b.get_addresses()
        ('tas1', 'tas2')

        """
        directory = abspath(directory).rstrip(sep)

        filenames = self.get_filenames()
        addresses = self.get_addresses()

        # Note: It is assumed that each existing file name is either
        #       an absolute path or an absolute URI.
        new_filenames = list(filenames)
        new_addresses = list(addresses)
        for filename, address in zip(filenames, addresses):
            new_filename = join(directory, basename(filename))
            if new_filename not in new_filenames:
                new_filenames.append(new_filename)
                new_addresses.append(address)

        a = self.copy()
        a._set_component("filename", tuple(new_filenames), copy=False)
        a._set_component(
            "address",
            tuple(new_addresses),
            copy=False,
        )
        return a

    def close(self, dataset):
        """Close the dataset containing the data."""
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.close"
        )  # pragma: no cover

    def del_file_directory(self, directory):
        """Remove a file directory, not in-place.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `add_file_directory`, `file_directories`

        :Parameters:

            directory: `str`
                 The file directory to remove.

        :Returns:

            `{{class}}`
                A new {{class}} with reference to files in *directory*
                removed.

        **Examples**

        >>> a.get_filenames()
        ('/data1/file1', '/data2/file2')
        >>> a.get_addresses()
        ('tas1', 'tas2')
        >>> b = a.del_file_directory('/data1')
        >>> b = get_filenames()
        ('/data2/file2',)
        >>> b.get_addresses()
        ('tas2',)

        >>> a.get_filenames()
        ('/data1/file1', '/data2/file1', '/data2/file2')
        >>> a.get_addresses()
        ('tas1', 'tas1', 'tas2')
        >>> b = a.del_file_directory('/data2')
        >>> b.get_filenames()
        ('/data1/file1',)
        >>> b.get_addresses()
        ('tas1',)

        """
        directory = abspath(directory).rstrip(sep)

        new_filenames = []
        new_addresses = []
        for filename, address in zip(
            self.get_filenames(), self.get_addresses()
        ):
            if dirname(filename) != directory:
                new_filenames.append(filename)
                new_addresses.append(address)

        if not new_filenames:
            raise ValueError(
                "Can't delete a file directory when it results in there "
                "being no files"
            )

        a = self.copy()
        a._set_component("filename", tuple(new_filenames), copy=False)
        a._set_component("address", tuple(new_addresses), copy=False)
        return a

    def file_directories(self):
        """The file directories.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `tuple`
                The file directory names, one for each file, as
                absolute paths with no trailing path name component
                separator.

        **Examples**

        >>> a.get_filenames()
        ('/data1/file1',)
        >>> a.file_directories()
        ('/data1,)

        >>> a.get_filenames()
        ('/data1/file1', '/data2/file2')
        >>> a.file_directories()
        ('/data1', '/data2')

        >>> a.get_filenames()
        ('/data1/file1', '/data2/file2', '/data1/file2')
        >>> a.file_directories()
        ('/data1', '/data2', '/data1')

        """
        return tuple(map(dirname, self.get_filenames()))

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
        addresses = self.get_addresses()
        n = len(addresses)
        if n == 1:
            return addresses[0]

        if default is None:
            return

        return self._default(
            default, f"{self.__class__.__name__} has no unique file address"
        )

    def get_addresses(self):
        """Return the names of the data addresses in the files.

        If there are multiple addresses then they correspond, in
        order, to the files returned by `get_filenames`

        .. versionadded:: (cfdm) 1.10.0.2

        .. seealso:: `get_filenames`

        :Returns:

            `tuple`
                The addresses.

        """
        return self._get_component("address", ())

    def get_filename(self, default=AttributeError()):
        """The name of the file containing the array.

        If there are multiple files then an `AttributeError` is
        raised by default.

        .. versionadded:: (cfdm) 1.10.0.2

        :Parameters:

            default: optional
                Return the value of the *default* parameter if there
                is no file or there is more than one file.

                {{default Exception}}

        :Returns:

            `str`
                The file name.

        """
        filenames = self._get_component("filename", ())
        if len(filenames) == 1:
            return filenames[0]

        if default is None:
            return

        return self._default(
            default, f"{self.__class__.__name__} has no files"
        )

    def get_filenames(self):
        """Return the names of files containing the data.

        If multiple files are returned then it is assumed that any
        one of them may contain the data, and when the data are
        requested an attempt to open file is made, in order, and the
        data is read from the first success.

        .. versionadded:: (cfdm) 1.10.0.2

        .. seealso:: `get_addresses`

        :Returns:

            `tuple`
                The filenames, in absolute form.

        """
        return tuple([abspath(f) for f in self._get_component("filename", ())])

    def get_format(self):
        """The format of the files.

        .. versionadded:: (cfdm) 1.10.1.0

        .. seealso:: `get_address`, `get_filename`, `get_formats`

        :Returns:

            `str`
                 The file format.

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.get_format"
        )  # pragma: no cover

    def get_formats(self):
        """Return the format of the files.

        .. versionadded:: (cfdm) 1.10.1.0

        .. seealso:: `get_format`, `get_filenames`, `get_addresses`

        :Returns:

            `tuple`
                The fragment file formats.

        """
        return (self.get_format(),) * len(self.get_filenames())

    def get_missing_values(self):
        """The missing values of the data.

        Deprecated at version NEXTVERSION. Use `get_attributes` instead.

        """
        raise DeprecationError(
            f"{self.__class__.__name__}.get_missing_values was deprecated "
            "at version NEXTVERSION and is no longer available. "
            f"Use {self.__class__.__name__}.get_attributes instead."
        )  # pragma: no cover

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
                        filename = self.get_filename()
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
        # Loop round the files, returning as soon as we find one that
        # works.
        filenames = self.get_filenames()
        for filename, address in zip(filenames, self.get_addresses()):
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
                continue
            except RuntimeError as error:
                raise RuntimeError(f"{error}: {filename}")

            # Successfully opened a dataset, so return.
            return dataset, address

        if len(filenames) == 1:
            raise FileNotFoundError(f"No such file: {filenames[0]}")

        raise FileNotFoundError(f"No such files: {filenames}")

    def replace_file_directory(self, old_directory, new_directory):
        """Add a new file directory, not in-place. TODOCFA.

        All existing files are additionally referenced from the given
        directory.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `del_file_directory`, `file_directories`

        :Parameters:

            directory: `str`
                The new directory.

        :Returns:

            `{{class}}`
                A new {{class}} with all previous files additionally
                referenced from *directory*.

        **Examples**

        >>> a.get_filenames()
        ('/data1/file1',)
        >>> a.get_addresses()
        ('tas',)
        >>> b = a.add_file_directory('/home')
        >>> b.get_filenames()
        ('/data1/file1', '/home/file1')
        >>> b.get_addresses()
        ('tas', 'tas')

        >>> a.get_filenames()
        ('/data1/file1', '/data2/file2',)
        >>> a.get_addresses()
        ('tas', 'tas')
        >>> b = a.add_file_directory('/home/')
        >>> b = get_filenames()
        ('/data1/file1', '/data2/file2', '/home/file1', '/home/file2')
        >>> b.get_addresses()
        ('tas', 'tas', 'tas', 'tas')

        >>> a.get_filenames()
        ('/data1/file1', '/data2/file1',)
        >>> a.get_addresses()
        ('tas1', 'tas2')
        >>> b = a.add_file_directory('/home/')
        >>> b.get_filenames()
        ('/data1/file1', '/data2/file1', '/home/file1')
        >>> b.get_addresses()
        ('tas1', 'tas2', 'tas1')

        >>> a.get_filenames()
        ('/data1/file1', '/data2/file1',)
        >>> a.get_addresses()
        ('tas1', 'tas2')
        >>> b = a.add_file_directory('/data1')
        >>> b.get_filenames()
        ('/data1/file1', '/data2/file1')
        >>> b.get_addresses()
        ('tas1', 'tas2')

        """
        old_directory = abspath(old_directory).rstrip(sep)
        new_directory = abspath(new_directory).rstrip(sep)

        filenames = self.get_filenames()
        addresses = self.get_addresses()

        # Note: It is assumed that each existing file name is either
        #       an absolute path or an absolute URI.
        new_filenames = []
        new_addresses = []
        for filename, address in zip(filenames, addresses):
            if dirname(filename) == old_directory:
                new_filename = join(new_directory, basename(filename))
                if new_filename not in new_filenames:
                    new_filenames.append(new_filename)
                    new_addresses.append(address)
            else:
                new_filenames.append(filename)
                new_addresses.append(address)

        a = self.copy()
        a._set_component("filename", tuple(new_filenames), copy=False)
        a._set_component(
            "address",
            tuple(new_addresses),
            copy=False,
        )
        return a
