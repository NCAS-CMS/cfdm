from .abstract import SubsampledSubarray
from .mixin import BiLinearInterpolation


class BiLinearSubarray(BiLinearInterpolation, SubsampledSubarray):
    """A subarray of an array compressed by subsamplng.

    A subarray describes a unique part of the uncompressed array.

    The compressed data is reconstituted by bi-linear interpolation.

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
        (d2, d1) = sorted(self.compressed_dimensions())

        u_abcd = self._select_data()

        u = self._bilinear_interpolation(
            ua=self._select_location(u_abcd, {d2: 0, d1: 0}),
            ub=self._select_location(u_abcd, {d2: 0, d1: 1}),
            uc=self._select_location(u_abcd, {d2: 1, d1: 0}),
            ud=self._select_location(u_abcd, {d2: 1, d1: 1}),
            d2=d2,
            d1=d1,
        )
        u = self._post_process(u)

        if indices is Ellipsis:
            return u

        return u[indices]
