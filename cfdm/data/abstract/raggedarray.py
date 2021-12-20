import numpy as np

from ..subarray import RaggedSubarray
from .compressedarray import CompressedArray


class RaggedArray(CompressedArray):
    """An underlying ragged array.

    See CF section 9 "Discrete Sampling Geometries"

    .. versionadded:: (cfdm) 1.7.0

    """

    def __new__(cls, *args, **kwargs):
        """Store subarray classes.

        If a child class requires different subarray classes than the
        ones defined here, then they must be defined in the __new__
        method of the child class.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        instance = super().__new__(cls)

        instance._Subarray = {
            "ragged contiguous": RaggedSubarray,
            "ragged indexed": RaggedSubarray,
            "ragged indexed contiguous": RaggedSubarray,
        }

        return instance

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        compressed_dimensions={},
        count_variable=None,
        index_variable=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: `Data`
                The compressed data.

            shape: `tuple`
                The shape of the uncompressed array.

            compressed_dimensions: `dict`
                Mapping of dimensions of the compressed array to their
                corresponding dimensions in the uncompressed
                array. Compressed array dimensions that are not
                compressed must be omitted from the mapping.

                *Parameter example:*
                  ``{0: (0, 1)}``

                *Parameter example:*
                  ``{0: (0, 1, 2)}``

            count_variable: `Count`, optional
                A count variable for uncompressing the data,
                corresponding to a CF-netCDF count variable, if
                required by the decompression method.

            index_variable: `Index`, optional
                An index variable for uncompressing the data,
                corresponding to a CF-netCDF count variable, if
                required by the decompression method.

        """
        if count_variable is not None:
            if index_variable is not None:
                compression_type = "ragged indexed contiguous"
            else:
                compression_type = "ragged contiguous"
        elif index_variable is not None:
            compression_type = "ragged indexed"
        else:
            compression_type = None

        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            compressed_dimensions=compressed_dimensions,
            compression_type=compression_type,
            source=source,
            copy=copy,
        )

        if source is not None:
            try:
                index_variable = source.get_index(None)
            except AttributeError:
                index_variable = None

            try:
                count_variable = source.get_count(None)
            except AttributeError:
                count_variable = None

        if index_variable is not None:
            self._set_component("index_variable", index_variable, copy=copy)

        if count_variable is not None:
            self._set_component("count_variable", count_variable, copy=copy)

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed array as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        Subarray = self._Subarray[self.get_compression_type()]

        compression_type = self.get_compression_type()
        Subarray = self._Subarray.get(compression_type)
        if Subarray is None:
            if not compression_type:
                raise IndexError(
                    "Can't subspace ragged data without a "
                    "standardised ragged compression type"
                )

            raise ValueError(
                "Can't subspace ragged data with unknown "
                f"ragged compression type {compression_type!r}"
            )

        # Initialise the un-sliced uncompressed array
        u = np.ma.masked_all(self.shape, dtype=self.dtype)

        compressed_dimensions = self.compressed_dimensions()
        compressed_data = self.conformed_data()["data"]

        for u_indices, u_shape, c_indices in zip(*self.subarrays()):
            subarray = Subarray(
                data=compressed_data,
                indices=c_indices,
                shape=u_shape,
                compressed_dimensions=compressed_dimensions,
            )
            u[u_indices] = subarray[...]

        if indices is Ellipsis:
            return u

        return self.get_subspace(u, indices, copy=True)

    @property
    def dtype(self):
        """Data-type of the uncompressed data."""
        return self.source().dtype

    def get_count(self, default=ValueError()):
        """Return the count variable for the compressed array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `Count`

        """
        out = self._get_component("count_variable", None)
        if out is None:
            if default is None:
                return

            return self._default(
                default, f"{self.__class__.__name__!r} has no count variable"
            )

        return out

    def get_index(self, default=ValueError()):
        """Return the index variable for the compressed array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `Index`

        """
        out = self._get_component("index_variable", None)
        if out is None:
            if default is None:
                return

            return self._default(
                default, f"{self.__class__.__name__!r} has no index variable"
            )

        return out

    def to_memory(self):
        """Bring data disk on disk into memory.

        There is no change to data that is already in memory.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `{{class}}`
                A copy of the array with all of its data in memory.

        """
        a = super().to_memory()

        count = a.get_count(None)
        if count is not None:
            try:
                a._set_component(
                    "count_variable", count.to_memory(), copy=False
                )
            except AttributeError:
                pass

        index = a.get_index(None)
        if index is not None:
            try:
                a._set_component(
                    "index_variable", index.to_memory(), copy=False
                )
            except AttributeError:
                pass

        return a
