import numpy as np

from ...abstract import Array


class Subarray(Array):
    """Abstract base class for a subarray of compressed array.

    A subarray describes a unique part of the uncompressed array.

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def __init__(
        self,
        data=None,
        indices=None,
        shape=None,
        compressed_dimensions=None,
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

            indices: `tuple`
                The indices of *data* that define this subarray.

            shape: `tuple` of `int`
                The shape of the uncompressed subarray.

            {{init compressed_dimensions: `dict`}}

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

            {{init source: optional}}

            {{init copy: `bool`, optional}}

            context_manager: function, optional
                A context manager that provides a runtime context for
                the conversion of *data* to a `numpy` array.

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

        elif compressed_dimensions is None:
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

        self._set_component("context_manager", context_manager, copy=False)

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed subarray.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed subarray as an
        independent numpy array.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.__getitem__"
        )  # pragma: no cover

    def _asanyarray(self, data, indices=None, check_mask=True):
        """Convert data to a `numpy` array.

        The conversion takes place with a runtime context, if one has
        been provided.

        By default, the returned array will only a masked array if the
        data contains missing values.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            data: array_like
                The data to be converted.

            check_mask: `bool`, optional
                Check for masked elements, and if there are none
                convert the output to a non-masked `numpy` array.

        :Returns:

            `numpy.ndarray`
                The converted data.

        """
        context_manager = self._get_component("context_manager")
        if context_manager:
            # Convert the data to a numpy array within the given
            # runtime context
            with context_manager():
                if indices is not None:
                    data = data[indices]

                data = np.asanyarray(data)
        else:
            if indices is not None:
                data = data[indices]

            data = np.asanyarray(data)

        if check_mask and np.ma.isMA(data) and not np.ma.is_masked(data):
            data = np.array(data)

        return data

    def _select_data(self, data=None, check_mask=True):
        """Select compressed elements that correspond to this subarray.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            data: array_like or `None`
                A full compressed array spanning all subarrays, from
                which the elements for this subarray will be
                returned. By default, or if `None` then the `data`
                array is used.

            check_mask: `bool`, optional
                Check for masked elements in the selected data, and if
                there are none convert the output to a non-masked
                `numpy` array.

        :Returns:

            `numpy.ndarray`
                Values of the compressed array that correspond to this
                subarray.

        """
        if data is None:
            data = self.data

        return self._asanyarray(
            data, indices=self.indices, check_mask=check_mask
        )

    @property
    def data(self):
        """The full compressed array spanning all subarrays.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self._get_component("data")

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.dtype"
        )  # pragma: no cover

    @property
    def indices(self):
        """The indices of the data that define this subarray.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self._get_component("indices")

    @property
    def shape(self):
        """The shape of the uncompressed data.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self._get_component("shape")

    def compressed_dimensions(self):
        """Mapping of compressed to uncompressed dimensions.

        A dictionary key is a position of a dimension in the
        compressed data, with a value of the positions of the
        corresponding dimensions in the uncompressed data. Compressed
        array dimensions that are not compressed are omitted from the
        mapping.

        .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `dict`
                The mapping of dimensions of the compressed array to
                their corresponding dimensions in the uncompressed
                array. Compressed array dimensions that are not
                compressed are omitted from the mapping.

        """
        c = self._get_component("compressed_dimensions")
        if not c:
            raise ValueError("No compressed dimensions have been defined")

        return c.copy()

    def get_filenames(self):
        """Return the names of any files containing the data.

        .. versionadded:: (cfdm) 1.10.0.2

        :Returns:

            `set`
                The file names in normalised, absolute form. If the
                data are all in memory then an empty `set` is
                returned.

        """
        try:
            return tuple(self.data.get_filenames())
        except AttributeError:
            return ()
