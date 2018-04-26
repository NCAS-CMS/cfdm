import abc

from ... import IO

_MUST_IMPLEMENT = 'This method must be implemented'

class IOWrite(IO):
    '''
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def write(self, *args, **kwargs):
        '''Write fields to a netCDF file.
        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
#--- End: class

