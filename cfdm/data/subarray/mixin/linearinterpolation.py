import numpy as np


_float64 = np.dtype(float)


class LinearInterpolation:
    """Mixin class for subsampled arrays that need linear interpolation.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def _linear_interpolation(self, ua, ub, d, s=None, returns=False):
        """Interpolate linearly between pairs of tie points.

        General purpose one-dimensional linear interpolation method.

        u = fl(ua, ub, s) = ua + s*(ub-ua)
                          = ua*(1-s) + ub*s

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_s`, `_trim`

        :Parameters:

            ua: `numpy.ndarray`
                The values of the first tie point in index space.

            ub: `numpy.ndarray`
                The values of the second tie point in index space.

            {{d: `int`}}

            {{s: array_like, optional}}

            returns: `bool`, optional
                TODO

        :Returns:

            `numpy.ndarray`

        """
        s, one_minus_s = self._s(d, s=s)

        u = ua * one_minus_s + ub * s

        if returns:
            return (u, s, one_minus_s)

        return u

    def _s(self, d, s=None, returns=True):
        """The interpolation coefficients for an interpolation subarea.

        Returns the interpolation coefficients ``s`` and ``1-s`` for
        the specified subsampled dimension of an interpolation subarea
        with the given shape. See CF appendix J.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            {{d: `int`}}

            {{s: array_like, optional}}

            returns: `bool`, optional
                TODO

        :Returns:

            `numpy.ndarray`, `numpy.ndarray`
                The interpolation coefficents ``s`` and ``1 - s``, in
                that order, each of which is a numpy array with values
                in the numerical range [0.0, 1.0]. The arrays will
                have extra size 1 dimensions corresponding to all tie
                point array dimensions other than *d*.

        **Examples**

        >>> x.shape
        (12, 5)
        >>> x.first
        (False, True)
        >>> x.bounds
        False
        >>> x._s(1)
        array([[0.  , 0.25, 0.5 , 0.75, 1.  ]])
        array([[1.  , 0.75, 0.5 , 0.25, 0.  ]])

        >>> x.shape
        (12, 5)
        >>> x.first
        (False, False)
        >>> x.bounds
        False
        >>> x._s(1)
        array([[0. , 0.2, 0.4, 0.6, 0.8, 1. ]])
        array([[1. , 0.8, 0.6, 0.4, 0.2, 0. ]])

        >>> x.shape
        (12, 5)
        >>> x.first
        (False, True)
        >>> x.bounds
        True
        >>> x._s(1)
        array([[0. , 0.2, 0.4, 0.6, 0.8, 1. ]])
        array([[1. , 0.8, 0.6, 0.4, 0.2, 0. ]])

        >>> x.shape
        (12, 5)
        >>> x.first
        (False, False)
        >>> x.bounds
        True
        >>> x._s(1)
        array([[0. , 0.2, 0.4, 0.6, 0.8, 1. ]])
        array([[1. , 0.8, 0.6, 0.4, 0.2, 0. ]])

        >>> x.shape
        (12, 5)
        >>> x._s(1, s=0.4)
        array([[0.4]])
        array([[0.6]])

        """
        if s is not None:
            s = np.asanyarray(s, dtype=_float64)
            one_minus_s = 1.0 - s
        else:
            size = self.shape[d]
            if self.bounds or not self.first[d]:
                size += 1

            s = np.linspace(0, 1, size, dtype=_float64)

            one_minus_s = s[::-1]

        # Add extra size 1 dimensions so that s and 1-s are guaranteed
        # to be broadcastable to the tie points.
        ndim = self.tie_points.ndim
        if ndim > 1:
            new_shape = [1] * ndim
            new_shape[d] = s.size
            s = s.reshape(new_shape)
            one_minus_s = one_minus_s.reshape(new_shape)

        return (s, one_minus_s)
