class CompressedArrayMixin:
    """Mixin class for compressed arrays.

    .. versionadded:: (cfdm) 1.11.2.0

    """

    def to_dask_array(self, chunks="auto"):
        """Convert the data to a `dask` array.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            chunks: `int`, `tuple`, `dict` or `str`, optional
                Specify the chunking of the returned dask array.

                Any value accepted by the *chunks* parameter of the
                `dask.array.from_array` function is allowed.

                The chunk sizes implied by *chunks* for a dimension that
                has been fragmented are ignored and replaced with values
                that are implied by that dimension's fragment sizes.

        :Returns:

            `dask.array.Array`
                The `dask` array representation.

        """
        from functools import partial

        import dask.array as da
        from dask import config
        from dask.base import tokenize

        getter = da.core.getter

        from ..utils import normalize_chunks

        name = (f"{self.__class__.__name__}-{tokenize(self)}",)

        dtype = self.dtype

        context = partial(config.set, scheduler="synchronous")

        conformed_data = self.conformed_data()
        subarray_kwargs = {**conformed_data, **self.subarray_parameters()}

        # Get the (cfdm) subarray class
        Subarray = self.get_Subarray()
        subarray_name = Subarray().__class__.__name__

        # Set the chunk sizes for the dask array
        chunks = normalize_chunks(
            self.subarray_shapes(chunks),
            shape=self.shape,
            dtype=dtype,
        )

        dsk = {}
        for u_indices, u_shape, c_indices, chunk_location in zip(
            *self.subarrays(chunks)
        ):
            subarray = Subarray(
                indices=c_indices,
                shape=u_shape,
                context_manager=context,
                **subarray_kwargs,
            )

            key = f"{subarray_name}-{tokenize(subarray)}"
            dsk[key] = subarray
            dsk[name + chunk_location] = (getter, key, Ellipsis, False, False)

        # Return the dask array
        return da.Array(dsk, name[0], chunks=chunks, dtype=dtype)
