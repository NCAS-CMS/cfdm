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
        '''
        **Initialization**
        '''
        self._properties = {}

        if source is not None and  isinstance(source, Properties):
            # Properties
            p = source.properties()
            if properties:
                p.update(properties)

            properties = p

        self._properties = {}            
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
        _attr = '_'+attr
        x = getattr(self, _attr, None)
        delattr(self, _attr)
        return x
    #--- End: def

    def _get_attribute(self, attr, *default):
        '''
        '''
        _attr = '_'+attr
        value = getattr(self, _attr, None)
        if value is None:
            if default:
                return default[0]

            raise AttributeError("Can't get non-existent property {!r}".format(attr))
        
        return value
    #--- End: def

    def _has_attribute(self, attr):
        '''
        '''
        return getattr(self, '_'+attr, None) is not None
    #--- End: def
    
    def _set_attribute(self, attr, value):
        '''
        '''        
        setattr(self, '_'+attr, value)
    #--- End: def
    
    def _del_attribute_term(self, attr, term):
        '''
        '''
        d = self._get_attribute(attr, {})
        return d.pop(term, None)
    #--- End: def

    def _get_attribute_term(self, attr, term, *default):
        '''
        '''
        d = self._get_attribute(attr, {})

        try:
            return d[term]
        except KeyError:
            if default:
                return default[0]

            raise AttributeError("Can't get non-existent property {!r}".format(term))
    #--- End: def

    def _has_attribute_term(self, attr, term):
        '''
        '''
        d = self._get_attribute(attr, {})
        return term in d
    #--- End: def

    def _set_attribute_term(self, attr, term, value):
        '''
        '''
        d = self._get_attribute(attr, None)
        if d is None:
            d = {}
            d = self._set_attribute(attr, d)

        d[term] = value
    #--- End: def

    def copy(self):
        '''Return a deep copy.

``c.copy()`` is equivalent to ``copy.deepcopy(c)``.

.. versionadded:: 1.6

:Examples 1:

>>> d = c.copy()

:Returns:

    out:
        The deep copy.

        '''        
        return type(self)(source=self, copy=True)
    #--- End: def
    
#    def del_ncvar(self):
#        '''
#        '''        
#        return self._del_attribute('ncvar')
#    #--- End: def

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
        return self._del_attribute_term('properties', prop)
    #--- End: def

#    def get_ncvar(self, *default):
#        '''
#        '''        
#        return self._get_attribute('ncvar', *default)
#    #--- End: def

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
        return self._get_attribute_term('properties', prop, *default)
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
        return self._has_attribute_term('properties', prop)
    #--- End: def

#    @abc.abstractmethod
    def name(self, default=None, ncvar=True):
        '''Return a name for the construct.
        '''
        pass
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
        self_properties = self._get_attribute('properties')
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
        else:
            props = props.copy()

        # Delete None-valued properties
        for key, value in props.items():
            if value is None:
                del props[key]
        #--- End: for

        self_properties.update(props)

        return out
    #--- End: def

#    def set_ncvar(self, value))
#        '''
#        '''        
#        return self._set_attribute('ncvar', value)
#    #--- End: def

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
        self._set_attribute_term('properties', prop, value)
    #--- End: def

#--- End: class
