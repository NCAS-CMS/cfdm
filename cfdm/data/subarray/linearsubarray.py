from .abstract import SubsampledSubarray
from .mixin import LinearInterpolation


class LinearSubarray(LinearInterpolation, SubsampledSubarray):
    """A subsampled array with linear interpolation.

    The information needed to uncompress the data is stored in a tie
    point index variable that defines the relationship between the
    indices of the subsampled dimension and the indices of the
    corresponding interpolated dimension.

    >>> coords = cfdm.SubsampledLinearArray(
    ...     compressed_array=cfdm.Data([15, 135, 225, 255, 345]),
    ...     shape=(12,),
    ...     ndim=1,
    ...     size=12,
    ...     tie_point_indices={0: cfdm.TiePointIndex(data=[0, 4, 7, 8, 11])},
    ... )
    >>> print(coords[...])
    [15.0 45.0 75.0 105.0 135.0 165.0 195.0 225.0 255.0 285.0 315.0 345.0]

    **Cell boundaries**

    If the subsampled array represents cell boundaries, then the
    *shape*, *ndim* and *size* parameters that describe the
    uncompressed array will include the required trailing size 2
    dimension.

    >>> bounds = cfdm.SubsampledLinearArray(
        compressed_array=cfdm.Data([0, 150, 240, 240, 360]),
        shape=(12, 2),
        ndim=2,
        size=24,
        tie_point_indices={0: cfdm.TiePointIndex(data=[0, 4, 7, 8, 11])},
    )
    >>> print(bounds[...])
    [[0.0 30.0]
     [30.0 60.0]
     [60.0 90.00000000000001]
     [90.00000000000001 120.0]
     [120.0 150.0]
     [150.0 180.0]
     [180.0 210.0]
     [210.0 240.0]
     [240.0 270.0]
     [270.0 300.0]
     [300.0 330.0]
     [330.0 360.0]]

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        (d1,) = tuple(self.compressed_dimensions())

        u_ab = self._select_data()

        u = self._linear_interpolation(
            ua=self._select_location(u_ab, {d1: 0}),
            ub=self._select_location(u_ab, {d1: 1}),
            d1=d1,
        )
        u = self._post_process(u)

        if indices is Ellipsis:
            return u

        return self.get_subspace(u, indices, copy=True)
