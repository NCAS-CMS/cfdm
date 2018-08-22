import abc

from ... import IO
from future.utils import with_metaclass

_MUST_IMPLEMENT = 'This method must be implemented'


class IOWrite(with_metaclass(abc.ABCMeta, IO)):
    '''Base class writing Field constructs to a dataset.

    '''

    @abc.abstractmethod
    def write(self, *args, **kwargs):
        '''Write fields to a netCDF file.
        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
#--- End: class

