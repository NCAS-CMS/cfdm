from ..pyfivearray import PyfiveArray
from .mixin import FragmentFileArrayMixin


class FragmentPyfiveArray(FragmentFileArrayMixin, PyfiveArray):
    """A fragment of aggregated data in a file accessed with `pyfive`.

    .. versionadded:: (cfdm) NEXTVERSION

    """
