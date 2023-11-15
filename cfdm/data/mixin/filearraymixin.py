from urllib.parse import urlparse

from ...functions import abspath


class FileArrayMixin:
    """Mixin class for a file container of an array.

    .. versionadded:: (cfdm) 1.10.1.0

    """

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
        addresses = self.get_addresses()
        if len(addresses) == 1:
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

    def open(self, func, *args, **kwargs):
        """Return an open file object containing the data array.

        When multiple files have been provided an attempt is made to
        open each one, in the order stored, and an open file object is
        returned from the first file that exists.

        .. versionadded:: (cfdm) 1.10.1.0

        :Parameters:

            func: callable
                Function that opens a file.

            args, kwargs: optional
                Optional arguments to *func*.

        :Returns:

            `tuple`
                The open file object, and the address of the data
                within the file.

        """
        # Loop round the files, returning as soon as we find one that
        # works.
        filenames = self.get_filenames()
        for filename, address in zip(filenames, self.get_addresses()):
            url = urlparse(filename)
            if url.scheme == "file":
                # Convert a file URI into an absolute path
                filename = url.path

            try:
                nc = func(filename, *args, **kwargs)
            except FileNotFoundError:
                continue
            except RuntimeError as error:
                raise RuntimeError(f"{error}: {filename}")

            return nc, address

        if len(filenames) == 1:
            raise FileNotFoundError(f"No such netCDF file: {filenames[0]}")

        raise FileNotFoundError(f"No such netCDF files: {filenames}")
