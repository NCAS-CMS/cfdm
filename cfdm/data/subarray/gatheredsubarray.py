import numpy as np

from .abstract import Subarray


class GatheredSubarray(Subarray):
    """A subarray of an array compressed by gathering.

    A subarray describes a unique part of the uncompressed array.

    See CF section 8.2. "Lossless Compression by Gathering".

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def __init__(
        self,
        data=None,
        indices=None,
        shape=None,
        compressed_dimensions=None,
        uncompressed_indices=None,
        source=None,
        copy=True,
        context_manager=None,
    ):
        """**Initialisation**

        :Parameters:

            data: array_like
                The full compressed array spanning all subarrays, from
                which the elements for this subarray are defined by
                the *indices*.

            indices: `tuple` of `slice`
                The indices of *data* that define this subarray.

            shape: `tuple` of `int`
                The shape of the uncompressed subarray.

            compressed_dimensions: `dict`
                Mapping of compressed to uncompressed dimensions.

                A dictionary key is a position of a dimension in the
                compressed data, with a value of the positions of the
                corresponding dimensions in the uncompressed
                data. Compressed array dimensions that are not
                compressed must be omitted from the mapping.

                *Parameter example:*
                  ``{2: (2,)}``

                *Parameter example:*
                  ``{1: (1, 2)}``

                *Parameter example:*
                  ``{0: (0, 1, 2)}``

            uncompressed_indices: `tuple`
                Indices of the uncompressed subarray for the
                compressed data.

            {{init source: optional}}

            {{init copy: `bool`, optional}}

            context_manager: function, optional
                A context manager that provides a runtime context for
                the conversion of *data* to a `numpy` array.

        """
        super().__init__(
            data=data,
            indices=indices,
            shape=shape,
            compressed_dimensions=compressed_dimensions,
            source=source,
            copy=copy,
            context_manager=context_manager,
        )

        if source is not None:
            try:
                uncompressed_indices = source._get_component(
                    "uncompressed_indices", None
                )
            except AttributeError:
                uncompressed_indices = None

        if uncompressed_indices is not None:
            self._set_component(
                "uncompressed_indices", uncompressed_indices, copy=False
            )

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        u = np.ma.masked_all(self.shape, dtype=self.dtype)

        u[self.uncompressed_indices] = self._select_data(check_mask=False)

        if indices is Ellipsis:
            return u

        return u[indices]

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self.data.dtype

    @property
    def uncompressed_indices(self):
        """Indices of the uncompressed subarray for the compressed data.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self._get_component("uncompressed_indices")
