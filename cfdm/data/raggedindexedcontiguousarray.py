from builtins import (range, super, zip)

import numpy

from . import abstract


class RaggedIndexedContiguousArray(abstract.CompressedArray):
    '''A container for an indexed contiguous ragged compressed array.

    '''
    def __init__(self, compressed_array=None, shape=None, size=None,
                 ndim=None, elements_per_profile=None,
                 profile_indices=None):
        '''**Initialization**

:Parameters:

    compressed_array: `Array`
        The compressed array.

    shape: `tuple`
        The uncompressed array dimension sizes.

    size: `int`
        Number of elements in the uncompressed array.

    ndim: `int`
        The number of uncompressed array dimensions

    sample_axis: `int`
        The position of the compressed axis in the compressed array.

    elements_per_profile: `Array` or numpy array_like
        The number of elements that each profile has in the compressed
        array.

    profile_indices: `Array` or numpy array_like
        The zero-based indices of the instance to which each profile
        in the compressed array belongs.

        '''
        super().__init__(compressed_array=compressed_array,
                         shape=shape, size=size, ndim=ndim,
                         elements_per_profile=elements_per_profile,
                         profile_indices=profile_indices,
                         sample_axis=0)    
    #--- End: def

    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns an uncompressed subspace of the gathered array as an
independent numpy array.

The indices that define the subspace are relative to the full
uncompressed array and must be either `Ellipsis` or a sequence that
contains an index for each dimension. In the latter case, each
dimension's index must either be a `slice` object or a sequence of
integers.

        '''
        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        
        compressed_array = self.compressed_array

        # Initialise the un-sliced uncompressed array
        uarray = numpy.ma.masked_all(self.shape, dtype=self.dtype)

        elements_per_profile = self.elements_per_profile
        profile_indices      = self.profile_indices.get_array()
        
        # Loop over instances
        for i in range(uarray.shape[0]):
            
            # For all of the profiles in ths instance, find the
            # locations in the elements_per_profile array of the
            # number of elements in the profile
            xprofile_indices = numpy.where(profile_indices == i)[0]
                
            # Find the number of profiles in this instance
            n_profiles = xprofile_indices.size
            
            # Loop over profiles in this instance
            for j in range(uarray.shape[1]):
                if j >= n_profiles:
                    continue
                
                # Find the location in the elements_per_profile array
                # of the number of elements in this profile
                profile_index = xprofile_indices[j]
                
                if profile_index == 0:
                    start = 0
                else:                    
                    start = int(elements_per_profile[:profile_index].sum())
                    
                stop = start + int(elements_per_profile[profile_index])
                
                sample_indices = slice(start, stop)
                
                u_indices = (i, #slice(i, i+1),
                             j, #slice(j, j+1), 
                             slice(0, stop-start)) #slice(0, sample_indices.stop - sample_indices.start))
                
                uarray[u_indices] = compressed_array[sample_indices]
            #--- End: for
        #--- End: for

        return self.get_subspace(uarray, indices, copy=True)
    #--- End: def

#--- End: class
