from .linearinterpolation import LinearInterpolation


class QuadraticInterpolation(LinearInterpolation):
    """Mixin class for quadratic interpolation of tie points.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def _fq(self, *args, **kwargs):
        """Alias for `_quadratic_interpolation`.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return self._quadratic_interpolation(*args, **kwargs)

    def _fw(self, ua, ub, u_i, d, s_i):
        """Calculate the quadratic interpolation parameter ``w``.

        w = fw(ua, ub, u(i), s(i))
          = (u(i) - (1-s(i))*ua - s(i)*ub) / (4*(1-s(i))*s(i))

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_quadratic_interpolation`

        :Parameters:

            ua: `numpy.ndarray`
                The values of the first tie point in index space.

            ub: `numpy.ndarray`
                The values of the second tie point in index space.

            u_i: `numpy.ndarray`
                The value of the uncompressed value at the midpoint of
                the subsampled dimension of the interpolation subarea. TODO

            {{d: `int`}}

            {{s_i: array_like}}

        :Returns:

            `numpy.ndarray`

        """
        s, one_minus_s = self._s(d, s=s_i)

        return (u_i - one_minus_s * ua - s * ub) / (4 * one_minus_s * s)

    def _quadratic_interpolation(self, ua, ub, w, d, s=None, returns=False):
        """Interpolate quadratically between pairs of tie points.

        Computes the quadratic interpolation operator ``fq``, where
        ``fl`` is the linear interpolation operator and ``w`` is the
        quadratic coefficient:

        u = fq(ua, ub, w, s)
          = ua + s*(ub - ua + 4*w*(1-s))
          = ua*(1-s) + ub*s + 4*w*s*(1-s)
          = fl(ua, ub, s) + 4*w*s*(1-s)

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_linear_interpolation`, `_s`

        :Parameters:

            ua: `numpy.ndarray`
                The values of the first (in index space) tie point.

            ub: `numpy.ndarray`
                The values of the second (in index space) tie point.

            w: `numpy.ndarray` or `None`
                The quadratic coefficient. It is assumed that the
                coefficient has the same number of dimensions in the
                same relative order as the tie points array. If `None`
                then the quadratic coefficient is assumed to be zero.

            {{d: `int`}}

            {{s: array_like, optional}}

            returns: `bool`, optional
                TODO

        :Returns:

            `numpy.ndarray`

        """
        if returns or w is not None:
            u, s, one_minus_s = self._linear_interpolation(
                ua, ub, d, s=s, returns=True
            )
        else:
            u = self._linear_interpolation(a, ub, d, s=s)

        if w is not None:
            u += 4 * s * one_minus_s * w

        if returns:
            return (u, s, one_minus_s)

        return u
