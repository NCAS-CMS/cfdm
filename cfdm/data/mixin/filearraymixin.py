from urllib.parse import urlparse

from ...functions import abspath


class FileArrayMixin:
    """Mixin class for a container of an array. TODOCFADOCS.

    .. versionadded:: (cfdm) TODOCFAVER

    """

    def __str__(self):
        """x.__str__() <==> str(x)"""
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

                .. versionadded:: (cfdm) 1.10.0.2

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
        """TODOCFADOCS Return the.

        .. versionadded:: TODOCFAVER

        :Returns:

            `tuple`
                TODOCFADOCS

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
                is no file.

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
        """TODOCFADOCS Return the names of files containing.

        .. versionadded:: TODOCFAVER

        :Returns:

            `tuple`
                TODOCFADOCS

        """
        return tuple([abspath(f) for f in self._get_component("filename", ())])

    def get_format(self):
        """The TODOCFADOCS in the file of the variable.

        .. versionadded:: (cfdm) TODOCFAVER

        :Returns:

            `str`
                The address, or `None` if there isn't one.

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.get_format"
        )  # pragma: no cover

    def get_formats(self):
        """Return the format of the files.

        .. versionadded:: TODOCFAVER

        .. seealso:: `get_format`, `get_filenames`, `get_addresses`

        :Returns:

            `tuple`
                The fragment file formats.

        """
        return (self.get_format(),) * len(self.get_filenames())

    def open(self, func, *args, **kwargs):
        """Returns an open dataset containing the data array.

        When multiple fragment files have been provided an attempt is
        made to open each one, in arbitrary order, and the
        `netCDF4.Dataset` is returned from the first success.

        .. versionadded:: TODOCFAVER

        :Returns:

            (`netCDF4.Dataset`, address)

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
