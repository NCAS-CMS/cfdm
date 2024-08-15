from copy import deepcopy
from itertools import accumulate, product

import numpy as np

from ..utils import chunk_locations, chunk_positions


class CFAMixin:
    """Mixin class for a CFA array.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def __new__(cls, *args, **kwargs):
        """Store fragment array classes.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        # Import fragment array classes. Do this here (as opposed to
        # outside the class) to avoid a circular import.
        from ...fragment import FragmentFileArray, FragmentValueArray

        instance = super().__new__(cls)
        instance._FragmentArray = {
            "location": FragmentFileArray,
            "value": FragmentValueArray,
        }
        return instance

    def __init__(
        self,
        filename=None,
        address=None,
        dtype=None,
        mask=True,
        unpack=True,
        instructions=None,
        substitutions=None,
        attributes=None,
        storage_options=None,
        source=None,
        copy=True,
        x=None,
    ):
        """**Initialisation**

        :Parameters:

            filename: (sequence of) `str`, optional
                The name of the CFA file containing the array. If a
                sequence then it must contain one element.

            address: (sequence of) `str`, optional
                The name of the CFA aggregation variable for the
                array. If a sequence then it must contain one element.

            dtype: `numpy.dtype`
                The data type of the aggregated data array. May be
                `None` if the numpy data-type is not known (which can
                be the case for some string types, for example).

            mask: `bool`
                If True (the default) then mask by convention when
                reading data from disk.

                A array is masked depending on the values of any of
                the variable attributes ``valid_min``, ``valid_max``,
                ``valid_range``, ``_FillValue`` and ``missing_value``.

            {{init unpack: `bool`, optional}}

            instructions: `str`, optional
                The ``aggregated_data`` attribute value as found on
                the CFA variable. If set then this will be used to
                improve the performance of `__dask_tokenize__`.

            substitutions: `dict`, optional
                A dictionary whose key/value pairs define text
                substitutions to be applied to the fragment file
                names. Each key must be specified with the ``${...}``
                syntax, for instance ``{'${base}': 'sub'}``.

            storage_options: `dict` or `None`, optional
                Key/value pairs to be passed on to the creation of
                `s3fs.S3FileSystem` file systems to control the
                opening of fragment files in S3 object stores. Ignored
                for files not in an S3 object store, i.e. those whose
                names do not start with ``s3:``.

                By default, or if `None`, then *storage_options* is
                taken as ``{}``.

                If the ``'endpoint_url'`` key is not in
                *storage_options* or is not in a dictionary defined by
                the ``'client_kwargs`` key (which is always the case
                when *storage_options* is `None`), then one will be
                automatically inserted for accessing a fragment S3
                file. For example, for a file name of
                ``'s3://store/data/file.nc'``, an ``'endpoint_url'``
                key with value ``'https://store'`` would be created.

                *Parameter example:*
                  ``{'key: 'scaleway-api-key...', 'secret':
                  'scaleway-secretkey...', 'endpoint_url':
                  'https://s3.fr-par.scw.cloud', 'client_kwargs':
                  {'region_name': 'fr-par'}}``

            {{init attributes: `dict` or `None`, optional}}

                If *attributes* is `None`, the default, then the
                attributes will be set from the netCDF variable during
                the first `__getitem__` call.

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        if source is not None:
            super().__init__(source=source, copy=copy)

            try:
                fragment_array_shape = source.get_fragment_array_shape()
            except AttributeError:
                fragment_array_shape = None

            try:
                instructions = source._get_component("instructions")
            except AttributeError:
                instructions = None

            try:
                aggregated_data = source.get_aggregated_data(copy=False)
            except AttributeError:
                aggregated_data = {}

            try:
                substitutions = source.get_substitutions()
            except AttributeError:
                substitutions = None

        elif filename is not None:
            shape, fragment_array_shape, fragment_type, aggregated_data = (
                self._parse_cfa(x, substitutions)
            )
            super().__init__(
                filename=filename,
                address=address,
                shape=shape,
                dtype=dtype,
                mask=mask,
                attributes=attributes,
                copy=copy,
            )
        else:
            super().__init__(
                filename=filename,
                address=address,
                dtype=dtype,
                mask=mask,
                attributes=attributes,
                copy=copy,
            )

            fragment_array_shape = None
            aggregated_data = None
            fragment_type = None
            instructions = None

        self._set_component(
            "fragment_array_shape", fragment_array_shape, copy=False
        )
        self._set_component("aggregated_data", aggregated_data, copy=False)
        self._set_component("instructions", instructions, copy=False)
        self._set_component("fragment_type", fragment_type, copy=False)

        print ('init', fragment_type)
        
        if substitutions is not None:
            self._set_component(
                "substitutions", substitutions.copy(), copy=False
            )

    def _parse_cfa(self, x, substitutions):
        """Parse the CFA aggregation instructions.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            x: `dict`

            substitutions: `dict` or `None`
                A dictionary whose key/value pairs define text
                substitutions to be applied to the fragment file
                names. Each key must be specified with the ``${...}``
                syntax, for instance ``{'${base}': 'sub'}``.

        :Returns:

            4-`tuple`
                1. The shape of the aggregated data.
                2. The shape of the array of fragments.
                3. The type of the fragments (either ``"value"`` or
                   ``"location"``).
                4. The parsed aggregation instructions.

        """
        aggregated_data = {}

        location = x["location"]
        ndim = location.shape[0]
        compressed = np.ma.compressed
        chunks = [compressed(i).tolist() for i in location]
        aggregated_shape = [sum(c) for c in chunks]
        fragment_array_indices = chunk_positions(chunks)
        fragment_shapes = chunk_locations(chunks)

        if "value" in x:
            # --------------------------------------------------------
            # Each fragment contains a constant value, not file
            # locations.
            # --------------------------------------------------------
            fragment_type = "value"
            value = x["value"]
            fragment_array_shape = value.shape
            aggregated_data = {
                index: {
                    "shape": shape,
                    "value": value[index].item(),
                }
                for index, shape in zip(
                    fragment_array_indices, fragment_shapes
                )
            }
        else:
            # --------------------------------------------------------
            # Each fragment contains file locations
            # --------------------------------------------------------
            fragment_type = "location"
            a = x["address"]
            f = x["location"]

            extra_dimension = f.ndim > ndim
            if extra_dimension:
                # There is an extra non-fragment dimension
                fragment_array_shape = f.shape[:-1]
            else:
                fragment_array_shape = f.shape

            if not a.ndim:
                a = (a.item(),)
                scalar_address = True
            else:
                scalar_address = False

            for index, shape in zip(fragment_array_indices, fragment_shapes):
                if extra_dimension:
                    location = compressed(f[index]).tolist()
                    if scalar_address:
                        address = a * len(location)
                    else:
                        address = compressed(a[index].tolist())
                else:
                    location = (f[index].item(),)
                    if scalar_address:
                        address = a
                    else:
                        address = (a[index].item(),)

                aggregated_data[index] = {
                    "shape": shape,
                    "location": location,
                    "address": address,
                }

            # Apply string substitutions to the fragment filenames
            if substitutions:
                for value in aggregated_data.values():
                    location = []
                    for filename in value["location"]:
                        for base, sub in substitutions.items():
                            filename = filename.replace(base, sub)

                        location.append(filename)

                    value["location"] = location

        return (
            aggregated_shape,
            fragment_array_shape,
            fragment_type,
            aggregated_data,
        )

    def __dask_tokenize__(self):
        """Used by `dask.base.tokenize`.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        out = super().__dask_tokenize__()
        aggregated_data = self._get_component("instructions", None)
        if aggregated_data is None:
            aggregated_data = self.get_aggregated_data(copy=False)

        return out + (aggregated_data,)

    def __getitem__(self, indices):
        """x.__getitem__(indices) <==> x[indices]"""
        return NotImplemented  # pragma: no cover

    def get_aggregated_data(self, copy=True):
        """Get the aggregation data dictionary.

        The aggregation data dictionary contains the definitions of
        the fragments and the instructions on how to aggregate them.
        The keys are indices of the CFA fragment dimensions,
        e.g. ``(1, 0, 0 ,0)``.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            copy: `bool`, optional
                Whether or not to return a copy of the aggregation
                dictionary. By default a deep copy is returned.

                .. warning:: If False then changing the returned
                             dictionary in-place will change the
                             aggregation dictionary stored in the
                             {{class}} instance, **as well as in any
                             copies of it**.

        :Returns:

            `dict`
                The aggregation data dictionary.

        **Examples**

        >>> a.shape
        (12, 1, 73, 144)
        >>> a.get_fragment_array_shape()
        (2, 1, 1, 1)
        >>> a.get_aggregated_data()
        {(0, 0, 0, 0): {
          'file': ('January-June.nc',),
          'address': ('temp',),
          'format': 'nc',
          'location': [(0, 6), (0, 1), (0, 73), (0, 144)]},
         (1, 0, 0, 0): {
          'file': ('July-December.nc',),
          'address': ('temp',),
          'format': 'nc',
          'location': [(6, 12), (0, 1), (0, 73), (0, 144)]}}

        """
        aggregated_data = self._get_component("aggregated_data")
        if copy:
            aggregated_data = deepcopy(aggregated_data)

        return aggregated_data

    def get_fragmented_dimensions(self):
        """Get the positions of dimensions that have two or more
        fragments.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `list`
                The dimension positions.

        **Examples**

        >>> a.get_fragment_array_shape()
        (20, 1, 40, 1)
        >>> a.get_fragmented_dimensions()
        [0, 2]

        >>> a.get_fragment_array_shape()
        (1, 1, 1)
        >>> a.get_fragmented_dimensions()
        []

        """
        return [
            i
            for i, size in enumerate(self.get_fragment_array_shape())
            if size > 1
        ]

    def get_fragment_array_shape(self):
        """Get the sizes of the fragment dimensions.

        The fragment dimension sizes are given in the same order as
        the aggregated dimension sizes given by `shape`.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `tuple`
                The shape of the fragment dimensions.

        """
        return self._get_component("fragment_array_shape")

    def get_fragment_type(self):
        """TODOCFA.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `str`
                TODOCFA

        """
        return self._get_component("fragment_type", None)

    def get_storage_options(self):
        """Return `s3fs.S3FileSystem` options for accessing S3 fragment
        files.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `dict` or `None`
                The `s3fs.S3FileSystem` options.

        **Examples**

        >>> f.get_storage_options()
        {}

        >>> f.get_storage_options()
        {'anon': True}

        >>> f.get_storage_options()
        {'key: 'scaleway-api-key...',
         'secret': 'scaleway-secretkey...',
         'endpoint_url': 'https://s3.fr-par.scw.cloud',
         'client_kwargs': {'region_name': 'fr-par'}}

        """
        return super().get_storage_options(create_endpoint_url=False)

    def subarray_shapes(self, shapes):
        """Create the subarray shapes.

        A fragmented dimenion (i.e. one spanned by two or fragments)
        will always have a subarray size equal to the size of each of
        its fragments, overriding any other size implied by the
        *shapes* parameter.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `subarrays`

        :Parameters:

            shapes: `int`, sequence, `dict` or `str`, optional
                Define the subarray shapes.

                Any value accepted by the *chunks* parameter of the
                `dask.array.from_array` function is allowed.

                The subarray sizes implied by *chunks* for a dimension
                that has been fragmented are ignored, so their
                specification is arbitrary.

        :Returns:

            `tuple`
                The subarray sizes along each dimension.

        **Examples**

        >>> a.shape
        (12, 1, 73, 144)
        >>> a.get_fragment_array_shape()
        (2, 1, 1, 1)
        >>> a.fragmented_dimensions()
        [0]
        >>> a.subarray_shapes(-1)
        ((6, 6), (1,), (73,), (144,))
        >>> a.subarray_shapes(None)
        ((6, 6), (1,), (73,), (144,))
        >>> a.subarray_shapes("auto")
        ((6, 6), (1,), (73,), (144,))
        >>> a.subarray_shapes((None, 1, 40, 50))
        ((6, 6), (1,), (40, 33), (50, 50, 44))
        >>>  a.subarray_shapes((None, None, "auto", 50))
        ((6, 6), (1,), (73,), (50, 50, 44))
        >>>  a.subarray_shapes({2: 40})
        ((6, 6), (1,), (40, 33), (144,))

        """
        from numbers import Number

        from dask.array.core import normalize_chunks

        # Positions of fragmented dimensions (i.e. those spanned by
        # two or more fragments)
        f_dims = self.get_fragmented_dimensions()

        shape = self.shape
        aggregated_data = self.get_aggregated_data(copy=False)

        # Create the base chunks.
        chunks = []
        ndim = self.ndim
        for dim, (n_fragments, size) in enumerate(
            zip(self.get_fragment_array_shape(), self.shape)
        ):
            if dim in f_dims:
                # This aggregated dimension is spanned by two or more
                # fragments => set the chunks to be the same size as
                # the each fragment.
                c = []
                index = [0] * ndim
                for j in range(n_fragments):
                    index[dim] = j
                    loc = aggregated_data[tuple(index)]["location"][dim]
                    chunk_size = loc[1] - loc[0]
                    c.append(chunk_size)

                chunks.append(tuple(c))
            else:
                # This aggregated dimension is spanned by exactly one
                # fragment => store `None` for now. This will get
                # overwritten from 'shapes'.
                chunks.append(None)

        if isinstance(shapes, (str, Number)) or shapes is None:
            chunks = [
                c if i in f_dims else shapes for i, c in enumerate(chunks)
            ]
        elif isinstance(shapes, dict):
            chunks = [
                chunks[i] if i in f_dims else shapes.get(i, "auto")
                for i, c in enumerate(chunks)
            ]
        else:
            # chunks is a sequence
            if len(shapes) != ndim:
                raise ValueError(
                    f"Wrong number of 'shapes' elements in {shapes}: "
                    f"Got {len(shapes)}, expected {self.ndim}"
                )

            chunks = [
                c if i in f_dims else shapes[i] for i, c in enumerate(chunks)
            ]

        return normalize_chunks(chunks, shape=shape, dtype=self.dtype)

    def subarrays(self, subarray_shapes):
        """Return descriptors for every subarray.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `subarray_shapes`

        :Parameters:

            subarray_shapes: `tuple`
                The subarray sizes along each dimension, as returned
                by a prior call to `subarray_shapes`.

        :Returns:

            6-`tuple` of iterators
               Each iterator iterates over a particular descriptor
               from each subarray.

               1. The indices of the aggregated array that correspond
                  to each subarray.

               2. The shape of each subarray.

               3. The indices of the fragment that corresponds to each
                  subarray (some subarrays may be represented by a
                  part of a fragment).

               4. The location of each subarray.

               5. The location on the fragment dimensions of the
                  fragment that corresponds to each subarray.

               6. The shape of each fragment that overlaps each chunk.

        **Examples**

        An aggregated array with shape (12, 73, 144) has two
        fragments, both with with shape (6, 73, 144).

        >>> a.shape
        (12, 73, 144)
        >>> a.get_fragment_array_shape()
        (2, 1, 1)
        >>> a.fragmented_dimensions()
        [0]
        >>> subarray_shapes = a.subarray_shapes({1: 40})
        >>> print(subarray_shapes)
        ((6, 6), (40, 33), (144,))
        >>> (
        ...  u_indices,
        ...  u_shapes,
        ...  f_indices,
        ...  s_locations,
        ...  f_locations,
        ...  f_shapes,
        ... ) = a.subarrays(subarray_shapes)
        >>> for i in u_indices:
        ...    print(i)
        ...
        (slice(0, 6, None), slice(0, 40, None), slice(0, 144, None))
        (slice(0, 6, None), slice(40, 73, None), slice(0, 144, None))
        (slice(6, 12, None), slice(0, 40, None), slice(0, 144, None))
        (slice(6, 12, None), slice(40, 73, None), slice(0, 144, None))

        >>> for i in u_shapes
        ...    print(i)
        ...
        (6, 40, 144)
        (6, 33, 144)
        (6, 40, 144)
        (6, 33, 144)
        >>> for i in f_indices:
        ...    print(i)
        ...
        (slice(None, None, None), slice(0, 40, None), slice(0, 144, None))
        (slice(None, None, None), slice(40, 73, None), slice(0, 144, None))
        (slice(None, None, None), slice(0, 40, None), slice(0, 144, None))
        (slice(None, None, None), slice(40, 73, None), slice(0, 144, None))
        >>> for i in s_locations:
        ...    print(i)
        ...
        (0, 0, 0)
        (0, 1, 0)
        (1, 0, 0)
        (1, 1, 0)
        >>> for i in f_locations:
        ...    print(i)
        ...
        (0, 0, 0)
        (0, 0, 0)
        (1, 0, 0)
        (1, 0, 0)
        >>> for i in f_shapes:
        ...    print(i)
        ...
        (6, 73, 144)
        (6, 73, 144)
        (6, 73, 144)
        (6, 73, 144)

        """
        f_dims = self.get_fragmented_dimensions()

        # The indices of the uncompressed array that correspond to
        # each subarray, the shape of each uncompressed subarray, and
        # the location of each subarray
        s_locations = []
        u_shapes = []
        u_indices = []
        f_locations = []
        for dim, c in enumerate(subarray_shapes):
            nc = len(c)
            s_locations.append(tuple(range(nc)))
            u_shapes.append(c)

            if dim in f_dims:
                f_locations.append(tuple(range(nc)))
            else:
                # No fragmentation along this dimension
                f_locations.append((0,) * nc)

            c = tuple(accumulate((0,) + c))
            u_indices.append([slice(i, j) for i, j in zip(c[:-1], c[1:])])

        # For each subarray, the part of the fragment that corresponds
        # to it.
        f_indices = [
            (slice(None),) * len(u) if dim in f_dims else u
            for dim, u in enumerate(u_indices)
        ]

        # For each subarray, the shape of the fragment that
        # corresponds to it.
        f_shapes = [
            u_shape if dim in f_dims else (size,) * len(u_shape)
            for dim, (u_shape, size) in enumerate(zip(u_shapes, self.shape))
        ]

        return (
            product(*u_indices),
            product(*u_shapes),
            product(*f_indices),
            product(*s_locations),
            product(*f_locations),
            product(*f_shapes),
        )

    def to_dask_array(self, chunks="auto"):
        """Create a dask array with `FragmentArray` chunks.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            chunks: `int`, `tuple`, `dict` or `str`, optional
                Specify the chunking of the returned dask array.

                Any value accepted by the *chunks* parameter of the
                `dask.array.from_array` function is allowed.

                The chunk sizes implied by *chunks* for a dimension that
                has been fragmented are ignored and replaced with values
                that are implied by that dimensions fragment sizes.

        :Returns:

            `dask.array.Array`

        """
        import dask.array as da
        from dask.array.core import getter
        from dask.base import tokenize

        name = (f"{self.__class__.__name__}-{tokenize(self)}",)

        dtype = self.dtype
        units = self.get_units(None)
        calendar = self.get_calendar(None)
        aggregated_data = self.get_aggregated_data(copy=False)

        # Set the chunk sizes for the dask array
        chunks = self.subarray_shapes(chunks)

        storage_options = self.get_storage_options()

        fragment_type = self.get_fragment_type()
        try:
            FragmentArray = self._FragmentArray[fragment_type]
        except KeyError:
            raise ValueError(
                "Can't get fragment array class for unknown "
                f"fragment type: {fragment_type!r}"
            )

        dsk = {}
        for (
            u_indices,
            u_shape,
            f_indices,
            chunk_index,
            fragment_index,
            fragment_shape,
        ) in zip(*self.subarrays(chunks)):
            kwargs = aggregated_data[fragment_index].copy()
            kwargs.pop("shape", None)

            if storage_options and fragment_type == "location":
                kwargs["storage_options"] = storage_options

            fragment = FragmentArray(
                dtype=dtype,
                shape=fragment_shape,
                aggregated_units=units,
                aggregated_calendar=calendar,
                **kwargs,
            )

            key = f"{fragment.__class__.__name__}-{tokenize(fragment)}"
            dsk[key] = fragment
            dsk[name + chunk_index] = (
                getter,
                key,
                f_indices,
                False,
                False,
            )

        # Return the dask array
        return da.Array(dsk, name[0], chunks=chunks, dtype=dtype)
