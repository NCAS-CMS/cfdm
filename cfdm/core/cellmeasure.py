import abc

import mixin

from ..structure import CellMeasure as structure_CellMeasure

# ====================================================================
#
# CellMeasure object
#
# ====================================================================

class CellMeasure(structure_CellMeasure, mixin.PropertiesData):
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
    __metaclass__ = abc.ABCMeta

    def dump(self, display=True, omit=(), field=None, key=None,
             _level=0, _title=None):
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
            if hasattr(self, 'measure'):
                _title = 'Cell Measure: ' + str(self.measure)
            elif hasattr(self.Units, 'units'):
                _title = 'Cell Measure: ' + str(self.units)
            else:
                _title = 'Cell Measure: ' + self.name(default='')

        return super(CellMeasure, self).dump(
            display=display, omit=omit, field=field, key=key,
             _level=_level, _title=_title)
    #--- End: def

    def identity(self, default=None, relaxed_identity=None):
        '''

Return the cell measure's identity.

The identity is first found of:

* The `!measure` attribute.

* The `standard_name` CF property.

* The `!id` attribute.

* The value of the *default* parameter.

:Parameters:

    default : optional
        If none of `measure`, `standard_name` and `!id` exist then
        return *default*. By default, *default* is None.

:Returns:

    out :
        The identity.

:Examples:

'''
        n = self.measure()
        if n is not None:
            return n
        
        return super(CellMeasure, self).identity(default, relaxed_identity=relaxed_identity)
    #--- End: def


    def name(self, default=None, identity=False, ncvar=False, relaxed_identity=None):
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
#        if ncvar:
#            if identity:
#                raise ValueError(
#"Can't find name: ncvar and identity parameters can't both be True")
#
#            n = getattr(self, 'ncvar', None)
#            if n is not None:
#                return 'ncvar%%%s' % n
#            
#            return default
#        #--- End: if

        if not ncvar:
            n = self.measure()
            if n is not None:
                return n

        return super(CellMeasure, self).name(default,
                                             identity=identity,
                                             ncvar=ncvar,
                                             relaxed_identity=relaxed_identity)
    #--- End: def

#--- End: class
