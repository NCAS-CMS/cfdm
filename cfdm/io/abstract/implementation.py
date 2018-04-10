import abc


class Implementation(object):
    '''
    '''
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, **kwargs):
        '''
        '''
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
