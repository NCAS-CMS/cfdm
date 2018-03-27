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

#    NOCOPY      = 'nocopy'
#    COPY        = 'copy'
#    DEEPCOPY    = 'deepcopy'
#    CUSTOMCOPY  = 'customcopy'
    
    def __init__(self, source=None, copy=True):
        '''**Initialization**

:Parameters:

    source: optional

    copy: `bool`, optional

        '''
#        self._copy_method = {
#            self.COPY      : (),
#            self.DEEPCOPY  : (),
#        }
        
        
#            # Components that not copied as object identities. Good
#            # for immutable objects (e.g. a str or a tuple)
#            self.NOCOPY: {},
#            # Components that may be sufficiently copied with a copy
#            # method (e.g. a set or a dict with immutable values, or a
#            # numpy array)
#            self.SHALLOWCOPY: {},
#            # Components that need to be deep copied with copy.deepcopy
#            self.DEEPCOPY: {},
#            # Components that are should have bespoke copy algorithms
#            self.CUSTOMCOPY: {},
#        }

        if source is not None:
#            self._copy_method.update(source._copy_method)

            self._components = source._components.copy()
        else:
            self._components = {}
            #            for component in source._copy_method[self.NOCOPY]:
#                components[component] = component

#            for component in source._copy_method[self.COPY]:
#                components[component] = components[component].copy()
#
#            for component in source._copy_method[self.DEEPCOPY]:
#                components[component] = deepcopy(components[component])
#
#            self._components = components

#            key = self.NOCOPY
#            components = source._components[key]
#            if components:
#                self._components[key] = components.copy()
#
#            key = self.SHALLOWCOPY
#            components = source._components[key]
#            if components:
#                components = components.copy()
#                if copy:
#                    for k, v in components.items():
#                        components[k] = v.copy()
#                        
#                self._components[key] = components
#
#            key = self.DEEPCOPY
#            components = source._components[key]
#            if components:
#                components = components.copy()
#                if copy:
#                    for k, v in components.items():
#                        components[k] = deepcopy(v)
#                        
#                self._components[key] = components
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
#        out = []
#        for key, value in sorted(self._components.items()):
#            out.extend(sorted(value.keys()))


        out = sorted(self._components)
        return ', '.join(out)
    #--- End: def

#    def _del_component(self, component_type, component, key=None):
    def _del_component(self, component, key=None):
        '''
        '''
#        components = self._components[component_type]
#        components = self._components
        if key is None:            
            return self._components.pop(component, None)
        else:
            return self._components[component].pop(key, None)
    #--- End: def

#    def _set_copy_method(self, component, copy_method):
#        self._copy_method[copy_method] = self._copy_method[copy_method] + (component,)

#    def _get_component(self, component_type, component, key, *default):
    def _get_component(self, component, key, *default):
        '''
        '''
#        components = self._components[component_type]
#        components = self._components
        if key is None:
            value = self._components.get(component)
        else:
            value = self._components[component].get(key)
        
        if value is None:
            if default:
                return default[0]
            if key is None:
                raise AttributeError("Can't get non-existent {!r}".format(component))
            raise AttributeError("Can't get non-existent {!r}".format(key))

        return value
    #--- End: def

#    def _has_component(self, component_type, component, key=None):
    def _has_component(self, component, key=None):
        '''
        '''
#        components = self._components[component_type]
#        components = self._components
        if key is None:
            return component in self._components
        else:
            return key in self._components[component]
    #--- End: def

#    def _set_component(self, component_type, component, key, value):
    def _set_component(self, component, key, value):
        '''
        '''
#        components = self._components[component_type]
#        components = self._components
        if key is None:
            self._components[component] = value
        else:
            self._components[component][key] = value
    #--- End: def

    @abc.abstractmethod
    def copy(self):
        '''
        '''
        return type(self)(source=self, copy=True)
#--- End: class
