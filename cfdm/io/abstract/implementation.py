import abc


class Implementation(object):
    '''Store an implementation of the CF data model.
    '''
    __metaclass__ = abc.ABCMeta
    
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
