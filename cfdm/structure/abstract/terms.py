import abc

from copy import deepcopy

import mixin
from .container import Container


class Terms(mixin.Ancillaries, Container):
    '''Base class for named parameters and names ancillary arrays.

    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, parameters=None, ancillaries=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    source: optional

    copy: `bool`, optional

        '''
        super(Terms, self).__init__(source=source)

        if source:
            try:
                parameters = source.parameters()
            except AttributeError:
                parameters = None

            try:
                ancillaries = source.ancillaries()
            except AttributeError:
                ancillaries = None
        #--- End: if
        
        if parameters is None:
            parameters = {}
            copy = False
            
        self.parameters(parameters, copy=copy)
        
        if ancillaries is None:
            ancillaries = {}
        elif copy or not _use_data:
            ancillaries = ancillaries.copy()
            for key, value in ancillaries.items():
                try:
                    ancillaries[key] = value.copy(data=_use_data)
                except AttributeError:
                    ancillaries[key] = deepcopy(value)
        #--- End: if
            
        self.ancillaries(ancillaries, copy=False)
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        out = []

        parameters = self.parameters()
        if parameters:
            out.append('Parameters: {0}'.format(', '.join(sorted(parameters))))
            
        ancillaries = self.ancillaries()
        if ancillaries:
            out.append('Ancillaries: {0}'.format(', '.join(sorted(ancillaries))))
            
        return '; '.join(out)
    #--- End: def

    def copy(self, data=True):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.6

:Examples 1:

>>> g = f.copy()

:Parameters:

    data: `bool`, optional
        If False then do not copy the ancillary data arrays. By
        default the data arrays are copied.

:Returns:

    out:
        The deep copy.

:Examples 2:

>>> g = f.copy(data=False)

        '''
        return type(self)(source=self, copy=True, _use_data=data)
    #--- End: def
    
    def del_parameter(self, parameter):
        '''Delete a parameter.

.. seealso:: `get_parameter`, `has_parameter`, `parameters`,
             `set_parameter`

:Examples 1:

>>> f.del_parameter('grid_mapping_name')

:Parameters:

    parmtaeter: `str`
        The name of the parameter to be deleted.

:Returns:

     out:
        The value of the deleted parameter, or `None` if the parameter
        was not set.

:Examples 2:

        '''
        return self._del_component('parameters', parameter)
    #--- End: def

    def get_parameter(self, term, *default):
        '''Get a parameter value.

.. versionadded:: 1.6

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
        d = self._get_component('parameters', None)
        if term in d:
            return d[term]
        
        if default:
            return default[0]

        raise AttributeError("{} doesn't have parameter term {!r}".format(
                self.__class__.__name__, term))
    #--- End: def
    
    def parameters(self, parameters=None, copy=True):
        '''Return or replace the parameter-valued terms.

.. versionadded:: 1.6

.. seealso:: `ancillaries`

:Examples 1:

>>> d = c.parameters()

:Parameters:

    parameters: `dict`, optional
        Replace all parameter-valued terms with those provided.

          *Example:*
            ``parameters={'earth_radius': 6371007}``

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
        return self._dict_component('parameters',
                                    replacement=parameters, copy=copy)
    #--- End: def

    def set_parameter(self, term, value, copy=True):
        '''Set a parameter-valued term.

.. versionadded:: 1.6

.. seealso:: `parameters`

:Examples 1:

>>> c.set_parameter('longitude_of_central_meridian', 265.0)

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
            value = deepcopy(value)
            
        self._set_component('parameters', term, value)
    #--- End: def
    
#--- End: class
