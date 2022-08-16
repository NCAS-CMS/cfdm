import numpy as np

from .quadraticgeographicinterpolation import QuadraticGeographicInterpolation


class BiQuadraticLatitudeLongitudeInterpolation(
    QuadraticGeographicInterpolation
):
    """Mixin class for bi-quadratic latitude longitude interpolation.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.10.0.0

    """

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

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            lat_a, lon_a: `numpy.ndarray`
                The latitude and longitude of the tie point at
                location A, in the sense of CF appendix J Figure J.2.

            lat_b, lon_b: `numpy.ndarray`
                The latitude and longitude of the tie point at
                location B, in the sense of CF appendix J Figure J.2.

            lat_c, lon_c: `numpy.ndarray`
                The latitude and longitude of the tie point at
                location C, in the sense of CF appendix J Figure J.2.

            lat_d, lon_d: `numpy.ndarray`
                The latitude and longitude of the tie point at
                location D, in the sense of CF appendix J Figure J.2.

            ce1, ca1, ce2, ca2, ce3, ca3: `numpy.ndarray` or `None`
                The interpolation parameters ``ce1``, ``ca1``,
                ``ce2``, ``ca2``, ``ce3``, and ``ca3``, with the same
                number of dimensions in the same relative order as the
                full tie points array. If any are `None` then those
                parameter are assumed to be zero.

            {{location_use_3d_cartesian: `numpy.ndarray` or `None`}}

            {{d2: `int`}}

            {{d1: `int`}}

        :Returns:

            `numpy.ndarray`

        """
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

        # Find out if these tie points are latitudes or longitudes. If
        # they are latitudes then the dependent tie points will be
        # longitudes.
        latitude = "longitude" in self.dependent_tie_points

        if latitude:
            fv2ll = self._fv2lat
        else:
            fv2ll = self._fv2lon

        va = self._fll2v(lat_a, lon_a)
        vb = self._fll2v(lat_b, lon_b)
        vc = self._fll2v(lat_c, lon_c)
        vd = self._fll2v(lat_d, lon_d)

        # ce2, ca2: Span interpolation subarea dimension 2 and
        #           subsampled dimension 1
        cea2 = (
            self._select_location(ce2, {d1: 0}),
            self._select_location(ca2, {d1: 0}),
        )
        cv_ac = self._fcea2cv(va, vc, *cea2)

        cea2 = (
            self._select_location(ce2, {d1: 1}),
            self._select_location(ca2, {d1: 1}),
        )
        cv_bd = self._fcea2cv(vb, vd, *cea2)
        del cea2

        # ce1, ca1: Span subsampled dimension 2 and interpolation
        #           subarea dimension 1
        cea1 = (
            self._select_location(ce1, {d2: 0}),
            self._select_location(ca1, {d2: 0}),
        )
        vab = self._fqv(va, vb, self._fcea2cv(va, vb, *cea1), d1, s=0.5)

        cea1 = (
            self._select_location(ce1, {d2: 1}),
            self._select_location(ca1, {d2: 1}),
        )
        vcd = self._fqv(vc, vd, self._fcea2cv(vc, vd, *cea1), d1, s=0.5)
        del cea1

        # ce3, ca3: Span interpolation subarea dimension 2 and
        #           interpolation subarea dimension 1
        cea3 = (self._select_location(ce3, {}), self._select_location(ca3, {}))
        cv_z = self._fcea2cv(vab, vcd, *cea3)
        del cea3

        if any_cartesian:
            # Interpolation in three-dimensional cartesian coordinates
            vac = self._fqv(va, vc, cv_ac, d2)
            if all_cartesian:
                del va, vc, cv_ac

            vbd = self._fqv(vb, vd, cv_bd, d2)
            if all_cartesian:
                del vb, vd, cv_bd

            vz = self._fqv(vab, vcd, cv_z, d2)
            if all_cartesian:
                del vab, vcd, cv_z

            cv_zz = self._fcv(vac, vbd, vz, d1, s_i=0.5)
            del vz

            vp = self._fqv(vac, vbd, cv_zz, d1)
            del vac, vbd, cv_zz

            u_c = fv2ll(vp)
            del vp

            if all_cartesian:
                llp = u_c

        if not all_cartesian:
            # Interpolation in latitude-longitude coordinates
            if latitude:
                lla, llb, llc, lld = lat_a, lat_b, lat_c, lat_d
            else:
                lla, llb, llc, lld = lon_a, lon_b, lon_c, lon_d

            llc_ac = self._fw(
                lla,
                llc,
                fv2ll(self._fqv(va, vc, cv_ac, d2, s=0.5)),
                d2,
                s_i=0.5,
            )
            del va, vc, cv_ac

            llac = self._fq(lla, llc, llc_ac, d2)
            del lla, llc, llc_ac
            if latitude:
                del lat_a, lat_c
            else:
                del lon_a, lon_c

            llc_bd = self._fw(
                llb,
                lld,
                fv2ll(self._fqv(vb, vd, cv_bd, d2, s=0.5)),
                d2,
                s_i=0.5,
            )
            del vb, vd, cv_bd

            llbd = self._fq(llb, lld, llc_bd, d2)
            del llb, lld, llc_bd
            if latitude:
                del lat_b, lat_d
            else:
                del lon_b, lon_d

            llab = fv2ll(vab)
            llcd = fv2ll(vcd)
            llc_z = self._fw(
                llab,
                llcd,
                fv2ll(self._fqv(vab, vcd, cv_z, d2, s=0.5)),
                d2,
                s_i=0.5,
            )
            del vab, vcd, cv_z

            llz = self._fq(llab, llcd, llc_z, d2)
            del llc_z

            cl_zz = self._fw(llac, llbd, llz, d1, s_i=0.5)
            del llz

            u_l = self._fq(llac, llbd, cl_zz, d1)
            del llac, llbd, cl_zz

            if not any_cartesian:
                llp = u_l

        if any_cartesian and not all_cartesian:
            # Combine the results of cartesian and latitude-longitude
            # interpolations
            llp = np.where(location_use_3d_cartesian, u_c, u_l)

        return llp
