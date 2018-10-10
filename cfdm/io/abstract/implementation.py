from builtins import object
from future.utils import with_metaclass
import abc


class Implementation(with_metaclass(abc.ABCMeta, object)):
    '''Store an implementation of the CF data model.
    '''
    
    def __init__(self, version=None, **kwargs):
        '''**Initialisation**

:Parameters:

    kwargs:
        The concrete objects required to represent a Field.

        '''
        self._version = version
        self._class = kwargs.copy()
        for key, value in kwargs.items():
            if value is None:
                del self._class[key]
    #--- End: def

    def copy(self):
        '''Copy 
        
        '''
        return type(self)(self._class)
    #--- End: def

    def get_class(self, name):
        '''Return a class of the implementation.

:Parameters:

    name: `str`
        The name of the class.

          *Example:*
            ``name='Field'``

:Returns:
    
    out:
        The class object.

:Examples:

>>> Field = i.get_class('Field')
>>> f = Field()

        '''
        try:
            return self._class[name]
        except KeyError:
            raise ValueError("Implementation does not have class {!r}".format(name))
    #--- End: def

    def get_version(self):
        '''Return the version of the implementation.

:Returns:
    
    out: `str`
        The version.

:Examples:

>>> i.get_version()
'1.8'    

        '''
        return self._version
    #--- End: def

    def set_class(self, name, cls):
        '''Set a class of the implementation.

:Parameters:

    name: `str`
        The name of the class.

          *Example:*
            ``name='Field'``
    cls: 
        The class object.

:Returns:

    `None`

        '''
        self._class[name] = cls
    #--- End: def

#--- End: class
