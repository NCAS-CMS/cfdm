import abc

from copy import deepcopy

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

    def __init__(self, properties={}, source=None, copy=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional

    source: optional

    copy: `bool`, optional

        '''
        self._private = {'properties': {},
                         'attributes': {}}
      
        if source is not None:
            self._set_attribute('attributes',
                                deepcopy(source._get_attribute('attributes', {})))
                
            p = source.properties(copy=False)
            if properties:
                p.update(properties)

            properties = p
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

    def _del_attribute(self, attr):
        '''
        '''
        return self._private.pop(attr, None)
    #--- End: def

    def _get_attribute(self, attr, *default):
        '''
        '''
        value = self._private.get(attr)
        if value is None:
            if default:
                return default[0]

            raise AttributeError("Can't get non-existent {!r}".format(attr))
        
        return value
    #--- End: def

    def _has_attribute(self, attr):
        '''
        '''
        return attr in self._private
    #--- End: def
    
    def _set_attribute(self, attr, value):
        '''
        '''        
        self._private[attr] = value
    #--- End: def
    
    def _del_attribute_key(self, attr, term):
        '''
        '''
        return self._private.get(attr, {}).pop(term, None)
    #--- End: def

    def _get_attribute_key(self, attr, term, *default):
        '''
        '''
        value = self._private.get(attr, {}).get(term)

        if value is None:
            if default:
                return default[0]
            raise AttributeError("Can't get non-existent {!r}".format(term))

        return value
    #--- End: def

    def _has_attribute_key(self, attr, term):
        '''
        '''
        return term in self._private.get(attr, {})
    #--- End: def

    def _set_attribute_key(self, attr, term, value):
        '''
        '''
        d = self._private.get(attr)
        if d is None:
            d = {}
            self._private[attr] = d

        d[term] = value
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
        return self._del_attribute_key('properties', prop)
    #--- End: def

    def del_attribute(self, attr):
        '''Get an attribute (as

'''        
        return self._del_attribute_key('attributes', attr)
    #--- End: def

    def get_attribute(self, attr, *default):
        '''Get an attribute (as

'''        
        return self._get_attribute_key('attributes', attr, *default)
    #--- End: def

    def has_attribute(self, attr, *default):
        '''Get an attribute (as

'''        
        return self._has_attribute_key('attributes', attr)
    #--- End: def

    def set_attribute(self, attr, value):
        '''Get an attribute (as

'''        
        self._set_attribute_key('attributes', attr, value)
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
        return self._get_attribute_key('properties', prop, *default)
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
        return self._has_attribute_key('properties', prop)
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
        self_properties = self._get_attribute('properties', None)

        if self_properties is None:
           self_properties = {}
           self._set_attribute('properties', self_properties)
        
        if copy:            
            out = deepcopy(self_properties)
        else:
            out = self_properties.copy()
                    
        if clear:
            self_properties.clear()

        if not props:
            return out

        # Still here?
        if copy:
            props = deepcopy(props)

        self_properties.update(props)

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
#        self._private['properties'][prop] = value
        self._set_attribute_key('properties', prop, value)
    #--- End: def

#--- End: class
