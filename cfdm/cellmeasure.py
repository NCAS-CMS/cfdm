from __future__ import print_function
from builtins import super

from . import mixin
from . import structure


class CellMeasure(mixin.NetCDFVariable,
                  mixin.PropertiesData,
                  structure.CellMeasure):
        #with_metaclass(
        #abc.ABCMeta,
        #type('NewBase', (mixin.PropertiesData, structure.CellMeasure), {}))):
    '''A CF cell measure construct.

A cell measure construct provides information that is needed about the
size or shape of the cells and that depends on a subset of the domain
axis constructs. Cell measure constructs have to be used when the size
or shape of the cells cannot be deduced from the dimension or
auxiliary coordinate constructs without special knowledge that a
generic application cannot be expected to have. The cell measure
construct consists of a numeric array of the metric data which spans a
subset of the domain axis constructs, and properties to describe the
data (in the same sense as for the field construct). The properties
must contain a `!measure` property, which indicates which metric of
the space it supplies e.g. cell horizontal areas, and a units property
consistent with the measure property e.g. square metres. It is assumed
that the metric does not depend on axes of the domain which are not
spanned by the array, along which the values are implicitly
propagated. CF-netCDF cell measure variables correspond to cell
measure constructs.

    '''
    def __init__(self, measure=None, properties={}, data=None, source=None,
                 copy=True, _use_data=True):
        '''
        '''
        super().__init__(measure=measure, properties=properties,
                         data=data, source=source, copy=copy,
                         _use_data=_use_data)
        
        if source is not None:
            self._intialise_ncvar_from(source)
    #--- End: def
    
    def dump(self, display=True, _omit_properties=None, field=None,
             key=None, _level=0, _title=None, _axes=None,
             _axis_names=None):
        '''

Return a string containing a full description of the cell measure.

:Parameters:

    display : bool, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``c.dump()`` is equivalent to
        ``print c.dump(display=False)``.

:Returns:

    out : None or str
        A string containing the description.

:Examples:

''' 
        if _title is None:
            name = self.name(default=self.get_property('units', ''))
            _title = 'Cell Measure: ' + name

        if self.get_external():
            if not (self.has_data() or self.properties()):
                _title += ' (external variable: {0})'.format(self.get_ncvar(''))
                
        return super().dump( display=display, field=field, key=key,
                             _omit_properties=_omit_properties,
                             _level=_level, _title=_title,
                             _axes=_axes, _axis_names=_axis_names)
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_construct_type=False):
        '''
        '''
        if not super().equals(
                other, rtol=rtol, atol=atol,
                traceback=traceback,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_properties=ignore_properties,
                ignore_construct_type=ignore_construct_type):
            return False

        measure0 = self.get_measure(None)
        measure1 = other.get_measure(None)
        if measure0 != measure1:
            if traceback:
                print("{0}: Different measure ({1} != {2})".format(
                    self.__class__.__name__, measure0, measure1))
            return False
        #--- End: if

        return True
    #--- End: def

    def get_external(self):
        '''Whether the cell measure construct is external.

The cell measure construct is assumed to be internal unless
sepcifically set to be external with the `set_external` method.

.. seealso:: `set_external`

:Examples 1:

>>> x = c.get_external()

:Returns:

    out:
        True if the cell measure is external, otherwise False.

:Examples 2:

>>> if c.get_external():
...     print "Cell measure is external"

        '''        
        return self._get_component('external', None, False)
    #--- End: def

    def name(self, default=None, ncvar=False, custom=None,
             all_names=False):
        '''Return a name for the cell measure.

By default the name is the first found of the following:

  1. The `!measure` attribute.
  
  2. The `standard_name` CF property.
  
  3. The `!id` attribute.

  4. The `long_name` CF property, preceeded by the string
     ``'long_name:'``.

  5. The `!ncvar` attribute, preceeded by the string ``'ncvar:'``.

  6. The value of the *default* parameter.

Note that ``c.name(identity=True)`` is equivalent to ``c.identity()``.

.. seealso:: `identity`

:Parameters:

    default : *optional*
        If no name can be found then return the value of the *default*
        parameter. By default the default is None.

    identity : bool, optional
        If True then 3. and 4. are not considered as possible names.

    ncvar : bool, optional
        If True then 1., 2., 3. and 4. are not considered as possible
        names.

:Returns:

    out : str
        A  name for the cell measure.

:Examples:

>>> f.standard_name = 'air_temperature'
>>> f.long_name = 'temperature of the air'
>>> f.ncvar = 'tas'
>>> f.name()
'air_temperature'
>>> del f.standard_name
>>> f.name()
'long_name:temperature of the air'
>>> del f.long_name
>>> f.name()
'ncvar:tas'
>>> del f.ncvar
>>> f.name()
None
>>> f.name('no_name')
'no_name'
>>> f.standard_name = 'air_temperature'
>>> f.name('no_name')
'air_temperature'

        '''
        out = []
        
        if custom is None:
            n = self.get_measure(None)
            if n is not None:
                out.append(n)

            custom = ()
        
        if all_names:    
            out += super().name(default=default,
                                                 ncvar=ncvar,
                                                 custom=custom,
                                                 all_names=all_names)
            return out
        
        if out:
            return out[-1]

        return default    
    #--- End: def

    def set_external(self, value):
        '''Set whether the cell measure construct is external.

The cell measure construct is assumed to be internal unless
sepcifically set to be external with the `set_external` method.

.. seealso:: `get_external`

:Examples 1:

>>> f.set_external(True)

:Parameters:

    value: `bool`
        Whether the cell measure construct is external or not.

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
        return self._set_component('external', None, bool(value))
    #--- End: def

#--- End: class
