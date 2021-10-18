class LinearInterpolation:
    """Mixin class for subsampled arrays that need linear interpolation.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def _linear_interpolation(
        self, ua, ub, subsampled_dimension, subarea_shape, first
    ):
        """Interpolate linearly between pairs of tie points.

        This is the linear interpolation operator ``fl`` defined in CF
        appendix J:

        u = fl(ua, ub, s) = ua + s*(ub-ua)
                          = ua*(1-s) + ub*s

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            ua, ub: array_like
               The arrays containing the points for pair-wise
               interpolation along dimension *subsampled_dimension*.

            subsampled_dimension: `int`
                The position of a subsampled dimension in the
                compressed array.

            subarea_shape: `tuple` of `int`
                The shape of the uncompressed interpolation subararea,
                including all tie points, but excluding a bounds
                dimension.

            first: `tuple`
                For each tie point array dimension, True if the
                interpolation subarea is the first (in index space) of
                a new continuous area, otherwise False.

        :Returns:

            `numpy.ndarray`

        """
        # Get the interpolation coefficents
        s, one_minus_s = self._s(subsampled_dimension, subarea_shape, first)

        # Interpolate
        u = ua * one_minus_s + ub * s

        if not self.bounds and not first[subsampled_dimension]:
            # Remove the first point of the interpolation subarea when
            # it is not the first (in index space) of a continuous
            # area. This is beacuse this value in the uncompressed
            # data has already been calculated from the previous (in
            # index space) interpolation subarea.
            #
            # Only do this if the we are interpolating tie point
            # coordinates.
            #
            # If we are interpolating bounds tie points then we do
            # duplicate the shared tie point for simplicity (although
            # it would be nice not to ...).
            indices = [slice(None)] * u.ndim
            indices[subsampled_dimension] = slice(1, None)
            u = u[tuple(indices)]

        return u
