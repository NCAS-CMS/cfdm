from __future__ import print_function
from builtins import (str, super, zip)
#primordial Kadavar - Come Back Life
import re
from . import mixin
from . import core

from . import Constructs
from . import Domain

_debug = False
       

class Field(mixin.NetCDFDataVariable,
            mixin.NetCDFVariable,
            mixin.ConstructAccess,
            mixin.PropertiesData,
            core.Field):
    '''A field construct of the CF data model.

The field construct is central to the CF data model, and includes all
the other constructs. A field corresponds to a CF-netCDF data variable
with all of its metadata. All CF-netCDF elements are mapped to a field
construct or some element of the CF field construct. The field
construct contains all the data and metadata which can be extracted
from the file using the CF conventions.

The field construct consists of a data array and the definition of its
domain (that describes the locations of each cell of the data array),
field ancillary constructs containing metadata defined over the same
domain, and cell method constructs to describe how the cell values
represent the variation of the physical quantity within the cells of
the domain. The domain is defined collectively by the following
constructs of the CF data model: domain axis, dimension coordinate,
auxiliary coordinate, cell measure, coordinate reference and domain
ancillary constructs.

The field construct also has optional properties to describe aspects
of the data that are independent of the domain. These correspond to
some netCDF attributes of variables (e.g. units, long_name and
standard_name), and some netCDF global file attributes (e.g. history
and institution).

.. versionadded:: 1.7.0

    '''
    def __new__(cls, *args, **kwargs):
        '''
        '''
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        instance._Domain     = Domain
        return instance
    #--- End: def

    def __init__(self, properties=None, source=None, copy=True,
                 _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

        *Parameter example:*
           ``properties={'standard_name': 'air_temperature'}``
        
        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.

    source: optional
        Initialize the properties, data and metadata constructs from
        those of *source*.
        
    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''        
        # Initialize the new field with attributes and CF properties
        core.Field.__init__(self, properties=properties,
                            source=source, copy=copy,
                            _use_data=_use_data)
        
        self._initialise_netcdf(source)
    
        self._set_component('HDFgubbins', 'TO DO', copy=False)
    #--- End: def

    def __repr__(self):
        '''Called by the `repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__,
                                   self._one_line_description())
    #--- End: def

    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

        '''
        title = "Field: {0}".format(self.name(''))

        # Append the netCDF variable name
        ncvar = self.nc_get_variable(None)
        if ncvar is not None:
            title += " (ncvar%{0})".format(ncvar)
        
        string = [title]
        string.append(''.ljust(len(string[0]), '-'))

        # Units
        units = getattr(self, 'units', '')
        calendar = getattr(self, 'calendar', None)
        if calendar is not None:
            units += ' {0} {1}'.format(calendar)
            
        axis_name = self.domain_axis_name

        # Axes
        data_axes = self.get_data_axes(())
        non_spanning_axes = set(self.domain_axes()).difference(data_axes)

        axis_names = self._unique_domain_axis_names()
        
        # Data
        string.append(
            'Data            : {0}'.format(self._one_line_description(axis_names)))

        # Cell methods
        cell_methods = self.cell_methods()
        if cell_methods:
            x = []
            for cm in list(cell_methods.values()):
                cm = cm.copy()
                cm.set_axes(tuple([axis_names.get(axis, axis)
                                   for axis in cm.get_axes(())]))                
                x.append(str(cm))
                
            c = ' '.join(x)
            
            string.append('Cell methods    : {0}'.format(c))
        #--- End: if
        
        def _print_item(self, key, variable, axes, dimension_coord):
            '''Private function called by __str__'''
            
            if dimension_coord:
                # Dimension coordinate
                axis = self.get_construct_data_axes(key)[0]
                name = variable.name(ncvar=True, default=key)
                if variable.has_data():
                    name += '({0})'.format(variable.get_data().size)
                elif hasattr(variable, 'nc_get_external'):
                    if variable.nc_get_external():
                        ncvar = variable.nc_get_variable(None)
                        if ncvar is not None:
                            x.append(' (external variable: ncvar%{})'.format(ncvar))
                        else:
                            x.append(' (external variable)')
                            
                if variable is None:
                    return name
                          
                x = [name]
                
            else:
                # Auxiliary coordinate
                # Cell measure
                # Field ancillary
                # Domain ancillary
                x = [variable.name(ncvar=True, default=key)]

                if variable.has_data():
                    shape = [axis_names[axis] for axis in axes]
                    shape = str(tuple(shape)).replace("'", "")
                    shape = shape.replace(',)', ')')
                    x.append(shape)
                elif hasattr(variable, 'nc_get_external'):
                    if variable.nc_get_external():
                        ncvar = variable.nc_get_variable(None)
                        if ncvar is not None:
                            x.append(' (external variable: ncvar%{})'.format(ncvar))
                        else:
                            x.append(' (external variable)')
            #--- End: if
                
            if variable.has_data():
                x.append(' = {0}'.format(variable.get_data()))
                
            return ''.join(x)
        #--- End: def
                          
        # Field ancillary variables
        x = [_print_item(self, cid, anc, self.get_construct_data_axes(key=cid), False)
             for cid, anc in sorted(self.field_ancillaries().items())]
        if x:
            string.append('Field ancils    : {}'.format(
                '\n                : '.join(x)))


        string.append(str(self.domain))
#        x = []
#        for key in tuple(non_spanning_axes) + data_axes:
#            for dc_key, dim in list(self.dimension_coordinates().items()):
#                if self.constructs_data_axes()[dc_key] == (key,):
#                    name = dim.name(default='id%{0}'.format(dc_key), ncvar=True)
#                    y = '{0}({1})'.format(name, dim.get_data().size)
#                    if y != axis_names[key]:
#                        y = '{0}({1})'.format(name, axis_names[key])
#                    if dim.has_data():
#                        y += ' = {0}'.format(dim.get_data())
#                        
#                    x.append(y)
#        #--- End: for
#        string.append('Dimension coords: {}'.format('\n                : '.join(x)))
#
#        # Auxiliary coordinates
#        x = [_print_item(self, aux, v, False) 
#             for aux, v in sorted(self.auxiliary_coordinates().items())]
#        if x:
#            string.append('Auxiliary coords: {}'.format(
#                '\n                : '.join(x)))
#        
#        # Cell measures
#        x = [_print_item(self, msr, v, False)
#             for msr, v in sorted(self.cell_measures().items())]
#        if x:
#            string.append('Cell measures   : {}'.format(
#                '\n                : '.join(x)))
#            
#        # Coordinate references
#        x = sorted([str(ref) for ref in list(self.coordinate_references().values())])
#        if x:
#            string.append('Coord references: {}'.format(
#                '\n                : '.join(x)))
#            
#        # Domain ancillary variables
#        x = [_print_item(self, cid, anc, False)
#             for cid, anc in sorted(self.domain_ancillaries().items())]
#        if x:
#            string.append('Domain ancils   : {}'.format(
#                '\n                : '.join(x)))
#                                      
#        string.append('')
        
        return '\n'.join(string)
    #--- End def

    def __getitem__(self, indices):
        '''Return a subspace of the field defined by indices.

f.__getitem__(indices) <==> f[indices]

The new subspace contains the same properties and similar metadata
constructs to the original field, but the latter are also subspaced
when they span domain axis constructs that have been changed.

Indexing follows rules that are very similar to the numpy indexing
rules, the only differences being:

* An integer index i takes the i-th element but does not reduce the
  rank by one.

* When two or more dimensions' indices are sequences of integers then
  these indices work independently along each dimension (similar to
  the way vector subscripts work in Fortran). This is the same
  behaviour as indexing on a Variable object of the netCDF4 package.

:Returns:

    `Field`
        The subspace of the field construct.

**Examples:**

>>> f.data.shape
(1, 10, 9)
>>> f[:, :, 1].data.shape
(1, 10, 1)
>>> f[:, 0].data.shape
(1, 1, 9)
>>> f[..., 6:3:-1, 3:6].data.shape
(1, 3, 3)
>>> f[0, [2, 9], [4, 8]].data.shape
(1, 2, 2)
>>> f[0, :, -2].data.shape
(1, 10, 1)

        ''' 
        data  = self.get_data()
        shape = data.shape

        indices = data._parse_indices(indices)
        indices = tuple(indices)
        
        new = self.copy(data=False)

        data_axes = new.get_data_axes()
        
        # Open any files that contained the original data (this not
        # necessary, is an optimsation)
        
        # ------------------------------------------------------------
        # Subspace the field's data
        # ------------------------------------------------------------
        new.set_data(data[tuple(indices)], data_axes)

        # ------------------------------------------------------------
        # Subspace other constructs that contain arrays
        # ------------------------------------------------------------
        self_constructs = self._get_constructs()
        new_constructs_data_axes = new.constructs_data_axes()
        
        for key, construct in new.data_constructs().items():
            data = self.get_construct(key=key).get_data(None)
            if data is None:
                # This construct has no data
                continue

            needs_slicing = False
            dice = []
            for axis in new_constructs_data_axes[key]:
                if axis in data_axes:
                    needs_slicing = True
                    dice.append(indices[data_axes.index(axis)])
                else:
                    dice.append(slice(None))
            #--- End: for

            if needs_slicing:
                new_data = data[tuple(dice)]
            else:
                new_data = data.copy()

            construct.set_data(new_data, copy=False)
        #--- End: for

        # Replace domain axes
        domain_axes = new.domain_axes()
        new_constructs = new._get_constructs()
        for key, size in zip(data_axes, new.get_data().shape):
            domain_axis = domain_axes[key].copy()
            domain_axis.set_size(size)
            new_constructs.replace(key, domain_axis)

        return new
    #--- End: def

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------

#    def _unique_construct_names(self, constructs):
#        '''
#
#        '''    
#        key_to_name = {}
#        name_to_keys = {}
#
#        for key, construct in getattr(self, constructs)().items():
#            name = construct.name(default='cfdm%'+key)
#            name_to_keys.setdefault(name, []).append(key)
#            key_to_name[key] = name
#
#        for name, keys in name_to_keys.items():
#            if len(keys) <= 1:
#                continue
#            
#            for key in keys:
#                key_to_name[key] = '{0}{{{1}}}'.format(
#                    name,
#                    re.findall('\d+$', key)[0])
#        #--- End: for
#        
#        return key_to_name
#    #--- End: def
    
#    def _unique_domain_axis_names(self):
#        '''
#        '''    
#        key_to_name = {}
#        name_to_keys = {}
#
#        for key, value in self.domain_axes().items():
#            name_size = (self.domain_axis_name(key), value.get_size(''))
#            name_to_keys.setdefault(name_size, []).append(key)
#            key_to_name[key] = name_size
#
#        for (name, size), keys in name_to_keys.items():
#            if len(keys) == 1:
#                key_to_name[keys[0]] = '{0}({1})'.format(name, size)
#            else:
#                for key in keys:                    
#                    key_to_name[key] = '{0}{{{1}}}({2})'.format(name,
#                                                                re.findall('\d+$', key)[0],
#                                                                size)
#        #--- End: for
#        
#        return key_to_name
#    #--- End: def
    
    def _one_line_description(self, axis_names_sizes=None):
        '''
        '''
        if axis_names_sizes is None:
            axis_names_sizes = self._unique_domain_axis_names()
            
        x = [axis_names_sizes[axis] for axis in self.get_data_axes(())]
        axis_names = ', '.join(x)
        if axis_names:
            axis_names = '({0})'.format(axis_names)
            
        # Field units        
        units    = self.get_property('units', None)
        calendar = self.get_property('calendar', None)
        if units is not None:
            units = ' {0}'.format(units)
        else:
            units = ''
            
        if calendar is not None:
            units += ' {0}'.format(calendar)
            
        return "{0}{1}{2}".format(self.name(''), axis_names, units)
    #--- End: def

    def _dump_axes(self, axis_names, display=True, _level=0):
        '''Return a string containing a description of the domain axes of the
field.
    
:Parameters:
    
    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed.
    
    _level: `int`, optional

:Returns:
    
    `str`
        A string containing the description.
    
**Examples:**

        '''
        indent1 = '    ' * _level
        indent2 = '    ' * (_level+1)

        data_axes = self.get_data_axes(())

        axes = self.domain_axes()

        w = sorted(["{0}Domain Axis: {1}".format(indent1, axis_names[axis])
                    for axis in axes
                    if axis not in data_axes])

        x = ["{0}Domain Axis: {1}".format(indent1, axis_names[axis])
             for axis in data_axes]

        string = '\n'.join(w+x)

        if display:
            print(string)
        else:
            return string
    #--- End: def


#    def domain_axis_name(self, key):
#        '''
#        '''
#        constructs = self._get_constructs()
#        return constructs.domain_axis_name(key)
#    #--- End: def

    def _set_dataset_compliance(self, value):
        '''Set the report of problems encountered whilst reading the field
construct from a dataset.

.. versionadded:: 1.7.0

.. seealso:: `dataset_compliance`

:Parameters:

    value:
        TODO

:Returns:

    `None`

**Examples:**

        '''
        self._set_component('dataset_compliance', value, copy=True)
    #--- End: def    

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self, data=True):
        '''Return a deep copy of the field construct.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

Arrays within `Data` instances are copied with a copy-on-write
technique. This means that a copy takes up very little extra memory,
even when the original contains very large data arrays, and the copy
operation is fast.

.. versionadded:: 1.7.0

:Parameters:

    data: `bool`, optional
        If False then do not copy the data field construct, nor that
        of any of its metadata constructs. By default all data are
        copied.

:Returns:

        The deep copy.

**Examples:**

>>> g = f.copy()
>>> g = f.copy(data=False)
>>> g.has_data()
False

        '''
        new = super().copy(data=data)

        new._set_dataset_compliance(self.dataset_compliance())

        return new
    #--- End: def

    def del_construct(self, name=None, properties=None, measure=None,
                      ncvar=None, ncdim=None, key=None, axis=None,
                      construct_type=None, default=ValueError()):
        '''Remove a metadata construct.

The construct is identified via optional parameters. The *unique*
construct that satisfies *all* of the given criteria is removed. An
error is raised if multiple constructs satisfy all of the given
criteria.

If a domain axis construct is to be removed then it can't be spanned
by any data arrays, nor be referenced by any cell method constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`, `has_construct`,
             `set_construct`

:Parameters:

    description: `str`, optional
        Select constructs that have the given property, or other
        attribute, value.

        The description may be one of:

        * The value of the standard name property on its own. 

          *Parameter example:*
            ``description='air_pressure'`` will select constructs that
            have a "standard_name" property with the value
            "air_pressure".

        * The value of any property prefixed by the property name and
          a colon (``:``).

          *Parameter example:*
            ``description='positive:up'`` will select constructs that
            have a "positive" property with the value "up".

          *Parameter example:*
            ``description='foo:bar'`` will select constructs that have
            a "foo" property with the value "bar".

          *Parameter example:*
            ``description='standard_name:air_pressure'`` will select
            constructs that have a "standard_name" property with the
            value "air_pressure".

        * The measure of cell measure constructs, prefixed by
          ``measure%``.

          *Parameter example:*
            ``description='measure%area'`` will select "area" cell
            measure constructs.

        * A construct identifier, prefixed by ``cid%`` (see also the
          *cid* parameter).

          *Parameter example:* 
            ``description='cid%cellmethod1'`` will select cell method
            construct with construct identifier "cellmethod1". This is
            equivalent to ``cid='cellmethod1'``.

        * The netCDF variable name, prefixed by ``ncvar%``.

          *Parameter example:*
            ``description='ncvar%lat'`` will select constructs with
            netCDF variable name "lat".

        * The netCDF dimension name of domain axis constructs,
          prefixed by ``ncdim%``.

          *Parameter example:*
            ``description='ncdim%time'`` will select domain axis
            constructs with netCDF dimension name "time".

    cid: `str`, optional
        Select the construct with the given construct identifier.

        *Parameter example:*
          ``cid='domainancillary0'`` will the domain ancillary
          construct with construct identifier "domainancillary1". This
          is equivalent to ``description='cid%domainancillary0'``.

    construct_type: `str`, optional
        Select constructs of the given type. Valid types are:

          ==========================  ================================
          *construct_type*            Constructs
          ==========================  ================================
          ``'domain_ancillary'``      Domain ancillary constructs
          ``'dimension_coordinate'``  Dimension coordinate constructs
          ``'domain_axis'``           Domain axis constructs
          ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
          ``'cell_measure'``          Cell measure constructs
          ``'coordinate_reference'``  Coordinate reference constructs
          ``'cell_method'``           Cell method constructs
          ``'field_ancillary'``       Field ancillary constructs
          ==========================  ================================

        *Parameter example:*
          ``construct_type='dimension_coordinate'``

        *Parameter example:*
          ``construct_type=['auxiliary_coordinate']``

        *Parameter example:*
          ``construct_type=('domain_ancillary', 'cell_method')``

    axes: sequence of `str`, optional
        Select constructs which have data that spans one or more of
        the given domain axes, in any order. Domain axes are specified
        by their construct identifiers.

        *Parameter example:*
          ``axes=['domainaxis2']``

        *Parameter example:*
          ``axes=['domainaxis0', 'domainaxis1']``

    default: optional
        Return *default* if no metadata construct can be found. By
        default an exception is raised in this case.

        *Parameter example:*
          ``default=None``

:Returns:

        The removed metadata construct.

**Examples:**

>>> c = f.del_construct('grid_latitude')
>>> c = f.del_construct('long_name:Air Pressure')
>>> c = f.del_construct('ncvar%lat)
>>> c = f.del_construct('cid%cellmeasure0')
>>> c = f.del_construct(cid='domainaxis2')
>>> c = f.del_construct(construct_type='auxiliary_coordinate',
...                     axes=['domainaxis1'])

        '''
        cid = self.get_construct_key(name=name, properties=properties,
                                     measure=measure, ncvar=ncvar,
                                     ncdim=ncdim, key=key,
                                     construct_type=construct_type,
                                     axis=axis, default=None)
        if cid is None:
            return self._get_constructs()._default(
                default, 'No unique construct meets criteria')
            
        if cid in self.get_data_axes(()):
            raise ValueError(  # <TODO> consider other construct data axes?
                "Can't remove domain axis {!r} that is spanned by the field's data".format(cid))

        return self._get_constructs().del_construct(key=cid)
    #--- End: def

    def dump(self, display=True, _level=0, _title=None):
        '''A full description of the field construct.

Returns a description of all properties, including those of metadata
constructs and their components, and provides selected values of all
data arrays.

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
        indent = '    '      
        indent0 = indent * _level
        indent1 = indent0 + indent

        if _title is None:
            ncvar = self.nc_get_variable(None)
            _title = self.name(default=None)
            if ncvar is not None:
                if _title is None:
                    _title = "ncvar%{0}".format(ncvar)
                else:
                    _title += " (ncvar%{0})".format(ncvar)
            #--- End: if
            if _title is None:
                _title = ''
                
            _title = 'Field: {0}'.format(_title)
        #--- End: if

        line  = '{0}{1}'.format(indent0, ''.ljust(len(_title), '-'))

        # Title
        string = [line, indent0+_title, line]

        axis_to_name = self._unique_domain_axis_names()

        name = self._unique_construct_names()

        constructs_data_axes = self.constructs_data_axes()
        
        # Simple properties
        properties = self.properties()
        if properties:
           string.append(self._dump_properties(_level=_level))
               
        # Data
        data = self.get_data(None)
        if data is not None:
            x = [axis_to_name[axis] for axis in self.get_data_axes(())]

            units = self.get_property('units', None)
            if units is None:
                isreftime = bool(self.get_property('calendar', False))
            else:
                isreftime = 'since' in units
    
            if isreftime:
                data = data.asdata(data.get_dtarray())
                
            string.append('')
            string.append('{0}Data({1}) = {2}'.format(indent0,
                                                      ', '.join(x),
                                                      str(data)))
            string.append('')

        # Cell methods
        cell_methods = self.cell_methods()
        if cell_methods:
            for cm in list(cell_methods.values()):
                cm = cm.copy()
                cm.set_axes(tuple([axis_to_name.get(axis, axis)
                                   for axis in cm.get_axes(())]))
                string.append(cm.dump(display=False,  _level=_level))

            string.append('') 
        #--- End: if

        # Field ancillaries
        
        for cid, value in sorted(self.field_ancillaries().items()):
            string.append(value.dump(display=False,
                                     _axes=constructs_data_axes[cid],
                                     _axis_names=axis_to_name,
                                     _level=_level))
            string.append('') 

        string.append(self.get_domain().dump(display=False))
        
        string = '\n'.join(string)
       
        if display:
            print(string)
        else:
            return string
    #--- End: def

#    def equal_datums(self, coordinate_reference0,
#                     coordinate_reference1, rtol=None, atol=None,
#                     verbose=False, ignore_data_type=False,
#                     ignore_fill_value=False,
#                     ignore_type=False):
#        '''
#        '''
#        coordinate_references = self.coordinate_references()
#        
#        datum0 = coordinate_references[coordinate_reference0].get_datum()
#        datum1 = coordinate_references[coordinate_reference1].get_datum()
#        
#    #--- End: def
    
    def equals(self, other, rtol=None, atol=None, verbose=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_compression=False,
               ignore_type=False):
        '''Whether two field constructs are the same.

Equality is strict by default. This means that for two field
constructs to be considered equal they must have corresponding
metadata constructs and for each pair of constructs:

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
possible with another field construct, or a subclass of one. See the
*ignore_type* parameter.

NetCDF elements, such as netCDF variable and dimension names, do not
constitute part of the CF data model and so are not checked on any
construct.

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
        are omitted from the comparison, for the field construct and
        metadata constructs.

    verbose: `bool`, optional
        If True then print information about differences that lead to
        inequality.

    ignore_properties: sequence of `str`, optional
        The names of properties of the field construct (not the
        metadata constructs) to omit from the comparison. Note that
        the "Conventions" property is always omitted by default.

    ignore_data_type: `bool`, optional
        If True then ignore the data types in all numerical 
        comparisons. By default different numerical data types imply
        inequality, regardless of whether the elements are within the
        tolerance for equality.

    ignore_compression: `bool`, optional
        If True then any compression applied to underlying arrays is
        ignored and only uncompressed arrays are tested for
        equality. By default the compression type and, if appliciable,
        the underlying compressed arrays must be the same, as well as
        the arrays in their uncompressed forms

    ignore_type: `bool`, optional
        Any type of object may be tested but, in general, equality is
        only possible with another field construct, or a subclass of
        one. If *ignore_type* is True then ``Field(source=other)`` is
        tested, rather than the ``other`` defined by the *other*
        parameter.

:Returns: 
  
    `bool`
        Whether the two field constructs are equal.

**Examples:**

>>> f.equals(f)
True
>>> f.equals(f.copy())
True
>>> f.equals(f[...])
True
>>> f.equals('not a Field instance')
False

>>> g = f.copy()
>>> g.set_property('foo', 'bar')
>>> f.equals(g)
False
>>> f.equals(g, verbose=True)
Field: Non-common property name: foo
Field: Different properties
False

        '''
        ignore_properties = tuple(ignore_properties) + ('Conventions',)
            
        if not super().equals(
                other,
                rtol=rtol, atol=atol, verbose=verbose,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_properties=ignore_properties,
                ignore_compression=ignore_compression,
                ignore_type=ignore_type):
            return False

        # ------------------------------------------------------------
        # Check the constructs
        # ------------------------------------------------------------              
        if not self._equals(self._get_constructs(),
                            other._get_constructs(), rtol=rtol,
                            atol=atol, verbose=verbose,
                            ignore_data_type=ignore_data_type,
                            ignore_fill_value=ignore_fill_value,
                            ignore_compression=ignore_compression,
                            ignore_type=ignore_type):
            if verbose:
                print(
                    "{0}: Different {1}".format(self.__class__.__name__, 'constructs'))
            return False

        return True
    #--- End: def
        
    def insert_dimension(self, axis, position=0):
        '''Expand the shape of the data array.

Inserts a new size 1 axis, corresponding to an existing domain axis
construct, into the data array.

.. versionadded:: 1.7.0

.. seealso:: `squeeze`, `transpose`

:Parameters:

    axis: `str`
        The construct identifier of the domain axis construct
        corresponding to the inserted axis.

        *Parameter example:*
          ``axis='domainaxis2'``

    position: `int`, optional
        Specify the position that the new axis will have in the data
        array. By default the new axis has position 0, the slowest
        varying position. Negative integers counting from the last
        position are allowed.

        *Parameter example:*
          ``position=2``

        *Parameter example:*
          ``position=-1``

:Returns:

    `Field`
        The new field construct with expanded data axes.

**Examples:**

>>> f.data.shape
(19, 73, 96)
>>> f.insert_dimension('domainaxis3').data.shape
(1, 96, 73, 19)
>>> f.insert_dimension('domainaxis3', position=3).data.shape
(19, 73, 96, 1)
>>> f.insert_dimension('domainaxis3', position=-1).data.shape
(19, 73, 1, 96)

        '''
        f = self.copy()
        
        domain_axis = self.domain_axes().get(axis)
        data_axes = list(self.get_data_axes(()))

        if domain_axis is None:
            raise ValueError("Can't insert non-existent domain axis: {}".format(axis))
        
        if domain_axis.get_size() != 1:
            raise ValueError(
"Can't insert an axis of size {}: {!r}".format(domain_axis.get_size(), axis))

        if axis in data_axes:
            raise ValueError(
                "Can't insert a duplicate data array axis: {!r}".format(axis))
       
        data_axes.insert(position, axis)
        f.set_data_axes(data_axes)

        # Expand the dims in the field's data array
        new_data = self.data.insert_dimension(position)
        
        f.set_data(new_data, data_axes)

        return f
    #--- End: def

    def convert(self, name=None, properties=None, measure=None,
                ncvar=None, ncdim=None, key=None, axis=None,
                construct_type=None, full_domain=True):
        '''Return a new field construct based on a metadata construct.

A unique metdata construct is identified with the *description* and
*key* parameters, and a new field construct based on its properties
and data is returned. The new field construct always has domain axis
constructs corresponding to the data, and may also contain other
metadata constructs that further define its domain.

The `cfdm.read` function allows field constructs to be derived
directly from the netCDF variables that, in turn, correspond to
metadata constructs. In this case, the new field constructs will have
a domain limited to that which can be inferred from the corresponding
netCDF variable, but without the connections that are defined by the
parent netCDF data variable. This will usually result in different
field constructs than are created with the `~Field.convert` method,
regardless of the setting of the *full_domain* parameter.

.. versionadded:: 1.7.0

.. seealso:: `cfdm.read`

:Parameters:

    description: `str`, optional
        Select the construct that has the given property, or other
        attribute, value.

        The description may be one of:

        * The value of the standard name property on its own. 

          *Parameter example:*
            ``description='air_pressure'`` will select constructs that
            have a "standard_name" property with the value
            "air_pressure".

        * The value of any property prefixed by the property name and
          a colon (``:``).

          *Parameter example:*
            ``description='positive:up'`` will select constructs that
            have a "positive" property with the value "up".

          *Parameter example:*
            ``description='foo:bar'`` will select constructs that have
            a "foo" property with the value "bar".

          *Parameter example:*
            ``description='standard_name:air_pressure'`` will select
            constructs that have a "standard_name" property with the
            value "air_pressure".

        * The measure of cell measure constructs, prefixed by
          ``measure%``.

          *Parameter example:*
            ``description='measure%area'`` will select "area" cell
            measure constructs.

        * A construct identifier, prefixed by ``cid%`` (see also the
          *cid* parameter).

          *Parameter example:*
            ``description='cid%cellmethod1'`` will select cell method
            construct with construct identifier "cellmethod1". This is
            equivalent to ``cid='cellmethod1'``.

        * The netCDF variable name, prefixed by ``ncvar%``.

          *Parameter example:*
            ``description='ncvar%lat'`` will select constructs with
            netCDF variable name "lat".

        * The netCDF dimension name of domain axis constructs,
          prefixed by ``ncdim%``.

          *Parameter example:*
            ``description='ncdim%time'`` will select domain axis
            constructs with netCDF dimension name "time".

    cid: `str`, optional
        Select the construct with the given construct identifier.

        *Parameter example:*
          ``cid='domainancillary0'`` will the domain ancillary
          construct with construct identifier "domainancillary0". This
          is equivalent to ``description='cid%domainancillary0'``.

    full_domain: `bool`, optional
        If False then do not create a domain, other than domain axis
        constructs, for the new field construct. By default as much of
        the domain as possible is copied to the new field construct.

:Returns:

    `Field`
        The new field construct.

**Examples:**

>>> f = cfdm.read('file.nc')
>>> f
[<Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>]
>>> f = f[0]
>>> print(f)
Field: air_temperature (ncvar%ta)
---------------------------------
Data            : air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K
Cell methods    : grid_latitude(10): grid_longitude(9): mean where land (interval: 0.1 degrees) time(1): maximum
Field ancils    : air_temperature standard_error(grid_latitude(10), grid_longitude(9)) = [[0.76, ..., 0.32]] K
Dimension coords: atmosphere_hybrid_height_coordinate(1) = [1.5]
                : grid_latitude(10) = [2.2, ..., -1.76] degrees
                : grid_longitude(9) = [-4.7, ..., -1.18] degrees
                : time(1) = [2019-01-01 00:00:00]
Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[53.941, ..., 50.225]] degrees_N
                : longitude(grid_longitude(9), grid_latitude(10)) = [[2.004, ..., 8.156]] degrees_E
                : long_name:Grid latitude name(grid_latitude(10)) = [--, ..., kappa]
Cell measures   : measure%area(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2
Coord references: atmosphere_hybrid_height_coordinate
                : rotated_latitude_longitude
Domain ancils   : ncvar%a(atmosphere_hybrid_height_coordinate(1)) = [10.0] m
                : ncvar%b(atmosphere_hybrid_height_coordinate(1)) = [20.0]
                : surface_altitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 270.0]] m
>>> x = f.convert('domainancillary2')
>>> print(x)
Field: surface_altitude (ncvar%surface_altitude)
------------------------------------------------
Data            : surface_altitude(grid_latitude(10), grid_longitude(9)) m
Dimension coords: grid_latitude(10) = [2.2, ..., -1.76] degrees
                : grid_longitude(9) = [-4.7, ..., -1.18] degrees
Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[53.941, ..., 50.225]] degrees_N
                : longitude(grid_longitude(9), grid_latitude(10)) = [[2.004, ..., 8.156]] degrees_E
                : long_name:Grid latitude name(grid_latitude(10)) = [--, ..., kappa]
Cell measures   : measure%area(grid_longitude(9), grid_latitude(10)) = [[2391.9657, ..., 2392.6009]] km2
Coord references: rotated_latitude_longitude
>>> y = f.convert('domainancillary2', full_domain=False)
>>> print(y)
Field: surface_altitude (ncvar%surface_altitude)
------------------------------------------------
Data            : surface_altitude(grid_latitude(10), grid_longitude(9)) m
>>> g = cfdm.read('file.nc', convert='domain_ancillary')
>>> g
[<Field: ncvar%a(atmosphere_hybrid_height_coordinate(1)) m>,
 <Field: ncvar%b(atmosphere_hybrid_height_coordinate(1))>,
 <Field: surface_altitude(grid_latitude(10), grid_longitude(9)) m>,
 <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>]
>>> print(g[2])
Field: surface_altitude (ncvar%surface_altitude)
------------------------------------------------
Data            : surface_altitude(grid_latitude(10), grid_longitude(9)) m
Dimension coords: grid_latitude(10) = [2.2, ..., -1.76] degrees
                : grid_longitude(9) = [-4.7, ..., -1.18] degrees
		   
.. _Creating-field-constructs-from-metadata-constructs:

Creating field constructs from metadata constructs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Independent field constructs may be created from metadata in two ways:
either from a netCDF variable using the `cfdm.read` function, or from
a metadata construct using the `~Field.convert` method of the field
construct.

The `~Field.convert` method of the field construct identifies a unique
metadata construct and returns a new field construct based on its
properties and data. The new field construct has domain axis
constructs corresponding to the data, and (by default) any other
metadata constructs that further define its domain.

.. code-block:: python

   >>> orog = tas.convert('surface_altitude')	  
   >>> print(orog)
   Field: surface_altitude
   -----------------------
   Data            : surface_altitude(grid_latitude(10), grid_longitude(9)) m
   Dimension coords: grid_latitude(10) = [0.0, ..., 9.0] degrees
                   : grid_longitude(9) = [0.0, ..., 8.0] degrees
   Auxiliary coords: latitude(grid_latitude(10), grid_longitude(9)) = [[0.0, ..., 89.0]] degrees_north
                   : longitude(grid_longitude(9), grid_latitude(10)) = [[0.0, ..., 89.0]] degrees_east
                   : long_name:Grid latitude name(grid_latitude(10)) = [--, ..., j]
   Cell measures   : measure%area(grid_longitude(9), grid_latitude(10)) = [[0.0, ..., 89.0]] km2
   Coord references: rotated_latitude_longitude

The `~Field.convert` method has an option to only include domain axis
constructs in the new field construct, with no other metadata
constructs.

   >>> orog1 = tas.convert('surface_altitude', full_domain=False) 
   >>> print(orog1)
   Field: surface_altitude
   -----------------------
   Data            : surface_altitude(key%domainaxis2(10), key%domainaxis3(9)) m
   
The `cfdm.read` function allows field constructs to be derived
directly from the netCDF variables that correspond to metadata
constructs. In this case, the new field constructs will have a domain
limited to that which can be inferred from the corresponding netCDF
variable, but without the connections that are defined by the parent
netCDF data variable. This will often result in a new field construct
that has fewer metadata constructs than one created with the
`~Field.convert` method.

.. code-block:: python

   >>> cfdm.write(tas, 'tas.nc')
   >>> fields = cfdm.read('tas.nc', convert='domain_ancillary')
   >>> fields
   [<Field: ncvar%a(atmosphere_hybrid_height_coordinate(1)) m>,
    <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>,
    <Field: ncvar%b(atmosphere_hybrid_height_coordinate(1)) 1>,
    <Field: surface_altitude(grid_latitude(10), grid_longitude(9)) m>]
   >>> print(fields[3])
   Field: surface_altitude (ncvar%surface_altitude)
   ------------------------------------------------
   Data            : surface_altitude(grid_latitude(10), grid_longitude(9)) m
   Dimension coords: grid_latitude(10) = [0.0, ..., 9.0] degrees
                   : grid_longitude(9) = [0.0, ..., 8.0] degrees

        '''
        c0 = self.constructs(name=name, properties=properties,
                             measure=measure, ncvar=ncvar,
                             ncdim=ncdim, key=key, axis=axis,
                             construct_type=construct_type, copy=False)
        if len(c0) != 1:
            self.get_construct(name=name, properties=properties,
                               measure=measure, ncvar=ncvar,
                               ncdim=ncdim, key=key, axis=axis,
                               construct_type=construct_type, copy=False)
            return

        cid, c = c0.popitem()
        
        # ------------------------------------------------------------
        # Create a new field with the properties and data from the
        # construct
        # ------------------------------------------------------------
        f = type(self)(source=c, copy=True)

        # ------------------------------------------------------------
        # Add domain axes
        # ------------------------------------------------------------
        constructs_data_axes = self.constructs_data_axes()
        data_axes = constructs_data_axes.get(cid)
        if data_axes is not None:
            for domain_axis in data_axes:
                f.set_construct(self.domain_axes()[domain_axis],
                                key=domain_axis, copy=True)
        #--- End: if

        # ------------------------------------------------------------
        # Set the data axes
        # ------------------------------------------------------------
        if data_axes is not None:
            f.set_data_axes(axes=data_axes)

        # ------------------------------------------------------------
        # Add a more complete domain
        # ------------------------------------------------------------
        if full_domain:
            for construct_type in ('dimension_coordinate',
                                   'auxiliary_coordinate',
                                   'cell_measure'):
                for ccid, con in self.constructs(construct_type=construct_type,
                                                 axis=data_axes,
                                                 copy=False).items():
                    axes = constructs_data_axes.get(ccid)
                    if axes is None:
                        continue
    
                    if set(axes).issubset(data_axes):
                        f.set_construct(con, key=ccid, axes=axes,
                                        copy=True)
                #--- End: for
            #--- End: for
       
            # Add coordinate references which span a subset of the item's
            # axes
            for rcid, ref in self.coordinate_references().items():

                new_coordinates = [ccid for ccid in ref.coordinates()
                                   if set(constructs_data_axes[ccid]).issubset(data_axes)]

                if not new_coordinates:
                    continue

                # Still here?
                ok = True
                for ccid in ref.coordinate_conversion.domain_ancillaries().values():
                    axes = constructs_data_axes[ccid]
                    if not set(axes).issubset(data_axes):
                        ok = False
                        break
                #--- End: for

                if ok:
                    ref = ref.copy()
                    ref.coordinates(new_coordinates)
                    f.set_construct(ref, key=rcid, copy=False)                    
            #--- End: for
        #--- End: if
              
        return f
    #--- End: def
   
    def dataset_compliance(self, display=False):
        '''A report of problems encountered whilst reading the field construct
from a dataset.

.. versionadded:: 1.7.0

.. seealso:: `cfdm.read`

:Parameters:

    display: `bool`, optional
        If True print the compliance report. By default the report is
        returned as a dictionary.  the report is printed.

:Returns:

    `None` or `dict`
        The report. If *display* is True then the report is printed
        and `None` is returned. Otherwise the report is returned as a
        dictionary.

        '''
        d = self._get_component('dataset_compliance', {})

        if not display:
            return d
        
        if not d:
            print(d)
            return
    
        for key0, value0 in d.items():
            print('{{{0!r}:'.format(key0))
            print('    CF version: {0!r},'.format(value0['CF version']))
            print('    dimensions: {0!r},'.format(value0['dimensions']))
            print('    non-compliance: {')
            for key1, value1 in sorted(value0['non-compliance'].items()):
                for x in value1:
                    print('        {!r}: ['.format(key1))
                    print('            {{{0}}},'.format(
                        '\n             '.join(['{0!r}: {1!r},'.format(key2, value2)
                                                for key2, value2 in sorted(x.items())])))
                #--- End: for
                print('        ],')

            print('    },')
            print('}\n')
    #--- End: def
     
    def squeeze(self, axes=None):
        '''Remove size one axes from the data array.

By default all size one axes are removed, but particular size one axes
may be selected for removal.

.. versionadded:: 1.7.0

.. seealso:: `insert_dimension`, `transpose`

:Parameters:

    axes: (sequence of) `int`, optional
        The positions of the size one axes to be removed. By default
        all size one axes are removed. Each axis is identified by its
        original integer position. Negative integers counting from the
        last position are allowed.

        *Parameter example:*
          ``axes=0``

        *Parameter example:*
          ``axes=-2``

        *Parameter example:*
          ``axes=[2, 0]``

:Returns:

    `Field`
        The new field construct with removed data axes.

**Examples:**

>>> f.data.shape
(1, 73, 1, 96)
>>> f.squeeze().data.shape
(73, 96)
>>> f.squeeze(0).data.shape
(73, 1, 96)
>>> f.squeeze([-3, 2]).data.shape
(73, 96)

        '''
        f = self.copy()


        if axes is None:
            axes = [i for i, n in enumerate(f.data.shape) if n == 1]
        else:
            try:
                axes = self.data._parse_axes(axes)
            except ValueError as error:
                raise ValueError("Can't squeeze data: {}".format(error))

        data_axes = self.get_data_axes(())
        
#        domain_axes = self.domain_axes()
#            
#        if axes is None:
#            axes = [axis for axis in data_axes if domain_axes[axis].get_size(None) == 1]
#        else:
#            for axis in axes:
#                if domain_axes[axis].get_size() != 1:
#                    raise ValueError(
#"Can't squeeze domain axis with size {}".format(domain_axes[axis].get_size(None)))
#            #--- End: for
#            
#            axes = [axis for axis in axes if axis in data_axes]
#        #--- End: if

        new_data_axes = [data_axes[i] for i in range(self.data.ndim) if i not in axes]
        
#        new_data_axes = [axis for axis in data_axes if axis not in axes]
#        f.set_data_axes(new_data_axes)

        # Squeeze the field's data array
 #       iaxes = [data_axes.index(axis) for axis in axes]
        new_data = self.data.squeeze(axes)

        f.set_data(new_data, new_data_axes)

        return f
    #--- End: def

    def transpose(self, axes=None):
        '''Permute the axes of the data array.

.. versionadded:: 1.7.0

.. seealso:: `insert_dimension`, `squeeze`

:Parameters:

    axes: (sequence of) `int`
        The new axis order. By default the order is reversed. Each
        axis in the new order is identified by its original integer
        position. Negative integers counting from the last position
        are allowed.

        *Parameter example:*
          ``axes=[2, 0, 1]``

        *Parameter example:*
          ``axes=[-1, 0, 1]``

:Returns:

    `Field`
         The new field construct with permuted data axes.

**Examples:**

>>> f.data.shape
(19, 73, 96)
>>> f.tranpose().data.shape
(96, 73, 19)
>>> f.tranpose([1, 0, 2]).data.shape
(73, 19, 96)

        '''
        f = self.copy()
        try:
            axes = self.data._parse_axes(axes)
        except ValueError as error:
            raise ValueError("Can't transpose data: {}".format(error))

        data_axes = self.get_data_axes(())

        new_data_axes = [data_axes[i] for i in axes]
        
        # Transpose the field's data array
        new_data = self.data.transpose(axes)

        f.set_data(new_data, new_data_axes)

        return f
    #--- End: def

    def field_ancillaries(self, copy=False):
        '''Return field ancillary constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.field_ancillaries()
{}

>>> f.field_ancillaries()
{'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}

        '''
        return self._get_constructs().constructs(
            construct_type='field_ancillary', copy=copy)
    #--- End: def
    
    def cell_methods(self, copy=False):
        '''Return cell method constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`, `set_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `collections.OrderDict`
        Constructs are returned as values of an ordered dictionary,
        keyed by their construct identifiers. The order is determined
        by the order in which the cell method constructs were added to
        the field construct.

**Examples:**

>>> f.cell_methods()
OrderedDict()

>>> f.cell_methods()
OrderedDict([('cellmethod0', <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>),
             ('cellmethod1', <CellMethod: domainaxis3: maximum>)])

        '''
        return self._get_constructs().constructs(construct_type='cell_method',
                                                 copy=copy)
    #--- End: def
    
#    def cell_methods(self, copy=False):
#        '''
#        '''
#        out = self.Constructs.cell_methods(copy=copy)
#
#        if not description:
#            return self.Constructs.cell_methods()
#        
#        if not isinstance(description, (list, tuple)):
#            description = (description,)
#            
#        cms = []
#        for d in description:
#            if isinstance(d, dict):
#                cms.append([self._CellMethod(**d)])
#            elif isinstance(d, basestring):
#                cms.append(self._CellMethod.parse(d))
#            elif isinstance(d, self._CellMethod):
#                cms.append([d])
#            else:
#                raise ValueError("asd 123948u m  BAD DESCRIPTION TYPE")
#        #--- End: for
#
#        keys = self.cell_methods().keys()                    
#        f_cell_methods = self.cell_methods().values()
#        nf = len(f_cell_methods)
#
#        out = {}
#        
#        for d in cms:
#            c = self._conform_cell_methods(d)
#
#            n = len(c)
#            for j in range(nf-n+1):
#                found_match = True
#                for i in range(0, n):
#                    if not f_cell_methods[j+i].match(c[i].properties()):
#                        found_match = False
#                        break
#                #--- End: for
#            
#                if not found_match:
#                    continue
#
#                # Still here?
#                key = tuple(keys[j:j+n])
#                if len(key) == 1:
#                    key = key[0]
#
#                if key not in out:
#                    value = f_cell_methods[j:j+n]
#                    if copy:
#                    value = [cm.copy() for cm in value]                        
#
#                out[key] = value
#            #--- End: for
#        #--- End: for
#        
#        return out
#    #--- End: def

#--- End: class
