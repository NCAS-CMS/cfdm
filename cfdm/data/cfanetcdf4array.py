from .mixin import CFAMixin
from .netcdf4array import NetCDF4Array


class CFANetCDF4Array(CFAMixin, NetCDF4Array):
    """A CF aggregation variable array accessed with `netCDF4`.

    .. versionadded:: NEXTVERSION

    """
