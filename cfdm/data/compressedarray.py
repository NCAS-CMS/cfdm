import sys

from operator import mul

import numpy

from .array import Array


class CompressedArray(Array):
    '''

    '''
    def __init__(self, array=None, shape=None, size=None, ndim=None,
                 compression_type=None, compression_parameters=None):
        '''**Initialization**

:Parameters:

    array:

        '''
        self.array  = array

        self._shape = shape
        self._size  = size
        self._ndim  = ndim

        self.compression_type       = compression_type
        self.compression_parameters = compression_parameters
    #--- End: def

    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns an independent numpy array.

        '''
#        print 'self.compression_type =',self.compression_type
#        print 'self.compression_parameters =',self.compression_parameters

        compression_type       = self.compression_type
        compression_parameters = self.compression_parameters
        
        if compression_type == 'gathered':
            # --------------------------------------------------------
            # Compression by gathering
            # --------------------------------------------------------
            compressed_array = self.array
                        
            uarray = numpy.ma.masked_all(self.shape, dtype=self.dtype)
            
            sample_axis           = compression_parameters['sample_axis']
            uncompression_indices = compression_parameters['indices']

            
            compressed_axes = self.compressed_axes()
            
#           compressed_axes = range(sample_axis,
#                                   self.ndim - (compressed_array.ndim - sample_axis - 1))
            n_compressed_axes = len(compressed_axes)

            uncompressed_shape = self.shape
            partial_uncompressed_shapes = [
                reduce(mul, [uncompressed_shape[i] for i in compressed_axes[i:]], 1)
                for i in range(1, n_compressed_axes)]
            
            sample_indices = [slice(None)] * compressed_array.ndim
            u_indices      = [slice(None)] * self.ndim        
        
            zeros = [0] * n_compressed_axes
            for j, b in enumerate(uncompression_indices):
                sample_indices[sample_axis] = j
                
                u_indices[compressed_axes[0]:compressed_axes[-1]+1] = zeros
                for i, z in zip(compressed_axes[:-1], partial_uncompressed_shapes):
                    if b >= z:
                        (a, b) = divmod(b, z)
                        u_indices[i] = a
                #--- End: for                    
                u_indices[compressed_axes[-1]] = b

                uarray[u_indices] = compressed_array[sample_indices]
            #--- End: for

        elif compression_type == 'ragged_contiguous':
            # --------------------------------------------------------
            # Compression by contiguous ragged array
            # --------------------------------------------------------
            # Create an empty Data array which has dimensions (instance
            # dimension, element dimension).
            compressed_array = self.array

            uarray = numpy.ma.masked_all(self.shape, dtype=self.dtype)

            elements_per_instance = compression_parameters['elements_per_instance']
            
            start = 0 
            for i, n in enumerate(elements_per_instance):
                n = int(n)
                sample_indices = slice(start, start + n)
                
                u_indices = (slice(i, i+1),
                             slice(0, sample_indices.stop - sample_indices.start))
                
                uarray[u_indices] = compressed_array[sample_indices]
                
                start += n
            #--- End: for

        elif compression_type == 'ragged_indexed':
            # --------------------------------------------------------
            # Compression by indexed ragged array
            # --------------------------------------------------------
            # Create an empty Data array which has dimensions (instance
            # dimension, element dimension).
            compressed_array = self.array

            uarray = numpy.ma.masked_all(self.shape, dtype=self.dtype)

            instances = compression_parameters['instances']
            instances = instances.get_array()

            for i in range(uarray.shape[0]):
                sample_dimension_indices = numpy.where(instances == i)[0]

                u_indices = (slice(i, i+1),
                             slice(0, len(sample_dimension_indices)))

                uarray[u_indices] = compressed_array[sample_dimension_indices]
            #--- End: for

        elif compression_type == 'ragged_indexed_contiguous':
            # --------------------------------------------------------
            # Compression by indexed contiguous ragged array
            # --------------------------------------------------------
            compressed_array = self.array

            uarray = numpy.ma.masked_all(self.shape, dtype=self.dtype)

            elements_per_profile = compression_parameters['elements_per_profile']

            profile_indices = compression_parameters['profile_indices']
            profile_indices = profile_indices.get_array()
            
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
                    
                    u_indices = (slice(i, i+1),
                                 slice(j, j+1), 
                                 slice(0, sample_indices.stop - sample_indices.start))

                    uarray[u_indices] = compressed_array[sample_indices]
        #--- End: if

        return uarray[indices]
    #--- End: def

    @property
    def ndim(self):
        return self._ndim

    @property
    def shape(self):
        return self._shape

    @property
    def size(self):
        return self._size

    @property
    def dtype(self):
        return self.array.dtype

    @property
    def isunique(self):
        '''
        '''
        return sys.getrefcount(self.array) <= 2

    def close(self):
        self.array.close()
            
    def open(self):
        self.array.open()

    def compressed_axes(self):
        '''
        '''
        sample_axis = self.compression_parameters.get('sample_axis', 0)

        return range(sample_axis, self.ndim - (self.array.ndim - sample_axis - 1))
#--- End: class
