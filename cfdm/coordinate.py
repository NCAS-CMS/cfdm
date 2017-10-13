from .boundedvariable import BoundedVariable


# ====================================================================
#
# Coordinate object
#
# ====================================================================

class Coordinate(BoundedVariable):
    '''

Base class for a CF dimension or auxiliary coordinate construct.


**Attributes**

===============  ========  ===================================================
Attribute        Type      Description
===============  ========  ===================================================
`!climatology`   ``bool``  Whether or not the bounds are intervals of
                           climatological time. Presumed to be False if unset.
===============  ========  ===================================================

'''
    @property
    def iscoordinate(self):
        '''True, denoting that the variable is a generic coordinate object.

.. seealso::`role`

.. seealso:: `isboundedvariable`, `isvariable`

:Examples:

>>> c.iscoordinate
True

        '''
        return True
    #--- End: def

    # ----------------------------------------------------------------
    # CF property: axis
    # ----------------------------------------------------------------
    @property
    def axis(self):
        '''The axis CF property.

The `axis` property may be used to specify the type of coordinates. It
may take one of the values `'X'`, `'Y'`, `'Z'` or `'T'` which stand
for a longitude, latitude, vertical, or time axis respectively. A
value of `'X'`, `'Y'` or `'Z'` may also also used to identify generic
spatial coordinates (the values `'X'` and `'Y'` being used to identify
horizontal coordinates).

:Examples:

>>> c.axis = 'Y'
>>> c.axis
'Y'
>>> del c.axis

>>> c.setprop('axis', 'T')
>>> c.getprop('axis')
'T'
>>> c.delprop('axis')

        '''
        return self.getprop('axis')
    #--- End: def
    @axis.setter
    def axis(self, value): 
        self.setprop('axis', value)    
    @axis.deleter
    def axis(self):       
        self.delprop('axis')

    # ----------------------------------------------------------------
    # CF property: positive
    # ----------------------------------------------------------------
    @property
    def positive(self):
        '''The positive CF property.

The direction of positive (i.e., the direction in which the coordinate
values are increasing), whether up or down, cannot in all cases be
inferred from the `units`. The direction of positive is useful for
applications displaying the data. The `positive` attribute may have
the value `'up'` or `'down'` (case insensitive).

For example, if ocean depth coordinates encode the depth of the
surface as `0` and the depth of 1000 meters as `1000` then the
`postive` property will have the value `'down'`.
      
:Examples:

>>> c.positive = 'up'
>>> c.positive
'up'
>>> del c.positive

>>> c.setprop('positive', 'down')
>>> c.getprop('positive')
'down'
>>> c.delprop('positive')

        '''
        return self.getprop('positive')
    #--- End: def

    @positive.setter
    def positive(self, value):
        self.setprop('positive', value)  
    @positive.deleter
    def positive(self):
        self.delprop('positive')       

    def dump(self, display=True, omit=(), field=None, key=None,
             _level=0, _title=None): 
        '''

Return a string containing a full description of the coordinate.

:Parameters:

    display : bool, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``c.dump()`` is equivalent to
        ``print c.dump(display=False)``.

    omit : sequence of strs
        Omit the given CF properties from the description.

:Returns:

    out : None or str
        A string containing the description.

:Examples:

'''
        if _title is None:
            if getattr(self, 'isdimension', False):
                _title = 'Dimension Coordinate: '
            elif getattr(self, 'isauxiliary', False):
                _title = 'Auxiliary Coordinate: '
            else:
                _title = 'Coordinate: '
            _title = _title + self.name(default='')

        return super(Coordinate, self).dump(
            display=display, omit=omit, field=field, key=key,
             _level=_level, _title=_title)
    #--- End: def

#--- End: class
