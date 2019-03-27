from future.utils import with_metaclass
from builtins import super

import abc

from copy import deepcopy

from . import Container


class Parameters(with_metaclass(abc.ABCMeta, Container)):
    '''Abstract base class for a collection of named parameters.

.. versionadded:: 1.7.0
    '''
    def __init__(self, parameters=None, source=None, copy=True): 
        '''**Initialization**

:Parameters:

    parameters: `dict`, optional
       Set parameters. The dictionary keys are parameter names, with
       corresponding values. Ignored if the *source* parameter is set.

       *Parameter example:*
         ``parameters={'earth_radius': 6371007.}``

       Parameters may also be set after initialisation with the
       `set_parameters` and `set_parameter` methods.

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

        self.set_parameters(parameters, copy=copy)
    #--- End: def

    def clear_parameters(self):
        '''Remove all parameters.

.. versionadded:: 1.7.0

.. seealso:: `del_parameter`, `parameters`, `set_parameters`

:Returns:

    `dict`
        The parameters that have been removed.

**Examples:**

>>> old = f.clear_parameters()
>>> old
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}
>>> f.parameters()
{}
>>> f.set_parameters(old)
>>> f.parameters()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}

        '''
        out = self._get_component('parameters')
        self._set_component('parameters', {})
        return out.copy()
    #--- End: def
    
    def copy(self):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.7.0

:Returns:

        The deep copy.

**Examples:**

>>> g = f.copy()

        '''
        return type(self)(source=self, copy=True)
    #--- End: def
    
    def del_parameter(self, parameter, default=ValueError()):
        '''Delete a parameter.

.. versionadded:: 1.7.0

.. seealso:: `get_parameter`, `has_parameter`, `parameters`,
             `set_parameter`

:Parameters:

    parameter: `str`
        The name of the parameter to be deleted.

    default: optional
        Return the value of the *default* parameter if the parameter
        has not been set. If set to an `Exception` instance then it
        will be raised instead.

:Returns:

        The removed parameter. If the parameter has not been then
        *default* is returned, if provided.

**Examples:**

>>> f.set_parameter('earth_radius', 6371007)
>>> f.has_parameter('earth_radius')
True      
>>> f.get_parameter('earth_radius')
6371007   
>>> f.del_parameter('earth_radius')
6371007   
>>> f.has_parameter('earth_radius')
False
>>> print(f.del_parameter('earth_radius', None))
None
>>> print(f.get_paramete('earth_radius', None))
None

        '''
        try:
            return self._get_component('parameters').pop(parameter)
        except KeyError:
            return self._default(default,
                                 "{!r} has no {!r} parameter".format(
                                     self.__class__.__name__, parameter))
    #--- End: def

    def get_parameter(self, parameter, default=ValueError()):
        '''Get a parameter value.

.. versionadded:: 1.7.0

:Parameters:

    parameter: `str`
        The name of the parameter.

    default: optional
        Return the value of the *default* parameter if the parameter
        has not been set. If set to an `Exception` instance then it
        will be raised instead.

:Returns:

        The value of the parameter.

**Examples:**

>>> f.set_parameter('earth_radius', 6371007)
>>> f.has_parameter('earth_radius')
True      
>>> f.get_parameter('earth_radius')
6371007   
>>> f.del_parameter('earth_radius')
6371007   
>>> f.has_parameter('earth_radius')
False
>>> print(f.del_parameter('earth_radius', None))
None
>>> print(f.get_parameter('earth_radius', None))
None

        '''
        try:
            return self._get_component('parameters')[parameter]
        except KeyError:
            return self._default(default,
                                 "{!r} has no {!r} parameter".format(
                                     self.__class__.__name__, parameter))
    #--- End: def
    
    def has_parameter(self, parameter):
        '''Whether a parameter has been set.

.. versionadded:: 1.7.0

.. seealso:: `del_parameter`, `get_parameter`, `parameters`,
             `set_parameter`

:Parameters:

    parameter: `str`
        The name of the parameter.

        *Parameter example:*
           ``parameter='geoid_name'``

:Returns:

     `bool`
        True if the parameter has been set, otherwise False.

**Examples:**

>>> f.set_parameter('earth_radius', 6371007)
>>> f.has_parameter('earth_radius')
True      
>>> f.get_parameter('earth_radius')
6371007   
>>> f.del_parameter('earth_radius')
6371007   
>>> f.has_parameter('earth_radius')
False
>>> print(f.del_parameter('earth_radius', None))
None
>>> print(f.get_parameter('earth_radius', None))
None

        '''
        return parameter in self._get_component('parameters')
    #--- End: def

    def parameters(self):
        '''Return all parameters.

.. versionadded:: 1.7.0

.. seealso:: `clear_parameters`, `get_parameter`, `has_parameter`
             `set_parameters`

:Returns:

    `dict`
        The parameters.

**Examples:**

>>> old = f.clear_parameters()
>>> old
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}
>>> f.parameters()
{}
>>> f.set_parameters(old)
>>> f.parameters()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}

        '''
        return self._get_component('parameters').copy()
    #--- End: def

    def set_parameters(self, parameters, copy=True):
        '''Set parameters.

.. versionadded:: 1.7.0

.. seealso:: `clear_parameters`, `parameters`, `set_parameter`

:Parameters:

    parameters: `dict` 
        Store the parameters from the dictionary supplied.

        *Parameter example:*
          ``parameters={'earth_radius': 6371007}``

    copy: `bool`, optional
        If False then any parameter values provided by the
        *parameters* parameter are not copied before insertion. By
        default they are deep copied.

:Returns:

    `None`

**Examples:**

>>> old = f.clear_parameters()
>>> old
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}
>>> f.parameters()
{}
>>> f.set_parameters(old)
>>> f.parameters()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}

        '''
        if copy:
            parameters = deepcopy(parameters)                
        else:
            parameters = parameters.copy()
        
        self._get_component('parameters').update(parameters)
    #--- End: def

    def set_parameter(self, term, value, copy=True):
        '''Set a parameter-valued term.

.. versionadded:: 1.7.0

.. seealso:: `parameters`

:Returns:

    `None`

**Examples:**

>>> f.set_parameter('earth_radius', 6371007)
>>> f.has_parameter('earth_radius')
True      
>>> f.get_parameter('earth_radius')
6371007   
>>> f.del_parameter('earth_radius')
6371007   
>>> f.has_parameter('earth_radius')
False
>>> print(f.del_parameter('earth_radius', None))
None
>>> print(f.get_parameter('earth_radius', None))
None

     '''
        if copy:
            value = deepcopy(value)
            
        self._get_component('parameters')[term] = value
    #--- End: def
    
#--- End: class
