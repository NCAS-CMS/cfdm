from .fragmentarraymixin import FragmentArrayMixin


class FragmentFileArrayMixin(FragmentArrayMixin):
    """Mixin class for a fragment of aggregated data in a file.

    .. versionadded:: (cfdm) 1.12.0.0

    """

    def __init__(
        self,
        filename=None,
        address=None,
        dtype=None,
        shape=None,
        filesystem=None,
        backend=None,
        backend_options=None,
        unpack_aggregated_data=True,
        aggregated_attributes=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            filename: (sequence of `str`), optional
                The names of the netCDF fragment files containing the
                array.

            address: (sequence of `str`), optional
                The name of the netCDF variable containing the
                fragment array. Required unless *varid* is set.

            dtype: `numpy.dtype`, optional
                The data type of the aggregated array. May be `None`
                if the numpy data-type is not known (which can be the
                case for netCDF string types, for example). This may
                differ from the data type of the netCDF fragment
                variable.

            shape: `tuple`, optional
                The shape of the fragment within the aggregated
                array. This may differ from the shape of the netCDF
                fragment variable in that the latter may have fewer
                size 1 dimensions.

            {{aggregated_units: `str` or `None`, optional}}

            {{aggregated_calendar: `str` or `None`, optional}}

            {{init filesystem: optional}}

                .. versionadded:: (cfdm) 1.13.3.0

            {{init backend: `None` or (sequence of) `str`, optional}}

                .. versionadded:: (cfdm) 1.13.3.0

            {{init backend_options: `None` or `dict`, optional}}

                .. versionadded:: (cfdm) 1.13.3.0

            {{init source: optional}}

            {{init copy: `bool`, optional}}

            storage_options: Deprecated at version 1.13.3.0
                Use *filesystem* intesad.

        """
        super().__init__(
            filename=filename,
            address=address,
            dtype=dtype,
            shape=shape,
            mask=True,
            unpack=True,
            attributes=None,
            filesystem=filesystem,
            backend=backend,
            backend_options=backend_options,
            source=source,
            copy=copy,
        )

        if source is not None:
            try:
                aggregated_attributes = source._get_component(
                    "aggregated_attributes", None
                )
            except AttributeError:
                aggregated_attributes = None

            try:
                unpack_aggregated_data = source._get_component(
                    "unpack_aggregated_data", True
                )
            except AttributeError:
                unpack_aggregated_data = True

        self._set_component(
            "unpack_aggregated_data",
            unpack_aggregated_data,
            copy=False,
        )
        self._set_component(
            "aggregated_attributes", aggregated_attributes, copy=False
        )
