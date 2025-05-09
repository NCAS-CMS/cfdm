from math import prod

import numpy as np

from ....units import Units
from ...netcdfindexer import netcdf_indexer


class FragmentArrayMixin:
    """Mixin class for a fragment of aggregated data.

    .. versionadded:: (cfdm) 1.12.0.0

    """

    def _get_array(self, index=None):
        """Returns a subspace of the dataset variable.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `__array__`, `index`

        :Parameters:

            {{index: `tuple` or `None`, optional}}

               It is important that there is a distinct value for each
               fragment dimension, which is guaranteed when the
               default of the `index` attribute is being used.

        :Returns:

            `numpy.ndarray`
                The subspace.

        """
        if index is None:
            index = self.index()

        try:
            array = super()._get_array(index)
        except ValueError:
            # A ValueError is expected to be raised when the fragment
            # variable has fewer than 'self.ndim' dimensions (we know
            # that this is the case because 'index' has 'self.ndim'
            # elements).
            axis = self._size_1_axis()  # index)
            if axis is not None:
                # There is a unique size 1 index that must correspond
                # to the missing dimension => Remove it from the
                # indices, get the fragment array with the new
                # indices; and then insert the missing size one
                # dimension.
                index = list(index)
                index.pop(axis)
                array = super()._get_array(tuple(index))
                array = np.expand_dims(array, axis)
            else:
                # There are multiple size 1 indices so we don't know
                # how many missing dimensions the fragment has, nor
                # their positions => Get the full fragment array and
                # then reshape it to the shape of the dask compute
                # chunk; and then apply the index.
                array = super()._get_array(Ellipsis)
                if array.size > prod(self.original_shape):
                    raise ValueError(
                        f"Can't get fragment data from ({self}) when "
                        "the fragment has two or more missing size 1 "
                        "dimensions, whilst also spanning two or more "
                        "Dask compute chunks."
                        "\n\n"
                        "Consider re-creating the data with exactly one "
                        "Dask compute chunk per fragment (e.g. by setting "
                        "'chunks=None' as a keyword to cf.read)."
                    )

                array = array.reshape(self.original_shape)
                array = array[index]

        array = self._conform_to_aggregated_units(array)

        # Apply any unpacking deinfed on the aggregation variable. Do
        # this after conforming the units.
        array = self._unpack_aggregated_data(array)

        return array

    def _conform_to_aggregated_units(self, array):
        """Conform the array to have the aggregated units.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            array: `numpy.ndarray` or `dict`
                The array to be conformed. If *array* is a `dict` with
                `numpy` array values then selected values are
                conformed.

        :Returns:

            `numpy.ndarray` or `dict`
                The conformed array. The returned array may or may not
                be the input array updated in-place, depending on its
                data type and the nature of its units and the
                aggregated units.

                If *array* is a `dict` then a dictionary of conformed
                arrays is returned.

        """
        units = self.Units
        if units:
            aggregated_units = self.aggregated_Units
            if not units.equivalent(aggregated_units):
                raise ValueError(
                    f"Can't convert fragment data with units {units!r} to "
                    f"have aggregated units {aggregated_units!r}"
                )

            if units != aggregated_units:
                if isinstance(array, dict):
                    # 'array' is a dictionary.
                    raise ValueError(
                        "TODOACTIVE. Placeholder notification thatn "
                        "we can't yet dealing with active "
                        "storage reductions on fragments."
                    )
                else:
                    # 'array' is a numpy array
                    array = Units.conform(
                        array, units, aggregated_units, inplace=True
                    )

        return array

    def _size_1_axis(self):  # , indices):
        """Find the position of a unique size 1 index.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `_parse_indices`, `__getitem__`

        :Parameters:

            indices: sequence of index
                The array indices to be parsed, as returned by
                `_parse_indices`.

        :Returns:

            `int` or `None`
                The position of the unique size 1 index, or `None` if
                there are zero or at least two of them.

        **Examples**

        >>> a._size_1_axis(([2, 4, 5], slice(0, 1), slice(0, 73)))
        1
        >>> a._size_1_axis(([2, 4, 5], slice(3, 4), slice(0, 73)))
        1
        >>> a._size_1_axis(([2, 4, 5], [0], slice(0, 73)))
        1
        >>> a._size_1_axis(([2, 4, 5], slice(0, 144), slice(0, 73)))
        None
        >>> a._size_1_axis(([2, 4, 5], slice(3, 7), [0, 1]))
        None
        >>> a._size_1_axis(([2, 4, 5], slice(0, 1), [0]))
        None

        """
        original_shape = self.original_shape
        if original_shape.count(1):
            return original_shape.index(1)

        return

    def _unpack_aggregated_data(self, array):
        """Unpack the canonical data, if requested.

        .. versionadded:: (cfdm) 1.12.0.0

        """
        if self.get_unpack_aggregated_data():
            array = netcdf_indexer(
                array,
                mask=False,
                unpack=True,
                attributes=self.get_aggregated_attributes(),
                copy=False,
            )[...]

        return array

    @property
    def aggregated_Units(self):
        """The units of the aggregated data.

        .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `Units`
                The units of the aggregated data.

        """
        aggregated_attributes = self.get_aggregated_attributes(copy=False)
        calendar = aggregated_attributes.get("calendar", None)
        units = aggregated_attributes.get("units", None)
        return Units(units, calendar)

    def get_aggregated_attributes(self, copy=True):
        """The calendar of the aggregated array.

        If the calendar is `None` then the CF default calendar is
        assumed, if applicable.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                aggregated calendar has not been set. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `str` or `None`
                The calendar value.

        """
        attributes = self._get_component("aggregated_attributes")
        return attributes.copy()

    def get_unpack_aggregated_data(self):
        """Whether or not to unpack the canonical data.

        If `True` and there are aggregated variable packing
        attributes, then the array is unpacked according to those
        attributes.

        .. versionadded:: (cfdm) 1.12.0.0

        **Examples**

        >>> a.get_unpack_aggregated_data()
        True

        """
        return self._get_component("unpack_aggregated_data")
