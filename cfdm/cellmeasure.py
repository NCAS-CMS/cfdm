from __future__ import print_function
from builtins import super
#primordial Enter Shikari - Take My Country Back
from . import mixin
from . import core


class CellMeasure(mixin.NetCDFVariable,
                  mixin.NetCDFExternal,
                  mixin.PropertiesData,
                  core.CellMeasure):
    '''A cell measure construct of the CF data model.

A cell measure construct provides information that is needed about the
size or shape of the cells and that depends on a subset of the domain
axis constructs. Cell measure constructs have to be used when the size
or shape of the cells cannot be deduced from the dimension or
auxiliary coordinate constructs without special knowledge that a
generic application cannot be expected to have.

The cell measure construct consists of a numeric array of the metric
data which spans a subset of the domain axis constructs, and
properties to describe the data. The cell measure construct specifies
a "measure" to indicate which metric of the space it supplies,
e.g. cell horizontal areas, and must have a units property consistent
with the measure, e.g. square metres. It is assumed that the metric
does not depend on axes of the domain which are not spanned by the
array, along which the values are implicitly propagated. CF-netCDF
cell measure variables correspond to cell measure constructs.

.. versionadded:: 1.7.0

    '''
    def __init__(self, measure=None, properties=None, data=None,
                 source=None, copy=True, _use_data=True):
        '''**Initialisation**

:Parameters:

    measure: `str`, optional
        Set the measure that indicates which metric given by the data
        array. Ignored if the *source* parameter is set.

        *Parameter example:*
          ``measure='area'``

        The measure may also be set after initialisation with the
        `set_measure` method.

    properties: `dict`, optional
       Set descriptive properties. The dictionary keys are property
       names, with corresponding values. Ignored if the *source*
       parameter is set.

       *Parameter example:*
          ``properties={'standard_name': 'cell_area'}``

       Properties may also be set after initialisation with the
       `properties` and `set_property` methods.

    data: `Data`, optional
        Set the data array. Ignored if the *source* parameter is set.

        The data array may also be set after initialisation with the
        `set_data` method.

    source: optional
        Initialize the measure, properties and data from those of
        *source*.

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__(measure=measure, properties=properties,
                         data=data, source=source, copy=copy,
                         _use_data=_use_data)
        
        self._initialise_netcdf(source)
    #--- End: def
    
    def dump(self, display=True, _omit_properties=None, field=None,
             key=None, _level=0, _title=None, _axes=None,
             _axis_names=None):
        '''A full description of the cell measure construct.

Returns a description of all properties, including those of
components, and provides selected values of all data arrays.

.. versionadded:: 1.7.0

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed.

:Returns:

    `None` or `str`
        The description. If *display* is True then the description is
        printed and `None` is returned. Otherwise the description is
        returned as a string.

''' 
        if _title is None:
            name = self.name(default=self.get_property('units', ''))
            _title = 'Cell Measure: ' + name

        if self.nc_external():
            if not (self.has_data() or self.properties()):

                ncvar = self.nc_get_variable(None)
                if ncvar is not None:
                    ncvar = 'ncvar%'+ncvar
                else:
                    ncvar = ''
                _title += ' (external variable: {0})'.format(ncvar)
                
        return super().dump( display=display, field=field, key=key,
                             _omit_properties=_omit_properties,
                             _level=_level, _title=_title,
                             _axes=_axes, _axis_names=_axis_names)
    #--- End: def

    def equals(self, other, rtol=None, atol=None, verbose=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_compression=False,
               ignore_type=False):
        '''Whether two cell measure constructs are the same.

Equality is strict by default. This means that:

* the same descriptive properties must be present, with the same
  values and data types, and vector-valued properties must also have
  same the size and be element-wise equal (see the *ignore_properties*
  and *ignore_data_type* parameters), and

..

* if there are data arrays then they must have same shape and data
  type, the same missing data mask, and be element-wise equal (see the
  *ignore_data_type* parameter).

Two real numbers ``x`` and ``y`` are considered equal if
``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
differences) and ``rtol`` (the tolerance on relative differences) are
positive, typically very small numbers. See the *atol* and *rtol*
parameters.

If data arrays are compressed then the compression type and the
underlying compressed arrays must be the same, as well as the arrays
in their uncompressed forms. See the *ignore_compression* parameter.

Any type of object may be tested but, in general, equality is only
possible with another cell measure construct, or a subclass of
one. See the *ignore_type* parameter.

NetCDF elements, such as netCDF variable and dimension names, do not
constitute part of the CF data model and so are not checked.

.. versionadded:: 1.7.0

:Parameters:

    other: 
        The object to compare for equality.

    atol: float, optional
        The tolerance on absolute differences between real
        numbers. The default value is set by the `cfdm.ATOL` function.
        
    rtol: float, optional
        The tolerance on relative differences between real
        numbers. The default value is set by the `cfdm.RTOL` function.

    ignore_fill_value: `bool`, optional
        If True then the "_FillValue" and "missing_value" properties
        are omitted from the comparison.

    verbose: `bool`, optional
        If True then print information about differences that lead to
        inequality.

    ignore_properties: sequence of `str`, optional
        The names of properties to omit from the comparison.

    ignore_data_type: `bool`, optional
        If True then ignore the data types in all numerical
        comparisons. By default different numerical data types imply
        inequality, regardless of whether the elements are within the
        tolerance for equality.

    ignore_compression: `bool`, optional
        If True then any compression applied to the underlying arrays
        is ignored and only the uncompressed arrays are tested for
        equality. By default the compression type and, if appliciable,
        the underlying compressed arrays must be the same, as well as
        the arrays in their uncompressed forms

    ignore_type: `bool`, optional
        Any type of object may be tested but, in general, equality is
        only possible with another cell measure construct, or a
        subclass of one. If *ignore_type* is True then
        ``CellMeasure(source=other)`` is tested, rather than the
        ``other`` defined by the *other* parameter.

:Returns: 
  
    `bool`
        Whether the two cell measure constructs are equal.

**Examples:**

>>> f.equals(f)
True
>>> f.equals(f.copy())
True
>>> f.equals('not a cell measure')
False

>>> g = f.copy()
>>> g.set_property('foo', 'bar')
>>> f.equals(g)
False
>>> f.equals(g, verbose=True)
CellMeasure: Non-common property name: foo
CellMeasure: Different properties
False

        '''
        if not super().equals(other,
                              rtol=rtol, atol=atol,
                              verbose=verbose,
                              ignore_data_type=ignore_data_type,
                              ignore_fill_value=ignore_fill_value,
                              ignore_properties=ignore_properties,
                              ignore_compression=ignore_compression,
                              ignore_type=ignore_type):
            return False

        measure0 = self.get_measure(None)
        measure1 = other.get_measure(None)
        if measure0 != measure1:
            if verbose:
                print("{0}: Different measure ({1} != {2})".format(
                    self.__class__.__name__, measure0, measure1))
            return False
        #--- End: if

        return True
    #--- End: def

    def name(self, default=None, ncvar=True, custom=None,
             all_names=False):
        '''Return a name for the cell measure construct.

By default the name is the first found of the following:

1. The "standard_name" property.
2. The measure property, preceeded by 'measure%'.
3. The "cf_role" property, preceeded by 'cf_role:'.
4. The "long_name" property, preceeded by 'long_name:'.
5. The netCDF variable name, preceeded by 'ncvar%'.
6. The value of the default parameter.

.. versionadded:: 1.7.0

:Parameters:

    default: optional
        If no other name can be found then return the value of the
        *default* parameter. By default `None` is returned in this
        case.

    ncvar: `bool`, optional
        If False then do not consider the netCDF variable name.

    all_names: `bool`, optional
        If True then return a list of all possible names.

    custom: sequence of `str`, optional
        Replace the ordered list of properties from which to seatch
        for a name. The default list is ``['standard_name', 'cf_role',
        'long_name']``.

        *Parameter example:*
          ``custom=['project']``

        *Parameter example:*
          ``custom=['project', 'long_name']``

:Returns:

        The name. If the *all_names* parameter is True then a list of
        all possible names.

**Examples:**

>>> c.get_measure()
'area'
>>> f.properties()
{'foo': 'bar',
 'long_name': 'Area',
 'standard_name': 'cell_area'}
>>> c.name()
'cell_area'
>>> c.name(all_names=True)
['cell_area', 'measure%area', 'long_name:Area', 'ncvar:areacella']

        '''
        out = []

        if custom is None:
            n = self.get_property('standard_name', None)
            if n is not None:
                out.append(n)

            if all_names or not out:
                n = self.get_measure(None)
                if n is not None:
                    out.append('measure%{}'.format(n))

            custom = ('cf_role', 'long_name')
            
        if all_names or not out:
            for prop in custom:
                n = self.get_property(prop, None)
                if n is not None:
                    out.append('{0}:{1}'.format(prop, n))
                    if not all_names:
                        break
        #--- End: if
        
        if ncvar and (all_names or not out):
            n = self.nc_get_variable(None)
            if n is not None:
                out.append('ncvar%{0}'.format(n))
        #--- End: if

        if all_names:
            if default is not None:
                out.append(default)
                
            return out
        
        if out:
            return out[-1]

        return default
    #--- End: def

#--- End: class
