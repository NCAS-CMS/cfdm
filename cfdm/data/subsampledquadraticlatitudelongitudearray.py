import numpy as np

from .abstract import CompressedArray
from .mixin import (
    GeographicInterpolation,
    QuadraticInterpolation,
    SubsampledArray,
)


class SubsampledQuadraticLatitudeLongitudeArray(
    GeographicInterpolation,
    QuadraticInterpolation,
    SubsampledArray,
    CompressedArray,
):
    """A subsampled array with quadratic latitude-longitude interpolation.

    The information needed to uncompress the data is stored in a tie
    point index variable that defines the relationship between the
    indices of the subsampled dimension and the indices of the
    corresponding interpolated dimension.

    **Cell boundaries**

    If the subsampled array represents cell boundaries, then the
    *shape*, *ndim* and *size* parameters that describe the
    uncompressed array will include the required trailing size 2
    dimension.

    See CF appendix J "Coordinate Interpolation Methods" for details.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        interpolation_description=None,
        computational_precision=None,
        tie_point_indices={},
        parameters={},
        parameter_dimensions={},
        dependent_tie_points={},
        dependent_tie_point_dimensions={},
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
            interpolation_name="quadratic_latitude_longitude",
            computational_precision=computational_precision,
            tie_point_indices=tie_point_indices.copy(),
            parameters=parameters.copy(),
            parameter_dimensions=parameter_dimensions.copy(),
            dependent_tie_points=dependent_tie_points.copy(),
            dependent_tie_point_dimensions=dependent_tie_point_dimensions.copy(),
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
        lat, lon = self.codependent_tie_points("latitude", "longitude")
        is_latitude = 'latitude' not in self.get_dependent_tie_points()

        (d0,) = tuple(self.compressed_dimensions())

        parameters = self.get_parameters(conform=True)
        ce = parameters.get("ce")
        ca = parameters.get("ca")
        flags = parameters.get("interpolation_subarea_flags")

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=np.dtype(float))

        # Interpolate the tie points for each interpolation subarea
        for u_indices, tp_indices, subarea_size, first, subarea_index in zip(
            *self._interpolation_subareas()
        ):
            lat_a = self._select_tie_points(lat, tp_indices, {d0: 0})
            lon_a = self._select_tie_points(lon, tp_indices, {d0: 0})
            lat_b = self._select_tie_points(lat, tp_indices, {d0: 1})
            lon_b = self._select_tie_points(lon, tp_indices, {d0: 1})

            lat_p, lon_p = self._quadratic_latitude_longitude_interpolation(
                lat_a,
                lon_a,
                lat_b,
                lon_b,
                ce,
                ca,
                flags,
                d0,
                first,
                subarea_index,
            )

            if is_latitude:
                u = lat_p
            else:
                u = lon_p

            self._set_interpolated_values(uarray, u, u_indices, (d0,))

        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)

    def _fcll(self, lat_a, lon_a, lat_b, lon_b, va, vb, cv):
        """TODO.

        cll = fcll(lla, llb, llab)
            = (fw(lla.lat, llb.lat, llab.lat, 0.5),
               fw(lla.lon, llb.lon, llab.lon, 0.5))

        where

        llab = fv2ll(fqv(va, vb, cv, 0.5))

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        (lat_ab, lon_ab) = self._fv2ll(
            self._fqv(
                va, vb,
                cv,
                subsampled_dimension,
                subarea_shape,
                subarea_index,
                first,
                s=0.5
        )

        return (
            self._fw(lat_a, lat_b, lat_ab, s=0.5),
            self._fw(lon_a, lon_b, lon_ab, s=0.5),
        )

    def _quadratic_latitude_longitude_interpolation(
        self,
        lat_a,
        lon_a,
        lat_b,
        lon_b,
        ce,
        ca,
        flags,
        subsampled_dimension,
        subarea_index,
        first,
        trim=True,
    ):
        """Quadratic interpolation of geographic coordinates.

        A one-dimensional quadratic method for interpolation of the
        geographic coordinates latitude and longitude, typically used
        for remote sensing products with geographic coordinates on the
        reference ellipsoid.

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            lat_a, lon_a: array_like
                The latitudes and longitudes of the first tie point in
                index space space.

            lat_b, lon_b: array_like
                The latitudes and longitudes of the second tie point
                in index space.

            ce1, ca1: `InterpolationParameter` or `None`
                The interpolation parameters "ce1", "ca1". It is
                assumed that each coefficient has the same number of
                dimensions in the same relative order as the tie
                points array, or if `None` then the parameter is
                assumed to be zero.

            flags: `InterpolationParameter` or `None`
                The interpolation parameter
                "interpolation_subarea_flags". It is assumed that the
                parameter has the same number of dimensions in the
                same relative order as the tie points array. If `None`
                then an exception is raised.

            subsampled_dimension: `int`
                The position of the subsampled dimension in the
                compressed data.

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
        use_3d_cartesian = self._use_3d_cartesian(flags, subarea_index)
        any_cartesian = use_3d_cartesian.any()
        all_cartesian = use_3d_cartesian.all()

        va = self._fll2v(lat_a, lon_a)
        vb = self._fll2v(lat_b, lon_b)
        cv = self._fcea2cv(va, vb, ce, ca, subarea_index)

        if any_cartesian:
            # Interpolation in three-dimensional cartesian coordinates
            vp = self._fqv(
                va,
                vb,
                cv,
                subsampled_dimension,
                subarea_shape,
                subarea_index,
                first,
            )
            v_lat_p, v_lon_p = self._fv2ll(vp)
            if all_cartesian:
                lat_p, lon_p = v_lat_p, v_lon_p

        if not all_cartesian:
            # Interpolation in latitude-longitude coordinates
            lat_c, lon_c = self._fcll(lat_a, lon_a, lat_b, lon_b, va, vb, cv)
            ll_lat_p, ll_lon_p = self._fqll(
                lat_a,
                lon_a,
                lat_b,
                lon_b,
                lat_c,
                lon_c,
                subsampled_dimension,
                subarea_shape,
                subarea_index,
                first,
            )
            if not any_cartesian:
                lat_p, lon_p = ll_lat_p, ll_lon_p

        if any_cartesian and not all_cartesian:
            # Combine the results of cartesian and latitude-longitude
            # interpolations
            lat_p = np.where(use_3d_cartesian, v_lat_p, ll_lat_p)
            lon_p = np.where(use_3d_cartesian, v_lon_p, ll_lon_p)

        if trim:
            lat_p = self._trim(lat_p, (subsampled_dimension,), first)
            lon_p = self._trim(lon_p, (subsampled_dimension,), first)

        return (lat_p, lon_p)
