from ..xnetcdfarray import XnetcdfArray
from .mixin import FragmentFileArrayMixin


class FragmentXnetcdfArray(FragmentFileArrayMixin, XnetcdfArray):
    """Fragment of aggregated data in a file.

    .. versionadded:: (cfdm) 1.13.3.0

    """
