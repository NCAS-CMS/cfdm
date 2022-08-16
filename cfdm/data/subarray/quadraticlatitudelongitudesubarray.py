from .abstract import SubsampledSubarray
from .mixin import QuadraticLatitudeLongitudeInterpolation


class QuadraticLatitudeLongitudeSubarray(
    QuadraticLatitudeLongitudeInterpolation, SubsampledSubarray
):
    """A subarray of an array compressed by subsamplng.

    A subarray describes a unique part of the uncompressed array.

    The compressed data is reconstituted by quadratic latitude
    longitude interpolation.

    See CF appendix J "Coordinate Interpolation Methods".

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

        return u[indices]
