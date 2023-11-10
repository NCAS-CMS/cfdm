from ..decorators import _inplace_enabled, _inplace_enabled_define_and_cleanup


class Topology:
    """Mixin class for topology-related constructs.

    .. versionadded:: (cfdm) UGRIDVER

    """

    @classmethod
    def _normalise_cell_ids(cls, data, start_index, remove_empty_columns):
        """Normalise cell identifier values.

        Normalised data is in a form that is suitable for creating a
        CF-netCDF UGRID connectivity variable.

        The first column of the input data defines the unique
        identifier for each cell.

        See `normalise` for further details.

        .. versionadded:: (cfdm) UGRIDVER

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

        masked = np.ma.is_masked(data)
        if masked:
            mask = data.mask

        # Get the original cell ids
        ids = data[:, 0]
        id0 = ids[0]
        n_cells = ids.size
        relabel = not (
            (not id0 and (ids == np.arange(n_cells)).all())
            or (id0 == 1 and (ids == np.arange(1, n_cells + 1)).all())
        )

        if not relabel:
            # The cell ids are already correct (barring a possible
            # 'start_index' offset).
            if start_index and not id0:
                data += 1
            elif not start_index and id0 == 1:
                data -= 1

            smallest_id = data[0, 0]
            largest_id = data[-1, 0]
        else:
            # Remove negative values
            #
            # PERFORMANCE WARNING: A potentially slow loop
            smallest_id = None
            dmin = data.min()
            if dmin < 0:
                data -= dmin
                ids = data[:, 0]

            # Replace the non-negative cell ids (i) with negative
            # numbers (j)
            copyto = np.copyto
            for i, j in zip(ids.tolist(), range(-n_cells, 0)):
                copyto(data, j, where=data == i)

            if masked:
                # Re-mask the data, since np.copyto is not mask-aware.
                data = np.ma.array(data, mask=mask)

            largest_id = -1

        # Remove redundant cell ids. These may occur when a previous
        # indexing operation removed cells.
        move_missing_values = False
        if data.max() > largest_id:
            data = np.ma.where(data > largest_id, np.ma.masked, data)
            move_missing_values = True

        if smallest_id is not None and data.min() < smallest_id:
            data = np.ma.where(data < smallest_id, np.ma.masked, data)
            move_missing_values = True

        if move_missing_values:
            # Move missing values to the end of each row
            data[:, 1:].sort(axis=1, endwith=True)

        if remove_empty_columns:
            # Discard columns that are all missing data
            data = cls._remove_empty_columns(data)

        if relabel:
            # Convert the negative ids to non-negative numbers
            if start_index:
                data += n_cells + 1
            else:
                data += n_cells

        return data

    @classmethod
    def _remove_empty_columns(cls, data):
        """Remove any data columns that are entirely missing data.

        It is assumed that any such columns will be a the end of the
        dimension.

        .. versionadded:: (cfdm) UGRIDVER

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
            if not count.min():
                index = np.where(count)[0]
                data = data[:, index[0] : index[-1] + 1]

        return data

    @_inplace_enabled(default=False)
    def transpose(self, axes=None, inplace=False):
        """Permute the axes of the data array.

        In this context, the data only has one axis, the first
        one. The second data dimension can not be moved and may not be
        specified. Therefore, the `transpose` method never changes the
        data.

        .. versionadded:: (cfdm) UGRIDVER

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
