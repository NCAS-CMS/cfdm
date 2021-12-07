from functools import lru_cache
from itertools import product

import numpy as np


_float64 = np.dtype(float)


class SubsampledArray:
    """TODO.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

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
#        raise NotImplementedError("Must implement __getitem__ in subclasses")

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        # If the first or last element is requested then we don't need
        # to interpolate
        try:
            return self._first_or_last_index(indices)
        except IndexError:
            pass

        Subarray = self._Subarray
        if Subarray is None:
            raise IndexError(
                "Can't subspace subsampled data with a non-standardised "
                "interpolation method"
            )
        
        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        subsampled_dimensions = self.compressed_dimensions()

        tie_points = self._get_compressed_Array()
        
        self.conform()
        parameters = self.get_parameters()
        dependent_tie_points = self.get_dependent_tie_points()
        
        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=np.dtype(float))

        # Interpolate the tie points for each interpolation subarea
        for u_indices, tp_indices, subarea_shape, first, subarea_indices in (
                zip(*self._interpolation_subareas())
        ):
            subarray = Subarray(
                tie_points=tie_points,
                tp_indices=tp_indices,
                subsampled_dimensions=subsampled_dimensions,
                shape=subarea_shape,
                first=first,
                subarea_indices=subarea_indices,
                parameters=parameters,
                dependent_tie_points=dependent_tie_points,
            )
            uarray[u_indices] = subarray[...]
            
        return self.get_subspace(uarray, indices, copy=True)
    
    def _conform_location_use_3d_cartesian(self):
        """TODO

        It is assumed that the "interpolation_subarea_flags"
        interpolation parameters has been checked with
        `_check_3d_cartesian_flags`.

        See CF section 3.5 "Flags" and Appendix J "Coordinate
        Interpolation Methods" for details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `None`

        """
        location_use_3d_cartesian = "location_use_3d_cartesian"

        flags = self.parameters.get(location_use_3d_cartesian)
        if flags is None:
            return

        flag_values = flags.get_property("flag_values", None)
        flag_masks = flags.get_property("flag_masks", None)
        flag_meanings = flags.get_property("flag_meanings", None)

        if flag_meanings is None:
            raise ValueError(
                "Can't uncompress subsampled coordinates with the "
                f"{self.get_interpolation_name()} method when the "
                "interpolation_subarea_flags interpolation parameter "
                "does not have a flag_meanings property"
            )

        if flags_masks is None and flags_values is None:
            raise ValueError(
                "Can't uncompress subsampled coordinates with the "
                f"{self.get_interpolation_name()} method when the "
                "interpolation_subarea_flags interpolation parameter "
                "does not have either or both of the flag_values "
                "flag_masks and properties"
            )

        flag_meanings = flag_meanings.split()
        if location_use_3d_cartesian not in flag_meanings:
            raise ValueError(
                "Can't uncompress subsampled coordinates with the "
                f"{self.get_interpolation_name()} method when the "
                "interpolation_subarea_flags interpolation parameter "
                f"does not have {location_use_3d_cartesian} in its "
                "flag_meanings property"
            )

        flag_meanings = np.atleast_1d(flag_meanings)
        index = np.where(flag_meanings == location_use_3d_cartesian)[0]

        data = flags.data
        
        if flags_masks is not None:
            flag_mask = np.atleast_1d(flag_masks)[index]
      
        if flag_values is not None:
            flag_value = np.atleast_1d(flag_values)[index]
            if flags_masks is None:
                # flag_values but no flag_masks
                new_data = data == flag_value
            else:
                # flag_values and flag_masks
                new_data = data & (flag_mask & flag_value)
        else:
            # flag_masks but no flag_values
            new_data = data & flag_mask

        flags = flags.set_data(new_data, copy=False, inplace=False)
            
        self.parameters[location_use_3d_cartesian] = flags

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
        tie_point_indices = self.get_tie_point_indices()

        shape = self.shape        
#        if self.bounds:
#            bounds_size = shape[-1]
#            shape = shape[:-1]
#        else:
#            bounds_size = 0

        ndim = len(shape)

        # The indices of the uncompressed array that correspond to
        # each interpolation subarea. NO A bounds dimension is excluded.
        #
        # .. note:: If a tie point is shared with a previous
        #           interpolation subarea, then that location is
        #           excluded from the index, thereby avoiding any
        #           overlaps between indices.
        u_indices = [(slice(None),)] * ndim

        # The indices of the tie point array that correspond to each
        # interpolation subarea. NO A bounds dimension is excluded.
        tp_indices = [(slice(None),)] * ndim

        # The shape of each uncompressed interpolated subarea along
        # the interpolated dimensions, including all tie points. NO A
        # bounds dimension is excluded.
        interpolation_subarea_shapes = list(shape)

        # The flags which state, for each dimension, whether (`True`)
        # or not (`False`) an interplation subarea is at the start of
        # a continuous area. Non-interpolated dimensions are given the
        # flag `None`. NO A bounds dimension is excluded.
        new_continuous_area = [(None,)] * ndim

        # The index of each interpolation subarea along the
        # interpolation subarea dimensions. NO A bounds dimension is
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

#    def _set_interpolated_values(
#        self, uarray, u, u_indices, subsampled_dimensions
#    ):
#        """TODO.
#
#        If the compressed data are bounds tie points, then the
#        interpolated values are broadcast to each location of the
#        trailing bounds dimension. See CF 8.3.9. "Interpolation of
#        Cell Boundaries".
#
#        .. versionadded:: (cfdm) 1.9.TODO.0
#
#        .. seealso:: `_trim`
#
#        :Parameters:
#
#            uarray: `numpy.ndarray`
#
#            u_indices: `tuple`
#
#            subsampled_dimensions: sequence of `int`
#
#            u: `numpy.ndarray`
#
#        :Returns:
#
#            `None`
#
#        """
#        if not self.bounds:
#            # Tie point coordinates
#            uarray[u_indices] = u
#            return
#
#        # Bounds tie points
#        indices = [slice(None)] * u.ndim
#        n_subsampled_dimensions = len(subsampled_dimensions)
#        if n_subsampled_dimensions == 1:
#            (d0,) = subsampled_dimensions
#
#            indices[d0] = slice(0, -1)
#            uarray[u_indices + (0,)] = u[tuple(indices)]
#
#            indices[d0] = slice(1, None)
#            uarray[u_indices + (1,)] = u[tuple(indices)]
#        elif n_subsampled_dimensions == 2:
#            (d0, d1) = subsampled_dimensions
#
#            indices[d0] = slice(0, -1)
#            indices[d1] = slice(0, -1)
#            uarray[u_indices + (0,)] = u[tuple(indices)]
#
#            indices[d1] = slice(1, None)
#            uarray[u_indices + (1,)] = u[tuple(indices)]
#
#            indices[d0] = slice(1, None)
#            indices[d1] = slice(1, None)
#            uarray[u_indices + (2,)] = u[tuple(indices)]
#
#            indices[d1] = slice(1, None)
#            indices[d1] = slice(0, -1)
#            uarray[u_indices + (3,)] = u[tuple(indices)]
#        else:
#            raise ValueError(
#                f"Can't yet create uncompressed bounds from "
#                f"{n_subsampled_dimensions} subsampled dimensions"
#            )

    @property
    def bounds(self):
        """True if the compressed array represents bounds tie points.

        When the compressed array represents bounds tie points the
        uncompressed data has an extra trailing dimension compared to
        the compressed array. See CF section 8.3.9 "Interpolation of
        Cell Boundaries".

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        is_bounds = self._get_component("bounds", None)
        if is_bounds is None:
            is_bounds = self.ndim > self._get_compressed_Array().ndim
            self._set_component("bounds", b, copy=False)

        return is_bounds

    @property
    def dtype(self):
        """Data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return _float64

    def codependent_tie_points(self, *identities):
        """Get all codependent tie points.

        Returns the tie points from `source` as well as those returned
        by `get_dependent_tie_points`.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            identities:
                The identities of the codependent tie points, all
                except one of which must be keys of the dictionary
                returned by `get_dependent_tie_points`.

        :Returns:

            `list`
                The codependent tie points, in the order specified by
                the *identities* parameter.

        **Examples**

        >>> lat, lon = g.codependent_tie_points('latitude', 'longitude')

        """
        dependent_tie_points = self.get_dependent_tie_points(conform=True)
        if (
                len(identities) != len(dependent_tie_points) + 1
                or not set(identities).issubset(dependent_tie_points)
        ):
            raise ValueError(
                "Specified identities must comprise all except one of "
                f"{', '.join(map(str, dependent_tie_points))}. Got "
                f"{', '.join(map(str, identities))}"
            )
        
        out = []
        for identity in identities:
            tie_points = dependent_tie_points.get(identity)
            if tie_points is None:
                out.append(self.source())
            else:
                out.append(tie_points)

        return out

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

    def conform(self, dependent_tie_points=True, parameters=True):
        """Conform interpolation parameters and extra tie_points.

        Tranposes the interpolation parameters and extra tie points,
        if any, to have the same relative dimension order as the
        compressed array.

        Missing dimensions in interpolation parameters may be inserted
        as size 1 axes.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            dependent_tie_points: `bool`
                If False then do not conform any extra tie points.

            parameters: `bool`
                If False then do not conform any interpolation
                parameters.

        :Returns:

            `None`

        """
        if not (dependent_tie_points or parameters):
            return

        parameter_dimensions = None
        tie_point_dims = None

        if parameters:
            parameters = self._get_component("parameters")
            parameter_dimensions = self._get_component("parameter_dimensions")
            
        if dependent_tie_points:
            tie_points = self._get_component("dependent_tie_points")
            tie_point_dimensions = self._get_component(
                "dependent_tie_point_dimensions"
            )

        ndim = self._get_compressed_Array().ndim
        dims = tuple(range(ndim))

        if parameter_dimensions:
            for term, param in parameters.items():
                param_dims = parameter_dimensions[term]
                if tuple(sorted(param_dims)) == dims:
                    # The interpolation parameter dimensions are already
                    # in the correct order
                    continue

                if len(param_dims) > 1:
                    new_order = [
                        param_dims.index(i) for i in dims if i in param_dims
                    ]
                    param = param.transpose(new_order)

                # Add missing interpolation parameter dimensions
                # as size 1 axes
                if len(param_dims) < ndim:
                    for d in sorted(set(dims).difference(param_dims)):
                        param = param.insert_dimension(position=d)

                parameters[term] = param
                parameter_dimensions[term] = dims

            self._conform_location_use_3d_cartesian()
                
        if tie_point_dimensions:
            for identity, tp in tie_points.items():
                tp_dims = tie_point_dimensions[identity]
                if tuple(sorted(tp_dims)) == dims:
                    # The dependent tie point dimensions are already
                    # in the correct order
                    continue

                if len(tp_dims) > 1:
                    new_order = [
                        tp_dims.index(i) for i in dims if i in tp_dims
                    ]
                    tp = tp.transpose(new_order)

                tie_points[identity] = tp
                tie_point_dims[identity] = dims

    def get_dependent_tie_points(self, conform=False):
        """Return the TODO interpolation parameter variables.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `conform`, `get_dependent_tie_point_dimensions`

        :Parameters:

            conform: `bool`, optional
                If True then the extra tie points and extra tie point
                dimensions are conformed to match the dimensions of
                the tie points.

        :Returns:

            `dict`
                TODO. If no interpolation parameter variables have
                been set then an empty dictionary is returned.

        """
        if conform:
            self.conform(dependent_tie_points=True, parameters=False)

        return self._get_component("dependent_tie_points").copy()

    def get_dependent_tie_point_dimensions(self, conform=False):
        """Return the TODO interpolation parameter variables.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `conform`, `get_dependent_tie_points`

        :Parameters:

            conform: `bool`, optional
                If True then the extra tie points and extra tie point
                dimensions are conformed to match the dimensions of
                the tie points.

        :Returns:

            `dict`
                TODO. If no interpolation parameter variables have
                been set then an empty dictionary is returned.

        """
        if conform:
            self.conform(dependent_tie_points=True, parameters=False)

        return self._get_component("dependent_tie_point_dimensions").copy()

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

    def get_parameters(self, conform=False):
        """Return the interpolation parameter variables.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `conform`, `get_parameter_dimensions`

        :Parameters:

            conform: `bool`, optional
                If True then the interpolation parameters and
                interpolation parameter dimensions are conformed to
                match the dimensions of the tie points.

        :Returns:

            `dict`
                TODO. If no interpolation parameter variables have
                been set then an empty dictionary is returned.

        """
        if conform:
            self.conform(dependent_tie_points=False, parameters=True)

        return self._get_component("parameters").copy()

    def get_parameter_dimensions(self, conform=False):
        """TODO.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `conform`, `get_parameters`

        :Parameters:

            conform: `bool`, optional
                If True then the interpolation parameters and
                interpolation parameter dimensions are conformed to
                match the dimensions of the tie points.

        :Returns:

            `dict`
                If no parameter dimensions have been set then an empty
                dictionary is returned.

        """
        if conform:
            self.conform(dependent_tie_points=False, parameters=True)

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

    def set_dependent_tie_point_dimensions(self, value, copy=True):
        """TODO
        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `None`

        """
        self._set_component(
            "dependent_tie_point_dimensions", value.copy(), copy=False
        )

    def set_dependent_tie_points(self, value, copy=True):
        """TODO
        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `None`

        """
        if copy:
            value = {key: tp.copy() for key, tp in value.items()}
        else:
            value = value.copy()

        self._set_component("dependent_tie_points", value, copy=False)

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

        for v in self.get_parameters.values():
            v.data.to_memory()

        return self


#    def tranpose(self, axes=None):
#        """Tranpose the compressed array without uncompressing it.
#
#        .. versionadded:: 1.9.TODO.0
#
#        .. seealso:: `conform`
#
#        :Parameters:
#
#            axes: seqeunce of `ints`, optional
#                By default, reverse the dimensions, otherwise permute
#                the axes according to the values given.
#
#        :Returns:
#
#            `{{class}}`
#                 A new instance with the transposed compressed array.
#
#        """
#        # Parse axes
#        ndim = self.ndim
#        if axes:
#            if len(axes) != ndim:
#                raise ValueError("axes don't match array")
#
#            axes = tuple(d + ndim if d < 0 else d for d in axes)
#        else:
#            axes = tuple(range(ndim))[::-1]
#
#        # Tranpose the compressed array
#        compressed_array = self.source().tranpose(axes=axes)
#
#        # Transpose the uncompressed shape
#        shape = self.shape
#        if self.bounds:
#            shape1 = shape[:-1]
#            new_shape = tuple([shape1.index(i) for i in axes]) + (shape[-1],)
#        else:
#            new_shape = tuple([shape.index(i) for i in axes])
#
#        # Change the tie point index dimensions
#        tie_point_indices = {
#            axes.index(i): tpi
#            for i, tpi in self.get_tie_point_indices().items()
#        }
#
#        # Change the interpolation parameter dimensions
#        parameter_dimensions = {
#            term: tuple([axes.index(i) for i in dims])
#            for term, dims in self.get_parameter_dimensions().items()
#        }
#
#        return type(self)(
#            compressed_array=compressed_array,
#            shape=new_shape,
#            ndim=self.ndim,
#            size=self.size,
#            interpolation_name=self.get_interpolation_name(None),
#            interpolation_description=self.get_interpolation_description(None),
#            tie_point_indices=tie_point_indices,
#            parameters=self.get_parameters(),
#            parameter_dimensions=parameter_dimensions,
#        )
