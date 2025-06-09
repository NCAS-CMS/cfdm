from copy import deepcopy

import numpy as np
from cfunits import Units


class ArrayMixin:
    """Mixin class for a container of an array.

    .. versionadded:: (cfdm) 1.11.2.0

    """

    # Functions handled by __array_function__ implementations (numpy
    # NEP 18)
    _HANDLED_FUNCTIONS = {}

    def __array__(self, dtype=None, copy=None):
        """The numpy array interface.

        .. versionadded:: (cfdm) 1.8.7.0

        :Parameters:

            dtype: optional
                Typecode or data-type to which the array is cast.

            copy: `None` or `bool`
                Included to match the v2 `numpy.ndarray.__array__`
                API, but ignored. The return numpy array is always
                independent.

                .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples**

        >>> isinstance(a, Array)
        True
        >>> n = numpy.asanyarray(a)
        >>> isinstance(n, numpy.ndarray)
        True

        """
        array = self.array
        if dtype is None:
            return array

        return array.astype(dtype, copy=False)

    def __array_function__(self, func, types, args, kwargs):
        """Implement the `numpy` ``__array_function__`` protocol.

        See numpy NEP 18 for details.

        .. versionadded:: (cfdm) 1.11.2.0

        """
        if func not in self._HANDLED_FUNCTIONS:
            return NotImplemented

        # Note: This allows subclasses that don't override
        #       __array_function__ to handle Array objects
        if not all(issubclass(t, self.__class__) for t in types):
            return NotImplemented

        return self._HANDLED_FUNCTIONS[func](*args, **kwargs)

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed subarray.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed subarray as an
        independent numpy array.

        .. versionadded:: (cfdm) 1.8.7.0

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.__getitem__"
        )  # pragma: no cover

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        .. versionadded:: (cfdm) 1.8.7.0

        """
        return f"<{self.__class__.__name__}{self.shape}: {self}>"

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        .. versionadded:: (cfdm) 1.8.7.0

        """
        return f"shape={self.shape}, dtype={self.dtype}"

    def __docstring_package_depth__(self):
        """Returns the package depth for {{package}} substitutions.

        See `_docstring_package_depth` for details.

        """
        return 0

    @property
    def _meta(self):
        """Normalize the array to an appropriate Dask meta object.

        The Dask meta can be thought of as a suggestion to Dask. Dask
        uses this meta to generate the task graph until it can infer
        the actual metadata from the values. It does not force the
        output to have the structure or dtype of the specified meta.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `dask.utils.meta_from_array`

        """
        return np.array((), dtype=self.dtype)

    @property
    def Units(self):
        """The `Units` object containing the units of the array.

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return Units(self.get_units(None), self.get_calendar(None))

    def astype(self, dtype, **kwargs):
        """Cast the data to a specified type.

        .. versionadded:: (cfdm) 1.12.1.0

        :Parameters:

            dtype: `str` or dtype
                Typecode or data-type to which the array is cast.

            kwargs: optional
                Any other keywords accepted by `np.astype`.

        :Returns:

            `np.ndarray`
                The data with the new data type

        """
        kwargs["copy"] = False
        return self.array.astype(dtype, **kwargs)

    def get_attributes(self, copy=True):
        """The attributes of the array.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                attributes have not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

            `dict`
                The attributes.

        """
        attributes = self._get_component("attributes", None)
        if attributes is None:
            attributes = {}
        elif copy:
            attributes = deepcopy(attributes)

        return attributes

    def get_calendar(self, default=ValueError()):
        """The calendar of the array.

        If the calendar is `None` then the CF default calendar is
        assumed, if applicable.

        .. versionadded:: (cfdm) 1.10.0.1

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                calendar has not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

            `str` or `None`
                The calendar value.

        """
        attributes = self.get_attributes({})
        if "calendar" not in attributes:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__} 'calendar' has not been set",
            )

        return attributes["calendar"]

    def get_compression_type(self):
        """Returns the array's compression type.

        Specifically, returns the type of compression that has been
        applied to the underlying array.

        .. versionadded:: (cfdm) 1.8.7.0

        :Returns:

            `str`
                The compression type. An empty string means that no
                compression has been applied.

        **Examples**

        >>> a.compression_type
        ''

        >>> a.compression_type
        'gathered'

        >>> a.compression_type
        'ragged contiguous'

        """
        return self._get_component("compression_type", "")

    def get_units(self, default=ValueError()):
        """The units of the array.

        If the units are `None` then the array has no defined units.

        .. versionadded:: (cfdm) 1.10.0.1

        .. seealso:: `get_calendar`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                units have not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

            `str` or `None`
                The units value.

        """
        attributes = self.get_attributes({})
        if "units" not in attributes:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__} 'units' have not been set",
            )

        return attributes["units"]


# --------------------------------------------------------------------
# __array_function__ implementations (numpy NEP 18)
# --------------------------------------------------------------------
def array_implements(cls, numpy_function):
    """Decorator for __array_function__ implementations.

    .. versionadded:: (cfdm) 1.12.0.0

    """

    def decorator(func):
        cls._HANDLED_FUNCTIONS[numpy_function] = func
        return func

    return decorator


# Implementationing np.concatenate is necessary for some use cases of
# `dask.array.slicing.take`
@array_implements(ArrayMixin, np.concatenate)
def concatenate(arrays, axis=0):
    """Version of `np.concatenate` that works for `Array` objects.

    .. versionadded:: (cfdm) 1.12.0.0

    """
    # Convert the inputs to numpy arrays, and concatenate those.
    return np.ma.concatenate(tuple(map(np.asanyarray, arrays)), axis=axis)
