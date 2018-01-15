from collections import abc

from .arrayconstruct import AbstractArrayConstruct


# ====================================================================
#
# Coordinate object
#
# ====================================================================

class AbstractBounds(AbstractArrayConstruct):
    '''

'''
    __metaclass__ = abc.ABCMeta
        
    def dump(self, display=True, prefix=None, omit=(), field=None,
             key=None, _title=None, _level=0):
        '''

Return a string containing a full description of the instance.

.. versionadded:: 1.6

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``f.dump()`` is equivalent to
        ``print f.dump(display=False)``.

    omit: sequence of `str`, optional
        Omit the given CF properties from the description.

    prefix: optional
        Ignored.

:Returns:

    out: `None` or `str`
        A string containing the description.

:Examples:

>>> f.{+name}()
Data(1, 2) = [[2999-12-01 00:00:00, 3000-12-01 00:00:00]] 360_day
axis = 'T'
standard_name = 'time'

>>> f.{+name}(omit=('axis',))
Data(1, 2) = [[2999-12-01 00:00:00, 3000-12-01 00:00:00]] 360_day
standard_name = 'time'

'''
        if _title is None:
            _title = 'Auxiliary coordinate: ' + self.name(default='')

        return super(AuxiliaryCoordinate, self).dump(
            display=display, omit=omit, field=field, key=key,
             _level=_level, _title=_title)
    #--- End: def
    
        indent0 = '    ' * _level
        indent1 = '    ' * (_level+1)

        if _title is None:
            string = ['{0}{1}: {2}'.format(indent0,
                                           self.__class__.__name__,
                                           self.name(default=''))]
        else:
            string = [indent0 + _title]
                        
        _properties = self._dump_properties(omit=omit, _level=_level+1)
        if _properties:
            string.append(_properties)

        if self.hasdata:
            if field and key:
                x = ['{0}({1})'.format(field.domain_axis_name(axis),
                                       field.domain_axes()[axis].size)
                     for axis in field.construct_axes(key)]
            else:
                x = [str(s) for s in self.data.shape]
           
            string.append('{0}Data({1}) = {2}'.format(indent1,
                                                      ', '.join(x),
                                                      str(self.data)))
        #--- End: if
        
        string = '\n'.join(string)
       
        if display:
            print string
        else:
            return string
    #--- End: def

#--- End: class
