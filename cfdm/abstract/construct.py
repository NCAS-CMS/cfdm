from collections import abc


# ====================================================================
#
# AbstractConstruct object
#
# ====================================================================

class AbstractConstruct(object):
    '''

Base class for storing a data array with metadata.

A variable contains a data array and metadata comprising properties to
describe the physical nature of the data.

All components of a variable are optional.

'''
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        '''
        **Initialization**
        '''
        self._ncvar = None

    #--- End: def
        
    def __deepcopy__(self, memo):
        '''

Called by the :py:obj:`copy.deepcopy` standard library function.

.. versionadded:: 1.6

'''
        return self.copy()
    #--- End: def

    def __repr__(self):
        '''
Called by the :py:obj:`repr` built-in function.

x.__repr__() <==> repr(x)

.. versionadded:: 1.6

'''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    @abc.abstractmethod
    def __str__(self):
        '''Called by the :py:obj:`str` built-in function.

x.__str__() <==> str(x)

        '''
        pass
    #--- End: def

    @abc.abstractmethod
    def copy(self):
        '''Return a deep copy.

``c.copy()`` is equivalent to ``copy.deepcopy(c)``.

.. versionadded:: 1.6

:Examples 1:

>>> d = c.copy()

:Returns:

    out: `AbstractConstruct`
        The deep copy.

        '''        
        pass
    #--- End: def
    
    @abc.abstractmethod
    def equals(self, other, *args, **kwargs):
        '''
        '''
        pass
    #--- End: def

    @abc.abstractmethod
    def name(self, default=None, ncvar=True):
        '''Return a name for the construct.
        '''
        pass
    #--- End: def

    def ncvar(self, *name):
        '''
        '''
        if not name:
            return self._ncvar


        name = name[0]
        self._ncvar = name

        return name
    #--- End: def

#--- End: class
