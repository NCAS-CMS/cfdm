import abc


class Ancillaries(object):
    '''Mixin class for named ancillary arrays.

    '''
    __metaclass__ = abc.ABCMeta

    def ancillaries(self, ancillaries=None, copy=True):
        '''Return or replace the ancillary-valued terms.

.. versionadded:: 1.6

.. seealso:: `parameters`

:Examples 1:

>>> d = c.ancillaries()

:Parameters:

    ancillaries: `dict`, optional
        Replace all named ancillaries with those provided.

          *Example:*
            ``ancillaries={'x': x_ancillary}``

    copy: `bool`, optional

:Returns:

    out: `dict`
        The parameter-valued terms and their values. If the
        *parameters* keyword has been set then the parameter-valued
        terms prior to replacement are returned.

:Examples 2:

>>> c.parameters()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}

>>> c.parameters()
{}

        '''
        return self._dict_component('ancillaries',
                                    replacement=ancillaries, copy=copy)
    #--- End: def
    
    def del_ancillary(self, ancillary):
        '''Delete an ancillary.

.. seealso:: `ancillaries`, `get_ancillary`, `has_ancillary`,
             `set_ancillary`

:Examples 1:

>>> f.del_ancillary('orog')

:Parameters:

    parmtaeter: `str`
        The name of the parameter to be deleted.

:Returns:

     out:
        The value of the deleted parameter, or `None` if the parameter
        was not set.

:Examples 2:

        '''
        return self._del_component('ancillaries', ancillary)
    #--- End: def

    def get_ancillary(self, ancillary, *default):
        '''Get a parameter value.

:Examples 1:

>>> v = c.get_parameter('false_northing')

:Parameters:

    term: `str`
        The name of the term.

    default: optional

:Returns:

    out:
        The value of the term <SOMETING BAOUT DEFAULT>

:Examples 2:

>>> c.get_parameter('grid_north_pole_latitude')
70.0

>>> c.get_parameter('foo')
ERROR
>>> c.get_parameter('foo', 'nonexistent term')
'nonexistent term'


        '''
        d = self._get_component('ancillaries', None)
        if term in d:
            return d[term]
        
        if default:
            return default[0]

        raise AttributeError("{} doesn't have ancillary-valued term {!r}".format(
                self.__class__.__name__, term))
    #--- End: def
    
    def set_ancillary(self, term, value, copy=True):
        '''Set an ancillary-valued term.

.. versionadded:: 1.6

.. seealso:: `ancillaries`, `del_ancillary`, `get_ancillary`,
             `set_ancillary`

:Examples 1:

>>> c.set_ancillary('longitude_of_central_meridian', 265.0)

:Returns:

    `None`

:Examples 2:

>>> c.parameters()
{'standard_parallel': 25.0;
 'latitude_of_projection_origin': 25.0}
>>> c.set_parameter('longitude_of_central_meridian', 265.0)
>>> c.parameters()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}

        '''
        if copy:
            value = value.copy()
            
        self._set_component('ancillaries', term, value)
    #--- End: def
    
#--- End: class
