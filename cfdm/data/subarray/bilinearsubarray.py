from .abstract import SubsampledSubarray
from .mixin import BiLinearInterpolation


class BiLinearSubarray(BiLinearInterpolation, SubsampledSubarray):
    """TODO.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

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

        return self.get_subspace(u, indices, copy=True)
