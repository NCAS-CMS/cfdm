from builtins import object
from future.utils import with_metaclass
import abc


class IO(with_metaclass(abc.ABCMeta, object)):
    '''Abstract base class for reading and writing Fields.

    '''
    def __init__(self, implementation):
        '''**Initialisation**

    :Parameters:

        implementation: `Implementation'
            The objects required to represent a Field.

        '''
        self.implementation = implementation


    @abc.abstractmethod
    def file_close(self, *args, **kwargs):
        '''Close the dataset file.

        '''
        raise NotImplementedError() # pragma: no cover


    @abc.abstractmethod
    def file_open(self, *args, **kwargs):
        '''Open the dataset file.

        '''
        raise NotImplementedError() # pragma: no cover

# --- End: class


class IORead(with_metaclass(abc.ABCMeta, IO)):
    '''Abstract base class for instantiating Fields from a dataset.

    '''
    @abc.abstractmethod
    def read(self, *args, **kwargs):
        '''Read fields from a netCDF file.

        '''
        raise NotImplementedError() # pragma: no cover

# --- End: class


class IOWrite(with_metaclass(abc.ABCMeta, IO)):
    '''Abstract base class for writing Fields to a dataset.

    '''
    @abc.abstractmethod
    def write(self, *args, **kwargs):
        '''Write fields to a netCDF file.

        '''
        raise NotImplementedError() # pragma: no cover

# --- End: class
