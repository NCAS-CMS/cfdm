from builtins import object


class RaggedContiguous(object):
    '''Mixin class for an underlying compressed ragged array.

    .. versionadded:: 1.7.0

    '''
    def get_count(self, default=ValueError()):
        '''Return the countcount_va variable for a compressed array.

    .. versionadded:: 1.7.0

    :Parameters:

        default: optional
            Return the value of the *default* parameter if a count
            variable has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The count variable.

    **Examples:**

    >>> c = d.get_count()

        '''
        try:
            return self._get_component('count_variable')
        except ValueError:
            return self._default(default,
                                 "{!r} has no count variable".format(
                                     self.__class__.__name__))

# --- End: class


class RaggedIndexed(object):
    '''Mixin class for an underlying indexed ragged array.

    '''
    def get_index(self, default=ValueError()):
        '''Return the index variable for a compressed array.

    .. versionadded:: 1.7.0

    :Parameters:

        default: optional
            Return the value of the *default* parameter if an index
            variable has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The index variable.

    **Examples:**

    >>> i = d.get_index()

        '''
        try:
            return self._get_component('index_variable')
        except ValueError:
            return self._default(default,
                                 "{!r} has no index variable".format(
                                     self.__class__.__name__))

# --- End: class
