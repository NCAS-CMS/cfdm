from copy import deepcopy


class ArrayMixin:
    """Mixin class for a container of an array.

    .. versionadded:: (cfdm) 1.8.7.0

    """

    def __array__(self, *dtype):
        """The numpy array interface.

        .. versionadded:: (cfdm) 1.8.7.0

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
        if not dtype:
            return array
        else:
            return array.astype(dtype[0], copy=False)

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

    def get_attributes(self, default=ValueError()):
        """The attributes of the array.

        .. versionadded:: (cfdm) NEXTVERSION

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
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__} attributes have not yet been set",
            )

        return deepcopy(attributes)

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
