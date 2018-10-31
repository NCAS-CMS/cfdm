from builtins import object


class RaggedContiguous(object):
    '''TODO
    '''

    def get_count_variable(self, *default):
        '''TODO

.. versionadded:: 1.7

:Parameters:

    default: optional
        Return *default* if the count variable has not been set.

:Returns:

    out:
        TODO

**Examples**

TODO
        '''
        return self._get_component('count_variable', *default)
#        try:
#            return self._count_variable
#        except AttributeError:
#            if default:
#                return default[0]
#
#            raise AttributeError("{!r} has no count variable".format(
#                self.__class__.__name__))
    #--- End: def

#--- End: class


class RaggedIndexed(object):
    '''TODO

    '''
    def get_index_variable(self, *default):
        '''TODO

.. versionadded:: 1.7

:Parameters:

    default: optional
        Return *default* if the index variable has not been set.

:Returns:

    out:
        TODO

**Examples**

TODO

        '''
        return self._get_component('index_variable', *default)
#        try:
#            return self._index_variable
#        except AttributeError:
#            if default:
#                return default[0]
#
#            raise AttributeError("{!r} has no index variable".format(
#                self.__class__.__name__))
    #--- End: def
    
#--- End: class
