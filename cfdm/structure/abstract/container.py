import abc


# ====================================================================
#

#
# ====================================================================

class Container(object):
    '''

Base class for storing a data array with metadata.

A variable contains a data array and metadata comprising properties to
describe the physical nature of the data.

All components of a variable are optional.

'''
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, source=None):
        '''**Initialization**

:Parameters:

    source: optional

        '''
        if source is not None:
            self._components = source._components.copy()
        else:
            self._components = {}
    #--- End: def
        
    def __repr__(self):
        '''x.__repr__() <==> repr(x)

.. versionadded:: 1.6

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

.. versionadded:: 1.6

        '''
        out = sorted(self._components)
        return ', '.join(out)
    #--- End: def

    def _del_component(self, component, key=None):
        '''
        '''
        if key is None:            
            return self._components.pop(component, None)
        else:
            return self._components[component].pop(key, None)
    #--- End: def

    def _get_component(self, component, key, *default):
        '''
        '''
        if key is None:
            value = self._components.get(component)
        else:
            value = self._components[component].get(key)
        
        if value is None:
            if default:
                return default[0]

            if key is None:
                raise AttributeError("{!r} object has no component {!r}".format(
                    self.__class__.__name__, component))
            
            raise AttributeError("{!r} object has no element {!r} of the {!r} component".format(
                self.__class__.__name__, key, component))
        #--- End: if
        
        return value
    #--- End: def

    def _has_component(self, component, key=None):
        '''
        '''
        if key is None:
            return component in self._components
        else:
            return key in self._components[component]
    #--- End: def

    def _set_component(self, component, key, value):
        '''
        '''
        if key is None:
            self._components[component] = value
        else:
            self._components[component][key] = value
    #--- End: def

    @abc.abstractmethod
    def copy(self):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.6

        '''
        pass
    #--- End: def
    
#--- End: class
