from .abstract import SubsampledSubarray
from .mixin import BiQuadraticLatitudeLongitudeInterpolation


class BiQuadraticLatitudeLongitudeSubarray(
    BiQuadraticLatitudeLongitudeInterpolation, SubsampledSubarray
):
    """A subarray of an array compressed by subsamplng.

    A subarray describes a unique part of the uncompressed array.

    The compressed data is reconstituted by bi-quadratic latitude
    longitude interpolation.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed subarray as an
        independent numpy array.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        (d2, d1) = sorted(self.compressed_dimensions())

        lat, lon = self._codependent_tie_points("latitude", "longitude")

        lat = self._select_data(lat)
        lon = self._select_data(lon)

        u = self._bi_quadratic_latitude_longitude_interpolation(
            lat_a=self._select_location(lat, {d2: 0, d1: 0}),
            lon_a=self._select_location(lon, {d2: 0, d1: 0}),
            lat_b=self._select_location(lat, {d2: 0, d1: 1}),
            lon_b=self._select_location(lon, {d2: 0, d1: 1}),
            lat_c=self._select_location(lat, {d2: 1, d1: 0}),
            lon_c=self._select_location(lon, {d2: 1, d1: 0}),
            lat_d=self._select_location(lat, {d2: 1, d1: 1}),
            lon_d=self._select_location(lon, {d2: 1, d1: 1}),
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

        return u[indices]
