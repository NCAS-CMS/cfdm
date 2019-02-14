from builtins import object


class RaggedContiguous(object):
    '''TODO

.. versionadded:: 1.7.0

    '''
    def get_count_variable(self, default=ValueError()):
        '''TODO

.. versionadded:: 1.7.0

:Parameters:

    default: optional
        Return the value of the *default* parameter if a count
        variable has not been set. If set to an `Exception` instance
        then it will be raised instead.

:Returns:

        The count variable.

**Examples:**

TODO

        '''
        try:
            return self._get_component('count_variable')
        except ValueError:
            return self._default(default,
                                 "{!r} has no count variable".format(
                                     self.__class__.__name__))
    #--- End: def

#--- End: class


class RaggedIndexed(object):
    '''TODO

    '''
    def get_index_variable(self, default=ValueError()):
        '''TODO

.. versionadded:: 1.7.0

:Parameters:

    default: optional
        Return the value of the *default* parameter if an index
        variable has not been set. If set to an `Exception` instance
        then it will be raised instead.

:Returns:

        The index variable.

**Examples:**

TODO

        '''
        try:
            return self._get_component('index_variable')
        except ValueError:
            return self._default(default,
                                 "{!r} has no index variable".format(
                                     self.__class__.__name__))
    #--- End: def
    
#--- End: class
