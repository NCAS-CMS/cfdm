import numpy as np


class ArrayMixin:
    """Mixin class for a container of an array.

    .. versionadded:: (cfdm) 1.8.7.0

    """

    def __array__(self, *dtype):
        """The numpy array interface.

        .. versionadded:: (cfdm) 1.8.7.0

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples**

        >>> isinstance(a, Array)
        True
        >>> n = numpy.asanyarray(a)
        >>> isinstance(n, numpy.ndarray)
        True

        """
        array = self.array
        if not dtype:
            return array
        else:
            return array.astype(dtype[0], copy=False)

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed subarray.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed subarray as an
        independent numpy array.

        .. versionadded:: (cfdm) 1.8.7.0

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.__getitem__"
        )  # pragma: no cover

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        .. versionadded:: (cfdm) 1.8.7.0

        """
        return f"<{self.__class__.__name__}{self.shape}: {self}>"

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        .. versionadded:: (cfdm) 1.8.7.0

        """
        return f"shape={self.shape}, dtype={self.dtype}"

    def __docstring_package_depth__(self):
        """Returns the package depth for {{package}} substitutions.

        See `_docstring_package_depth` for details.

        """
        return 0

    def _set_units(self):
        """The units and calendar properties.

        These are the values set during initialisation, defaulting to
        `None` if either was not set at that time.

        .. versionadded:: (cfdm) 1.10.1.0

        :Returns:

            `tuple`
                The units and calendar values, either of which may be
                `None`.

        """
        units = self.get_units(False)
        if units is False:
            self._set_component("units", None, copy=False)

        calendar = self.get_calendar(False)
        if calendar is False:
            self._set_component("calendar", None, copy=False)

        return units, calendar

    def get_calendar(self, default=ValueError()):
        """The calendar of the array.

        If the calendar is `None` then the CF default calendar is
        assumed, if applicable.

        .. versionadded:: (cfdm) 1.10.0.1

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                calendar has not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

            `str` or `None`
                The calendar value.

        """
        calendar = self._get_component("calendar", False)
        if calendar is False:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__} 'calendar' has not been set",
            )

        return calendar

    def get_compression_type(self):
        """Returns the array's compression type.

        Specifically, returns the type of compression that has been
        applied to the underlying array.

        .. versionadded:: (cfdm) 1.8.7.0

        :Returns:

            `str`
                The compression type. An empty string means that no
                compression has been applied.

        **Examples**

        >>> a.compression_type
        ''

        >>> a.compression_type
        'gathered'

        >>> a.compression_type
        'ragged contiguous'

        """
        return self._get_component("compression_type", "")

    @classmethod
    def get_subspace(cls, array, indices, copy=True):
        """Return a subspace, defined by indices, of a numpy array.

        Only certain type of indices are allowed. See the *indices*
        parameter for details.

        Indexing is similar to numpy indexing. Given the restrictions on
        the type of indices allowed - see the *indicies* parameter - the
        only difference to numpy indexing is

          * When two or more dimension's indices are sequences of integers
            then these indices work independently along each dimension
            (similar to the way vector subscripts work in Fortran).

        .. versionadded:: (cfdm) 1.8.7.0

        :Parameters:

            array: `numpy.ndarray`
                The array to be subspaced.

            indices:
                The indices that define the subspace.

                Must be either `Ellipsis` or a sequence that contains an
                index for each dimension. In the latter case, each
                dimension's index must either be a `slice` object or a
                sequence of two or more integers.

                  *Parameter example:*
                    indices=Ellipsis

                  *Parameter example:*
                    indices=[[5, 7, 8]]

                  *Parameter example:*
                    indices=[slice(4, 7)]

                  *Parameter example:*
                    indices=[slice(None), [5, 7, 8]]

                  *Parameter example:*
                    indices=[[2, 5, 6], slice(15, 4, -2), [8, 7, 5]]

            copy: `bool`
                If `False` then the returned subspace may (or may not) be
                independent of the input *array*. By default the returned
                subspace is independent of the input *array*.

        :Returns:

            `numpy.ndarray`

        """
        if indices is not Ellipsis:
            if not isinstance(indices, tuple):
                indices = (indices,)

            axes_with_list_indices = [
                i for i, x in enumerate(indices) if not isinstance(x, slice)
            ]
            n_axes_with_list_indices = len(axes_with_list_indices)

            if n_axes_with_list_indices < 2:
                # ----------------------------------------------------
                # At most one axis has a list-of-integers index so we
                # can do a normal numpy subspace
                # ----------------------------------------------------
                array = array[tuple(indices)]
            else:
                # ----------------------------------------------------
                # At least two axes have list-of-integers indices so
                # we can't do a normal numpy subspace
                # ----------------------------------------------------
                n_indices = len(indices)
                if n_axes_with_list_indices < n_indices:
                    # Apply subspace defined by slices
                    slices = [
                        i if isinstance(i, slice) else slice(None)
                        for i in indices
                    ]
                    array = array[tuple(slices)]

                if n_axes_with_list_indices:
                    # Apply subspaces defined by lists (this
                    # methodology works for both numpy arrays and
                    # scipy sparse arrays).
                    lists = [slice(None)] * n_indices
                    for axis in axes_with_list_indices:
                        lists[axis] = indices[axis]
                        array = array[tuple(lists)]
                        lists[axis] = slice(None)

        if copy:
            if np.ma.isMA(array) and not array.ndim:
                # This is because numpy.ma.copy doesn't work for
                # scalar arrays (at the moment, at least)
                ma_array = np.ma.empty((), dtype=array.dtype)
                ma_array[...] = array
                array = ma_array
            else:
                array = array.copy()

        return array

    def get_units(self, default=ValueError()):
        """The units of the array.

        If the units are `None` then the array has no defined units.

        .. versionadded:: (cfdm) 1.10.0.1

        .. seealso:: `get_calendar`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                units have not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

            `str` or `None`
                The units value.

        """
        units = self._get_component("units", False)
        if units is False:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__} 'units' have not been set",
            )

        return units
