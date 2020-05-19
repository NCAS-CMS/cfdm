from __future__ import print_function
from builtins import (str, super)

import logging

from . import mixin
from . import core

from . import Constructs

from .decorators import _manage_log_level_via_verbosity


logger = logging.getLogger(__name__)


class Domain(mixin.ConstructAccess,
             mixin.Container,
             core.Domain):
    '''A domain of the CF data model.

    The domain represents a set of discrete "locations" in what
    generally would be a multi-dimensional space, either in the real
    world or in a model's simulated world. These locations correspond
    to individual data array elements of a field construct

    The domain is defined collectively by the following constructs of
    the CF data model: domain axis, dimension coordinate, auxiliary
    coordinate, cell measure, coordinate reference and domain
    ancillary constructs.

    .. versionadded:: 1.7.0

    '''
    def __new__(cls, *args, **kwargs):
        '''This must be overridden in subclasses.

        '''
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        return instance

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

#        string.append('')

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
        indent2 = '    ' * (_level+1)

        axes = self.domain_axes

        w = sorted(["{0}Domain Axis: {1}".format(indent1, axis_names[axis])
                    for axis in axes])

        string = '\n'.join(w)

        if display:
            print(string)
        else:
            return string

    def dump(self, display=True, _level=0, _title=None):
        '''A full description of the domain.

    The domain components are described without abbreviation with the
    exception of data arrays, which are abbreviated to their first and
    last values.

    :Parameters:

        display: `bool`, optional
            If False then return the description as a string. By
            default the description is printed.

            *Parameter example:*
              ``f.dump()`` is equivalent to ``print
              f.dump(display=False)``.

    :Returns:

        `None` or `str`
            If *display* is True then the description is printed and
            `None` is returned. Otherwise the description is returned
            as a string.

        '''
        indent = '    '
        indent0 = indent * _level
        indent1 = indent0 + indent

        axis_to_name = self._unique_domain_axis_identities()

        construct_name = self._unique_construct_names()

        constructs_data_axes = self.constructs.data_axes()

        string = []

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
            string.append( value.dump(
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

    .. versionadded:: 1.7.0

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
