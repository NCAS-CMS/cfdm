from ..decorators import _inplace_enabled, _inplace_enabled_define_and_cleanup


class Topology:
    """Mixin class for topology-related constructs.

    .. versionadded:: (cfdm) 1.11.0.0

    """

    @classmethod
    def _normalise_cell_ids(cls, data, start_index, remove_empty_columns):
        """Normalise cell identifier values.

        Normalised data is in a form that is suitable for creating a
        CF-netCDF UGRID connectivity variable.

        The first column of the input data defines the unique
        identifier for each cell.

        See `normalise` for further details.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `normalise`

        :Parameters:

            data: `numpy.ndarray`
                The original numpy array of cell identifiers.

            start_index: `int`
                The start index for the data values in the normalised
                data. Must be ``0`` or ``1`` for zero- or one-based
                indices respectively.

            remove_empty_columns: `bool`
                If True then remove any array columns that are
                entirely missing data.

        :Returns:

            `numpy.ndarray`
                The normalised data.

        **Examples*

        See `normalise` for examples.

        """
        import numpy as np

        # Extract the IDs from column 0 (the unique cell IDs)
        col0_ids = data[:, 0]
        n_cells = col0_ids.size
        id_min = col0_ids.min()
        id_max = col0_ids.max()

        # Check for the simple case: The IDs in column 0 form a
        # contiguous set of unique integers, and there are no dangling
        # references in columns 1:N
        is_contiguous_and_bounded = (
            (id_max - id_min + 1 == n_cells)
            and (data.min() >= id_min)
            and (data.max() <= id_max)
            and (len(np.unique(col0_ids)) == n_cells)
        )

        if is_contiguous_and_bounded:
            # We have the simple case: Simply shift the IDs up or down
            # to match the 'start_index'
            del col0_ids
            if id_min != start_index:
                data -= id_min - start_index

            if remove_empty_columns:
                data = cls._remove_empty_columns(data)

            return data

        # Still here? Then we don't have the simple case ...
        is_masked = np.ma.is_masked(data)
        if is_masked:
            unmasked_buf = data.data
        else:
            unmasked_buf = data

        # Map by row order of column 0
        sorter = np.argsort(col0_ids)
        sorted_col0 = col0_ids[sorter]
        del col0_ids

        # Row position in column 0 is the target index: row 0 ->
        # start_index, row 1 -> start_index + 1, ...
        #
        # sorter[i] is the row index where sorted_col0[i] originated.
        sorted_targets = sorter + start_index
        del sorter

        # Search against unmasked_buf
        idx = np.searchsorted(sorted_col0, unmasked_buf)
        idx_clamped = np.minimum(idx, n_cells - 1)

        # Validate matches against original values
        valid_matches = (idx < n_cells) & (
            sorted_col0[idx_clamped] == unmasked_buf
        )
        del idx, sorted_col0
        if is_masked:
            valid_matches &= ~data.mask

        # Combine pre-existing masks with newly found dangling
        # references
        if is_masked:
            full_mask = data.mask | ~valid_matches
        else:
            full_mask = ~valid_matches

        has_new_dangling = np.any(
            ~valid_matches & (~data.mask if is_masked else True)
        )

        # Compute mapped output into a clean buffer
        mapped_data = np.zeros_like(unmasked_buf)
        del unmasked_buf
        mapped_data[valid_matches] = sorted_targets[idx_clamped[valid_matches]]
        del sorted_targets, idx_clamped, valid_matches

        # Construct final masked array
        data = np.ma.masked_array(mapped_data, mask=full_mask)
        del mapped_data, full_mask

        # Sort columns 1: to push any newly created masked elements to
        # the right-hand end
        if has_new_dangling:
            data[:, 1:] = np.ma.sort(data[:, 1:], axis=1)

        if remove_empty_columns:
            data = cls._remove_empty_columns(data)

        return data

    @classmethod
    def _remove_empty_columns(cls, data):
        """Remove any data columns that are entirely missing data.

        It is assumed that any such columns will be at the end of the
        dimension.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `_normalise_cell_ids`, `normalise`

        :Parameters:

            data: `numpy.ndarray`
                The data.

        :Returns:

            `numpy.ndarray`
                The normalised data.

        """
        import numpy as np

        if np.ma.is_masked(data):
            count = data.count(axis=0)
            # Only slice if the very last column is empty
            if count[-1] == 0:
                # Find the last non-empty column
                last_valid = np.flatnonzero(count)[-1]
                data = data[:, : last_valid + 1]

        return data

    @_inplace_enabled(default=False)
    def transpose(self, axes=None, inplace=False):
        """Permute the axes of the data array.

        In this context, the data only has one axis, the first
        one. The second data dimension can not be moved and may not be
        specified. Therefore, the `transpose` method never changes the
        data.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `insert_dimension`, `squeeze`

        :Parameters:

            axes: (sequence of) `int`, optional
                The new axis order. By default the order is reversed.

                {{axes int examples}}

            {{inplace: `bool`, optional}}

        :Returns:

            `{{class}}` or `None`
                The new construct with permuted data axes. If the
                operation was in-place then `None` is returned.

        """
        if axes is None:
            iaxes = list(range(self.ndim - 1, -1, -1))
        else:
            iaxes = self._parse_axes(axes)

        if iaxes != [0]:
            raise ValueError(
                f"Can't transpose {self.__class__.__name__} with axes "
                f"of {axes!r}. Axes must be equivalent to [0]"
            )

        c = _inplace_enabled_define_and_cleanup(self)
        super(Topology, c).transpose(iaxes + [-1], inplace=True)
        return c
