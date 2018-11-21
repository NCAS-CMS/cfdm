from builtins import (str, super) #(object, str)
from future.utils import with_metaclass

import abc

from ...abstract import Container

#class Array(with_metaclass(abc.ABCMeta, object)):
class Array(with_metaclass(abc.ABCMeta, Container)):
    '''Abstract base class for a container of an array.

The form of the array is arbitrary and is defined by the
initialization parameters of a subclass of `Array`.

See cfdm.core.NumpyArray for an example implementation.

    '''
    def __init__(self, **kwargs):
        '''**Initialization**

:Parameters:

    kwargs: *optional*
        Named parameters and their values that define the array.

        '''
        super().__init__()

        for key, value in kwargs.items():
            self._set_component(key, value, copy=False)
    #--- End: def

    def __array__(self, *dtype):
        '''The numpy array interface.

:Returns: 

    out: `numpy.ndarray`
        An independent numpy array of the data.

**Examples:**

>>> isinstance(a, Array)
True
>>> n = numpy.asanyarray(a)
>>> isinstance(n, numpy.ndarray)
True

        '''
        array = self.get_array()
        if not dtype:
            return array
        else:
            return array.astype(dtype[0], copy=False)
    #--- End: def

    def __deepcopy__(self, memo):
        '''Called by the `copy.deepcopy` function.

x.__deepcopy__() <==> copy.deepcopy(x)

Copy-on-write is employed. Therefore, after copying, care must be
taken when making in-place modifications to attributes of either the
original or the new copy.

.. versionadded:: 1.7

**Examples:**

>>> import copy
>>> y = copy.deepcopy(x)

        '''
        return self.copy()
    #--- End: def

#    def __repr__(self):
#        '''Called by the `repr` built-in function.
#
#x.__repr__() <==> repr(x)
#
#.. versionadded:: 1.7
#
#        '''      
#        return "<{0}: {1}>".format(self.__class__.__name__, str(self))
#    #--- End: def
#        
#    def __str__(self):
#        '''Called by the `str` built-in function.
#
#x.__str__() <==> str(x)
#
#.. versionadded:: 1.7
#
#        '''
#        return "shape={0}, dtype={1}".format(self.shape, self.dtype)
#    #--- End: def

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    @abc.abstractmethod
    def dtype(self):
        '''Data-type of the data elements.

:Examples:

>>> a.dtype
dtype('float64')
>>> print(type(a.dtype))
<type 'numpy.dtype'>

        '''
        raise NotImplementedError()
    #--- End: def

    @property
    @abc.abstractmethod
    def ndim(self):
        '''Number of array dimensions

:Examples:

>>> a.shape
(73, 96)
>>> a.ndim
2
>>> a.size
7008

>>> a.shape
(1, 1, 1)
>>> a.ndim
3
>>> a.size
1

>>> a.shape
()
>>> a.ndim
0
>>> a.size
1

        '''
        raise NotImplementedError()
    #--- End: def
    
    @property
    @abc.abstractmethod
    def shape(self):
        '''Tuple of array dimension sizes.

:Examples:

>>> a.shape
(73, 96)
>>> a.ndim
2
>>> a.size
7008

>>> a.shape
(1, 1, 1)
>>> a.ndim
3
>>> a.size
1

>>> a.shape
()
>>> a.ndim
0
>>> a.size
1

        '''
        raise NotImplementedError()
    #--- End: def
    
    @property
    @abc.abstractmethod
    def size(self):
        '''Number of elements in the array.

:Examples:

>>> a.shape
(73, 96)
>>> a.size
7008
>>> a.ndim
2

>>> a.shape
(1, 1, 1)
>>> a.ndim
3
>>> a.size
1

>>> a.shape
()
>>> a.ndim
0
>>> a.size
1

        '''
        raise NotImplementedError()
    #--- End: def

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self):
        '''Return a deep copy of the array.

``a.copy() is equivalent to ``copy.deepcopy(a)``.

Copy-on-write is employed. Therefore, after copying, care must be
taken when making in-place modifications to attributes of either the
original or the new copy.

:Returns:

    out:
        The deep copy.

:Examples:

>>> b = a.copy()

        '''
        klass = self.__class__
        new = klass.__new__(klass)
        new.__dict__ = self.__dict__.copy()
        return new
    #--- End: def

    @abc.abstractmethod
    def get_array(self):
        '''Return an independent numpy array containing the data.

:Returns:

    out: `numpy.ndarray`
        An independent numpy array of the data.

:Examples:

>>> n = a.get_array()
>>> isinstance(n, numpy.ndarray)
True

        '''
        raise NotImplementedError()
    #--- End: def
    
#--- End: class
