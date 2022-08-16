from .linearinterpolation import LinearInterpolation


class BiLinearInterpolation(LinearInterpolation):
    """Mixin class for bi-linear interpolation.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def _bilinear_interpolation(self, ua, ub, uc, ud, d2, d1):
        """Interpolate bi-linearly between four points.

        uac = fl(ua, uc, s(ia2, ic2, i2))
        ubd = fl(ub, ud, s(ia2, ic2, i2))
        u(i2, i1) = fl(uac, ubd, s(ia1, ib1, i1))

        See CF appendix J "Coordinate Interpolation Methods".

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_linear_interpolation`, `_s`

        :Parameters:

            ua, ub: `numpy.ndarray`
                The tie points at locations A and B, in the sense of
                CF appendix J Figure J.2.

            uc, ud: `numpy.ndarray`
                The tie points at locations C and D, in the sense of
                CF appendix J Figure J.2.

            {{d2: `int`}}

            {{d1: `int`}}

        :Returns:

            `numpy.ndarray`
                The result of interpolating the tie points to interior
                locations implied by *s*.

        """
        uac = self._linear_interpolation(ua, uc, d2)
        ubd = self._linear_interpolation(ub, ud, d2)

        u = self._linear_interpolation(uac, ubd, d1)

        return u
