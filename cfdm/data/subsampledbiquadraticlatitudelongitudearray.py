from .abstract import CompressedArray
from .mixin import (
    GeographicInterpolation,
    QuadraticInterpolation,
    SubsampledArray,
)


class SubsampledBiQuadraticLatitudeLongitudeArray(
    GeographicInterpolation,
    QuadraticInterpolation,
    SubsampledArray,
    CompressedArray,
):
    """A subsampled array with bi-quadratic latitude-longitude
    interpolation.

    The information needed to uncompress the data is stored in a tie
    point index variable that defines the relationship between the
    indices of the subsampled dimensions and the indices of the
    corresponding interpolated dimensions.

    **Cell boundaries**

    If the subsampled array represents cell boundaries, then the
    *shape*, *ndim* and *size* parameters that describe the
    uncompressed array will include the required trailing size 2
    dimension.

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
                  ``tie_point_indices={0: cfdm.TiePointIndex(data=[0, 16]), 2: cfdm.TiePointIndex(data=[0, 20, 20])}``

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
            interpolation_name="bi_quadratic_latitude_longitude",
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

        (d0, d1) = sorted(self.compressed_dimensions())

        parameters = self.get_parameters(conform=True)
        ce1 = parameters.get("ce1")
        ca1 = parameters.get("ca1")
        ce2 = parameters.get("ce2")
        ca2 = parameters.get("ca2")
        ce3 = parameters.get("ce3")
        ca3 = parameters.get("ca3")
        flags = parameters.get("interpolation_subarea_flags")

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=np.dtype(float))

        for u_indices, tp_indices, subarea_shape, first, subarea_index in zip(
            *self._interpolation_subareas()
        ):
            lat_a = self._select_tie_points(lat, tp_indices, {d0: 0})
            lon_a = self._select_tie_points(lon, tp_indices, {d0: 0})
            lat_b = self._select_tie_points(lat, tp_indices, {d0: 1})
            lon_b = self._select_tie_points(lon, tp_indices, {d0: 1})
            lat_c = self._select_tie_points(lat, tp_indices, {d1: 0})
            lon_c = self._select_tie_points(lon, tp_indices, {d1: 0})
            lat_d = self._select_tie_points(lat, tp_indices, {d1: 1})
            lon_d = self._select_tie_points(lon, tp_indices, {d1: 1})

            lat_p, lon_p = self._bi_quadratic_latitude_longitude_interpolation(
                lat_a,
                lon_a,
                lat_b,
                lon_b,
                lat_c,
                lon_c,
                lat_d,
                lon_d,
                ce1,
                ca1,
                ce2,
                ca2,
                ce3,
                ca3,
                flags,
                d0,
                first,
                subarea_index,
            )

            if is_latitude:
                u = lat_p
            else:
                u = lon_p

            self._set_interpolated_values(uarray, u, u_indices, (d0, d1))

        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)

    def _bi_quadratic_latitude_longitude_interpolation(
        self,
        lat_a,
        lon_a,
        lat_b,
        lon_b,
        lat_c,
        lon_c,
        lat_d,
        lon_d,
        ce1,
        ca1,
        ce2,
        ca2,
        ce3,
        ca3,
        flags,
        subsampled_dimension,
        subarea_index,
        first,
        trim=True,
    ):
        """Bi-quadratic interpolation of geographic coordinates.

        A two-dimensional quadratic method for interpolation of the
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

            lat_c, lon_c: array_like
                The latitudes and longitudes of the second tie point
                in index space.

            lat_d, lon_d: array_like
                The latitudes and longitudes of the second tie point
                in index space.

            ce1, ca1, ce2, ca2, ce3, ca3: `InterpolationParameter` or `None`
                The interpolation parameters "ce1", "ca1", "ce2",
                "ca2", "ce3", "ca3". It is assumed that each 
                coefficient has the same number of dimensions in the
                same relative order as the tie points array, or if `None`
                then the parameter is assumed to be zero.

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
        vc = self._fll2v(lat_c, lon_c)
        vd = self._fll2v(lat_d, lon_d)

        # cea1(tpi2, is1) = fcv2cea(va, vb, cv_ab) SPACE
        cea1_0 = self._fcv2cea(va, vb, cv_ab);

        # cea1(tpi2+1, is1) = fcv2cea(vc, vd, cv_cd)     SPACE    
        cea1_1 = self._fcv2cea(vc, vd, cv_cd)

        # cea2(is2, tpi1) = fcv2cea( va, vc, cv_ac);
        cea2_0 = self._fcv2cea(va, vc, cv_ac)
        
        # cea2(is2, tpi1+1) = fcv2cea( vb, vd, cv_bd);
        cea2_1 = self._fcv2cea(vb, vd, cv_bd)
        
        # cea3(is2, is1) = fcv2cea( vab, vcd, cv_z).
        cea3 = self._fcv2cea(vab, vcd, cv_z)
        
        cv_ac = self._fcea2cv(va, vc, cea2)
        cv_bd = self._fcea2cv(vb, vd, cea2_1)

        vab = self._fqv(va, vb, cv_ab,
                        subsampled_dimension,
                        subarea_shape,
                        subarea_index,
                        first,
                        s=0.5)
        vcd = self._fqv(vc, vd, cv_cd,         subsampled_dimension,
                        subarea_shape,
                        subarea_index,
                        first,
                        s=0.5)
        
        vab = self._fqv(
            va, vb,
            self._fcea2cv(va, vb, self._fcv2cea(va, vb, cv_ab))
            0.5
        )
        vcd = self._fqv(vc, vd, self._fcea2cv(vc, vd, cea1(tpi2 + 1, is1)), 0.5);
        cv_z = self._fcea2cv(vab, vcd, cea3(is2, is1));
        
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
