import logging
import textwrap

import numpy

from . import Container

from ..decorators import _manage_log_level_via_verbosity


logger = logging.getLogger(__name__)


class Properties(Container):
    '''Mixin class for descriptive properties.

    .. versionadded:: (cfdm) 1.7.0

    '''
    def __str__(self):
        '''Called by the `str` built-in function.

    x.__str__() <==> str(x)

    .. versionadded:: (cfdm) 1.7.0

        '''
        return '{0}'.format(self.identity(''))

    def _dump_properties(self, _prefix='', _level=0,
                         _omit_properties=None):
        '''Dump the properties.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        _omit_properties: sequence of `str`, optional
            Omit the given CF properties from the description.

        _level: `int`, optional

    :Returns:

        `str`

        '''
        indent0 = '    ' * _level
        string = []

        properties = self.properties()

        if _omit_properties:
            for prop in _omit_properties:
                properties.pop(prop, None)
        # --- End: if

        for prop, value in sorted(properties.items()):
            name = '{0}{1}{2} = '.format(indent0, _prefix, prop)
            value = repr(value)
            subsequent_indent = ' ' * len(name)
            if value.startswith("'") or value.startswith('"'):
                subsequent_indent = '{0} '.format(subsequent_indent)

            string.append(
                textwrap.fill(name + value, 79,
                              subsequent_indent=subsequent_indent))

        return '\n'.join(string)

    def dump(self, display=True, _key=None, _omit_properties=(),
             _prefix='', _title=None, _create_title=True, _level=0):
        '''A full description.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        display: `bool`, optional
            If False then return the description as a string. By
            default the description is printed.

    :Returns:

        {{returns dump}}

        '''
        indent0 = '    ' * _level
        indent1 = '    ' * (_level + 1)

        string = []

        # ------------------------------------------------------------
        # Title
        # ------------------------------------------------------------
        if _create_title:
            if _title is None:
                if _key:
                    default = 'key%{0}'.format(_key)
                else:
                    default = ''

                string.append('{0}{1}: {2}'.format(
                    indent0,
                    self.__class__.__name__,
                    self.identity(default=default)))
            else:
                string.append(indent0 + _title)
        # --- End: if

        # ------------------------------------------------------------
        # Properties
        # ------------------------------------------------------------
        properties = self._dump_properties(_prefix=_prefix,
                                           _level=_level + 1,
                                           _omit_properties=_omit_properties)
        if properties:
            string.append(properties)

        string = '\n'.join(string)

        if display:
            print(string)
        else:
            return string

    @_manage_log_level_via_verbosity
    def equals(self, other, rtol=None, atol=None, verbose=None,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_type=False):
        '''Whether two instances are the same.

    Equality is strict by default. This means that:

    * the same descriptive properties must be present, with the same
      values and data types, and vector-valued properties must also have
      same the size and be element-wise equal (see the *ignore_properties*
      and *ignore_data_type* parameters).

    {{equals tolerance}}

    Any type of object may be tested but, in general, equality is only
    possible with another object of the same type, or a subclass of
    one. See the *ignore_type* parameter.

    {{equals netCDF}}

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        other:
            The object to compare for equality.

        {[atol: float, optional}}

        {{rtol: float, optional}}

        ignore_fill_value: `bool`, optional
            If True then the ``_FillValue`` and ``missing_value``
            properties are omitted from the comparison.

        {{verbose: `int` or `str` or `None`, optional}}

        ignore_properties: sequence of `str`, optional
            The names of properties to omit from the comparison.

        {{ignore_data_type: `bool`, optional}}

        {{ignore_type: `bool`, optional}}

    :Returns:

        `bool`
            Whether the two instances are equal.

    **Examples:**

    >>> p.equals(p)
    True
    >>> p.equals(p.copy())
    True
    >>> p.equals('not a colection of properties')
    False

    >>> q = p.copy()
    >>> q.set_property('foo', 'bar')
    >>> p.equals(q)
    False
    >>> p.equals(q, verbose=3)
    Field: Non-common property name: foo
    Field: Different properties
    False

        '''
        pp = super()._equals_preprocess(other, verbose=verbose,
                                        ignore_type=ignore_type)
        if pp is True or pp is False:
            return pp

        other = pp

        # ------------------------------------------------------------
        # Check the properties
        # ------------------------------------------------------------
        if ignore_fill_value:
            ignore_properties += ('_FillValue', 'missing_value')

        self_properties = self.properties()
        other_properties = other.properties()

        if ignore_properties:
            for prop in ignore_properties:
                self_properties.pop(prop, None)
                other_properties.pop(prop, None)
        # --- End: if

        if set(self_properties) != set(other_properties):
            for prop in set(self_properties).symmetric_difference(
                    other_properties):
                logger.info(
                    "{}: Missing property: {}".format(
                        self.__class__.__name__, prop)
                )
        # --- End: if

            return False

        for prop, x in self_properties.items():
            y = other_properties[prop]

            if not self._equals(x, y,
                                rtol=rtol, atol=atol,
                                ignore_fill_value=ignore_fill_value,
                                ignore_data_type=True,
                                verbose=verbose):
                logger.info(
                    "{}: Different {!r} property values: "
                    "{!r}, {!r}".format(
                        self.__class__.__name__, prop, x, y)
                )

                return False
        # --- End: for

        return True

    def identity(self, default=''):
        '''Return the canonical identity.

    By default the identity is the first found of the following:

    * The ``standard_name`` property.
    * The ``cf_role`` property, preceeded by ``'cf_role='``.
    * The ``axis`` property, preceeded by ``'axis='``.
    * The ``long_name`` property, preceeded by ``'long_name='``.
    * The netCDF variable name, preceeded by ``'ncvar%'``.
    * The value of the *default* parameter.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `identities`

    :Parameters:

        default: optional
            If no identity can be found then return the value of the
            default parameter.

    :Returns:

            The identity.

    **Examples:**

    >>> f = {{package}}.{{class}}()
    >>> f.set_properties({'foo': 'bar',
    ...                   'long_name': 'Air Temperature',
    ...                   'standard_name': 'air_temperature'}
    >>> f.nc_set_variable('tas')
    >>> f.identity()
    'air_temperature'
    >>> f.del_property('standard_name')
    'air_temperature'
    >>> f.identity(default='no identity')
    'air_temperature'
    >>> f.identity()
    'long_name=Air Temperature'
    >>> f.del_property('long_name')
    >>> f.identity()
    'ncvar%tas'
    >>> f.nc_del_variable()
    'tas'
    >>> f.identity()
    'ncvar%tas'
    >>> f.identity()
    ''
    >>> f.identity(default='no identity')
    'no identity'

        '''
        n = self.get_property('standard_name', None)
        if n is not None:
            return n

        for prop in ('cf_role', 'axis', 'long_name'):
            n = self.get_property(prop, None)
            if n is not None:
                return '{0}={1}'.format(prop, n)
        # --- End: for

        n = self.nc_get_variable(None)
        if n is not None:
            return 'ncvar%{0}'.format(n)

        return default

    def identities(self):
        '''Return all possible identities.

    The identities comprise:

    * The ``standard_name`` property.
    * All properties, preceeded by the property name and a colon,
      e.g. ``'long_name:Air temperature'``.
    * The netCDF variable name, preceeded by ``'ncvar%'``.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `identity`

    :Returns:

        `list`
            The identities.

    **Examples:**

    >>> f.properties()
    {'foo': 'bar',
     'long_name': 'Air Temperature',
     'standard_name': 'air_temperature'}
    >>> f.nc_get_variable()
    'tas'
    >>> f.identities()
    ['air_temperature',
     'long_name=Air Temperature',
     'foo=bar',
     'standard_name=air_temperature',
     'ncvar%tas']

        '''
        properties = self.properties()
        cf_role = properties.pop('cf_role', None)
        axis = properties.pop('axis', None)
        long_name = properties.pop('long_name', None)
        standard_name = properties.pop('standard_name', None)

        out = []

        if standard_name is not None:
            out.append(standard_name)

        if cf_role is not None:
            out.append('cf_role={}'.format(cf_role))

        if axis is not None:
            out.append('axis={}'.format(axis))

        if long_name is not None:
            out.append('long_name={}'.format(long_name))

        out += ['{0}={1}'.format(prop, value)
                for prop, value in sorted(properties.items())]

        if standard_name is not None:
            out.append('standard_name={}'.format(standard_name))

        n = self.nc_get_variable(None)
        if n is not None:
            out.append('ncvar%{0}'.format(n))

        return out

# --- End: class
