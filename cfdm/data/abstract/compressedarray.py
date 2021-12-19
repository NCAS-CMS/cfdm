# TODO: Remove once only python +3.8 is supported:
import sys

from functools import reduce
from operator import mul

import numpy as np

from ..utils import cached_property

from .array import Array


class DeprecationError(Exception):
    """Deprecation error."""

    pass


class CompressedArray(Array):
    """Mixin class for a container of an underlying compressed array.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __new__(cls, *args, **kwargs):
        """Store subarray classes.

        A child class must define its subarray classes in the
        `_Subarray` dictionary.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        instance = super().__new__(cls)
        instance._Subarray = {}
        return instance

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        compressed_dimension=None,
        compressed_dimensions={},
        compression_type=None,
        **kwargs,
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: subclass of `Array`
                The compressed array.

            shape: `tuple`
                The uncompressed array dimension sizes.

            size: `int`
                Deprecated at version 1.9.TODO.0. If set will be
                ignored.

                Number of elements in the uncompressed array.

            ndim: `int`
                Deprecated at version 1.9.TODO.0. If set will be
                ignored.

                The number of uncompressed array dimensions

            compressed_dimensions: `dict`
                Mapping of dimensions of the compressed array to their
                corresponding dimensions in the uncompressed
                array. Compressed array dimensions that are not
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

                .. versionadded:: (cfdm) 1.9.TODO.0

            compression_type: `str`
                The type of compression.

            kwargs: optional
                Further named parameters and their values needed to define
                the compressed array.

            compressed_dimension: Deprecated at version 1.9.TODO.0
                Use the *compressed_dimensions* parameter instead.

        """
        if compressed_dimension is not None:
            raise DeprecationError(
                "The 'compressed_dimension' keyword was deprecated at "
                "version 1.9.TODO.0. "
                "Use the 'compressed_dimensions' keyword instead."
            )  # pragma: no cover

        super().__init__(
            shape=shape,
            size=size,
            ndim=ndim,
            compressed_dimensions=compressed_dimensions.copy(),
            compression_type=compression_type,
            **kwargs,
        )

        self._set_compressed_Array(compressed_array, copy=False)

#    def __getitem__(self, indices):
#        """Return a subspace of the uncompressed data.
#
#        x.__getitem__(indices) <==> x[indices]
#
#        Returns a subspace of the uncompressed array as an independent
#        numpy array.
#
#        .. versionadded:: (cfdm) 1.9.TODO.0
#
#        """
#        raise NotImplementedError(
#            "Must implement __getitem__ in subclasses"
#        )  # pragma: no cover

    def _first_or_last_index(self, indices):
        """Return the first or last element of the uncompressed array.

        This method will return the first or last element without
        having to perform any decompression.

        .. warning:: It is assumed that the first (last) element of
                     the compressed array has the same value as the
                     first (last) element of the uncompressed
                     array. If this is not the case then an incorrect
                     value will be returned.

        First and last elements are only recognised by exact *indices*
        matches to:

        * ``(slice(0, 1, 1),) * self.ndim``
        * ``(slice(-1, None, 1),) * self.ndim``

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `__getitem__`

        :Parameters:

            indices:
                Indices to the uncompressed array.

        :Returns:

            `numpy.ndarray`
                The first or last element. If the *indices* do not
                acceptably select a first or last element then an
                `IndexError` is raised.

        """
        ndim = self.ndim
        for index in (slice(0, 1, 1), slice(-1, None, 1)):
            if indices == (index,) * ndim:
                data = self.source()
                return np.asanyarray(data[(index,) * data.ndim])

        # Indices do not acceptably select the first nor last element
        raise IndexError()

    def _get_compressed_Array(self, default=ValueError()):
        """Return the compressed array.

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the array
                has not been set. If set to an `Exception` instance then
                it will be raised instead.

        :Returns:

                The compressed Array instance.

        **Examples:**

        >>> c = d._get_compressed_Array()

        """
        return self._get_component("compressed_Array", default)

    def _set_compressed_Array(self, array, copy=True):
        """Set the compressed array.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            array: subclass of `cfdm.data.Array`
                The compressed data to be inserted.

        :Returns:

            `None`

        **Examples:**

        >>> d._set_compressed_Array(a)

        """
        if copy:
            array = array.copy()

        self._set_component("compressed_Array", array, copy=False)

    @property
    def array(self):
        """Returns a numpy array containing the uncompressed data.

        :Returns:

            `numpy.ndarray`
                The uncompressed array.

        **Examples:**

        >>> n = a.array
        >>> isinstance(n, numpy.ndarray)
        True

        """
        return self[...]

    @property
    def dtype(self):
        """Data-type of the uncompressed data."""
        raise NotImplementedError(
            "Must implement dtype in subclasses"
        )  # pragma: no cover
    
    @cached_property
    def ndim(self):
        """The number of dimensions of the uncompressed data."""
        return len(self.shape)

    @property
    def shape(self):
        """Shape of the uncompressed data.

        """
        return self._get_component("shape")

    @cached_property
    def size(self):
        """Number of elements in the uncompressed data."""
        return reduce(mul, self.shape, 1)

    @property
    def compressed_array(self):
        """Returns an independent numpy array with the compressed data.

        :Returns:

            `numpy.ndarray`
                The compressed array.

        **Examples:**

        >>> n = a.compressed_array

        >>> isinstance(n, numpy.ndarray)
        True

        """
        ca = self._get_compressed_Array(None)
        if ca is None:
            raise ValueError("There is no underlying compressed array")

        return ca.array

    def get_compressed_axes(self):
        """Return axes that are compressed in the underlying array.

        :Returns:

            `list`
                The compressed axes described by their integer
                positions in the uncompressed array.

        **Examples:**

        >>> c.ndim
        4
        >>> c.compressed_array.ndim
        3
        >>> c.compressed_axes()
        [1, 2]

        """
        return sorted(
            {x for y in self.compressed_dimensions().values() for x in y}
        )

    def get_compressed_dimension(self, default=ValueError()):
        """Returns the compressed dimension's position in the array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_compressed_axes`, `get_compression_type`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                underlying array is not compressed. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `int`
                The position of the compressed dimension in the compressed
                array. If the underlying is not compressed then *default*
                is returned, if provided.

        **Examples:**

        >>> i = d.get_compressed_dimension()

        """
        compressed_dimensions = self.compressed_dimensions()
        if len(compressed_dimensions) > 1:
            raise ValueError(
                "Can't get unique compressed dimension when there "
                f"more than one: {self.compressed_dimensions()}"
            )

        return tuple(compressed_dimensions)[0]

    def compressed_dimensions(self):
        """Mapping of compressed to uncompressed dimensions.

        A dictionary key is a position of a dimension in the
        compressed data, with a value of the positions of the
        corresponding dimensions in the uncompressed data. Compressed
        array dimensions that are not compressed are omitted from the
        mapping.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_compressed_axes`, `get_compression_type`

        :Returns:

            `dict`
                The mapping of dimensions of the compressed array to
                their corresponding dimensions in the uncompressed
                array. Compressed array dimensions that are not
                compressed are omitted from the mapping.

        """
        return self._get_component("compressed_dimensions").copy()

    def conformed_data(self):
        """The compressed data in the form required by the decompression
        algorthm.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `dict`
                The compressed data, with the key ``'data'``.

        """
        return {"data": self.source().copy()}

    def source(self, default=ValueError()):
        """Return the underlying array object.

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the array
                has not been set. If set to an `Exception` instance then
                it will be raised instead.

        :Returns:

            subclass of `Array`
                The underlying array object.

        **Examples:**

        >>> array
        <RaggedContiguousArray(2, 4): >
        >>> array.source()
        <Data(5): [280.0, ..., 279.5]>

        """
        return self._get_compressed_Array(default=default)

    def subarrays(self):
        """Return descriptors for every subarray.

        Theses descriptors are used during subarray decompression.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            sequence of iterables
                Each iterable iterates over a particular descriptor
                from each subarray.

        """
        raise NotImplementedError(
            "Must implement subarrays in subclasses"
        )  # pragma: no cover
    
    def to_memory(self):
        """Bring an array on disk into memory and retain it there.

        There is no change to an array that is already in memory.

        :Returns:

            `{{class}}`
                TODO

        **Examples:**

        >>> a.to_memory()

        """
        self.source().data.to_memory()
