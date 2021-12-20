import numpy as np

from .abstract import Subarray


class GatheredSubarray(Subarray):
    """A subarray of an array compressed by gathering.

    A subarray describes a unique part of the uncompressed array.

    See CF section 8.2. "Lossless Compression by Gathering".

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(
        self,
        data=None,
        indices=None,
        shape=None,
        compressed_dimensions={},
        unravelled_indices=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            data: array_like
                The full compressed array spanning all subarrays, from
                which the elements for this subarray are defined by
                the *indices*.

            indices: `tuple` of `slice`
                The inidces of *data* that are needed to uncompress
                this subarray.

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

            unravelled_indices: `tuple`
                TODO

            source: optional
                Initialise the subarray from the given object.

                {{init source}}

            copy: `bool`, optional
                If False then do not deep copy input parameters prior
                to initialisation. By default arguments are deep
                copied.

        """
        super().__init__(
            data=data,
            indices=indices,
            shape=shape,
            compressed_dimensions=compressed_dimensions,
            source=source,
            copy=copy,
        )

        if source is not None:
            try:
                unravelled_indices = source._get_component(
                    "unravelled_indices", None
                )
            except AttributeError:
                unravelled_indices = None

        if unravelled_indices is not None:
            self._set_component(
                "unravelled_indices", unravelled_indices, copy=False
            )

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        u = np.ma.masked_all(self.shape, dtype=self.dtype)

        u[self.unravelled_indices] = self._select_data()

        if indices is Ellipsis:
            return u

        return u[indices]

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return self.data.dtype

    @property
    def unravelled_indices(self):
        """TODO.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return self._get_component("unravelled_indices")
