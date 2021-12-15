import numpy as np

from .abstract import SubsampledSubarray
from .mixin import QuadraticGeographicInterpolation


class QuadraticLatitudeLongitudeSubarray(
    QuadraticGeographicInterpolation,
    SubsampledSubarray,
):
    """A subsampled array with quadratic latitude-longitude
    interpolation.

    The information needed to uncompress the data is stored in a tie
    point index variable that defines the relationship between the
    indices of the subsampled dimension and the indices of the
    corresponding interpolated dimension.

    **Cell boundaries**

    If the subsampled array represents cell boundaries, then the
    *shape*, *ndim* and *size* parameters that describe the
    uncompressed array will include the required trailing size 2
    dimension.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        (d1,) = tuple(self.compressed_dimensions)

        lat, lon = self._codependent_tie_points("latitude", "longitude")

        lat = self._select_data(lat)
        lon = self._select_data(lon)

        u = self._quadratic_latitude_longitude_interpolation(
            lat_a=self._select_location(lat, {d1: 0}),
            lon_a=self._select_location(lon, {d1: 0}),
            lat_b=self._select_location(lat, {d1: 1}),
            lon_b=self._select_location(lon, {d1: 1}),
            ce=self._select_parameter("ce"),
            ca=self._select_parameter("ca"),
            location_use_3d_cartesian=self._select_parameter(
                "location_use_3d_cartesian"
            ),
            d1=d1,
        )
        u = self._post_process(u)

        if indices is Ellipsis:
            return u

        return self.get_subspace(u, indices, copy=True)

    def _quadratic_latitude_longitude_interpolation(
        self,
        lat_a,
        lon_a,
        lat_b,
        lon_b,
        ce,
        ca,
        location_use_3d_cartesian,
        d1,
    ):
        """Quadratic interpolation of geographic coordinates.

        A one-dimensional quadratic method for interpolation of
        the geographic coordinates latitude and longitude,
        typically used for remote sensing products with geographic
        coordinates on the reference ellipsoid.

        See CF appendix J "Coordinate Interpolation Methods".

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            lat_a, lon_a: `numpy.ndarray`
                The latitudes and longitudes of the first (in index
                space) tie points of the subsampled dimension.

            lat_b, lon_b: `numpy.ndarray`
                The latitudes and longitudes of the second (in index
                space) tie points of the subsampled dimension.

            ce, ca: `numpy.ndarray` or `None`
                The interpolation parameters ``ce`` and ``ca``, with
                the same number of dimensions in the same relative
                order as the tie points array. If any are `None` then
                the parameter is assumed to be zero.

            {{location_use_3d_cartesian: `numpy.ndarray` or `None`}}

            {{d1: `int`}}

        :Returns:

            `numpy.ndarray`

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

        latitude = "longitude" in self.dependent_tie_points
        longitude = not latitude

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
