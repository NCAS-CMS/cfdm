from ..h5netcdfarray import H5netcdfArray
from .mixin import FragmentFileArrayMixin


class FragmentH5netcdfArray(FragmentFileArrayMixin, H5netcdfArray):
    """A fragment of aggregated data in a file accessed with `h5netcdf`.

    Deprecated at version 1.13.3.0 and is no longer available. Use
    `{{package}}.FragmentXnetcdfArray` instead.

    .. versionadded:: (cfdm) 1.12.0.0

    """

    def __init__(self, *args, **kwargs):
        class DeprecationError(Exception):
            """Deprecation error."""

        raise DeprecationError(
            f"{self.__class__.__name__} was deprecated at version 1.13.3.0 "
            "and is no longer available. Use FragmentXnetcdfArray instead."
        )
