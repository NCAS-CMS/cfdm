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

            computational_precision: `str`, optional
                The floating-point arithmetic precision used during
                the preparation and validation of the compressed
                coordinates.

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
        """Return the first or last element of tie points array

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
        
    def _select_tie_points(self, tie_points, tp_indices, location={}):
        """Select tie points from a given interpolation subarea location.

        .. versionadded:: (cfdm) 1.9.TODO.0
        
        .. seealso:: `get_tie_points`
    
        :Parameters:

            tie_points: array_like
               The full tie points array.

            tp_indices: `tuple` of `slice`
                The index of the *tie_points* array that defines the
                tie points for the interpolation subarea.

            location: `dict`, optional
                Identify the tie point location. Each key is an
                integer that specifies a dimension position, with a
                value of ``0`` or ``1`` that indicates ones of the two
                tie points along that dimension. If location is an
                empty dictionary (the default), then all tie points
                for the interpolation subarea are returned.

        :Returns:
 
            `numpy.ndarray`
                The selected tie points.

        """
        tp_indices = list(tp_indices)
        for dim, position in location.items():
            tpi0 = tp_indices[dim].start + position
            tp_indices[dim] = slice(tpi0, tpi0 + 1)
        
        return tie_points[tuple(tp_indices)].array
        
    def interpolation_subareas(self):
        """TODO.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            5-`tuple` of iterators
               * The indices of the uncompressed array that correspond
                 to each interpolation subarea. Each index in the
                 tuple is expressed as a `slice` object. 

                 .. note:: If a tie point is shared with a previous
                           interpolation subarea, then that location
                           is excluded from the index, thereby
                           avoiding any overlaps between indices.

               * The indices of the tie point array that correspond to
                 each interpolation subarea. Each index for the tie
                 point interpolated dimensions is expressed as a list
                 of two integers, rather than a `slice` object, to
                 facilitate retrieval of each tie point individually.

               * The shape of each interpolation subarea, included all
                 tie points. Non-interpolated dimensions have a size
                 of `None`.

               * Flags which state, for each interpolated dimension,
                 whether each interplation subarea is at the start of
                 a continuous area.

               * The index of each interpolation subarea along the
                 interpolation subarea dimensions.

        **Examples** 

        A 3-d array with shape (20, 12, 15) has been compressed with
        dimensions 0 and 2 being interpolated dimensions. Interpolated
        dimension 0 (size 20) has two equally-sized continuous areas,
        each with one interpolation subarea of size 10; and
        intertolated dimenson 2 (size 15) has a single continuous area
        divided into has three interpolation subarareas of szes 5, 6,
        and 6.

        >>> (u_indices,
        ...  tp_indices,
        ...  interpolation_subarea_shapes,
        ...  new_continuous_area,
        ...  interpolation_subarea_indices) = x.interpolation_subareas()

        >>> for i in u_indices:
        ...    print(i)
        ...
        (slice(0, 10, None), slice(None, None, None), slice(0, 5, None))
        (slice(0, 10, None), slice(None, None, None), slice(5, 10, None))
        (slice(0, 10, None), slice(None, None, None), slice(10, 15, None))
        (slice(10, 20, None), slice(None, None, None), slice(0, 5, None))
        (slice(10, 20, None), slice(None, None, None), slice(5, 10, None))
        (slice(10, 20, None), slice(None, None, None), slice(10, 15, None))
             
        >>> for i in tp_indices,
        ...    print(i)
        ...
        (slice(0, 2, None), slice(None, None, None), slice(0, 2, None))
        (slice(0, 2, None), slice(None, None, None), slice(1, 3, None))
        (slice(0, 2, None), slice(None, None, None), slice(2, 4, None))
        (slice(2, 4, None), slice(None, None, None), slice(0, 2, None))
        (slice(2, 4, None), slice(None, None, None), slice(1, 3, None))
        (slice(2, 4, None), slice(None, None, None), slice(2, 4, None))

        >>> for i in interpolation_subarea_shapes:
        ...    print(i)
        ...
        (10, 12, 5)
        (10, 12, 6)
        (10, 12, 6)
        (10, 12, 5)
        (10, 12, 6)
        (10, 12, 6)

        >>> for i in new_continuous_area:
        ...    print(i)
        ...
        (True, None, True)
        (True, None, False)
        (True, None, False)
        (True, None, True)
        (True, None, False)
        (True, None, False)
 
        >>> for i in interpolation_subarea_indices:
        ...    print(i)
        ...       
        (slice(0, 1, None), slice(None, None, None), slice(0, 1, None)
        (slice(0, 1, None), slice(None, None, None), slice(1, 2, None)
        (slice(0, 1, None), slice(None, None, None), slice(2, 3, None)
        (slice(1, 2, None), slice(None, None, None), slice(0, 1, None)
        (slice(1, 2, None), slice(None, None, None), slice(1, 2, None)
        (slice(1, 2, None), slice(None, None, None), slice(2, 3, None)

        """
        tie_point_indices = self.get_tie_point_indices()

        ndim = self.ndim

        # The indices of the uncompressed array that correspond to
        # each interpolation subarea.
        #
        # .. note:: If a tie point is shared with a previous
        #           interpolation subarea, then that location is
        #           excluded from the index, thereby avoiding any
        #           overlaps between indices.
        u_indices = [(slice(None),)] * ndim

        # The indices of the tie point array that correspond to each
        # interpolation subarea.
        tp_indices = [(slice(None),)] * ndim

        # The shape of each interpolated subarea along the
        # interpolated dimensions, including all tie points.
        interpolation_subarea_shapes = list(self.shape)

        # The flags which state, for each dimension, whether (`True`)
        # or not (`False`) an interplation subarea is at the start of
        # a continuous area. Non-interpolated dimensions are given the
        # flag `None`.
        new_continuous_area = [(None,)] * ndim

        # The index of each interpolation subarea along the
        # interpolation subarea dimensions
        interpolation_subarea_indices = [(slice(None),)] * ndim
     
        for d in self.get_compressed_axes():
            tp_index = []
            u_index = []
            new_continuous_area = []
            subarea_shape = []
            interpolation_subarea_index = []
            
            tie_point_indices = tie_point_indices[d].array.flatten().tolist()

            new = True

            # Initialize the count alng the interpolation subarea
            # dimension
            j = 0
            for i, (index0, index1) in enumerate(
                zip(tie_point_indices[:-1], tie_point_indices[1:])
            ):
                new_continuous_area.append(new)

                if index1 - index0 <= 1:
                    new = True
                    new_continuous_area.pop()
                    continue

                # The index of the interpolation subarea along the
                # corresponding interpolated subarea dimension
                interpolation_subarea_index.append(slice(j, j + 1))
                j += 1
                
                # The subspace for the axis of the tie points that
                # corresponds to this axis of the interpolation
                # subarea
                tp_index.append(slice(i, i + 2))

                # The size of the interpolation subarea along this
                # interpolated dimension
                subarea_shape.append(index1 - index0 + 1)
                
                # The subspace for this axis of the uncompressed array
                # that corresponds to the interpolation suabrea, only
                # including the first tie point if this the first
                # interpolation subarea in a new continuous area.
                if not new:
                    index0 += 1

                u_index.append(slice(index0, index1 + 1))

                new = False

            tp_indices[d] = tp_index
            u_indices[d] = u_index
            interpolation_subarea_shapes[d] = subarea_shape
            new_continuous_area[d] = new_area
            interpolation_subarea_indices[d] = interpolation_subarea_index
            
        return (
            product(*tp_indices),
            product(*u_indices),
            product(*interpolation_subarea_shapes),
            product(*new_continuous_area),
            product(*interpolation_subarea_indices),
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
    def computational_precision(self):
        """The validation computational precision.

        The floating-point arithmetic precision used during the
        preparation and validation of the compressed coordinates.

        """
        return self._get_component("computational_precision")

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
