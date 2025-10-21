from copy import deepcopy
from itertools import accumulate, product

import numpy as np
from uritools import isuri, uricompose

from ..functions import dirname
from . import abstract
from .fragment import FragmentFileArray, FragmentUniqueValueArray
from .netcdfindexer import netcdf_indexer
from .utils import chunk_locations, chunk_positions


class AggregatedArray(abstract.FileArray):
    """An array stored in a CF aggregation variable.

    .. versionadded:: (cfdm) 1.12.0.0

    """

    def __new__(cls, *args, **kwargs):
        """Store fragment array classes.

        .. versionadded:: (cfdm) 1.12.0.0

        """
        instance = super().__new__(cls)
        instance._FragmentArray = {
            "uri": FragmentFileArray,
            "unique_value": FragmentUniqueValueArray,
        }
        return instance

    def __init__(
        self,
        filename=None,
        address=None,
        dtype=None,
        mask=True,
        unpack=True,
        fragment_array=None,
        attributes=None,
        storage_options=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            filename: `str`, optional
                The name of the aggregation file containing the
                aaggregation variable.

            address: `str`, optional
                The name of the aggregation variable for the array.

            dtype: `numpy.dtype`
                The data type of the aggregated data array. May be
                `None` if the numpy data-type is not known (which can
                be the case for some string types, for example).

            {{init mask: `bool`, optional}}

            {{init unpack: `bool`, optional}}

            fragment_array: `dict`
                A dictionary representation of the fragment array, in
                either "uri" form::

                   {'map': <'map' fragment variable data>,
                    'uris': <'uris' fragment variable data>,
                    'identifiers': <'identifiers' fragment variable data>}

                or else in "unique_value" form::

                   {'map': <'map' fragment variable data>,
                    'unique_values': <'unique_values' fragment variable data>}

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
        super().__init__(
            filename=filename,
            address=address,
            dtype=dtype,
            mask=True,
            unpack=unpack,
            attributes=attributes,
            storage_options=storage_options,
            source=source,
            copy=copy,
        )

        if source is not None:
            try:
                shape = source.shape
            except AttributeError:
                shape = None

            try:
                fragment_array_shape = source.get_fragment_array_shape()
            except AttributeError:
                fragment_array_shape = None

            try:
                fragment_array = source.get_fragment_array(copy=False)
            except AttributeError:
                fragment_array = {}

            try:
                fragment_type = source.get_fragment_type()
            except AttributeError:
                fragment_type = None
        else:
            if filename is not None:
                (
                    shape,
                    fragment_array_shape,
                    fragment_type,
                    fragment_array,
                ) = self._parse_fragment_array(filename, fragment_array)
            else:
                shape = None
                fragment_array_shape = None
                fragment_array = None
                fragment_type = None

        self._set_component("shape", shape, copy=False)
        self._set_component(
            "fragment_array_shape", fragment_array_shape, copy=False
        )
        self._set_component("fragment_array", fragment_array, copy=False)
        self._set_component("fragment_type", fragment_type, copy=False)

    def __getitem__(self, index):
        """Return a subspace.

        .. versionadded:: (cfdm) 1.12.0.0

        """
        dx = netcdf_indexer(
            self.to_dask_array(),
            mask=True,
            unpack=False,
            always_masked_array=False,
            orthogonal_indexing=True,
            attributes=self.get_attributes(),
            copy=False,
        )
        return dx[index].compute()

    @property
    def __in_memory__(self):
        """True if the array data is in memory.

        .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `bool`

        """
        return False

    def _parse_fragment_array(self, aggregated_filename, fragment_array):
        """Parse the fragment array dictionary.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            aggregated_filename: `str`
                The name of the aggregation file.

            fragment_array: `dict`
               A dictionary representation of the fragment array, in
               either "uri" form::

                  {'map': <'map' fragment variable data>,
                   'uris': <'uris' fragment variable data>,
                   'identifiers': <'identifiers' fragment variable data>}

               or else "unique_value" form::

                  {'map': <'map' fragment variable data>,
                   'unique_values': <'unique_values' fragment variable data>}

        :Returns:

            4-`tuple`
                1. The shape of the aggregated data.
                2. The shape of the array of fragments.
                3. The type of the fragments (either ``'uri'`` or
                   ``'unique_value'``).
                4. The parsed aggregation instructions.

        """
        parsed_fragment_array = {}

        fa_map = fragment_array["map"]
        if fa_map.ndim:
            compressed = np.ma.compressed
            chunks = [compressed(i).tolist() for i in fa_map]
        else:
            # Scalar 'map' variable
            chunks = []

        aggregated_shape = tuple([sum(c) for c in chunks])
        fragment_array_indices = chunk_positions(chunks)
        fragment_shapes = chunk_locations(chunks)

        if "uris" in fragment_array:
            # --------------------------------------------------------
            # Each fragment is in an external dataset, rather than
            # given by a unique value.
            # --------------------------------------------------------
            fragment_type = "uri"
            fa_identifiers = fragment_array["identifiers"]
            fa_uris = fragment_array["uris"]
            fragment_array_shape = fa_uris.shape

            if not fa_identifiers.ndim:
                identifier = fa_identifiers.item()
                scalar = True
            else:
                scalar = False

            for index, shape in zip(fragment_array_indices, fragment_shapes):
                if not scalar:
                    identifier = fa_identifiers[index].item()

                parsed_fragment_array[index] = {
                    "map": shape,
                    "uri": fa_uris[index].item(),
                    "identifier": identifier,
                }
        else:
            # --------------------------------------------------------
            # Each fragment comprises a unique value, rather than
            # being in a file.
            # --------------------------------------------------------
            fragment_type = "unique_value"
            fa_unique_values = fragment_array["unique_values"]
            fragment_array_shape = fa_unique_values.shape
            parsed_fragment_array = {
                index: {
                    "map": shape,
                    "unique_value": fa_unique_values[index].item(),
                }
                for index, shape in zip(
                    fragment_array_indices, fragment_shapes
                )
            }

        return (
            aggregated_shape,
            fragment_array_shape,
            fragment_type,
            parsed_fragment_array,
        )

    def get_fragment_array(self, copy=True):
        """Get the aggregation data dictionary.

        The aggregation data dictionary contains the definitions of
        the fragments and the instructions on how to aggregate them.
        The keys are indices of the fragment array dimensions,
        e.g. ``(1, 0, 0, 0)``.

        .. versionadded:: (cfdm) 1.12.0.0

         .. seealso:: `get_fragment_type`,
                      `get_fragment_array_shape`,
                      `get_fragmented_dimensions`

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
        >>> a.get_fragment_array()
        {(0, 0, 0, 0): {
            'uri': 'January-March.nc',
            'identifier': 'temp',
            'map': [3, 1, 73, 144]}
         (1, 0, 0, 0): {
            'uri': 'April-December.nc',
            'identifier': 'temp',
            'map': [9, 1, 72, 144]}}

        """
        fragment_array = self._get_component("fragment_array")
        if copy:
            fragment_array = deepcopy(fragment_array)

        return fragment_array

    def get_fragment_array_shape(self):
        """Get the sizes of the fragment dimensions.

        The fragment dimension sizes are given in the same order as
        the aggregated dimension sizes given by `shape`.

        .. versionadded:: (cfdm) 1.12.0.0

         .. seealso:: `get_fragment_array`,
                      `get_fragment_type`,
                      `get_fragmented_dimensions`

        :Returns:

            `tuple`
                The shape of the fragment dimensions.

        """
        return self._get_component("fragment_array_shape")

    def get_fragment_type(self):
        """The type of fragments in the fragment array.

        Either ``'uri'`` to indicate that the fragments are files, or
        else ``'unique_value'`` to indicate that they are represented
        by their unique data values.

        .. versionadded:: (cfdm) 1.12.0.0

         .. seealso:: `get_fragment_array`,
                      `get_fragment_array_shape`,
                      `get_fragmented_dimensions`

        :Returns:

            `str`
                The fragment type.

        """
        return self._get_component("fragment_type", None)

    def get_fragmented_dimensions(self):
        """The positions of dimensions spanned by two or more fragments.

        .. versionadded:: (cfdm) 1.12.0.0

         .. seealso:: `get_fragment_array`,
                      `get_fragment_array_shape`,
                      `get_fragment_type`

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

    def subarray_shapes(self, shapes):
        """Create the subarray shapes.

        A fragmented dimenion (i.e. one spanned by two or fragments)
        will always have a subarray size equal to the size of each of
        its fragments, overriding any other size implied by the
        *shapes* parameter.

        .. versionadded:: (cfdm) 1.12.0.0

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
        fragment_array = self.get_fragment_array(copy=False)

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
                    loc = fragment_array[tuple(index)]["map"][dim]
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

        .. versionadded:: (cfdm) 1.12.0.0

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

        .. versionadded:: (cfdm) 1.12.0.0

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
        fragment_array = self.get_fragment_array(copy=False)
        storage_options = self.get_storage_options()
        fragment_type = self.get_fragment_type()
        aggregated_attributes = self.get_attributes()
        unpack = self.get_unpack()

        if fragment_type == "uri":
            # Get the directory of the aggregation file as an absolute
            # URI
            aggregation_file_directory = dirname(self.get_filename())
            if not isuri(aggregation_file_directory):
                aggregation_file_directory = uricompose(
                    scheme="file",
                    authority="",
                    path=aggregation_file_directory,
                )

        # Set the chunk sizes for the dask array
        chunks = self.subarray_shapes(chunks)

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
            kwargs = fragment_array[fragment_index].copy()
            kwargs.pop("map", None)

            if fragment_type == "uri":
                kwargs["filename"] = kwargs.pop("uri")
                kwargs["address"] = kwargs.pop("identifier")
                kwargs["storage_options"] = storage_options
                kwargs["aggregation_file_directory"] = (
                    aggregation_file_directory
                )

            fragment = FragmentArray(
                dtype=dtype,
                shape=fragment_shape,
                unpack_aggregated_data=unpack,
                aggregated_attributes=aggregated_attributes,
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
