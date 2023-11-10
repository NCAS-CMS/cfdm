from .subarray import Subarray


class MeshSubarray(Subarray):
    """A subarray of an arry defined by a UGRID connectivity variable.

    .. versionadded:: (cfdm) UGRIDVER

    """

    def __init__(
        self,
        data=None,
        indices=None,
        shape=None,
        compressed_dimensions=None,
        dtype=None,
        start_index=None,
        cell_dimension=None,
        source=None,
        copy=True,
        context_manager=None,
    ):
        """**Initialisation**

        :Parameters:

            data: array_like
                A 2-d integer array that contains zero-based indices
                that identifies UGRID nodes for each cell, as found in
                a UGRID connectivty variable. This array contains the
                indices for all subarrays.

            indices: `tuple` of `slice`
                The indices of *data* that define this subarray.

            shape: `tuple` of `int`
                The shape of the uncompressed subarray.

            {{init compressed_dimensions: `dict`}}

            {{init start_index: `int`}}

            {{init cell_dimension: `int`}}

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
                start_index = source.get_start_index(None)
            except AttributeError:
                start_index = None

            try:
                cell_dimension = source.get_cell_dimension(None)
            except AttributeError:
                cell_dimension = None

        if start_index is not None:
            self._set_component("start_index", start_index, copy=False)

        if cell_dimension is not None:
            self._set_component("cell_dimension", cell_dimension, copy=False)

    def _select_data(self, data=None, check_mask=True):
        """Select compressed elements that correspond to this subarray.

        .. versionadded:: (cfdm) UGRIDVER

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

        indices = self.indices
        cell_dimension = self.cell_dimension
        if cell_dimension == 1:
            # The 2-d data is stored with the wrong axis order
            indices = indices[::-1]

        array = self._asanyarray(data, indices=indices, check_mask=check_mask)

        if cell_dimension == 1:
            array = array.T

        return array

    @property
    def cell_dimension(self):
        """The position of the dimension that indexes the cells.

        Either ``0`` or ``1``.

        .. versionadded:: (cfdm) UGRIDVER

        """
        return self._get_component("cell_dimension")

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) UGRIDVER

        """
        return self.data.dtype

    @property
    def start_index(self):
        """The start index of values in the compressed data.

        Either ``0`` or ``1``.

        .. versionadded:: (cfdm) UGRIDVER

        """
        return self._get_component("start_index")
