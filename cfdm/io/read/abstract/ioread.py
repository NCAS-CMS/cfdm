import abc

from ... import IO

_MUST_IMPLEMENT = 'This method must be implemented'


class IORead(IO):
    '''
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def read(self, *args, **kwargs):
        raise NotImplementedError(_MUST_IMPLEMENT)    
#--- End: class

