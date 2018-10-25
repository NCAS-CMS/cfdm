from builtins import object


class External(object):
    '''TODO

    '''
    def get_external(self):
        '''TODO Whether the construct is external.

The construct is assumed to be internal unless sepcifically set to be
external with the `set_external` method.

.. seealso:: `set_external`

:Examples 1:

>>> x = c.get_external()

:Returns:

    out: `bool`
        True if the construct is external, otherwise False.

:Examples 2:

>>> if c.get_external():
...     print "Is external"

        '''        
        return self._get_component('external', False)
    #--- End: def

    def set_external(self, value):
        '''TODO Set whether the construct is external.

The construct is assumed to be internal unless sepcifically set to be
external with the `set_external` method.

.. seealso:: `get_external`

:Examples 1:

>>> f.set_external(True)

:Parameters:

    value: `bool`
        Whether the construct is external or not.

:Returns:

     `None`

:Examples 2:

>>> c.set_external(True)
>>> c.get_external()
True
>>> c.set_external(False)
>>> c.get_external()
False

        '''
        return self._set_component('external', bool(value), copy=False)
    #--- End: def

#--- End: class
