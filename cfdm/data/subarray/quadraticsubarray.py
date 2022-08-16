from .abstract import SubsampledSubarray
from .mixin import QuadraticInterpolation


class QuadraticSubarray(QuadraticInterpolation, SubsampledSubarray):
    """A subarray of an array compressed by subsamplng.

    A subarray describes a unique part of the uncompressed array.

    The compressed data is reconstituted by quadratic interpolation.

    See CF section 8.3 "Lossy Compression by Coordinate Subsampling"
    and appendix J "Coordinate Interpolation Methods".

    >>> import numpy as np
    >>> tie_points = np.array([15, 135, 225, 255, 345])
    >>> w = np.array([5, 10, 5])
    >>> coords = {{package}}.QuadraticSubarray(
    ...     tie_points=tie_points,
    ...     tp_indices=(slice(0, 2, None),),
    ...     subsampled_dimensions=(0,),
    ...     shape=(5,),
    ...     subarea_indices=(slice(0, 1, None),),
    ...     first=(True,),
    ...     parameters={'w': w},
    ... )
    >>> print(coords[...])
    [15.0 48.75 80.0 108.75 135.0]
    >>> coords = {{package}}.QuadraticSubarray(
    ...     tie_points=tie_points,
    ...     tp_indices=(slice(1, 3, None),),
    ...     subsampled_dimensions=(0,),
    ...     shape=(4,),
    ...     subarea_indices=(slice(1, 2, None),),
    ...     first=(False,),
    ...     parameters={'w': w},
    ... )
    >>> print(coords[...])
    [173.88888888888889 203.88888888888889 225.0]
    >>> coords = {{package}}.QuadraticSubarray(
    ...     tie_points=tie_points,
    ...     tp_indices=(slice(3, 5, None),),
    ...     subsampled_dimensions=(0,),
    ...     shape=(4,),
    ...     subarea_indices=(slice(2, 3, None),),
    ...     first=(True,),
    ...     parameters={'w': w},
    ... )
    >>> print(coords[...])
    [255.0 289.44444444444446 319.44444444444446 345.0]


    **Cell boundaries**

    When the tie points array represents bounds tie points, then the
    *shape* parameter describes the uncompressed bounds shape.

    >>> bounds_tie_points = np.array([0, 150, 240, 240, 360])
    >>> bounds = {{package}}.QuadraticSubarray(
    ...     tie_points=bounds_tie_points,
    ...     tp_indices=(slice(0, 2, None),),
    ...     subsampled_dimensions=(0,),
    ...     shape=(5, 2),
    ...     subarea_indices=(slice(0, 1, None),),
    ...     first=(True,),
    ...     parameters={'w': w},
    ... )
    >>> print(bounds[...])
    [[0.0 33.2]
     [33.2 64.8]
     [64.8 94.80000000000001]
     [94.80000000000001 123.2]
     [123.2 150.0]]
    >>> bounds = {{package}}.QuadraticSubarray(
    ...     tie_points=bounds_tie_points,
    ...     tp_indices=(slice(1, 3, None),),
    ...     subsampled_dimensions=(0,),
    ...     shape=(3, 2),
    ...     subarea_indices=(slice(1, 2, None),),
    ...     first=(False,),
    ...     parameters={'w': w},
    ... )
    >>> print(bounds[...])
    [[150.0 188.88888888888889]
     [188.88888888888889 218.88888888888889]
     [218.88888888888889 240.0]]
    >>> bounds = {{package}}.QuadraticSubarray(
    ...     tie_points=bounds_tie_points,
    ...     tp_indices=(slice(3, 5, None),),
    ...     subsampled_dimensions=(0,),
    ...     shape=(4, 2),
    ...     subarea_indices=(slice(2, 3, None),),
    ...     first=(True,),
    ...     parameters={'w': w},
    ... )
    >>> print(bounds[...])
    [[240.0 273.75]
     [273.75 305.0]
     [305.0 333.75]
     [333.75 360.0]]

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        (d1,) = tuple(self.compressed_dimensions())

        u_ab = self._select_data()

        u = self._quadratic_interpolation(
            ua=self._select_location(u_ab, {d1: 0}),
            ub=self._select_location(u_ab, {d1: 1}),
            w=self._select_parameter("w"),
            d1=d1,
        )
        u = self._post_process(u)

        if indices is Ellipsis:
            return u

        return u[indices]
