from builtins import (range, super, zip)

import numpy

from . import abstract


class RaggedIndexedContiguousArray(abstract.CompressedArray):
    '''

    '''
    def __init__(self, array=None, shape=None, size=None, ndim=None,
                 elements_per_profile=None, profile_indices=None):
        '''**Initialization**

:Parameters:

    array: `abstract.Array`

        '''
        super().__init__(array=array, shape=shape, size=size,
                         ndim=ndim,
                         elements_per_profile=elements_per_profile,
                         profile_indices=profile_indices)    
    #--- End: def

    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a numpy array that does not share memory with the compressed
array.

        '''
        compressed_array = self.array

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

        return self.get_subspace(uarray, indices, copy=False)
    #--- End: def

#--- End: class
