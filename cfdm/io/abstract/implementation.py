from builtins import object
from future.utils import with_metaclass
import abc


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
        for key, value in kwargs.items():
            if value is None:
                del self._class[key]
    #--- End: def

    def copy(self):
        '''Copy 
        
        '''
        return type(self)(self._class)
    #--- End: def

    def get_class(self, classname):
        '''Return a class of the implementation.
        '''
        try:
            return self._class[classname]
        except KeyError:
            raise ValueError("Implementation does not have class {}".format(classname))
    #--- End: def

    def get_version(self):
        '''Return the version of the implementation.
        '''
        return self._version
    #--- End: def

#--- End: class
