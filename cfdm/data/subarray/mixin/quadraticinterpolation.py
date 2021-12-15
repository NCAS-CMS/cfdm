class QuadraticInterpolation:
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
        """Calculate the quadratic interpolation parameter ``w`` for a
        subsampled dimension.

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

                        A value for the interpolation coeficient ``s`` for the
                        subsampled dimension, at some the location between the
                        two tie points.

                    d: `int`
                        The position in the tie points array of the subsampled
                        dimension.

                    {{s_i: array_like}}
        A value for the interpolation coeficient ``s`` for the
                        subsampled dimension, at some the location between the
                        two tie points.
                :Returns:

                    `numpy.ndarray`

        """
        #        s, one_minus_s = self._s(d, s=s_i)
        s = self._s(d, s=s_i)
        one_minus_s = 1 - s

        return (u_i - one_minus_s * ua - s * ub) / (4 * one_minus_s * s)

    def _quadratic_interpolation(self, ua, ub, w, d1, s=None):
        """Interpolate quadratically between pairs of tie points.

        Computes the quadratic interpolation operator ``fq``, where
        ``fl`` is the linear interpolation operator and ``w`` is the
        quadratic coefficient:

        u = fq(ua, ub, w, s)
          = ua + s*(ub - ua + 4*w*(1-s))
          = ua*(1-s) + ub*s + 4*w*s*(1-s)
          = fl(ua, ub, s) + 4*w*s*(1-s)

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_linear_interpolation`

        :Parameters:

            ua: `numpy.ndarray`
                The first tie point in index space of subsampled
                dimension 1 (in the sense of CF Appendix J Figure
                J.1).

            ub: `numpy.ndarray`
                The second tie point in index space of subsampled
                dimension 1 (in the sense of CF Appendix J Figure
                J.1).

            w: `numpy.ndarray` or `None`
                The quadratic interpolation coefficient, with the same
                number of dimensions in the same relative order as the
                full tie points array. If `None` then assumed to be
                zero.

            {{d1: `int`}}

            {{s: array_like, optional}}

        :Returns:

            `numpy.ndarray`

        """
        s = self._s(d1, s=s)

        if w is not None:
            u = ua + s * (ub - ua + 4 * w * (1 - s))
        else:
            u = ua + s * (ub - ua)

        return u
