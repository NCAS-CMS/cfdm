from ..netcdf4array import NetCDF4Array
from .mixin import FragmentFileArrayMixin


class FragmentNetCDF4Array(FragmentFileArrayMixin, NetCDF4Array):
    """A fragment of aggregated data in a file accessed with `netCDF4`.

    .. versionadded:: (cfdm) 1.12.0.0

    """
