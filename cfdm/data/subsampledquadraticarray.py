import numpy as np

from .abstract import CompressedArray
from .mixin import LinearInterpolation, SubsampledArray


class SubsampledQuadraticArray(
    LinearInterpolation, SubsampledArray, CompressedArray
):
    """An underlying subsampled array with quadratic interpolation.

    The information needed to uncompress the data is stored in an tie
    point index variable that defines the relationship between the
    indices of the subsampled dimension and the indices of its
    corresponding interpolated dimension.

    >>> coords = cfdm.SubsampledQuadraticArray(
    ...     compressed_array=cfdm.Data([15, 135, 225, 255, 345]),
    ...     shape=(12,),
    ...     ndim=1,
    ...     size=12,
    ...     compressed_axes=[0],
    ...     tie_point_indices={0: cfdm.TiePointIndex(data=[0, 4, 7, 8, 11])},
    ...     interpolation_parameters={
    ...       "w": cfdm.InterpolationParameter(data=[5, 10, 5])
    ...     },
    ...     parameter_dimensions={"w": (0,)},
    ... )
    >>> print(coords[...])
    [ 15.          48.75        80.         108.75       135.
     173.88888889 203.88888889 225.         255.         289.44444444
     319.44444444 345.        ]


    **Cell boundaries**

    If the subsampled array contains cell boundaries, then the
    *shape*, *ndim* and *size* parameters that describe the
    uncompressed array will include the required trailing size 2
    dimension.

    >>> bounds = cfdm.SubsampledQuadraticArray(
    ...     compressed_array=cfdm.Data([0, 150, 240, 240, 360]),
    ...     shape=(12, 2),
    ...     ndim=2,
    ...     size=24,
    ...     compressed_axes=[0],
    ...     tie_point_indices={0: cfdm.TiePointIndex(data=[0, 4, 7, 8, 11])},
    ...     interpolation_parameters={
    ...       "w": cfdm.InterpolationParameter(data=[5, 10, 5])
    ...     },
    ...     parameter_dimensions={"w": (0,)},
    ... )
    >>> print(bounds[...])
    [[  0.          33.2       ]
     [ 33.2         64.8       ]
     [ 64.8         94.8       ]
     [ 94.8        123.2       ]
     [123.2        150.        ]
     [150.         188.88888889]
     [188.88888889 218.88888889]
     [218.88888889 240.        ]
     [240.         273.75      ]
     [273.75       305.        ]
     [305.         333.75      ]
     [333.75       360.        ]]

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        #        dtype=None,
        tie_point_indices={},
        computational_precision=None,
        interpolation_parameters={},
        parameter_dimensions={},
    ):
        """**Initialisation**

                :Parameters:

                    compressed_array: `Data`
                        The tie points array.

                    shape: `tuple`
                        The uncompressed array dimension sizes.

                    size: `int`
                        Number of elements in the uncompressed array.

                    ndim: `int`
                        The number of uncompressed array dimensions.

        #            dtype: data-type, optional
        #               The data-type for the uncompressed array. This datatype
        #               type is also used in all interpolation calculations. By
        #               default, the data-type is double precision float.

                    compressed_axes: sequence of `int`
                        The position of the compressed axis in the tie points
                        array.

                        *Parameter example:*
                          ``compressed_axes=[1]``

                    tie_point_indices: `dict`, optional
                        TODO

                    tie_point_indices: `dict`
                        The tie point index variable for each subsampled
                        dimension. A key indentifies a subsampled dimension by
                        its integer position in the compressed array, and its
                        value is a `TiePointIndex` variable.

                        *Parameter example:*
                          ``tie_point_indices={1: cfdm.TiePointIndex(data=[0, 16])}``

                    computational_precision: `str`, optional
                        The floating-point arithmetic precision used during
                        the preparation and validation of the compressed
                        coordinates.

                        *Parameter example:*
                          ``computational_precision='64'``

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            size=size,
            ndim=ndim,
            #            dtype=dtype,
            compression_type="subsampled",
            interpolation_name="quadratic",
            computational_precision=computational_precision,
            tie_point_indices=tie_point_indices.copy(),
            interpolation_parameters=interpolation_parameters.copy(),
            parameter_dimensions=parameter_dimensions.copy(),
            compressed_dimensions=tuple(tie_point_indices),
            one_to_one=True,
        )

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the array as an independent numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        # If the first or last element is requested then we don't need
        # to interpolate
        try:
            return self._first_or_last_index(indices)
        except IndexError:
            pass

        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        (d0,) = tuple(self.compressed_dimensions())

        tie_points = self._get_compressed_Array()

        self.conform_interpolation_parameters()
        w = self.get_interpolation_parameters().get("w")

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=np.dtype(float))

        # Interpolate the tie points for each interpolation subarea
        for u_indices, tp_indices, subarea_size, first, subarea_index in zip(
            *self._interpolation_subareas()
        ):
            ua = self._select_tie_points(tie_points, tp_indices, {d0: 0})
            ub = self._select_tie_points(tie_points, tp_indices, {d0: 1})
            u = self._quadratic_interpolation(
                ua, ub, d0, subarea_size, first, w, subarea_index
            )

            self._set_interpolated_values(uarray, u, u_indices, (d0,))

        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)

    def _quadratic_interpolation(
        self,
        ua,
        ub,
        subsampled_dimension,
        subarea_shape,
        first,
        w,
        subarea_index,
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

            ua, ub: array_like
               The arrays containing the points for pair-wise
               interpolation along dimension *d0*.

            subsampled_dimension: `int`
                The position of the subsampled dimension in the tie
                points array.

            shape: `tuple` of `int`
                The shape of the interpolation subararea, including
                all tie points.

            first: `tuple` of `bool`
                For each dimension, True if the interpolation subarea
                is the first (in index space) of a new continuous
                area, otherwise False.

            w: `InterpolationParameter` or `None`
                The quadratic coefficient, which must span the
                interpolation subarea dimension instead of the
                subsampled dimension. If `None` then the values of *w*
                are assumed to be zero.

            subarea_index: `tuple` of `slice`
                The index of the interpolation subarea along the
                interpolation subarea dimension. Ignored if *w* is
                `None`.

            trim: `bool`, optional
                For the subsampled dimension, remove the first point
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
            u += 4 * w.data[subarea_index].array * s * one_minus_s

        if trim:
            u = self._trim(u, (subsampled_dimension,), first)

        return u
