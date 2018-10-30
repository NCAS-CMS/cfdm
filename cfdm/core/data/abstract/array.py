from builtins import (str, super) #(object, str)
from future.utils import with_metaclass

import abc

from ...abstract import Container

#class Array(with_metaclass(abc.ABCMeta, object)):
class Array(with_metaclass(abc.ABCMeta, Container)):
    '''A container for an array.

The form of the array is arbitrary and is defined by the attributes
set on a subclass of the abstract `Array` object.

See `cfdm.core.data.NumpyArray` for an example implementation.

    '''
    def __init__(self, **kwargs):
        '''**Initialization**

:Parameters:

    kwargs: *optional*
        Named attributes and their values that define the array.

        '''
        super().__init__()
        EDIT HERE
        self.__dict__.update(kwargs)
    #--- End: def

    def __array__(self):
        '''The numpy array interface.

:Returns: 

    out: `numpy.ndarray`
        An independent numpy array of the data.

:Examples:

>>> n = numpy.asanyarray(a)
>>> isinstance(n, numpy.ndarray)
True

        '''
        return self.get_array()
    #--- End: def

    def __deepcopy__(self, memo):
        '''x.__deepcopy__() -> Deep copy of data.

Used if copy.deepcopy is called on data. 

Copy-on-write is employed, so care must be taken when modifying any
attribute.

        '''
        return self.copy()
    #--- End: def

    def __repr__(self):
        '''x.__repr__() <==> repr(x)

        '''      
        return "<{0}: {1}>".format(self.__class__.__name__, str(self))
    #--- End: def
        
    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        return "shape={0}, dtype={1}".format(self.shape, self.dtype)
    #--- End: def

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

Note that copy-on-write is employed, so care must be taken when
modifying any attribute.

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
