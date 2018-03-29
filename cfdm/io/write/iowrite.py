import abc

from .. import IO

NOT_IMPLEMENTED = 'This method must be implemented'

class IOWrite(IO):
    '''
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def write(self, *args, **kwargs):
        raise NotImplementedError(NOT_IMPLEMENTED)

#--- End: class

