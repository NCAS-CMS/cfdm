class LinearInterpolation:
    """Mixin class for linear interpolation.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def _linear_interpolation(self, ua, ub, d1, s=None):
        """Interpolate linearly between two points.

        u = fl(ua, ub, s) = ua + s*(ub-ua)
                          = ua*(1-s) + ub*s

        See CF appendix J "Coordinate Interpolation Methods".

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_s`

        :Parameters:

            ua, ub: `numpy.ndarray`
                The tie points at locations A and B, in the sense of
                CF appendix J Figure J.1.

            {{d1: `int`}}

            {{s: array_like, optional}}

        :Returns:

            `numpy.ndarray`
                The result of interpolating the tie points to interior
                locations implied by *s*.

        """
        s = self._s(d1, s=s)
        u = ua + s * (ub - ua)
        return u
