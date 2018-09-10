from builtins import (object, str)
from future.utils import with_metaclass

import abc

_MUST_IMPLEMENT = 'This method must be implemented'


class Array(with_metaclass(abc.ABCMeta, object)):
    '''A container for an array.
    
    '''
           
    def __init__(self, **kwargs):
        '''
        
**Initialization**

'''
        self.__dict__ = kwargs
    #--- End: def
               
    def __deepcopy__(self, memo):
        '''Used if copy.deepcopy is called on the variable.

        '''
        return self.copy()
    #--- End: def

    def __repr__(self):
        '''

x.__repr__() <==> repr(x)

'''      
        return "<{0}: {1}>".format(self.__class__.__name__, str(self))
    #--- End: def
        
    def __str__(self):
        '''

x.__str__() <==> str(x)

'''
        return "shape={0}, dtype={1}".format(self.shape, self.dtype)
    #--- End: def

    @property
    @abc.abstractmethod
    def ndim(self):
        raise NotImplementedError(_MUST_IMPLEMENT)

    @property
    @abc.abstractmethod
    def shape(self):
        raise NotImplementedError(_MUST_IMPLEMENT)

    @property
    @abc.abstractmethod
    def size(self):
        raise NotImplementedError(_MUST_IMPLEMENT)
    
    @property
    @abc.abstractmethod
    def dtype(self):
        raise NotImplementedError(_MUST_IMPLEMENT)
    
    def copy(self):
        '''Return a deep copy.

``f.copy() is equivalent to ``copy.deepcopy(f)``.

:Returns:

    out :
        A deep copy.

:Examples:

>>> g = f.copy()

        '''
        klass = self.__class__
        new = klass.__new__(klass)
        new.__dict__ = self.__dict__.copy()
        return new
    #--- End: def

    @abc.abstractmethod
    def get_array(self):
        '''Return an independent numpy array containing the data.

:Examples:

>>> n = a.get_array()

        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def
    
#--- End: class
