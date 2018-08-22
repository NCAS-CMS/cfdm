from builtins import object
import abc
from future.utils import with_metaclass


class Implementation(with_metaclass(abc.ABCMeta, object)):
    '''Store an implementation of the CF data model.
    '''
    
    def __init__(self, version=None, **kwargs):
        '''**Initialisation**

:Parameters:

    kwargs:
        The concrete objects required to represent a Field.

        '''
        self._version = version
        self._class = kwargs.copy()
    #--- End: def

    def copy(self):
        '''Copy 
        
        '''
        return type(self)(self._class)
    #--- End: def

    def get_class(self, classname):
        '''Return a class of the implementation.
        '''
        return self._class[classname]
    #--- End: def

    def get_version(self):
        '''Return the version of the implementation.
        '''
        return self._version
    #--- End: def

#--- End: class
