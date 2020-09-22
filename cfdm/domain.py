import logging

from . import mixin
from . import core

from . import Constructs

from .decorators import _manage_log_level_via_verbosity


logger = logging.getLogger(__name__)


class Domain(mixin.NetCDFVariable,
             mixin.ConstructAccess,
             mixin.Properties,
             core.Domain):
    '''A domain construct of the CF data model.

    The domain represents a set of discrete "locations" in what
    generally would be a multi-dimensional space, either in the real
    world or in a model's simulated world. These locations correspond
    to individual data array elements of a field construct

    The domain construct is defined collectively by the following
    constructs of the CF data model: domain axis, dimension
    coordinate, auxiliary coordinate, cell measure, coordinate
    reference and domain ancillary constructs; as well as properties
    to descibe the domain.

    **NetCDF interface**

    The netCDF variable name of the construct may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_del_variable` and
    `nc_has_variable` methods.

    The netCDF variable group structure may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_variable_groups`,
    `nc_clear_variable_groups` and `nc_set_variable_groups` methods.

    .. versionadded:: (cfdm) 1.7.0

    '''
    def __new__(cls, *args, **kwargs):
        '''This must be overridden in subclasses.

    .. versionadded:: (cfdm) 1.7.0

        '''
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        return instance

    def __init__(self, source=None, copy=True, _use_data=True):
        '''**Initialization**

    :Parameters:

        source: optional
            Initialize the metadata constructs from those of *source*.

            A new domain may also be instantiated with the
            `fromconstructs` class method.

        {{init copy: `bool`, optional}}

        '''
        super().__init__(source=source, copy=copy,
                         _use_data=_use_data)

        self._initialise_netcdf(source)

    def __repr__(self):
        '''Called by the `repr` built-in function.

    x.__repr__() <==> repr(x)

        '''
        shape = sorted([domain_axis.get_size()
                        for domain_axis in list(self.domain_axes.values())])
        shape = str(shape)
        shape = shape[1:-1]

        return '<{0}: {{{1}}}>'.format(self.__class__.__name__, shape)

    def __str__(self):
        '''Called by the `str` built-in function.

    x.__str__() <==> str(x)

        '''
        def _print_item(self, cid, variable, axes):
            '''Private function called by __str__

            '''
            x = [variable.identity(default='key%{0}'.format(cid))]

            if variable.has_data():
                shape = [axis_names[axis] for axis in axes]
                shape = str(tuple(shape)).replace("'", "")
                shape = shape.replace(',)', ')')
                x.append(shape)
            elif (variable.construct_type in ('auxiliary_coordinate',
                                              'domain_ancillary')
                  and variable.has_bounds()
                  and variable.bounds.has_data()):
                # Construct has no data but it does have bounds
                shape = [axis_names[axis] for axis in axes]
                shape.extend([str(n)
                              for n in variable.bounds.data.shape[len(axes):]])
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
                x.append(' = {0}'.format(variable.data))
            elif (variable.construct_type in ('auxiliary_coordinate',
                                              'domain_ancillary')
                  and variable.has_bounds()
                  and variable.bounds.has_data()):
                # Construct has no data but it does have bounds data
                x.append(' = {0}'.format(variable.bounds.data))

            return ''.join(x)
        # --- End: def

        string = []

        axis_names = self._unique_domain_axis_identities()

        constructs_data_axes = self.constructs.data_axes()

        x = []
        for axis_cid in sorted(self.domain_axes):
            for cid, dim in list(self.dimension_coordinates.items()):
                if constructs_data_axes[cid] == (axis_cid,):
                    name = dim.identity(default='key%{0}'.format(cid))
                    y = '{0}({1})'.format(name, dim.get_data().size)
                    if y != axis_names[axis_cid]:
                        y = '{0}({1})'.format(name, axis_names[axis_cid])
                    if dim.has_data():
                        y += ' = {0}'.format(dim.get_data())

                    x.append(y)
        # --- End: for
        if x:
            string.append('Dimension coords: {}'.format(
                '\n                : '.join(x)))

        # Auxiliary coordinates
        x = [_print_item(self, cid, v, constructs_data_axes[cid])
             for cid, v in sorted(self.auxiliary_coordinates.items())]
        if x:
            string.append('Auxiliary coords: {}'.format(
                '\n                : '.join(x)))

        # Cell measures
        x = [_print_item(self, cid, v, constructs_data_axes[cid])
             for cid, v in sorted(self.cell_measures.items())]
        if x:
            string.append('Cell measures   : {}'.format(
                '\n                : '.join(x)))

        # Coordinate references
        x = sorted([str(ref)
                    for ref in list(self.coordinate_references.values())])
        if x:
            string.append('Coord references: {}'.format(
                '\n                : '.join(x)))

        # Domain ancillary variables
        x = [_print_item(self, cid, anc, constructs_data_axes[cid])
             for cid, anc in sorted(self.domain_ancillaries.items())]
        if x:
            string.append('Domain ancils   : {}'.format(
                '\n                : '.join(x)))

        return '\n'.join(string)

    def _dump_axes(self, axis_names, display=True, _level=0):
        '''Return a string containing a description of the domain axes of the
    field.

    :Parameters:

        display: `bool`, optional
            If False then return the description as a string. By
            default the description is printed.

        _level: `int`, optional

    :Returns:

        `str`
            A string containing the description.

    **Examples:**

        '''
        indent1 = '    ' * _level

        axes = self.domain_axes

        w = sorted(["{0}Domain Axis: {1}".format(indent1, axis_names[axis])
                    for axis in axes])

        string = '\n'.join(w)

        if display:
            print(string)
        else:
            return string

    def dump(self, display=True, _omit_properties=(), _prefix='',
             _title=None, _create_title=True, _level=0):
        '''A full description of the domain construct.

    Returns a description of all properties, including those of
    metadata constructs and their components, and provides selected
    values of all data arrays.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        display: `bool`, optional
            If False then return the description as a string. By
            default the description is printed.

    :Returns:

        {{returns dump}}

        '''
        indent = '    '
        indent0 = indent * _level
        indent1 = indent0 + indent

        if _create_title:
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

                _title = '{0}: {1}'.format(self.__class__.__name__, _title)

            line = '{0}{1}'.format(indent0, ''.ljust(len(_title), '-'))

            # Title
            string = [
                line,
                indent0 + _title,
                line
            ]

            properties = super().dump(display=False,
                                      _create_title=False,
                                      _omit_properties=_omit_properties,
                                      _prefix=_prefix, _title=_title,
                                      _level=_level-1)
            string.append(properties)
            string.append('')
        else:
            string = []

        axis_to_name = self._unique_domain_axis_identities()

        construct_name = self._unique_construct_names()

        constructs_data_axes = self.constructs.data_axes()

        # Domain axes
        axes = self._dump_axes(axis_to_name, display=False, _level=_level)
        if axes:
            string.append(axes)

        # Dimension coordinates
        for cid, value in sorted(self.dimension_coordinates.items()):
            string.append('')
            string.append(
                value.dump(display=False, _level=_level,
                           _title='Dimension coordinate: {0}'.format(
                               construct_name[cid]),
                           _axes=constructs_data_axes[cid],
                           _axis_names=axis_to_name))

        # Auxiliary coordinates
        for cid, value in sorted(self.auxiliary_coordinates.items()):
            string.append('')
            string.append(
                value.dump(display=False, _level=_level,
                           _title='Auxiliary coordinate: {0}'.format(
                               construct_name[cid]),
                           _axes=constructs_data_axes[cid],
                           _axis_names=axis_to_name))

        # Domain ancillaries
        for cid, value in sorted(self.domain_ancillaries.items()):
            string.append('')
            string.append(value.dump(display=False, _level=_level,
                                     _title='Domain ancillary: {0}'.format(
                                         construct_name[cid]),
                                     _axes=constructs_data_axes[cid],
                                     _axis_names=axis_to_name))

        # Coordinate references
        for cid, value in sorted(self.coordinate_references.items()):
            string.append('')
            string.append(
                value.dump(
                    display=False, _level=_level,
                    _title='Coordinate reference: {0}'.format(
                        construct_name[cid]),
                    _construct_names=construct_name,
                    _auxiliary_coordinates=tuple(self.auxiliary_coordinates),
                    _dimension_coordinates=tuple(self.dimension_coordinates)))

        # Cell measures
        for cid, value in sorted(self.cell_measures.items()):
            string.append('')
            string.append(value.dump(
                display=False, _key=cid,
                _level=_level, _title='Cell measure: {0}'.format(
                    construct_name[cid]),
                _axes=constructs_data_axes[cid],
                _axis_names=axis_to_name))

        string.append('')

        string = '\n'.join(string)

        if display:
            print(string)
        else:
            return string

    @_manage_log_level_via_verbosity
    def equals(self, other, rtol=None, atol=None, verbose=None,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_compression=True, ignore_type=False):
        '''Whether two domains are the same.

    .. versionadded:: (cfdm) 1.7.0

    :Returns:

        `bool`

    **Examples:**

    >>> d.equals(d)
    True
    >>> d.equals(d.copy())
    True
    >>> d.equals('not a domain')
    False

        '''
        pp = super()._equals_preprocess(other, verbose=verbose,
                                        ignore_type=ignore_type)
        if pp is True or pp is False:
            return pp

        other = pp

        # ------------------------------------------------------------
        # Check the constructs
        # ------------------------------------------------------------
        if not self._equals(self.constructs, other.constructs,
                            rtol=rtol, atol=atol, verbose=verbose,
                            ignore_data_type=ignore_data_type,
                            ignore_fill_value=ignore_fill_value,
                            ignore_compression=ignore_compression):
            logger.info(
                "{0}: Different metadata constructs".format(
                    self.__class__.__name__)
            )
            return False

        return True

# --- End: class
