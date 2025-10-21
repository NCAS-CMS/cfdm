"""Functions intended to be passed to be dask.

These will typically be functions that operate on dask chunks. For
instance, as would be passed to `dask.array.map_blocks`.

"""

import numpy as np


def cfdm_to_memory(a):
    """Return an in-memory version of *a*.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        a: array_like
            The array.

    :Returns:

            If *a* has an `__in_memory__` attribute that is False then
            ``np.asanyarray(a)`` will be returned. Otherwise *a* will
            be returned unchanged.

    """
    if not getattr(a, "__in_memory__", True):
        return np.asanyarray(a)

    return a


def cfdm_filled(a, fill_value=None):
    """Replace masked elements with a fill value.

    .. versionadded:: (cfdm) 1.11.2.0

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
    a = cfdm_to_memory(a)
    return np.ma.filled(a, fill_value=fill_value)


def cfdm_harden_mask(a):
    """Harden the mask of a masked `numpy` array.

    Has no effect if the array is not a masked array.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        a: `numpy.ndarray`
            The array to give a hardened mask.

    :Returns:

        `numpy.ndarray`
            The array with hardened mask.

    """
    a = cfdm_to_memory(a)
    if np.ma.isMA(a):
        try:
            a.harden_mask()
        except AttributeError:
            # Trap cases when the input array is not a numpy array
            # (e.g. it might be numpy.ma.masked).
            pass

    return a


def cfdm_soften_mask(a):
    """Soften the mask of a masked `numpy` array.

    Has no effect if the array is not a masked array.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        a: `numpy.ndarray`
            The array to give a softened mask.

    :Returns:

        `numpy.ndarray`
            The array with softened mask.

    """
    a = cfdm_to_memory(a)
    if np.ma.isMA(a):
        try:
            a.soften_mask()
        except AttributeError:
            # Trap cases when the input array is not a numpy array
            # (e.g. it might be numpy.ma.masked).
            pass

    return a


def cfdm_where(array, condition, x, y, hardmask):
    """Set elements of *array* from *x* or *y* depending on *condition*.

    The input *array* is not changed in-place.

    **Missing data**

    Array elements may be set to missing values if either *x* or *y*
    are the `cfdm.masked` constant, or by assignment from any missing
    data elements in *x* or *y*.

    If the *array* mask is hard then missing data values in the array
    will not be overwritten, regardless of the content of *x* and *y*.

    If the *condition* contains missing data then the corresponding
    elements in the array will not be assigned to, regardless of the
    contents of *x* and *y*.

    .. note:: This function sets the mask hardness of the output
              array appropriately.

    .. versionadded:: (cfdm) 1.11.2.0

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
           Set the mask hardness for a returned masked `numpy` array.

           If False then a returned masked `numpy` array will have a
           soft mask.

           If True then mask of the input `numpy` *array* (if there is
           one) will be applied to the returned `numpy` array, in
           addition to any masked elements arising from assignments
           from *x* or *y*; and the if the returned `numpy` array is
           masked then it will have a hard mask.

    :Returns:

        `numpy.ndarray`
            A copy of the input *array* with elements from *y* where
            *condition* is False or masked, and elements from *x*
            elsewhere.

    """
    array = cfdm_to_memory(array)
    condition = cfdm_to_memory(condition)
    if x is not None:
        x = cfdm_to_memory(x)

    if y is not None:
        y = cfdm_to_memory(y)

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
