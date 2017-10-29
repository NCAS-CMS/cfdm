from collections import OrderedDict
from itertools   import izip, izip_longest
from re          import match as re_match

from .constants  import masked as cf_masked
from .domainaxis import DomainAxis
from .flags      import Flags

from .functions import (parse_indices, equals, RTOL, ATOL,
                        RELAXED_IDENTITIES)
from .variable  import Variable

_debug = False


# ====================================================================
#
# Field object
#
# ====================================================================

class Field(Variable):
    '''A CF field construct.

The field construct is central to the CF data model, and includes all
the other constructs. A field corresponds to a CF-netCDF data variable
with all of its metadata. All CF-netCDF elements are mapped to some
element of the CF field construct and the field constructs completely
contain all the data and metadata which can be extracted from the file
using the CF conventions.

The field construct consists of a data array (stored in a `Data`
object) and the definition of its domain, ancillary metadata fields
defined over the same domain (stored in `FieldAncillary` objects), and
cell methods constructs to describe how the cell values represent the
variation of the physical quantity within the cells of the domain
(stored in `CellMethod` objects).

The domain is defined collectively by various other constructs
included in the field:

====================  ================================================
Domain construct      Description
====================  ================================================
Domain axis           Independent axes of the domain stored in
                      `DomainAxis` objects

Dimension coordinate  Domain cell locations stored in
                      `DimensionCoordinate` objects

Auxiliary coordinate  Domain cell locations stored in
                      `AuxiliaryCoordinate` objects

Coordinate reference  Domain coordinate systems stored in
                      `CoordinateReference` objects

Domain ancillary      Cell locations in alternative coordinate systems
                      stored in `DomainAncillary` objects

Cell measure          Domain cell size or shape stored in
                      `CellMeasure` objects
====================  ================================================

All of the constructs contained by the field construct are optional.

The field construct also has optional properties to describe aspects
of the data that are independent of the domain. These correspond to
some netCDF attributes of variables (e.g. units, long_name and
standard_name), and some netCDF global file attributes (e.g. history
and institution).

**Miscellaneous**

Field objects are picklable.

    '''
    _DomainAxis = DomainAxis
    
    _special_properties = Variable._special_properties.union(        
        ('cell_methods',
         'flag_values',
         'flag_masks',
         'flag_meanings')
         )
    
#    def __new__(cls, **kwargs):
#        cls = object.__new__(cls)
#        cls._DomainAxis = DomainAxis
#        return cls
    
    def __init__(self, properties={}, attributes={}, data=None,
                 source=None, copy=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Provide the new field with CF properties from the dictionary's
        key/value pairs.

    attributes: `dict`, optional
        Provide the new field with attributes from the dictionary's
        key/value pairs.

    source: 

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        # Domain axes and items
        self._private = {'simple_properties' : {},
                         'special_attributes': {'items': Items()}
        }
        
        # Initialize the new field with attributes and CF properties
        super(Field, self).__init__(properties=properties,
                                    attributes=attributes,
                                    source=source,
                                    data=data,
                                    copy=copy) 

        if getattr(source, 'isfield', False):
            # Initialise items and axes from a source field
            self._private['special_attributes']['items'] = source.Items.copy(shallow=not copy)

        self._unlimited = None
    #--- End: def
    
    def __getitem__(self, indices):
        '''f.__getitem__(indices) <==> f[indices]

Return a subspace of the field defined by index values

Subspacing by axis indices uses an extended Python slicing syntax,
which is similar to :ref:`numpy array indexing
<numpy:arrays.indexing>`. There are extensions to the numpy indexing
functionality:

* Size 1 axes are never removed.

  An integer index *i* takes the *i*-th element but does not reduce
  the rank of the output array by one:

  >>> f.shape
  (12, 73, 96)
  >>> f[0].shape
  (1, 73, 96)
  >>> f[3, slice(10, 0, -2), 95:93:-1].shape
  (1, 5, 2)

* The indices for each axis work independently.

  When more than one axis's slice is a 1-d boolean sequence or 1-d
  sequence of integers, then these indices work independently along
  each axis (similar to the way vector subscripts work in Fortran),
  rather than by their elements:

  >>> f.shape
  (12, 73, 96)
  >>> f[:, [0, 72], [5, 4, 3]].shape
  (12, 2, 3)

  Note that the indices of the last example would raise an error when
  given to a numpy array.

* Boolean indices may be any object which exposes the numpy array
  interface, such as the field's coordinate objects:

  >>> f[:, f.coord('latitude')<0].shape
  (12, 36, 96)

>>> f.shape
(12, 73, 96)
>>> f[...].shape
(12, 73, 96)

.. versionadded:: 1.6

.. seealso:: `__setitem__`

:Examples 1:

>>> g = f[..., 0, :6, 9:1:-2, [1, 3, 4]]

:Returns:

    out: `Field`

:Examples 2:

>>> f.shape
(12, 73, 96)
>>> f[...].shape
(12, 73, 96)

        ''' 
        data  = self.data
        shape = data.shape

        # Parse the index
        if not isinstance(indices, tuple):
            indices = (indices,)

        indices = parse_indices(shape, indices)

        new = self.copy()

        # Open any files that contained the original data (this not
        # necessary, is an optimsation)
        
        # ------------------------------------------------------------
        # Subspace the field's data
        # ------------------------------------------------------------
        new._Data = self.data[tuple(indices)]

        # ------------------------------------------------------------
        # Subspace items
        # ------------------------------------------------------------
        Items = new.Items
        data_axes = new.data_axes()

        items = new.items(role=('d', 'a', 'm', 'f', 'c'), axes=data_axes)
        for key, item in items.iteritems():
            item_axes = new.item_axes(key)
            dice = []
            for axis in item_axes:
                if axis in data_axes:
                    dice.append(indices[data_axes.index(axis)])
                else:
                    dice.append(slice(None))
            #--- End: for

            if _debug:
                print '    item:', repr(item)
                print '    dice = ', dice
                
            # Replace existing item with its subspace
            Items[key] = item[tuple(dice)]
        #--- End: for

        # Replace existing domain axes
        Axes = new.Axes
        for axis, size in izip(data_axes, new.shape):
            Axes[axis] = self._DomainAxis(size, ncdim=Axes[axis].ncdim)

        return new
    #--- End: def

    def _no_None_dict(self, d):
        '''
        '''
        return dict((key, value) for key, value in d.iteritems() 
                    if value is not None)
    #--- End: def

    def __repr__(self):
        '''Called by the :py:obj:`repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        if self.hasdata:
            axis_name = self.axis_name
            axis_size = self.axis_size
            x = ['{0}({1})'.format(axis_name(axis), axis_size(axis))
                 for axis in self.data_axes()]
            axis_names = '({0})'.format(', '.join(x))
        else:
            axis_names = ''
            
        # Field units
        units = getattr(self, 'units', '')
        calendar = getattr(self, 'calendar', None)
        if calendar:
            units += '{0} calendar'.format(calendar)

        return '<{0}: {1}{2} {3}>'.format(self.__class__.__name__,
                                          self.name(default=''),
                                          axis_names, units)
    #--- End: def

    def __str__(self):
        '''Called by the :py:obj:`str` built-in function.

x.__str__() <==> str(x)

        '''
        string = ["{} field summary".format(self.name(''))]
        string.append(''.ljust(len(string[0]), '-'))

        # Units
        units = getattr(self, 'units', '')
        calendar = getattr(self, 'calendar', None)
        if calendar:
            units += ' {0} calendar'.format(calendar)
            
        axis_name = self.axis_name
        axis_size = self.axis_size        
        
        # Data
        if self.hasdata:
            x = ['{0}({1})'.format(axis_name(axis), axis_size(axis))
                 for axis in self.data_axes()]
            string.append('Data           : {0}({1}) {2}'.format(
                self.name(''), ', '.join(x), units))
        elif units:
            string.append('Data           : {0}'.format(units))

        # Cell methods
        cell_methods = getattr(self, 'cell_methods', None)
        if cell_methods:
            string.append('Cell methods   : {0}'.format(self.cell_methods))

        axis_to_name = {}
        def _print_item(self, key, variable, dimension_coord):
            '''Private function called by __str__'''

            if dimension_coord:
                # Dimension coordinate
                name = "{0}({1})".format(axis_name(key), axis_size(key))
                axis_to_name[key] = name
                
                variable = self.Items.get(key, None)

                if variable is None:
                    return name
                
                x = [name]

            else:
                # Auxiliary coordinate
                # Cell measure
                # Field ancillary
                # Domain ancillary
                shape = [axis_to_name[axis] for axis in self.Items.axes(key)]
                shape = str(tuple(shape)).replace("'", "")
                shape = shape.replace(',)', ')')
                x = [variable.name(key)]
                x.append(shape)
            #--- End: if

            if variable.hasdata:
                x.append(' = {}'.format(variable.data))

            return ''.join(x)
        #--- End: def

        # Axes and dimension coordinates
        ddd = self.data_axes()
        if ddd is None:
            ddd = ()
        non_spanning_axes = set(self.Axes).difference(ddd)
        x1 = [_print_item(self, dim, None, True)
              for dim in sorted(non_spanning_axes)]
        x2 = [_print_item(self, dim, None, True)
              for dim in ddd]
        x = x1 + x2
        if x:
            string.append('Axes           : {}'.format(
                '\n               : '.join(x)))
            
        # Auxiliary coordinates
        x = [_print_item(self, aux, v, False) 
             for aux, v in sorted(self.Items.auxs().iteritems())]
        if x:
            string.append('Aux coords     : {}'.format(
                '\n               : '.join(x)))

        # Cell measures
        x = [_print_item(self, msr, v, False)
             for msr, v in sorted(self.Items.msrs().iteritems())]
        if x:
            string.append('Cell measures  : {}'.format(
                '\n               : '.join(x)))

        # Coordinate references
        x = sorted([ref.name(default='')
                    for ref in self.Items.refs().itervalues()])
        if x:
            string.append('Coord refs     : {}'.format(
                '\n               : '.join(x)))

        # Domain ancillary variables
        x = [_print_item(self, key, anc, False)
             for key, anc in sorted(self.Items.domain_ancs().iteritems())]
        if x:
            string.append('Domain ancils  : {}'.format(
                '\n               : '.join(x)))
            
        # Field ancillary variables
        x = [_print_item(self, key, anc, False)
             for key, anc in sorted(self.Items.field_ancs().iteritems())]
        if x:
            string.append('Field ancils   : {}'.format(
                '\n               : '.join(x)))
            
        string.append('')
        
        return '\n'.join(string)
    #--- End def

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def Axes(self):
        '''
        '''
        try:
            return self.Items.Axes
        except (AttributeError, KeyError):
            return {}
    #--- End: def

    @property
    def Flags(self):
        '''A `Flags` object containing self-describing CF flag values.

A `Flags` object stores the `flag_values`, `flag_meanings` and
`flag_masks` CF properties in an internally consistent manner.

        '''
        return self._get_special_attr('Flags')
    @Flags.setter
    def Flags(self, value):
        self._set_special_attr('Flags', value)
    @Flags.deleter
    def Flags(self):
        self._del_special_attr('Flags')

    @property
    def Items(self):
        return self._private['special_attributes']['items']
        
    @property
    def ncdimensions(self):
        '''
        '''
        out = {}
        for dim, axis in self.Axes.iteritems():
            ncdim = axis.ncdim
            if ncdim is not None:
                out[dim] = ncdim

        return out
    #--- End: def

#    @property
#    def rank(self):
#        '''The number of axes in the domain.
#
#Note that this may be greater the number of data array axes.
#
#.. seealso:: `ndim`
#
#:Examples:
#
#>>> print f
#air_temperature field summary
#-----------------------------
#Data           : air_temperature(time(12), latitude(64), longitude(128)) K
#Cell methods   : time: mean
#Axes           : time(12) = [ 450-11-16 00:00:00, ...,  451-10-16 12:00:00] noleap
#               : latitude(64) = [-87.8638000488, ..., 87.8638000488] degrees_north
#               : longitude(128) = [0.0, ..., 357.1875] degrees_east
#               : height(1) = [2.0] m
#>>> f.rank, f.ndim
#(4, 3)
#>>> g = f.unsqueeze()
#>>> f.rank, f.ndim
#(4, 4)
#
#        '''
#        return len(self.Axes)
#    #--- End: def

    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def flag_values(self):
        '''The flag_values CF property.

Provides a list of the flag values. Use in conjunction with
`flag_meanings`. See http://cfconventions.org/latest.html for details.

Stored as a 1-d numpy array but may be set as any array-like object.

:Examples:

>>> f.flag_values = ['a', 'b', 'c']
>>> f.flag_values
array(['a', 'b', 'c'], dtype='|S1')
>>> f.flag_values = numpy.arange(4)
>>> f.flag_values
array([1, 2, 3, 4])
>>> del f.flag_values

>>> f.setprop('flag_values', 1)
>>> f.getprop('flag_values')
array([1])
>>> f.delprop('flag_values')

        '''
        try:
            return self.Flags.flag_values
        except AttributeError:
            raise AttributeError(
                "%s doesn't have CF property 'flag_values'" %
                self.__class__.__name__)
    #--- End: def
    @flag_values.setter
    def flag_values(self, value):
        try:
            flags = self.Flags
        except AttributeError:
            self.Flags = Flags(flag_values=value)
        else:
            flags.flag_values = value
    #--- End: def
    @flag_values.deleter
    def flag_values(self):
        try:
            del self.Flags.flag_values
        except AttributeError:
            raise AttributeError(
                "Can't delete non-existent %s CF property 'flag_values'" %
                self.__class__.__name__)
        else:
            if not self.Flags:
                del self.Flags
    #--- End: def

    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def flag_masks(self):
        '''The flag_masks CF property.

Provides a list of bit fields expressing Boolean or enumerated
flags. See http://cfconventions.org/latest.html for details.

Stored as a 1-d numpy array but may be set as array-like object.

:Examples:

>>> f.flag_masks = numpy.array([1, 2, 4], dtype='int8')
>>> f.flag_masks
array([1, 2, 4], dtype=int8)
>>> f.flag_masks = (1, 2, 4, 8)
>>> f.flag_masks
array([1, 2, 4, 8], dtype=int8)
>>> del f.flag_masks

>>> f.setprop('flag_masks', 1)
>>> f.getprop('flag_masks')
array([1])
>>> f.delprop('flag_masks')

        '''
        try:
            return self.Flags.flag_masks
        except AttributeError:
            raise AttributeError(
                "%s doesn't have CF property 'flag_masks'" %
                self.__class__.__name__)
    #--- End: def
    @flag_masks.setter
    def flag_masks(self, value):
        try:
            flags = self.Flags
        except AttributeError:
            self.Flags = Flags(flag_masks=value)
        else:
            flags.flag_masks = value
    #--- End: def
    @flag_masks.deleter
    def flag_masks(self):
        try:
            del self.Flags.flag_masks
        except AttributeError:
            raise AttributeError(
                "Can't delete non-existent %s CF property 'flag_masks'" %
                self.__class__.__name__)
        else:
            if not self.Flags:
                del self.Flags
    #--- End: def

    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def flag_meanings(self):
        '''The flag_meanings CF property.

Use in conjunction with `flag_values` to provide descriptive words or
phrases for each flag value. If multi-word phrases are used to
describe the flag values, then the words within a phrase should be
connected with underscores. See http://cfconventions.org/latest.html
for details.

Stored as a 1-d numpy string array but may be set as a space delimited
string or any array-like object.

:Examples:

>>> f.flag_meanings = 'low medium      high'
>>> f.flag_meanings
array(['low', 'medium', 'high'],
      dtype='|S6')
>>> del flag_meanings

>>> f.flag_meanings = ['left', 'right']
>>> f.flag_meanings
array(['left', 'right'],
      dtype='|S5')

>>> f.flag_meanings = 'ok'
>>> f.flag_meanings
array(['ok'],
      dtype='|S2')

>>> f.setprop('flag_meanings', numpy.array(['a', 'b'])
>>> f.getprop('flag_meanings')
array(['a', 'b'],
      dtype='|S1')
>>> f.delprop('flag_meanings')

        '''
        try:
            return self.Flags.flag_meanings
        except AttributeError:
            raise AttributeError(
                "%s doesn't have CF property 'flag_meanings'" %
                self.__class__.__name__)
    #--- End: def
    @flag_meanings.setter
    def flag_meanings(self, value): 
        try:
            flags = self.Flags
        except AttributeError:
            self.Flags = Flags(flag_meanings=value)
        else:
            flags.flag_meanings = value
    #--- End: def
    @flag_meanings.deleter
    def flag_meanings(self):
        try:
            del self.Flags.flag_meanings
        except AttributeError:
            raise AttributeError(
                "Can't delete non-existent %s CF property 'flag_meanings'" %
                self.__class__.__name__)
        else:
            if not self.Flags:
                del self.Flags
    #--- End: def

    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def cell_methods(self):
        '''

The `CellMethods` object containing the CF cell methods of the data
array

:Examples:

>>> f.cell_methods
'time: maximum (interval: 1.0 month) area: mean (area-weighted)'

'''
        axis_map = self.axes_names()
        return ' '.join([cm.write(axis_map) for cm in self.Items.cell_methods])    

    @cell_methods.deleter
    def cell_methods(self):
        self.Items.cell_methods = []
 
    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property 
    def Conventions(self):
        '''The Conventions CF property.

The name of the conventions followed by the field. See
http://cfconventions.org/latest.html for details.

:Examples:

>>> f.Conventions = 'CF-1.6'
>>> f.Conventions
'CF-1.6'
>>> del f.Conventions

>>> f.setprop('Conventions', 'CF-1.6')
>>> f.getprop('Conventions')
'CF-1.6'
>>> f.delprop('Conventions')

        '''
        return self.getprop('Conventions')
    #--- End: def

    @Conventions.setter
    def Conventions(self, value): self.setprop('Conventions', value)
    @Conventions.deleter
    def Conventions(self):        self.delprop('Conventions')

    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def featureType(self):
        '''The featureType CF property.

The type of discrete sampling geometry, such as ``point`` or
``timeSeriesProfile``. See http://cfconventions.org/latest.html for
details.

.. versionadded:: 1.6

:Examples:

>>> f.featureType = 'trajectoryProfile'
>>> f.featureType
'trajectoryProfile'
>>> del f.featureType

>>> f.setprop('featureType', 'profile')
>>> f.getprop('featureType')
'profile'
>>> f.delprop('featureType')

        '''
        return self.getprop('featureType')
    #--- End: def

    @featureType.setter
    def featureType(self, value):
        self.setprop('featureType', value)
    @featureType.deleter
    def featureType(self):        
        self.delprop('featureType')

    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def institution(self):
        '''The institution CF property.

Specifies where the original data was produced. See
http://cfconventions.org/latest.html for details.

:Examples:

>>> f.institution = 'University of Reading'
>>> f.institution
'University of Reading'
>>> del f.institution

>>> f.setprop('institution', 'University of Reading')
>>> f.getprop('institution')
'University of Reading'
>>> f.delprop('institution')

        '''
        return self.getprop('institution')
    #--- End: def
    @institution.setter
    def institution(self, value): self.setprop('institution', value)
    @institution.deleter
    def institution(self):        self.delprop('institution')

    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def references(self):
        '''The references CF property.

Published or web-based references that describe the data or methods
used to produce it. See http://cfconventions.org/latest.html for
details.

:Examples:

>>> f.references = 'some references'
>>> f.references
'some references'
>>> del f.references

>>> f.setprop('references', 'some references')
>>> f.getprop('references')
'some references'
>>> f.delprop('references')

        '''
        return self.getprop('references')
    #--- End: def
    @references.setter
    def references(self, value): self.setprop('references', value)
    @references.deleter
    def references(self):        self.delprop('references')

    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def standard_error_multiplier(self):
        '''The standard_error_multiplier CF property.

If a data variable with a `standard_name` modifier of
``'standard_error'`` has this attribute, it indicates that the values
are the stated multiple of one standard error. See
http://cfconventions.org/latest.html for details.

:Examples:

>>> f.standard_error_multiplier = 2.0
>>> f.standard_error_multiplier
2.0
>>> del f.standard_error_multiplier

>>> f.setprop('standard_error_multiplier', 2.0)
>>> f.getprop('standard_error_multiplier')
2.0
>>> f.delprop('standard_error_multiplier')

        '''
        return self.getprop('standard_error_multiplier')
    #--- End: def

    @standard_error_multiplier.setter
    def standard_error_multiplier(self, value):
        self.setprop('standard_error_multiplier', value)
    @standard_error_multiplier.deleter
    def standard_error_multiplier(self):
        self.delprop('standard_error_multiplier')

    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def source(self):
        '''The source CF property.

The method of production of the original data. If it was
model-generated, `source` should name the model and its version, as
specifically as could be useful. If it is observational, `source`
should characterize it (for example, ``'surface observation'`` or
``'radiosonde'``). See http://cfconventions.org/latest.html for
details.

:Examples:

>>> f.source = 'radiosonde'
>>> f.source
'radiosonde'
>>> del f.source

>>> f.setprop('source', 'surface observation')
>>> f.getprop('source')
'surface observation'
>>> f.delprop('source')

        '''
        return self.getprop('source')
    #--- End: def

    @source.setter
    def source(self, value): self.setprop('source', value)
    @source.deleter
    def source(self):        self.delprop('source')

    # ----------------------------------------------------------------
    # CF property
    # ----------------------------------------------------------------
    @property
    def title(self):
        '''The title CF property.

A short description of the file contents from which this field was
read, or is to be written to. See http://cfconventions.org/latest.html
for details.

:Examples:

>>> f.title = 'model data'
>>> f.title
'model data'
>>> del f.title

>>> f.setprop('title', 'model data')
>>> f.getprop('title')
'model data'
>>> f.delprop('title')

        '''
        return self.getprop('title')
    #--- End: def

    @title.setter
    def title(self, value): self.setprop('title', value)
    @title.deleter
    def title(self):        self.delprop('title')

    def compress(self, method, axes=None, mask=None, mask_axes=None):
        '''Compress

.. versionadded:: 1.6

:Parameters:

    method: `str`

    axes:

    mask: data-like

        '''
        if method == 'gather':
            pass
            
        
    #--- End: def

    def constructs(self):
        '''Return all of the data model constructs of the field.

.. versionadded:: 1.6

.. seealso:: `dump`

:Examples 1:

>>> f.{+name}()

:Returns:

    out: `list`
        The objects correposnding CF data model constructs.

:Examples 2:

>>> print f
eastward_wind field summary
---------------------------
Data           : eastward_wind(air_pressure(15), latitude(72), longitude(96)) m s-1
Cell methods   : time: mean
Axes           : time(1) = [2057-06-01T00:00:00Z] 360_day
               : air_pressure(15) = [1000.0, ..., 10.0] hPa
               : latitude(72) = [88.75, ..., -88.75] degrees_north
               : longitude(96) = [1.875, ..., 358.125] degrees_east
>>> f.{+name}()
[<Field: eastward_wind(air_pressure(15), latitude(72), longitude(96)) m s-1>,
 <DomainAxis: 96>,
 <DomainAxis: 1>,
 <DomainAxis: 15>,
 <DomainAxis: 72>,
 <CellMethod: dim3: mean>,
 <DimensionCoordinate: longitude(96) degrees_east>,
 <DimensionCoordinate: time(1) 360_day>,
 <DimensionCoordinate: air_pressure(15) hPa>,
 <DimensionCoordinate: latitude(72) degrees_north>]

        '''
        out = [self]
        out.extend(self.Axes.values())
        out.extend(self.Items.cell_methods)
        out.extend(self.Items().values())
        return out
    #--- End: def

    def data_axes(self):
        '''Return the domain axes for the data array dimensions.

.. seealso:: `axes`, `axis`, `item_axes`

:Examples 1:

>>> d = f.{+name}()

:Returns:

    out: list or None
        The ordered axes of the data array. If there is no data array
        then `None` is returned.

:Examples 2:

>>> f.ndim
3
>>> f.{+name}()
['dim2', 'dim0', 'dim1']
>>> f.remove_data()
>>> print f.{+name}()
None

>>> f.ndim
0
>>> f.{+name}()
[]

        '''    
        if not self.hasdata:
            return None

        return self._data_axes[:]
    #--- End: def

    @property
    def isfield(self): 
        '''True, denoting that the variable is a field object

:Examples:

>>> f.isfield
True

        '''
        return True
    #--- End: def

    def _dump_axes(self, display=True, _level=0):
        '''Return a string containing a description of the domain axes of the
field.
    
:Parameters:
    
    display: `bool`, optional

        If False then return the description as a string. By default
        the description is printed.
    
    _level: `int`, optional

:Returns:
    
    out: `str`
        A string containing the description.
    
:Examples:

        '''
        indent1 = '    ' * _level
        indent2 = '    ' * (_level+1)

#        string = ['%sAxes:' % indent1]
        
        data_axes = self.data_axes()
        if data_axes is None:
            data_axes = ()

        axis_name = self.axis_name
        axis_size = self.axis_size

        w = sorted(["{0}Domain Axis: {1}({2})".format(indent1, axis_name(axis), size)
                    for axis, size in self.axes().iteritems()
                    if axis not in data_axes])

        x = ["{0}Domain Axis: {1}({2})".format(indent1, axis_name(axis), axis_size(axis))
             for axis in data_axes]

        string = '\n'.join(w+x)

        if display:
            print string
        else:
            return string
    #--- End: def

#    def _dump_cell_methods(self, display=True, _level=0):
#        '''Return a string containing a description of the cell methods of the
#field.
#    
#:Parameters:
#    
#    display: `bool`, optional
#
#        If False then return the description as a string. By default
#        the description is printed.
#    
#    _level: `int`, optional
#
#:Returns:
#    
#    out: `str`
#        A string containing the description.
#    
#:Examples:
#
#        '''
#        indent1 = '    ' * _level
#        indent2 = '    ' * (_level+1)
#
#        data_axes = self.data_axes()
#        if data_axes is None:
#            data_axes = ()
#
#        axis_name = self.axis_name
#        axis_size = self.axis_size
#
#        w = sorted(["{0}Domain Axis: {1}({2})".format(indent1, axis_name(axis), size)
#                    for axis, size in self.axes().iteritems()
#                    if axis not in data_axes])
#
#        x = ["{0}Domain Axis: {1}({2})".format(indent1, axis_name(axis), axis_size(axis))
#             for axis in data_axes]
#
#        string = '\n'.join(w+x)
#
#        if display:
#            print string
#        else:
#            return string
#    #--- End: def
#
#    def direction(self, axis):
#        '''
#
#Return True if an axis is increasing, otherwise return False.
#
#An axis is considered to be increasing if its dimension coordinate
#values are increasing in index space or if it has no dimension
#coordinates.
#
#
#:Parameters:
#
#    axis: `str`
#        A domain axis identifier, such as ``'dim0'``.
#
#:Returns:
#
#    out: `bool`
#        Whether or not the axis is increasing.
#        
#:Examples:
#
#>>> i.direction('dim0')
#True
#>>> i.direction('dim2')
#False
#        '''
#        axis = self.axis(axis)
#        
#
#        return self.Items.direction(axis)
#    #--- End: def
        
    def dump(self, display=True, _level=0, _title='Field', _q='-'):
        '''A full description of the field.

The field and its components are described without abbreviation with
the exception of data arrays, which are abbreviated to their first and
last values.

:Examples 1:
        
>>> f.{+name}()

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed.

          *Example:*
            ``f.dump()`` is equivalent to ``print
            f.dump(display=False)``.

:Returns:

    out: `None` or `str`
        If *display* is True then the description is printed and
        `None` is returned. Otherwise the description is returned as a
        string.

        '''
#        # List functionality
#        if self._list:
#            kwargs2 = self._parameters(locals())
#            if display:
#                for f in self:
#                    f.dump(**kwargs2)
#                return
#            else:
#                return [f.dump(**kwargs2) for f in self]
#        #--- End: if 

        indent = '    '      
        indent0 = indent * _level
        indent1 = indent0 + indent

        title = '{0}{1}: {2}'.format(indent0, _title, self.name(''))
        line  = '{0}{1}'.format(indent0, ''.ljust(len(title)-_level*4, '-'))

        # Title
        string = [line, title, line]

        # Simple properties
        if self._simple_properties():
            string.append(
                self._dump_simple_properties(_level=_level,
                                             omit=('Conventions',
                                                   '_FillValue',
                                                   'missing_value')))

        # Axes
        axes = self._dump_axes(display=False, _level=_level)
        if axes:
            string.extend(('', axes))
           
        # Data
        if self.hasdata:
            axis_name = self.axis_name
            axis_size = self.axis_size
            x = ['{0}({1})'.format(axis_name(axis), axis_size(axis))
                 for axis in self.data_axes()]
            string.extend(('', '{0}Data({1}) = {2}'.format(indent0,
                                                           ', '.join(x),
                                                           str(self.data))))
        # Cell methods        
        cell_methods = self.Items.cell_methods
        if cell_methods:
            string.append('') 
            for value in cell_methods:
                string.append(
                    value.dump(display=False, field=self, _level=_level))

        # Flags
        flags = getattr(self, 'Flags', None)
        if flags is not None:            
            string.extend(('', flags.dump(display=False, _level=_level)))

        # Field ancillaries
        for key, value in sorted(self.Items.field_ancs().iteritems()):
            string.append('') 
            string.append(
                value.dump(display=False, field=self, key=key, _level=_level))

        # Dimension coordinates
        for key, value in sorted(self.Items.dims().iteritems()):
            string.append('')
            string.append(value.dump(display=False, 
                                     field=self, key=key, _level=_level))
             
        # Auxiliary coordinates
        for key, value in sorted(self.Items.auxs().iteritems()):
            string.append('')
            string.append(value.dump(display=False, field=self, 
                                     key=key, _level=_level))
        # Domain ancillaries
        for key, value in sorted(self.Items.domain_ancs().iteritems()):
            print type(value), value.dump() #dch
            string.append('') 
            string.append(
                value.dump(display=False, field=self, key=key, _level=_level))
            
        # Coordinate references
        for key, value in sorted(self.Items.refs().iteritems()):
            string.append('')
            string.append(
                value.dump(display=False, field=self, key=key, _level=_level))

        # Cell measures
        for key, value in sorted(self.Items.msrs().iteritems()):
            string.append('')
            string.append(
                value.dump(display=False, field=self, key=key, _level=_level))

        string.append('')
        
        string = '\n'.join(string)
       
        if display:
            print string
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None,
               ignore_data_type=False, ignore_fill_value=False,
               traceback=False, ignore=('Conventions',)):
        # Note: map(None, f, g) only works at python 2.x
        '''True if two {+variable}s are equal, False otherwise.

Two fields are equal if ...

Note that a {+variable} may be equal to a single element field list,
for example ``f.equals(f[0:1])`` and ``f[0:1].equals(f)`` are always
True.

.. versionadded:: 1.6

:Examples 1:

>>> b = f.{+name}(g)

:Parameters:

    other: `object`
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
        The names of CF properties to omit from the comparison. By
        default, the CF Conventions property is omitted.

:Returns: 
  
    out: `bool`
        Whether or not the two {+variable}s are equal.

:Examples 2:

>>> f.Conventions
'CF-1.0'
>>> g = f.copy()
>>> g.Conventions = 'CF-1.6'
>>> f.equals(g)
True

In the following example, two fields differ only by the long name of
their time coordinates. The traceback shows that they differ in their
domains, that they differ in their time coordinates and that the long
name could not be matched.

>>> g = f.copy()
>>> g.coord('time').long_name += ' different'
>>> f.equals(g, traceback=True)
Domain: Different coordinate: <CF Coordinate: time(12)>
Field: Different domain properties: <CF Domain: (128, 1, 12, 64)>, <CF Domain: (128, 1, 12, 64)>
False

        '''

        kwargs2 = self._parameters(locals())
        return super(Field, self).equals(**kwargs2)
    #---End: def

    def transpose(self, axes=None, copy=True, items=True, **kwargs):
        '''Permute the axes of the data array.

By default the order of the axes is reversed, but any ordering may be
specified by selecting the axes of the output in the required order.

The axes are selected with the *axes* parameter.

.. seealso:: `expand_dims`, `squeeze`, `transpose`, `unsqueeze`

:Examples 1:

>>> g = f.{+name}()
>>> g = f.{+name}(['T', 'X', 'Y'])

.. seealso:: `axes`, `expand_dims`, `flip`, `squeeze`, `unsqueeze`

:Parameters:

    {+axes, kwargs}

    items: `bool`
        If False then metadata items (corodinates, cell measures,
        etc.) are not tranposed. By default, metadata items are
        tranposed so that their axes are in the same relative order as
        in the tranposed data array of the field.

    {+copy}

:Returns:

    out: `{+Variable}`
        The transposed {+variable}.

:Examples 2:

>>> f.items()
{'dim0': <CF DimensionCoordinate: time(12) noleap>,
 'dim1': <CF DimensionCoordinate: latitude(64) degrees_north>,
 'dim2': <CF DimensionCoordinate: longitude(128) degrees_east>,
 'dim3': <CF DimensionCoordinate: height(1) m>}
>>> f.data_axes()
['dim0', 'dim1', 'dim2']
>>> f.transpose()
>>> f.transpose(['Y', 'T', 'X'])
>>> f.transpose([1, 0, 2])
>>> f.transpose((1, 'time', 'dim2'))

        ''' 
        data_axes = self.data_axes()

        if _debug:
            print '{}.tranpose:'.format(self.__class__.__name__)
            print '    axes, kwargs:', axes, kwargs
            print '    shape =', self.shape

        if axes is None and not kwargs:
            axes2 = data_axes[::-1]
            iaxes = range(self.ndim-1, -1, -1)
        else:
            kwargs['ordered'] = True
            axes2 = list(self.axes(axes, **kwargs))
            if set(axes2) != set(data_axes):
                raise ValueError(
"Can't transpose {}: Bad axis specification: {!r}".format(
    self.__class__.__name__, axes))

            iaxes = [data_axes.index(axis) for axis in axes2]
        #---- End: if

        # Transpose the field's data array
        f = super(Field, self).transpose(iaxes, copy=copy)

        # Reorder the list of data axes
        f._data_axes = axes2
        
        if _debug:
            print '    iaxes =', iaxes
            print '    axes2 =', f.data_axes()
            print '    shape =', f.shape

        if items:
            ndim = f.ndim
            for key, item in f.items(role=('d', 'a', 'm', 'f', 'c')).iteritems():
                item_ndim = item.ndim
                if item.ndim < 2:
                    # No need to transpose 1-d items
                    continue
                item_axes = f.item_axes(key)

                faxes = [axis for axis in axes2 if axis in item_axes]        
                for i, axis in enumerate(item_axes):
                    if axis not in faxes:
                        faxes.insert(i, axis)

                iaxes = [item_axes.index(axis) for axis in faxes]                
                if _debug:
                    print '    item, item_axes, iaxes:', repr(item), item_axes, iaxes

                f.transpose_item(key, iaxes)
                if _debug:
                    print '                      item:', repr(item)
        #--- End: if
        
        return f
    #--- End: def

    def transpose_item(self, description=None, iaxes=None, **kwargs):
        '''Permute the axes of a field item data array.

By default the order of the axes is reversed, but any ordering may be
specified by selecting the axes of the output in the required order.

The axes are selected with the *axes* parameter.

.. seealso:: `expand_dims`, `squeeze`, `transpose`, `unsqueeze`

:Examples 1:

>>> g = f.{+name}()

:Parameters:

    {+axes, kwargs}

:Returns:

    out: `{+Variable}`
        The transposed {+variable}.

:Examples 2:

        '''     
        key, item = self.Items.key_item(description, **kwargs)
        item_axes = self.item_axes(key)            
        
        if iaxes is None and not kwargs:
            axes2 = item_axes[::-1]
            iaxes = range(item.ndim-1, -1, -1)
        else:
            if len(iaxes) != item.ndim:
                raise ValueError(
"Can't transpose {}: Bad axis specification for {}-d array: {!r}".format(
    item.__class__.__name__, item.ndim, iaxes))
            
            axes2 = [item_axes[i] for i in iaxes]
        #---- End: if

        # Transpose the item's data array
        item.transpose(iaxes, copy=False)

        # Reorder the field's list of axes
        self.Items.axes(key=key, axes=axes2)
        
        return item
    #--- End: def

    def unsqueeze(self, axes=None, copy=True, **kwargs):
        '''Insert size 1 axes into the data array.

By default all size 1 domain axes which are not spanned by the field's
data array are inserted, but existing size 1 axes may be selected for
insertion.

The axes are selected with the *axes* parameter.

The axes are inserted into the slowest varying data array positions.

.. seealso:: `expand_dims`, `squeeze`, `transpose`

:Examples 1:

>>> g = f.{+name}()

:Parameters:

    {+axes, kwargs}

    {+copy}

:Returns:

    out: `{+Variable}`
        The unsqueezed {+variable}.

:Examples 2:

>>> g = f.{+name}('T', size=1)

>>> print f
Data            : air_temperature(time, latitude, longitude)
Cell methods    : time: mean
Dimensions      : time(1) = [15] days since 1860-1-1
                : latitude(73) = [-90, ..., 90] degrees_north
                : longitude(96) = [0, ..., 356.25] degrees_east
                : height(1) = [2] m
Auxiliary coords:
>>> f.unsqueeze()
>>> print f
Data            : air_temperature(height, time, latitude, longitude)
Cell methods    : time: mean
Dimensions      : time(1) = [15] days since 1860-1-1
                : latitude(73) = [-90, ..., 90] degrees_north
                : longitude(96) = [0, ..., 356.25] degrees_east
                : height(1) = [2] m
Auxiliary coords:

        '''     
        data_axes = self.data_axes()
        axes = set(self.axes(axes, size=1, **kwargs)).difference(data_axes)

        if copy:
            f = self.copy()
        else:
            f = self

        for axis in axes:
            f.expand_dims(0, axis, copy=False)

        return f
    #--- End: def

    def expand_dims(self, position=0, axes=None, copy=True, **kwargs):
        '''Insert a size 1 axis into the data array.

By default default a new size 1 axis is inserted which doesn't yet
exist, but a unique existing size 1 axis which is not already spanned
by the data array may be selected.

.. seealso:: `axes`, `squeeze`, `transpose`

:Examples 1:

>>> g = f.{+name}()
>>> g = f.{+name}(2, axes='T')

:Parameters:

    position: `int`, optional
        Specify the position that the new axis will have in the data
        array. By default the new axis has position 0, the slowest
        varying position.

    {+axes, kwargs}

    {+copy}

:Returns:

    out: `{+Variable}`
        The expanded field.

:Examples 2:

        '''
        if axes is None and not kwargs:
            axis = None
        else:
            axis = self.axis(axes, key=True, **kwargs)
            if axis is None:
                raise ValueError("Can't identify a unique axis to insert")
            elif self.axis_size(axis) != 1:
                raise ValueError(
"Can't insert an axis of size {}: {!r}".format(self.axis_size(axis), axis))
            elif axis in self.data_axes():
                raise ValueError(
                    "Can't insert a duplicate axis: {!r}".format(axis))
        #--- End: if
       
        # Expand the dims in the field's data array
        f = super(Field, self).expand_dims(position, copy=copy)

        axis = f.insert_axis(self._DomainAxis(1), key=axis, replace=False)

        f._data_axes.insert(position, axis)

        return f
    #--- End: def

    def squeeze(self, axes=None, copy=True, **kwargs):
        '''Remove size-1 axes from the data array.

By default all size 1 axes are removed, but particular size 1 axes may
be selected for removal.

The axes are selected with the *axes* parameter.

Squeezed axes are not removed from the coordinate and cell measure
objects, nor are they removed from the domain. To completely remove
axes, use the `remove_axes` method.

.. seealso:: `expand_dims`, `remove_axes`, `transpose`, `unsqueeze`


:Examples 1:

>>> g = f.{+name}()
>>> g = f.{+name}('T')

:Parameters:

    {+axes, kwargs}

    {+copy}

:Returns:

    out: `{+Variable}`
        The squeezed field.

:Examples 2:

        '''     
        data_axes = self.data_axes()

        if axes is None and not kwargs:
            all_axes = self.axes()
            axes = [axis for axis in data_axes if all_axes[axis] == 1]
        else:
            axes = set(self.axes(axes, **kwargs)).intersection(data_axes)

        iaxes = [data_axes.index(axis) for axis in axes]      

        # Squeeze the field's data array
        f = super(Field, self).squeeze(iaxes, copy=copy)

        f._data_axes = [axis for axis in data_axes if axis not in axes]

        return f
    #--- End: def

    def _insert_item_parse_axes(self, item, role, axes=None, allow_scalar=True):
        '''
        '''
        all_axes = self.axes()

        if axes is None:
            # --------------------------------------------------------
            # The axes have not been set => infer the axes.
            # --------------------------------------------------------
            shape = item.shape
            if allow_scalar and not shape:
                axes = []
            else:
                if not allow_scalar and not shape:
                    shape = (1,)

                if not shape or len(shape) != len(set(shape)):
                    raise ValueError(
"Can't insert {0}: Ambiguous shape: {1}. Consider setting the 'axes' parameter.".format(
    item.__class__.__name__, shape))

                axes = []
                axes_sizes = all_axes.values()
                for n in shape:
                    if axes_sizes.count(n) == 1:
                        axes.append(self.axis(size=n, key=True))
                    else:
                        raise ValueError(
"Can't insert {} {}: Ambiguous shape: {}. Consider setting the 'axes' parameter.".format(
    item.name(default=''), item.__class__.__name__, shape))
            #--- End: if

        else:
            # --------------------------------------------------------
            # Axes have been provided
            # --------------------------------------------------------
            ndim = item.ndim
            if not ndim and not allow_scalar:
                ndim = 1

            axes = list(self.axes(axes, ordered=True))
            if len(set(axes)) != ndim:
                raise ValueError(
"Can't insert {} {}: Mismatched axis size (got {}, expected {})".format(
    item.__class__.__name__, item.name(default=''), len(set(axes)), ndim))

            axes2 = []                
            for axis, size in izip_longest(axes, item.shape, fillvalue=1):
                if size != self.axis_size(axis):
                    raise ValueError(
"Can't insert {} {}: Mismatched axis size (got {}, expected {})".format(
    item.__class__.__name__, item.name(default=''), size, self.axis_size(axis)))

                axes2.append(axis)
            #--- End: for
            axes = axes2

            if ndim != len(set(axes)):
                raise ValueError(
"Can't insert {} {}: Mismatched number of axes ({} != {})".format(
    item.name(default=''), item.__class__.__name__, len(set(axes)), ndim))
        #--- End: if
    
        return axes
    #--- End: def

    def insert_aux(self, item, key=None, axes=None, copy=True, replace=True):
        '''Insert an auxiliary coordinate object into the {+variable}.

.. seealso:: `insert_axis`, `insert_measure`, `insert_data`,
             `insert_dim`, `insert_ref`

:Parameters:

    item: `AuxiliaryCoordinate`
        The new auxiliary coordinate object. If it is not already a
        auxiliary coordinate object then it will be converted to one.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    axes: sequence of `str`, optional
        The ordered list of axes for the *item*. Each axis is given by
        its identifier. By default the axes are assumed to be
        ``'dim0'`` up to ``'dimM-1'``, where ``M-1`` is the number of
        axes spanned by the *item*.

    {+copy_item_in}
      
    replace: `bool`, optional
        If False then do not replace an existing auxiliary coordinate
        object of domain which has the same identifier. By default an
        existing auxiliary coordinate object with the same identifier
        is replaced with *item*.
    
:Returns:

    out: `str`
        The identifier for the inserted *item*.

:Examples:

>>>

        '''

#        item = item._asauxiliary(AuxiliaryCoordinate, copy=copy)            
        if copy:
            item = item.copy()
            
        if key is None:
            key = self.new_identifier('aux')

        if key in self.axes() and not replace:
            raise ValueError(
"Can't insert auxiliary coordinate object: Identifier {0!r} already exists".format(key))

        axes = self._insert_item_parse_axes(item, 'auxiliary coordinate', axes,
                                            allow_scalar=False)

        # Turn a scalar auxiliary coordinate into 1-d
        if item.isscalar:
            item = item.expand_dims(0, copy=False)

        self.Items.insert_aux(item, key=key, axes=axes, copy=False)

        # Update coordindate references
        refs = self.items(role='r')
        if refs:
            for ref in refs.itervalues():
                self._conform_ref(ref, copy=False)

        # Update cell methods
        if self.Items.cell_methods:
            self.Items.cell_methods = self._conform_cell_methods()

        return key
    #--- End: def

    def insert_data(self, data, axes=None, copy=True, replace=True,
                    force=False):
        '''Insert a data array into the {+variable}.

:Examples 1:

>>> f.insert_data(d)

:Parameters:

    data: `Data`
        The data array to be inserted.

    axes: sequence of `str`, optional
        A list of axis identifiers (``'dimN'``), stating the axes, in
        order, of the data array.

        The ``N`` part of each identifier should be replaced by an
        integer greater then or equal to zero such that either a) each
        axis identifier is the same as one in the field's domain, or
        b) if the domain has no axes, arbitrary integers greater then
        or equal to zero may be used, the only restriction being that
        the resulting identifiers are unique.

        If an axis of the data array already exists in the domain then
        the it must have the same size as the domain axis. If it does
        not exist in the domain then a new axis will be created.

        By default the axes will either be those defined for the data
        array by the domain or, if these do not exist, the domain axis
        identifiers whose sizes unambiguously match the data array.

    copy: `bool`, optional
        If False then the new data array is not deep copied prior to
        insertion. By default the new data array is deep copied.

    replace: `bool`, optional
        If False then raise an exception if there is an existing data
        array. By default an existing data array is replaced with
        *data*.
   
    force: `bool`, optional
        If True then insert the new data without checking or changing
        any other metadata. Warning: if the new data array has a
        different shape to an existing data arary this may break the
        field.
   
:Returns:

    `None`

:Examples 2:

>>> f.axes()
{'dim0': 1, 'dim1': 3}
>>> f.insert_data(Data([[0, 1, 2]]))

>>> f.axes()
{'dim0': 1, 'dim1': 3}
>>> f.insert_data(Data([[0, 1, 2]]), axes=['dim0', 'dim1'])

>>> f.axes()
{}
>>> f.insert_data(Data([[0, 1], [2, 3, 4]]))
>>> f.axes()
{'dim0': 2, 'dim1': 3}

>>> f.insert_data(Data(4))

>>> f.insert_data(Data(4), axes=[])

>>> f.axes()
{'dim0': 3, 'dim1': 2}
>>> data = Data([[0, 1], [2, 3, 4]])
>>> f.insert_data(data, axes=['dim1', 'dim0'], copy=False)

>>> f.insert_data(Data([0, 1, 2]))
>>> f.insert_data(Data([3, 4, 5]), replace=False)
ValueError: Can't initialize data: Data already exists
>>> f.insert_data(Data([3, 4, 5]))

        '''
        if force:
            if data.shape != self.shape:
                print "WARNING: Forcing insertion of new data with a different shape to existing data"

            self._Data = data
            return
        #--- End: if

        if data is None:
            return

        if self.hasdata and not replace:
            raise ValueError(
"Can't insert data: Data already exists and replace={}".format(replace))

        if data.isscalar:
            # --------------------------------------------------------
            # The data array is scalar
            # --------------------------------------------------------
            if axes: 
                raise ValueError(
"Can't insert data: Wrong number of axes for scalar data array: axes={}".format(axes))

            axes = []

        elif axes is not None:
            # --------------------------------------------------------
            # Axes have been set
            # --------------------------------------------------------
            if len(axes) != len(set(axes)):
                raise ValueError(
"Can't insert data: Ambiguous axes: {}".format(axes))

            if len(axes) != data.ndim:
                raise ValueError(
"Can't insert data: Wrong number of axes for data array: {!r}".format(axes))

            domain_axes = self.axes()

            if not domain_axes:
                # The domain has no axes: Use those given.
                for axis in axes:
                    if not re_match('dim\d+', axis):
                        raise ValueError("asdasdasdasdadass7y87g y boih8 ")
                    
                for key, size in zip(axes, data.shape):
                    self.insert_axis(self._DomainAxis(size), key=key)
            else: 
                # The domain has axes: Check the input axes.
                axes = list(self.axes(axes, ordered=True))

                if len(axes) != data.ndim:
                    raise ValueError(
                        "Can't insert data: Ambiguous axes: {}".format(axes))
                
                for axis, size in izip(axes, data.shape):
                    if size != self.axis_size(axis):
                        raise ValueError(
"Can't insert data: Incompatible domain size for axis {!r} ({})".format(axis, size))
                #--- End: for
            #--- End: if
            
            axes = list(axes)
            
        elif self.data_axes() is None:
            # --------------------------------------------------------
            # The data is not scalar and axes have not been set and
            # the domain does not have data axes defined
            #
            # => infer the axes
            # --------------------------------------------------------
            if not self.axes():
                # The domain has no axes, so make some up for the data
                # array
                axes = []
                for size in data.shape:
                    axes.append(self.insert_axis(self._DomainAxis(size)))
            else:
                # The domain already has some axes
                data_shape = data.shape
                if len(data_shape) != len(set(data_shape)):
                    raise ValueError(
"Can't insert data: Ambiguous data shape: {}. Consider setting the axes parameter.".format(
    data_shape))

                axes = []
                axis_sizes = self.axes().values()
                for n in data_shape:
                    if axis_sizes.count(n) == 1:
                        axes.append(self.axis(size=n, key=True))
                    else:
                        raise ValueError(
"Can't insert data: Ambiguous data shape: {}. Consider setting the axes parameter.".format(
    data_shape))
                 #--- End: for
        else:
            # --------------------------------------------------------
            # The data is not scalar and axes have not been set, but
            # there are data axes defined on the field.
            # --------------------------------------------------------
            axes = self.data_axes()
            if len(axes) != data.ndim:
                raise ValueError(
                    "Wrong number of axes for data array: {!r}".format(axes))
            
            for axis, size in izip(axes, data.shape):
                try:
                    self.insert_axis(self._DomainAxis(size), axis, replace=False)
                except ValueError:
                    raise ValueError(
"Can't insert data: Incompatible size for axis {!r}: {}".format(axis, size))
            #--- End: for
        #--- End: if

        self._data_axes = axes

        if copy:
            data = data.copy()

        self._Data = data
    #--- End: def

    def HDF_chunks(self, *chunksizes):
        '''{+HDF_chunks}

**Chunking the metadata**

The coordinate, cell measure, and ancillary contructs are not
automatically chunked, but they may be chunked manually. For example,
a two dimensional latitude coordinate could chunked as follows (see
`AuxiliaryCoordinate.HDF_chunks` for details):

>>> f.coord('latitude').HDF_chunks({0: 10, 1: 15})

In version 2.0, the metadata will be automatically chunked.

**Chunking via `write`**

Chunking may also be defined via a parameter to the `write` function,
in which case any axis chunk sizes set on the field take precedence.

.. versionadded:: 1.6

.. seealso:: `write`

:Examples 1:
        
To define chunks which are the full size for each axis except for the
time axis which is to have a chunk size of 12:

>>> old_chunks = f.{+name}({'T': 12})

:Parameters:


    chunksizes: `dict` or None, optional
        Specify the chunk sizes for axes of the field. Axes are given
        by dictionary keys, with a chunk size for those axes as the
        dictionary values. A dictionary key of ``axes`` defines the
        axes that would be returned by the field's `~Field.axes`
        method, i.e. by ``f.axes(axes)``. See `Field.axes` for
        details. In the special case of *chunksizes* being `None`,
        then chunking is set to the netCDF default.

          *Example:*
            To set the chunk size for time axes to 365: ``{'T':
            365}``.

          *Example:*
            To set the chunk size for the first and third data array
            axes to 100: ``{0: 100, 2: 100}``, or equivalently ``{(0,
            2): 100}``.

          *Example:*
            To set the chunk size for the longitude axis to 100 and
            for the air temperature axis to 5: ``{'X': 100,
            'air_temperature': 5}``.

          *Example:*
            To set the chunk size for all axes to 10: ``{None:
            10}``. This works because ``f.axes(None)`` returns all
            field axes.

          *Example:*
            To set the chunking to the netCDF default: ``None``.

:Returns:

    out: `dict`
        The chunk sizes prior to the new setting, or the current
        current sizes if no new values are specified.

:Examples 2:

>>> f
<CF Field: air_temperature(time(3650), latitude(64), longitude(128)) K>
>>> f.HDF_chunks()
{0: None, 1: None, 2: None}
>>> f.HDF_chunks({'T': 365, 2: 1000})
{0: None, 1: None, 2: None}
>>> f.HDF_chunks({'X': None})
{0: 365, 1: None, 2: 1000}
>>> f.HDF_chunks(None)
{0: 365, 1: None, 2: None}
>>> f.HDF_chunks()
{0: None, 1: None, 2: None}

        '''
        if not chunksizes:
            return super(Field, self).HDF_chunks()

        if len(chunksizes) > 1:
            raise ValueError("asfdds ")
            
        chunks = chunksizes[0]

        if chunks is None:
            return super(Field, self).HDF_chunks(None)

        _HDF_chunks = {}

        data_axes = self.data_axes()
        for axes, size in chunks.iteritems():
            for axis in self.axes(axes):
                try:
                    _HDF_chunks[data_axes.index(axis)] = size
                except ValueError:
                    pass                
        #--- End: for

        return super(Field, self).HDF_chunks(_HDF_chunks)
    #--- End: def

    def field(self, description=None, role=None, axes=None, axes_all=None,
              axes_subset=None, axes_superset=None, exact=False,
              inverse=False, match_and=True, ndim=None, bounds=False):
        '''Create an independent field from a domain item.

An item is either a dimension coordinate, auxiliary coordinate, cell
measure, domain ancillary or field anciallary object of the field.

{+item_selection}

#If a unique item can not be found then no field is created and `None`
#is returned.

By default, bounds of the selected item are not included in the
returned field (see the *bounds* parameter).

.. versionadded:: 1.6

.. seealso:: `read`, `item`

:Examples 1:

Create a field whose data are the latitude coordinates

>>> g = f.field('latitude')

:Parameters:

    {+description}

    {+role}

    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+match_and}

    {+exact}
       
    {+inverse}

    bounds: `bool`, optional
        If True then create a field from the item's bounds. By
        default, bounds of the selected item are ignored.

:Returns:

    out: `{+Variable}`
        The field based on the selected domain item.
        
:Examples 2:

::

   >>> print f 
   eastward_wind field summary
   ---------------------------
   Data           : eastward_wind(time(3), grid_latitude(110), grid_longitude(106)) m s-1
   Cell methods   : time: mean
   Axes           : time(3) = [1979-05-01 12:00:00, ..., 1979-05-03 12:00:00] gregorian
                  : grid_longitude(106) = [-20.54, ..., 25.66] degrees
                  : grid_latitude(110) = [23.32, ..., -24.64] degrees
   Aux coords     : latitude(grid_latitude(110), grid_longitude(106)) = [[67.12, ..., 22.89]] degrees_north
                  : longitude(grid_latitude(110), grid_longitude(106)) = [[-45.98, ..., 35.29]] degrees_east
   Coord refs     : <CF CoordinateReference: rotated_latitude_longitude>
   
   >>> print f.field('X')
   grid_longitude field summary
   ----------------------------
   Data           : grid_longitude(grid_longitude(106)) degrees
   Axes           : grid_longitude(106) = [-20.54, ..., 25.66] degrees
   Coord refs     : <CF CoordinateReference: rotated_latitude_longitude>
   
   >>> print f.field('X', bounds=True)
   grid_longitude field summary
   ----------------------------
   Data           : grid_longitude(grid_longitude(106), dim1(2)) degrees
   Axes           : dim1(2)
                  : grid_longitude(106) = [-20.54, ..., 25.66] degrees
   Coord refs     : <CF CoordinateReference: rotated_latitude_longitude>
   
   >>> print f.field('lat')
   latitude field summary
   ----------------------
   Data           : latitude(grid_latitude(110), grid_longitude(106)) degrees_north
   Axes           : grid_longitude(106) = [-20.54, ..., 25.66] degrees
                  : grid_latitude(110) = [23.32, ..., -24.64] degrees
   Aux coords     : latitude(grid_latitude(110), grid_longitude(106)) = [[67.12, ..., 22.89]] degrees_north
                  : longitude(grid_latitude(110), grid_longitude(106)) = [[-45.98, ..., 35.29]] degrees_east
   Coord refs     : <CF CoordinateReference: rotated_latitude_longitude>

To multiply the field by the cosine of its latitudes:

>>> latitude = f.field({'units': 'radian', None: 'Y'})
>>> latitude
<CF Field: grid_latitude(grid_latitude(110)) degrees>
>>> g = f * latitude.cos()

        '''
        kwargs2 = self._parameters(locals())
        del kwargs2['bounds']
 
        (key, item) = self.Items.key_item(**kwargs2)
        if key is None:
            raise ValueError("No unique item could be found from {}".format(
                self._no_None_dict(kwargs2)))

        item_axes = self.item_axes(key)
        data_axes = item_axes
        
        f = type(self)(properties=item.properties())
        
        if bounds and item.hasbounds:
            if not item.bounds.hasdata:
                raise ValueError("No bounds data")

            data_axes.append(self.new_identifier('axis'))
            data = item.bounds.data
        else:
            data = item.data
        
        f.insert_data(data, axes=data_axes)
        
        for key, item in self.items(axes_superset=item_axes).iteritems():
            role = self.Items.role(key)
            if role in ('d', 'a', 'm'):
                f.insert_item(role, item, key=key, axes=self.item_axes(key))

        # Add coordinate references which span a subset of the item's
        # axes
        for rkey, ref in self.items(role='r').iteritems():
            if not set(f.axes(ref.coordinates)).issuperset(item_axes):
                continue

            ref = ref.copy()

            coordinates = []
            new_field_coordinates = f.items(role='da')
            for x in ref.coordinates:
                if x in new_field_coordinates:
                    coordinates.append(x)
            ref._coordinates = set(coordinates)

            ancillaries = []
            for term in ref.ancillaries:
                key = ref[term]
                domain_anc = self.item(key, role='c', axes_superset=item_axes)
                print repr(domain_anc),item_axes, key
                if domain_anc is not None:
                    ancillaries.append(term)
                    f.insert_item('c', domain_anc, key=key, axes=self.item_axes(key))
                else:
                    ref[term] = None
                    
                ref._ancillaries = set(ancillaries)
            #--- End: for
                
            f.insert_ref(ref, key=rkey, copy=False)
        #--- End: for

        return f
    #--- End: def

    def remove_data(self):
        '''Docstring copied from Variable.remove_data

        '''
        self._data_axes = None
        return super(Field, self).remove_data()
    #--- End: def
    remove_data.__doc__ = Variable.remove_data.__doc__
    
    def unlimited(self, *xxx):
        '''Todo ...


.. versionadded:: 1.6
        
.. seealso:: `write`

:Examples 1:

Set the time axis to be unlimited when written to a netCDF file:

>>> f.{+name}({'T': True})

:Parameters:

    xxx: `dict` or `None`, optional
        Specify the chunk sizes for axes of the field. Axes are given
        by dictionary keys, with a chunk size for those axes as the
        dictionary values. A dictionary key of ``axes`` defines the
        axes that would be returned by the field's axes method,
        i.e. by ``f.axes(axes)``. See `Field.axes` for details. In the
        special case of *xxx* being `None`, then chunking is set to
        the netCDF default.

          *Example:*
            To set time axes to be unlimited: ``{'T': True}``.

        Example:

            To set the chunk size for the first and third data array
        axes to 100: {0: 100, 2: 100}, or equivalently {(0, 2): 100}.
        Example:

            To set the chunk size for the longitude axis to 100 and
        for the air temperature axis to 5: {'X': 100,
        'air_temperature': 5}.  Example:

            To set the chunk size for all axes to 10: {None: 10}. This
        works because f.axes(None) returns all field axes.  Example:
        To set the chunking to the netCDF default: None.

:Returns:

    out: `dict`

:Examples 2:

        '''
        if len(xxx) > 1:
            raise ValueError("asfdds asdasdas4444444")

        org = {}
        for axis in self.axes():
            org[axis] = None            
            
        if self._unlimited:
            org.update(self._unlimited)

        if not xxx:
            return org
    
        xxx = xxx[0]

        if xxx is None:
            # Clear all settings
            self._unlimited = None
            return org

        _unlimited = {}
        for axes, value in xxx.iteritems():
            for axis in self.axes(axes):
                _unlimited[axis] = value

        if not _unlimited:        
            _unlimited = None

        self_unlimited = self._unlimited
        if self_unlimited is None:
            self._unlimited = _unlimited
        else:
            self._unlimited = self_unlimited.copy()
            self._unlimited.update(_unlimited)

        return org
    #--- End: def

    def match(self, description=None, items=None, rank=None, ndim=None,
              exact=False, match_and=True, inverse=False):
        '''Test whether or not the field satisfies the given conditions.

Different types of conditions may be set with the parameters:
         
=============  =======================================================
Parameter      What gets tested
=============  =======================================================
*description*  Field properties and attributes
             
*items*        Field items
               
*rank*         The number of domain axes
               
*ndim*         The number of field data array axes
=============  =======================================================

By default, when multiple criteria are given the field matches if it
satisfies the conditions given by each one.

.. seealso:: `items`, `select`

**Quick start examples**

There is great flexibility in the types of test which can be
specified, and as a result the documentation is very detailed in
places. These preliminary, simple examples show that the usage need
not always be complicated and may help with understanding the keyword
descriptions.

1. Test if a field contains air temperature data, as given determined
   by its `identity` method:

   >>> f.match('air_temperature')

2. Test if a field contains air temperature data, as given determined
   by its `identity` method, or has a long name which contains the
   string "temp":

   >>> f.match(['air_temperature', {'long_name': cfeq('.*temp.*', regex=true)}])

3. Test if a field has at least one longitude grid cell point on the
   Greenwich meridian:

   >>> f.match(items={'longitude': 0})

4. Test if a field has latitude grid cells which all have a resolution
   of less than 1 degree:

   >>> f.match(items={'latitude': cf.cellsize(cf.lt(1, 'degree'))})

5. Test if a field has exactly 4 domain axes:

   >>> f.match(rank=4)

6. Examples 1 to 4 may be combined to test if a field has exactly 4
   domain axes, contains air temperature data, has at least one
   longitude grid cell point on the Greenwich meridian and all
   latitude grid cells have a resolution of less than 1 degree:

   >>> f.match('air_temperature',
   ...         items={'longitude': 0,
   ...                'latitude': cf.cellsize(cf.lt(1, 'degree'))},
   ...         rank=4)

7. Test if a field contains Gregorian calendar monthly mean data array
   values:

   >>> f.match({'cell_methods': CellMethods('time: mean')},
   ...         items={'time': cf.cellsize(cf.wi(28, 31, 'days'))})

Further examples are given within and after the description of the
arguments.


:Parameters:

    description: *optional*
        Set conditions on the field's CF property and attribute
        values. *description* may be one, or a sequence of:

          * `None` or an empty dictionary. Always matches the
            field. This is the default.

     ..

          * A string which identifies string-valued metadata of the
            field and a value to compare it against. The value may
            take one of the following forms:

              ==============  ======================================
              *description*   Interpretation
              ==============  ======================================
              Contains ``:``  Selects on the CF property specified
                              before the first ``:``
                                
              Contains ``%``  Selects on the attribute specified
                              before the first ``%``              
              
              Anything else   Selects on identity as returned by the
                              `identity` method
              ==============  ======================================

            By default the part of the string to be compared with the
            item is treated as a regular expression understood by the
            :py:obj:`re` module and the field matches if its
            appropriate value matches the regular expression using the
            :py:obj:`re.match` method (i.e. if zero or more characters
            at the beginning of field's value match the regular
            expression pattern). See the *exact* parameter for
            details.
            
              *Example:*
                To match a field with `identity` beginning with "lat":
                ``match='lat'``.

              *Example:*
                To match a field with long name beginning with "air":
                ``match='long_name:air'``.

              *Example:*
                To match a field with netCDF variable name of exactly
                "tas": ``match='ncvar%tas$'``.

              *Example:*
                To match a field with `identity` which ends with the
                letter "z": ``match='.*z$'``.

              *Example:*
                To match a field with long name which starts with the
                string ".*a": ``match='long_name%\.\*a'``. 

        ..

          * A `cf.Query` object to be compared with field's identity,
            as returned by its `identity` method.

              *Example:*
                To match a field with `identity` of exactly
                "air_temperature" you could set
                ``match=cf.eq('air_temperature')`` (see `cf.eq`).

              *Example:*
                To match a field with `identity` ending with
                "temperature" you could set
                ``match=cf.eq('.*temperature$', exact=False)`` (see
                `cf.eq`).

     ..

          * A dictionary which identifies properties of the field with
            corresponding tests on their values. The field matches if
            **all** of the tests in the dictionary are passed.

            In general, each dictionary key is a CF property name with
            a corresponding value to be compared against the field's
            CF property value. 

            If the dictionary value is a string then by default it is
            treated as a regular expression understood by the
            :py:obj:`re` module and the field matches if its
            appropriate value matches the regular expression using the
            :py:obj:`re.match` method (i.e. if zero or more characters
            at the beginning of field's value match the regular
            expression pattern). See the *exact* parameter for
            details.
            
              *Example:*
                To match a field with standard name of exactly
                "air_temperature" and long name beginning with the
                letter "a": ``match={'standard_name':
                cf.eq('air_temperature'), 'long_name': 'a'}`` (see
                `cf.eq`).

            Some key/value pairs have a special interpretation:

              ==================  ========================================
              Special key         Value
              ==================  ========================================
              ``'units'``         The value must be a string and by
                                  default is evaluated for
                                  equivalence, rather than equality,
                                  with the field's `units` property,
                                  for example a value of ``'Pa'``
                                  will match units of Pascals or
                                  hectopascals, etc. See the *exact*
                                  parameter.
                            
              ``'calendar'``      The value must be a string and by
                                  default is evaluated for
                                  equivalence, rather than equality,
                                  with the field's `calendar`
                                  property, for example a value of
                                  ``'noleap'`` will match a calendar
                                  of noleap or 365_day. See the
                                  *exact* parameter.
                              
              ``'cell_methods'``  The value must be a `CellMethods`
                                  object containing *N* cell methods
                                  and by default is evaluated for
                                  equivalence with the last *N* cell
                                  methods contained within the field's
                                  `cell_methods` property. See the
                                  *exact* parameter.

              `None`              The value is interpreted as for a
                                  string value of the *description*
                                  parameter. For example,
                                  ``description={None: 'air'}`` is
                                  equivalent to ``match='air'`` and
                                  ``description={None: 'ncvar%pressure'}``
                                  is equivalent to
                                  ``description='ncvar%pressure'``.
              ==================  ========================================
            
              *Example:*
                To match a field with standard name starting with
                "air", units of temperature and a netCDF variable name
                beginning with "tas" you could set
                ``match={'standard_name': 'air', 'units': 'K', None:
                'ncvar%tas'}``.

              *Example:*
                To match a field whose last two cell methods are
                equivalent to "time: minimum area: mean":
                ``match={'cell_methods': Cellmethods('time: minimum
                area: mean')``. This would match a field which has,
                for example, cell methods of "height: mean time:
                minimum area: mean".

        If *description* is a sequence of any combination of the above
        then the field matches if it matches **at least one** element
        of the sequence:

          *Example:* 

            >>> f.match('air_temperature')
            True
            >>> f.match('air_pressure')
            False
            >>> f.match({'units': 'hPa', 'long_name': 'foo'})
            False
            >>> f.match(['air_temperature',
            ...          'air_pressure',
            ...          {'units': 'hPa', 'long_name': 'foo'}])
            True
  
        If the sequence is empty then the field always matches.
 
    items: `dict`, optional
        A dictionary which identifies items of the field (dimension
        coordinate, auxiliary coordinate, cell measure or coordinate
        reference objects) with corresponding tests on their
        elements. The field matches if **all** of the specified items
        exist and their tests are passed.

        Each dictionary key specifies an item to test as the one that
        would be returned by this call of the field's `item` method:
        ``f.item(key, exact=exact)`` (see `Field.item`).

        The corresponding value is, in general, any object for which
        the item may be compared with for equality (``==``). The test
        is passed if the result evaluates to True, or if the result is
        an array of values then the test is passed if at least one
        element evaluates to true.

        If the value is `None` then the test is always passed,
        i.e. this case tests for item existence.

          *Example:*
             To match a field which has a latitude coordinate value of
             exactly 30: ``items={'latitude': 30}``.

          *Example:*
             To match a field whose longitude axis spans the Greenwich
             meridien: ``items={'longitude': cf.contain(0)}`` (see
             `cf.contain`).

          *Example:*
             To match a field which has a time coordinate value of
             2004-06-01: ``items={'time': cf.dt('2004-06-01')}`` (see
             `cf.dt`).

          *Example:*
             To match a field which has a height axis: ``items={'Z':
             None}``.

          *Example:*
             To match a field which has a time axis and depth
             coordinates greater then 1000 metres: ``items={'T': None,
             'depth': cf.gt(1000, 'm')}`` (see `cf.gt`).

          *Example:*
            To match a field with time coordinates after than 1989 and
            cell sizes of between 28 and 31 days: ``items={'time':
            cf.dtge(1990) & cf.cellsize(cf.wi(28, 31, 'days'))}`` (see
            `cf.dtge`, `cf.cellsize` and `cf.wi`).

    rank: *optional*
        Specify a condition on the number of axes in the field.  The
        field matches if its number of domain axes equals *rank*. A
        range of values may be selected if *rank* is a `cf.Query`
        object. Not to be confused with the *ndim* parameter (the
        number of data array axes may be fewer than the number of
        domain axes).

          *Example:*
            ``rank=2`` matches a field with exactly two domain axes
            and ``rank=cf.wi(3, 4)`` matches a field with three or
            four domain axes (see `cf.wi`).

    ndim: *optional*
        Specify a condition on the number of axes in the field's data
        array. The field matches if its number of data array axes
        equals *ndim*. A range of values may be selected if *ndim* is
        a `cf.Query` object. Not to be confused with the *rank*
        parameter (the number of domain axes may be greater than the
        number of data array axes).

          *Example:*
            ``ndim=2`` matches a field with exactly two data array
            axes and ``ndim=cf.le(2)`` matches a field with fewer than
            three data array axes (see `cf.le`).

    exact: `bool`, optional
        The *exact* parameter applies to the interpretation of string
        values of the *description* parameter and of keys of the
        *items* parameter. By default *exact* is False, which means
        that:

          * A string value is treated as a regular expression
            understood by the :py:obj:`re` module. 

          * Units and calendar values in a *description* dictionary
            are evaluated for equivalence rather then equality
            (e.g. "metre" is equivalent to "m" and to "km").

          * A cell methods value containing *N* cell methods in a
            *description* dictionary is evaluated for equivalence with
            *the last *N* cell methods contained within the field's
            *`cell_methods` property.

        ..

          *Example:*
            To match a field with a standard name which begins with
            "air" and any units of pressure:
            ``f.match({'standard_name': 'air', 'units': 'hPa'})``.

          *Example:*          
            ``f.match({'cell_methods': CellMethods('time: mean
            (interval 1 hour)')})`` would match a field with cell
            methods of "area: mean time: mean (interval 60 minutes)".

        If *exact* is True then:

          * A string value is not treated as a regular expression.

          * Units and calendar values in a *description* dictionary
            are evaluated for exact equality rather than equivalence
            (e.g. "metre" is equal to "m", but not to "km").

          * A cell methods value in a *description* dictionary is
            evaluated for exact equality to the field's cell methods.
          
        ..

          *Example:*          
            To match a field with a standard name of exactly
            "air_pressure" and units of exactly hectopascals:
            ``f.match({'standard_name': 'air_pressure', 'units':
            'hPa'}, exact=True)``.

          *Example:*          
            To match a field with a cell methods of exactly "time:
            mean (interval 1 hour)": ``f.match({'cell_methods':
            CellMethods('time: mean (interval 1 hour)')``.

        Note that `cf.Query` objects provide a mechanism for
        overriding the *exact* parameter for individual values.

          *Example:*
            ``f.match({'standard_name': cf.eq('air', exact=False),
            'units': 'hPa'}, exact=True)`` will match a field with a
            standard name which begins "air" but has units of exactly
            hectopascals (see `cf.eq`).
    
          *Example:*
            ``f.match({'standard_name': cf.eq('air_pressure'),
            'units': 'hPa'})`` will match a field with a standard name
            of exactly "air_pressure" but with units which equivalent
            to hectopascals (see `cf.eq`).

    match_and: `bool`, optional
        By default *match_and* is True and the field matches if it
        satisfies the conditions specified by each test parameter
        (*description*, *items*, *rank* and *ndim*).

        If *match_and* is False then the field will match if it
        satisfies at least one test parameter's condition.

          *Example:*
            To match a field with a standard name of "air_temperature"
            **and** 3 data array axes: ``f.match('air_temperature',
            ndim=3)``. To match a field with a standard name of
            "air_temperature" **or** 3 data array axes:
            ``f.match('air_temperature", ndim=3, match_and=False)``.
    
    inverse: `bool`, optional
        If True then return the field matches if it does **not**
        satisfy the given conditions.

          *Example:*

            >>> f.match('air', ndim=4, inverse=True) == not f.match('air', ndim=4)
            True

:Returns:

    out: `bool`
        True if the field satisfies the given criteria, False
        otherwise.

:Examples:

Field identity starts with "air":

>>> f.match('air')

Field identity ends contains the string "temperature":

>>> f.match('.*temperature')

Field identity is exactly "air_temperature":

>>> f.match('^air_temperature$')
>>> f.match('air_temperature', exact=True)

Field has units of temperature:

>>> f.match({'units': 'K'}):

Field has units of exactly Kelvin:

>>> f.match({'units': 'K'}, exact=True)

Field identity which starts with "air" and has units of temperature:

>>> f.match({None: 'air', 'units': 'K'})

Field identity starts with "air" and/or has units of temperature:

>>> f.match(['air', {'units': 'K'}])

Field standard name starts with "air" and/or has units of exactly Kelvin:

>>> f.match([{'standard_name': cf.eq('air', exact=False), {'units': 'K'}],
...         exact=True)

Field has height coordinate values greater than 63km:

>>> f.match(items={'height': cf.gt(63, 'km')})

Field has a height coordinate object with some values greater than
63km and a north polar point on its horizontal grid:

>>> f.match(items={'height': cf.gt(63, 'km'),
...                'latitude': cf.eq(90, 'degrees')})

Field has some longitude cell sizes of 3.75:

>>> f.match(items={'longitude': cf.cellsize(3.75)})

Field latitude cell sizes within a tropical region are all no greater
than 1 degree:

>>> f.match(items={'latitude': (cf.wi(-30, 30, 'degrees') &
...                             cf.cellsize(cf.le(1, 'degrees')))})

Field contains monthly mean air pressure data and all vertical levels
within the bottom 100 metres of the atmosphere have a thickness of 20
metres or less:

>>> f.match({None: '^air_pressure$', 'cell_methods': CellMethods('time: mean')},
...         items={'height': cf.le(100, 'm') & cf.cellsize(cf.le(20, 'm')),
...                'time': cf.cellsize(cf.wi(28, 31, 'days'))})

        '''
        conditions_have_been_set = False
        something_has_matched    = False

        if rank is not None:
            conditions_have_been_set = True
            found_match = len(self.axes()) == rank
            if match_and and not found_match:
                return bool(inverse)

            something_has_matched = True
        #--- End: if

        if description:
            conditions_have_been_set = True
             
        # --------------------------------------------------------
        # Try to match other properties and attributes
        # --------------------------------------------------------
        found_match = super(Field, self).match(
            description=description, ndim=ndim, exact=exact,
            match_and=match_and, inverse=False, _Flags=True,
            _CellMethods=True)

        if match_and and not found_match:
            return bool(inverse)

        something_has_matched = found_match

        # ------------------------------------------------------------
        # Try to match items
        # ------------------------------------------------------------
        if items:
            conditions_have_been_set = True

            found_match = False

            for identity, condition in items.iteritems():
                c = self.item(identity, exact=exact)

                if condition is None:
                    field_matches = c is not None
                else:
                    field_matches = condition == c
                    try:
                        field_matches = field_matches.any()
                    except AttributeError:
                        pass
                #--- End: if
                
                if match_and:                    
                    if field_matches:
                        found_match = True 
                    else:
                        found_match = False
                        break
                elif field_matches:
                    found_match = True
                    break
            #--- End: for 

            if match_and and not found_match:
                return bool(inverse)

            something_has_matched = found_match
        #--- End: if

        if conditions_have_been_set:
            if something_has_matched:            
                return not bool(inverse)
            else:
                return bool(inverse)
        else:
            return not bool(inverse)
    #--- End: def

    def axis_name(self, axes=None, default=None, **kwargs):
        '''Return the canonical name for an axis.

{+axis_selection}

.. seealso:: `axis`, `axis_size`, `item`

:Parameters:

    {+axes, kwargs}

:Returns:

    out: `str`
        The canonical name for the axis.

:Examples:

>>> f.axis_name('dim0')
'time'
>>> f.axis_name('X')
'dim1'
>>> f.axis_name('long_name%latitude')
'ncdim%lat'

        '''      
        axis = self.axis(axes, key=True, **kwargs)
        if axis is None:
            raise ValueError("No unique axis could be identified")

        return self.Items.axis_name(axis, default=default)
    #--- End: def

    def axes_names(self, axes=None, **kwargs):
        '''Return the canonical names for domain axes.

{+axis_selection}

.. seealso:: `axis`, `axis_name`, `axis_size`, `item`

:Parameters:

    {+axes, kwargs}

:Returns:

    out: `dict`
        The canonical name for the axis. DCH

:Examples:

>>> f.axis_names()
'time' DCH
>>> f.axis_name('X')
'dim1' DCH
>>> f.axis_name('long_name%latitude')
'ncdim%lat' DCH

        '''          
        out = {}
        for axis in self.Axes:
            out[axis] = self.Items.axis_name(axis)

        return out
    #--- End: def

    def axis_size(self, axes=None, **kwargs):
        '''Return the size of a domain axis.

{+axis_selection}

.. seealso:: `axis`, `axis_name`, `axis_identity`

:Parameters:

    {+axes, kwargs}

:Returns:
    
    out: `int`
        The size of the axis.

:Examples:

>>> f
<CF Field: eastward_wind(time(3), air_pressure(5), latitude(110), longitude(106)) m s-1>
>>> f.axis_size('longitude')
106
>>> f.axis_size('Z')
5
        '''
        axis = self.axis(axes, key=True, **kwargs)
        if axis is None:
            return None

        return self.Axes[axis].size
    #--- End: def

    def axes(self, axes=None, size=None, ordered=False, **kwargs):
        '''Return domain axis identifiers from the field.

The output is a set of domain axis identifiers, which may be empty.

{+axis_selection}

.. seealso:: `axis`, `data_axes`, `item_axes`, `items`, `remove_axes`

:Parameters:

    {+axes, kwargs}

          *Example:*

            >>> x = f.axes(['dim2', 'time', {'units': 'degree_north'}])
            >>> y = set()
            >>> for axes in ['dim2', 'time', {'units': 'degree_north'}]:
            ...     y.update(f.axes(axes))
            ...
            >>> x == y
            True
 
    {+size}

    ordered: `bool`, optional
        Return an ordered list of axes instead of an unordered
        set. The order of the list will reflect any ordering specified
        by the *axes* and *kwargs* parameters.

          *Example:*
            If the data array axes, as returned by the field's
            `data_axes` method, are ``['dim0', 'dim1', 'dim2']``, then
            ``f.axes([2, 0, 1, 2])`` will return ``set(['dim0',
            'dim1', 'dim2'])``, but ``f.axes([2, 0, 1, 2],
            ordered=True)`` will return ``['dim2', 'dim0', 'dim1',
            'dim2']``.

:Returns:

    out: `dict` or `OrderedDict`
        A dictionary of domain axis identifiers and their sizes, or an
        `OrderedDict` if *ordered* is True.

:Examples:

All axes and their identities:

>>> f.axes()
set(['dim0', 'dim1', 'dim2', 'dim3'])
>>> dict([(axis, f.domain.axis_name(axis)) for axis in f.axes()])
{'dim0': time(12)
 'dim1': height(19)
 'dim2': latitude(73)
 'dim3': longitude(96)}

Axes which are not spanned by the data array:

>>> f.axes().difference(f.data_axes())

        '''
        def _axes(self, axes, size, items_axes, data_axes, domain_axes,
                  kwargs):
            ''':Parameters:

        items_axes: `dict`
            Dictionary of item axes keyed by the item identifiers.

        data_axes: sequence of `str`
            The domain axis identifiers for the data array.
            
        domain_axes: `dict`
            Dictionary of `DomainAxis` objects keyed by their
            identifiers.

            '''
            a = None

            if axes is not None:
                if axes.__hash__:
                    if isinstance(axes, slice):
                        # --------------------------------------------
                        # axes is a slice object
                        # -------------------------------------------
                        if data_axes is not None:
                            try:                            
                                a = tuple(data_axes[axes])
                            except IndexError:
                                a = []
                        else:
                            a = []
                    elif axes in domain_axes:
                        # --------------------------------------------
                        # axes is a domain axis identifier
                        # --------------------------------------------
                        a = [axes]
                    elif axes in items_axes and not kwargs:
                        # --------------------------------------------
                        # axes is a domain item identifier
                        # --------------------------------------------
                        a = items_axes[axes][:]
                    else:
                        try:
                            axes_is_ncdim_name = axes.startswith('ncdim%')
                        except AttributeError:
                            axes_is_ncdim_name = False

                        if axes_is_ncdim_name:
                            # ----------------------------------------
                            # axes is a netCDF dimension name
                            # ----------------------------------------
                            ncdimensions = self.ncdimensions
                            if ncdimensions:
                                ncdim = axes[6:]  # Note: There are 6 characters in 'ncdim%'
                                tmp = []
                                for axis, value in ncdimensions.iteritems():
                                    if value == ncdim:
                                        tmp.append(axis)
                                if tmp:
                                    a = tmp
                        else:
                            try:
                                # --------------------------------
                                # If this works then axes is a
                                # valid integer
                                # --------------------------------
                                a = [data_axes[axes]]
                            except IndexError:
                                # axes is an out-of bounds integer
                                a = []
                            except TypeError:
                                # ------------------------------------
                                # Axes is something else, or data_axes
                                # is None
                                # ------------------------------------
                                a = None    
                #--- End: if
 
            elif not kwargs:
                if not data_axes:
                    data_axes = ()
                a = []
                for x in domain_axes:
                    if x not in data_axes:
                        a.append(x)

                a.extend(data_axes)
            #--- End: if

            if a is None:
                # ----------------------------------------------------
                # Assume that axes is a value accepted by the items
                # method
                # ----------------------------------------------------
                a = [] 
                kwargs2 = kwargs.copy()
                kwargs2['axes'] = None
                for key in self.items(axes, **kwargs2):
                    a += items_axes.get(key, ())
            #--- End: if

            if size:
                a = [axis for axis in a if size == domain_axes[axis]]

            return a
        #--- End: def

#        role = kwargs.get('role', None)
#        if role is None:
#            # By default, omit coordinate reference items from the
#            # axis selection.
#            kwargs['role'] = ('d', 'a', 'm', 'f', 'c')

        domain_axes = self.Axes

        data_axes  = self.data_axes()
        items_axes = self.items_axes()

        if axes is None or isinstance(axes, (basestring, dict, slice,
                                             int, long)):
            # --------------------------------------------------------
            # axes is not a sequence or a set
            # --------------------------------------------------------
            a = _axes(self, axes, size, items_axes, data_axes,
                      domain_axes, kwargs)
        else:   
            # --------------------------------------------------------
            # axes is a sequence or a set
            # --------------------------------------------------------
            a = []
            for x in axes:
                a += _axes(self, x, size, items_axes, data_axes,
                           domain_axes, kwargs)
        #--- End: if

        if ordered:
            out = OrderedDict()
        else:
            out = {}    

        for x in a:
            out[x] = domain_axes[x]
            
        return out
    #--- End: def
        
    def axis(self, axes=None, size=None, default=None, key=False,
             **kwargs):
        '''Return a domain axis.

{+axis_selection}

.. seealso:: `axes`, `data_axes`, `item_axes`, `item`, `remove_axis`

:Examples 1:

>>> a = f.{+name}('time')

:Parameters:

    {+axes, kwargs}
 
    {+size}

:Returns:

    out: `str` or `None`
        The unique domain axis, or its identifier or, if there is no
        unique item, `None`.

:Examples 2:

>>> f
<CF Field: air_temperature(time(12), latitude(64), longitude(128)) K>
>>> f.data_axes()
['dim0', 'dim1', 'dim2']
>>> f.axis('time')
'dim0'
>>> f.axis('Y')
'dim1'
>>> f.axis(size=64)
'dim1'
>>> f.axis('X', size=128)
'dim2'
>>> print f.axis('foo')
None
>>> print f.axis('T', size=64)
None

        '''
        kwargs2 = self._parameters(locals())

        key = kwargs2.pop('key')

        del kwargs2['default'] 
        kwargs2['ordered'] = False
  
        d = self.axes(**kwargs2)
        if not d:
            return default

        axes = d.popitem()

        if d:
            return default 

        if key:
            return axes[0]
        else:
            return axes[1]
    #--- End: def

    def insert_cell_method(self, item):
        '''Insert cell method objects into the {+variable}.

.. seealso:: `insert_aux`, `insert_measure`, `insert_ref`,
             `insert_data`, `insert_dim`

:Parameters:

    item: `CellMethod`

:Returns:

    `None`

:Examples:

        '''
#        if isinstance(item, basestring):
#            item = self._CellMethod.parse(item)
            
        self.Items.cell_methods.append(item)
        self.Items.cell_methods = self._conform_cell_methods()
    #--- End: def

    def insert_axis(self, axis, key=None, replace=True, copy=True):
        '''Insert a domain axis into the {+variable}.

.. seealso:: `insert_aux`, `insert_measure`, `insert_ref`,
             `insert_data`, `insert_dim`

:Parameters:

    axis: `DomainAxis`
        The new domain axis.

    key: `str`, optional
        The identifier for the new axis. By default a new,
        unique identifier is generated.
  
    replace: `bool`, optional
        If False then do not replace an existing axis with the same
        identifier but a different size. By default an existing axis
        with the same identifier is changed to have the new size.

:Returns:

    out: `str`
        The identifier of the new domain axis.


:Examples:

>>> f.insert_axis(DomainAxis(1))
>>> f.insert_axis(DomainAxis(90), key='dim4')
>>> f.insert_axis(DomainAxis(23), key='dim0', replace=False)

        '''
        if key is None:
            key = self.new_identifier('axis')

        if not replace and key in self.Axes and self.Axes[key].size != axis.size:
            raise ValueError(
"Can't insert axis: Existing axis {!r} has different size (got {}, expected {})".format(
    key, axis.size, self.Axes[key].size))

        if copy:
            axis = axis.copy()

        self.Axes[key] = axis

        return key
    #--- End: def

    def new_identifier(self, item_type):
        '''

Return a new, unique auxiliary coordinate identifier for the domain.

.. seealso:: `new_measure_identifier`, `new_dimemsion_identifier`,
             `new_ref_identifier`

The domain is not updated.

:Parameters:

    item_type: `str`

:Returns:

    out: `str`
        The new identifier.

:Examples:

>>> d.items().keys()
['aux2', 'aux0', 'dim1', 'ref2']
>>> d.new_identifier('aux')
'aux3'
>>> d.new_identifier('ref')
'ref1'

>>> d.items().keys()
[]
>>> d.new_identifier('dim')
'dim0'


>>> d.axes()
{'dim0', 'dim4'}
>>> d.new_identifier('axis')
'dim2'

>>> d.axes()
{}
>>> d.new_identifier('axis')
'dim0'

'''
        if item_type in ('axis', 'dim'):
            keys = self.Axes
            item_type = 'dim'
        else:
            keys = getattr(self.Items, item_type[0])
        
        n = len(keys)
        key = '{0}{1}'.format(item_type, n)

        while key in keys:
            n += 1
            key = '{0}{1}'.format(item_type, n)
        #--- End: while

        return key
    #--- End: def

    def insert_field_anc(self, item, key=None, axes=None, copy=True,
                         replace=True):
        '''Insert a field ancillary object into the {+variable}.
        
    {+copy_item_in}
      
        '''
        if key is None:
            key = self.new_identifier('fav')
        elif key in self.Items.f and not replace:
            raise ValueError(
"Can't insert field ancillary object: Identifier {0!r} already exists".format(key))

        axes = self._insert_item_parse_axes(item, 'field ancillary', 
                                            axes, allow_scalar=True)

        if copy:
            item = item.copy()

        # Turn a scalar field ancillary into 1-d
        if item.isscalar:
            item = item.expand_dims(0, copy=False)

        self.Items.insert_field_anc(item, key=key, axes=axes, copy=False)

        return key
    #--- End: def

    def insert_domain_anc(self, item, key=None, axes=None, copy=True,
                          replace=True):
        '''Insert a domain ancillary object into the {+variable}.
      
    {+copy_item_in}
        '''
       
        if key is None:
            key = self.new_identifier('cct')
        elif key in self.Items.c and not replace:
            raise ValueError(
"Can't insert domain ancillary object: Identifier {0!r} already exists".format(key))

        axes = self._insert_item_parse_axes(item, 'domain ancillary', 
                                            axes, allow_scalar=True)
        if copy:
            item = item.copy()

#        # Turn a scalar domain ancillary into 1-d
#        if item.isscalar:
#            item = item.expand_dims(0, copy=False)

        self.Items.insert_domain_anc(item, key=key, axes=axes, copy=False)

        refs = self.items(role='r')
        if refs:
            for ref in refs.itervalues():
                self._conform_ref(ref, copy=False)

        return key
    #--- End: def

    def _parameters(self, d):
        '''
.. versionadded:: 1.6
'''
        del d['self']
        if 'kwargs' in d:
            d.update(d.pop('kwargs'))
        return d
    #--- End: def

    def _conform_ref(self, ref, copy=True):
        '''Where possible, replace the content of ref.coordinates with
coordinate identifiers and the values of domain ancillary terms with
domain ancillary identifiers.

:Parameters:

    ref: `CoordinateReference`

:Returns:

    `None`

:Examples:

>>> s = f._conform_ref(r)
>>> s = f._conform_ref(r, copy=False)

        '''
        if copy:
            ref = ref.copy()

        identity_map = {}
        role = ('d', 'a')        
        for identifier in ref.coordinates:
            key = self.Items.key(identifier, role=role, exact=True)
            if key is not None:
                identity_map[identifier] = key
        #--- End: for
        ref.change_identifiers(identity_map, ancillary=False, copy=False)

        identity_map = {}
        for identifier in ref.ancillaries.values():
            key = self.item(identifier, role='c', exact=True, key=True)
            if key is not None:
                identity_map[identifier] = key
        #--- End: for

# DCH inplace??
        ref.change_identifiers(identity_map, coordinate=False, copy=False)
    #--- End: def

    def _conform_cell_methods(self):
        '''

:Examples 1:

>>> f._conform_cell_methods()

:Parameters:

    cms: 

:Returns:

    out: `list`

:Examples 2:

        '''
        cms = self.Items.cell_methods
        
        axis_map = {}
        for cm in cms:
            for axis in cm.axes:
                if axis in axis_map:
                    continue

                if axis == 'area':
                    axis_map[axis] = axis
                    continue

                axis_map[axis] = self.axis(axis, default=axis, ndim=1, key=True)
        #--- End: for

        return [cm.change_axes(axis_map) for cm in cms]
    #--- End: def

#    def _unconform_cell_methods(self, cms, copy=True):
#        '''
#
#:Parameters:
#
#:Returns:
#
#    out: `CellMethods`
#
#:Examples:
#
#>>> f._unconform_cell_methods()
#
#        '''
#        axes_names = self.axes_names()
#
#        axis_map = {}
#        for cm in cms:
#            for axis in cm.axes:
#                if axis in axes_names:
#                    axis_map[axis] = axes_names.pop(axis)
#        #--- End: for
#
#        return [cm.change_axes(axis_map) for cm in cms]
#    #--- End: def

    def _unconform_ref(self, ref, copy=True):
        '''Replace the content of ref.coordinates with coordinate identifiers
and domain ancillaries where possible.

:Parameters:

    ref: `CoordinateReference`

:Returns:

    `None`

:Examples:

>>> s = f._unconform_ref(r)
>>> s = f._unconform_ref(r, copy=False)
        
        '''
        if copy:
            ref = ref.copy()
            
        identity_map = {}
        role = ('d', 'a')        
        for identifier in ref.coordinates:
            item = self.item(identifier, role=role, exact=True)
            if item is not None:
                identity_map[identifier] = item.identity()
        #--- End: for
        ref.change_identifiers(identity_map, ancillary=False, strict=True, copy=False)
 
        identity_map = {}
        role = ('c',)
        for identifier in ref.ancillaries.values():
            anc = self.item(identifier, role=role, exact=True)
            if anc is not None:
                identity_map[identifier] = anc.identity()
        #--- End: for
        ref.change_identifiers(identity_map, coordinate=False, strict=True, copy=False)
# DCH inplace??
        return ref
    #--- End: def

    def insert_item(self, role, item, key=None, axes=None,
                    copy=True, replace=True):
        '''Insert an item into the {+variable}.

.. seealso:: `insert_axis`, `insert_measure`, `insert_data`,
             `insert_dim`, `insert_ref`

:Parameters:

    role: `str`

    item: `AuxiliaryCoordinate` or `cf.Coordinate` or `cf.DimensionCoordinate`
        The new auxiliary coordinate object. If it is not already a
        auxiliary coordinate object then it will be converted to one.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    axes: sequence of `str`, optional
        The ordered list of axes for the *item*. Each axis is given by
        its identifier. By default the axes are assumed to be
        ``'dim0'`` up to ``'dimM-1'``, where ``M-1`` is the number of
        axes spanned by the *item*.

    copy: `bool`, optional
        If False then the *item* is not copied before insertion. By
        default it is copied.
      
    replace: `bool`, optional
        If False then do not replace an existing auxiliary coordinate
        object of domain which has the same identifier. By default an
        existing auxiliary coordinate object with the same identifier
        is replaced with *item*.
    
:Returns:

    out: `str`
        The identifier for the inserted *item*.

:Examples:

>>>
        '''
        kwargs2 = self._parameters(locals())
        del kwargs2['role']

        if role == 'd':
            return self.insert_dim(**kwargs2)
        if role == 'a':
            return self.insert_aux(**kwargs2)
        if role == 'm':
            return self.insert_measure(**kwargs2)
        if role == 'c':
            return self.insert_domain_anc(**kwargs2)
        if role == 'f':
            return self.insert_field_anc(**kwargs2)
        if role == 'r':
            return self.insert_ref(**kwargs2)
    #--- End: def

    def insert_measure(self, item, key=None, axes=None, copy=True, replace=True):
        '''Insert a cell measure object into the {+variable}.

.. seealso:: `insert_axis`, `insert_aux`, `insert_data`, `insert_dim`,
             `insert_ref`

:Parameters:

    item: `CellMeasure`
        The new cell measure object.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    axes: sequence of `str`, optional
        The ordered list of axes for the *item*. Each axis is given by
        its identifier. By default the axes are assumed to be
        ``'dim0'`` up to ``'dimM-1'``, where ``M-1`` is the number of
        axes spanned by the *item*.

    {+copy_item_in}
      
    replace: `bool`, optional
        If False then do not replace an existing cell measure object
        of domain which has the same identifier. By default an
        existing cell measure object with the same identifier is
        replaced with *item*.
    
:Returns:

    out: 
        The identifier for the *item*.

:Examples:

>>>

        '''
        if key is None:
            key = self.new_identifier('msr')

        if key in self.axes() and not replace:
            raise ValueError(
"Can't insert cell measure object: Identifier {0!r} already exists".format(key))

        axes = self._insert_item_parse_axes(item, 'cell measure', axes,
                                            allow_scalar=False)

        if copy:
            item = item.copy()

        # Convert scalar cell measure to 1-d
        if item.isscalar:
            item = item.expand_dims(0, copy=False)

        self.Items.insert_measure(item, key=key, axes=axes, copy=False)

        return key
    #--- End: def

    def insert_dim(self, item, key=None, axes=None, copy=True, replace=True):
        '''Insert a dimension coordinate object into the {+variable}.

.. seealso:: `insert_aux`, `insert_axis`, `insert_item`,
             `insert_measure`, `insert_data`, `insert_ref`,
             `remove_item`

:Parameters:

    item: `DimensionCoordinate` or `cf.Coordinate` or `cf.AuxiliaryCoordinate`
        The new dimension coordinate object. If it is not already a
        dimension coordinate object then it will be converted to one.

    axes: sequence of `str`, optional
        The axis for the *item*. The axis is given by its domain
        identifier. By default the axis will be the same as the given
        by the *key* parameter.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    {+copy_item_in}

    replace: `bool`, optional
        If False then do not replace an existing dimension coordinate
        object of domain which has the same identifier. By default an
        existing dimension coordinate object with the same identifier
        is replaced with *item*.
    
:Returns:

    out: 
        The identifier for the inserted *item*.

:Examples:

>>>

        '''
        if copy:
            item = item.copy()
            
        if key is None and axes is None:
            # Key is not set and axes is not set
            item_size = item.size
            c = [axis for axis, domain_axis in self.Axes.iteritems() 
                 if domain_axis == item_size]
            if len(c) == 1:
                key = c[0]
                if self.items(role='d', axes_all=key):
                    key = self.insert_axis(self._DomainAxis(item_size))
                axes = [key]
            elif not c:
                key = self.insert_axis(self._DomainAxis(item_size))
                axes = [key]
            else:
                raise ValueError(
"Ambiguous dimension coordinate object size. Condsider setting the key or axes parameter")

        elif key is not None:
            if axes is None:
                # Key is set, axes is not set
                axes = [key]
                if key not in self.Axes:
                    key = self.insert_axis(self._DomainAxis(item.size), key=key)
            elif axes != [key]:
                # Key is set, axes is set
                raise ValueError(
                    "Incompatible key and axes parameters: {0!r}, {1!r}".format(
                        key, axes))

            axes = self._insert_item_parse_axes(item, 'dimension coordinate',
                                                axes, allow_scalar=False)
        else:
            # Key is not set, axes is set
            key = axes[0]
            axes = self._insert_item_parse_axes(item, 'dimension coordinate',
                                                axes, allow_scalar=False)    

        if key in self.Items.d and not replace:
            raise ValueError(
"Can't insert dimension coordinate object: Identifier {!r} already exists".format(key))

        # Turn a scalar dimension coordinate into 1-d
        if item.isscalar:
            item = item.expand_dims(0, copy=False)
        
        self.Items.insert_dim(item, key=key, axes=axes, copy=False)

        refs = self.Items.refs()
        if refs:
            for ref in refs.itervalues():
                self._conform_ref(ref, copy=False)
                
        if self.Items.cell_methods:
            self.Items.cell_methods = self._conform_cell_methods()

        return key
    #--- End: def

    def insert_ref(self, item, key=None, axes=None, copy=True, replace=True):
        '''Insert a coordinate reference object into the {+variable}.

.. seealso:: `insert_axis`, `insert_aux`, `insert_measure`,
             `insert_data`, `insert_dim`
             
:Parameters:

    item: `CoordinateReference`
        The new coordinate reference object.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    axes: *optional*
        *Ignored*

    {+copy_item_in}

    replace: `bool`, optional
        If False then do not replace an existing coordinate reference object of
        domain which has the same identifier. By default an existing
        coordinate reference object with the same identifier is replaced with
        *item*.
    
:Returns:

    out: 
        The identifier for the *item*.


:Examples:

>>>

        '''
        if key is None:
            key = self.new_identifier('ref')

        if copy:
            item = item.copy()

        self._conform_ref(item, copy=False)

        self.Items.insert_ref(item, key=key, copy=False)

        return key
    #--- End: def

    def item_axes(self, description=None, role=None, axes=None,
                  axes_all=None, axes_subset=None, axes_superset=None,
                  exact=False, inverse=False, match_and=True,
                  ndim=None, default=None):
        '''Return the axes of a domain item of the field.

An item is a dimension coordinate, an auxiliary coordinate, a cell
measure or a coordinate reference object.

.. seealso:: `axes`, `data_axes`, `item`

:Parameters:

    {+description}

    {+role}

    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+match_and}

    {+exact}
       
    {+inverse}

:Returns:

    out: `list` or `None`
        The ordered list of axes for the item or, if there is no
        unique item or the item is a coordinate reference then `None`
        is returned.

:Examples:

'''    
        kwargs2 = self._parameters(locals())
        kwargs2['key'] = True

        del kwargs2['default']

        key = self.item(**kwargs2)
        if key is None:
            return default

        return list(self.Items.axes(key=key))
    #--- End: def

    def key(self, description=None, role=None, axes=None,
            axes_all=None, axes_subset=None, axes_superset=None,
            exact=False, inverse=False, match_and=True, ndim=None,
            default=None):
#            _restrict_inverse=False):
        '''Return the identifier of a field item.

{+item_definition}
 
If no unique item can be found then the value of the *default*
parameter is returned.

{+item_selection}
 
.. versionadded:: 2.0

.. seealso:: `item`, `items`

:Examples 1:

>>> key = f.{+name}('X')

:Parameters:

    {+description}

    {+role}

    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+match_and}

    {+exact}
       
    {+inverse}

    {+default}

:Returns:

    out: 
        The unique item identifier or, if there is no unique item, the
        value of the *default* parameter.

:Examples 2:

>>>
        '''
        kwargs2 = self._parameters(locals())

        del kwargs2['default']

        d = self.items(**kwargs2)
        if not d:
            return default

        items = d.popitem()

        return default if d else items[0]
    #--- End: def

    def items_axes(self, description=None, role=None, axes=None,
                   axes_all=None, axes_subset=None, axes_superset=None,
                   exact=False, inverse=False, match_and=True,
                   ndim=None):
        '''Return the axes of items of the field.

An item is a dimension coordinate, an auxiliary coordinate, a cell
measure or a coordinate reference object.   .......................................

.. seealso:: `axes`, `data_axes`, `item`

:Parameters:

    {+description}

    {+role}

    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+match_and}

    {+exact}
       
    {+inverse}

:Returns:

    out: `dict`
        
:Examples:

'''    
        kwargs2 = self._parameters(locals())
        
        out = {}
        for key in self.items(**kwargs2):
            out[key] = self.Items.axes(key=key)

        return out
    #--- End: def

    def item(self, description=None, role=None, axes=None, axes_all=None,
             axes_subset=None, axes_superset=None, exact=False,
             inverse=False, match_and=True, ndim=None, key=False,
             default=None, copy=False): #, _restrict_inverse=True):
        '''Return a field item.

{+item_definition}
 
{+item_selection}

The output is the unique item found from the selection criteria (see
the *key* parameter).

If no unique item can be found which meets the given selection
critiera then the value of the *default* parameter is returned.

{+items_criteria}

To find multiple items, use the `~Field.{+name}s` method.

.. seealso:: `aux`, `measure`, `coord`, `ref`, `dim`, `item_axes`,
             `items`, `remove_item`

:Examples 1:

>>> item = f.{+name}('X')

:Parameters:

    {+description}

    {+role}

    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+match_and}

    {+exact}
       
    {+inverse}

    {+key}

    {+default}

    {+copy}

:Returns:

    out: 
        The unique item or its identifier or, if there is no
        unique item, the value of the *default* parameter.

:Examples 2:

>>>

        '''
        kwargs2 = self._parameters(locals())

        del kwargs2['key']
        del kwargs2['default']

        d = self.items(**kwargs2)
        if not d:
            return default

        items = d.popitem()

        if d:
            return default

        if key:
            return items[0] 
        else:
            return items[1] 
    #--- End: def

    def key_item(self, description=None, role=None, axes=None,
                 axes_all=None, axes_subset=None, axes_superset=None,
                 exact=False, inverse=False, match_and=True,
                 ndim=None, copy=False, default=(None, None)):
        '''Return an item, or its identifier, from the field.

{+item_definition}
 
If no unique item can be found then the value of the *default*
parameter is returned.

{+item_selection}

.. versionadded:: 2.0 

.. seealso:: `item`, `items`

:Examples 1:

>>> key, item = f.{+name}('X')

:Parameters:

    {+description}

    {+role}

    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+match_and}

    {+exact}
       
    {+inverse}

    {+default}

    {+copy}

:Returns:

    out: 
        The unique item identifier or, if there is no unique item, the
        value of the *default* parameter.

:Examples 2:

>>>

        '''
        kwargs2 = self._parameters(locals())

        del kwargs2['default']

        d = self.items(**kwargs2)
        if not d:
            return default

        items = d.popitem()

        if d:
            return default

        return items
    #--- End: def

    def items(self, description=None, role=None, axes=None, axes_all=None,
              axes_subset=None, axes_superset=None, ndim=None,
              match_and=True, exact=False, inverse=False, copy=False):
#              _restrict_inverse=False):
        '''Return items of the field.

{+item_definition}

{+item_selection}

The output is a dictionary whose key/value pairs are item identifiers
with corresponding values of items of the field. If no items are found
then the dictionary will be empty.

{+items_criteria}

To find a unique item, use the `item` method.

.. seealso:: `auxs`, `axes`, `measures`, `coords`, `dims`, `item`, `match`
             `remove_items`, `refs`

:Examples 1:

Select all items whose identities (as returned by their `!identity`
methods) start "height":

>>> f.{+name}('height')

Select all items which span only one axis:

>>> f.items(ndim=1)

Select all cell measure objects:

>>> f.items(role='m')

Select all items which span the "time" axis:

>>> f.items(axes='time')

Select all CF latitude coordinate objects:

>>> f.items('Y')

Select all multidimensional dimension and auxiliary coordinate objects
which span at least the "time" and/or "height" axes and whose long
names contain the string "qwerty":

>>> f.items('long_name:.*qwerty', 
...         role='da',
...         axes=['time', 'height'],
...         ndim=cf.ge(2))

:Parameters:

    {+description}

          *Example:* 

            >>> x = f.items(['aux1',
            ...             'time',
            ...             {'units': 'degreeN', 'long_name': 'foo'}])
            >>> y = {}
            >>> for items in ['aux1', 'time', {'units': 'degreeN', 'long_name': 'foo'}]:
            ...     y.update(f.items(items))
            ...
            >>> set(x) == set(y)
            True

    {+role}

    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+match_and}

    {+exact}

    {+inverse}

          *Example:*
            ``f.items(role='da', inverse=True)`` selects the same
            items as ``f.items(role='mr')``.

    {+copy}

:Returns:

    out: `dict`
        A dictionary whose keys are domain item identifiers with
        corresponding values of items. The dictionary may be empty.

:Examples:

        '''
        kwargs2 = self._parameters(locals())

        # Parse the various axes options
        if axes is not None:
            if not isinstance(axes, dict):
                axes = {'axes': axes}

            kwargs2['axes'] = set(self.axes(**axes))

        if axes_subset is not None:
            if not isinstance(axes_subset, dict):
                axes_subset = {'axes': axes_subset}

            kwargs2['axes_subset'] = set(self.axes(**axes_subset))

        if axes_superset is not None:
            if not isinstance(axes_superset, dict):
                axes_superset = {'axes': axes_superset}

            kwargs2['axes_superset'] = set(self.axes(**axes_superset))

        if axes_all is not None:
            if not isinstance(axes_all, dict):
                axes_all = {'axes': axes_all}

            kwargs2['axes_all'] = set(self.axes(**axes_all))

        # By default, omit coordinate reference items.
        if role is None:
            kwargs2['role'] = ('d', 'a', 'm', 'c', 'f')

        return self.Items(**kwargs2)
    #--- End: def
 
    def remove_item(self, description=None, role=None, axes=None,
                    axes_all=None, axes_subset=None,
                    axes_superset=None, ndim=None, exact=False,
                    inverse=False, match_and=True, key=False):
        '''Remove and return an item from the field.

{+item_definition}

By default all items of the domain are removed, but particular items
may be selected with the keyword arguments.

{+item_selection}

.. seealso:: `items`, `remove_axes`, `remove_axis`, `remove_item`

:Parameters:

    {+description}

    {+role}

    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+match_and}

    {+exact}

    {+inverse}

:Returns:

    out: 
        A dictionary whose keys are domain item identifiers with
        corresponding values of the removed items. The dictionary may
        be empty.

:Examples:

        '''
        kwargs2 = self._parameters(locals())

#        kwargs2['items'] = kwargs2.pop('item')

        del kwargs2['key']

        # Include coordinate references by default
        if kwargs2['role'] is None:
            kwargs2['role'] = ('d', 'a', 'm', 'c', 'f', 'r')

        items = self.items(**kwargs2)
        if len(items) == 1:
            out = self.remove_items(**kwargs2)
            if key:
                return out.popitem()[0]
            return out.popitem()[1]
            
        if not len(items):
            raise ValueError(
"Can't remove non-existent item defined by parameters {0}".format(kwargs2))
        else:
            raise ValueError(
"Can't remove non-unique item defined by parameters {0}".format(kwargs2))
    #--- End: def

    def remove_items(self, description=None, role=None, axes=None,
                     axes_all=None, axes_subset=None,
                     axes_superset=None, ndim=None, exact=False,
                     inverse=False, match_and=True):
        '''Remove and return items from the field.

An item is either a dimension coordinate, an auxiliary coordinate, a
cell measure or a coordinate reference object.

By default all items of the domain are removed, but particular items
may be selected with the keyword arguments.

.. seealso:: `items`, `remove_axes`, `remove_axis`, `remove_item`

:Parameters:

    {+description}

    {+role}

    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+match_and}

    {+exact}

    {+inverse}

:Returns:

    out: `dict`
        A dictionary whose keys are domain item identifiers with
        corresponding values of the removed items. The dictionary may
        be empty.

:Examples:

        '''
        kwargs2 = self._parameters(locals())

        # Include coordinate references by default
        if kwargs2['role'] is None:
            kwargs2['role'] = ('d', 'a', 'm', 'c', 'f', 'r')

        Items = self.Items
        role  = Items.role

        items = self.items(**kwargs2)

        out = {}
 
        for key, item in items.items():
            if role(key) == 'r':
                ref = Items.remove_item(key)
                out[key ] = self._unconform_ref(ref)
                del items[key]
                
        for key, item in items.iteritems():
            item_role = role(key)

            if item_role in 'dac':
                # The removed item is a dimension coordinate,
                # auxiliary coordinate or domain ancillary, so replace
                # its identifier in any coordinate references with its
                # identity.
                identity_map = {key: item.identity()}
                for ref in self.Items.refs().itervalues():
                    ref.change_identifiers(identity_map,
                                           coordinate=(item_role!='c'),
                                           ancillary=(item_role=='c'),
                                           copy=False)
            #--- End: if
                
            out[key] = Items.remove_item(key)        
        #--- End: if        
                                                      
        return out
    #--- End: def

    def remove_axes(self, axes=None, size=None, **kwargs):
        '''

Remove and return axes from the field.

By default all axes of the domain are removed, but particular axes may
be selected with the keyword arguments.

The axis may be selected with the keyword arguments. If no unique axis
can be found then no axis is removed and `None` is returned.

If an axis has size greater than 1 then it is not possible to remove
it if it is spanned by the field's data array or any multidimensional
coordinate or cell measure object of the field.

.. seealso:: `axes`, `remove_axis`, `remove_item`, `remove_items`

:Parameters:

    {+axes, kwargs}

    {+size}

:Returns:

    out: `dict`
        The removed axes. The dictionary may be empty.

:Examples:

'''
        axes = self.axes(axes, size=size, **kwargs)
        if not axes:
            return axes

        axes = set(axes)

        size1_data_axes = []
        domain_axes = self.axes()
        if self.data_axes() is not None:
            for axis in axes.intersection(domain_axes).intersection(self.data_axes()):
                if domain_axes[axis] == 1:
                    size1_data_axes.append(axis)
                else:
                    raise ValueError(
"Can't remove an axis with size > 1 which is spanned by the data array")
        #---End: if

        for axis in axes:
            if (domain_axes[axis] > 1 and
                self.items(ndim=2, axes=axis)):  ##### DCH replace 2 with equivalent to  cf.gt (1) 
                raise ValueError(
"Can't remove an axis with size > 1 which is spanned by a multidimensional item")
        #--- End: for

        # Replace the axis in cell methods with a standard name, if
        # possible.
        cell_methods = self.Items.cell_methods
        if cell_methods:            
            axis_map = {}
            del_axes = []
            for axis in axes:
                coord = self.item(role=('d',), axes=axis)
                standard_name = getattr(coord, 'standard_name', None)
                if standard_name is None:
                    coord = self.item(role=('a',), ndim=1, axes_all=axis)
                    standard_name = getattr(coord, 'standard_name', None)
                if standard_name is not None:
                    axis_map[axis] = standard_name
                else:
                    del_axes.append(axis)
        #--- End: if

        # Remove coordinate references which span any of the removed axes
        for key in self.items(role='r'):
            if axes.intersection(self.Items.axes(key)):
                self.Items.remove_item(key)

        for key, item in self.items(axes=axes).iteritems():
            item_axes = self.item_axes(key)

            # Remove the item if it spans only removed axes
            if axes.issuperset(item_axes):
                self.Items.remove_item(key)
                continue            

            # Still here? Then squeeze removed axes from the item,
            # which must be multidimensional and have size 1 along the
            # axes to be removed.
            iaxes = [item_axes.index(axis) for axis in axes
                     if axis in item_axes]
            item.squeeze(iaxes, copy=False)

            # Remove the removed axes from the multidimensional item's
            # list of axes
            for axis in axes.intersection(item_axes):
                item_axes.remove(axis)

            self.Items.axes(key, axes=item_axes)
        #--- End: for

        if size1_data_axes:
            self.squeeze(size1_data_axes, copy=False)
            
        # Replace the axis in cell methods with a standard name, if
        # possible.
        if cell_methods:
            self.items.cell_methods = [cm.change_axes(axis_map) for cm in cell_methods]
            self.Items.cell_methods = [cm.remove_axes(del_axes) for cm in cell_methods]

        # Remove the axes
        for axis in axes:
            del self.Axes[axis]

        # Remove axes from unlimited dictionary
        unlimited = self._unlimited
        if unlimited:
            for axis in axes:
                unlimited.pop(axis, None)
            if not unlimited:
                self._unlimited = None

        return axes
    #--- End: def

    def remove_axis(self, axes=None, size=None, **kwargs):
        '''

Remove and return a unique axis from the field.

The axis may be selected with the keyword arguments. If no unique axis
can be found then no axis is removed and `None` is returned.

If the axis has size greater than 1 then it is not possible to remove
it if it is spanned by the field's data array or any multidimensional
coordinate or cell measure object of the field.

.. seealso:: `axis`, `remove_axes`, `remove_item`, `remove_items`

:Parameters:

    {+axes, kwargs}

    {+size}

:Returns:

    out: `str`
        The identifier of the removed axis, or `None` if there
        isn't one.

:Examples:

'''      
        axis = self.axis(axes, key=True, **kwargs)
        if axis is None:
            return

        return self.remove_axes(axis).pop()
    #--- End: def

#--- End: class

class Items(dict):
    '''
Keys are item identifiers, values are item objects.
    '''
    # Mapping of role name to single-character id (DO NOT CHANGE)
    _role_name = {
        'f': 'field ancillary',
        'a': 'auxiliary coordinate',
        'c': 'domain ancillary',
        'd': 'dimension coordinate',
        'm': 'cell measure',
        'r': 'coordinate reference',
    }

    def __init__(self, Axes=None):
        '''
'''
        self.f = set()  # Field ancillary identifiers,      e.g. 'fav0'
        self.a = set()  # Auxiliary coordinate identifiers, e.g. 'aux0'
        self.c = set()  # Domain ancillary identifiers,     e.g. 'cct0'
        self.d = set()  # Dimension coordinate identifiers, e.g. 'dim0'
        self.m = set()  # Cell measures identifier,         e.g. 'msr0'
        self.r = set()  # Coordinate reference identifiers, e.g. 'ref0'

        # Map of item identifiers to their roles. For example,
        # self._role['aux2'] = 'a'
        self._role = {}

        # The axes identifiers for each item. For example,
        # self._role['aux2'] = ['dim1, 'dim0']
        self._axes = {}

        self.cell_methods = []
        
        # Domain axes
        # 
        # For example: self.Axes = {'dim1': DomainAxis(20)}
        self.Axes = {} #Axes
        
    #--- End: def

#    def __delitem__(self, key):
#        del self._items[key]
#
#    def __getitem__(self, key):
#        return self._items[key]
#        
#    def __iter__(self):
#        return self._items.iteritems()
#
#    def __setitem__(self, key, value):
#        self._items[key] = value
#
#    # ----------------------------------------------------------------
#    # Dictionary methods
#    # ----------------------------------------------------------------
#    def get(self, k, *d):
#        return self._items.get(k, *d)
#
#    def items(self):
#        return self._items.items()
#        
#    def iteritems(self):
#        return self._items.iteritems()
#
#    def itervalues(self):
#        return self._items.itervalues()
#        
#    def pop(self, k, *d):
#        return self._items.pop(k, *d)
#        
#    def values(self):
#        return self._items.values()
        
    def __call__(self, description=None, role=None, axes=None,
                 axes_all=None, axes_subset=None, axes_superset=None,
                 ndim=None, match_and=True, exact=False,
                 inverse=False, copy=False):#, _restrict_inverse=False):

        '''Return items which span domain axes.

The set of all items comprises:

  * Dimension coordinate objects
  * Auxiliary coordinate objects
  * Cell measure objects
  * Coordinate reference objects
  * Coordinate conversion terms
  * Ancillary variable objects

The output is a dictionary whose key/value pairs are item identifiers
with corresponding values of items of the field.

{+item_selection}

{+items_criteria}

.. seealso:: `auxs`, `axes`, `measures`, `coords`, `dims`, `item`, `match`
             `remove_items`, `refs`

:Examples 1:

Select all items whose identities (as returned by their `!identity`
methods) start "height":

>>> i('height')

Select all items which span only one axis:

>>> i(ndim=1)

Select all cell measure objects:

>>> i(role='m')

Select all items which span the "time" axis:

>>> i(axes='time')

Select all CF latitude coordinate objects:

>>> i('Y')

Select all multidimensional dimension and auxiliary coordinate objects
which span at least the "time" and/or "height" axes and whose long
names contain the string "qwerty":

>>> i('long_name:.*qwerty', 
...         role='da',
...         axes=['time', 'height'],
...         ndim=cf.ge(2))

:Parameters:

    {+description}

          *Example:* 

            >>> x = i(['aux1',
            ...             'time',
            ...             {'units': 'degreeN', 'long_name': 'foo'}])
            >>> y = {}
            >>> for items in ['aux1', 'time', {'units': 'degreeN', 'long_name': 'foo'}]:
            ...     y.update(i(items))
            ...
            >>> set(x) == set(y)
            True

    role: (sequence of) `str`, optional
        Select items of the given roles. Valid roles are:
    
        =======  ============================
        role     Items selected
        =======  ============================
        ``'d'``  Dimension coordinate objects
        ``'a'``  Auxiliary coordinate objects
        ``'m'``  Cell measure objects
        ``'c'``  Domain ancillary objects
        ``'f'``  Field ancillary objects
        ``'r'``  Coordinate reference objects
        =======  ============================
    
        Multiple roles may be specified by a sequence of role
        identifiers.
    
          *Example:*
            Selecting auxiliary coordinate and cell measure objects
            may be done with any of the following values of *role*:
            ``'am'``, ``'ma'``, ``('a', 'm')``, ``['m', 'a']``,
            ``set(['a', 'm'])``, etc.
 
        By default all roles are considered, i.e. by default
        ``role=('d', 'a', 'm', 'f', 'c', 'r')``.
    
    {+axes}

    {+axes_all}

    {+axes_subset}

    {+axes_superset}

    {+ndim}

    {+match_and}

    {+exact}

    {+inverse}

          *Example:*
            ``i(role='da', inverse=True)`` selects the same
            items as ``i(role='mr')``.

    copy: `bool`, optional
        If True then do not copy the returned items. By default the
        returned items are not copies.

:Returns:

    out: `dict`
        A dictionary whose keys are domain item identifiers with
        corresponding values of items. The dictionary may be empty.

:Examples:

        '''
        if role is None:
            pool = dict(self)
        else:
            pool = {}
            for r in role:
                for key in getattr(self, r):
                    pool[key] = self[key]
                    
        if inverse:
            master = pool.copy()            

        if (description is None and axes is None and axes_all is None and
            axes_subset is None and axes_superset is None and ndim is None):
            out = pool.copy()
        else:       
            out = {}

        if pool and axes is not None:
            # --------------------------------------------------------
            # Select items which span at least one of the given axes,
            # and possibly others.
            # --------------------------------------------------------
            axes_out = {}
            for key, value in pool.iteritems():
                if axes.intersection(self.axes(key)):
                    axes_out[key] = value

            if match_and:
                out = pool = axes_out
            else:                
                for key in axes_out:
                    out[key] = pool.pop(key)
        #--- End: if

        if pool and axes_subset is not None:
            # --------------------------------------------------------
            # Select items whose data array spans all of the specified
            # axes, taken in any order, and possibly others.
            # --------------------------------------------------------
            axes_out = {}
            for key, value in pool.iteritems():
                if axes_subset.issubset(self.axes(key)):
                    axes_out[key] = value                            

            if match_and:
                out = pool = axes_out
            else:                
                for key in axes_out:
                    out[key] = pool.pop(key)
        #--- End: if

        if pool and axes_superset is not None:
            # --------------------------------------------------------
            # Select items whose data array spans a subset of the
            # specified axes, taken in any order, and no others.
            # --------------------------------------------------------
            axes_out = {}
            for key, value in pool.iteritems():
                if axes_superset.issuperset(self.axes(key)):
                    axes_out[key] = value                            

            if match_and:
                out = pool = axes_out
            else:                
                for key in axes_out:
                    out[key] = pool.pop(key)
        #--- End: if

        if pool and axes_all is not None:
            # --------------------------------------------------------
            # Select items which span all of the given axes and no
            # others
            # --------------------------------------------------------
            axes_out = {}
            for key, value in pool.iteritems():
                if axes_all == set(self.axes(key)):
                    axes_out[key] = value                            

            if match_and:
                out = pool = axes_out
            else:                
                for key in axes_out:
                    out[key] = pool.pop(key)
        #--- End: if

        if pool and ndim is not None:
            # --------------------------------------------------------
            # Select items whose number of data array axes satisfies a
            # condition
            # --------------------------------------------------------
            ndim_out = {}
            for key, item in pool.iteritems():
                if ndim == len(self.axes(key)):
                    ndim_out[key] = item
            #--- End: for

            if match_and:                
                out = pool = ndim_out
            else:
                for key in ndim_out:
                    out[key] = pool.pop(key)
        #--- End: if

        if pool and description is not None:
            # --------------------------------------------------------
            # Select items whose properties satisfy conditions
            # --------------------------------------------------------
            items_out = {}

            if isinstance(description, (basestring, dict)):
                description = (description,)

            if description:
                pool2 = pool.copy()

                match = []
                for m in description:
                    if m.__hash__ and m in pool:
                        # m is an item identifier
                        items_out[m] = pool2.pop(m)
                    else:                    
                        match.append(m)
                #--- End: for

                if match and pool:                
                    for key, item in pool2.iteritems():
                        if item.match(match, exact=exact):
                            # This item matches the critieria
                            items_out[key] = item
                #--- End: if

                if match_and:                
                    out = pool = items_out
                else:
                    for key in items_out:
                        out[key] = pool.pop(key)
            #--- End: if
        #--- End: if

        if inverse:
            # --------------------------------------------------------
            # Select items other than those previously selected
            # --------------------------------------------------------
            for key in out:
                del master[key]
                                
            out = master
        #--- End: if

        if copy:
            # --------------------------------------------------------
            # Copy the items
            # --------------------------------------------------------
            out2 = {}
            for key, item in out.iteritems():
                out2[key] = item.copy()
                
            out = out2
        #--- End: if

        # ------------------------------------------------------------
        # Return the selected items
        # ------------------------------------------------------------
        return out
    #--- End: def

    def auxs(self):
        '''Auxiliary coordinate objects and their identifiers
        
:Returns:
        
    out: `dict`
          A dictionary of auxiliary coordinate objects keyed by their
          identifiers.

:Examples:

>>> i.auxs()
{'aux0': <CF AuxiliaryCorodinate: >}

        '''
        return dict([(key, self[key]) for key in self.a])

    def dims(self):
        '''Return dimension coordinate objects and their identifiers
        
:Returns:
        
    out: `dict`
          A dictionary of dimension coordinate objects keyed by their
          identifiers.

:Examples:

>>> i.dims()
{'dim0': <CF DimensionCoordinate: >}

        '''
        return dict([(key, self[key]) for key in self.d])
 
#    def direction(self, axis):
#        '''
#
#Return True if an axis is increasing, otherwise return False.
#
#An axis is considered to be increasing if its dimension coordinate
#values are increasing in index space or if it has no dimension
#coordinates.
#
#:Parameters:
#
#    axis: `str`
#        A domain axis identifier, such as ``'dim0'``.
#
#:Returns:
#
#    out: `bool`
#        Whether or not the axis is increasing.
#        
#:Examples:
#
#>>> i.direction('dim0')
#True
#>>> i.direction('dim2')
#False
#        '''
#        if axis not in self.d:
#            return 
#
#        return self[axis].direction()
#    #--- End: def
        
    def domain_ancs(self):
        '''Return domain ancillary objects and their identifiers

:Returns:
        
    out: `dict`
        A dictionary of domain ancillary objects keyed by their
        identifiers.

:Examples:

>>> i.domain_ancs()
{'cct0': <CF DomainAncillary: >}

        '''
        return dict([(key, self[key]) for key in self.c])
        
    def field_ancs(self):
        '''Return field ancillary objects and their identifiers
        
:Returns:
        
    out: `dict`
          A dictionary of field ancillary objects keyed by their
          identifiers.

:Examples:

>>> i.field_ancs()
{'fav0': <CF FieldAncillary: >}

        '''
        return dict([(key, self[key]) for key in self.f])

    def msrs(self):
        '''Return cell measure objects and their identifiers
        
:Returns:
        
    out: `dict`
          A dictionary of cell measure objects keyed by their
          identifiers.

:Examples:

>>> i.msrs()
{'msr0': <CF CellMeasures: >}

        '''        
        return dict([(key, self[key]) for key in self.m])
        
    def refs(self):
        '''Return coordinate reference objects and their identifiers
        
:Returns:
        
    out: `dict`
          A dictionary of coordinate reference objects keyed by their
          identifiers.

:Examples:

>>> i.refs()
{'ref0': <CF CoordinateReference: >}

        '''  
        return dict([(key, self[key]) for key in self.r])

    def all_axes(self):
        '''
        '''        
        out = []
        for item_axes  in self._axes.itervalues():
            out.extend(item_axes)

        return set(out)

    def axes(self, key=None, axes=None, default=None):
        '''
:Examples 1:

>>> i.axes()

:Parameters:

    key: `str`, optional

    axes: sequence of `str`, optional

    default:

:Returns:

    out: `dict` or `list` or `None`

:Examples 2:

i.axes()
{'aux0': ('dim1', 'dim0'),
 'aux1': ('dim0',),
 'aux2': ('dim0',),
 'aux3': ('dim0',),
 'aux4': ('dim0',),
 'aux5': ('dim0',)}
>>>i.axes(key='aux0')
('dim1', 'dim0')
>>> print i.axes(key='aux0', axes=['dim0', 'dim1'])
None
>>> i.axes(key='aux0')
('dim0', 'dim1')

'''
        if key is None:
            # Return all of the items' axes
            return self._axes.copy()

        if axes is None:
            if self.role(key) != 'r':                            
                # Not a coordinate reference
                return self._axes.get(key, default)
            else:
                # Is a coordinate reference
                r_axes = []
                ref = self.get(key, None)
                
                if ref is None:
                    return default

                _axes = self._axes
                for key in self(ref.coordinates | set(ref.ancillaries.values()),
                                exact=True):
                    r_axes.extend(_axes.get(key, ()))
                
                return set(r_axes)

        elif self.role(key) == 'r':
            raise ValueError("Can't set coordinate reference axes")
 
        # Still here? The set new item axes.
        self._axes[key] = tuple(axes)
    #--- End: def
    
    def axes_to_items(self):
        '''
:Examples:

>>> i.axes_to_items()
{
 ('dim1',): {
        'd': {'dim1': <>},
        'a': {},
        'm': {}
        'c': {}
        'f': {}
        }
 ('dim1', 'dim2',): {
        'd': {},
        'a': {'aux0': <>, 'aux1': <>},
        'm': {}
        'c': {}
        'f': {}
        }
}
'''
        axes = self._axes
        out = {}

        for item_axes in axes.values():
            out[item_axes] = {}
                
        for role in ('d', 'a', 'm', 'c', 'f'):
            for item_axes, items in out.iteritems():
                items_role = {}
                for key in getattr(self, role):
                    if axes[key] == item_axes:
                        items_role[key] = self[key]
                items[role] = items_role
        return out
    #--- End: def

    def axis_name(self, axis, default=None):
        '''Return the canonical name for an axis.

:Parameters:

:Returns:

    out: `str`
        The canonical name for the axis.

:Examples:

        '''
        if default is None:
            default = 'axis%{}'.format(axis)

        if axis in self.d:
            # Get the name from the dimension coordinate
            return self[axis].name(default=default)

        aux = self.item(role='a', axes_all=set((axis,)))
        if aux is not None:
            # Get the name from the unique 1-d auxiliary coordinate
            return aux.name(default=default)
        
        ncdim = self.Axes[axis].ncdim
        if ncdim is not None:
            # Get the name from netCDF dimension name            
            return 'ncdim%{0}'.format(ncdim)
        else:
            # Get the name from the axis identifier
            return 'axis%{0}'.format(axis)
    #--- End: def

    def axis_identity(self, axis):
        '''Return the canonical name for an axis.

:Parameters:

:Returns:

    out: `str`
        The canonical name for the axis.

:Examples:

        '''      
        if axis in self.d:
            # Get the name from the dimension coordinate
            dim = self[axis]            
            identity = dim.identity()
            if identity is None:
                for ctype in ('T', 'X', 'Y', 'Z'):
                    if getattr(dim, ctype, False):
                        identity = ctype
                        break
            #--- End: if
            if identity is None:
                identity = 'axis%{0}'.format(axis)
        else:
            aux = self.item(role='a', axes_all=set((axis,)))
            if aux is not None:
                # Get the name from the unique 1-d auxiliary coordinate
                identity = aux.identity(default='axis%{0}'.format(axis))
            else:
                identity = 'axis%{0}'.format(axis)

        return identity
    #--- End: def

    def copy(self, shallow=False):
        '''

Return a deep or shallow copy.

``i.copy()`` is equivalent to ``copy.deepcopy(i)``.

``i.copy(shallow=True)`` is equivalent to ``copy.copy(i)``.

:Parameters:

    shallow: `bool`, optional

:Returns:

    out: `Items`
        The copy.

:Examples:

>>> i = j.copy()

'''
        X = type(self)
        new = X.__new__(X)

        # Copy the domain axes
        new.Axes = {}
        for key, axis in self.Axes.iteritems():
            new.Axes[key] = axis.copy()

        # Copy the actual items (e.g. dimension coordinates, field
        # ancillaries, etc.)
        if shallow:
            for key, value in self.iteritems():
                new[key] = value
        else:
            for key, value in self.iteritems():
                new[key] = value.copy()

        # Copy the identifiers
        new.f = self.f.copy()     # Field ancillaries
        new.a = self.a.copy()     # Auxiliary coordinates
        new.c = self.c.copy()     # Domain ancillaries
        new.d = self.d.copy()     # Dimension coordinates
        new.m = self.m.copy()     # Cell measures
        new.r = self.r.copy()     # Coordinate references

        # Copy the roles
        new._role = self._role.copy()

        new.cell_methods = [cm.copy() for cm in self.cell_methods]

        # Copy item axes (this is OK because it is a dictionary of
        # tuples).
        new._axes = self._axes.copy()

        return new
    #--- End: def

    def _Axes_equals(self, other, traceback=False):
        '''
        '''
        Axes = self.Axes
        if Axes is other:
            return True
        
        # Check that each instance is the same type
        if type(Axes) != type(other):
            if traceback:
                print("{0}: Different types: {1}, {2}".format(
                    self.__class__.__name__, Axes.__class__.__name__,
                    other.__class__.__name__))
            return False
        #--- End: if

        Axes_sizes  = [d.size for d in Axes.values()]
        other_sizes = [d.size for d in other.values()]
        
        if sorted(Axes_sizes) != sorted(other_sizes):
            # There is not a 1-1 correspondence between axis sizes
            if traceback:
                print("{0}: Different domain axis sizes: {1} != {2}".format(
                    self.__class__.__name__,
                    sorted(Axes.values()),
                    sorted(other.values())))
            return False
        #--- End: if

        # ------------------------------------------------------------
        # Still here? Then the two collections of domain axis objects
        # are equal
        # ------------------------------------------------------------
        return True
    #-- End: def
    
    def equals(self, other, rtol=None, atol=None,
               ignore_data_type=False, ignore_fill_value=False,
               traceback=False, _equivalent=False, ignore=()):
        '''
        
        '''
        if self is other:
            return True
        
        # Check that each instance is the same type
        if type(self) != type(other):
            if traceback:
                print("{0}: Different object types: {0}, {1}".format(
                    self.__class__.__name__, other.__class__.__name__))
            return False

        if not self._Axes_equals(other.Axes, traceback=traceback):
            if traceback:
                print("{0}: Different domain axes: {1}, {2}".format(
                    self.__class__.__name__, self.Axes, other.Axes))
            return False
        
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        # ------------------------------------------------------------
        # 
        # ------------------------------------------------------------
        axes0_to_axes1 = {}

        key1_to_key0 = {}

        axes_to_items0 = self.axes_to_items()
        axes_to_items1 = other.axes_to_items()
#        print
#        for key, value in axes_to_items0.iteritems():
#            print key
#            print value
#        print 
#        print
#        for key, value in axes_to_items1.iteritems():
#            print key
#            print value
#        print
        
        for axes0, items0 in axes_to_items0.iteritems():
            matched_all_items_with_these_axes = False

#            directions0 = [self.direction(axis0) for axis0 in axes0]

            len_axes0 = len(axes0) 
            for axes1, items1 in axes_to_items1.items():
                matched_roles = False

                if len_axes0 != len(axes1):
                    # axes1 and axes0 contain differents number of
                    # axes.
                    continue
            
#                directions1 = [other.direction(axis1) for axis1 in axes1]        

                for role in ('d', 'a', 'm', 'f', 'c'):
                    matched_role = False

                    role_items0 = items0[role]
                    role_items1 = items1[role]

                    if len(role_items0) != len(role_items1):
                        # There are the different numbers of items
                        # with this role
                        matched_all_items_with_these_axes = False
                        break

                    # Check that there are matching pairs of equal
                    # items
                    for key0, item0 in role_items0.iteritems():
                        matched_item = False
                        for key1, item1 in role_items1.items():
                            if _equivalent:
#                                # Flip item1 axes, if necessary
#                                flip = [i
#                                        for i, (d0, d1) in enumerate(zip(directions0, directions1))
#                                        if d0 != d1]
#                                if flip:
#                                    item1 = item1.flip(flip)
#
#                                # Transpose item1 axes, if necessary
#                                
#
#                                item0_compare = item0.equivalent
                                pass
                            else:
                                item0_compare = item0.equals
                               
                            if item0_compare(item1, rtol=rtol,
                                             atol=atol,
                                             ignore_data_type=ignore_data_type,
                                             ignore_fill_value=ignore_fill_value,
                                             ignore=ignore,
                                             traceback=False):
                                del role_items1[key1]
                                key1_to_key0[key1] = key0
                                matched_item = True
                                break
                        #--- End: for

                        if not matched_item:
                            break
                    #--- End: for

                    if role_items1:
                        break

                    del items1[role]
                #--- End: for

                matched_all_items_with_these_axes = not items1

                if matched_all_items_with_these_axes:
                    del axes_to_items1[axes1]
                    break
            #--- End: for

            # Map item axes in the two instances
            axes0_to_axes1[axes0] = axes1

            if not matched_all_items_with_these_axes:
                if traceback:
                    names = [self.axis_name(axis0) for axis0 in axes0]
                    print("Can't match items spanning axes {0}".format(names))
                return False
        #--- End: for

        axis0_to_axis1 = {}
        axis1_to_axis0 = {}
        for axes0, axes1 in axes0_to_axes1.iteritems():
            for axis0, axis1 in zip(axes0, axes1):
                if axis0 in axis0_to_axis1 and axis1 != axis0_to_axis1[axis0]:
                    if traceback:
                        print(
"Field: Ambiguous axis mapping ({} -> {} and {})".format(
    self.axis_name(axes0), other.axis_name(axis1),
    other.axis_name(axis0_to_axis1[axis0])))
                    return False
                elif axis1 in axis1_to_axis0 and axis0 != axis1_to_axis0[axis1]:
                    if traceback:
                        print(
"Field: Ambiguous axis mapping ({} -> {} and {})".format(
    self.axis_name(axis0), self.axis_name(axis1_to_axis0[axis0]),
    other.axis_name(axes1)))
                    return False

                axis0_to_axis1[axis0] = axis1
                axis1_to_axis0[axis1] = axis0
        #--- End: for     

        #-------------------------------------------------------------
        # Cell methods
        #-------------------------------------------------------------
        if len(self.cell_methods) != len(other.cell_methods):
            if traceback:
                print(
"Field: Different cell methods: {0!r}, {1!r}".format(
    self.cell_methods, other.cell_methods))
            return False

        for cm0, cm1 in zip(self.cell_methods, other.cell_methods):
            # Check that there are the same number of axes
            axes0 = cm0.axes
            axes1 = list(cm1.axes)
            if len(cm0.axes) != len(axes1):
                if traceback:
                    print (
"Field: Different cell methods (mismatched axes): {0!r}, {1!r}".format(
    self.cell_methods, other.cell_methods))
                return False

            argsort = []
            for axis0 in axes0:
                if axis0 is None:
                    return False
                for axis1 in axes1:
                    if axis0 in axis0_to_axis1 and axis1 in axis1_to_axis0:
                        if axis1 == axis0_to_axis1[axis0]:
                            axes1.remove(axis1)
                            argsort.append(cm1.axes.index(axis1))
                            break
                    elif axis0 in axis0_to_axis1 or axis1 in axis1_to_axis0:
                        if traceback:
                            print (
"Field: Different cell methods (mismatched axes): {0!r}, {1!r}".format(
    self.cell_methods, other.cell_methods))

                        return False
                    elif axis0 == axis1:
                        # Assume that the axes are standard names
                        axes1.remove(axis1)
                        argsort.append(cm1.axes.index(axis1))
                    elif axis1 is None:
                        if traceback:
                            print (
"Field: Different cell methods (undefined axis): {0!r}, {1!r}".format(
    self.cell_methods, other.cell_methods))
                        return False
            #--- End: for

            if len(cm1.axes) != len(argsort):
                if traceback:
                    print (
"Field: Different cell methods: {0!r}, {1!r}".format(
    self.cell_methods, other.cell_methods))
                return False

            cm1 = cm1.copy()
            cm1.sort(argsort=argsort)
            cm1.axes = axes0

            if not cm0.equals(cm1, atol=atol, rtol=rtol,
                              ignore_data_type=ignore_data_type,
                              ignore_fill_value=ignore_fill_value,
                              traceback=traceback):
                if traceback:
                    print (
                        "Field: Different cell methods: {0!r}, {1!r}".format(
                            self.cell_methods, other.cell_methods))
                return False                
        #--- End: for

        # ------------------------------------------------------------
        # Coordinate references
        # ------------------------------------------------------------
        refs1 = other.refs()
        for ref0 in self.refs().values():
            found_match = False
            for key1, ref1 in refs1.items():
                if not ref0.equals(ref1, rtol=rtol, atol=atol,
                                   ignore_data_type=ignore_data_type,
                                   ignore_fill_value=ignore_fill_value, traceback=False):
                    continue

                # Coordinates
                coordinates0 = set(
                    [self.key(value, role='da', exact=True, default=value)
                     for value in ref0.coordinates])
                coordinates1 = set(
                    [key1_to_key0.get(other.key(value, role='da', exact=True), value)
                     for value in ref1.coordinates])
                if coordinates0 != coordinates1:
                    continue

                # Domain ancillary terms
                terms0 = dict(
                    [(term,
                      self.key(value, role='c', exact=True, default=value))
                     for term, value in ref0.ancillaries.iteritems()])
                terms1 = dict(
                    [(term,
                      key1_to_key0.get(other.key(value, role='c', exact=True), value))
                     for term, value in ref1.ancillaries.iteritems()])
                if terms0 != terms1:
                    continue

                found_match = True
                del refs1[key1]                                       
                break
            #--- End: for

            if not found_match:
                if traceback:
                    print("Field: No match for {0!r})".format(ref0))
                return False
        #--- End: for

        # ------------------------------------------------------------
        # Still here? Then the two Items are equal
        # ------------------------------------------------------------
        return True
    #--- End: def

    def analyse_axis(self, axis):
        '''
        '''
        if axis in self.d:
            # This axis of the domain has a dimension coordinate
            dim = self[axis]

            identity = dim.identity()
            if identity is None:
                # Dimension coordinate has no identity, but it may
                # have a recognised axis.
                for ctype in ('T', 'X', 'Y', 'Z'):
                    if getattr(dim, ctype, False):
                        identity = ctype
                        break
            #--- End: if

            if identity is not None and dim.hasdata:
                axis_to_id[axis]      = identity
                id_to_axis[identity]  = axis
                axis_to_coord[axis]   = key
                id_to_coord[identity] = key
                axis_to_dim[axis]     = key
                id_to_dim[identity]   = key
        else:
            auxs = self(role='a', ndim=1)
            if len(auxs) == 1:                
                # This axis of the domain does not have a
                # dimension coordinate but it does have exactly
                # one 1-d auxiliary coordinate, so that will do.
                key, aux = auxs.popitem()
                identity = aux.identity()
                if identity is None:
                    # Auxiliary coordinate has no identity, but it may
                    # have a recognised axis.
                    for ctype in ('T', 'X', 'Y', 'Z'):
                        if getattr(dim, ctype, False):
                            identity = ctype
                            break
                #--- End: if

                if identity is not None and aux.hasdata:                
                    axis_to_id[axis]      = identity
                    id_to_axis[identity]  = axis
                    axis_to_coord[axis]   = key
                    id_to_coord[identity] = key
                    axis_to_aux[axis]     = key
                    id_to_aux[identity]   = key
    #--- End: def

    def insert_field_anc(self, item, key, axes, copy=True):
        if copy:
            item = item.copy()
        self[key] = item
        self._axes[key] = tuple(axes)
        self.f.add(key)
        self._role[key] = 'f'
        
    def insert_aux(self, item, key, axes, copy=True):
        '''
        '''
        if copy:
            item = item.copy()
        self[key] = item
        self._axes[key] = tuple(axes)
        self.a.add(key)
        self._role[key] = 'a'

    def insert_domain_anc(self, item, key, axes, copy=True):
        '''
        '''
        if copy:
            item = item.copy()
        self[key] = item
        self._axes[key] = tuple(axes)
        self.c.add(key)
        self._role[key] = 'c'

    def insert_dim(self, item, key, axes, copy=True):
        '''
        '''
        if copy:
            item = item.copy()
        self[key] = item
        self._axes[key] = tuple(axes)
        self.d.add(key)
        self._role[key] = 'd'

    def insert_measure(self, item, key, axes, copy=True):
        '''
        '''
        if copy:
            item = item.copy()
        self[key] = item
        self._axes[key] = tuple(axes)
        self.m.add(key)
        self._role[key] = 'm'

    def insert_ref(self, item, key, copy=True):
        if copy:
            item = item.copy()
        self[key] = item
        self.r.add(key)
        self._role[key] = 'r'

    def insert_item(self, role, item, key, copy=True):
        if copy:
            item = item.copy()
        self[key] = item
        getattr(self, role).add(key)
        self._role[key] = role

    def item(self, description=None, key=False, default=None, **kwargs):
        '''
'''    
        if key:
            return self.key(description=description, default=default, **kwargs)

        d = self(description, **kwargs)
        if not d:
            return default

        items = d.popitem()

        return default if d else items[1]
    #--- End: def

    def key(self, description=None, default=None, **kwargs):
        '''
'''    
        d = self(description, **kwargs)
        if not d:
            return default

        items = d.popitem()

        return default if d else items[0]
    #--- End: def

    def key_item(self, description=None, default=(None, None), **kwargs):
        '''
'''    
        d = self(description, **kwargs)
        if not d:
            return default

        items = d.popitem()

        return default if d else items
    #--- End: def

    def remove_item(self, key):
        '''
'''
        self._axes.pop(key, None)
        getattr(self, self._role.pop(key)).discard(key)
        return self.pop(key)
    #--- End: def

    def role(self, key):
        return self._role[key]
    #--- End: def

    def aaa(self, other, atol=None, rtol=None, _equivalent=False):
        '''
        '''
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        # ------------------------------------------------------------
        # 
        # ------------------------------------------------------------
        axes0_to_axes1 = {}

        key1_to_key0 = {}

        axes_to_items0 = self.axes_to_items()
        axes_to_items1 = other.axes_to_items()
        
        for axes0, items0 in axes_to_items0.iteritems():
            matched_all_items_with_these_axes = False

            len_axes0 = len(axes0) 
            for axes1, items1 in axes_to_items1.items():
                matched_roles = False

                if len_axes0 != len(axes1):
                    # axes1 and axes0 contain differents number of
                    # axes.
                    continue
            
                for role in ('d', 'a', 'm', 'f', 'c'):
                    matched_role = False

                    role_items0 = items0[role]
                    role_items1 = items1[role]

                    if len(role_items0) != len(role_items1):
                        # There are the different numbers of items
                        # with this role
                        matched_all_items_with_these_axes = False
                        break

                    # Check that there are matching pairs of equal
                    # items
                    for key0, item0 in role_items0.iteritems():
                        matched_item = False
                        for key1, item1 in role_items1.items():
                            if _equivalent:
                                pass
#                                # Flip item1 axes, if necessary
#                                flip = [i
#                                        for i, (d0, d1) in enumerate(zip(directions0, directions1))
#                                        if d0 != d1]
#                                if flip:
#                                    item1 = item1.flip(flip)
#
#                                # Transpose item1 axes, if necessary
#                                
#
#                                item0_compare = item0.equivalent
                            else:
                                item0_compare = item0.equals
                               
                            if item0_compare(item1, rtol=rtol,
                                             atol=atol,
                                             ignore_data_type=ignore_data_type,
                                             ignore_fill_value=ignore_fill_value,
                                             ignore=ignore,
                                             traceback=False):
                                del role_items1[key1]
                                key1_to_key0[key1] = key0
                                matched_item = True
                                break
                        #--- End: for

                        if not matched_item:
                            break
                    #--- End: for

                    if role_items1:
                        break

                    del items1[role]
                #--- End: for

                matched_all_items_with_these_axes = not items1

                if matched_all_items_with_these_axes:
                    del axes_to_items1[axes1]
                    break
            #--- End: for

            # Map item axes in the two instances
            axes0_to_axes1[axes0] = axes1

            if not matched_all_items_with_these_axes:
                if traceback:
                    names = [self.axis_name(axis0) for axis0 in axes0]
                    print("Can't match items spanning axes {0}".format(names))
                return False
        #--- End: for

        axis0_to_axis1 = {}
        axis1_to_axis0 = {}
        for axes0, axes1 in axes0_to_axes1.iteritems():
            for axis0, axis1 in zip(axes0, axes1):
                if axis0 in axis0_to_axis1 and axis1 != axis0_to_axis1[axis0]:
                    if traceback:
                        print(
"Field: Ambiguous axis mapping ({} -> {} and {})".format(
    self.axis_name(axes0), other.axis_name(axis1),
    other.axis_name(axis0_to_axis1[axis0])))
                    return False
                elif axis1 in axis1_to_axis0 and axis0 != axis1_to_axis0[axis1]:
                    if traceback:
                        print(
"Field: Ambiguous axis mapping ({} -> {} and {})".format(
    self.axis_name(axis0), self.axis_name(axis1_to_axis0[axis0]),
    other.axis_name(axes1)))
                    return False

                axis0_to_axis1[axis0] = axis1
                axis1_to_axis0[axis1] = axis0
        #--- End: for     

#--- End: class
