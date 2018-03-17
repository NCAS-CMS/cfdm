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

    def __init__(self, source=None, copy=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional

    source: optional

    copy: `bool`, optional

        '''
        self._components = {
            # Immutable components that are not deep copied
            1: {},
            # Mutable components that are deep copied
            2: {},
            # Placeholder of components that have bespoke copy
            # algorithms defined in sublcasses
            3: {},
        }

        if source is not None:
#            p = source.properties(copy=False)
#            if properties:
#                p.update(properties)
#
#            properties = p
#
#            components = source._components[2]
#            if components:            
#                components = components2.copy()
#                if copy:
#                    for key, value in components.items():
#                        self._components[key] = value.copy()
#
#                self._components[2] = components
#            #--- End: if
            
            components = source._components[1]
            if components:
                self._components[1] = components.copy()
            #--- End: if

            components = source._components[2]
            if components:
                components = components.copy()
                if copy:
                    for key, value in components.items():
                        components[key] = deepcopy(value)
                        
                self._components[2] = components
            #--- End: if
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
            raise AttributeError("Can't get non-existent {0} {1!r} ".format(component, key))

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

    @abc.abstractmethod
    def copy(self):
        '''
        '''
        pass
    #--- End: def
    
#--- End: class
