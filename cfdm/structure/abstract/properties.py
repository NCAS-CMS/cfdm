import abc

from copy import deepcopy

#from ..collection import Collection

# ====================================================================
#

#
# ====================================================================

class Properties(object):
    '''

Base class for storing a data array with metadata.

A variable contains a data array and metadata comprising properties to
describe the physical nature of the data.

All components of a variable are optional.

'''
    __metaclass__ = abc.ABCMeta

    _special_properties = ()

#    _Collection = Collection
    
    def __init__(self, properties={}, source=None, copy=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional

    source: optional

    copy: `bool`, optional

        '''
#        self._components = {'properties': Collection()}
        self._components1 = {'properties': {}}
        self._components2 = {}
        self._components3 = {}
#        self._extra       = {}
      
        if source is not None:
#            self._extra = source._extra.copy()
                
            p = source.properties(copy=False)
            if properties:
                p.update(properties)

            properties = p

            self._components2 = source._components2.copy()
            if copy:
                for key, value in self._components2:
                    self._components2[key] = value.copy()

            self._components3 = source._components3.copy()
        #--- End: if

        if properties:
            self.properties(properties, copy=copy)
    #--- End: def
        
    def __deepcopy__(self, memo):
        '''Called by the `copy.deepcopy` standard library function.

.. versionadded:: 1.6

        '''
        return self.copy()
    #--- End: def

    def __repr__(self):
        '''x.__repr__() <==> repr(x)

.. versionadded:: 1.6

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    def _del_component(self, component, key):
        '''
        '''
        if key is None:            
            return self._components1.pop(component, None)
        else:
            return self._components1[component].pop(key, None)
    #--- End: def

    def _del_component3(self, component3):
        '''
        '''
        return self._components3.pop(component3, None)
    #--- End: def

    def _get_component(self, component, key, *default):
        '''
        '''
        if key is None:
            value = self._components1.get(component)
        else:
            value = self._components1[component].get(key)
        
        if value is None:
            if default:
                return default[0]
            raise AttributeError("Can't get non-existent {!r}".format(key))

        return value
    #--- End: def

    def _get_component3(self, component3, *default):
        '''
        '''
        value = self._components3.get(component3)
        
        if value is None:
            if default:
                return default[0]
            raise AttributeError("Can't get non-existent attribute {!r}".format(component3))

        return value
    #--- End: def

    def _has_component(self, component, key):
        '''
        '''
        if key is None:
            return component in self._components1
        else:
            return key in self._components1[component]
    #--- End: def

    def _has_component3(self, component3):
        '''
        '''
        return component3 in self._components3
    #--- End: def

    def _set_component(self, component, key, value):
        '''
        '''
        if key is None:
            self._components1[component] = value
        else:
            self._components1[component][key] = value
    #--- End: def

    def _set_component3(self, component3, value):
        '''
        '''
        self._components3[component3] = value
    #--- End: def

    def copy(self, data=True):
        '''Return a deep copy.

``x.copy()`` is equivalent to ``copy.deepcopy(x)``.

.. versionadded:: 1.6

:Examples 1:

>>> d = c.copy()

:Parameters:

    data: `bool`, optional
        This parameter has no effect and is ignored.

:Returns:

    out:
        The deep copy.

        '''        
        return type(self)(source=self, copy=True)
    #--- End: def
    
    def del_property(self, prop):
        '''Delete a CF or non-CF property.

.. versionadded:: 1.6

.. seealso:: `getprop`, `hasprop`, `setprop`

:Examples 1:

>>> f.{+name}('standard_name')

:Parameters:

    prop: `str`
        The name of the property to be deleted.

:Returns:

     `None`

:Examples 2:

>>> f.setprop('project', 'CMIP7')
>>> f.{+name}('project')
>>> f.{+name}('project')
AttributeError: Can't delete non-existent property 'project'

        '''
        return self._del_component('properties', prop)
    #--- End: def

    def get_property(self, prop, *default):
        '''

Get a CF property.

When a default argument is given, it is returned when the attribute
doesn't exist; without it, an exception is raised in that case.

.. versionadded:: 1.6

.. seealso:: `delprop`, `hasprop`, `setprop`

:Examples 1:

>>> f.{+name}('standard_name')

:Parameters:

    prop: `str`
        The name of the CF property to be retrieved.

    default: optional
        Return *default* if and only if the variable does not have the
        named property.

:Returns:

    out:
        The value of the named property or the default value, if set.

:Examples 2:

>>> f.setprop('standard_name', 'air_temperature')
>>> f.{+name}('standard_name')
'air_temperature'
>>> f.delprop('standard_name')
>>> f.{+name}('standard_name')
AttributeError: Field doesn't have CF property 'standard_name'
>>> f.{+name}('standard_name', 'foo')
'foo'

'''
        return self._get_component('properties', prop, *default)
    #--- End: def

    def has_property(self, prop):
        '''

Return True if a CF property exists, otherise False.

.. versionadded:: 1.6

.. seealso:: `delprop`, `getprop`, `setprop`

:Examples 1:

>>> if f.{+name}('standard_name'):
...     print 'Has standard name'

:Parameters:

    prop: `str`
        The name of the property.

:Returns:

     out: `bool`
         True if the CF property exists, otherwise False.

'''
        return self._has_component('properties', prop)
    #--- End: def

    def properties(self, props=None, clear=False, copy=True):
        '''Inspect or change the CF properties.

.. versionadded:: 1.6

:Examples 1:

>>> f.{+name}()

:Parameters:

    props: `dict`, optional   
        Set {+variable} attributes from the dictionary of values. If
        the *copy* parameter is True then the values in the *attrs*
        dictionary are deep copied

    clear: `bool`, optional
        If True then delete all CF properties.

    copy: `bool`, optional
        If False then any property values provided bythe *props*
        parameter are not copied before insertion into the
        {+variable}. By default they are deep copied.

:Returns:

    out: `dict`
        The CF properties prior to being changed, or the current CF
        properties if no changes were specified.

:Examples 2:

        '''
        existing_properties = self._get_component('properties', None, None)

        if existing_properties is None:
           existing_properties = {}
           self._set_component('properties', None, existing_properties)
        
        out = existing_properties.copy()

        for prop in self._special_properties:
            value = getattr(self, 'get_'+prop)(None)
            if value is not None:
                out[prop] = value
        
        if clear:
            existing_properties.clear()
            for prop in self._special_properties:
                getattr(self, 'del_'+prop)

        if not props:
            return out

        # Still here?
        if copy:
            props = deepcopy(props)

        existing_properties.update(props)

        return out
    #--- End: def

    def set_property(self, prop, value):
        '''Set a CF or non-CF property.

.. versionadded:: 1.6

.. seealso:: `delprop`, `getprop`, `hasprop`

:Examples 1:

>>> f.setprop('standard_name', 'time')
>>> f.setprop('project', 'CMIP7')

:Parameters:

    prop: `str`
        The name of the property.

    value:
        The value for the property.

:Returns:

     `None`

        '''
        self._set_component('properties', prop, value)
    #--- End: def

#--- End: class
