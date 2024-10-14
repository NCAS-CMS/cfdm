from pathlib import Path
from urllib.parse import ParseResult, urlparse

from ..abstract import Array
from ..mixin import FileArrayMixin, IndexMixin
from .mixin import FragmentArrayMixin


class FragmentFileArray(
    FragmentArrayMixin,
    IndexMixin,
    FileArrayMixin,
    Array,
):
    """Fragment of aggregated data in a file.

    Access will be with either `netCDF4` or `h5netcdf`.

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
        aggregated_units=False,
        aggregated_calendar=False,
        attributes=None,
        storage_options=None,
            aggregation_file_directory=None,
            aggregation_file_scheme='file',
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            filename: (sequence of `str`), optional
                The locations fragment datasets containing the array.

            address: (sequence of `str`), optional
                How to find the fragments in the fragment datasets.

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
            source=source,
            copy=copy,
        )

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
                attributes = source._get_component("attributes", None)
            except AttributeError:
                attributes = None

            try:
                aggregated_units = source._get_component(
                    "aggregated_units", False
                )
            except AttributeError:
                aggregated_units = False

            try:
                aggregated_calendar = source._get_component(
                    "aggregated_calendar", False
                )
            except AttributeError:
                aggregated_calendar = False

            try:
                storage_options = source._get_component(
                    "storage_options", None
                )
            except AttributeError:
                storage_options = None

            try:
                substitutions = source._get_component("substitutions", None)
            except AttributeError:
                substitutions  = None

        if filename is not None:
            if isinstance(filename, str):
                filename = (filename,)
            else:
                filename = tuple(filename)

            self._set_component("filename", filename, copy=False)

        if address is not None:
            if isinstance(address, int):
                address = (address,)
            else:
                address = tuple(address)

            self._set_component("address", address, copy=False)

        if storage_options is not None:
            self._set_component("storage_options", storage_options, copy=False)

        self._set_component("shape", shape, copy=False)
        self._set_component("dtype", dtype, copy=False)
        self._set_component("attributes", attributes, copy=False)
        self._set_component("mask", True, copy=False)

        self._set_component("aggregated_units", aggregated_units, copy=False)
        self._set_component(
            "aggregated_calendar", aggregated_calendar, copy=False
        )
        if substitutions is not None:
            self._set_component(
                "substitutions", substitutions.copy(), copy=True
            )
            
        # By default, close the file after data array access
        self._set_component("close", True, copy=False)

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
            "aggregated_units": self.get_aggregated_units(None),
            "aggregated_calendar": self.get_aggregated_calendar(None),
            "attributes": self.get_attributes(None),
            "copy": False,
        }

        # Loop round the files, returning as soon as we find one that
        # is accessible.
        filenames = self.get_filenames()
        for filename, address in zip(filenames, self.get_addresses()):
            kwargs["filename"] = filename
            kwargs["address"] = address
            kwargs["storage_options"] = self.get_storage_options(
                create_endpoint_url=False
            )

            # Loop round the fragment array backends until we find one
            # that can open the file
            for FragmentArray in self._FragmentArrays:
                try:
                    return FragmentArray(**kwargs)._get_array(index)
                except Exception:
                    pass

        # Still here?
        raise OSError(f"Can't access any of the fragment files: {filenames}")
   
    def clear_substitutions(self):
        """TODOCFA

        .. versionadded:: (cfdm) NEXTVERSION
        """
        a = self.copy()
        substitutions = a.get_substitutions(copy=False)
        substitutions.clear()
        return a
    
    def del_substitution(self, base):
        """TODOCFA

        .. versionadded:: (cfdm) NEXTVERSION
        """
        a = self.copy()
        substitutions = a.get_substitutions(copy=False)
        substitutions.pop(base, None)
        return a
    
    def get_filenames(self):
        """TODOCFA

        .. versionadded:: (cfdm) NEXTVERSION
        """
        substitutions = self.get_substitutions(copy=False)
        
        parsed_filenames = []
        for filename in super().get_filenames():
            # Apply substitutions to the file name
            for base, sub in substitutions.items():
                filename = filename.replace(base, sub)
                
            if not urlparse(filename).scheme:
                # File name is a relative-path URI reference, so
                # replace it with an absolute URI.
                filename = Path(
                    self._get_component('aggregation_file_directory'),
                    filename
                ).resolve()
                filename = ParseResult(
                    scheme= self._get_component('aggregation_file_scheme'),
                    netloc="",
                    path=str(filename),
                    params="",
                    query="",
                    fragment="",
                ).geturl()
                
            parsed_filenames.append(filename)

        return parsed_filenames
                 
    def get_substitutions(self, copy=True):
        """TODOCFA

        .. versionadded:: (cfdm) NEXTVERSION
        """
        substitutions = self._get_component("substitutions", None)
        if substitutions is None:
            substitutions = {}
            self._set_component("substitutions", substitutions, copy=False)
        elif copy:
            substitutions = substitutions.copy()

        return substitutions
        
    def update_substitutions(self, substitutions):
        """TODOCFA

        .. versionadded:: (cfdm) NEXTVERSION
        """
        a = self.copy()
        old = a.get_substitutions(copy=False)
        old.update(substitutions)
        return a
