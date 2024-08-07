"""Functions intended to be passed to be dask.

These will typically be functions that operate on dask chunks. For
instance, as would be passed to `dask.array.map_blocks`.

"""

from functools import partial

import dask.array as da
import numpy as np
from dask.core import flatten
from scipy.ndimage import convolve1d

from ..cfdatetime import dt, dt2rt, rt2dt
from ..functions import atol as cf_atol
from ..functions import rtol as cf_rtol
from ..units import Units


def harden_mask(a):
    """Harden the mask of a masked `numpy` array.

    Has no effect if the array is not a masked array.

    .. versionadded:: 3.14.0

    .. seealso:: `cf.Data.harden_mask`

    :Parameters:

        a: `numpy.ndarray`
            The array to have a hardened mask.

    :Returns:

        `numpy.ndarray`
            The array with hardened mask.

    """
    # REVIEW: getitem: `harden_mask`: convert a to a usable array
    a = asanyarray(a)
    if np.ma.isMA(a):
        try:
            a.harden_mask()
        except AttributeError:
            # Trap cases when the input array is not a numpy array
            # (e.g. it might be numpy.ma.masked).
            pass

    return a


def soften_mask(a):
    """Soften the mask of a masked `numpy` array.

    Has no effect if the array is not a masked array.

    .. versionadded:: 3.14.0

    .. seealso:: `cf.Data.soften_mask`

    :Parameters:

        a: `numpy.ndarray`
            The array to have a softened mask.

    :Returns:

        `numpy.ndarray`
            The array with softened mask.

    """
    # REVIEW: getitem: `soften_mask`: convert a to a usable array
    a = asanyarray(a)

    if np.ma.isMA(a):
        try:
            a.soften_mask()
        except AttributeError:
            # Trap cases when the input array is not a numpy array
            # (e.g. it might be numpy.ma.masked).
            pass

    return a


def filled(a, fill_value=None):
    """Replace masked elements with a fill value.

    .. versionadded:: NEXTVERSION

    :Parameters:

        a: array_like
            The array.

        fill_value: scalar
            The fill value.

    :Returns:

        `numpy.ndarray`
            The filled array.

    **Examples**

    >>> a = np.array([[1, 2, 3]])
    >>> print(data.dask_utils.filled(a, -999))
    [[1 2 3]]
    >>> a = np.ma.array([[1, 2, 3]], mask=[[True, False, False]])
    >>> print(data.dask_utils.filled(a, -999))
    [[-999    2    3]]

    """
    # REVIEW: getitem: `filled`: convert a to a usable array
    a = asanyarray(a)
    return np.ma.filled(a, fill_value=fill_value)


# REVIEW: getitem: `cf_asanyarray`: convert a to a usable array
def asanyarray(a):
    """Convert to a `numpy` array.

    Only do this is the input *a* has an `__asanyarray__` attribute
    with value True.

    .. versionadded:: NEXTVERSION

    :Parameters:

        a: array_like
            The array.

    :Returns:

            The array converted to a `numpy` array, or the input array
            unchanged if ``a.__asanyarray__`` False.

    """
    # REVIEW: getitem: `cf_asanyarray`: convert a to a usable array
    if getattr(a, "__asanyarray__", False):
        return np.asanyarray(a)

    return a
