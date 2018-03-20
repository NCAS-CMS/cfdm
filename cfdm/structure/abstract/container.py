import abc

from copy import deepcopy

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

    def __init__(self, source=None, copy=True):
        '''**Initialization**

:Parameters:

    source: optional

    copy: `bool`, optional

        '''
        self._components = {
            # Components that not copied as object identities. Good
            # for immutable objects (e.g. a str or a tuple)
            1: {},
            # Components that may be sufficiently copied with a copy
            # method (e.g. a set or a dict with immutable values)
            4: {},
            # Components that need to be deep copied with copy.deepcopy
            2: {},
            # Components that are should have bespoke copy algorithms
            3: {},
        }

        if source is not None:            
            components = source._components[1]
            if components:
                self._components[1] = components.copy()

            key = 4
            components = source._components[key]
            if components:
                components = components.copy()
                if copy:
                    for k, v in components.items():
                        components[k] = v.copy()
                        
                self._components[key] = components

            key = 2
            components = source._components[key]
            if components:
                components = components.copy()
                if copy:
                    for k, v in components.items():
                        components[k] = deepcopy(v)
                        
                self._components[key] = components
        #--- End: if
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
        out = []
        for key, value in sorted(self._components.items()):
            out.extend(sorted(value.keys()))

        return ', '.join(out)
    #--- End: def

    def _del_component(self, component_type, component, key=None):
        '''
        '''
        components = self._components[component_type]
        if key is None:            
            return components.pop(component, None)
        else:
            return components[component].pop(key, None)
    #--- End: def

    def _get_component(self, component_type, component, key, *default):
        '''
        '''
        components = self._components[component_type]
        if key is None:
            value = components.get(component)
        else:
            value = components[component].get(key)
        
        if value is None:
            if default:
                return default[0]
            if key is None:
                raise AttributeError("Can't get non-existent {!r}".format(component))
            raise AttributeError("Can't get non-existent {!r}".format(key))

        return value
    #--- End: def

    def _has_component(self, component_type, component, key=None):
        '''
        '''
        components = self._components[component_type]
        if key is None:
            return component in components
        else:
            return key in components[component]
    #--- End: def

    def _set_component(self, component_type, component, key, value):
        '''
        '''
        components = self._components[component_type]
        if key is None:
            components[component] = value
        else:
            components[component][key] = value
    #--- End: def

    def copy(self):
        '''
        '''
        return type(self)(source=self, copy=True)
#--- End: class
