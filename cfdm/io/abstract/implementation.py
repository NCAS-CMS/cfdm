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
        return type(self)(self._class)
    #--- End: def

    def get_class(self, classname):
        return self._class[classname]
    #--- End: def
