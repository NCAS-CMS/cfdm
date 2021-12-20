from .linearinterpolation import LinearInterpolation


class BiLinearInterpolation(LinearInterpolation):
    """Mixin class for bi-linear interpolation.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def _bilinear_interpolation(self, ua, ub, uc, ud, d2, d1):
        """Interpolate bi-linearly between four points.

        uac = fl(ua, uc, s(ia2, ic2, i2))
        ubd = fl(ub, ud, s(ia2, ic2, i2))
        u(i2, i1) = fl(uac, ubd, s(ia1, ib1, i1))

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_linear_interpolation`

        :Parameters:

            ua: `numpy.ndarray`
                The first point in index space of subsampled dimension
                1 (in the sense of CF appendix J Figure J.2).

            ub: `numpy.ndarray`
                The second point in index space of subsampled
                dimension 1 (in the sense of CF appendix J Figure
                J.2).

            uc: `numpy.ndarray`
                The first point in index space of subsampled dimension
                2 (in the sense of CF appendix J Figure J.2).

            ud: `numpy.ndarray`
                The second point in index space of subsampled
                dimension 2 (in the sense of CF appendix J Figure
                J.2).

            {{d2: `int`}}

            {{d1: `int`}}

        :Returns:

            `numpy.ndarray`

        """
        uac = self._linear_interpolation(ua, uc, d2)
        ubd = self._linear_interpolation(ub, ud, d2)

        u = self._linear_interpolation(uac, ubd, d1)

        return u
