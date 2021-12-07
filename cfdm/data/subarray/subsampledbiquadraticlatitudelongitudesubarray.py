import numpy as np

from .abstract import SubsampledArray
from .mixin import QuadraticGeographicInterpolation


class SubsampledBiQuadraticLatitudeLongitudeSubArray(
        QuadraticGeographicInterpolation,
        SubsampledArray,
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
    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        (d1, d2) = self.subsampled_dimensions

        lat, lon = self.codependent_tie_points("latitude", "longitude")
        
        lat, lon = self._bi_quadratic_latitude_longitude_interpolation(
            lat_a=self._select_tie_point(lat, location={d1: 0, d2: 0}),
            lon_a=self._select_tie_point(lon, location={d1: 0, d2: 0}),
            lat_b=self._select_tie_point(lat, location={d1: 0, d2: 1}),
            lon_b=self._select_tie_point(lon, location={d1: 0, d2: 1}),
            lat_c=self._select_tie_point(lat, location={d1: 1, d2: 0}),
            lon_c=self._select_tie_point(lon, location={d1: 1, d2: 0}),
            lat_d=self._select_tie_point(lat, location={d1: 1, d2: 1}),
            lon_d=self._select_tie_point(lon, location={d1: 1, d2: 1}),
            ce1=self._select_parameter("ce1"),
            ca1=self._select_parameter("ca1"),
            ce2=self._select_parameter("ce2"),
            ca2=self._select_parameter("ca2"),
            ce3=self._select_parameter("ce3"),
            ca3=self._select_parameter("ca3"),
            location_use_3d_cartesian=self._select_parameter(
                "location_use_3d_cartesian"
            ),
            d1=d1,
            d2=d2,
        )
        
        if 'longitude' in self.dependent_tie_points:
            u = lat
        else:
            u = lon
            
        u = self._post_process(u)
        
        if indices is Ellipsis:
            return u
    
        return self.get_subspace(u, indices, copy=True)
            
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
            location_use_3d_cartesian,
            d1,
            d2,
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
        (d1, d2) = subsampled_dimensions

        lla = lat_a, lon_a
        llb = lat_b, lon_b
        llc = lat_c, lon_c
        lld = lat_d, lon_d
        
        va = self._fll2v(*lla)
        vb = self._fll2v(*llb)
        vc = self._fll2v(*llc)
        vd = self._fll2v(*lld)

        cea2 = (
            self._parameter_location(ce2, {d2: 'is', d1: 'tp0'}),            
            self._parameter_location(ca2, {d2: 'is', d1: 'tp0'})
        )
        cv_ac = fcea2cv(va, vc, *cea2)                
                                                       
        cea2 = (
            self._parameter_location(ce2, {d2: 'is', d1: 'tp1'}),            
            self._parameter_location(ca2, {d2: 'is', d1: 'tp1'})
        )
        cv_bd = fcea2cv(vb, vd, *cea2)                
                                                       
        cea1 = (
            self._parameter_location(ce1, {d2: 'tp0', d1: 'is'}),
            self._parameter_location(ca1, {d2: 'tp0', d1: 'is'})
        )
        vab = self._fqv(
            va,
            vb,
            self._fcea2cv(va, vb, *cea1),
            d1,
            s=0.5
        )

        cea1 = (
            self._parameter_location(ce1, {d2: 'tp1', d1: 'is'}),
            self._parameter_location(ca1, {d2: 'tp1', d1: 'is'})
        )
        vcd = self._fqv(
            vc,
            vd,
            self._fcea2cv(vc, vd, *cea1),
            d1,
            s=0.5
        )

        cea3 = (
            self._parameter_location(ce3, {d1: 'is', d2: 'is'}),
            self._parameter_location(ca3, {d1: 'is', d2: 'is'})
        )
        cv_z = self._fcea2cv(vab, vcd, *cea3)
        
        any_cartesian = location_use_3d_cartesian.any()
        all_cartesian = location_use_3d_cartesian.all()

        if any_cartesian:
            # Interpolation in three-dimensional cartesian coordinates
            vac = self._fqv(va, vc, cv_ac, d2)
            vbd = self._fqv(vb, vd, cv_bd, d2)
            vz = self._fqv(vab, vcd, cv_z, d2)
            cv_zz = self._fcv(vac, vbd, vz, d1, s_i=0.5)

            v = self._fqv(vac, vbd, cv_zz, d1)

            v_lat_p, v_lon_p = self._fv2ll(v)

            if all_cartesian:
                lat, lon = v_lat_p, v_lon_p

        if not all_cartesian:
            # Interpolation in latitude-longitude coordinates
            llc_ac = self._fcll(
                *lla,
                *llc,
                *self._fv2ll(self._fqv(va, vc, cv_ac, d2, s=0.5))
                d2,
            )
            llc_bd = self._fcll(
                *llb,
                *lld,
                *self._fv2ll(self._fqv(vb, vd, cv_bd, d2, s=0.5)),
                d2,
            )
            llab = self._fv2ll(vab)
            llcd = self._fv2ll(vcd)
            llc_z = self._fcll(
                *llab,
                *llcd,
                *self._fv2ll(self._fqv(vab, vcd, cv_z, d2, s=0.5))
                d2,
            )

            llac = self._fqll(*lla, *llc, *llc_ac, d2)
            llbd = self._fqll(*llb, *lld, *llc_bd, d2)
            llz = self._fqll(*llab, *llcd, *llc_z, d2)
            cl_zz = self._fcll(*llac, *llbd, *llz, d1)

            ll_lat_p, ll_lon_p = self._fqll(*llac, *llbd, *cl_zz, d1)
            
            if not any_cartesian:
                lat, lon = ll_lat_p,  ll_lon_p 

        if any_cartesian and not all_cartesian:
            # Combine the results of cartesian and latitude-longitude
            # interpolations
            lat = np.where(use_3d_cartesian, v_lat_p, ll_lat_p)
            lon = np.where(use_3d_cartesian, v_lon_p, ll_lon_p)

        return (lat, lon)
