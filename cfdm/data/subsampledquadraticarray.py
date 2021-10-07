import numpy as np

from .sampledlineararray import SampledLinearArray


class SampledBiLinearArray(SampledLinearArray):
    """TODO.

    .. versionadded:: (cfdm) TODO

    """

    def __init__(
            self, 
            compressed_array=None,
            shape=None,
            size=None,
            ndim=None,
            compressed_axes=None,
            tie_point_indices={},
            interpolation_description=None,
            computational_precision=None,
            interpolation_parameters={},
            parameter_dimensions={},
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

            compressed_axes: sequence of `int`
                The position of the compressed axis in the tie points
                array.

                *Parameter example:*
                  ``compressed_axes=[1]``

            tie_point_indices: `dict`, optional
                TODO

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            size=size,
            ndim=ndim,
            compressed_axes=compressed_axes,
            interpolation_name="bilinear"
            tie_point_indices=tie_point_indices,
            interpolation_description=interpolation_description,
            interpolation_parameters=interpolation_parameters.copy(),
            parameter_dimensions=parameter_dimensions.copy(),
        )
        
    def __getitem__(self, indices):
        """x.__getitem__(indices) <==> x[indices]
        
        Returns a subspace of the array as an independent numpy array.

        .. versionadded:: (cfdm) TODO

        """
        try:
            # If the first or last element is requested then we don't
            # need to interpolate
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
        uarray = np.ma.masked_all(self.shape, dtype=float)

        # Interpolate the tie points according to CF appendix J
        for u_indices, tp_indices, subarea_size, first, subarea_index in zip(
            *self.interpolation_subareas()
        ):
            ua = self._select_tie_points(tie_points, tp_indices, {d0: 0})
            ub = self._select_tie_points(tie_points, tp_indices, {d0: 1})
            u = self._quadratic_interpolation(ua, ub, d0,
                                              subarea_size, first, w,
                                              subarea_index)
            uarray[u_indices] = u
            
        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)

    def _quadratic_interpolation(self, ua, ub, d0, subarea_shape,
                                 first, w, subarea_index):
        """Interpolate quadratically pairs of tie points.
        
        Computes the function ``fq()`` defined in CF appendix J:
        
        u = fq(ua, ub, w, s) = ua + s*(ub - ua + 4*w*(1-s))
                             = ua*(1-s) + ub*s + 4*w*s*(1-s)
                             = fl(ua, ub, s) + 4*w*s*(1-s)

        .. versionadded:: (cfdm) 1.9.TODO.0
        
        .. seealso:: `_linear_interpolation`
        
        :Parameters:
        
            ua, ub: array_like
               The arrays containing the points for pair-wise
               interpolation along dimension *d0*.
        
            d0: `int`
                The position of the subsampled dimension in the tie
                points array.
 
            shape: `tuple` of `int`
                The shape of the interpolation subararea, including
                all tie points.
 
            first: `tuple`
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
        u = self._linear_interpolation(ua, ub, d0, subarea_shape, first)

        if w is not None:
            s, one_minus_s = self._s(d0, subarea_shape[d0]):
            u += 4 * w[subarea_index] * s * one_minus_s

        return u
