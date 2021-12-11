import numpy as np

from .abstract import SubsampledSubarray
from .mixin import QuadraticGeographicInterpolation


class BiQuadraticLatitudeLongitudeSubarray(
    QuadraticGeographicInterpolation,
    SubsampledSubarray,
):
    """The subsampled array for a single interpolation subarea.

    The array is uncompressed with a two-dimensional quadratic method
    for interpolation of the geographic coordinates latitude and
    longitude.

    Requires a pair of latitude and longitude tie point variables, one
    of which is given . For each interpolation subarea, none of the
    tie points defining the interpolation subarea are permitted to
    coincide.

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
        (d2, d1) = self.compressed_dimensions

        lat, lon = self._codependent_tie_points("latitude", "longitude")

        u = self._bi_quadratic_latitude_longitude_interpolation(
            lat_a=self._select_data(lat, location={d1: 0, d2: 0}),
            lon_a=self._select_data(lon, location={d1: 0, d2: 0}),
            lat_b=self._select_data(lat, location={d1: 0, d2: 1}),
            lon_b=self._select_data(lon, location={d1: 0, d2: 1}),
            lat_c=self._select_data(lat, location={d1: 1, d2: 0}),
            lon_c=self._select_data(lon, location={d1: 1, d2: 0}),
            lat_d=self._select_data(lat, location={d1: 1, d2: 1}),
            lon_d=self._select_data(lon, location={d1: 1, d2: 1}),
            ce1=self._select_parameter("ce1"),
            ca1=self._select_parameter("ca1"),
            ce2=self._select_parameter("ce2"),
            ca2=self._select_parameter("ca2"),
            ce3=self._select_parameter("ce3"),
            ca3=self._select_parameter("ca3"),
            location_use_3d_cartesian=self._select_parameter(
                "location_use_3d_cartesian"
            ),
            d2=d2,
            d1=d1,
        )
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
        d2,
        d1,
    ):
        """Bi-quadratic interpolation of geographic coordinates.

        A two-dimensional quadratic method for interpolation of the
        geographic coordinates latitude and longitude, typically used
        for remote sensing products with geographic coordinates on the
        reference ellipsoid.

        See CF appendix J "Coordinate Interpolation Methods".

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            lat_a, lon_a: `numpy.ndarray`
                The latitudes and longitudes of the first (in index
                space) tie points of the first subsampled dimension.

            lat_b, lon_b: `numpy.ndarray`
                The latitudes and longitudes of the second (in index
                space) tie points of the first subsampled dimension.

            lat_c, lon_c: `numpy.ndarray`
                The latitudes and longitudes of the first (in index
                space) tie points of the second subsampled dimension.

            lat_d, lon_d: `numpy.ndarray`
                The latitudes and longitudes of the second (in index
                space) tie points of the second subsampled dimension.

            ce1, ca1, ce2, ca2, ce3, ca3: `numpy.ndarray` or `None`
                The interpolation parameters ``ce1``, ``ca1``,
                ``ce2``, ``ca2``, ``ce3``, and ``ca3`` with the same
                number of dimensions in the same relative order as the
                tie points array. If any are `None` then the parameter
                is assumed to be zero.

            {{location_use_3d_cartesian: `numpy.ndarray` or `None`}}

            {{d2: `int`}}

            {{d1: `int`}}

        :Returns:

            `numpy.ndarray`

        """
        # TODO: optimise to remove unnecessary lat or lon calculations

        if location_use_3d_cartesian is None:
            raise ValueError(
                "Can't uncompress tie points by "
                "bi_quadratic_latitude_longitude interpolation "
                "when there is no interpolation_subarea_flags "
                "interpolation parameter that includes "
                "'location_use_3d_cartesian' in its flag_meanings "
                "attribute"
            )

        any_cartesian = bool(location_use_3d_cartesian.any())
        all_cartesian = bool(location_use_3d_cartesian.all())

        latitude = "longitude" in self.dependent_tie_points
        longitude = not latitude

        va = self._fll2v(lat_a, lon_a)
        vb = self._fll2v(lat_b, lon_b)
        vc = self._fll2v(lat_c, lon_c)
        vd = self._fll2v(lat_d, lon_d)

        cea2 = (
            self._parameter_location(ce2, {d1: 0}),
            self._parameter_location(ca2, {d1: 0}),
        )
        cv_ac = self._fcea2cv(va, vc, *cea2)

        cea2 = (
            self._parameter_location(ce2, {d1: 1}),
            self._parameter_location(ca2, {d1: 1}),
        )
        cv_bd = self._fcea2cv(vb, vd, *cea2)

        cea1 = (
            self._parameter_location(ce1, {d2: 0}),
            self._parameter_location(ca1, {d2: 0}),
        )
        vab = self._fqv(va, vb, self._fcea2cv(va, vb, *cea1), d1, s=0.5)

        cea1 = (
            self._parameter_location(ce1, {d2: 1}),
            self._parameter_location(ca1, {d2: 1}),
        )
        vcd = self._fqv(vc, vd, self._fcea2cv(vc, vd, *cea1), d1, s=0.5)

        cea3 = (
            self._parameter_location(ce3, {}),
            self._parameter_location(ca3, {}),
        )
        cv_z = self._fcea2cv(vab, vcd, *cea3)

        if any_cartesian:
            # Interpolation in three-dimensional cartesian coordinates
            vac = self._fqv(va, vc, cv_ac, d2)
            vbd = self._fqv(vb, vd, cv_bd, d2)
            vz = self._fqv(vab, vcd, cv_z, d2)
            cv_zz = self._fcv(vac, vbd, vz, d1, s_i=0.5)

            vp = self._fqv(vac, vbd, cv_zz, d1)

            if latitude:
                fv2ll = self._fv2lat
            else:
                # longitude
                fv2ll = self._fv2lon

            u_c = fv2ll(vp)

            if all_cartesian:
                llp = u_c

        if not all_cartesian:
            # Interpolation in latitude-longitude coordinates
            if latitude:
                fv2ll = self._fv2lat
                lla, llb, llc, lld = lat_a, lat_b, lat_c, lat_d
            else:
                fv2ll = self._fv2lon
                lla, llb, llc, lld = lon_a, lon_b, lon_c, lon_d

            llc_ac = self._fw(
                lla,
                llc,
                fv2ll(self._fqv(va, vc, cv_ac, d2, s=0.5)),
                d2,
                s_i=0.5,
            )
            llc_bd = self._fw(
                llb,
                lld,
                fv2ll(self._fqv(vb, vd, cv_bd, d2, s=0.5)),
                d2,
                s_i=0.5,
            )
            llab = fv2ll(vab)
            llcd = fv2ll(vcd)
            llc_z = self._fw(
                llab,
                llcd,
                fv2ll(self._fqv(vab, vcd, cv_z, d2, s=0.5)),
                d2,
                s_i=0.5,
            )

            llac = self._fq(lla, llc, llc_ac, d2)
            llbd = self._fq(llb, lld, llc_bd, d2)
            llz = self._fq(llab, llcd, llc_z, d2)
            cl_zz = self._fw(llac, llbd, llz, d1, s_i=0.5)

            u_l = self._fq(llac, llbd, llz, d1)

            if not any_cartesian:
                llp = u_l

        if any_cartesian and not all_cartesian:
            # Combine the results of cartesian and latitude-longitude
            # interpolations
            llp = np.where(location_use_3d_cartesian, u_c, u_l)

        return llp
