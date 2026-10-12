from ..pyfivearray import PyfiveArray
from .mixin import FragmentFileArrayMixin


class FragmentPyfiveArray(FragmentFileArrayMixin, PyfiveArray):
    """A fragment of aggregated data in a file accessed with `pyfive`.

    .. versionadded:: (cfdm) 1.13.1.0

    """

    def __init__(self, *args, **kwargs):
        class DeprecationError(Exception):
            """Deprecation error."""

        raise DeprecationError(
            f"{self.__class__.__name__} was deprecated at version 1.13.3.0 "
            "and is no longer available. Use FragmentXnetcdfArray instead."
        )
