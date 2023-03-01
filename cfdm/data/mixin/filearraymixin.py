from ...functions import abspath


class FileArrayMixin:
    """Mixin class for a container of an array. TODOCFADOCS

    .. versionadded:: (cfdm) TODOCFAVER

    """
    def close(self):
        """Close the dataset containing the data."""
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.close"
        )  # pragma: no cover

    def get_address(self):
        """The address in the file of the variable.

        .. versionadded:: (cfdm) TODOCFAVER

        :Returns:

            `str` or `None`
                The address, or `None` if there isn't one.

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.get_address"
        )  # pragma: no cover

    def get_format(self):
        """The TODOCFADOCS in the file of the variable.

        .. versionadded:: (cfdm) TODOCFAVER

        :Returns:

            `str`
                The address, or `None` if there isn't one.

        """
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.get_format"
        )  # pragma: no cover

    def open(self):
        """Returns an open dataset containing the data array."""
        raise NotImplementedError(
            f"Must implement {self.__class__.__name__}.open"
        )  # pragma: no cover
