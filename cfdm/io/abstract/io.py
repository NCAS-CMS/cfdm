import abc

_MUST_IMPLEMENT = 'This method must be implemented'


class IO(object):
    '''Base class for reading Fields from, or writing Fields to, a dataset.

    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, implementation):
        '''**Initialisation**

:Parameters:

    implementation: `Implementation'
        The objects required to represent a Field.

        '''
        self.implementation = implementation
    #--- End: def

    @abc.abstractmethod
    def file_close(self, *args, **kwargs):
        '''Close the file.
        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def

    @abc.abstractmethod
    def file_open(self, *args, **kwargs):
        '''Open the file.
        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def

    @abc.abstractmethod
    def file_type(cls, *args, **kwargs):
        '''Return the format of a file.
        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def
#--- End: class

