from collections import abc


# ====================================================================
#

#
# ====================================================================

class AbstractProperties(object):
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

        if source is not None:
            if not isinstance(source, AbstractProperties):
                raise ValueError(
"ERROR: source must be a subclass of 'AbstractProperties'. Got {!r}".format(
    source.__class__.__name__))

            # Properties
            p = source.properties()
            if properties:
                p.update(properties)
            properties = p
        
        if properties:
            self.properties(properties, copy=copy)

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

    def _del_attribute(self, attr):
        '''
        '''
        attr = '_'+attr
        x = getattr(self, attr, None)
        if x is None:
            return

        setattr(self, attr, None)
        return x
    #--- End: def
    
    def _get_attribute(self, attr, *default):
        '''
        '''
        x = getattr(self, '_'+attr, None)
        if x is None:
            if default:
                return default[0]

            raise AttributeError("{!r} aascas 34r34 5iln ".format(attr))

        return x
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
        # Still here? Then delete a simple attribute
        try:
            del self._properties[prop]
        except KeyError:
            raise AttributeError(
                "Can't delete non-existent CF property {!r}".format(prop))
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
        d = self._properties

        if default:
            return d.get(prop, default[0])

        try:
            return d[prop]
        except KeyError:
            raise AttributeError("{} doesn't have CF property {}".format(
                self.__class__.__name__, prop))
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
        return prop in self._properties
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

    def properties(self, properties=None, clear=False, copy=True):
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
        out = self._properties
        if copy:            
            out = deepcopy(out)
        else:
            out = out.copy()
                    
        if clear:
            self._properties.clear()

        if not properties:
            return out

        # Still here?
        if copy:
            properties = deepcopy(properties)
        else:
            properties = properties.copy()

        # Delete None-valued properties
        for key, value in properties.items():
            if value is None:
                del properties[key]
        #--- End: for

        self._properties.update(properties)

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
        self._properties[prop] = value
    #--- End: def

#--- End: class
