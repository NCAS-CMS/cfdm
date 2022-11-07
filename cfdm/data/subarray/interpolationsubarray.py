from .abstract import SubsampledSubarray


class InterpolationSubarray(SubsampledSubarray):
    """A subarray of an array compressed by subsamplng.

    A subarray describes a unique part of the uncompressed array.

    The subarray has no standardised interpolation algorithm. An
    interpolation algorithm may have been provided via the
    *interpolation_description* parameter, but that algorithm can not
    be interpreted by the {{class}} object. Nonetheless, the subarray
    is still representable in its uncompressed form (e.g. its shape is
    known), even though the uncompressed data values can not be
    calculated.

    See CF section 8.3.3 "Interpolation Variable".

    .. versionadded:: (cfdm) 1.10.0.2

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Always raises a `ValueError`, rather than returning a subspace
        of the uncompressed data as an independent numpy array, since
        the non-standardised interpolation algorithm can't be
        interpreted.

        .. versionadded:: (cfdm) 1.10.0.2

        """
        raise ValueError(
            "Can't uncompress subsampled data using a non-standardised "
            "interpolation algorithm:\n\n"
            f"{self.get_interpolation_description('')}"
        )
