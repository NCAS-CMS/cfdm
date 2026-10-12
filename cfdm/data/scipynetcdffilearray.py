from .abstract import FileArray
from .mixin import IndexMixin


class DeprecationError(Exception):
    """Deprecation error."""

    pass


class ScipyNetcdfFileArray(IndexMixin, FileArray):
    """A netCDF-3 array accessed with `scipy.io.netcdf_file`.

    Deprecated at version 1.13.3.0 and is no longer available. Use
    `{{package}}.XnetcdfArray` instead.

    .. versionadded:: (cfdm) 1.13.1.0

    """

    def __init__(self, *args, **kwargs):
        class DeprecationError(Exception):
            """Deprecation error."""

        raise DeprecationError(
            f"{self.__class__.__name__} was deprecated at version 1.13.3.0 "
            "and is no longer available. Use XnetcdfArray instead."
        )
