from builtins import super

from . import abstract


from ..structure.data import NumpyArray as structure_NumpyArray


class NumpyArray(abstract.Array, structure_NumpyArray):
    '''A container for a numpy array.

    '''
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a subspace of the array as an independent numpy array.

The indices that define the subspace must be either `Ellipsis` or a
sequence that contains an index for each dimension. In the latter
case, each dimension's index must either be a `slice` object or a
sequence of integers.

        '''
        return self.get_subspace(self.array, indices, copy=True)
    #--- End: def

#--- End: class
