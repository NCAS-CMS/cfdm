class QuadraticInterpolation:
    """Mixin class for quadratic interpolation.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def _fq(self, *args, **kwargs):
        """Alias for `_quadratic_interpolation`.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self._quadratic_interpolation(*args, **kwargs)

    def _fw(self, ua, ub, u_i, d, s_i):
        """Calculate the quadratic interpolation parameter ``w``.

        Calculates the quadratic interpolation parameter ``w`` for a
        subsampled dimension.

        w = fw(ua, ub, u(i), s(i))
          = (u(i) - (1-s(i))*ua - s(i)*ub) / (4*(1-s(i))*s(i))

        See CF appendix J "Coordinate Interpolation Methods".

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_quadratic_interpolation`

        :Parameters:

            ua, ub: `numpy.ndarray`
                The tie points at locations A and B, in the sense of
                CF appendix J Figure J.1.

            u_i: `numpy.ndarray`
                The uncompressed value at the interior location
                implied by *s_i*.

            {{d: `int`}}

            {{s_i: array_like}}

        :Returns:

            `numpy.ndarray`

        """
        s = self._s(d, s=s_i)
        one_minus_s = 1 - s

        return (u_i - one_minus_s * ua - s * ub) / (4 * one_minus_s * s)

    def _quadratic_interpolation(self, ua, ub, w, d1, s=None):
        """Interpolate quadratically between two of tie points.

        Computes the quadratic interpolation operator ``fq``, where
        ``fl`` is the linear interpolation operator and ``w`` is the
        quadratic coefficient:

        u = fq(ua, ub, w, s)
          = ua + s*(ub - ua + 4*w*(1-s))
          = ua*(1-s) + ub*s + 4*w*s*(1-s)
          = fl(ua, ub, s) + 4*w*s*(1-s)

        See CF appendix J "Coordinate Interpolation Methods".

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_linear_interpolation`

        :Parameters:

            ua, ub: `numpy.ndarray`
                The tie points at locations A and B, in the sense of
                CF appendix J Figure J.1.

            w: `numpy.ndarray` or `None`
                The quadratic interpolation coefficient, with the same
                number of dimensions in the same relative order as the
                full tie points array. If `None` then assumed to be
                zero.

            {{d1: `int`}}

            {{s: array_like, optional}}

        :Returns:

            `numpy.ndarray`
                The result of interpolating the tie points to interior
                locations implied by *s*.

        """
        s = self._s(d1, s=s)

        if w is not None:
            u = ua + s * (ub - ua + 4 * w * (1 - s))
        else:
            u = ua + s * (ub - ua)

        return u
