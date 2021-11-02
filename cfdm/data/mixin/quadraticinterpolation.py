from .linearinterpolation import LinearInterpolation


class QuadraticInterpolation(LinearInterpolation):
    """Mixin class for subsampled arrays that need quadratic
    interpolation.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def _fq(self, *args, **kwargs):
        """Alias for `_quadratic_interpolation`.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return self._quadratic_interpolation(*args, **kwargs)

    def _fw(self, ua, ub, u, s):
        """TODO.

        See CF appendix J for details.

        w = fw(ua, ub, u, s)
          = (u - (1-s)*ua - s*ub)/(4*(1-s)*s)

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_quadratic_interpolation`

        :Parameters:

            ua: array_like
                The values of the first tie point in index space.

            ub: array_like
                The values of the second tie point in index space.

            u: array_like
                TODO

            s: array_like
                TODO

        :Returns:

            `numpy.ndarray`

        """
        return (u - (1 - s) * ua - s * ub) / (4 * (1 - s) * s)

    def _quadratic_interpolation(
        self,
        ua,
        ub,
        w,
        subsampled_dimension,
        subarea_shape,
        subarea_index,
        first,
        trim=True,
    ):
        """Interpolate quadratically between pairs of tie points.

        Computes the quadratic interpolation operator ``fq`` defined
        in CF appendix J, where ``fl`` is the linear interpolation
        operator and ``w`` is the quadratic coefficient:

        u = fq(ua, ub, w, s) = ua + s*(ub - ua + 4*w*(1-s))
                             = ua*(1-s) + ub*s + 4*w*s*(1-s)
                             = fl(ua, ub, s) + 4*w*s*(1-s)

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_linear_interpolation`, `_s`, `_trim`

        :Parameters:

            ua: array_like
                The values of the first (in index space) tie point.

            ub: array_like
                The values of the second (in index space) tie point.

            w: `InterpolationParameter` or `None`
                The quadratic coefficient. It is assumed that the
                coefficient has the same number of dimensions in the
                same relative order as the tie points array (see
                `conform_interpolation_parameters`). If `None` then
                the quadratic coefficient is assumed to be zero.

            subsampled_dimension: `int`
                The position of the subsampled dimension in the
                compressed data.

            subarea_shape: `tuple` of `int`
                The shape of the uncompressed interpolation subararea,
                including all tie points, but excluding a bounds
                dimension.

            subarea_index: `tuple` of `slice`
                The index of the interpolation subarea.

            first: `tuple` of `bool`
                For each dimension, True if the interpolation subarea
                is the first (in index space) of a new continuous
                area, otherwise False.

            trim: `bool`, optional
                For the interpolated dimension, remove the first point
                of the interpolation subarea when it is not the first
                (in index space) of a continuous area, and when the
                compressed data are not bounds tie points.

        :Returns:

            `numpy.ndarray`

        """
        u = self._linear_interpolation(
            ua, ub, subsampled_dimension, subarea_shape, first, trim=False
        )

        if w is not None:
            s, one_minus_s = self._s(
                subsampled_dimension, subarea_shape, first
            )
            u += 4 * s * one_minus_s * w.data[subarea_index].array

        if trim:
            u = self._trim(u, (subsampled_dimension,), first)

        return u
