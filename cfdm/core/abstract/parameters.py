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

>>> c.get_parameter('grid_north_pole_latitude')
70.0

>>> c.get_parameter('foo')
ERROR
>>> c.get_parameter('foo', 'nonexistent term')
'nonexistent term'


        '''
        try:
            return self._get_component('parameters')[parameter]
        except KeyError:
            return self._default(default,
                                 "{!r} has no {!r} parameter".format(
                                     self.__class__.__name__, parameter))
    #--- End: def
    
    def parameters(self, parameters=None, copy=True):
        '''Return or replace all parameter-valued terms.

.. versionadded:: 1.7.0

.. seealso:: `ancillaries`

:Parameters:

    parameters: `dict`, optional
        Delete all existing named parameters, and instead store those
        from the dictionary supplied.

        *Parameter example:*
          ``parameters={'earth_radius': 6371007}``

        *Parameter example:*
          ``parameters={}``

    copy: `bool`, optional
        If False then any parameters provided by the *parameters*
        parameter are not copied before insertion. By default they are
        deep copied.

:Returns:

    `dict`
        The parameters or, if the *parameters* parameter was set, the
        original parmaeters.

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
                parameters = deepcopy(parameters)
            else:
                parameters = parameters.copy()
                
            self._set_component('parameters', parameters, copy=False)

        return out
    #--- End: def

    def set_parameter(self, term, value, copy=True):
        '''Set a parameter-valued term.

.. versionadded:: 1.7.0

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
