import numpy as np

from .quadraticgeographicinterpolation import QuadraticGeographicInterpolation


class QuadraticLatitudeLongitudeInterpolation(
    QuadraticGeographicInterpolation
):
    """Mixin class for quadratic latitude longitude interpolation.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def _quadratic_latitude_longitude_interpolation(
        self, lat_a, lon_a, lat_b, lon_b, ce, ca, location_use_3d_cartesian, d1
    ):
        """Quadratic interpolation of geographic coordinates.

        A one-dimensional quadratic method for interpolation of the
        geographic coordinates latitude and longitude, typically used
        for remote sensing products with geographic coordinates on the
        reference ellipsoid.

        See CF appendix J "Coordinate Interpolation Methods".

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            lat_a, lon_a: `numpy.ndarray`
                The latitude and longitude of the tie point at
                location A, in the sense of CF appendix J Figure J.3.

            lat_b, lon_b: `numpy.ndarray`
                The latitude and longitude of the tie point at
                location B, in the sense of CF appendix J Figure J.3.

            ce, ca: `numpy.ndarray` or `None`
                The interpolation parameters ``ce`` and ``ca``, with
                the same number of dimensions in the same relative
                order as the tie points array. If any are `None` then
                the parameter is assumed to be zero.

            {{location_use_3d_cartesian: `numpy.ndarray` or `None`}}

            {{d1: `int`}}

        :Returns:

            `numpy.ndarray`
                The result of interpolating the tie points to interior
                locations implied by *s*.

        """
        if location_use_3d_cartesian is None:
            raise ValueError(
                "Can't uncompress tie points by "
                "quadratic_latitude_longitude interpolation "
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

        cv = self._fcea2cv(va, vb, ce, ca)

        if any_cartesian:
            # Interpolation in three-dimensional cartesian coordinates
            vp = self._fqv(va, vb, cv, d1)
            if all_cartesian:
                del va, vb, cv

            u_c = fv2ll(vp)
            del vp

            if all_cartesian:
                llp = u_c

        if not all_cartesian:
            # Interpolation in latitude-longitude coordinates
            if latitude:
                lla, llb = lat_a, lat_b
            else:
                lla, llb = lon_a, lon_b

            llab = fv2ll(self._fqv(va, vb, cv, 0.5))
            del va, vb, cv

            cll = self._fw(lla, llab, llab, s_i=0.5)
            del llab

            u_l = self._fq(lla, llb, cll, d1)
            del lla, llb, cll
            if latitude:
                del lat_a, lat_b
            else:
                del lon_a, lon_b

            if not any_cartesian:
                llp = u_l

        if any_cartesian and not all_cartesian:
            # Combine the results of cartesian and latitude-longitude
            # interpolations
            llp = np.where(location_use_3d_cartesian, u_c, u_l)

        return llp
