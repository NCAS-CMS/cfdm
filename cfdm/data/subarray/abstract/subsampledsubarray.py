from functools import reduce
from itertools import product
from operator import mul

import numpy as np


_float64 = np.dtype(float)


class SubsampledSubarray:
    """TODO.

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
                The (bounds) tie points array.

            tp_indices: `tuple` of `slice`
                The index of the *array* that defines the
                tie points for the interpolation subarea.

            subsampled_dimensions: sequence of `int`
                The positions of the subsampled dimensions in the
                compressed data.

            shape: `tuple`
                The uncompressed array shape.

            first: `tuple`
                For each dimension, True if the interpolation subarea
                is the first (in index space) of a new continuous
                area, otherwise False.

        """
        super().__init__(
            tie_points=tie_points,
            tp_indices=tp_indices,
            subsampled_dimensions=subsampled_dimensions,
            shape=shape,
            subarea_indices=subarea_indices,
            first=first,
            parameters=parameters,
            dependent_tie_points=dependent_tie_points,
        )

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
       trailing bounds dimension. See CF 8.3.9 "Interpolation of
       Cell Boundaries".
 
       """
       bounds = np.empty(self.shape, dtype=u.dtype)

       subsampled_dimensions = self.subsampled_dimensions
       n = len(subsampled_dimensions)
       
       if n == 1:
           (d0,) = subsampled_dimensions
           
           indices = [slice(None)] * u.ndim
           
           indices[d0] = slice(0, -1)
           bounds[..., 0] = u[tuple(indices)]
           
           indices[d0] = slice(1, None)
           bounds[..., 1] = u[tuple(indices)]

       elif n == 2:
           (d0, d1) = subsampled_dimensions
           
           indices = [slice(None)] * u.ndim
        
           indices[d0] = slice(0, -1)
           indices[d1] = slice(0, -1)
           bounds[..., 0] = u[tuple(indices)]
           
           indices[d1] = slice(1, None)
           bounds[..., 1] = u[tuple(indices)]
           
           indices[d0] = slice(1, None)
           bounds[..., 2] = u[tuple(indices)]
           
           indices[d1] = slice(1, None)
           indices[d1] = slice(0, -1)
           bounds[..., 3] = u[tuple(indices)]
       
       return bounds

    def _parameter_location(self, c, positions):
        """TODO
        
        """
        indices = [slice(None)] * self.array.ndim
       
        take_slice = False
        for subsampled_dimension, position in positions.items():
            if position == "is":
                continue

            if position == "tp0":
                indices[subsampled_dimension] = slice(0, 1)                
            elif position == "tp1":
                indices[subsampled_dimension] = slice(1, 2)                

            take_slice = True

        if take_slice:
            c = c[tuple(indices)]
            
        return c

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

            array_like

        """
        if self.bounds:
            return self._broadcast_bounds(u)
        
        return self._trim(u)

    def _select_parameter(self, name, default=None):
        """Select tie points from an interpolation subarea.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            p: array_like or `None`
               A full array of interpolation parameters

            default: optional
                TODO

        :Returns:

            `numpy.ndarray`
                The selected values.

        """
        parameter = self.parameters.get(name)

        if parameter is None:
            if default is None:
                return

            # Return a size 1 array containing a default value
            return np.full((1,) * len(self.subarea_indices), default)

#        subsampled_dimensions = [
#            i
#            for i, (m, n) in enumerate(zip(parameter.shape, self.tie_points.shape))
#            if m == n
#        ]
        
#        if subsampled_dimensions:
        subsampled_dimensions = self.subsampled_dimensions 
        indices = [
            tp_index if dim in subsampled_dimensions else
            subarea_index
            for dim, (subarea_index, tp_index) in (
                    enumerate(zip(self.subarea_indices, self.tp_indices))
            )
        ]
        
        return np.asanyarray(parameter[tuple(subarea_indices)])
    
    def _select_tie_point(self, tie_points=None, location={}):
        """Select TODO  tie points from an interpolation subarea.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            tie_points: array_like
               A full (bounds) tie points array.

            indices: `tuple` of `slice`
                The index of the *tie_points* array that defines the
                tie points for the interpolation subarea.

            location: `dict`, optional
                Identify the tie point location within the
                interpolation subarea. Each key is an integer that
                specifies a dimension position in the tie points
                array, with a value of either ``0`` or ``1`` that
                indicates ones of the two tie point positions along
                that dimension of an interpolation subarea. By
                default, or if location is an empty dictionary, then
                all tie points for the interpolation subarea are
                returned.

            default: optional
                TODO

        :Returns:

            array_like
                The selected values.

        """
        tp_indices = self.tp_indices
        
        if location:
            tp_indices = list(tp_indices)
            for dim, position in location.items():
                i = tp_indices[dim].start + position
                indices[dim] = slice(i, i + 1)

            tp_indices = tuple(tp_indices)

        if tie_points is None:
            tie_points = self.tie_points
            
        return np.gasanyarray(tie_points[tp_indices])

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
               The uncompressed data for the interpolation subarea
               that includes all tie point locations.

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
            indices[d] = slice(1, None)

        if take_slice:
            u = u[tuple(indices)]

        return u

    @property
    def bounds(self):
        """True if the tie points array represents bounds tie points.

        When the tie points array represents bounds tie points the
        uncompressed data has an extra trailing dimension compared to
        the compressed array. See CF section 8.3.9 "Interpolation of
        Cell Boundaries".

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        is_bounds = self._get_component("bounds", None)
        if is_bounds is None:
            is_bounds = self.ndim > self.tie_points.ndim
            self._set_component("bounds", b, copy=False)

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
        dependent_tie_points = self.dependent_tie_points
        if (
                len(identities) != len(dependent_tie_points) + 1
                or not set(identities).issubset(dependent_tie_points)
        ):
            raise ValueError(
                "The specified identities "
                f"{', '.join(map(str, identities))} must comprise "
                "all except one of the dependent tie point names "
                f"{', '.join(map(str, dependent_tie_points))}"
            )
        
        out = []
        for identity in identities:
            tie_points = dependent_tie_points.get(identity)
            if tie_points is None:
                out.append(self.tie_points)
            else:
                out.append(tie_points)

        return out
