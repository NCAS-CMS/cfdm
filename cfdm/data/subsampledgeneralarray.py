from itertools import product

import numpy as np

from .abstract import CompressedArray


_float64 = np.dtype(float)


class SubsampledGeneralArray(CompressedArray):
    """TODO.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        compressed_axes=None,
        tie_point_indices={},
        interpolation_parameters={},
        parameter_dimensions={},
            interpolation_name="",
        interpolation_description="",
            computational_precision="",
    ):
        """Initialisation.

        :Parameters:

            compressed_array: `Data`
                The tie points array.

            shape: `tuple`
                The uncompressed array dimension sizes.

            size: `int`
                Number of elements in the uncompressed array.

            ndim: `int`
                The number of uncompressed array dimensions.

            compressed_axes: sequence of `int`
                The positions of the compressed axes in the tie points
                array.

                *Parameter example:*
                  ``compressed_axes=[1]``

                *Parameter example:*
                  ``compressed_axes=(1, 2)``

            interpolation_name: `str`, optional
                The interpolation method used to uncompress the
                coordinates values.

                *Parameter example:*
                  ``interpolation_name='linear'``

            interpolation_description: `str`, optional
                A non-standardized description of the interpolation
                method used to uncompress the coordinates values.

            tie_point_indices: `dict`, optional
 
               The tie point index variables cooresponding to the
                compressed dimensions. The set keys must be the same
                as the set of *compressed_axes*.

            interpolation_parameters: `dict`
                TODO

            parameter_dimensions: `dict`
                TODO

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            size=size,
            ndim=ndim,
            compressed_dimension=tuple(sorted(compressed_axes)),
            compression_type="subsampled",
            tie_point_indices=tie_point_indices.copy(),
            interpolation_parameters=interpolation_parameters.copy(),
            parameter_dimensions=parameter_dimensions.copy(),
            interpolation_name=interpolation_name,
            interpolation_description=interpolation_description,
            computational_precision=computational_precision,
        )

    def __getitem__(self, indices):
        """x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the array as an independent numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        try:
            # If the first or last element is requested then we don't
            # need to interpolate
            return self._first_or_last_index(indices)
        except IndexError:
            pass

        raise IndexError("Don't know how to uncompress {self!r}")
        
    def _first_or_last_index(self, indices):
        """Return the first or last element.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        ndim = self.ndim
        if (
                indices == (slice(0, 1),) * ndim or
                indices == (slice(-1, None),) * ndim
        ):
            return self.get_tie_points()[indices]
        
        raise IndexError(
            f"Indices {indices} do not select the first nor last element"
        )
        
    def interpolation_subareas(
        self, non_interpolation_dimension_value=slice(None)
    ):
        """TODO.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            4-`tuple` of iterators
               * The indices of the tie point array that correspond to
                 each interpolation subarea. Each index for the tie
                 point interpolated dimensions is expressed as a list
                 of two integers, rather than a `slice` object, to
                 facilitate retrieval of each tie point individually.

               * The indices of the uncompressed array that correspond
                 to each interpolation subarea. Each index in the
                 tuple is expressed as a `slice` object. 

                 .. note:: If a tie point is shared with a previous
                           interpolation subarea, then that location
                           is excluded from the index.

               * The size of each interpolated subarea along the
                 interpolated dimensions. Each size includes both tie
                 points.

               * Flags which state, for each interpolated dimension,
                 whether each interplation subarea is at the start of
                 a continuous area.

        """
        tie_point_indices = self.get_tie_point_indices()

        non_interpolated_dimension_value = slice(None)

        # ------------------------------------------------------------
        # The indices of the tie point array that correspond to each
        # interpolation subarea.
        #
        # Example: The tie point array has three dimensions and
        #          dimensions 0 and 2 are tie point interpolation
        #          dimensions; intertolated dimenson 2 (size 15) has a
        #          single continuous area divided into has three
        #          equally-sized interpolation subarareas; and
        #          interpolated dimension 0 (size 20) has two
        #          equally-sized continuous areas, each with one
        #          interpolation subarea.
        #
        # Initialization:
        #
        #   [(slice(None),),
        #    (slice(None),),
        #    (slice(None),)]
        #   
        # Overwrite tie point interpolated dimension entries with
        # indices to tie point pairs:
        #   
        #   [[[0, 1], [2, 3]],
        #    (slice(None),),
        #    [[0, 1], [1, 2], [2, 3]]]
        #   
        # Returned cartesian product (one set of indices per
        # interpolation subarea):
        #   
        #   [[0, 1], slice(None), [0, 1]),
        #    [0, 1], slice(None), [1, 2]),
        #    [0, 1], slice(None), [2, 3]),
        #    [2, 3], slice(None), [0, 1]),
        #    [2, 3], slice(None), [1, 2]),
        #    [2, 3], slice(None), [2, 3])]
        # ------------------------------------------------------------
        tp_interpolation_subareas = [
            (non_interpolated_dimension_value,)
        ] * self.ndim

        # ------------------------------------------------------------
        # The indices of the uncompressed array that correspond to
        # each interpolation subarea.
        #
        # .. note:: If a tie point is shared with a previous
        #           interpolation subarea, then that location is
        #           excluded from the index.
        #
        # Example: The tie point array has three dimensions and
        #          dimensions 0 and 2 are tie point interpolation
        #          dimensions; intertolated dimenson 2 (size 15) has a
        #          single continuous area divided into has three
        #          equally-sized interpolation subarareas(sizes 5, 6,
        #          and 6); and interpolated dimension 0 (size 20) has
        #          two equally-sized continuous areas, each with one
        #          interpolation subarea.
        #
        # Initialization:
        #
        #   [(slice(None),),
        #    (slice(None),),
        #    (slice(None),)]
        #
        # Overwrite interpolated dimension entries with indices to tie
        # point pairs:
        #
        #   [[slice(0, 10), slice(10, 20)],
        #    (slice(None),),
        #    [slice(0, 5), slice(5, 10), slice(10, 15)]]
        #
        # Returned cartesian product (one set of indices per
        # interpolation subarea):
        #
        #   [(slice(0, 10),  slice(None), slice(0, 5)  ),
        #    (slice(0, 10),  slice(None), slice(5, 10) ),
        #    (slice(0, 10),  slice(None), slice(10, 15)),
        #    (slice(10, 20), slice(None), slice(0, 5)  ),
        #    (slice(10, 20), slice(None), slice(5, 10) ),
        #    (slice(10, 20), slice(None), slice(10, 15))]
        # ------------------------------------------------------------
        u_interpolation_subareas = tp_indices[:]

        # ------------------------------------------------------------
        # The size of each interpolated subarea along the interpolated
        # dimensions. Each size includes both tie points.
        #
        # Example: The tie point array has three dimensions and
        #          dimensions 0 and 2 are tie point interpolation
        #          dimensions; intertolated dimenson 2 (size 15) has a
        #          single continuous area divided into has three
        #          equally-sized interpolation subarareas(sizes 5, 6,
        #          and 6); and interpolated dimension 0 (size 20) has
        #          two equally-sized continuous areas, each with one
        #          interpolation subarea.
        #
        # Initialization:
        #
        #   [(None,),
        #    (None,),
        #    (None,)]
        #
        # Overwrite interpolated dimension entries with interpolation
        # subarea sizes: point pairs:
        #
        #   [[10, 10],
        #    (None,),
        #    [5, 6, 6]]
        #
        # Returned cartesian product (one set of sizes per
        # interpolation subarea):
        #
        #   [(10, None, 5),
        #    (10, None, 6),
        #    (10, None, 6),
        #    (10, None, 5),
        #    (10, None, 6),
        #    (10, None, 6)]
        # ------------------------------------------------------------
        interpolation_subarea_sizes =  [(None,)] * self.ndim

        # ------------------------------------------------------------
        # Initialise the boolean flags which state, for each
        # interpolated dimension, whether each interplation subarea
        # is at the start of a continuous area, moving from left to
        # right in index space. Non-interpolated dimensions are given
        # the flag `None`.
        #
        # Example: The tie point array has three dimensions and
        #          dimensions 0 and 2 are tie point interpolation
        #          dimensions; intertolated dimenson 2 (size 15) has a
        #          single continuous area divided into has three
        #          equally-sized interpolation subarareas; and
        #          interpolated dimension 0 (size 20) has two
        #          equally-sized continuous areas, each with one
        #          interpolation subarea.
        #
        # Initialization:
        #
        #   [(None,),
        #    (None,),
        #    (None,)]
        #
        # Overwrite interpolated dimension entries with flags for
        # each interpolation subarea:
        #
        #  [[True, True],
        #   (None,),
        #   [True, False, False]]
        #
        # Returned cartesian product (one set of flags per
        # interpolation suabarea):
        #
        #   [(True, None, True),
        #    (True, None, False),
        #    (True, None, False),
        #    (True, None, True),
        #    (True, None, False),
        #    (True, None, False)]
        # ------------------------------------------------------------
        new_continuous_area = interpolation_subarea_sizes[:]

        for d in self.get_compressed_axes():
            tp_index = []
            u_index = []
            new_continuous_area = []
            subarea_size = []
            
            tie_point_indices = tie_point_indices[d].array.flatten().tolist()

            new = True

            for i, (index0, index1) in enumerate(
                zip(tie_point_indices[:-1], tie_point_indices[1:])
            ):
                new_continuous_area.append(new)

                if index1 - index0 <= 1:
                    new = True
                    new_continuous_area.pop()
                    continue

                # The subspace for the axis of the tie points that
                # corresponds to this axis of the interpolation
                # subarea
                tp_index.append([i, i + 1])

                # The size of the interpolation subarea along this
                # interpolated dimension
                subarea_size.append(index1 - index0 + 1)
                
                # The subspace for this axis of the uncompressed array
                # that corresponds to the interpolation suabrea, only
                # including the first tie point if this the first
                # interpolation subarea in a new continuous area.
                if not new:
                    index0 += 1

                u_index.append(slice(index0, index1 + 1))

                new = False

            tp_interpolation_subareas[d] = tp_index
            u_interpolation_subareas[d] = u_index
            interpolation_subarea_sizes[d] = subarea_size
            new_continuous_area[d] = new_area
            
        return (
            product(*tp_interpolation_subareas),
            product(*u_interpolation_subareas),
            product(*interpolation_subarea_sizes),
            product(*new_continuous_area),
        )

    @lru_cache(maxsize=32)
    def _s(self, d, size):
        """Create the interpolation coefficients ``s`` and ``1-s``.

        The interpolation coefficients for the specified dimension of
        an interpolation subarea with the given size, as per CF
        appendix J.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            d: `int`
                The position of a subsampled dimension in the tie
                point array.

            size: `int`
                The number of uncompressed points along the
                interpolated dimension in the interpolation subarea
                (including both tie points).

        :Returns:

            `numpy.ndarray`, `numpy.ndarray`
                The interpolation coefficents ``s`` and ``1 - s``, in
                that order, each of which is a numpy array in the
                range [0.0, 1.0]. The numpy arrays will have extra
                size 1 dimensions corresponding to all tie point array
                dimensions other than *d*.

        **Examples:**

        >>> x.ndim
        >>> 2
        >>> x._s(1, 6)
        (array([[0. , 0.2, 0.4, 0.6, 0.8, 1. ]]),
         array([[1. , 0.8, 0.6, 0.4, 0.2, 0. ]]))
 
        """
        s = np.linspace(0, 1, size)

        one_minus_s = s[::-1]

        ndim = self.ndim
        if ndim > 1:
            new_shape = [1] * ndim
            new_shape[d] = s.size
            s = s.reshape(new_shape)
            one_minus_s = one_minus_s.reshape(new_shape)
            
        return (s, one_minus_s)

    @property
    def dtype(self):
        """Data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return _float64

    @property
    def interpolation_name(self):
        """The interpolation method."""
        return self._get_component("interpolation_name")

    @property
    def interpolation_description(self):
        """Non-standardized description of the interpolation method."""
        return self._get_component("interpolation_description")

    def conform_interpolation_parameters(self):
        """Conform the interpolation parameters in-place.

        Tranposes the interpolation parameters, if any, to have the
        same relative dimension order as the tie point array, and
        inserts any missing dimensions as size 1 axes.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `None`

        """
        parameters = self.get_interpolation_parameters()
        if not parameters:
            return

        parameter_dimensions = self.get_parameter_dimensions()

        dims = tuple(range(self.ndim))
        for term, c in parameters.items():
            dimensions = parameter_dimensions[term]
            if dimensions == tuple(sorted(dimensions)):
                # Interpolation parameter dimensions are already in
                # the correct order
                continue

            new_order = [dimensions.index(i) for i in dims if i in dimensions]
            c = c.tranpose(new_order)

            # Add non-interpolated dimensions as size 1 axes, if
            # they're not already there.
            if len(dimensions) < self.ndim:
                for d in sorted(set(dims).difference(dimensions)):
                    c = c.insert_dimension(position=d)

            parameters[term] = c
            parameter_dimensions[term] = dims
    
    def get_interpolation_parameters(self):
        """Return the interpolation parameter variables for sampled
        dimensions.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_parameter_dimensions`

        :Returns:

            `dict`

        """
        return self._get_component("interpolation_parameters")

    def get_parameter_dimensions(self):
        """TODO.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_interpolation_parameters`

        :Returns:

            `dict`

        """
        return self._get_component("parameter_dimensions")

    def get_tie_point_indices(self, default=ValueError()):
        """Return the tie point index variables for sampled dimensions.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            default: optional
                Return the value of the *default* parameter if tie point
                index variables have not been set.

                {{default Exception}}

        :Returns:

            `tuple` of `TiePointIndex`
                The tie point index variables.

        **Examples:**

        >>> c = d.get_tie_point_indices()

        """
        return self._get_component("tie_point_indices")

    def get_tie_points(self, default=ValueError()):
        """Return the tie points data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            default: optional
                Return the value of the *default* parameter if tie point
                variables have not been set.

                {{default Exception}}

        :Returns:

            `TiePoint`
                The tie point variable.

        **Examples:**

        >>> c = d.get_tie_points()

        """
        try:
            return self._get_compressed_Array()
        except ValueError:
            return self._default(
                default, f"{self.__class__.__name__} has no tie points"
            )

    def get_compressed_axes(self):
        """Return axes that are compressed in the underlying array.

        :Returns:

            `list`
                The compressed axes described by their integer
                positions in the uncompressed array.

        **Examples:**

        >>> c.get_compressed_dimension()
        (1, 3)
        >>> c.compressed_axes()
        [1, 3)

        """
       return list(self.get_compressed_dimension())

    def to_memory(self):
        """Bring an array on disk into memory.

        There is no change to an array that is already in memory.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `{{class}}`
                The array that is stored in memory.

        **Examples:**

        >>> b = a.to_memory()

        """
        for v in self.get_tie_points():
            v.data.to_memory()

        for v in self.get_tie_point_indices().values():
            v.data.to_memory()

        for v in self.get_interpolation_parameters.values():
            v.data.to_memory()

        return self

#    def tranpose(self, axes):
#        """TODO."""
#        # Tranpose the compressed array
#        compressed_array = self.source().tranpose(axes=axes)
#
#        # Transpose the shape
#        old_shape = self.shape
#        shape = tuple([old_shape.index(i) for n in axes])
#
#        # Change the compressed dimensions
#        compressed_dimensions = sorted(
#            [
#                axes.index(i)
#                for i in self._get_component("compressed_dimension")
#            ]
#        )
#
#        # Change the tie point index dimensions
#        tie_point_indices = {
#            axes.index(i): v for i, v in self.tie_point_indices.items()
#        }
#
#        # Change the interpolation parameter dimensions
#        parameter_dimensions = {
#            term: tuple([axes.index(i) for i in v])
#            for term, v in self.parameter_dimensions.items()
#        }
#
#        return type(self)(
#            compressed_array=compressed_array,
#            shape=shape,
#            ndim=self.ndim,
#            size=self.size,
#            compressed_dimensions=compressed_dimensions,
#            interpolation_name=self.interpolation_name,
#            interpolation_description=self.interpolation_description,
#            tie_point_indices=tie_point_indices,
#            interpolation_parameters=self.get_interpolation_parameters(),
#            parameter_dimensions=parameter_dimensions,
#        )
