from itertools import product

import numpy as np

from .abstract import CompressedArray
from .subarray import (
    BiLinearSubarray,
    BiQuadraticLatitudeLongitudeSubarray,
    LinearSubarray,
    QuadraticLatitudeLongitudeSubarray,
    QuadraticSubarray,
)
from .utils import cached_property


class SubsampledArray(CompressedArray):
    """An underlying subsampled array.

    For some structured coordinate data (e.g. coordinates describing
    remote sensing products) space may be saved by storing a subsample
    of the data, called tie points. The uncompressed data can be
    reconstituted by interpolation, from the subsampled values. This
    process will likely result in a loss in accuracy (as opposed to
    precision) in the uncompressed variables, due to rounding and
    approximation errors in the interpolation calculations, but it is
    assumed that these errors will be small enough to not be of
    concern to users of the uncompressed dataset. The creator of the
    compressed dataset can control the accuracy of the reconstituted
    data through the degree of subsampling and the choice of
    interpolation method.

    See CF section 8.3 "Lossy Compression by Coordinate Subsampling"
    and Appendix J "Coordinate Interpolation Methods".

    >>> tie_point_indices={{package}}.TiePointIndex(data=[0, 4, 7, 8, 11])
    >>> w = {{package}}.InterpolationParameter(data=[5, 10, 5])
    >>> coords = {{package}}.SubsampledArray(
    ...     interpolation_name='quadratic',
    ...     compressed_array={{package}}.Data([15, 135, 225, 255, 345]),
    ...     shape=(12,),
    ...     ndim=1,
    ...     size=12,
    ...     tie_point_indices={0: tie_point_indices},
    ...     parameters={"w": w},
    ...     parameter_dimensions={"w": (0,)},
    ... )
    >>> print(coords[...])
    [ 15.          48.75        80.         108.75       135.
     173.88888889 203.88888889 225.         255.         289.44444444
     319.44444444 345.        ]

    **Cell boundaries**

    When the tie points array represents bounds tie points then the
    *shape* parameter describes the uncompressed bounds shape. See CF
    section 8.3.9 "Interpolation of Cell Boundaries".

    >>> bounds = {{package}}.SubsampledArray(
    ...     interpolation_name='quadratic',
    ...     compressed_array={{package}}.Data([0, 150, 240, 240, 360]),
    ...     shape=(12, 2),
    ...     ndim=2,
    ...     size=24,
    ...     tie_point_indices={0: tie_point_indices},
    ...     parameters={"w": w},
    ...     parameter_dimensions={"w": (0,)},
    ... )
    >>> print(bounds[...])
    [[0.0 33.2]
     [33.2 64.8]
     [64.8 94.80000000000001]
     [94.80000000000001 123.2]
     [123.2 150.0]
     [150.0 188.88888888888889]
     [188.88888888888889 218.88888888888889]
     [218.88888888888889 240.0]
     [240.0 273.75]
     [273.75 305.0]
     [305.0 333.75]
     [333.75 360.0]]

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    _flag_names = ("location_use_3d_cartesian",)

    def __new__(cls, *args, **kwargs):
        """Store subarray classes.

        The subarray classes are stored as values of a dictionary
        whose keys are the corresponding "interpolation_name" property
        values.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        instance = super().__new__(cls)

        instance._Subarray = {
            "bi_linear": BiLinearSubarray,
            "bi_quadratic_latitude_longitude": BiQuadraticLatitudeLongitudeSubarray,
            "linear": LinearSubarray,
            "quadratic": QuadraticSubarray,
            "quadratic_latitude_longitude": QuadraticLatitudeLongitudeSubarray,
        }

        return instance

    def __init__(
        self,
        interpolation_name=None,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        computational_precision=None,
        interpolation_description=None,
        tie_point_indices={},
        parameters={},
        parameter_dimensions={},
        dependent_tie_points={},
        dependent_tie_point_dimensions={},
    ):
        """**Initialisation**

        :Parameters:

            interpolation_name: `str`, optional
                The name of the interpolation method.

                Standardised interpolation method are defined in CF
                appendix J "Coordinate Interpolation Methods".

                If not set then the non-standardised interpolation
                method is assumed to be defined by the
                *interpolation_description* parameter

                *Parameter example:*
                  ``'bi_linear'``

            compressed_array: `Data`
                The (bounds) tie points array.

            shape: `tuple`
                The uncompressed array shape.

            size: `int`
                Number of elements in the uncompressed array, must be
                equal to the product of *shape*.

            ndim: `int`
                The number of uncompressed array dimensions, equal to
                the length of *shape*.

            tie_point_indices: `dict`
                The tie point index variable for each subsampled
                dimension. A key indentifies a subsampled dimension by
                its integer position in the compressed array, and its
                value is a `TiePointIndex` variable.

                *Parameter example:*
                  ``{1: {{package}}.TiePointIndex(data=[0, 16, 31])}``

            computational_precision: `str`, optional
                The floating-point arithmetic precision used during
                the preparation and validation of the compressed data.

                *Parameter example:*
                  ``'64'``

            interpolation_description: `str`, optional
                A complete non-standardised description of the
                interpolation method.

            parameters: `dict`, optional
                Interpolation parameters required by the interpolation
                method. Each key is an interpolation parameter term
                name, whose value is an `InterpolationParameter`
                variable.

                Interpolation parameter term names for the
                standardised interpolation methods are defined in CF
                Appendix J "Coordinate Interpolation Methods".

                Set to an empty dictionary for interpolation methods
                that do not require interpolation parameters.

                *Parameter example:*
                  ``{}``

                *Parameter example:*
                  ``{'w': {{package}}.InterpolationParameter(data=[5, 10, 5])}``

            parameter_dimensions: `dict`, optional
                The tie point array dimensions that correspond to the
                dimensions of the interpolation parameters, keyed the
                interpolation parameter term names.

                Interpolation parameter term names for the
                standardised interpolation methods are defined in CF
                Appendix J "Coordinate Interpolation Methods".

                Set to an empty dictionary for interpolation methods
                that do not require interpolation parameters.

                *Parameter example:*
                  ``{}``

                *Parameter example:*
                  ``{'w': (0,)}``

                *Parameter example:*
                  ``{'ce1': (1, 2), 'ca2': (2, 1)}``

            dependent_tie_points: `dict`, optional
                The dependent tie point arrays needed by the
                interpolation method, keyed the dependent tie point
                identities. Each key is a dependent tie point
                identity, whose value is a `Data` variable.

                The identities must be understood the interpolation
                method. When *interpolation_name* is
                ``'quadratic_latitude_longitude'`` or
                ``'bi_quadratic_latitude_longitude'` then the
                *dependent_tie_points* dictionary must contain exactly
                one of the keys ``'latitude'`` or ``'longitude``.

                Set to an empty dictionary for interpolation methods
                that do require require dependent tie points.

                *Parameter example:*
                  ``{}``

                *Parameter example:*
                  ``{'latitude': {{package}}.Data([30, 31, 32])}``

            dependent_tie_points_dimensions: `dict`, optional
                The tie point array dimensions that correspond to the
                dimensions of the dependent tie points arrays, keyed
                the dependent tie point identities.

                Set to an empty dictionary for interpolation methods
                that do not require dependent tie points.

                *Parameter example:*
                  ``{}``

                *Parameter example:*
                  ``{'latitude': (0,)}``

                *Parameter example:*
                  ``{'longitude': (0, 1)}``

                *Parameter example:*
                  ``{'latitude': (2, 0, 1)}``

        """
        compressed_dimensions = {d: (d,) for d in sorted(tie_point_indices)}

        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            size=size,
            ndim=ndim,
            compression_type="subsampled",
            interpolation_name=interpolation_name,
            computational_precision=computational_precision,
            compressed_dimensions=compressed_dimensions,
            tie_point_indices=tie_point_indices.copy(),
            parameters=parameters.copy(),
            parameter_dimensions=parameter_dimensions.copy(),
            dependent_tie_points=dependent_tie_points.copy(),
            dependent_tie_point_dimensions=dependent_tie_point_dimensions.copy(),
        )

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

        interpolation_name = self.get_interpolation_name(None)
        Subarray = self._Subarray.get(interpolation_name)
        if Subarray is None:
            if interpolation_name is None:
                raise IndexError(
                    "Can't subspace subsampled data according to the "
                    "non-standardised interpolation_description "
                    f"{self.get_interpolation_description('')!r}"
                )

            raise ValueError(
                "Can't subspace subsampled data with unknown "
                f"interpolation_name {interpolation_name!r}"
            )

        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=self.dtype)

        subsampled_dimensions = self.compressed_dimensions()

        conformed_data = self.conformed_data()
        tie_points = conformed_data["data"]
        parameters = conformed_data["parameters"]
        dependent_tie_points = conformed_data["dependent_tie_points"]

        # Interpolate the tie points for each interpolation subarea
        for (
            u_indices,
            subarea_shape,
            tp_indices,
            first,
            subarea_indices,
        ) in zip(*self.subarrays()):
            subarray = Subarray(
                data=tie_points,
                indices=tp_indices,
                shape=subarea_shape,
                compressed_dimensions=subsampled_dimensions,
                first=first,
                subarea_indices=subarea_indices,
                parameters=parameters,
                dependent_tie_points=dependent_tie_points,
            )
            uarray[u_indices] = subarray[...]

        return self.get_subspace(uarray, indices, copy=True)

    def _conformed_dependent_tie_points(self):
        """Return the dependent tie points.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_conformed_parameters`, `conformed_data`

        :Returns:

            `dict`
                The conformed dependent tie points, keyed by their
                identities.

        """
        dependent_tie_points = self.get_dependent_tie_points()

        if dependent_tie_points:
            dependent_tie_point_dimensions = (
                self.get_dependent_tie_point_dimensions()
            )

            tp_ndim = self.source().ndim
            dims = list(range(tp_ndim))

            for identity, tp in dependent_tie_points.items():
                tp = tp.data
                tp_dims = dependent_tie_point_dimensions[identity]
                if sorted(tp_dims) == dims:
                    # The dependent tie point dimensions are already
                    # in the correct order
                    tp = tp.copy()
                else:
                    new_order = [
                        tp_dims.index(i) for i in dims if i in tp_dims
                    ]
                    tp = tp.transpose(new_order)

                dependent_tie_points[identity] = tp

        return dependent_tie_points

    def _conformed_interpolation_subarea_flags(self):
        """Return interpolation_subarea_flag interpolation parameters.

        See CF section 3.5 "Flags" and Appendix J "Coordinate
        Interpolation Methods".

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_conformed_parameters`

        :Returns:

            `dict`
                The conformed interpolation_subarea_flag parameters,
                keyed by flag names.

        """
        out = {}

        parameter = self.get_parameters().get("interpolation_subarea_flags")
        if parameter is None:
            return out

        flag_values = parameter.get_property("flag_values", None)
        flag_masks = parameter.get_property("flag_masks", None)
        flag_meanings = parameter.get_property("flag_meanings", None)

        if flag_meanings is None:
            # The interpolation_subarea_flags interpolation parameter
            # does not have the "flag_meanings" property
            return out

        if flag_masks is None and flag_values is None:
            # The interpolation_subarea_flags interpolation parameter
            # does not have the "flag_values" nor the "flag_masks"
            # properties
            return out

        flag_meanings = flag_meanings.split()

        parameter = parameter.data

        for name in self._flag_names:
            if name not in flag_meanings:
                # The interpolation_subarea_flags interpolation
                # parameter does not have this flag name in its
                # "flag_meanings" property
                continue

            flag_meanings = np.atleast_1d(flag_meanings)
            index = np.where(flag_meanings == name)[0]

            if flag_masks is not None:
                mask = np.atleast_1d(flag_masks)[index]

            if flag_values is not None:
                value = np.atleast_1d(flag_values)[index]
                if flag_masks is None:
                    # flag_values but no flag_masks
                    data = parameter == value
                else:
                    # flag_values and flag_masks
                    data = parameter & (mask & value)
            else:
                # flag_masks but no flag_values
                data = parameter & mask

            out[name] = data

        return out

    def _conformed_parameters(self):
        """Return interpolation parameters.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_conformed_dependent_tie_points`,
                     `conformed_data`

        :Returns:

            `dict`
                The conformed parameters, keyed by their parmaeter
                term names.

        """
        parameters = self.get_parameters()

        if parameters:
            parameter_dimensions = self.get_parameter_dimensions()

            tp_ndim = self.source().ndim
            dims = list(range(tp_ndim))

            for term, parameter in parameters.items():
                parameter = parameter.data
                parameter_dims = parameter_dimensions[term]
                if sorted(parameter_dims) == dims:
                    # The interpolation parameter dimensions are
                    # already in the correct order
                    parameter = parameter.copy()
                else:
                    new_order = [
                        parameter_dims.index(i)
                        for i in dims
                        if i in parameter_dims
                    ]
                    parameter = parameter.transpose(new_order)

                    # Add missing interpolation parameter dimensions as
                    # size 1 axes
                    if len(parameter_dims) < tp_ndim:
                        for d in sorted(set(dims).difference(parameter_dims)):
                            parameter = parameter.insert_dimension(position=d)

                parameters[term] = parameter

            parameters.update(self._conformed_interpolation_subarea_flags())

        return parameters

    @cached_property
    def bounds(self):
        """True if the compressed array represents bounds tie points.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return self.ndim > self.source().ndim

    @cached_property
    def dtype(self):
        """Data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return np.dtype(float)

    def conformed_data(self):
        """Return the conformed tie points and any ancillary data.

        Returns the tie points and any ancillary data in the forms
        required by the interpolation algorthm.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `dict`
                The conformed tie points, with the key ``'data'``; the
                conformed interpolation parameters, with the key
                ``'parameters'``; and the conformed dependent tie
                points, with the key ``'dependent_tie_points'``.

        """
        out = super().conformed_data()
        out["parameters"] = self._conformed_parameters()
        out["dependent_tie_points"] = self._conformed_dependent_tie_points()
        return out

    def get_computational_precision(self, default=ValueError()):
        """Get the validation computational precision.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                computational precision has not been set.

                {{default Exception}}

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

    def get_dependent_tie_point_dimensions(self):
        """Get the dimension order of dependent tie points.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_dependent_tie_points`

        :Returns:

            `dict`
                The tie point array dimensions that correspond to the
                dimensions of the dependent tie points arrays, keyed
                the dependent tie point identities.

        """
        return self._get_component("dependent_tie_point_dimensions").copy()

    def get_dependent_tie_points(self):
        """Get the dependent tie points.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_dependent_tie_point_dimensions`

        :Returns:

            `dict`
                A dictionary of dependent tie points, each keyed by
                its identity.

        """
        return self._get_component("dependent_tie_points").copy()

    def get_interpolation_description(self, default=ValueError()):
        """Get the non-standardised interpolation method description.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_interpolation_name`

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

    def get_interpolation_name(self, default=ValueError()):
        """Get the name of a standardised interpolation method.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_interpolation_description`

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

    def get_parameter_dimensions(self):
        """Get the dimension order interpolation parameters.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_parameters`, `set_parameter_dimensions`

        :Returns:

            `dict`
                The interpolation parameter dimension orders relative
                to the tie points array, each keyed the interpolation
                parameter term name.

        """
        return self._get_component("parameter_dimensions").copy()

    def get_parameters(self):
        """Get the interpolation parameter variables.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `get_parameter_dimensions`, `set_parameters`

        :Returns:

            `dict`
                The interpolation parameters, each keyed the
                interpolation parameter term name.

        """
        return self._get_component("parameters").copy()

    def get_tie_point_indices(self):
        """Get the tie point index variables for subsampled dimensions.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `dict`
                The tie point index variables, each keyed by its
                corresponding subsampled dimension position. If no tie
                point index variables have been set then an empty
                dictionary is returned.

        """
        return self._get_component("tie_point_indices").copy()

    def set_dependent_tie_point_dimensions(self, value):
        """Set the dimension order of dependent tie points.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `set_dependent_tie_points`

        :Parameters:

            value: `dict`
                The tie point array dimensions that correspond to the
                dimensions of the dependent tie points arrays, keyed
                the dependent tie point identities.

        :Returns:

            `None`

        """
        self._set_component(
            "dependent_tie_point_dimensions", value.copy(), copy=False
        )

    def set_dependent_tie_points(self, value, copy=True):
        """Set the dependent tie points.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `set_dependent_tie_point_dimensions`

        :Parameters:

            value: `dict`
                A dictionary of dependent tie points, each keyed by
                its identity.

            copy: `bool`, optional
                If False then the dependent tie points are not copies.
                By default the tie points are deep copied.

        :Returns:

            `None`

        """
        if copy:
            value = {identity: tp.copy() for identity, tp in value.items()}
        else:
            value = value.copy()

        self._set_component("dependent_tie_points", value, copy=False)

    def subarrays(self):
        """Return descriptors for every subarray.

        Theses descriptors are used during subarray decompression.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            5-`tuple` of iterators
               Each iterator iterates over a particular descriptor
               from each subarray.

               1. The indices of the uncompressed array that
                  correspond to each interpolation subarea.

                  .. note:: If a tie point is shared with a previous
                            interpolation subarea, then that location
                            is excluded from the index, thereby
                            avoiding any overlaps between indices.

               2. The shape of each uncompressed interpolation
                  subarea, excluding the tie point locations defined
                  in previous interpolation subareas.

               3. The indices of the tie point array that correspond
                  to each interpolation subarea. Each index for the
                  tie point interpolated dimensions is expressed as a
                  list of two integers, rather than a `slice` object,
                  to facilitate retrieval of each tie point
                  individually.

               4. Flags which state, for each interpolated dimension,
                  whether each interplation subarea is at the start of
                  a continuous area.

               5. The index of each interpolation subarea along the
                  interpolation subarea dimensions.

        **Examples**

        An original 3-d array with shape (20, 12, 15) has been
        compressed by subsampling with dimensions 0 and 2 being
        interpolated dimensions. Interpolated dimension 0 (size 20)
        has two equally-sized continuous areas, each with one
        interpolation subarea of size 10; and interpolated dimenson 2
        (size 15) has a single continuous area divided into has three
        interpolation subareas of szes 5, 6, and 6.

        >>> (u_indices,
        ...  interpolation_subarea_shapes,
        ...  tp_indices,
        ...  new_continuous_area,
        ...  interpolation_subarea_indices) = x.subarrays()
        >>> for i in u_indices:
        ...    print(i)
        ...
        (slice(0, 10, None), slice(None, None, None), slice(0, 5, None))
        (slice(0, 10, None), slice(None, None, None), slice(5, 10, None))
        (slice(0, 10, None), slice(None, None, None), slice(10, 15, None))
        (slice(10, 20, None), slice(None, None, None), slice(0, 5, None))
        (slice(10, 20, None), slice(None, None, None), slice(5, 10, None))
        (slice(10, 20, None), slice(None, None, None), slice(10, 15, None))
        >>> for i in interpolation_subarea_shapes:
        ...    print(i)
        ...
        (10, 12, 5)
        (10, 12, 5)
        (10, 12, 5)
        (10, 12, 5)
        (10, 12, 5)
        (10, 12, 5)
        >>> for i in tp_indices,
        ...    print(i)
        ...
        (slice(0, 2, None), slice(None, None, None), slice(0, 2, None))
        (slice(0, 2, None), slice(None, None, None), slice(1, 3, None))
        (slice(0, 2, None), slice(None, None, None), slice(2, 4, None))
        (slice(2, 4, None), slice(None, None, None), slice(0, 2, None))
        (slice(2, 4, None), slice(None, None, None), slice(1, 3, None))
        (slice(2, 4, None), slice(None, None, None), slice(2, 4, None))
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
        tp_ndim = self.source().ndim

        # The indices of the uncompressed array that correspond to
        # each interpolation subarea.
        #
        # .. note:: If a tie point is shared with a previous
        #           interpolation subarea, then that location is
        #           excluded from the index, thereby avoiding any
        #           overlaps.
        u_indices = [(slice(None),)] * tp_ndim

        # The indices of the tie point array that correspond to each
        # interpolation subarea.
        tp_indices = [(slice(None),)] * tp_ndim

        # The shape of each uncompressed interpolated subarea along
        # the interpolated dimensions, excluding the tie point
        # locations defined in previous interpolation subareas.
        interpolation_subarea_shapes = [[n] for n in self.shape]

        # The flags which state, for each dimension, whether (`True`)
        # or not (`False`) an interplation subarea is at the start of
        # a continuous area. Non-interpolated dimensions are given the
        # falsey flag `None`.
        new_continuous_area = [(None,)] * tp_ndim

        # The index of each interpolation subarea along the
        # interpolation subarea dimensions
        interpolation_subarea_indices = [(slice(None),)] * tp_ndim

        for d, tie_point_index in self.get_tie_point_indices().items():
            tp_index = []
            u_index = []
            continuous_area = []
            subarea_shape = []
            interpolation_subarea_index = []

            indices = np.array(tie_point_index).tolist()

            first = True

            # Initialize the count alng the interpolation subarea
            # dimension
            j = 0
            for i, (index0, index1) in enumerate(
                zip(indices[:-1], indices[1:])
            ):
                continuous_area.append(first)

                if index1 - index0 <= 1:
                    first = True
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
                size = index1 - index0 + 1
                if not first:
                    size -= 1

                subarea_shape.append(size)

                # The subspace for this axis of the uncompressed array
                # that corresponds to the interpolation suabrea, only
                # including the first tie point if this the first
                # interpolation subarea in a new continuous area.
                if not first:
                    index0 += 1

                u_index.append(slice(index0, index1 + 1))

                first = False

            tp_indices[d] = tp_index
            u_indices[d] = u_index
            interpolation_subarea_shapes[d] = subarea_shape
            new_continuous_area[d] = continuous_area
            interpolation_subarea_indices[d] = interpolation_subarea_index

        return (
            product(*u_indices),
            product(*interpolation_subarea_shapes),
            product(*tp_indices),
            product(*new_continuous_area),
            product(*interpolation_subarea_indices),
        )

    def to_memory(self):
        """Bring an array on disk into memory.

        There is no change to an array that is already in memory.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Returns:

            `{{class}}`
                The array that is stored in memory.

        """
        super().to_memory()

        for v in self.get_tie_point_indices().values():
            v.data.to_memory()

        for v in self.get_parameters().values():
            v.data.to_memory()

        for v in self.get_dependent_tie_points().values():
            v.data.to_memory()
