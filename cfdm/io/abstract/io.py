from builtins import object
from future.utils import with_metaclass
import abc

_MUST_IMPLEMENT = 'This method must be implemented'


class IO(with_metaclass(abc.ABCMeta, object)):
    '''Abstract base class for reading Fields from, or writing Fields to,
a dataset.

    '''

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

#    @abc.abstractmethod
#    def file_type(cls, *args, **kwargs):
#        '''Return the format of a file.
#        '''
#        raise NotImplementedError(_MUST_IMPLEMENT)
#    #--- End: def
#--- End: class

