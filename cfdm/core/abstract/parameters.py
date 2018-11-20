from future.utils import with_metaclass
from builtins import super

import abc

from copy import deepcopy

from . import Container


class Parameters(with_metaclass(abc.ABCMeta, Container)):
    '''Abstract base class for a collection of named parameters.

.. versionadded:: 1.7
    '''
    def __init__(self, parameters=None, source=None, copy=True): 
        '''**Initialization**

:Parameters:

    parameters: `dict`, optional
       Set parameters. The dictionary keys are parameter names, with
       corresponding values. Ignored if the *source* parameter is set.

       *Example:*
         ``parameters={'earth_radius': 6371007.}``

       Parameters may also be set after initialisation with the
       `parameters` and `set_parameter` methods.

    source: optional
        Initialize the parameters from those of *source*.

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__()

        self._set_component('parameters', {}, copy=False)

        if source:
            try:
                parameters = source.parameters()
            except AttributeError:
                parameters = None
        #--- End: if
        
        if parameters is None:
            parameters = {}
            copy = False

        self.parameters(parameters, copy=copy)
    #--- End: def

#    def __str__(self):
#        '''x.__str__() <==> str(x)
#
#        '''
#        out = []
#
#        parameters = self.parameters()
#        if parameters:
#            out.append('Parameters: {0}'.format(', '.join(sorted(parameters))))
#            
#        return '; '.join(out)
#    #--- End: def

    def copy(self):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.7

:Returns:

    out:
        The deep copy.

**Examples:**

>>> g = f.copy()

        '''
        return type(self)(source=self, copy=True)
    #--- End: def
    
    def del_parameter(self, parameter, *default):
        '''Delete a parameter.

.. versionadded:: 1.7

.. seealso:: `get_parameter`, `has_parameter`, `parameters`,
             `set_parameter`

:Parameters:

    parameter: `str`
        The name of the parameter to be deleted.

    default: optional
        Return *default* if the parameter has not been set.

:Returns:

     out:
        The removed parameter. If the parameter has not been then
        *default* is returned, if provided.

**Examples:**

        '''
        return self._get_component('parameters').pop(parameter, None)
    #--- End: def

    def get_parameter(self, term, *default):
        '''Get a parameter value.

.. versionadded:: 1.7

:Parameters:

    term: `str`
        The name of the term.

    default: optional

:Returns:

    out:
        The value of the term <SOMETING BAOUT DEFAULT>

**Examples:**

>>> c.get_parameter('grid_north_pole_latitude')
70.0

>>> c.get_parameter('foo')
ERROR
>>> c.get_parameter('foo', 'nonexistent term')
'nonexistent term'


        '''
        d = self._get_component('parameters')
        if term in d:
            return d[term]
        
        if default:
            return default[0]

        raise AttributeError("{} doesn't have parameter term {!r}".format(
                self.__class__.__name__, term))
    #--- End: def
    
    def parameters(self, parameters=None, copy=True):
        '''Return or replace the parameter-valued terms.

.. versionadded:: 1.7

.. seealso:: `ancillaries`

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

**Examples:**

>>> c.parameters()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}

>>> c.parameters()
{}

        '''
        out = self._get_component('parameters').copy()

        if parameters is not None:
            if copy:
                properties = deepcopy(parameters)
            else:
                properties = parameters.copy()
                
            self._set_component('parameters', parameters, copy=False)

        return out
    #--- End: def

    def set_parameter(self, term, value, copy=True):
        '''Set a parameter-valued term.

.. versionadded:: 1.7

.. seealso:: `parameters`

:Returns:

    `None`

**Examples:**

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
            
        self._get_component('parameters')[term] = value
    #--- End: def
    
#--- End: class
