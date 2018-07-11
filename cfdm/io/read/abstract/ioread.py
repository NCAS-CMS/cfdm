import abc

from ... import IO

_MUST_IMPLEMENT = 'This method must be implemented'


class IORead(IO):
    '''Base class for instantiating Field constructs from a dataset.

    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def read(self, *args, **kwargs):
        raise NotImplementedError(_MUST_IMPLEMENT)    
#--- End: class

