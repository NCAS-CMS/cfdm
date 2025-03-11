from ..fullarray import FullArray
from .mixin import FragmentArrayMixin


class FragmentUniqueValueArray(FragmentArrayMixin, FullArray):
    """A fragment of aggregated data that has a single unique value.

    .. versionadded:: (cfdm) 1.12.0.0

    """

    def __init__(
        self,
        unique_value=None,
        dtype=None,
        shape=None,
        unpack_aggregated_data=True,
        aggregated_attributes=None,
        attributes=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            unique_value: scalar
                The unique value for the fragment.

            dtype: `numpy.dtype`
                The data type of the aggregated array. May be `None`
                if the numpy data-type is not known (which can be the
                case for netCDF string types, for example). This may
                differ from the data type of the netCDF fragment
                variable.

            shape: `tuple`
                The shape of the fragment within the aggregated
                array. This may differ from the shape of the netCDF
                fragment variable in that the latter may have fewer
                size 1 dimensions.

            {{init attributes: `dict` or `None`, optional}}

            {{aggregated_units: `str` or `None`, optional}}

            {{aggregated_calendar: `str` or `None`, optional}}

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(
            fill_value=unique_value,
            dtype=dtype,
            shape=shape,
            attributes=None,
            source=source,
            copy=False,
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
        if aggregated_attributes is not None:
            self._set_component(
                "aggregated_attributes", aggregated_attributes, copy=copy
            )
