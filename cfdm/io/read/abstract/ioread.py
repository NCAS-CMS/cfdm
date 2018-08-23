from future.utils import with_metaclass

import abc

from ... import IO


_MUST_IMPLEMENT = 'This method must be implemented'


class IORead(with_metaclass(abc.ABCMeta, IO)):
    '''Base class for instantiating Field constructs from a dataset.

    '''

    @abc.abstractmethod
    def read(self, *args, **kwargs):
        raise NotImplementedError(_MUST_IMPLEMENT)    
#--- End: class

