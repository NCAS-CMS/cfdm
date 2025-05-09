from ctypes.util import find_library

from cfunits import Units as cfUnits

from .core.meta import DocstringRewriteMeta

_libpath = find_library("udunits2")
if _libpath is None:
    raise FileNotFoundError(
        "cfdm UNIDATA UDUNITS-2. Can't find the 'udunits2' library."
    )


class Units(metaclass=DocstringRewriteMeta):
    """Store, combine, compare, and convert physical units.

    This is a convenience class that creates a `cfunits.Units`
    instance.

    The full documentation is available via a `{{package}}.Units`
    instance, e.g. ``help({{package}}.Units())``.

    """

    def __new__(cls, *args, **kwargs):
        """Return a new Units instance."""
        return cfUnits(*args, **kwargs)

    @staticmethod
    def conform(*args, **kwargs):
        """Conform values to equivalent values in a compatible unit."""
        return cfUnits.conform(*args, **kwargs)
