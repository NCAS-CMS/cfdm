import numpy as np

from ....core.utils import cached_property
from .subarray import Subarray


class SubsampledSubarray(Subarray):
    """A subarray of an array compressed by subsampling.

    A subarray describes a unique part of the uncompressed array, and
    corresponds to a single interpolation subarea, omitting any
    elements that are defined by previous (in index-space)
    interpolation subareas.

    See CF section 8.3 "Lossy Compression by Coordinate Subsampling"
    and appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def __init__(
        self,
        data=None,
        indices=None,
        shape=None,
        compressed_dimensions=None,
        subarea_indices=None,
        first=None,
        parameters=None,
        dependent_tie_points=None,
        interpolation_description=None,
        source=None,
        copy=True,
        context_manager=None,
    ):
        """**Initialisation**

        :Parameters:

            data: array_like
                The full compressed tie points array spanning all
                subarrays, from which the elements for this subarray
                are defined by the *indices*.

            indices: `tuple`
                The indices of *data* that define this subarray.

            shape: `tuple` of `int`
                The shape of the uncompressed subarray.

            {{init compressed_dimensions: `dict`}}

                *Parameter example:*
                  ``{1: (1,)}``

                *Parameter example:*
                  ``{0: (0,), 2: (2,)}``

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

            interpolation_description: `str`, optional
                A complete description of the non-standardised
                interpolation method.

            {{init source: optional}}

            {{init copy: `bool`, optional}}

            context_manager: function, optional
                A context manager that provides a runtime context for
                the conversion of *data*, *dependent_tie_points*, and
                *parameters* to `numpy` arrays.

        """
        super().__init__(
            data=data,
            indices=indices,
            shape=shape,
            compressed_dimensions=compressed_dimensions,
            source=source,
            copy=copy,
            context_manager=context_manager,
        )

        if source is not None:
            try:
                subarea_indices = source._get_component(
                    "subarea_indices", None
                )
            except AttributeError:
                subarea_indices = None

            try:
                first = source._get_component("first", None)
            except AttributeError:
                first = None

            try:
                parameters = source._get_component("parameters", {})
            except AttributeError:
                parameters = {}

            try:
                dependent_tie_points = source._get_component(
                    "dependent_tie_points", {}
                )
            except AttributeError:
                dependent_tie_points = {}

            try:
                interpolation_description = source._get_component(
                    "interpolation_description", None
                )
            except AttributeError:
                interpolation_description = None

        if subarea_indices is not None:
            self._set_component("subarea_indices", subarea_indices, copy=copy)

        if first is not None:
            self._set_component("first", first, copy=False)

        if parameters is not None:
            self._set_component("parameters", parameters.copy(), copy=False)

        if dependent_tie_points is not None:
            self._set_component(
                "dependent_tie_points", dependent_tie_points.copy(), copy=False
            )

        if interpolation_description is not None:
            self._set_component(
                "interpolation_description",
                interpolation_description,
                copy=False,
            )

    def _broadcast_bounds(self, u):
        """Broadcast the raw uncompressed data to bounds locations.

        The raw uncompressed data is the basic interpolation of the
        bounds tie points, including the tie point locations.

        If *u* has not been calculated from bounds tie points then no
        broadcasting is done and the interpolated values are returned
        unchanged.

        See CF section 8.3.9 "Interpolation of Cell Boundaries".

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_post_process`, `_trim`

        :Parameters:

            u: `numpy.ndarray`
                The raw uncompressed data is the basic interpolation
                of the tie points, including the tie point locations.

        :Returns:

            `numpy.ndarray`

        """
        if not self.bounds:
            return u

        if np.ma.isMA(u):
            bounds = np.ma.empty(self.shape, dtype=u.dtype)
        else:
            bounds = np.empty(self.shape, dtype=u.dtype)

        subsampled_dimensions = sorted(self.compressed_dimensions())
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

        Returns the tie points from `data` as well as those provided
        by `get_dependent_tie_points`.

        .. versionadded:: (cfdm) 1.10.0.0

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
                f"Must provide an identity for each of the "
                f"{len(dependent_tie_points) + 1} codependent tie point "
                f"arrays. Identities {identities} were provided, which "
                f"should include the identities {tuple(dependent_tie_points)}"
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

    def _post_process(self, u):
        """Map the raw interpolated data to the uncompressed subarray.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            u: `numpy.ndarray`
               The uncompressed data for the whole interpolation
               subarea.

        :Returns:

            `numpy.ndarray`

        """
        u = self._broadcast_bounds(u)
        u = self._trim(u)
        return u

    def _s(self, d, s=None):
        """Return the interpolation coefficient ``s``.

        Returns the interpolation coefficient ``s`` for the specified
        subsampled dimension of the interpolation subarea. Note that
        the interpolation area may have fewer dimensions, and fewer
        elements, than the uncompresed subarray.

        See CF appendix J "Coordinate Interpolation Methods".

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            {{d: `int`}}

            {{s: array_like, optional}}

        :Returns:

            `numpy.ndarray`
                The interpolation coefficent ``s`` with values within
                the range [0, 1]. The array has extra size 1
                dimensions corresponding to all full tie point array
                dimensions other than *d*.

        **Examples**

        >>> x.shape
        (5, 5)
        >>> x.first
        (True, False)
        >>> x.bounds
        False
        >>> print(x._s(0))
        [[0.  ]
         [0.25]
         [0.5 ]
         [0.75]
         [1.  ]]
        >>> print(x._s(1))
        [[0.  0.2 0.4 0.6 0.8 1. ]]
        >>> print(x._s(1, s=0.5))
        [[0.5]]

        >>> x.shape
        (5, 5, 2)
        >>> x.first
        (True, False)
        >>> x.bounds
        True
        >>> print(x._s(0))
        [[0. ]
         [0.2]
         [0.4]
         [0.6]
         [0.8]
         [1. ]]
        >>> print(x._s(1))
        [[0.  0.2 0.4 0.6 0.8 1. ]]
        >>> print(x._s(1, s=0.5))
        [[0.5]]

        """
        ndim = self.data.ndim

        if s is not None:
            s = np.array(s, dtype=self.dtype)
            s.resize((1,) * ndim)
            return s

        size = self.shape[d]
        if self.bounds or not self.first[d]:
            size = size + 1

        s = np.linspace(0, 1, size, dtype=self.dtype)

        # Add extra size 1 dimensions so that s and 1-s are guaranteed
        # to be broadcastable to the tie points.
        if ndim > 1:
            new_shape = [1] * ndim
            new_shape[d] = size
            s.resize(new_shape)

        return s

    def _select_location(self, array, location=None):
        """Select interpolation parameter points interpolation subarea.

        Selects interpolation parameter points that correspond to this
        interpolation subarea.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_select_data`, `_select_parameter`

        :Parameters:

            array: `numpy.ndarray` or `None`
                All tie point or interpolation parameter values that
                apply to this interpolation subarea array, as returned
                by a call of `_select_data` or `_select_parameter`.

            location: `dict`, optional
                Identify the location within the interpolation
                subarea. Each key is an integer that specifies a
                subsampled dimension position in the array, with a
                value of either ``0`` or ``1`` indicating one of the
                two tie point positions along that dimension. By
                default, or if location is an empty dictionary, then
                all values for the interpolation subarea are returned.

        :Returns:

            `numpy.ndarray` or `None`
                The selected values, or `None` no array was provided.

        """
        if array is None:
            return

        if location:
            indices = [slice(None)] * array.ndim
            for subsampled_dimension, loc in location.items():
                indices[subsampled_dimension] = slice(loc, loc + 1)

            array = array[tuple(indices)]

        return array

    def _select_parameter(self, term):
        """Select interpolation parameter values.

        Selects interpolation parameter values for this interpolation
        subarea.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_select_data`, `_select_location`

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
            for i, (m, n) in (enumerate(zip(parameter.shape, self.data.shape)))
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

        return self._asanyarray(parameter, indices)

    def _trim(self, u):
        """Trim the raw uncompressed data.

        The raw uncompressed data is the basic interpolation of the
        tie points, including the tie point locations.

        For each subsampled dimension, removes the first point of the
        interpolation subarea when it is not the first (in
        index-space) of a continuous area. This is beacuse this value
        in the uncompressed data has already been calculated from the
        previous (in index space) interpolation subarea.

        However, if *u* has been calculated from bounds tie points
        then no elements are removed. This is because all elements are
        used for broadcasting to each CF bounds location. See CF
        section 8.3.9 "Interpolation of Cell Boundaries".

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_broadcast_bounds`, `_post_process`

        :Parameters:

            u: `numpy.ndarray`
                The raw uncompressed data is the basic interpolation
                of the tie points, including the tie point locations.

        :Returns:

            `numpy.ndarray`

        """
        if self.bounds:
            return u

        first = self.first

        take_slice = False
        indices = [slice(None)] * u.ndim
        for dim in self.compressed_dimensions():
            if first[dim]:
                continue

            take_slice = True
            indices[dim] = slice(1, None)

        if take_slice:
            u = u[tuple(indices)]

        return u

    @cached_property
    def bounds(self):
        """True if the tie points array represents bounds tie points.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self.ndim > self.data.ndim

    @property
    def dependent_tie_points(self):
        """The dependent tie points dictionary.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self._get_component("dependent_tie_points")

    @cached_property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return np.dtype(float)

    @property
    def first(self):
        """Relative interpolation subarea positions.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self._get_component("first")

    @property
    def parameters(self):
        """The interpolation parameters dictionary.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self._get_component("parameters")

    @property
    def subarea_indices(self):
        """Location of interpolation subarea.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self._get_component("subarea_indices")

    def get_filenames(self):
        """Return the names of any files containing the data.

        Includes the names of files that contain any parameters and
        dependent tie points.

        .. versionadded:: (cfdm) 1.10.0.2

        :Returns:

            `tuple`
                The file names in normalised, absolute form. If the
                data are all in memory then an empty `set` is
                returned.

        """
        filenames = super().get_filenames()

        for x in tuple(self.parameters.values()) + tuple(
            self.dependent_tie_points.values()
        ):
            try:
                filenames += x.get_filenames()
            except AttributeError:
                pass

        return tuple(set(filenames))

    def get_interpolation_description(self, default=ValueError()):
        """Get a non-standardised interpolation method description.

        .. versionadded:: (cfdm) 1.10.0.2

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                interpolation description has not been set.

                {{default Exception}}

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
