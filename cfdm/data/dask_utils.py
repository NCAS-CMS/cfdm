"""Functions intended to be passed to be dask.

These will typically be functions that operate on dask chunks. For
instance, as would be passed to `dask.array.map_blocks`.

"""

import numpy as np


def cfdm_asanyarray(a):
    """Convert to a `numpy` array.

    Only do this is the input *a* has an `__asanyarray__` attribute
    with value True.

    .. versionadded:: (cfdm) NEXTVERSION

    :Parameters:

        a: array_like
            The array.

    :Returns:

            The array converted to a `numpy` array, or the input array
            unchanged if ``a.__asanyarray__`` False.

    """
    # REVIEW: getitem: `cfdm_asanyarray`: convert a to a usable array
    if getattr(a, "__asanyarray__", False):
        return np.asanyarray(a)

    return a


def harden_mask(a):
    """Harden the mask of a masked `numpy` array.

    Has no effect if the array is not a masked array.

    .. versionadded:: (cfdm) NEXTVERSION

    .. seealso:: `cfdm.Data.harden_mask`

    :Parameters:

        a: `numpy.ndarray`
            The array to have a hardened mask.

    :Returns:

        `numpy.ndarray`
            The array with hardened mask.

    """
    # REVIEW: getitem: `harden_mask`: convert a to a usable array
    a = cfdm_asanyarray(a)
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

    .. versionadded:: (cfdm) NEXTVERSION

    .. seealso:: `cfdm.Data.soften_mask`

    :Parameters:

        a: `numpy.ndarray`
            The array to have a softened mask.

    :Returns:

        `numpy.ndarray`
            The array with softened mask.

    """
    # REVIEW: getitem: `soften_mask`: convert a to a usable array
    a = cfdm_asanyarray(a)

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

    .. versionadded:: (cfdm) NEXTVERSION

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
    a = cfdm_asanyarray(a)
    return np.ma.filled(a, fill_value=fill_value)


def cfdm_where(array, condition, x, y, hardmask):
    """Set elements of *array* from *x* or *y* depending on *condition*.

    The input *array* is not changed in-place.

    See `where` for details on the expected functionality.

    .. note:: This function correctly sets the mask hardness of the
              output array.

    .. versionadded:: (cfdm) NEXTVERSION

    :Parameters:

        array: numpy.ndarray
            The array to be assigned to.

        condition: numpy.ndarray
            Where False or masked, assign from *y*, otherwise assign
            from *x*.

        x: numpy.ndarray or `None`
            *x* and *y* must not both be `None`.

        y: numpy.ndarray or `None`
            *x* and *y* must not both be `None`.

        hardmask: `bool`
           Set the mask hardness for a returned masked array. If True
           then a returned masked array will have a hardened mask, and
           the mask of the input *array* (if there is one) will be
           applied to the returned array, in addition to any masked
           elements arising from assignments from *x* or *y*.

    :Returns:

        `numpy.ndarray`
            A copy of the input *array* with elements from *y* where
            *condition* is False or masked, and elements from *x*
            elsewhere.

    """
    array = cfdm_asanyarray(array)
    condition = cfdm_asanyarray(condition)
    if x is not None:
        x = cfdm_asanyarray(x)

    if y is not None:
        y = cfdm_asanyarray(y)

    mask = None

    if np.ma.isMA(array):
        # Do a masked where
        where = np.ma.where
        if hardmask:
            mask = array.mask
    elif np.ma.isMA(x) or np.ma.isMA(y):
        # Do a masked where
        where = np.ma.where
    else:
        # Do a non-masked where
        where = np.where
        hardmask = False

    condition_is_masked = np.ma.isMA(condition)
    if condition_is_masked:
        condition = condition.astype(bool)

    if x is not None:
        # Assign values from x
        if condition_is_masked:
            # Replace masked elements of condition with False, so that
            # masked locations are assigned from array
            c = condition.filled(False)
        else:
            c = condition

        array = where(c, x, array)

    if y is not None:
        # Assign values from y
        if condition_is_masked:
            # Replace masked elements of condition with True, so that
            # masked locations are assigned from array
            c = condition.filled(True)
        else:
            c = condition

        array = where(c, array, y)

    if hardmask:
        if mask is not None and mask.any():
            # Apply the mask from the input array to the result
            array.mask |= mask

        array.harden_mask()

    return array
