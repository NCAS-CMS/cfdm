import numpy as np

from .abstract import CompressedArray
from .mixin import QuadraticInterpolation, SubsampledArray


class SubsampledQuadraticArray(
    QuadraticInterpolation, SubsampledArray, CompressedArray
):
    """An subsampled array with quadratic interpolation.

    The information needed to uncompress the data is stored in a tie
    point index variable that defines the relationship between the
    indices of the subsampled dimension and the indices of the
    corresponding interpolated dimension.

    >>> coords = cfdm.SubsampledQuadraticArray(
    ...     compressed_array=cfdm.Data([15, 135, 225, 255, 345]),
    ...     shape=(12,),
    ...     ndim=1,
    ...     size=12,
    ...     tie_point_indices={0: cfdm.TiePointIndex(data=[0, 4, 7, 8, 11])},
    ...     parameters={
    ...       "w": cfdm.InterpolationParameter(data=[5, 10, 5])
    ...     },
    ...     parameter_dimensions={"w": (0,)},
    ... )
    >>> print(coords[...])
    [ 15.          48.75        80.         108.75       135.
     173.88888889 203.88888889 225.         255.         289.44444444
     319.44444444 345.        ]


    **Cell boundaries**

    If the subsampled array represents cell boundaries, then the
    *shape*, *ndim* and *size* parameters that describe the
    uncompressed array will include the required trailing size 2
    dimension.

    >>> bounds = cfdm.SubsampledQuadraticArray(
    ...     compressed_array=cfdm.Data([0, 150, 240, 240, 360]),
    ...     shape=(12, 2),
    ...     ndim=2,
    ...     size=24,
    ...     tie_point_indices={0: cfdm.TiePointIndex(data=[0, 4, 7, 8, 11])},
    ...     parameters={
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
        computational_precision=None,
        tie_point_indices={},
        parameters={},
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
            compression_type="subsampled",
            interpolation_name="quadratic",
            computational_precision=computational_precision,
            tie_point_indices=tie_point_indices.copy(),
            parameters=parameters.copy(),
            parameter_dimensions=parameter_dimensions.copy(),
            compressed_dimensions=tuple(tie_point_indices),
            one_to_one=True,
        )

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

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

        parameters = self.get_parameters(conform=True)
        w = parameters.get("w")

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=np.dtype(float))

        # Interpolate the tie points for each interpolation subarea
        for u_indices, tp_indices, subarea_size, first, subarea_index in zip(
            *self._interpolation_subareas()
        ):
            ua = self._select_tie_points(tie_points, tp_indices, {d0: 0})
            ub = self._select_tie_points(tie_points, tp_indices, {d0: 1})
            u = self._quadratic_interpolation(
                ua,
                ub,
                w,
                d0,
                subarea_size,
                subarea_index,
                first,
            )

            self._set_interpolated_values(uarray, u, u_indices, (d0,))

        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)
