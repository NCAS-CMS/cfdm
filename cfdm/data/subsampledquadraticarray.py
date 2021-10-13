import numpy as np

from .subsampledlineararray import SubsampledLinearArray


class SubsampledQuadraticArray(SubsampledLinearArray):
    """TODO.

    .. versionadded:: (cfdm) TODO

    """

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        dtype=None,
        compressed_axes=None,
        tie_point_indices={},
        interpolation_description=None,
        computational_precision=None,
        interpolation_parameters={},
        parameter_dimensions={},
        bounds=False,
            interpolation_variable=None,
    ):
        """Initialisation.

        :Parameters:

            compressed_array: `Data`
                The tie points array.

            shape: `tuple`
                The uncompressed array dimension sizes.

            size: `int`
                Number of elements in the uncompressed array.

            ndim: `int`
                The number of uncompressed array dimensions.

            dtype: data-type, optional
               The data-type for the uncompressed array. This datatype
               type is also used in all interpolation calculations. By
               default, the data-type is double precision float.

            compressed_axes: sequence of `int`
                The position of the compressed axis in the tie points
                array.

                *Parameter example:*
                  ``compressed_axes=[1]``

            tie_point_indices: `dict`, optional
                TODO

            tie_point_indices: `dict`
                The tie point index variable for each subsampled
                dimension. An integer key indentifies a subsampled
                dimensions by its position in the tie points array,
                and the value is a `TiePointIndex` variable.

            computational_precision: `str`, optional
                The floating-point arithmetic precision used during
                the preparation and validation of the compressed
                coordinates.

                *Parameter example:*
                  ``computational_precision='64'``

            bounds: `bool`, optional
                If True then the tie points represent coordinate
                bounds. See CF section 8.3.9 "Interpolation of Cell
                Boundaries".

             interpolation_variable: `Interpolation`


        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            size=size,
            ndim=ndim,
            dtype=dtype,
            compressed_dimension=tuple(compressed_axes),
            compression_type="subsampled",
            interpolation_name="bilinear",
            tie_point_indices=tie_point_indices.copy(),
            interpolation_description=interpolation_description,
            interpolation_parameters=interpolation_parameters.copy(),
            parameter_dimensions=parameter_dimensions.copy(),
            bounds=bounds,
            interpolation_variable=interpolation_variable,
        )

        if dtype is None:
            dtype = self._default_dtype
            
        self.dtype = dtype

    def __getitem__(self, indices):
        """x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the array as an independent numpy array.

        .. versionadded:: (cfdm) TODO

        """
        try:
            # If exactly the first or last element is requested then
            # we don't need to interpolate
            return self._first_or_last_index(indices)
        except IndexError:
            pass

        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        (d0,) = self.get_source_compressed_axes()

        tie_points = self.get_tie_points()

        self.conform_interpolation_parameters()
        w = self.get_interpolation_parameters().get("w")

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=self.dtype)

        # Interpolate the tie points for each interpolation subarea
        for u_indices, tp_indices, subarea_size, first, subarea_index in zip(
            *self.interpolation_subareas()
        ):
            ua = self._select_tie_points(tie_points, tp_indices, {d0: 0})
            ub = self._select_tie_points(tie_points, tp_indices, {d0: 1})
            u = self._quadratic_interpolation(
                ua, ub, (d0,), subarea_size, first, w, subarea_index
            )

            self._set_interpolated_values(uarray, u_indices, (d0,), u)

        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)

    def _quadratic_interpolation( self, ua, ub, subsampled_dimensions,
                                  subarea_shape, first, w, subarea_index ):
        """Interpolate quadratically pairs of tie points.

        Computes the quadratic interpolation operator ``fq`` defined
        in CF appendix J, where ``fl`` is the linear interpolation
        operator and ``w`` is the quadratic coefficient:

        u = fq(ua, ub, w, s) = ua + s*(ub - ua + 4*w*(1-s))
                             = ua*(1-s) + ub*s + 4*w*s*(1-s)
                             = fl(ua, ub, s) + 4*w*s*(1-s)

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_linear_interpolation`

        :Parameters:

            ua, ub: array_like
               The arrays containing the points for pair-wise
               interpolation along dimension *d0*.

            subsampled_dimensions: `tuple` of `int`
                The position of the subsampled dimension in the tie
                points array.

            shape: `tuple` of `int`
                The shape of the interpolation subararea, including
                all tie points.

            first: `tuple` of `bool`
                For each dimension, True if the interpolation subarea
                is the first (in index space) of a new continuous
                area, otherwise False.

            w: array_like or `None`
                The quadratic coefficient, which must span the
                interpolation subarea dimension instead of the
                subsampled dimension. If `None` then it is assumed to
                be zero.

            subarea_index: `tuple` of `slice`
                The index of the interpolation subarea along the
                interpolation subarea dimension. Ignored if *w* is
                `None`.

        :Returns:

            `numpy.ndarray`

        """
        (d0,) = subsampled_dimensions
        u = self._linear_interpolation(ua, ub, d0, subarea_shape, first)

        if w is not None:
            s, one_minus_s = self._s(d0, subarea_shape)
            u += 4 * w[subarea_index] * s * one_minus_s

        return u
