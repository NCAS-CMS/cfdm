from ..zarrarray import ZarrArray
from .mixin import FragmentFileArrayMixin


class FragmentZarrArray(FragmentFileArrayMixin, ZarrArray):
    """A fragment of aggregated data in a file accessed with `zarr`.

    .. versionadded:: (cfdm) 1.13.0.0

    """
