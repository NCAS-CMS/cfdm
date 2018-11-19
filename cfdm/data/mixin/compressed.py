from builtins import (object, super)


class Compressed(object):
    '''TODO
    '''
    def _set_compressed_Array(self, array, copy=True):
        '''Set the compressed array.

.. versionadded:: 1.7

:Parameters:

    array: `numpy` array_like or subclass of `cfdm.data.Array`
        The compressed data to be inserted.

:Returns:

    `None`

:Examples:

>>> d._set_compressed_Array(a)

        '''
        if not isinstance(array, abstract.Array):
            if not isinstance(array, numpy.ndarray):
                data = numpy.asanyarray(array)
                
            array = NumpyArray(array)
            
        super()._set_compressed_Array(array, copy=copy)
    #--- End: def

#--- End: class
