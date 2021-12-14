class LinearInterpolation:
    """Mixin class for linear interpolation of tie points.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def _linear_interpolation(self, ua, ub, d1, s=None, returns=False):
        """Interpolate linearly between pairs of tie points.

        General purpose one-dimensional linear interpolation method.

        u = fl(ua, ub, s) = ua + s*(ub-ua)
                          = ua*(1-s) + ub*s

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_s`

        :Parameters:

            ua: `numpy.ndarray`
                The first tie point in index space of subsampled
                dimension 1 (in the sense of CF Appendix J Figure
                J.1).

            ub: `numpy.ndarray`
                The second tie point in index space of subsampled
                dimension 1 (in the sense of CF Appendix J Figure
                J.1).

            {{d1: `int`}}

            {{s: array_like, optional}}

        :Returns:

            `numpy.ndarray`
                TODO

        """
        s = self._s(d1, s=s)    
        u = ua + s * (ub - ua)

        if returns:
            return (u, s)

        return u
