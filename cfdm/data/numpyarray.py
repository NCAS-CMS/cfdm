from . import abstract

from ..core.data import NumpyArray as core_NumpyArray


class NumpyArray(abstract.Array, core_NumpyArray):
    '''An underlying numpy array.

    '''
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

    Returns a subspace of the array as an independent numpy array.

    The indices that define the subspace must be either `Ellipsis` or
    a sequence that contains an index for each dimension. In the
    latter case, each dimension's index must either be a `slice`
    object or a sequence of two or more integers.

    Indexing is similar to numpy indexing. The only difference to
    numpy indexing (given the restrictions on the type of indices
    allowed) is:

      * When two or more dimension's indices are sequences of integers
        then these indices work independently along each dimension
        (similar to the way vector subscripts work in Fortran).

    .. versionadded:: 1.7.0

        '''
        return self.get_subspace(self._get_component('array'), indices,
                                 copy=True)

    def to_memory(self):
        '''TODO
        '''
        return self

# --- End: class
