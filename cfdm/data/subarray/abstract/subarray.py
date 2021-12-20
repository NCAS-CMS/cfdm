import numpy as np

from ...abstract import Array


class Subarray(Array):
    """Abstract base class for a subarray of compressed array.

    A subarray describes a unique part of the uncompressed array.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(
        self,
        data=None,
        indices=None,
        shape=None,
        compressed_dimensions={},
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            data: array_like
                The full compressed array spanning all subarrays, from
                which the elements for this subarray are defined by
                the *indices*.

            indices: `tuple`
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
                  ``{0: (0, 1)}``

                *Parameter example:*
                  ``{0: (0, 1, 2)}``

                *Parameter example:*
                  ``{2: (2, 3)}``

                *Parameter example:*
                  ``{1: (1,)}``

                *Parameter example:*
                  ``{0: (0,), 2: (2,)}``

            source: optional
                Initialise the subarray from the given object.

                {{init source}}

            copy: `bool`, optional
                If False then do not deep copy input parameters prior
                to initialisation. By default arguments are deep
                copied.

        """
        super().__init__(source=source, copy=copy)

        if source is not None:
            try:
                data = source._get_component("data", None)
            except AttributeError:
                data = None

            try:
                indices = source._get_component("indices", None)
            except AttributeError:
                indices = None

            try:
                shape = source._get_component("shape", None)
            except AttributeError:
                shape = None

            try:
                compressed_dimensions = source.compressed_dimensions()
            except AttributeError:
                compressed_dimensions = {}
        else:
            compressed_dimensions = compressed_dimensions.copy()

        if data is not None:
            self._set_component("data", data, copy=copy)

        if indices is not None:
            self._set_component("indices", indices, copy=False)

        if shape is not None:
            self._set_component("shape", shape, copy=False)

        self._set_component(
            "compressed_dimensions", compressed_dimensions, copy=False
        )

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed subarray.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed subarray as an
        independent numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.__getitem__"
        )  # pragma: no cover

    def _select_data(self, data=None):
        """Select compressed elements that correspond to this subarray.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            data: array_like or `None`
                A full compressed array spanning all subarrays, from
                which the elements for this subarray will be
                returned. By default, or if `None` then the `data`
                array is used.

        :Returns:

            `numpy.ndarray`
                Values of the compressed array that correspond to this
                subarray.

        """
        if data is None:
            data = self.data

        data = np.asanyarray(data[self.indices])
        if not np.ma.is_masked(data):
            data = np.array(data)

        return data

    @property
    def data(self):
        """TODO.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return self._get_component("data")

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.dtype"
        )  # pragma: no cover

    @property
    def indices(self):
        """TODO.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return self._get_component("indices")

    #    @cached_property
    #    def ndim(self):
    #        """The number of dimensions of the uncompressed data.#
    #
    #        .. versionadded:: (cfdm) 1.9.TODO.0
    #
    #        """
    #        return len(self.shape)

    @property
    def shape(self):
        """The number of dimensions of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return self._get_component("shape")

    #    @cached_property
    #    def size(self):
    #        """The size of the uncompressed data.
    #
    #        .. versionadded:: (cfdm) 1.9.TODO.0
    #
    #        """
    #        return reduce(mul, self.shape, 1)

    def compressed_dimensions(self):
        """Mapping of compressed to uncompressed dimensions.

        A dictionary key is a position of a dimension in the
        compressed data, with a value of the positions of the
        corresponding dimensions in the uncompressed data. Compressed
        array dimensions that are not compressed are omitted from the
        mapping.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `dict`
                The mapping of dimensions of the compressed array to
                their corresponding dimensions in the uncompressed
                array. Compressed array dimensions that are not
                compressed are omitted from the mapping.

        """
        return self._get_component("compressed_dimensions").copy()
