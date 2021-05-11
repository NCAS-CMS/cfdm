class RaggedIndexed:
    """Mixin class for an underlying indexed ragged array."""

    def get_index(self, default=ValueError()):
        """Return the index variable for a compressed array.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                index variable has not been set.

                {{default Exception}}

        :Returns:

                The index variable.

        **Examples:**

        >>> i = d.get_index()

        """
        out = self._get_component("index_variable", None)
        if out is None:
            return self._default(
                default, f"{self.__class__.__name__} has no index variable"
            )

        return out
