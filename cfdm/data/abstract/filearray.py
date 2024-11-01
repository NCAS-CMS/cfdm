from copy import deepcopy
from os.path import basename, join
from urllib.parse import urlparse

from s3fs import S3FileSystem

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
        substitutions=None,
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

            {{init substitutions: `dict`, optional}}

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

            try:
                substitutions = source._get_component("substitutions", None)
            except AttributeError:
                substitutions = None

        if shape is not None:
            self._set_component("shape", shape, copy=False)

        if filename is not None:
            if isinstance(filename, str):
                filename = (filename,)
            else:
                filename = tuple(filename)

            self._set_component("filename", filename, copy=False)

        if address is not None:
            if isinstance(address, (str, int)):
                address = (address,)
            else:
                address = tuple(address)

            self._set_component("address", address, copy=False)

        self._set_component("dtype", dtype, copy=False)
        self._set_component("mask", bool(mask), copy=False)
        self._set_component("unpack", bool(unpack), copy=False)
        self._set_component("attributes", attributes, copy=False)
        self._set_component("storage_options", storage_options, copy=False)

        if substitutions is not None:
            self._set_component(
                "substitutions", substitutions.copy(), copy=False
            )

        # By default, close the netCDF file after data array access
        self._set_component("close", True, copy=False)

    def __dask_tokenize__(self):
        """Return a value fully representative of the object.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return (
            self.__class__,
            self.shape,
            self.get_filenames(),
            self.get_addresses(),
            self.get_mask(),
            self.get_unpack(),
        )

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
        directory = dirname(directory, isdir=True)

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
        # TODO n_files += 1
        return a

    def clear_substitutions(self):
        """Remove all netCDF aggregation substitution definitions.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `del_substitution`,
                     `substitutions`,
                     `update_aggregation_substitutions`

        :Returns:

            `{{class}}`
                A new `{{class}}` with all substireference to files in
                *directory* removed.


            `dict`
                The removed CF-netCDF file location substitutions in a
                dictionary whose key/value pairs comprise a file
                location part to be substituted and its corresponding
                replacement text.

        .. versionadded:: (cfdm) NEXTVERSION

         TODOCFA.

        """
        a = self.copy()
        substitutions = a.get_substitutions(copy=False)

        # Replace the deleted substitutions
        filenames2 = []
        for f in a.get_filenames(normalise=False):
            for substitution, replacement in substitutions.items():
                f = f.replace(substitution, replacement)

            filenames2.append(f)

        a._set_component("filename", tuple(filenames2), copy=False)

        substitutions.clear()
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
                A new `{{class}}` with reference to files in
                *directory* removed.

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
        #        directory = abspath(directory).rstrip(sep)
        directory = dirname(directory, isdir=True)

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
        # TODO n_files = len(new_filenames)
        return a

    def del_substitution(self, substitution):
        """Remove a netCDF aggregation substitution definition.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `clear_substitutions`, `substitutions`,
                     `update_substitutions`

        :Parameters:

            substitution: `str`
                The CF-netCDF file location substitution definition to
                be removed. May be specified with or without the
                ``${...}`` syntax. For instance, the following are
                equivalent: ``'substitution'`` and
                ``'${substitution}'``.

        :Returns:

            `{{class}}`
                TODOCFA
                The removed CF-netCDF aggregation file location
                substitution in a dictionary whose key/value pairs are
                the location name part to be substituted and its
                corresponding replacement text. If the given
                substitution was not defined then an empty dictionary
                is returned.
                {{Returns nc_del_aggregation_substitution}}

        **Examples**
        TODOCFA.

        """
        a = self.copy()
        substitutions = a.get_substitutions(copy=False)
        replacement = substitutions.pop(substitution, None)
        if replacement is not None:
            # Replace the deleted substitution
            filenames2 = [
                f.replace(substitution, replacement)
                for f in a.get_filenames(normalise=False)
            ]
            a._set_component("filename", tuple(filenames2), copy=False)

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

    def get_filenames(self, normalise=True):
        """Return the names of files containing the data.

        If multiple files are returned then it is assumed that any
        one of them may contain the data, and when the data are
        requested an attempt to open file is made, in order, and the
        data is read from the first success.

        .. versionadded:: (cfdm) 1.10.0.2

        .. seealso:: `get_addresses`

        :Parameters:

            {{normalise: `bool`, optional}}

                .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `tuple`
                The filenames, in absolute form.

        """
        filenames = self._get_component("filename", ())
        if not normalise:
            return filenames

        normalised_filenames = []
        substitutions = self.get_substitutions(copy=False)
        for filename in filenames:
            # Apply substitutions to the file name
            for base, sub in substitutions.items():
                filename = filename.replace(base, sub)

            normalised_filenames.append(abspath(filename))

        return tuple(normalised_filenames)

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

    def get_substitutions(self, copy=True):
        """TODOCFA.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        substitutions = self._get_component("substitutions", None)
        if substitutions is None:
            substitutions = {}
            self._set_component("substitutions", substitutions, copy=False)
        elif copy:
            substitutions = substitutions.copy()

        return substitutions

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
        """Replace a file directories in-place.

        Every file in *old_directory* that is referenced by the data
        is redefined to be in *new_directory*.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `del_file_directory`, `file_directories`

        :Parameters:

            old_directory: `str`
                The directory to be replaced.

            new_directory: `str`
                The new directory.

        :Returns:

            `{{class}}`
                A new {{class}} with all previous files additionally
                referenced from *directory*.

        **Examples**

        >>> a.get_filenames()
        {'/data/file1.nc', '/home/file2.nc'}
        >>> b = a.replace_file_directory('/data', '/new/data/path/')
        >>> b.get_filenames()
        {'/new/data/path/file1.nc', '/home/file2.nc'}
        >>> c = b.replace_file_directory('/data', '/archive/location')
        >>> c.get_filenames()
        {'/archive/location/path/file1.nc', '/home/file2.nc'}

        """
        old_directory = dirname(old_directory, isdir=True)
        new_directory = dirname(new_directory, isdir=True)

        filenames = self.get_filenames()
        addresses = self.get_addresses()

        # Note: It is assumed that each existing file name is either
        #       an absolute path or an absolute URI.
        new_filenames = []
        new_addresses = []
        for filename, address in zip(filenames, addresses):
            if dirname(filename).startswith(old_directory):
                new_filename = filename.replace(old_directory, new_directory)
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

    def update_substitutions(self, substitutions):
        """TODOCFA.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        a = self.copy()
        old = a.get_substitutions(copy=False)
        old.update(substitutions)
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

            `NumpyArray`
                The new array with all of its data in memory.

        """
        from ..numpyarray import NumpyArray

        return NumpyArray(self.array)

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

    def replace_filenames(self, filenames):
        filenames = np.asanyarray(filenames)
        max_n_files = filenames.size

        addresses = self.get_addresses()
        old_n_files = len(addresses)
        
        filenames = tuple(filenames.compressed())
        new_n_files = len(filenames)
        
        self._set_component("filename", filenames, copy=False)
        addresses = self.get_addresses()
        if new_n_files < old_n_files:
            addresses = addresses[:nfiles]
        elif new_n_files > old_n_files:           
            addresses += (addresses[0],) * (new_n_files - old_n_files)

        self._set_component("address", addresses, copy=False)

        
