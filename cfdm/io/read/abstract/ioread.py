import abc

from ... import IO

NOT_IMPLEMENTED = 'This method must be implemented'

class IORead(IO):
    '''
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def read(self, *args, **kwargs):
        raise NotImplementedError(NOT_IMPLEMENTED)

#--- End: class

