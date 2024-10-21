from pathlib import Path
from urllib.parse import ParseResult  # , urlparse

from uritools import isrelpath, uricompose, urijoin

from ..abstract import FileArray
from ..mixin import IndexMixin
from .mixin import FragmentArrayMixin


class FragmentFileArray(
    FragmentArrayMixin,
    IndexMixin,
    #    FileArrayMixin,
    FileArray,
):
    """Fragment of aggregated data in a file.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def __new__(cls, *args, **kwargs):
        """Store fragment classes.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        # Import fragment classes. Do this here (as opposed to outside
        # the class) to aid subclassing.
        from . import FragmentH5netcdfArray, FragmentNetCDF4Array

        instance = super().__new__(cls)
        instance._FragmentArrays = (
            FragmentNetCDF4Array,
            FragmentH5netcdfArray,
        )
        return instance

    def __init__(
        self,
        filename=None,
        address=None,
        dtype=None,
        shape=None,
        substitutions=None,
        unpack_aggregated_data=True,
        aggregated_attributes=None,
        storage_options=None,
        aggregation_file_directory=None,
        aggregation_file_scheme="file",
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            filename: (sequence of `str`), optional
                The locations of fragment datasets containing the
                array.

            address: (sequence of `str`), optional
                How to find the array in the fragment datasets.

            dtype: `numpy.dtype`, optional
                The data type of the aggregated array. May be `None`
                if is not known. This may differ from the data type of
                the fragment's data.

            shape: `tuple`, optional
                The shape of the fragment in its canonical form.

            {{init substitutions: `dict`, optional}}

            {{init attributes: `dict` or `None`, optional}}

                If *attributes* is `None`, the default, then the
                attributes will be set from the fragment dataset
                during the first `__getitem__` call.

            {{aggregated_units: `str` or `None`, optional}}

            {{aggregated_calendar: `str` or `None`, optional}}

            {{init storage_options: `dict` or `None`, optional}}

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(
            filename=filename,
            address=address,
            dtype=dtype,
            shape=shape,
            mask=True,
            unpack=True,
            attributes=None,
            storage_options=storage_options,
            source=source,
            copy=copy,
        )

        if source is not None:
            try:
                aggregated_attributes = source._get_component(
                    "aggregated_attributes", None
                )
            except AttributeError:
                aggregated_attributes = None

            try:
                unpack_aggregated_data = source._get_component(
                    "unpack_aggregated_data", True
                )
            except AttributeError:
                unpack_aggregated_data = True

            try:
                aggregation_file_directory = source._get_component(
                    "aggregation_file_directory", None
                )
            except AttributeError:
                aggregation_file_directory = None

            try:
                aggregation_file_scheme = source._get_component(
                    "aggregation_file_scheme", None
                )
            except AttributeError:
                aggregation_file_scheme = None

        self._set_component(
            "aggregation_file_directory",
            aggregation_file_directory,
            copy=False,
        )
        self._set_component(
            "aggregation_file_scheme", aggregation_file_scheme, copy=False
        )
        self._set_component(
            "unpack_aggregated_data",
            unpack_aggregated_data,
            copy=False,
        )
        if aggregated_attributes is not None:
            self._set_component(
                "aggregated_attributes", aggregated_attributes, copy=copy
            )

    def _get_array(self, index=None):
        """Returns a subspace of the dataset variable.

        The method acts as a factory for either a
        `NetCDF4FragmentArray`, `H5netcdfFragmentArray`, or
        `UMFragmentArray` class, and it is the result of calling
        `!_get_array` on the newly created instance that is returned.

        `H5netcdfFragmentArray` will only be used if
        `NetCDF4FragmentArray` returns a `FileNotFoundError`
        exception; and `UMFragmentArray` will only be used
        if `H5netcdfFragmentArray` returns an `Exception`.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `__array__`, `index`

        :Parameters:

            {{index: `tuple` or `None`, optional}}

               When a `tuple`, there must be a distinct entry for each
               fragment dimension.

        :Returns:

            `numpy.ndarray`
                The subspace.

        """
        kwargs = {
            "dtype": self.dtype,
            "shape": self.shape,
            "aggregated_attributes": self.get_aggregated_attributes(),
            "copy": False,
        }

        # Loop round the files, returning as soon as we find one that
        # is accessible.
        errors = []
        filenames = self.get_filenames()
        for filename, address in zip(filenames, self.get_addresses()):
            kwargs["filename"] = filename
            kwargs["address"] = address
            kwargs["storage_options"] = self.get_storage_options(
                create_endpoint_url=False
            )

            # Loop round the fragment array backends, in the order
            # given by the `_FragmentArrays` attribute (which is
            # defined in `__new__`), until we find one that can open
            # the file.
            for FragmentArray in self._FragmentArrays:
                try:
                    array = FragmentArray(**kwargs)._get_array(index)
                except Exception as error:
                    errors.append(
                        f"{FragmentArray().__class__.__name__}: {error}"
                    )
                else:
                    return array

        # Still here?
        errors = "\n".join(errors)
        raise OSError(
            f"Can't access any of the fragment files {filenames} "
            "with the backends:\n"
            f"{errors}"
        )

    def get_filenames(self, normalise=True):
        """TODOCFA.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            {{normalise: `bool`, optional}}

                .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `set`
                The file names. If no files are required to compute
                the data then an empty `set` is returned.

        """
        filenames = self._get_component("filename", ())
        if not normalise:
            return filenames

        substitutions = self.get_substitutions(copy=False)

        parsed_filenames = []
        for filename in filenames:
            # Apply substitutions to the file name
            for base, sub in substitutions.items():
                filename = filename.replace(base, sub)

            # if not urlparse(filename).scheme:
            if isrelpath(filename):
                # File name is a relative-path URI reference, so
                # replace it with an absolute URI.
                filename = Path(
                    self._get_component("aggregation_file_directory"), filename
                ).resolve()
                # filename = ParseResult(
                #    scheme=self._get_component("aggregation_file_scheme"),
                #    netloc="",
                #    path=str(filename),
                #    params="",
                #    query="",
                #    fragment="",
                # ).geturl()
                filename = uricompose(
                    scheme=self._get_component("aggregation_file_scheme"),
                    authority="",
                    path=str(filename),
                )
            #                print (99999999999, filename)
            parsed_filenames.append(filename)

        return tuple(parsed_filenames)
