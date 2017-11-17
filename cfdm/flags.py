import numpy

#from numpy import argsort    as numpy_argsort
#from numpy import atleast_1d as numpy_atleast_1d
#from numpy import ndarray    as numpy_ndarray

from copy import deepcopy

from .functions import RTOL, ATOL, equals
#from .functions import inspect as cf_inspect

from .data.data import Data

# ====================================================================
#
# Flags object
#
# ====================================================================
class Flags(object):
    '''

Self-describing CF flag values.

Stores the flag_values, flag_meanings and flag_masks CF attributes in
an internally consistent manner.

'''
    def __init__(self, values=None, masks=None, meanings=None):
        '''

**Initialization**

:Parameters:

    values: optional
        The flag_values CF property. Sets the `flag_values` attribute.

    meanings: optional
        The flag_meanings CF property. Sets the `flag_meanings`
        attribute.

    masks: optional
        The flag_masks CF property. Sets the `flag_masks` attribute.

        '''
        self.flag_values   = values
        self.flag_masks    = masks
        self.flag_meanings = meanings
    #--- End: def

    def __eq__(self, other):
        '''
x.__eq__(y) <==> x==y <==> x.equals(y)

'''
        return self.equals(other)
    #--- End: def

    def __ne__(self, other):
        '''
x.__ne__(y) <==> x!=y <==> not x.equals(y)

'''
        return not self.equals(other)
    #--- End: def

    def __hash__(self):
        '''
Return the hash value of the flags.

Note that the flags will be sorted in place.

:Returns:

    out : int
        The hash value.

:Examples:

>>> hash(f)
-956218661958673979

'''
        self.sort()

        x = [tuple(getattr(self, attr, ())) 
             for attr in ('_flag_meanings', '_flag_values', '_flag_masks')]

        return hash(tuple(x))
    #--- End: def

    def __nonzero__(self):
        '''
x.__nonzero__() <==> x!=0

'''
        for attr in ('_flag_meanings', '_flag_values', '_flag_masks'):
            if hasattr(self, attr):
                return True
        #--- End: for

        return False
    #-- End: def

    # ----------------------------------------------------------------
    # Property attribute: flag_values
    # ----------------------------------------------------------------
    @property
    def flag_values(self):
        '''

The flag_values CF attribute.

Stored as a 1-d numpy array but may be set as any array-like object.

:Examples:

>>> f.flag_values = ['a', 'b', 'c']
>>> f.flag_values
array(['a', 'b', 'c'], dtype='|S1')
>>> f.flag_values = numpy.arange(4, dtype='int8')
>>> f.flag_values
array([1, 2, 3, 4], dtype=int8)
>>> f.flag_values = 1
>>> f.flag_values
array([1])

'''
        flag = self._flag_values
        if flag is None:
            raise AttributeError("'%s' object has no attribute 'flag_values'" %
                                 self.__class__.__name__)
            
        return flag
    #--- End: def
    @flag_values.setter
    def flag_values(self, value):
        if value is None:
            self._flag_values = None
            return

        value = Data.asdata(value)
        if not value.ndim:
            value = value.expand_dims()

        self._flag_values = value
    #--- End: def
    @flag_values.deleter
    def flag_values(self):
        if self._flag_values is None:
            raise AttributeError("Can't delete CF property 'flag_values'")            

        self._flag_values = None
    #--- End: def

    # ----------------------------------------------------------------
    # Property attribute: flag_masks
    # ----------------------------------------------------------------
    @property
    def flag_masks(self):
        '''

The flag_masks CF attribute.

Stored as a 1-d numpy array but may be set as array-like object.

:Examples:

>>> f.flag_masks = numpy.array([1, 2, 4], dtype='int8')
>>> f.flag_masks
array([1, 2, 4], dtype=int8)
>>> f.flag_masks = 1
>>> f.flag_masks
array([1])

'''
        flag = self._flag_masks
        if flag is None:
            raise AttributeError("'%s' object has no attribute 'flag_masks'" %
                                 self.__class__.__name__)
            
        return flag
    #--- End: def
    @flag_masks.setter
    def flag_masks(self, value):
        if value is None:
            self._flag_masks = value
            return
        
        value = Data.asdata(value)
        if not value.ndim:
            value = value.expand_dims()
            
        self._flag_masks = value
    #--- End: def
    @flag_masks.deleter
    def flag_masks(self):
        if self._flag_masks is None:
            raise AttributeError("Can't delete CF property 'flag_masks'")            

        self._flag_masks = None
    #--- End: def

    # ----------------------------------------------------------------
    # Property attribute: flag_meanings
    # ----------------------------------------------------------------
    @property
    def flag_meanings(self):
        '''

The flag_meanings CF attribute.

Stored as a 1-d numpy string array but may be set as a space delimited
string or any array-like object.

:Examples:

>>> f.flag_meanings = 'low medium      high'
>>> f.flag_meanings
array(['low', 'medium', 'high'],
      dtype='|S6')
>>> f.flag_meanings = ['left', 'right']
>>> f.flag_meanings
array(['left', 'right'],
      dtype='|S5')
>>> f.flag_meanings = 'ok'
>>> f.flag_meanings
array(['ok'],
      dtype='|S2')
>>> f.flag_meanings = numpy.array(['a', 'b'])
>>> f.flag_meanings
array(['a', 'b'],
      dtype='|S1')

'''
        flag = self._flag_meanings
        if flag is None:
            raise AttributeError("'%s' object has no attribute 'flag_meanings'" %
                                 self.__class__.__name__)
            
        return flag
    #--- End: def
    @flag_meanings.setter
    def flag_meanings(self, value):
        if value is None:
            self._flag_meanings = value
            return

        value = Data.asdata(value)
        if not value.ndim:
            value = value.expand_dims()

        self._flag_meanings = value
    #--- End: def
    @flag_meanings.deleter
    def flag_meanings(self):
        if self._flag_meanings is None:
            raise AttributeError("Can't delete CF property 'flag_meanings'")            
        
        self._flag_meanings = None
    #--- End: def

    def __repr__(self):
        '''x.__repr__() <==> repr(x)

        '''
        string = []

        flag = self._flag_values
        if flag is not None:
            string.append('flag_values={0}'.format(flag))

        flag = self._flag_masks
        if flag is not None:
            string.append('flag_masks={0}'.format(flag))


        flag = self._flag_meanings
        if flag is not None:
            string.append('flag_meanings={0}'.format(flag))

        return '<{0}: {1}>'.format(self.__class__.__name__, ', '.join(string))
    #--- End: def

    def copy(self):
        '''

Return a deep copy.

Equivalent to ``copy.deepcopy(f)``

:Returns:

    out :
        The deep copy.

:Examples:

>>> f.copy()

'''
        return deepcopy(self)
    #--- End: def

    def dump(self, display=True, _level=0):
        '''

Return a string containing a full description of the instance.

:Parameters:
 
    display : bool, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``f.dump()`` is equivalent to
        ``print f.dump(display=False)``.

:Returns:

    out : None or str
        A string containing the description.

:Examples:


'''
        indent0 = '    ' * _level
        indent1 = '    ' * (_level+1)

        string = ['%sFlags:' % indent0]

        for attr in ('_flag_values', '_flag_meanings', '_flag_masks'):
            value = getattr(self, attr, None)
            if value is not None:
                string.append('%s%s = %s' % (indent1, attr[1:], list(value)))
        #--- End: for
                
        string = '\n'.join(string)
        
        if display:
            print string
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None,
               ignore_fill_value=False, traceback=False):
        '''

True if two groups of flags are logically equal, False otherwise.

Note that both instances are sorted in place prior to the comparison.

:Parameters:

    other : 
        The object to compare for equality.

    atol : float, optional
        The absolute tolerance for all numerical comparisons, By
        default the value returned by the `ATOL` function is used.

    rtol : float, optional
        The relative tolerance for all numerical comparisons, By
        default the value returned by the `RTOL` function is used.

    ignore_fill_value : bool, optional
        If True then data arrays with different fill values are
        considered equal. By default they are considered unequal.

    traceback : bool, optional
        If True then print a traceback highlighting where the two
        instances differ.

:Returns:

    out : bool
        Whether or not the two instances are equal.
 
:Examples:

>>> f
<CF Flags: flag_values=[1 0 2], flag_masks=[2 0 2], flag_meanings=['medium' 'low' 'high']>
>>> g
<CF Flags: flag_values=[2 0 1], flag_masks=[2 0 2], flag_meanings=['high' 'low' 'medium']>
>>> f.equals(g) 
True
>>> f
<CF Flags: flag_values=[0 1 2], flag_masks=[0 2 2], flag_meanings=['low' 'medium' 'high']>
>>> g
<CF Flags: flag_values=[0 1 2], flag_masks=[0 2 2], flag_meanings=['low' 'medium' 'high']>

'''
        # Check that each instance is the same type
        if self.__class__ != other.__class__:
            if traceback:
                print("%s: Different type: %s, %s" %
                      (self.__class__.__name__,
                       self.__class__.__name__, other.__class__.__name__))
            return False
        #--- End: if

        self.sort()
        other.sort()

        # Set default tolerances
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()        

        for attr in ('_flag_meanings', '_flag_values', '_flag_masks'):
            if hasattr(self, attr):
                if not hasattr(other, attr):
                    if traceback:
                        print("%s: Different attributes: %s" %
                              (self.__class__.__name__, attr[1:]))
                    return False

                x = getattr(self, attr)
                y = getattr(other, attr)

                if (x.shape != y.shape or 
                    not equals(x, y, rtol=rtol, atol=atol,
                               ignore_fill_value=ignore_fill_value,
                               traceback=traceback)):
                    if traceback:
                        print("%s: Different '%s': %r, %r" %
                              (self.__class__.__name__, attr[1:], x, y))
                    return False

            elif hasattr(other, attr): 
                if traceback:
                    print("%s: Different attributes: %s" %
                          (self.__class__.__name__, attr[1:]))
                return False
        #--- End: for

        return True
    #--- End: def

#    def inspect(self):
#        '''
#
#Inspect the object for debugging.
#
#.. seealso:: `cf.inspect`
#
#:Returns: 
#
#    None
#
#'''
#        print cf_inspect(self)
#    #--- End: def

    def sort(self):
        '''

Sort the flags in place.

By default sort by flag values. If flag values are not present then
sort by flag meanings. If flag meanings are not present then sort by
flag_masks.

:Returns:

    None

:Examples:

>>> f
<CF Flags: flag_values=[2 0 1], flag_masks=[2 0 2], flag_meanings=['high' 'low' 'medium']>
>>> f.sort()
>>> f
<CF Flags: flag_values=[0 1 2], flag_masks=[0 2 2], flag_meanings=['low' 'medium' 'high']>

'''
        if not self:
            return

        # Sort all three attributes
        for attr in ('flag_values', '_flag_meanings', '_flag_masks'):
            if hasattr(self, attr):
                indices = numpy.argsort(getattr(self, attr))
                break
        #--- End: for

        for attr in ('_flag_values', '_flag_meanings', '_flag_masks'):
            if hasattr(self, attr):
                array      = getattr(self, attr).view()
                array[...] = array[indices]
        #--- End: for
    #--- End: def

#--- End: class
