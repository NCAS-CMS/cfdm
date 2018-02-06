import abc
import textwrap

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
        return self._del_attribute('ncvar')
    #--- End: def

    def get_ncvar(self, *default):
        '''
        '''        
        return self._get_attribute('ncvar', *default)
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
        return self._set_attribute('ncvar', value)
    #--- End: def

#--- End: class
