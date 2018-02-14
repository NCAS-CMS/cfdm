import abc
import textwrap

from ..functions import RTOL, ATOL
from ..functions import equals as cfdm_equals

# ====================================================================
#

#
# ====================================================================

class Properties(object):
    '''

Base class for storing a data array with metadata.

A variable contains a data array and metadata comprising properties to
describe the physical nature of the data.

All components of a variable are optional.

'''
    __metaclass__ = abc.ABCMeta

    def _dump_properties(self, _prefix='', _level=0,
                         _omit_properties=None):
        '''

.. versionadded:: 1.6

:Parameters:

    omit: sequence of `str`, optional
        Omit the given CF properties from the description.

    _level: `int`, optional

:Returns:

    out: `str`

:Examples:

'''
        indent0 = '    ' * _level
        string = []

        properties = self.properties()
        
        if _omit_properties:
            for prop in _omit_properties:
                 properties.pop(prop, None)
        #--- End: if
 
        for prop, value in sorted(properties.iteritems()):
            name   = '{0}{1}{2} = '.format(indent0, _prefix, prop)
            value  = repr(value)
            subsequent_indent = ' ' * len(name)
            if value.startswith("'") or value.startswith('"'):
                subsequent_indent = '{0} '.format(subsequent_indent)
                
            string.append(textwrap.fill(name+value, 79,
                                        subsequent_indent=subsequent_indent))
        #--- End: for
        
        return '\n'.join(string)
    #--- End: def

    def del_ncvar(self):
        '''
        '''        
        return self.del_attribute('ncvar')
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_construct_type=False,
               _extra=()):
        '''
        '''
        # Check for object identity
        if self is other:
            return True

        # Check that each instance is of the same type
        if not ignore_construct_type and not isinstance(other, self.__class__):
            if traceback:
                print("{0}: Incompatible types: {0}, {1}".format(
			self.__class__.__name__,
			other.__class__.__name__))
	    return False

        # ------------------------------------------------------------
        # Check the properties
        # ------------------------------------------------------------
        if ignore_fill_value:
            ignore_properties += ('_FillValue', 'missing_value')

        self_properties  = self.properties()
        other_properties = other.properties()

        if ignore_properties:
            for prop in ignore_properties:
                self_properties.pop(prop, None)
                other_properties.pop(prop, None)
        #--- End: if
                
        if set(self_properties) != set(other_properties):
            if traceback:
                print("{0}: Different properties: {1}, {2}".format( 
                    self.__class__.__name__,
                    sorted(self_properties), sorted(other_properties)))
            return False

        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        for prop, x in self_properties.iteritems():
            y = other_properties[prop]

            if not cfdm_equals(x, y, rtol=rtol, atol=atol,
                               ignore_fill_value=ignore_fill_value,
                               ignore_data_type=ignore_data_type,
                               traceback=traceback):
                if traceback:
                    print("{0}: Different {1}: {2!r}, {3!r}".format(
                        self.__class__.__name__, prop, x, y))
                return False
        #--- End: for

        return True
    #--- End: def
        
    def get_ncvar(self, *default):
        '''
        '''        
        return self.get_attribute('ncvar', *default)
    #--- End: def

#    def name(self, default=None, ncvar=True):
#        '''Return a name for the construct.
#        '''
#        n = self.get_property('standard_name', None)
#        if n is not None:
#            return n
#        
#        n = self.get_property('long_name', None)
#        if n is not None:
#            return 'long_name:{0}'.format(n)
#
#        if ncvar:
#            n = self.get_ncvar(None)
#            if n is not None:
#                return 'ncvar%{0}'.format(n)
#            
#        return default
#    #--- End: def

    def set_ncvar(self, value):
        '''
        '''        
        return self.set_attribute('ncvar', value)
    #--- End: def

#--- End: class
