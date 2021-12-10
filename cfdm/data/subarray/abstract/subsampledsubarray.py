from functools import reduce
from operator import mul

import numpy as np

from ....abstract import Container

_float64 = np.dtype(float)


class SubsampledSubarray(Container):
    """Uncompress an interpolation subarea of a subsampled array.

    When an instance is indexed, interpolation is carried out to
    uncompress the single interpolation subarea (defined by the
    *tp_indices* and *subarea_indices* parameters) into an array whose
    shape is given by the *shape* parameter. This array is then
    indexed as requested.

    The interpolation method must be defined in subclasses by
    overriding the `__getitem__` method.

    See CF section 8.3 "Lossy Compression by Coordinate Subsampling"
    and Appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(
        self,
        tie_points=None,
        tp_indices=None,
        subsampled_dimensions=None,
        shape=None,
        subarea_indices=None,
        first=None,
        parameters={},
        dependent_tie_points={},
    ):
        """**Initialisation**

        :Parameters:

            tie_points: array_like
                The full tie points array for all interpolation
                subarareas. May be a bounds tie point array. The array
                must provide values for all interpolation subareas,
                the applicable elements are defined by the
                *tp_indices* indices.

            tp_indices: `tuple` of `slice`
                For each dimension of the *tie_points* array, the
                index that defines the location of the interpolation
                subarea's tie points in te *tie_points*. An index
                corresponding to a non-interpolated dimension must be
                `slice(None)`.

            subsampled_dimensions: sequence of `int`
                The positions of the subsampled dimensions in the
                *tie_points* array.

            shape: `tuple` of `int`
                The shape of the uncompressed array.

                When `bounds` is False, if the interpolation subarea
                is not the first along a subsampled dimension of the
                continuous subarea (as defined by the *first*
                parameter), then the shared tie point location is
                ommited from the uncompressed array.

            first: `tuple` of `bool`
                For each dimension of the *tie_points* array, True if
                the interpolation subarea is the first along that
                dimension of the continuous area, otherwise False.

            subarea_indices: `tuple` of `slice`
                For each dimension of the *tie_points* array, the
                index that defines the location of the interpolation
                subarea in interpolation-subarea-space. An index
                corresponding to a non-interpolated dimension must be
                `slice(None)`.

            parameters: `dict`, optional If the interpolation method
                requires interpolation parameters then these are
                provided, then the array_like parameters are given in
                this dictionary, keyed by the parameter terms'
                names. A parameter array must provide values for all
                interpolation subareas, the applicable elements are
                defined by the *subarea_indices* and *tp_indices*
                indices.

                Each dimension of a parameter array maps to the
                dimension in the same position of the *tie_points*
                array. The size of a parameter array dimension is
                either i) the same as the *tie_points* array
                dimension; ii) the size of the interpolation subarea
                dimension corresponding to a *tie_points* array
                subsampled dimension; or iii) 1.

            dependent_tie_points: `dict`, optional
                If the interpolation method requires multiple tie
                points arrays to be interpolated simultaneously, then
                the array_like dependent (bounds) tie points are given
                in this dictionary, keyed by the dependent tie points'
                identities. A dependent tie points array must provide
                values for all interpolation subareas, the applicable
                elements are defined by the *tp_indices* indices.

                A dependent tie points array must have the same shape
                as the *tie_points* array, and each dimension maps to
                the dimension in the same position of the *tie_points*
                array.

        """
        super().__init__()

        self.tie_points = tie_points
        self.tp_indices = tp_indices
        self.subsampled_dimensions = subsampled_dimensions
        self.shape = shape
        self.subarea_indices = subarea_indices
        self.first = first
        self.parameters = parameters.copy()
        self.dependent_tie_points = dependent_tie_points.copy()

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed array as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        raise NotImplementedError("Must implement __getitem__ in subclasses")

    def _broadcast_bounds(self, u):
        """TODO

        When the compressed data are bounds tie points, then the
        interpolated values are broadcast to each location of the
        trailing bounds dimension. See CF 8.3.9 "Interpolation of Cell
        Boundaries".

        If the data compressed data are instead tie points, then the
        interpolated values are returned unchanged.

        """
        if not self.bounds:
            return u

        if np.ma.isMA(u):
            bounds = np.ma.masked_all(self.shape, dtype=u.dtype)
        else:
            bounds = np.empty(self.shape, dtype=u.dtype)

        subsampled_dimensions = self.subsampled_dimensions
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

        Returns the tie points from `tie_points` as well as those
        returned by `get_dependent_tie_points`.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            identities:
                The identities of all codependent tie points, of which
                all except one must be keys of the dictionary returned
                by `get_dependent_tie_points`. The identity that is
                not a key of that dictionary will correspond to the
                stored `tie_points`.

        :Returns:

            `list`
                The codependent tie points, in the order specified by
                the *identities* parameter.

        **Examples**

        >>> lat, lon = g._codependent_tie_points('latitude', 'longitude')

        """
        dependent_tie_points = self.dependent_tie_points
        if not (
            len(identities) == len(dependent_tie_points) + 1
            and set(dependent_tie_points).issubset(identities)
        ):
            raise ValueError(
                "The codependent tie point identities "
                f"({', '.join(map(str, identities))}) must comprise all of "
                "the dependent tie point names "
                f"({', '.join(map(str, dependent_tie_points))}) "
                "plus one other."
            )

        out = []
        for identity in identities:
            tie_points = dependent_tie_points.get(identity)
            if tie_points is None:
                out.append(self.tie_points)
            else:
                out.append(tie_points)

        return out

    def _parameter_location(self, parameter, location={}):
        """TODO"""
        if parameter is None:
            return

        if location:
            indices = [slice(None)] * self.tie_points.ndim
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

            u: array_like
               The uncompressed data for the interpolation subarea
               that includes all tie point locations.

        :Returns:

            `numpy.ndarray`

        """
        u = self._broadcast_bounds(u)
        u = self._trim(u)

        return np.asanyarray(u)

    def _select_parameter(self, name, location={}):
        """Select TODO.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `parameters`, `subarea_indices`, `tp_indices`

        :Parameters:

            name: `str`
               The term name of a paramater. Must be a key of the
               `parameters` dictionary.

            default: optional
                TODO

            flag: `bool`, opional
               TODO

        :Returns:

            `numpy.ndarray` or `None`
                The selected values.

        """
        parameter = self.parameters.get(name)

        if parameter is None:
            return
        #            if default is None:
        #                return
        #
        #            # Return a size 1 array containing a default value
        #            return np.full((1,) * len(self.subarea_indices), default)

        # Find the parameter array dimensions which are subsampled
        # dimensions
        subsampled_dimensions = [
            i
            for i, (m, n) in (
                enumerate(zip(parameter.shape, self.tie_points.shape))
            )
            if m == n
        ]

        #        if subsampled_dimensions:
        #            indices = list(self.subarea_indices)
        ##            indices = []
        #            for dim, tp_index in enumerate(self.tp_indices)):
        #                if dim in subsampled_dimensions:
        #                    if dim in locations:
        #                        i = tp_index.start + locations[dim]
        #                        index = slice(i, i + 1)
        #                    else:
        #                        index = tp_index
        #
        #                    indices[dim] = index
        ##                else:
        ##                    index = subarea_index
        #
        ##                indices.append(index)
        #
        #            indices = tuple(indices)
        #
        if subsampled_dimensions:
            indices = tuple(
                tp_index if dim in subsampled_dimensions else subarea_index
                for dim, (subarea_index, tp_index) in (
                    enumerate(zip(self.subarea_indices, self.tp_indices))
                )
            )
        else:
            indices = self.subarea_indices

        return np.asanyarray(parameter[indices])

    def _select_tie_point(self, tie_points=None, location={}):
        """Select TODO  tie points from an interpolation subarea.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `tie_points`, `tp_indices`

        :Parameters:

            tie_points: array_like or `None`
                The full array of tie points. If `None` then the
                `tie_points` array is used.

            location: `dict`, optional
                Identify the tie point location within the
                interpolation subarea. Each key is an integer that
                specifies a subsampled dimension position in the tie
                points array, with a value of either ``0`` or ``1``
                that indicates ones of the two tie point positions
                along that dimension of an interpolation subarea. By
                default, or if location is an empty dictionary, then
                all tie points for the interpolation subarea are
                returned.

        :Returns:

            `numpy.ndarray`
                The selected tie points.

        """
        tp_indices = self.tp_indices

        if location:
            tp_indices = list(tp_indices)
            for dim, position in location.items():
                i = tp_indices[dim].start + position
                tp_indices[dim] = slice(i, i + 1)

            tp_indices = tuple(tp_indices)

        if tie_points is None:
            tie_points = self.tie_points

        return np.asanyarray(tie_points[tp_indices])

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
        for dim in self.subsampled_dimensions:
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
            is_bounds = self.ndim > self.tie_points.ndim
            self._set_component("bounds", is_bounds, copy=False)

        return is_bounds

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return _float64

    @property
    def ndim(self):
        """The number of dimensions of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return len(self.shape)

    @property
    def size(self):
        """The size of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return reduce(mul, self.shape, 1)
