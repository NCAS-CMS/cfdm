class RaggedContiguous:
    '''Mixin class for an underlying compressed ragged array.

    .. versionadded:: (cfdm) 1.7.0

    '''
    def get_count(self, default=ValueError()):
        '''Return the count variable for a compressed array.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the count
            variable has not been set.

            {{default Exception}}

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
