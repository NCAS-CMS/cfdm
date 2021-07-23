from .. import core
from .mixin import ArrayMixin


class NumpyArray(ArrayMixin, core.NumpyArray):
    """An underlying numpy array.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __getitem__(self, indices):
        """Returns a subspace of the array as a numpy array.

        x.__getitem__(indices) <==> x[indices]

        The indices that define the subspace must be either `Ellipsis`
        or a sequence that contains an index for each dimension. In
        the latter case, each dimension's index must either be a
        `slice` object or a sequence of two or more integers.

        Indexing is similar to numpy indexing. The only difference to
        numpy indexing (given the restrictions on the type of indices
        allowed) is:

          * When two or more dimension's indices are sequences of
            integers then these indices work independently along each
            dimension (similar to the way vector subscripts work in
            Fortran).

        .. versionadded:: (cfdm) 1.7.0

        """
        return self.get_subspace(
            self._get_component("array"), indices, copy=True
        )

    def to_memory(self):
        """Bring an array on disk into memory and retain it there.

        There is no change to an array that is already in memory.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `{{class}}`
                The array that is stored in memory.

        **Examples:**

        >>> b = a.to_memory()

        """
        return self
