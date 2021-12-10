from .linearinterpolation import LinearInterpolation


class BiLinearInterpolation(LinearInterpolation):
    """Mixin class for subsampled arrays that need linear interpolation.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def _bilinear_interpolation(self, ua, ub, uc, ud, d2, d1):
        """Interpolate bilinearly between pairs of tie points.

        General purpose two-dimensional linear interpolation
        method.

        uac = fl(ua, uc, s(ia2, ic2, i2))
        ubd = fl(ub, ud, s(ia2, ic2, i2))
        u(i2, i1) = fl(uac, ubd, s(ia1, ib1, i1))

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_linear_interpolation`

        :Parameters:

            ua, ub, uc, ud: `numpy.ndarray`
               The arrays containing the points for bi-linear
               interpolation along the interpolated dimensions.

            {{d2: `int`}}

            {{d1: `int`}}

        :Returns:

            `numpy.ndarray`

        """
        uac = self._linear_interpolation(ua, uc, d2)
        ubd = self._linear_interpolation(ub, ud, d2)

        u = self._linear_interpolation(uac, ubd, d1)

        return u
