from os.path import join

from uritools import uricompose, urisplit

from ...functions import abspath
from ..abstract import FileArray
from ..mixin import IndexMixin
from .mixin import FragmentArrayMixin


class FragmentFileArray(
    FragmentArrayMixin,
    IndexMixin,
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
        storage_options=None,
        substitutions=None,
        min_file_versions=None,
        unpack_aggregated_data=True,
        aggregated_attributes=None,
        aggregation_file_directory=None,
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
            substitutions=substitutions,
            min_file_versions=min_file_versions,
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

        self._set_component(
            "aggregation_file_directory",
            aggregation_file_directory,
            copy=False,
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
        if index is None:
            index = self.index()

        kwargs = {
            "dtype": self.dtype,
            "shape": self.shape,
            "aggregated_attributes": self.get_aggregated_attributes(),
            "copy": False,
        }

        # Loop round the files, returning as soon as we find one that
        # is accessible.
        errors = []
        filenames = self.get_filenames(normalise=True)
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
            f"Can't access any of the fragment files {filenames}:\n"
            f"{errors}"
        )

    def get_filenames(self, normalise=True):
        """TODOCFA.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            normalise: `bool`, optional
                If True (the default) then normalise the file names to
                absolute URIs. If False then the file names are
                returned in the same form that they have in the
                CF-netCDF aggregation file.

        :Returns:

            `set`
                The file names. If no files are required to compute
                the data then an empty `set` is returned.

        """
        filenames = super().get_filenames(normalise=False)
        if not normalise:
            return filenames

        normalised_filenames = []
        #        substitutions = self.get_substitutions(copy=False)
        for filename in filenames:
            # Apply substitutions to the file name
            # for base, sub in substitutions.items():
            #    filename = filename.replace(base, sub)

            uri = urisplit(filename)

            # Convert the file name to an absolute URI
            if uri.isrelpath():
                # File name is a relative-path URI reference
                filename = abspath(
                    join(
                        self._get_component("aggregation_file_directory"),
                        filename,
                    )
                )
            elif uri.isabspath():
                # File name is an absolute-path URI reference
                filename = uricompose(
                    scheme="file",
                    authority="",
                    path=filename,
                )
            elif not uri.isabsuri():
                raise ValueError(
                    "Fragment file location must be an absolute URI, a "
                    "relative-path URI reference, or an absolute-path URI: "
                    f"Got: {filename}"
                )

            normalised_filenames.append(filename)

        return tuple(normalised_filenames)
