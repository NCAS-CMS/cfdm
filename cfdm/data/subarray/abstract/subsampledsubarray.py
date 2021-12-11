import numpy as np

from .subarray import Subarray

_float64 = np.dtype(float)


class SubsampledSubarray(Subarray):
    """A subsampled subarray of an array compressed by subsampling.

    Each subarray of the compressed array describes a unique part of
    the uncompressed array defined by the *indices* parameter.

    A subarray corresponds to a single interpolation subarea (defined
    by the *indices* and *subarea_indices* parameters), omitting any
    elements that are defined by previous (in index-space)
    interpolation subareas.

    When an instance is indexed, the subarray is first uncompressed
    into a `numpy.ndarray` whose shape is given by the *shape*
    parameter, which is the indexed as requested.

    The decompression method must be defined in subclasses by
    overriding the `__getitem__` method.

    See CF section 8.3 "Lossy Compression by Coordinate Subsampling"
    and Appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(
        self,
        data=None,
        indices=None,
        shape=None,
        compressed_dimensions=None,
        subarea_indices=None,
        first=None,
        parameters={},
        dependent_tie_points={},
    ):
        """**Initialisation**

        :Parameters:

            data: array_like
                The full tie points array for all interpolation
                subarareas. May be a bounds tie point array. The array
                must provide values for all interpolation subareas,
                from which the applicable elements are defined by the
                *indices* indices.

            indices: `tuple` of `slice`
                For each dimension of the *data* array, the index that
                defines the tie points elements that correspond to
                this interpolation subarea.

            compressed_dimensions: sequence of `int`
                The positions of the subsampled dimensions in the
                tie points array.

            shape: `tuple` of `int`
                The shape of the uncompressed array.

            first: `tuple` of `bool`
                For each dimension of the tie points array, True if
                the interpolation subarea is the first along that
                dimension of the continuous area, otherwise False.

            subarea_indices: `tuple` of `slice`
                For each dimension of the tie points array, the index
                that defines the location of the interpolation subarea
                in interpolation-subarea-space. An index corresponding
                to a non-interpolated dimension must be `slice(None)`.

            parameters: `dict`, optional
                If the interpolation method requires interpolation
                parameters then these are provided as array_like
                values, each keyed by its parameter term name. A
                parameter array must provide values for all
                interpolation subareas, from which the applicable
                elements are defined by the *subarea_indices* and
                *indices* indices.

                Each dimension of a parameter array maps to the
                dimension in the same position of the tie points
                array. The size of a parameter array dimension must be
                either i) the size as the corresponding tie points
                array dimension; ii) the size of the interpolation
                subarea dimension for the corresponding tie points
                array dimension; or iii) ``1``.

            dependent_tie_points: `dict`, optional
                If the interpolation method requires dependent tie
                point arrays then these are provided as array_like
                values, each keyed by its identity. A dependent tie
                points array must provide values for all interpolation
                subareas, from which the applicable elements are
                defined by the *indices* indices.

                A dependent tie points array must have the same shape
                as the tie points array, and each dimension maps to
                the dimension in the same position of the tie points
                array.

        """
        super().__init__(
            data=data,
            indices=indices,
            shape=shape,
            compressed_dimensions=compressed_dimensions
        )

        self.subarea_indices = subarea_indices
        self.first = first
        self.parameters = parameters.copy()
        self.dependent_tie_points = dependent_tie_points.copy()

    def _broadcast_bounds(self, u):
        """TODO

        When the compressed data are bounds tie points, then the
        interpolated values are broadcast to each location of the
        trailing bounds dimension. See CF 8.3.9 "Interpolation of Cell
        Boundaries".

        If the data compressed data are instead tie points, then the
        interpolated values are returned unchanged.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            u: `numpy.ndarray`
               The uncompressed data for the interpolation subarea
               that includes all tie point locations. TODO

        :Returns:

            `numpy.ndarray`
               TODO

        """
        if not self.bounds:
            return u

        if np.ma.isMA(u):
            bounds = np.ma.masked_all(self.shape, dtype=u.dtype)
        else:
            bounds = np.empty(self.shape, dtype=u.dtype)

        subsampled_dimensions = self.compressed_dimensions
        n = len(subsampled_dimensions)

        indices = [slice(None)] * u.ndim

        if n == 1:
            (d1,) = subsampled_dimensions

            indices[d1] = slice(0, -1)
            bounds[..., 0] = u[tuple(indices)]

            indices[d1] = slice(1, None)
            bounds[..., 1] = u[tuple(indices)]

        elif n == 2:
            (d1, d2) = subsampled_dimensions

            indices[d1] = slice(0, -1)
            indices[d2] = slice(0, -1)
            bounds[..., 0] = u[tuple(indices)]

            indices[d2] = slice(1, None)
            bounds[..., 1] = u[tuple(indices)]

            indices[d1] = slice(1, None)
            bounds[..., 2] = u[tuple(indices)]

            indices[d2] = slice(1, None)
            indices[d2] = slice(0, -1)
            bounds[..., 3] = u[tuple(indices)]
        else:
            raise ValueError("Can only deal with 1 or 2 subsampled dimensions")

        return bounds

    def _codependent_tie_points(self, *identities):
        """Get all codependent tie points.

        Returns the tie points from `data as well as those returned by
        `get_dependent_tie_points`.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            identities:
                The identities of all codependent tie points, of which
                all except one must be keys of the dictionary returned
                by `get_dependent_tie_points`. The identity that is
                not a key of that dictionary will correspond to the
                stored `tie_points`.

        :Returns:

            `list` of array_like
                The codependent tie points, in the order specified by
                the *identities* parameter.

        **Examples**

        >>> lat, lon = g._codependent_tie_points('latitude', 'longitude')

        """
        dependent_tie_points = self.dependent_tie_points

        if len(identities) != len(dependent_tie_points) + 1:
            raise ValueError(
                f"There must be exactly {len(dependent_tie_points)} "
                "dependent tie point array(s), got {len(identities)}"
            )
        
        if not set(dependent_tie_points).issubset(identities):
            raise ValueError(
                "Each dependent tie point identity must be one of: "
                f"{', '.join(map(str, identities))}"
            )

        out = []
        for identity in identities:
            tie_points = dependent_tie_points.get(identity)
            if tie_points is None:
                out.append(self.data)
            else:
                out.append(tie_points)

        return out

    def _parameter_location(self, parameter, location={}):
        """TODO"""
        if parameter is None:
            return

        if location:
            indices = [slice(None)] * self.data.ndim
            shape = parameter.shape
            for subsampled_dimension, loc in location.items():
                if shape[subsampled_dimension] != 2:
                    raise ValueError(
                        f"TODO {shape} {subsampled_dimension} {loc}"
                    )

                if loc == 1:
                    indices[subsampled_dimension] = slice(1, 2)
                else:
                    indices[subsampled_dimension] = slice(0, 1)

            parameter = parameter[tuple(indices)]

        return parameter

    def _post_process(self, u):
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

        :Parameters:

            u: `numpy.ndarray`
               The uncompressed data for the interpolation subarea
               that includes all tie point locations.

        :Returns:

            `numpy.ndarray`

        """
        u = self._broadcast_bounds(u)
        u = self._trim(u)
        return u

    def _select_data(self, data=None, location={}):
        """Select tie points that correspond to this interpolation subarea.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            data: array_like or `None`
                A full tie points array spanning all interpolation
                subareas, from which elements for this interpolation
                subarea will be returned. By default, or if `None`
                then the `data` array is used.

            location: `dict`, optional
                Identify the tie point location within the
                interpolation subarea. Each key is an integer that
                specifies a subsampled dimension position in the tie
                points array, with a value of either ``0`` or ``1``
                indicating one of the two tie point positions along
                that dimension. By default, or if location is an empty
                dictionary, then all tie points for the interpolation
                subarea are returned.

        :Returns:

            `numpy.ndarray`
                Values of the tie points array that correspond to this
                interpolation subarea.

        """
        tp_indices = self.indices

        if location:
            tp_indices = list(tp_indices)
            for dim, position in location.items():
                i = tp_indices[dim].start + position
                tp_indices[dim] = slice(i, i + 1)

            tp_indices = tuple(tp_indices)

        if data is None:
            data = self.data

        return np.asanyarray(data[tp_indices])

    def _select_parameter(self, term):
        """Select interpolation parameter values for this interpolation
        subarea.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `parameters`, `subarea_indices`, `indices`

        :Parameters:

            term: `str`
                The term name of an interpolation parameter. If *term*
                is not a key of the `parameters` dictionary, then
                `None` is returned.

        :Returns:

            `numpy.ndarray` or `None`
                The values of the interpolation parameter array that
                correspond to this interpolation subarea, or `None` if
                the interpolation parameter array has not been
                defined.

        """
        parameter = self.parameters.get(term)
        if parameter is None:
            return
        
        # Find the parameter array dimensions which are subsampled
        # dimensions
        subsampled_dimensions = [
            i
            for i, (m, n) in (
                enumerate(zip(parameter.shape, self.data.shape))
            )
            if m == n
        ]

        if subsampled_dimensions:
            indices = tuple(
                tp_index if dim in subsampled_dimensions else subarea_index
                for dim, (subarea_index, tp_index) in (
                    enumerate(zip(self.subarea_indices, self.indices))
                )
            )
        else:
            indices = self.subarea_indices

        return np.asanyarray(parameter[indices])

    def _trim(self, u):
        """Trim uncompressed data defined on an interpolation subarea.

        For each subsampled dimension, removes the first point of the
        interpolation subarea when it is not the first (in index
        space) of a continuous area. This is beacuse this value in the
        uncompressed data has already been calculated from the
        previous (in index space) interpolation subarea.

        If *u* has been calculated from bounds tie points then no
        elements are removed. This is because all elements are need
        for broadcasting to each CF bounds location. See CF section
        8.3.9 "Interpolation of Cell Boundaries".

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            u: array_like
               The raw interpolated array data for the interpolation
               subarea that includes all tie point locations.

        :Returns:

            array_like

        """
        if self.bounds:
            return u

        first = self.first

        take_slice = False
        indices = [slice(None)] * u.ndim
        for dim in self.compressed_dimensions:
            if first[dim]:
                continue

            take_slice = True
            indices[dim] = slice(1, None)

        if take_slice:
            u = u[tuple(indices)]

        return u

    @property
    def bounds(self):
        """True if the tie points array represents bounds tie points.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        is_bounds = self._get_component("bounds", None)
        if is_bounds is None:
            is_bounds = self.ndim > self.data.ndim
            self._set_component("bounds", is_bounds, copy=False)

        return is_bounds

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return _float64

    @property
    def tie_points(self):
        """The tie points array. An alias for `data`.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return self.data
