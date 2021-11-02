from functools import lru_cache
from itertools import product

import numpy as np

_float64 = np.dtype(float)


class SubsampledArray:
    """TODO.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed array as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        raise NotImplementedError("Must implement __getitem__ in subclasses")

    def _first_or_last_index(self, indices):
        """Return the first or last element of tie points array.

        This method will return the firat or last value without having
        to perform any interpolation.

        Currenly, the first and last elements are only recognised by
        exact *indices* matches to ``(slice(0, 1, 1),) * self.ndim``
        or ``(slice(-1, None, 1),) * self.ndim``

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            indices:
                Indices to the uncompressed array.

        :Returns:

            `numpy.ndarray`

        """
        ndim = self.ndim
        if (
            indices == (slice(0, 1, 1),) * ndim
            or indices == (slice(-1, None, 1),) * ndim
        ):
            if self.bounds:
                indices = indices[:-1]

            return self._get_compressed_Array()[indices]

        # Indices do not (acceptably) select the first nor last element
        raise IndexError()

    def _interpolation_subareas(self):
        """TODO.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            5-`tuple` of iterators
               * The indices of the uncompressed array that correspond
                 to each interpolation subarea, excluding a bounds
                 dimension.

                 .. note:: If a tie point is shared with a previous
                           interpolation subarea, then that location
                           is excluded from the index, thereby
                           avoiding any overlaps between indices.

               * The indices of the tie point array that correspond to
                 each interpolation subarea. Each index for the tie
                 point interpolated dimensions is expressed as a list
                 of two integers, rather than a `slice` object, to
                 facilitate retrieval of each tie point individually.

               * The shape of each uncompressed interpolation subarea,
                 including all tie points but excluding a bounds
                 dimension.

               * Flags which state, for each interpolated dimension,
                 whether each interplation subarea is at the start of
                 a continuous area, excluding a bounds dimension.

               * The index of each interpolation subarea along the
                 interpolation subarea dimensions, excluding a bounds
                 dimension.

        **Examples**

        An original 3-d array with shape (20, 12, 15) has been
        compressed by subsampling with dimensions 0 and 2 being
        interpolated dimensions. Interpolated dimension 0 (size 20)
        has two equally-sized continuous areas, each with one
        interpolation subarea of size 10; and interpolated dimenson 2
        (size 15) has a single continuous area divided into has three
        interpolation subarareas of szes 5, 6, and 6.

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
        bounds = self.bounds
        tie_point_indices = self.get_tie_point_indices()

        shape = self.shape
        if bounds:
            shape = shape[:-1]

        ndim = len(shape)

        # The indices of the uncompressed array that correspond to
        # each interpolation subarea. A bounds dimension is excluded.
        #
        # .. note:: If a tie point is shared with a previous
        #           interpolation subarea, then that location is
        #           excluded from the index, thereby avoiding any
        #           overlaps between indices.
        u_indices = [(slice(None),)] * ndim

        # The indices of the tie point array that correspond to each
        # interpolation subarea. A bounds dimension is excluded.
        tp_indices = [(slice(None),)] * ndim

        # The shape of each uncompressed interpolated subarea along
        # the interpolated dimensions, including all tie points. A
        # bounds dimension is excluded.
        interpolation_subarea_shapes = list(shape)

        # The flags which state, for each dimension, whether (`True`)
        # or not (`False`) an interplation subarea is at the start of
        # a continuous area. Non-interpolated dimensions are given the
        # flag `None`. A bounds dimension is excluded.
        new_continuous_area = [(None,)] * ndim

        # The index of each interpolation subarea along the
        # interpolation subarea dimensions. A bounds dimension is
        # excluded.
        interpolation_subarea_indices = [(slice(None),)] * ndim

        for d in self.compressed_dimensions():
            tp_index = []
            u_index = []
            continuous_area = []
            subarea_shape = []
            interpolation_subarea_index = []

            indices = tie_point_indices[d].data.array.flatten().tolist()

            new = True

            # Initialize the count alng the interpolation subarea
            # dimension
            j = 0
            for i, (index0, index1) in enumerate(
                zip(indices[:-1], indices[1:])
            ):
                continuous_area.append(new)

                if index1 - index0 <= 1:
                    new = True
                    continuous_area.pop()
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
            new_continuous_area[d] = continuous_area
            interpolation_subarea_indices[d] = interpolation_subarea_index

        return (
            product(*u_indices),
            product(*tp_indices),
            product(*interpolation_subarea_shapes),
            product(*new_continuous_area),
            product(*interpolation_subarea_indices),
        )

    @lru_cache(maxsize=32)
    def _s(self, subsampled_dimension, subarea_shape, first):
        """The interpolation coefficients for an interpolation subarea.

        Returns the interpolation coefficients ``s`` and ``1-s`` for
        the specified subsampled dimension of an interpolation subarea
        with the given shape. See CF appendix J.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            subsampled_dimension: `int`
                The position of a subsampled dimension in the tie
                point array.

            subarea_shape: `tuple` of `int`
                The shape of the uncompressed interpolation subarea,
                including both tie points but excluding a bounds
                dimension.

            first: `tuple` of `bool`
                For each dimension of the compressed array, whether or
                not the interpolation subarea is the first (in index
                space) of its continuous area.

        :Returns:

            `numpy.ndarray`, `numpy.ndarray`
                The interpolation coefficents ``s`` and ``1 - s``, in
                that order, each of which is a numpy array in the
                range [0.0, 1.0]. The numpy arrays will have extra
                size 1 dimensions corresponding to all tie point array
                dimensions other than *d*.

        **Examples**

        >>> x.bounds
        False
        >>> x._s(1, (12, 5), (False, True))
        array([[0.  , 0.25, 0.5 , 0.75, 1.  ]])
        array([[1.  , 0.75, 0.5 , 0.25, 0.  ]])
        >>> x._s(1, (12, 5), (False, False))
        array([[0.  , 0.25, 0.5 , 0.75, 1.  ]])
        array([[1.  , 0.75, 0.5 , 0.25, 0.  ]])

        >>> x.bounds
        True
        >>> x._s(1, (12, 5), (False, True))
        array([[0. , 0.2, 0.4, 0.6, 0.8, 1. ]])
        array([[1. , 0.8, 0.6, 0.4, 0.2, 0. ]])
        >>> x._s(1, (12, 5), (False, False))
        array([[0.  , 0.25, 0.5 , 0.75, 1.  ]])
        array([[1.  , 0.75, 0.5 , 0.25, 0.  ]])

        """
        size = subarea_shape[subsampled_dimension]
        first = first[subsampled_dimension]
        if self.bounds and first:
            # For bounds tie points, the first interpolation subarea
            # of a continuous area has an extra point. See CF
            # 8.3.9. "Interpolation of Cell Boundaries".
            size = size + 1

        s = np.linspace(0, 1, size, dtype=_float64)  # self.dtype)

        one_minus_s = s[::-1]

        # Add extra size 1 dimensions so that s and 1-s are guaranteed
        # to be broadcastable to the tie points.
        ndim = len(subarea_shape)
        if ndim > 1:
            new_shape = [1] * ndim
            new_shape[subsampled_dimension] = s.size
            s = s.reshape(new_shape)
            one_minus_s = one_minus_s.reshape(new_shape)

        return (s, one_minus_s)

    def _select_tie_points(self, tie_points, tp_indices, location={}):
        """Select tie points from an interpolation subarea.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            tie_points: array_like
               The full tie points array.

            tp_indices: `tuple` of `slice`
                The index of the *tie_points* array that defines the
                tie points for the interpolation subarea.

            location: `dict`, optional
                Identify the tie point location. Each key is an
                integer that specifies a dimension position in the tie
                points array, with a value of ``0`` or ``1`` that
                indicates ones of the two tie point positions along
                that dimension of an interpolation subarea. By
                default, or if location is an empty dictionary, then
                all tie points for the interpolation subarea are
                returned.

        :Returns:

            `numpy.ndarray`
                The selected tie points.

        """
        tp_indices = list(tp_indices)
        for dim, position in location.items():
            tpi0 = tp_indices[dim].start + position
            tp_indices[dim] = slice(tpi0, tpi0 + 1)

        return tie_points[tuple(tp_indices)].array

    def _set_interpolated_values(
        self, uarray, u, u_indices, subsampled_dimensions
    ):
        """TODO.

        If the compressed data are bounds tie points, then the
        interpolated values are broadcast to each location of the
        trailing bounds dimension. See CF 8.3.9. "Interpolation of
        Cell Boundaries".

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_trim`

        :Parameters:

            uarray: `numpy.ndarray`

            u_indices: `tuple`

            subsampled_dimensions: sequence of `int`

            u: `numpy.ndarray`

        :Returns:

            `None`

        """
        if not self.bounds:
            # Tie point coordinates
            uarray[u_indices] = u
            return

        # Bounds tie points
        indices = [slice(None)] * u.ndim
        n_subsampled_dimensions = len(subsampled_dimensions)
        if n_subsampled_dimensions == 1:
            (d0,) = subsampled_dimensions

            indices[d0] = slice(0, -1)
            uarray[u_indices + (0,)] = u[tuple(indices)]

            indices[d0] = slice(1, None)
            uarray[u_indices + (1,)] = u[tuple(indices)]
        elif n_subsampled_dimensions == 2:
            (d0, d1) = subsampled_dimensions

            indices[d0] = slice(0, -1)
            indices[d1] = slice(0, -1)
            uarray[u_indices + (0,)] = u[tuple(indices)]

            indices[d1] = slice(1, None)
            uarray[u_indices + (1,)] = u[tuple(indices)]

            indices[d0] = slice(1, None)
            indices[d1] = slice(1, None)
            uarray[u_indices + (2,)] = u[tuple(indices)]

            indices[d1] = slice(1, None)
            indices[d1] = slice(0, -1)
            uarray[u_indices + (3,)] = u[tuple(indices)]
        else:
            raise ValueError(
                f"Can't yet create uncompressed bounds from "
                f"{n_subsampled_dimensions} subsampled dimensions"
            )

    def _trim(self, u, subsampled_dimensions, first):
        """Trim uncompressed data defined on an interpolation subarea.

        For each subsampled dimension, removes the first point of the
        interpolation subarea when it is not the first (in index
        space) of a continuous area. This is beacuse this value in the
        uncompressed data has already been calculated from the
        previous (in index space) interpolation subarea.

        Only does this when interpolating tie point coordinates. If
        interpolating bounds tie points then the first point is always
        kept so that it may be used during the broadcast to the bounds
        locations.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_set_interpolated_values`

        :Parameters:

            u: array_like
               The uncompressed data for the interpolation subarea
               that includes all tie point locations.

            subsampled_dimensions: sequence of `int`
                The positions of the subsampled dimensions in the
                compressed data.

            first: `tuple`
                For each dimension, True if the interpolation subarea
                is the first (in index space) of a new continuous
                area, otherwise False.

        :Returns:

            `numpy.ndarray`

        """
        if self.bounds:
            return u

        take_slice = False
        indices = [slice(None)] * u.ndim
        for d in subsampled_dimensions:
            if first[d]:
                continue

            take_slice = True
            indices[d] = slice(1, None)

        if take_slice:
            u = u[tuple(indices)]

        return u

    @property
    def bounds(self):
        """True if the compressed array represent bounds tie points.

        This is the case when the uncompressed data has an extra
        trailing dimension compared to the compressed array. See CF
        section 8.3.9 "Interpolation of Cell Boundaries".

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        b = self._get_component("bounds", None)
        if b is None:
            b = self.ndim > self._get_compressed_Array().ndim
            self._set_component("bounds", b, copy=False)

        return b

    @property
    def dtype(self):
        """Data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return _float64

    def get_computational_precision(self, default=ValueError()):
        """Return the validation computational precision.

        The validation computational precision is the floating-point
        arithmetic precision used during the preparation and
        validation of the compressed coordinates.

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                computational precision has not been set.

                {{default Exception}}

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        out = self._get_component("computational_precision", None)
        if out is None:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__!r} has no "
                "'computational_precision'",
            )

        return out

    def conform_interpolation_parameters(self):
        """Conform the interpolation parameters.

        Tranposes the interpolation parameters, if any, to have the
        same relative dimension order as the compressed array, and
        inserts any missing dimensions as size 1 axes.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `None`

        """
        parameters = self.get_interpolation_parameters()
        if not parameters:
            return

        parameter_dimensions = self.get_parameter_dimensions()

        ndim = self._get_compressed_Array().ndim
        dims = list(range(ndim))

        for term, param in parameters.items():
            param_dims = parameter_dimensions[term]
            if sorted(param_dims) == dims:
                # The interpolation parameter dimensions are already
                # in the correct order
                continue

            if len(param_dims) > 1:
                new_order = [
                    param_dims.index(i) for i in dims if i in param_dims
                ]
                param = param.transpose(new_order)

            # Add non-interpolated dimensions as size 1 axes, if
            # they're not already there.
            if len(param_dims) < ndim:
                for d in sorted(set(dims).difference(param_dims)):
                    param = param.insert_dimension(position=d)

            parameters[term] = param
            parameter_dimensions[term] = dims

    def get_interpolation_description(self, default=ValueError()):
        """Return the non-standardised interpolation method description.

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                interpolation description has not been set.

                {{default Exception}}

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_interpolation_name`

        """
        out = self._get_component("interpolation_description", None)
        if out is None:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__!r} has no "
                "'interpolation_description'",
            )

        return out

    def get_interpolation_name(self, default=ValueError()):
        """Return the name a standardised interpolation method.

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                interpolation name has not been set.

                {{default Exception}}

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_interpolation_description`

        """
        out = self._get_component("interpolation_name", None)
        if out is None:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__!r} has no 'interpolation_name'",
            )

        return out

    def get_interpolation_parameters(self, conform=False):
        """Return the interpolation parameter variables.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `conform_interpolation_parameters`,
                     `get_parameter_dimensions`

        :Parameters:

            conform: `bool`, optional
                If True then the interpolation parameters are
                conformed to match the dimensions of the tie
                points. See `conform_interpolation_parameters` for
                details.

        :Returns:

            `dict`
                TODO. If no interpolation parameter variables have
                been set then an empty dictionary is returned.

        """
        if conform:
            self.conform_interpolation_parameters()

        return self._get_component("interpolation_parameters").copy()

    def get_parameter_dimensions(self):
        """TODO.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_interpolation_parameters`

        :Returns:

            `dict`
                If no parameter dimensions have been set then an empty
                dictionary is returned.

        """
        return self._get_component("parameter_dimensions").copy()

    def get_tie_point_indices(self):
        """Return the tie point index variables for subsampled
        dimensions.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `dict`
                The tie point index variables. If no tie point index
                variables have been set then an empty dictionary is
                returned.

        """
        return self._get_component("tie_point_indices").copy()

    def to_memory(self):
        """Bring an array on disk into memory.

        There is no change to an array that is already in memory.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `{{class}}`
                The array that is stored in memory.

        """
        for v in self._get_compressed_Array():
            v.data.to_memory()

        for v in self.get_tie_point_indices().values():
            v.data.to_memory()

        for v in self.get_interpolation_parameters.values():
            v.data.to_memory()

        return self

    def tranpose(self, axes=None):
        """Tranpose the compressed array without uncompressing it.

        .. versionadded:: 1.9.TODO.0

        .. seealso:: `conform_interpolation_parameters`

        :Parameters:

            axes: seqeunce of `ints`, optional
                By default, reverse the dimensions, otherwise permute
                the axes according to the values given.

        :Returns:

            `{{class}}`
                 A new instance with the transposed compressed array.

        """
        # Parse axes
        ndim = self.ndim
        if axes:
            if len(axes) != ndim:
                raise ValueError("axes don't match array")

            axes = tuple(d + ndim if d < 0 else d for d in axes)
        else:
            axes = tuple(range(ndim))[::-1]

        # Tranpose the compressed array
        compressed_array = self.source().tranpose(axes=axes)

        # Transpose the uncompressed shape
        shape = self.shape
        if self.bounds:
            shape1 = shape[:-1]
            new_shape = tuple([shape1.index(i) for i in axes]) + (shape[-1],)
        else:
            new_shape = tuple([shape.index(i) for i in axes])

        # Change the tie point index dimensions
        tie_point_indices = {
            axes.index(i): tpi
            for i, tpi in self.get_tie_point_indices().items()
        }

        # Change the interpolation parameter dimensions
        parameter_dimensions = {
            term: tuple([axes.index(i) for i in dims])
            for term, dims in self.get_parameter_dimensions().items()
        }

        return type(self)(
            compressed_array=compressed_array,
            shape=new_shape,
            ndim=self.ndim,
            size=self.size,
            interpolation_name=self.get_interpolation_name(None),
            interpolation_description=self.get_interpolation_description(None),
            tie_point_indices=tie_point_indices,
            interpolation_parameters=self.get_interpolation_parameters(),
            parameter_dimensions=parameter_dimensions,
        )
