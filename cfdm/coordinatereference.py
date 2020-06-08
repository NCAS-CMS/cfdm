from __future__ import print_function
from builtins import (str, super)
from past.builtins import basestring

import logging

from . import mixin
from . import core
from . import CoordinateConversion
from . import Datum

from .decorators import _manage_log_level_via_verbosity


logger = logging.getLogger(__name__)


class CoordinateReference(mixin.NetCDFVariable,
                          mixin.Container,
                          core.CoordinateReference):
    '''A coordinate reference construct of the CF data model.

    A coordinate reference construct relates the coordinate values of
    the coordinate system to locations in a planetary reference frame.

    The domain of a field construct may contain various coordinate
    systems, each of which is constructed from a subset of the
    dimension and auxiliary coordinate constructs. For example, the
    domain of a four-dimensional field construct may contain
    horizontal (y-x), vertical (z), and temporal (t) coordinate
    systems. There may be more than one of each of these, if there is
    more than one coordinate construct applying to a particular
    spatiotemporal dimension (for example, there could be both
    latitude-longitude and y-x projection coordinate systems). In
    general, a coordinate system may be constructed implicitly from
    any subset of the coordinate constructs, yet a coordinate
    construct does not need to be explicitly or exclusively associated
    with any coordinate system.

    A coordinate system of the field construct can be explicitly
    defined by a coordinate reference construct which relates the
    coordinate values of the coordinate system to locations in a
    planetary reference frame and consists of the following:

    * References to the dimension coordinate and auxiliary coordinate
      constructs that define the coordinate system to which the
      coordinate reference construct applies. Note that the coordinate
      values are not relevant to the coordinate reference construct,
      only their properties.

    ..

    * A definition of a datum specifying the zeroes of the dimension
      and auxiliary coordinate constructs which define the coordinate
      system. The datum may be implied by the metadata of the
      referenced dimension and auxiliary coordinate constructs, or
      explicitly provided.

    ..

    * A coordinate conversion, which defines a formula for converting
      coordinate values taken from the dimension or auxiliary
      coordinate constructs to a different coordinate system. A
      coordinate reference construct relates the coordinate values of
      the field to locations in a planetary reference frame.


    **NetCDF interface**

    The netCDF grid mapping variable name of a coordinate reference
    construct may be accessed with the `nc_set_variable`,
    `nc_get_variable`, `nc_del_variable` and `nc_has_variable`
    methods.

    .. versionadded:: 1.7.0

    '''
    def __new__(cls, *args, **kwargs):
        '''This must be overridden in subclasses.

        '''
        instance = super().__new__(cls)
        instance._CoordinateConversion = CoordinateConversion
        instance._Datum = Datum
        return instance

    def __init__(self, coordinates=None, datum=None,
                 coordinate_conversion=None,
                 source=None, copy=True):
        '''**Initialization**

    :Parameters:

        coordinates: sequence of `str`, optional
            Identify the related dimension and auxiliary coordinate
            constructs by their construct identifiers. Ignored if the
            *source* parameter is set.

            The coordinates may also be set after initialisation with
            the `set_coordinates` and `set_coordinate` methods.

            *Parameter example:*
              ``coordinates=['dimensioncoordinate2']``

            *Parameter example:*
              ``coordinates=('dimensioncoordinate0', 'dimensioncoordinate1')``

        datum: `Datum`, optional
            Set the datum component of the coordinate reference
            construct. Ignored if the *source* parameter is set.

            The datum may also be set after initialisation with the
            `set_datum` method.

        coordinate_conversion: `CoordinateConversion`, optional
            Set the coordinate conversion component of the coordinate
            reference construct. Ignored if the *source* parameter is
            set.

            The coordinate conversion may also be set after
            initialisation with the `set_coordinate_conversion`
            method.

        source: optional
            Initialize the coordinates, datum and coordinate
            conversion from those of *source*.

        copy: `bool`, optional
            If False then do not deep copy arguments prior to
            initialization. By default arguments are deep copied.

        '''
        super().__init__(
            coordinates=coordinates,
            datum=datum,
            coordinate_conversion=coordinate_conversion,
            source=source,
            copy=copy)

        self._initialise_netcdf(source)

    def __str__(self):
        '''Called by the `str` built-in function.

    x.__str__() <==> str(x)

    .. versionadded:: 1.7.0

        '''
        return self.identity(default=self.nc_get_variable(''))

    def dump(self, display=True, _omit_properties=None, field=None,
             key='', _level=0, _title=None, _construct_names=None,
             _auxiliary_coordinates=None, _dimension_coordinates=None):
        '''A full description of the coordinate reference construct.

    Returns a description of all properties, including those of
    components.

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
        indent0 = '    ' * _level
        indent1 = '    ' * (_level+1)
        indent2 = '    ' * (_level+2)

        if _title is None:
            string = ['{0}Coordinate Reference: {1}'.format(
                indent0, self.identity(default=''))]
        else:
            string = [indent0 + _title]

        # Coordinate conversion parameter-valued terms
        coordinate_conversion = self.get_coordinate_conversion()
        for term, value in sorted(coordinate_conversion.parameters().items()):
            string.append("{0}Coordinate conversion:{1} = {2}".format(
                indent1, term, value))

        # Coordinate conversion domain ancillary-valued terms
        if _construct_names:
            for term, key in sorted(
                    coordinate_conversion.domain_ancillaries().items()):
                if key in _construct_names:
                    construct_name = 'Domain Ancillary: ' \
                                     + _construct_names.get(
                                         key, 'key:{}'.format(key))
                else:
                    construct_name = ''

                string.append('{0}Coordinate conversion:{1} = {2}'.format(
                    indent1, term, construct_name))
        else:
            for term, value in sorted(
                    coordinate_conversion.domain_ancillaries().items()):
                string.append("{0}Coordinate conversion:{1} = {2}".format(
                    indent1, term, str(value)))

        # Datum parameter-valued terms
        datum = self.get_datum()
        for term, value in sorted(datum.parameters().items()):
            string.append("{0}Datum:{1} = {2}".format(indent1, term, value))

        # Coordinates
        if _construct_names:
            for key in sorted(self.coordinates(), reverse=True):
                coord = '{}'.format(
                    _construct_names.get(key, 'key:{}'.format(key)))
                if key in _dimension_coordinates:
                    coord = 'Dimension Coordinate: '+coord
                elif key in _auxiliary_coordinates:
                    coord = 'Auxiliary Coordinate: '+coord

                string.append('{0}{1}'.format(indent1, coord))
        else:
            for identifier in sorted(self.coordinates()):
                string.append('{0}Coordinate: {1}'.format(indent1, identifier))

        string = '\n'.join(string)

        if display:
            print(string)
        else:
            return string

    @_manage_log_level_via_verbosity
    def equals(self, other, rtol=None, atol=None, verbose=None,
               ignore_type=False):
        '''Whether two coordinate reference constructs are the same.

    Equality is strict by default. This means that:

    * the datum and coordinate conversion components must have the
      same string and numerical parameters.

    The dimension coordinate, auxiliary coordinate and domain
    ancillary constructs of the coordinate reference constructs are
    *not* considered, because they may only be correctly interpreted
    by the field constructs that contain the coordinate reference
    constructs in question. They are, however, taken into account when
    two fields constructs are tested for equality.

    Two real numbers ``x`` and ``y`` are considered equal if
    ``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
    differences) and ``rtol`` (the tolerance on relative differences)
    are positive, typically very small numbers. The data type of the
    numbers is not taken into consideration. See the *atol* and *rtol*
    parameters.

    Any type of object may be tested but, in general, equality is only
    possible with another coordinate reference construct, or a
    subclass of one. See the *ignore_type* parameter.

    NetCDF elements, such as netCDF variable and dimension names, do
    not constitute part of the CF data model and so are not checked.

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

        ignore_type: `bool`, optional
            Any type of object may be tested but, in general, equality
            is only possible with another coordinate reference
            construct, or a subclass of one. If *ignore_type* is True
            then ``CoordinateReference(source=other)`` is tested,
            rather than the ``other`` defined by the *other*
            parameter.

    :Returns:

        `bool`
            Whether the two coordinate reference constructs are equal.

    **Examples:**

    >>> c.equals(c)
    True
    >>> c.equals(c.copy())
    True
    >>> c.equals('not a coordinate reference')
    False

        '''
        pp = super()._equals_preprocess(other, verbose=verbose,
                                        ignore_type=ignore_type)
        if pp is True or pp is False:
            return pp

        other = pp

        coords0 = self.coordinates()
        coords1 = other.coordinates()
        if len(coords0) != len(coords1):
            logger.info(
                "{}: Different sized collections of coordinates "
                "({}, {})".format(
                    self.__class__.__name__, coords0, coords1)
            )

            return False

        if not self.coordinate_conversion.equals(
                other.coordinate_conversion,
                rtol=rtol, atol=atol,
                verbose=verbose,
                ignore_type=ignore_type):
            logger.info(
                "{}: Different coordinate conversions".format(
                    self.__class__.__name__)
            )

            return False

        if not self.datum.equals(
                other.datum,
                rtol=rtol, atol=atol,
                verbose=verbose,
                ignore_type=ignore_type):
            logger.info(
                "{}: Different datums".format(self.__class__.__name__))

            return False

        # Still here? Then the two coordinate references are as equal
        # as can be ascertained in the absence of domains.
        return True

    def identity(self, default=''):
        '''Return the canonical identity.

    By default the identity is the first found of the following:

    * The ``standard_name`` coordinate conversion parameter, preceeded
      by ``'standard_name:'``.
    * The ``grid_mapping_name`` coordinate conversion parameter,
      preceeded by ``'grid_mapping_name:'``.
    * The netCDF variable name (corresponding to a netCDF grid mapping
      variable), preceeded by ``'ncvar%'``.
    * The value of the *default* parameter.

    .. versionadded:: 1.7.0

    .. seealso:: `identities`

    :Parameters:

        default: optional
            If no identity can be found then return the value of the
            default parameter.

    :Returns:

            The identity.

    **Examples:**

    >>> c.identity()
    'standard_name:atmosphere_ln_pressure_coordinate'

    >>> c.identity()
    'grid_mapping_name:lambert_azimuthal_equal_area'

    >>> c.identity()
    'ncvar%rotated_pole'

    >>> c.identity()
    ''
    >>> c.identity(default='no identity')
    'no identity'

        '''
        for prop in ('standard_name', 'grid_mapping_name'):
            n = self.coordinate_conversion.get_parameter(prop, None)
            if n is not None:
                return '{0}:{1}'.format(prop, n)
        # --- End: for

        n = self.nc_get_variable(None)
        if n is not None:
            return 'ncvar%{0}'.format(n)

        return default

    def identities(self):
        '''Return all possible identities.

    The identities comprise:

    * The ``standard_name`` coordinate conversion parameter, preceeded
      by ``'standard_name:'``.
    * The ``grid_mapping_name`` coordinate conversion parameter,
      preceeded by ``'grid_mapping_name:'``.
    * The netCDF variable name (corresponding to a netCDF grid mapping
      variable), preceeded by ``'ncvar%'``.

    .. versionadded:: 1.7.0

    .. seealso:: `identity`

    :Returns:

        `list`
            The identities.

    **Examples:**

    >>> c.identities()
    ['standard_name:atmosphere_ln_pressure_coordinate']

    >>> c.identities()
    ['grid_mapping_name:lambert_azimuthal_equal_area', 'ncvar%grid_mapping']

    >>> c.identity()
    ['ncvar%rotated_pole']

    >>> c.identities()
    []

        '''

        out = []

        for prop in ('standard_name', 'grid_mapping_name'):
            n = self.coordinate_conversion.get_parameter(prop, None)
            if n is not None:
                out.append('{0}:{1}'.format(prop, n))
        # --- End: for

        n = self.nc_get_variable(None)
        if n is not None:
            out.append('ncvar%{0}'.format(n))

        return out

# --- End: class
