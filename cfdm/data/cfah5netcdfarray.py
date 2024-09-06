from .h5netcdfarray import H5netcdfArray
from .mixin import CFAMixin


class CFAH5netcdfArray(CFAMixin, H5netcdfArray):
    """A CF aggregation variable array accessed with `h5netcdf`.

    .. versionadded:: NEXTVERSION

    """
