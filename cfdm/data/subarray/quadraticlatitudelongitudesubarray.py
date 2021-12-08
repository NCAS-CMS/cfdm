import numpy as np

from .abstract import SubsampledSubarray
from .mixin import QuadraticGeographicInterpolation


class QuadraticLatitudeLongitudeSubarray(
    QuadraticGeographicInterpolation,
    SubsampledSubarray,
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

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        (d1,) = self.subsampled_dimensions

        lat, lon = self._codependent_tie_points("latitude", "longitude")

        lat, lon = self._quadratic_latitude_longitude_interpolation(
            lat_a=self._select_tie_point(lat, location={d1: 0}),
            lon_a=self._select_tie_point(lon, location={d1: 0}),
            lat_b=self._select_tie_point(lat, location={d1: 1}),
            lon_b=self._select_tie_point(lon, location={d1: 1}),
            ce=self._select_parameter("ce"),
            ca=self._select_parameter("ca"),
            location_use_3d_cartesian=self._select_parameter(
                "location_use_3d_cartesian"
            ),
            subsampled_dimension=d1,
        )

        if "longitude" in self.dependent_tie_points:
            u = lat
        else:
            u = lon

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
        subsampled_dimension,
    ):
        """Quadratic interpolation of geographic coordinates.

        A one-dimensional quadratic method for interpolation of
        the geographic coordinates latitude and longitude,
        typically used for remote sensing products with geographic
        coordinates on the reference ellipsoid.

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

            ce, ca: `InterpolationParameter` or `None`
                The interpolation parameters "ce", "ca". It is
                assumed that each coefficient has the same number of
                dimensions in the same relative order as the tie
                points array, or if `None` then the parameter is
                assumed to be zero.

            location_use_3d_cartesian: `InterpolationParameter` or `None`
                The interpolation parameter
                "interpolation_subarea_flags". It is assumed that the
                parameter has the same number of dimensions in the
                same relative order as the tie points array. If `None`
                then an exception is raised.

            first: `tuple` of `bool`
                For each dimension, True if the interpolation subarea
                is the first (in index space) of a new continuous
                area, otherwise False.

            {{subsampled_dimension: `int`}}
        
        :Returns:

            `numpy.ndarray`

        """
        d1 = subsampled_dimension

        lla = lat_a, lon_a
        llb = lat_b, lon_b

        va = self._fll2v(*lla)
        vb = self._fll2v(*llb)

        cv = self._fcea2cv(va, vb, ce, ca)

        any_cartesian = location_use_3d_cartesian.any()
        all_cartesian = location_use_3d_cartesian.all()

        if any_cartesian:
            # Interpolation in three-dimensional cartesian coordinates
            vp = self._fqv(va, vb, cv, d1)

            v_lat_p, v_lon_p = self._fv2ll(vp)

            if all_cartesian:
                lat, lon = v_lat_p, v_lon_p

        if not all_cartesian:
            # Interpolation in latitude-longitude coordinates
            llab = self._fv2ll(self._fqv(va, vb, cv, d1, s=0.5))
            cll = self._fcll(*lla, *llb, *llab)

            ll_lat_p, ll_lon_p = self._fqll(*lla, *llb, *cll, d1)

            if not any_cartesian:
                lat, lon = ll_lat_p, ll_lon_p

        if any_cartesian and not all_cartesian:
            # Combine the results of cartesian and latitude-longitude
            # interpolations
            lat = np.where(location_use_3d_cartesian, v_lat_p, ll_lat_p)
            lon = np.where(location_use_3d_cartesian, v_lon_p, ll_lon_p)

        return (lat, lon)
