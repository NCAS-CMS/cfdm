from ..netcdf4array import NetCDF4Array
from .mixin import FragmentFileArrayMixin


class FragmentNetCDF4Array(FragmentFileArrayMixin, NetCDF4Array):
    """A fragment of aggregated data in a file accessed with `netCDF4`.

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
