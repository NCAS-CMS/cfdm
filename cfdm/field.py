from __future__ import print_function
from builtins import (str, super, zip)

import logging

from . import mixin
from . import core
from . import Constructs
from . import Domain
from . import Count
from . import Index
from . import List

from .constants import masked as cfdm_masked

from .data import Data
from .data import RaggedContiguousArray
from .data import RaggedIndexedArray
from .data import RaggedIndexedContiguousArray
from .data import GatheredArray

from .decorators import (
    _inplace_enabled,
    _inplace_enabled_define_and_cleanup,
    _manage_log_level_via_verbosity,
)


logger = logging.getLogger(__name__)


class Field(mixin.NetCDFVariable,
            mixin.NetCDFGeometry,
            mixin.NetCDFGlobalAttributes,
            mixin.ConstructAccess,
            mixin.PropertiesData,
            core.Field):
    '''A field construct of the CF data model.

    The field construct is central to the CF data model, and includes
    all the other constructs. A field corresponds to a CF-netCDF data
    variable with all of its metadata. All CF-netCDF elements are
    mapped to a field construct or some element of the CF field
    construct. The field construct contains all the data and metadata
    which can be extracted from the file using the CF conventions.

    The field construct consists of a data array and the definition of
    its domain (that describes the locations of each cell of the data
    array), field ancillary constructs containing metadata defined
    over the same domain, and cell method constructs to describe how
    the cell values represent the variation of the physical quantity
    within the cells of the domain. The domain is defined collectively
    by the following constructs of the CF data model: domain axis,
    dimension coordinate, auxiliary coordinate, cell measure,
    coordinate reference and domain ancillary constructs.

    The field construct also has optional properties to describe
    aspects of the data that are independent of the domain. These
    correspond to some netCDF attributes of variables (e.g. units,
    long_name and standard_name), and some netCDF global file
    attributes (e.g. history and institution).

    **NetCDF interface**

    The netCDF variable name of the construct may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_del_variable` and
    `nc_has_variable` methods.

    .. versionadded:: 1.7.0

    '''
    def __new__(cls, *args, **kwargs):
        '''This must be overridden in subclasses.

        '''
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        instance._Domain     = Domain
        instance._Data       = Data
        instance._RaggedContiguousArray        = RaggedContiguousArray
        instance._RaggedIndexedArray           = RaggedIndexedArray
        instance._RaggedIndexedContiguousArray = RaggedIndexedContiguousArray
        instance._GatheredArray                = GatheredArray
        instance._Count = Count
        instance._Index = Index
        instance._List  = List
        return instance

    def __init__(self, properties=None, source=None, copy=True,
                 _use_data=True):
        '''**Initialization**

    :Parameters:

        properties: `dict`, optional
            Set descriptive properties. The dictionary keys are
            property names, with corresponding values. Ignored if the
            *source* parameter is set.

            Properties may also be set after initialisation with the
            `set_properties` and `set_property` methods.

            *Parameter example:*
              ``properties={'standard_name': 'air_temperature'}``

        source: optional
            Initialize the properties, data and metadata constructs
            from those of *source*.

        copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization. By default arguments are deep copied.

        '''
        # Initialize the new field with attributes and CF properties
        core.Field.__init__(self, properties=properties,
                            source=source, copy=copy,
                            _use_data=_use_data)

        self._initialise_netcdf(source)

    def __repr__(self):
        '''Called by the `repr` built-in function.

    x.__repr__() <==> repr(x)

    .. versionadded:: 1.7.0

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__,
                                   self._one_line_description())

    def __str__(self):
        '''Called by the `str` built-in function.

    x.__str__() <==> str(x)

    .. versionadded:: 1.7.0

        '''
        title = "Field: {0}".format(self.identity(''))

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
            units += ' {0}'.format(calendar)

        # Axes
        data_axes = self.get_data_axes(default=())
        non_spanning_axes = set(self.domain_axes).difference(data_axes)

        axis_names = self._unique_domain_axis_identities()

        # Data
        string.append(
            'Data            : {0}'.format(
                self._one_line_description(axis_names)))

        # Cell methods
        cell_methods = self.cell_methods
        if cell_methods:
            x = []
            for cm in cell_methods.values():
                cm = cm.copy()
                cm.set_axes(tuple([axis_names.get(axis, axis)
                                   for axis in cm.get_axes(())]))
                x.append(str(cm))

            c = ' '.join(x)

            string.append('Cell methods    : {0}'.format(c))

        def _print_item(self, key, variable, axes):
            '''Private function called by __str__

            '''
            # Field ancillary
            x = [variable.identity(default=key)]

            if variable.has_data():
                shape = [axis_names[axis] for axis in axes]
                shape = str(tuple(shape)).replace("'", "")
                shape = shape.replace(',)', ')')
                x.append(shape)
            elif (hasattr(variable, 'nc_get_external')
                  and variable.nc_get_external()):
                ncvar = variable.nc_get_variable(None)
                if ncvar is not None:
                    x.append(' (external variable: ncvar%{})'.format(ncvar))
                else:
                    x.append(' (external variable)')
            # --- End: if

            if variable.has_data():
                x.append(' = {0}'.format(variable.get_data()))

            return ''.join(x)
        # --- End: def

        # Field ancillary variables
        x = [_print_item(self, key, anc, self.constructs.data_axes()[key])
             for key, anc in sorted(self.field_ancillaries.items())]
        if x:
            string.append('Field ancils    : {}'.format(
                '\n                : '.join(x)))


        string.append(str(self.domain))

        return '\n'.join(string)

    def __getitem__(self, indices):
        '''Return a subspace of the field defined by indices.

    f.__getitem__(indices) <==> f[indices]

    The new subspace contains the same properties and similar metadata
    constructs to the original field, but the latter are also
    subspaced when they span domain axis constructs that have been
    changed.

    Indexing follows rules that are very similar to the numpy indexing
    rules, the only differences being:

    * An integer index i takes the i-th element but does not reduce
      the rank by one.

    * When two or more dimensions' indices are sequences of integers
      then these indices work independently along each dimension
      (similar to the way vector subscripts work in Fortran). This is
      the same behaviour as indexing on a Variable object of the
      netCDF4 package.

    .. versionadded:: 1.7.0

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

        new = self.copy() #data=False)

        data_axes = self.get_data_axes()

        # Open any files that contained the original data (this not
        # necessary, is an optimisation)

        # ------------------------------------------------------------
        # Subspace the field's data
        # ------------------------------------------------------------
        new_data = data[tuple(indices)]

        # Replace domain axes
        domain_axes = new.domain_axes
        for key, size in zip(data_axes, new_data.shape):
            domain_axis = domain_axes[key]
            domain_axis.set_size(size)
            new.set_construct(domain_axis, key=key)

        # ------------------------------------------------------------
        # Subspace other constructs that contain arrays
        # ------------------------------------------------------------
        self_constructs = self.constructs
        new_constructs_data_axes = new.constructs.data_axes()

        if data_axes:
            for key, construct in new.constructs.filter_by_axis(
                    'or', *data_axes).items():
                needs_slicing = False
                dice = []
                for axis in new_constructs_data_axes[key]:
                    if axis in data_axes:
                        needs_slicing = True
                        dice.append(indices[data_axes.index(axis)])
                    else:
                        dice.append(slice(None))
                # --- End: for

                if needs_slicing:
                    new.set_construct(construct[tuple(dice)],
                                      key=key, copy=False)
        # --- End: if

        new.set_data(new_data, copy=False)

        return new

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _one_line_description(self, axis_names_sizes=None):
        '''
        '''
        if axis_names_sizes is None:
            axis_names_sizes = self._unique_domain_axis_identities()

        x = [axis_names_sizes[axis] for axis in self.get_data_axes(default=())]
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

        return "{0}{1}{2}".format(self.identity(''), axis_names, units)

    def _set_dataset_compliance(self, value):
        '''Set the report of problems encountered whilst reading the field
    construct from a dataset.

    .. versionadded:: 1.7.0

    .. seealso:: `dataset_compliance`

    :Parameters:

        value:
            The value of the data_compliance component

    :Returns:

        `None`

    **Examples:**

        '''
        self._set_component('dataset_compliance', value, copy=True)

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def field_ancillaries(self):
        '''Return field ancillary constructs.

    .. versionadded:: 1.7.0

    .. seealso:: `constructs`, `get_construct`

    :Parameters:

        copy: `bool`, optional
            If True then return copies of the constructs. By default
            the constructs are not copied.

    :Returns:

        `Constructs`
            The field ancillary constructs and their construct keys.

    **Examples:**

    >>> print(f.field_ancillaries)
    Constructs:
    {}

    >>> print(f.field_ancillaries)
    Constructs:
    {'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}

    >>> print(f.field_ancillaries('specific_humuidity standard_error'))
    Constructs:
    {'fieldancillary0': <FieldAncillary: specific_humidity standard_error(10, 9) K>}

        '''
        return self.constructs.filter_by_type('field_ancillary')

    @property
    def cell_methods(self):
        '''Return cell method constructs.

    The cell methods are not returned in the order in which they were
    applied. To achieve this use the `~Constructs.ordered` of the
    returned `Constructs` instance.

    .. versionadded:: 1.7.0

    .. seealso:: `constructs`, `get_construct`, `set_construct`

    :Parameters:

        copy: `bool`, optional
            If True then return copies of the constructs. By default
            the constructs are not copied.

    :Returns:

        `Constructs`
            The cell method constructs and their construct keys.

    **Examples:**

    >>> f.cell_methods
    Constructs:
    {}

    >>> f.cell_methods
    Constructs:
    {'cellmethod1': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
     'cellmethod0': <CellMethod: domainaxis3: maximum>}

    >>> f.cell_methods.ordered()
    OrderedDict([('cellmethod0', <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>),
                 ('cellmethod1', <CellMethod: domainaxis3: maximum>)])

        '''
        return self.constructs.filter_by_type('cell_method')

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def apply_masking(self, inplace=False):
        '''Apply masking as defined by the CF conventions.

    Masking is applied to the field construct data as well as metadata
    constructs' data.

    Masking is applied according to any of the following criteria that
    are applicable:

    * where data elements are equal to the value of the
      ``missing_value`` property;

    * where data elements are equal to the value of the ``_FillValue``
      property;

    * where data elements are strictly less than the value of the
      ``valid_min`` property;

    * where data elements are strictly greater than the value of the
      ``valid_max`` property;

    * where data elements are within the inclusive range specified by
      the two values of ``valid_range`` property.

    If any of the above properties have not been set the no masking is
    applied for that method.

    Elements that are already masked remain so.

    .. note:: If using the `apply_masking` method on a construct that
              has been read from a dataset with the ``mask=False``
              parameter to the `read` function, then the mask defined
              in the dataset can only be recreated if the
              ``missing_value``, ``_FillValue``, ``valid_min``,
              ``valid_max``, and ``valid_range`` properties have not
              been updated.

    .. versionadded:: 1.8.3

    .. seealso:: `Data.apply_masking`, `read`, `write`

    :Parameters:

        inplace: `bool`, optional
            If True then do the operation in-place and return `None`.

    :Returns:

        `Field` or `None`
            A new field construct with masked values, or `None` if the
            operation was in-place.

    **Examples:**

                TODO DCH

        '''
        if inplace:
            f = self
        else:
            f = self.copy()

        # Apply masking to the field construct
        super(Field, f).apply_masking(inplace=True)

        # Apply masking to the metadata constructs
        for c in f.constructs.filter_by_data().values():
            c.apply_masking(inplace=True)

        if inplace:
            f = None
        return f

    def climatological_time_axes(self):
        '''TODO

    .. versionadded:: 1.7.0

    :Returns:

        `list`
            TODO

    **Examples:**

    TODO

        '''
        out = []

        domain_axes = self.domain_axes

        for key, cm in self.cell_methods.ordered().items():
            qualifiers = cm.qualifiers()
            if not ('within' in qualifiers or 'over' in qualifiers):
                continue

            axes = cm.get_axes(default=())
            if len(axes) != 1:
                continue

            axis = axes[0]
            if axis not in domain_axes:
                continue

            # Still here? Then this axis is a climatological time axis
            out.append((axis,))

        return out

    @_inplace_enabled
    def compress(self, method,axes=None, count_properties=None,
                 index_properties=None, list_properties=None,
                 inplace=False):
        '''Compress the field construct.

    Compression can save space by identifying and removing unwanted
    missing data. Such compression techniques store the data more
    efficiently and result in no precision loss.

    The field construct data is compressed, along with any applicable
    metadata constructs.

    Whether or not the field construct is compressed does not alter
    its functionality nor external appearance.

    A field that is already compressed will returned compressed by the
    chosen method.

    When writing a compressed field construct to a dataset space will
    be saved by the creation of compressed netCDF variables, along
    with the supplementary netCDF variables and attributes that are
    required for the encoding.

    The following type of compression are available (see the *method*
    parameter):

        * Ragged arrays for discrete sampling geometries (DSG). Three
          different types of ragged array representation are
          supported.

        ..

        * Compression by gathering.

    .. versionadded:: 1.7.11

    .. seealso:: `uncompress`

    :Parameters:

        method: `str`
            The compression method. One of:

            * ``'contiguous'``

              Contiguous ragged array representation for DSG "point",
              "timeSeries", "trajectory" or "profile" features.

              The field construct data must have exactly 2 dimensions
              for which the first (leftmost) dimension indexes each
              feature and the second (rightmost) dimension contains
              the elements for the features. Trailing missing data
              values in the second dimension are removed to created
              the compressed data.

            * ``'indexed'``

              Indexed ragged array representation for DSG "point",
              "timeSeries", "trajectory", or "profile" features.

              The field construct data must have exactly 2 dimensions
              for which the first (leftmost) dimension indexes each
              feature and the second (rightmost) dimension contains
              the elements for the features. Trailing missing data
              values in the second dimension are removed to created
              the compressed data.

            * ``'indexed_contiguous'``

              Indexed contiguous ragged array representation for DSG
              "timeSeriesProfile", or "trajectoryProfile" features.

              The field construct data must have exactly 3 dimensions
              for which the first (leftmost) dimension indexes each
              feature; the second (middle) dimension indexes each
              timeseries or trajectory; and the third (rightmost)
              dimension contains the elements for the timeseries or
              trajectories. Trailing missing data values in the third
              dimension are removed to created the compressed data.

            * ``'gathered'``

              Compression by gathering over any subset of the field
              construct data dimensions.

              *Not yet available.*

        count_properties: `dict`, optional
            Provide properties to the count variable for contiguous
            ragged array representation or indexed contiguous ragged
            array representation.

            *Parameter example:*
              ``count_properties={'long_name': 'number of timeseries'}``

        index_properties: `dict`, optional
            Provide properties to the index variable for indexed
            ragged array representation or indexed contiguous ragged
            array representation.

            *Parameter example:*
              ``index_properties={'long_name': 'station of profile'}``

        list_properties: `dict`, optional
            Provide properties to the list variable for compression by
            gathering.

            *Parameter example:*
              ``list_properties={'long_name': 'uncompression indices'}``

        inplace: `bool`, optional
            If True then do the operation in-place and return `None`.

    :Returns:

        `Field` or `None`
            The compressed field construct, or `None` if the operation
            was in-place.

    **Examples:**

    >>> f.data.get_compression_type()
    ''
    >>> print(f.array)
    [[3.98  0.0  0.0  --    --   --   --  --  --]
     [ 0.0  0.0  0.0  3.4  0.0  0.0 4.61  --  --]
     [0.86  0.8 0.75  0.0 4.56   --   --  --  --]
     [ 0.0 0.09  0.0 0.91 2.96 1.14 3.86 0.0 0.0]]
    >>> g = f.compress('contiguous')
    >>> cfdm.write(g, 'compressed_file_contiguous.nc')

    >>> g.equals(f)
    True

    >>> g.data.get_compression_type()
    'ragged contiguous'
    >>> g.data.get_count()
    <CF Count: (4) >
    >>> print(g.data.get_count().array)
    [3 7 5 9]
    >>> g.compress('indexed', inplace=True)
    >>> g.data.get_index()
     <CF Index: (24) >
    >>> print(g.data.get_index().array)
    [0 0 0 1 1 1 1 1 1 1 2 2 2 2 2 3 3 3 3 3 3 3 3 3]
    >>> cfdm.write(g, 'compressed_file_indexed.nc')

        '''
        def _empty_compressed_data(data, shape):
            return data.empty(shape=shape, dtype=data.dtype,
                              units=data.get_units(None),
                              calendar=data.get_calendar(None))
        # --- End: def

        def _RaggedContiguousArray(self, compressed_data, data,
                                   count_variable):
            return self._RaggedContiguousArray(compressed_data,
                                               shape=data.shape,
                                               size=data.size,
                                               ndim=data.ndim,
                                               count_variable=count_variable)
        # --- End: def

        def _RaggedIndexedArray(self, compressed_data, data,
                                index_variable):
            return self._RaggedIndexedArray(compressed_data,
                                            shape=data.shape,
                                            size=data.size,
                                            ndim=data.ndim,
                                            index_variable=index_variable)
        # --- End: def

        def _RaggedIndexedContiguousArray(self, compressed_data, data,
                                          count_variable,
                                          index_variable):
            return self._RaggedIndexedContiguousArray(
                compressed_data,
                shape=data.shape,
                size=data.size,
                ndim=data.ndim,
                count_variable=count_variable,
                index_variable=index_variable)
        # --- End: def

        def _compress_metadata(f, method, count, N, axes, Array_func,
                               **kwargs):
            '''TODO

        :Parameters:

            f: `Field`

            count: sequence of `int`

            N: `int`
                The number of elements in the compressed array.

            axes: sequence of `str`

            Array_func:

            kwargs:

        :Returns:

            `None`

            '''
            if method == 'indexed_contiguous':
                shape1 = f.data.shape[1]

            for key, c in f.constructs.filter_by_axis('or').items():
                c_axes = f.get_data_axes(key)
                if c_axes != axes:
                    # Skip metadata constructs which don't span
                    # exactly the same axes in the same order
                    continue

                # Initialize the compressed data for the metadata
                # construct
                data = c.get_data(None)
                if data is not None:
                    compressed_data = _empty_compressed_data(data, (N,))

                    # Populate the compressed data for the metadata
                    # construct
                    start = 0
                    if method == 'indexed_contiguous' and c.data.ndim == 2:
                        c_start = 0
                        for i, d in enumerate(
                                data.flatten(range(data.ndim-1))):
                            c_start = shape1 * i
                            c_end = c_start + shape1
                            last = sum(n > 0 for n in count[c_start:c_end])

                            end = start + last
                            compressed_data[start:end] = d[:last]
                            start += last
                    else:
                        for last, d in zip(count,
                                           data.flatten(range(data.ndim-1))):
                            if not last:
                                continue

                            end = start + last
                            compressed_data[start:end] = d[:last]
                            start += last
                # --- End: if

                # Insert the compressed data into the metadata
                # construct
                y = Array_func(f, compressed_data, data=data,
                               **kwargs)
                data._set_CompressedArray(y, copy=False)

                if c.has_bounds():
                    data = c.get_bounds_data(None)
                    if data is None:
                        continue

                    b_shape = data.shape[c.data.ndim:]
                    compressed_data = _empty_compressed_data(
                        data, (N,) + b_shape)

                    # Populate the compressed data for the metadata
                    # construct
                    start = 0
                    if method == 'indexed_contiguous' and c.data.ndim == 2:
                        c_start = 0
                        for i, d in enumerate(
                                data.flatten(range(c.data.ndim-1))):
                            c_start = shape1 * i
                            c_end = c_start + shape1
                            last = sum(n > 0 for n in count[c_start:c_end])

                            end = start + last
                            compressed_data[start:end] = d[:last]
                            start += last
                    else:
                        for last, d in zip(count,
                                           data.flatten(range(c.data.ndim-1))):
                            if not last:
                                continue

                            end = start + last
                            compressed_data[start:end] = d[:last]
                            start += last
                    # --- End: if

                    # Insert the compressed data into the metadata
                    # construct
                    y = Array_func(f, compressed_data, data=data,
                                   **kwargs)
                    data._set_CompressedArray(y, copy=False)
        # --- End: def

        f = _inplace_enabled_define_and_cleanup(self)

        data = f.get_data(None)
        if data is None:
            return f

        current_compression_type = data.get_compression_type().replace(
            ' ', '_')
        if (current_compression_type
            and current_compression_type == 'ragged_'+method):
            # The field is already compressed by the correct method
            return f

        if method == 'contiguous':
            if self.data.ndim != 2:
                raise ValueError(
                    "The field data must have exactly 2 dimensions for "
                    "DSG ragged contiguous compression. Got {}".format(
                        self.data.ndim))
        elif method == 'indexed':
            if self.data.ndim != 2:
                raise ValueError(
                    "The field data must have exactly 2 dimensions for "
                    "DSG ragged indexed compression. Got {}".format(
                        self.data.ndim))
        elif method == 'indexed_contiguous':
            if self.data.ndim != 3:
                raise ValueError(
                    "The field data must have exactly 3 dimensions for "
                    "DSG ragged indexed contiguous compression. Got {}".format(
                        self.data.ndim))
        # --- End: if

        # Make sure that the metadata constructs have the same
        # relative axis order as the field's data
        f.transpose(range(self.data.ndim), constructs=True, inplace=True)

        if method == 'gathered':
            # --------------------------------------------------------
            # Compression by gathering
            # --------------------------------------------------------
            pass
        else:
            # --------------------------------------------------------
            # DSG compression
            # --------------------------------------------------------
            flattened_data = data.flatten(range(data.ndim-1))

            count = []
            for d in flattened_data:
                last = d.size
                for i in d[::-1]:
                    if i is not cfdm_masked:
                        break
                    else:
                        last -= 1
                # --- End: for

                count.append(last)

            N = sum(count)
            compressed_field_data = _empty_compressed_data(data, (N,))

            start = 0
            for last, d in zip(count, flattened_data):
                if not last:
                    continue

                end = start + last
                compressed_field_data[start:end] = d[:last]
                start += last
        # --- End: if

        if method == 'contiguous':
            # --------------------------------------------------------
            # Ragged contiguous
            # --------------------------------------------------------
            count_variable = self._Count(
                properties=count_properties,
                data=self._Data([n for n in count if n]))

            x = _RaggedContiguousArray(self, compressed_field_data,
                                       data,
                                       count_variable=count_variable)

            _compress_metadata(f, method, count, N, f.get_data_axes(),
                               _RaggedContiguousArray,
                               count_variable=count_variable)

        elif method == 'indexed':
            # --------------------------------------------------------
            # Ragged indexed
            # --------------------------------------------------------
            index_variable = self._Index(properties=index_properties,
                                         data=self._Data.empty(shape=(N,),
                                                               dtype=int))

            start = 0
            for i, (last, d) in enumerate(zip(count, flattened_data)):
                if not last:
                    continue

                end = start + last
                index_variable.data[start:end] = i
                start += last

            x = _RaggedIndexedArray(self, compressed_field_data, data,
                                    index_variable)

            _compress_metadata(f, method, count, N, f.get_data_axes(),
                               _RaggedIndexedArray,
                               index_variable=index_variable)

        elif method == 'indexed_contiguous':
            # --------------------------------------------------------
            # Ragged indexed contiguous
            # --------------------------------------------------------
            index = []
            shape1 = f.data.shape[1]
            for i in range(f.data.shape[0]):
                start = shape1 * i
                end = start + shape1
                index.extend([i] * sum(n > 0 for n in count[start:end]))

            count_variable = self._Count(
                properties=count_properties,
                data=self._Data([n for n in count if n]))
            index_variable = self._Index(properties=index_properties,
                                         data=self._Data(index))

            x = _RaggedIndexedContiguousArray(self,
                                              compressed_field_data,
                                              data, count_variable,
                                              index_variable)

            _compress_metadata(f, method, count, N, f.get_data_axes(),
                               _RaggedIndexedContiguousArray,
                               count_variable=count_variable,
                               index_variable=index_variable)

            # Compress metadata constructs that span the index axis,
            # but not the count axis.
            _compress_metadata(f, method, count, len(index),
                               f.get_data_axes()[:-1],
                               _RaggedIndexedArray,
                               index_variable=index_variable)

#            axes = f.get_data_axes()[:-1]
#            for key, c in f.constructs.filter_by_axis('or').items():
#                c_axes = f.get_data_axes(key)
#                if c_axes != axes:
#                    # Skip metadata constructs which don't span
#                    # exactly the same axes in the same order
#                    continue
#
#                # Initialize the compressed data for the metadata
#                # construct
#                data = c.data
#                compressed_data = _empty_compressed_data(data, len(index))
#
#                # Populate the compressed data for the metadata
#                # construct
#                start = 0
#                c_start = 0
#                for i, d in enumerate(data.flatten(range(data.ndim-1))):
#                    c_start = shape1 * i
#                    c_end = c_start + shape1
#                    last = sum(n > 0 for n in count[c_start:c_end])
#
#                    end = start + last
#                    compressed_data[start:end] = d[:last]
#                    start += last
#
#                # Insert the compressed data into the metadata
#                # construct
#                y = _RaggedIndexedArray(compressed_data, data,
#                                        index_variable=index_variable)
#                data._create_partition_matrix_for_compressed_array(y)
        # --- End: if

        elif method == 'gathered':
            # --------------------------------------------------------
            # Gathered
            # --------------------------------------------------------
            raise ValueError(
                "Compression by gathering is not yet available - sorry!")

        else:
            raise ValueError("Unknown compression method: {!r}".format(method))

        f.data._set_CompressedArray(x, copy=False)

        return f

    def copy(self, data=True):
        '''Return a deep copy of the field construct.

    ``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

    Arrays within `Data` instances are copied with a copy-on-write
    technique. This means that a copy takes up very little extra
    memory, even when the original contains very large data arrays,
    and the copy operation is fast.

    .. versionadded:: 1.7.0

    :Parameters:

        data: `bool`, optional
            If False then do not copy the data field construct, nor
            that of any of its metadata constructs. By default all
            data are copied.

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

    def dump(self, display=True, _level=0, _title=None):
        '''A full description of the field construct.

    Returns a description of all properties, including those of
    metadata constructs and their components, and provides selected
    values of all data arrays.

    .. versionadded:: 1.7.0

    :Parameters:

        display: `bool`, optional
            If False then return the description as a string. By
            default the description is printed.

    :Returns:

        `None` or `str`
            The description. If *display* is True then the description
            is printed and `None` is returned. Otherwise the
            description is returned as a string.

        '''
        indent = '    '
        indent0 = indent * _level
        indent1 = indent0 + indent

        if _title is None:
            ncvar = self.nc_get_variable(None)
            _title = self.identity(default=None)
            if ncvar is not None:
                if _title is None:
                    _title = "ncvar%{0}".format(ncvar)
                else:
                    _title += " (ncvar%{0})".format(ncvar)
            # --- End: if
            if _title is None:
                _title = ''

            _title = 'Field: {0}'.format(_title)
        # --- End: if

        line  = '{0}{1}'.format(indent0, ''.ljust(len(_title), '-'))

        # Title
        string = [line, indent0+_title, line]

        axis_to_name = self._unique_domain_axis_identities()

        name = self._unique_construct_names()

        constructs_data_axes = self.constructs.data_axes()

        # Simple properties
        properties = self.properties()
        if properties:
           string.append(self._dump_properties(_level=_level))

        # Data
        data = self.get_data(None)
        if data is not None:
            x = [axis_to_name[axis] for axis in self.get_data_axes(default=())]

            units = self.get_property('units', None)
            if units is None:
                isreftime = bool(self.get_property('calendar', False))
            else:
                isreftime = 'since' in units

            if isreftime:
                data = data.asdata(data.datatime_array)

            string.append('')
            string.append('{0}Data({1}) = {2}'.format(indent0,
                                                      ', '.join(x),
                                                      str(data)))
            string.append('')

        # Cell methods
        cell_methods = self.cell_methods
        if cell_methods:
            for cm in cell_methods.values():
                cm = cm.copy()
                cm.set_axes(tuple([axis_to_name.get(axis, axis)
                                   for axis in cm.get_axes(())]))
                string.append(cm.dump(display=False,  _level=_level))

            string.append('')
        # --- End: if

        # Field ancillaries
        for cid, value in sorted(self.field_ancillaries.items()):
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

    @_manage_log_level_via_verbosity
    def equals(self, other, rtol=None, atol=None, verbose=None,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_compression=True,
               ignore_type=False):
        '''Whether two field constructs are the same.

    Equality is strict by default. This means that for two field
    constructs to be considered equal they must have corresponding
    metadata constructs and for each pair of constructs:

    * the same descriptive properties must be present, with the same
      values and data types, and vector-valued properties must also
      have same the size and be element-wise equal (see the
      *ignore_properties* and *ignore_data_type* parameters), and

    ..

    * if there are data arrays then they must have same shape and data
      type, the same missing data mask, and be element-wise equal (see
      the *ignore_data_type* parameter).

    Two real numbers ``x`` and ``y`` are considered equal if
    ``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
    differences) and ``rtol`` (the tolerance on relative differences)
    are positive, typically very small numbers. See the *atol* and
    *rtol* parameters.

    Any compression is ignored by default, with only the the arrays in
    their uncompressed forms being compared. See the
    *ignore_compression* parameter.

    Any type of object may be tested but, in general, equality is only
    possible with another field construct, or a subclass of one. See
    the *ignore_type* parameter.

    NetCDF elements, such as netCDF variable and dimension names, do
    not constitute part of the CF data model and so are not checked on
    any construct.

    .. versionadded:: 1.7.0

    :Parameters:

        other:
            The object to compare for equality.

        atol: float, optional
            The tolerance on absolute differences between real
            numbers. The default value is set by the `cfdm.ATOL`
            function.

        rtol: float, optional
            The tolerance on relative differences between real
            numbers. The default value is set by the `cfdm.RTOL`
            function.

        ignore_fill_value: `bool`, optional
            If True then the ``_FillValue`` and ``missing_value``
            properties are omitted from the comparison, for the field
            construct and metadata constructs.

        verbose: `int` or `None`, optional
            If an integer from ``0`` to ``3``, corresponding to increasing
            verbosity (else ``-1`` as a special case of maximal and extreme
            verbosity), set for the duration of the method call (only) as
            the minimum severity level cut-off of displayed log messages,
            regardless of the global configured `cfdm.LOG_LEVEL`.

            Else, if `None` (the default value), log messages will be
            filtered out, or otherwise, according to the value of the
            `cfdm.LOG_LEVEL` setting.

            Overall, the higher a non-negative integer that is set (up to
            a maximum of ``3``) the more description that is printed to
            convey information about differences that lead to inequality.

        ignore_properties: sequence of `str`, optional
            The names of properties of the field construct (not the
            metadata constructs) to omit from the comparison. Note
            that the ``Conventions`` property is always omitted by
            default.

        ignore_data_type: `bool`, optional
            If True then ignore the data types in all numerical
            comparisons. By default different numerical data types
            imply inequality, regardless of whether the elements are
            within the tolerance for equality.

        ignore_compression: `bool`, optional
            If False then the compression type and, if applicable, the
            underlying compressed arrays must be the same, as well as
            the arrays in their uncompressed forms. By default only
            the arrays in their uncompressed forms are compared.

        ignore_type: `bool`, optional
            Any type of object may be tested but, in general, equality
            is only possible with another field construct, or a
            subclass of one. If *ignore_type* is True then
            ``Field(source=other)`` is tested, rather than the
            ``other`` defined by the *other* parameter.

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
    >>> f.equals(g, verbose=3)
    Field: Non-common property name: foo
    Field: Different properties
    False

        '''
        # ------------------------------------------------------------
        # Check the properties and data
        # ------------------------------------------------------------
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
        if not self._equals(self.constructs, other.constructs,
                            rtol=rtol, atol=atol, verbose=verbose,
                            ignore_data_type=ignore_data_type,
                            ignore_fill_value=ignore_fill_value,
                            ignore_compression=ignore_compression,
                            _ignore_type=False):
            logger.info(
                "{0}: Different metadata constructs".format(
                    self.__class__.__name__)
            )
            return False

        return True

    def get_filenames(self):
        '''Return the name of the file or files containing the data.

    The names of the file or files containing the data of metadata
    constructs are also returned.

    :Returns:

        `set`
            The file names in normalized, absolute form. If all of the
            data are in memory then an empty `set` is returned.

    **Examples:**

    >>> f = cfdm.example_field(0)
    >>> cfdm.write(f, 'temp_file.nc')
    >>> g = cfdm.read('temp_file.nc')[0]
    >>> g.get_filenames()
    {'/data/user/file1.nc'}

        '''
        out = super().get_filenames()

        for c in self.constructs.filter_by_data().values():
            out.update(c.get_filenames())

        return out

    @_inplace_enabled
    def insert_dimension(self, axis, position=0, inplace=False):
        '''Expand the shape of the data array.

    Inserts a new size 1 axis, corresponding to an existing domain
    axis construct, into the data array.

    .. versionadded:: 1.7.0

    .. seealso:: `squeeze`, `transpose`

    :Parameters:

        axis: `str`
            The construct identifier of the domain axis construct
            corresponding to the inserted axis.

            *Parameter example:*
              ``axis='domainaxis2'``

        position: `int`, optional
            Specify the position that the new axis will have in the
            data array. By default the new axis has position 0, the
            slowest varying position. Negative integers counting from
            the last position are allowed.

            *Parameter example:*
              ``position=2``

            *Parameter example:*
              ``position=-1``

        inplace: `bool`, optional
            If True then do the operation in-place and return `None`.

    :Returns:

        `Field` or `None`
            The new field construct with expanded data axes. If the
            operation was in-place then `None` is returned.

    **Examples:**

    >>> f.data.shape
    (19, 73, 96)
    >>> f.insert_dimension('domainaxis3').data.shape
    (1, 96, 73, 19)
    >>> f.insert_dimension('domainaxis3', position=3).data.shape
    (19, 73, 96, 1)
    >>> f.insert_dimension('domainaxis3', position=-1, inplace=True)
    (19, 73, 1, 96)
    >>> f.data.shape
    (19, 73, 1, 96)

        '''
        f = _inplace_enabled_define_and_cleanup(self)

        domain_axis = f.domain_axes.get(axis, None)
        if domain_axis is None:
            raise ValueError(
                "Can't insert non-existent domain axis: {}".format(
                    axis))

        if domain_axis.get_size() != 1:
            raise ValueError(
                "Can't insert an axis of size {}: {!r}".format(
                    domain_axis.get_size(), axis))

        data_axes = f.get_data_axes(default=None)
        if data_axes is not None:
            if axis in data_axes:
                raise ValueError(
                    "Can't insert a duplicate data array axis: {!r}".format(
                        axis))

            data_axes = list(data_axes)
            data_axes.insert(position, axis)

        # Expand the dims in the field's data array
        super(Field, f).insert_dimension(position, inplace=True)

        if data_axes is not None:
            f.set_data_axes(data_axes)

        return f

    def convert(self, key, full_domain=True):
        '''Convert a metadata construct into a new field construct.

    The new field construct has the properties and data of the
    metadata construct, and domain axis constructs corresponding to
    the data. By default it also contains other metadata constructs
    (such as dimension coordinate and coordinate reference constructs)
    that define its domain.

    The `cfdm.read` function allows a field construct to be derived
    directly from a netCDF variable that corresponds to a metadata
    construct. In this case, the new field construct will have a
    domain limited to that which can be inferred from the
    corresponding netCDF variable - typically only domain axis and
    dimension coordinate constructs. This will usually result in a
    different field construct to that created with the
    `~Field.convert` method.

    .. versionadded:: 1.7.0

    .. seealso:: `cfdm.read`

    :Parameters:

        key: `str`
            Convert the metadata construct with the given construct
            key.

        full_domain: `bool`, optional
            If False then do not create a domain, other than domain
            axis constructs, for the new field construct. By default
            as much of the domain as possible is copied to the new
            field construct.

    :Returns:

        `Field`
            The new field construct.

    **Examples:**

    >>> f = cfdm.read('file.nc')[0]
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

        '''
        c = self.constructs.filter_by_key(key).value().copy()

        # ------------------------------------------------------------
        # Create a new field with the properties and data from the
        # construct
        # ------------------------------------------------------------
        data = c.del_data()

        f = type(self)(source=c, copy=True)

        # ------------------------------------------------------------
        # Add domain axes
        # ------------------------------------------------------------
        constructs_data_axes = self.constructs.data_axes()
        data_axes = constructs_data_axes.get(key)
        if data_axes is not None:
            for domain_axis in data_axes:
                f.set_construct(self.domain_axes[domain_axis],
                                key=domain_axis, copy=True)
        # --- End: if

        # ------------------------------------------------------------
        # Set data axes
        # ------------------------------------------------------------
        if data_axes is not None:
            f.set_data(data, axes=data_axes)

        # ------------------------------------------------------------
        # Add a more complete domain
        # ------------------------------------------------------------
        if full_domain:
            for ccid, construct in self.constructs.filter_by_type(
                    'dimension_coordinate',
                    'auxiliary_coordinate',
                    'cell_measure').items():
                axes = constructs_data_axes.get(ccid)
                if axes is None:
                    continue

                if set(axes).issubset(data_axes):
                    f.set_construct(construct, key=ccid, axes=axes, copy=True)
            # --- End: for

            # Add coordinate references which span a subset of the item's
            # axes
            for rcid, ref in self.coordinate_references.items():
                new_coordinates = [
                    ccid
                    for ccid in ref.coordinates()
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
                # --- End: for

                if ok:
                    ref = ref.copy()
                    ref.clear_coordinates()
                    ref.set_coordinates(new_coordinates)
                    f.set_construct(ref, key=rcid, copy=False)

                    # Copy domain ancillary constructs
                    for dakey in ref.coordinate_conversion.domain_ancillaries().values():
                        construct = self.constructs.get(dakey)
                        if construct is not None:
                            axes = constructs_data_axes.get(dakey)
                            f.set_construct(construct,
                                            key=dakey, axes=axes, copy=True)
            # --- End: for
        # --- End: if

        return f

    def dataset_compliance(self, display=False):
        '''A report of problems encountered whilst reading the field construct
    from a dataset.

    If the dataset is partially CF-compliant to the extent that it is
    not possible to unambiguously map an element of the netCDF dataset
    to an element of the CF data model, then a field construct is
    still returned by the `read` function, but may be incomplete.

    Such "structural" non-compliance would occur, for example, if the
    ``coordinates`` attribute of a CF-netCDF data variable refers to
    another variable that does not exist, or refers to a variable that
    spans a netCDF dimension that does not apply to the data variable.

    Other types of non-compliance are not checked, such whether or not
    controlled vocabularies have been adhered to.

    .. versionadded:: 1.7.0

    .. seealso:: `cfdm.read`

    :Parameters:

        display: `bool`, optional
            If True print the compliance report. By default the report
            is returned as a dictionary.

    :Returns:

        `None` or `dict`
            The report. If *display* is True then the report is
            printed and `None` is returned. Otherwise the report is
            returned as a dictionary.

    **Examples:**

    If no problems were encountered, an empty dictionary is returned:

    >>> f.dataset_compliance()
    {}

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
                        '\n             '.join(
                            ['{0!r}: {1!r},'.format(key2, value2)
                             for key2, value2 in sorted(x.items())]
                        )
                    ))

                print('        ],')

            print('    },')
            print('}\n')

    @_inplace_enabled
    def squeeze(self, axes=None, inplace=False):
        '''Remove size one axes from the data array.

    By default all size one axes are removed, but particular size one
    axes may be selected for removal.

    .. versionadded:: 1.7.0

    .. seealso:: `insert_dimension`, `transpose`

    :Parameters:

        axes: (sequence of) `int`, optional
            The positions of the size one axes to be removed. By
            default all size one axes are removed. Each axis is
            identified by its original integer position. Negative
            integers counting from the last position are allowed.

            *Parameter example:*
              ``axes=0``

            *Parameter example:*
              ``axes=-2``

            *Parameter example:*
              ``axes=[2, 0]``

        inplace: `bool`, optional
            If True then do the operation in-place and return `None`.

    :Returns:

        `Field` or `None`
            The field construct with removed data axes. If the
            operation was in-place then `None` is returned.

    **Examples:**

    >>> f.data.shape
    (1, 73, 1, 96)
    >>> f.squeeze().data.shape
    (73, 96)
    >>> f.squeeze(0).data.shape
    (73, 1, 96)
    >>> f.squeeze([-3, 2], inplace=True)
    >>> f.data.shape
    (73, 96)

        '''
        f = _inplace_enabled_define_and_cleanup(self)

        if axes is None:
            iaxes = [i for i, n in enumerate(f.data.shape) if n == 1]
        else:
            try:
                iaxes = f.data._parse_axes(axes)
            except ValueError as error:
                raise ValueError("Can't squeeze data: {}".format(error))

        data_axes = f.get_data_axes(default=None)
        if data_axes is  not None:
            new_data_axes = [data_axes[i]
                             for i in range(f.data.ndim) if i not in iaxes]

        # Squeeze the field's data array
        super(Field, f).squeeze(iaxes, inplace=True)

        if data_axes is not None:
            f.set_data_axes(new_data_axes)

        return f

    @_inplace_enabled
    def transpose(self, axes=None, constructs=False, inplace=False):
        '''Permute the axes of the data array.

    .. versionadded:: 1.7.0

    .. seealso:: `insert_dimension`, `squeeze`

    :Parameters:

        axes: (sequence of) `int`
            The new axis order. By default the order is reversed. Each
            axis in the new order is identified by its original
            integer position. Negative integers counting from the last
            position are allowed.

            *Parameter example:*
              ``axes=[2, 0, 1]``

            *Parameter example:*
              ``axes=[-1, 0, 1]``

        constructs: `bool`
            If True then tranpose the metadata constructs to have the
            same relative domain axis order as the data of tranposed
            field constuct. By default, metadata constructs are not
            changed.

        inplace: `bool`, optional
            If True then do the operation in-place and return `None`.

    :Returns:

        `Field` or `None`
            The field construct with permuted data axes. If the
            operation was in-place then `None` is returned.

    **Examples:**

    >>> f.data.shape
    (19, 73, 96)
    >>> f.transpose().data.shape
    (96, 73, 19)
    >>> f.transpose([1, 0, 2]).data.shape
    (73, 19, 96)
    >>> f.transpose(inplace=True)
    >>> f.data.shape
    (96, 19, 73)

        '''
        f = _inplace_enabled_define_and_cleanup(self)

        try:
            iaxes = f.data._parse_axes(axes)
        except ValueError as error:
            raise ValueError("Can't transpose data: {}".format(error))

        ndim = f.data.ndim
        if iaxes is None:
            iaxes = tuple(range(ndim-1, -1, -1))

        data_axes = f.get_data_axes(default=None)

        # Transpose the field's data array
        super(Field, f).transpose(iaxes, inplace=True)

        if data_axes is not None:
            new_data_axes = [data_axes[i] for i in iaxes]
            f.set_data_axes(new_data_axes)

        if constructs:
            for key, construct in f.constructs.filter_by_data().items():
                data = construct.get_data(None)
                if data is None:
                    continue

                if data.ndim < 2:
                    # No need to transpose 1-d constructs
                    continue

                construct_axes = f.get_data_axes(key)

                new_construct_axes = [axis for axis in new_data_axes
                                      if axis in construct_axes]

                for i, axis in enumerate(construct_axes):
                    if axis not in new_construct_axes:
                        new_construct_axes.insert(i, axis)
                # --- End: for

                iaxes = [construct_axes.index(axis)
                         for axis in new_construct_axes]

                # Transpose the construct
                construct.transpose(iaxes, inplace=True)

                f.set_data_axes(axes=new_construct_axes, key=key)
        # --- End: if

        return f

    @_inplace_enabled
    def uncompress(self, inplace=False):
        '''Uncompress the construct.

    Compression saves space by identifying and removing unwanted
    missing data. Such compression techniques store the data more
    efficiently and result in no precision loss.

    Whether or not the construct is compressed does not alter its
    functionality nor external appearance.

    A field construct that is already uncompressed will be returned
    uncompressed.

    The following type of compression are available:

        * Ragged arrays for discrete sampling geometries (DSG). Three
          different types of ragged array representation are
          supported.

        ..

        * Compression by gathering.

    .. versionadded:: 1.7.11

    .. seealso:: `compress`

    :Parameters:

        inplace: `bool`, optional
            If True then do the operation in-place and return `None`.

    :Returns:

        `Field` or `None`
            The uncompressed field construct, or `None` if the
            operation was in-place.

    **Examples:**

    >>> f.data.get_compression_type()
    'ragged contiguous'
    >>> g = f.uncompress()
    >>> g.data.get_compression_type()
    ''
    >>> g.equals(f)
    True

        '''
        f = _inplace_enabled_define_and_cleanup(self)
        super(Field, f).uncompress(inplace=True)

        for c in f.constructs.filter_by_data().values():
            c.uncompress(inplace=True)

        return f

# --- End: class
