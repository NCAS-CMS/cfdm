from ..h5netcdfarray import H5netcdfArray
from .mixin import FragmentFileArrayMixin


class FragmentH5netcdfArray(FragmentFileArrayMixin, H5netcdfArray):
    """A fragment of aggregated data in a file accessed with `h5netcdf`.

    .. versionadded:: (cfdm) NEXTVERSION

    """
