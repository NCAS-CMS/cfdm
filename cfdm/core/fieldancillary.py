from .abstract import AbstractArrayConstruct

class FieldAncillary(AbstractArrayConstruct):
    '''A CF field ancillary construct.
'''

    @property
    def isfieldancillary(self):
        '''True, denoting that the variable is a field ancillary object.

.. versionadded:: 1.6

:Examples:

>>> f.isfieldancillary
True

        '''
        return True
    #--- End: def

    def dump(self, display=True, omit=(), field=None, key=None,
             _level=0, _title=None):
        '''Return a string containing a full description of the field ancillary
object.

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``f.dump()`` is equivalent to
        ``print f.dump(display=False)``.

:Returns:

    out: `None` or `str`
        A string containing the description.

:Examples:

        '''
        if _title is None:
            _title = 'Field Ancillary: ' + self.name(default='')

        return super(FieldAncillary, self).dump(
            display=display, omit=omit, field=field, key=key,
             _level=_level, _title=_title)
    #--- End: def
    
    def equals(self, other, rtol=None, atol=None,
               ignore_data_type=False, ignore_fill_value=False,
               traceback=False, ignore=(), ignore_type=False, **kwargs):
        '''True if two field ancillary objects are equal, False otherwise.

.. versionadded:: 1.6

:Parameters:

    other: 
        The object to compare for equality.

    {+atol}

    {+rtol}

    ignore_fill_value: `bool`, optional
        If True then data arrays with different fill values are
        considered equal. By default they are considered unequal.

    traceback: `bool`, optional
        If True then print a traceback highlighting where the two
        {+variable}s differ.

    ignore: `tuple`, optional
        The names of CF properties to omit from the comparison.

:Returns: 

    out: `bool`
        Whether or not the two {+variable}s are equal.

:Examples:

>>> f.equals(f)
True
>>> g = f + 1
>>> f.equals(g)
False
>>> g -= 1
>>> f.equals(g)
True
>>> f.setprop('name', 'name0')
>>> g.setprop('name', 'name1')
>>> f.equals(g)
False
>>> f.equals(g, ignore=['name'])
True

        '''
        return super(FieldAncillary, self).equals(other, rtol=rtol,
                                                  atol=atol,
                                                  ignore_data_type=ignore_data_type,
                                                  ignore_fill_value=gnore_fill_value,
                                                  traceback=traceback,
                                                  ignore=ignore,
                                                  ignore_type=ignore_type,
                                                  **kwargs)
    #--- End: def
    
#--- End: class
