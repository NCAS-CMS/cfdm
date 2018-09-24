from builtins import object
from future.utils import with_metaclass
import abc


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
        raise NotImplementedError()
    #--- End: def

    @abc.abstractmethod
    def file_open(self, *args, **kwargs):
        '''Open the file.
        '''
        raise NotImplementedError()
    #--- End: def

#    @abc.abstractmethod
#    def file_type(cls, *args, **kwargs):
#        '''Return the format of a file.
#        '''
#        raise NotImplementedError()
#    #--- End: def
#--- End: class


class IORead(with_metaclass(abc.ABCMeta, IO)):
    '''Abstract base class for instantiating Field constructs from a
dataset.

    '''
    @abc.abstractmethod
    def read(self, *args, **kwargs):
        '''
        '''
        raise NotImplementedError()
    #--- End: def

#--- End: class


class IOWrite(with_metaclass(abc.ABCMeta, IO)):
    '''Base class writing Field constructs to a dataset.

    '''

    @abc.abstractmethod
    def write(self, *args, **kwargs):
        '''Write fields to a netCDF file.
        '''
        raise NotImplementedError()
#--- End: class
