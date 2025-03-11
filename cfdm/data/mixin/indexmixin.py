from numbers import Integral

import numpy as np
from dask.array.slicing import normalize_index
from dask.base import is_dask_collection

from ...functions import indices_shape, parse_indices


class IndexMixin:
    """Mixin class for lazy indexing of a data array.

    A data for a subspace is retrieved by casting the object as a
    `numpy` array. See `__getitem__` for more details.

    **Examples**

    >>> a = {{package}}.{{class}}(...)
    >>> a.shape
    (6, 5)
    >>> print(np.asanyarray(a)
    [[ 0  1  2  3  4])
     [ 5  6  7  8  9]
     [10 11 12 13 14]
     [15 16 17 18 19]
     [20 21 22 23 24]
     [25 26 27 28 29]]
    >>> a = a[::2, [1, 2, 4]]
    >>> a = a[[True, False, True], :]
    >>> a.shape
    (2, 3)
    >>> print(np.asanyarray(a))
    [[ 1,  2,  4],
     [21, 22, 24]]

    .. versionadded:: (cfdm) 1.11.2.0

    """

    def __array__(self, dtype=None, copy=None):
        """Convert the `{{class}}` into a `numpy` array.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            dtype: optional
                Typecode or data-type to which the array is cast.

            copy: `None` or `bool`
                Included to match the v2 `numpy.ndarray.__array__`
                API, but ignored. The return numpy array is always
                independent.

                .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `numpy.ndarray`
                An independent `numpy` array of the subspace of the
                data defined by the `indices` attribute.

        """
        array = self._get_array()
        if dtype is None:
            return array

        return array.astype(dtype, copy=False)

    def __getitem__(self, index):
        """Returns a subspace of the data as a new `{{class}}`.

        x.__getitem__(indices) <==> x[indices]

        Subspaces created by indexing are lazy and are not applied
        until the `{{class}}` object is converted to a `numpy` array,
        by which time all lazily-defined subspaces will have been
        converted to a single combined index which defines only the
        actual elements that need to be retrieved from the original
        data.

        The combined index is orthogonal, meaning that the index for
        each dimension is to be applied independently, regardless of
        how that index was defined. For instance, the indices ``[[0,
        1], [1, 3], 0]`` and ``[:2, 1::2, 0]`` will give identical
        results.

        For example, if the original data has shape ``(12, 145, 192)``
        and consecutive subspaces of ``[::2, [1, 3, 4], 96:]`` and
        ``[[0, 5], [True, False, True], 0]`` are applied, then only
        the elements defined by the combined index``[[0, 10], [1, 4],
        96]`` will be retrieved from the data when `__array__` is
        called.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `index`, `original_shape`, `__array__`,
                     `__getitem__`

        :Returns:

            `{{class}}`
                The subspaced data.

        """
        shape0 = self.shape
        index0 = self.index(conform=False)
        reference_shape = list(self.reference_shape)

        index1 = parse_indices(shape0, index, keepdims=False, newaxis=True)

        new = self.copy()
        new_indices = []
        new_shape = []

        newaxis = np.newaxis
        if len(index1) > len(index0):
            # Take new axes out of 'index1' for now. We'll put them
            # back later.
            none_positions = [
                i for i, ind1 in enumerate(index1) if ind1 is newaxis
            ]
            index1 = [ind1 for ind1 in index1 if ind1 is not newaxis]
        else:
            none_positions = []

        i = 0
        j = 0
        for ind0, reference_size in zip(index0, reference_shape[:]):
            if isinstance(ind0, Integral):
                # The previous call to __getitem__ resulted in a
                # dimension being removed (i.e. 'ind0' is
                # integer-valued). Therefore 'index1' must have fewer
                # elements than 'index0', so we need to "carry
                # forward" the integer-valued index so that it is
                # available at evaluation time.
                new_indices.append(ind0)
                continue

            ind1 = index1[i]
            size0 = shape0[i]

            i += 1
            if ind0 is newaxis:
                if isinstance(ind1, Integral):
                    # A previously introduced new axis is being
                    # removed by an integer index
                    if ind1 not in (0, -1):
                        raise IndexError(
                            f"index {ind1} is out of bounds for axis {i - 1} "
                            "with size 1"
                        )

                    reference_shape.pop(i - 1 - j)
                    j += 1
                else:
                    new_indices.append(ind0)

                continue

            # If this dimension is not subspaced by the new index then
            # we don't need to update the old index.
            if isinstance(ind1, slice) and ind1 == slice(None):
                new_indices.append(ind0)
                continue

            # Still here? Then we have to work out the index of the
            #             full array that is equivalent to applying
            #             'ind0' followed by 'ind1'.
            if is_dask_collection(ind1):
                # Note: This will never occur when this __getitem__ is
                #       being called from within a Dask graph, because
                #       any lazy indices will have already been
                #       computed as part of the whole graph execution;
                #       i.e. we don't have to worry about a
                #       compute-within-a-compute situation. (If this
                #       were not the case then we could add
                #       `scheduler="synchronous"` to the compute
                #       call.)
                ind1 = ind1.compute()

            if isinstance(ind0, slice):
                if isinstance(ind1, slice):
                    # ind0: slice
                    # ind1: slice
                    start, stop, step = ind0.indices(reference_size)
                    start1, stop1, step1 = ind1.indices(size0)
                    size1, mod1 = divmod(stop1 - start1, step1)

                    if mod1 != 0:
                        size1 += 1

                    start += start1 * step
                    step *= step1
                    stop = start + (size1 - 1) * step

                    if step > 0:
                        stop += 1
                    else:
                        stop -= 1

                    if stop < 0:
                        stop = None

                    new_index = slice(start, stop, step)
                else:
                    # ind0: slice
                    # ind1: int, or array of int/bool
                    new_index = np.arange(*ind0.indices(reference_size))[ind1]
            else:
                # ind0: array of int. If we made it to here then it
                #                     can't be anything else. This is
                #                     because we've dealt with ind0
                #                     being a slice or an int, the
                #                     very first ind0 is always
                #                     slice(None), and a previous ind1
                #                     that was an array of bool will
                #                     have resulted in this ind0 being
                #                     an array of int.
                #
                # ind1: anything
                new_index = np.asanyarray(ind0)[ind1]

            new_indices.append(new_index)

        if none_positions:
            for i in none_positions:
                new_indices.insert(i, newaxis)
                reference_shape.insert(i, 1)

        new._custom["index"] = tuple(new_indices)
        new._custom["reference_shape"] = tuple(reference_shape)

        # Find the shape defined by the new index
        new_shape = indices_shape(new_indices, reference_shape, keepdims=False)
        new._set_component("shape", tuple(new_shape), copy=False)

        return new

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        """
        return (
            f"<CF {self.__class__.__name__}{self.shape}: "
            f"{self}{self.original_shape}>"
        )

    @property
    def __in_memory__(self):
        """True if the array data is in memory.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `False`

        """
        return False

    def _get_array(self, index=None):
        """Returns a subspace of the dataset variable.

        The subspace is defined by the `index` attributes, and is
        applied with `cfdm.netcdf_indexer`.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `__array__`, `index`

        :Parameters:

            {{index: `tuple` or `None`, optional}}

        :Returns:

            `numpy.ndarray`
                The subspace.

        """
        return NotImplementedError(
            f"Must implement {self.__class__.__name__}._get_array"
        )

    @property
    def array(self):
        """Return an independent numpy array containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples**

        >>> n = numpy.asanyarray(a)
        >>> isinstance(n, numpy.ndarray)
        True

        """
        return self.__array__()

    def index(self, conform=True):
        """The index to be applied when converting to a `numpy` array.

        The `shape` is defined by the `index` applied to the
        `original_shape`.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `shape`, `original_shape`, `reference_shape`

        :Parameters:

            conform: `bool`, optional
                If True, the default, then

                * Convert a decreasing size 1 slice to an increasing
                  one.

                * Convert, where possible, a sequence of integers to a
                  slice.

                These transformations are to allow subspacing on data
                objects that have restricted indexing functionality,
                such as `h5py.Variable` objects.

                If False then these transformations are not done.

        :Returns:

            `tuple`

        **Examples**

        >>> x.shape
        (12, 145, 192)
        >>> x.index()
        (slice(None), slice(None), slice(None))
        >>> x = x[8:7:-1, 10:19:3, [15, 1,  4, 12]]
        >>> x = x[[0], [True, False, True], ::-2]
        >>> x.shape
        (1, 2, 2)
        >>> x.index()
        (slice(8, 9, None), slice(10, 17, 6), slice(12, -1, -11))
        >>> x.index(conform=False)
        (array([8]), array([10, 16]), array([12,  1]))

        """
        ind = self._custom.get("index")
        if ind is None:
            # No indices have been applied yet, so define indices that
            # are equivalent to Ellipsis, and set the original shape.
            shape = self.shape
            ind = tuple([slice(0, n, 1) for n in shape])
            self._custom["index"] = ind
            self._custom["original_shape"] = shape
            self._custom["reference_shape"] = shape
            return ind

        if not conform:
            return ind

        # Still here? Then conform the indices by:
        #
        # 1) Converting decreasing size 1 slices to increasing
        #    ones. This helps when the parent class can't cope with
        #    decreasing slices.
        #
        # 2) Converting, where possible, sequences of integers to
        #    slices. This helps when the parent class can't cope with
        #    indices that are sequences of integers.
        ind = list(ind)
        for n, (i, size) in enumerate(zip(ind[:], self.original_shape)):
            if isinstance(i, slice):
                if size == 1:
                    start, _, step = i.indices(size)
                    if step and step < 0:
                        # Decreasing slices are not universally
                        # accepted (e.g. `h5py` doesn't like them),
                        # but we can convert them to increasing ones.
                        ind[n] = slice(start, start + 1)
            elif np.iterable(i):
                i = normalize_index((i,), (size,))[0]
                if i.size == 1:
                    # Convert a sequence of one integer into a slice
                    start = i.item()
                    ind[n] = slice(start, start + 1)
                else:
                    # Convert a sequence of two or more evenly spaced
                    # integers into a slice.
                    step = np.unique(np.diff(i))
                    if step.size == 1:
                        start, stop = i[[0, -1]]
                        if stop >= start:
                            stop += 1
                        elif stop:
                            stop = -1
                        else:
                            stop = None

                        ind[n] = slice(start, stop, step.item())

        return tuple(ind)

    @property
    def reference_shape(self):
        """The shape of the data in the file with added dimensions.

        This is the same as `original_shape`, but with added size 1
        dimensions if `index` has new dimensions added with index
        values of `numpy.newaxis`.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `index`, `shape`, `original_shape`

        """
        out = self._custom.get("reference_shape")
        if out is None:
            # No subspace has been defined yet
            out = self.original_shape
            self._custom["reference_shape"] = out

        return out

    @property
    def original_shape(self):
        """The shape of the data in the file.

        The `shape` is defined by the result of subspacing the data in
        its original shape with the indices given by `index`.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `index`, `shape`, `reference_shape`

        """
        out = self._custom.get("original_shape")
        if out is None:
            # No subspace has been defined yet
            out = self.shape
            self._custom["original_shape"] = out

        return out

    def is_subspace(self):
        """True if the index represents a subspace of the data.

        The presence of `numpy.newaxis` (i.e. added size 1 dimensions)
        in `index` will not, on their own, cause `is_subspace` to
        return `False`

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `index`, `shape`

        """
        newaxis = np.newaxis
        index = [ind for ind in self.index() if ind is not newaxis]
        return index != [slice(0, n, 1) for n in self.original_shape]
