from builtins import object

import re


class ConstructAccess(object):
    '''Mixin class for manipulating constructs stored in a `Constructs`
object.

.. versionadded:: 1.7.0

    '''
    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _unique_construct_names(self):
        '''Return unique metadata construct names.

.. versionadded:: 1.7.0

**Examples:**

>>> f._unique_construct_names()
{'cellmethod0': 'method:mean',
 'dimensioncoordinate0': 'latitude',
 'dimensioncoordinate1': 'longitude',
 'dimensioncoordinate2': 'time',
 'domainaxis0': 'ncdim%lat',
 'domainaxis1': 'ncdim%lon',
 'domainaxis2': 'key%domainaxis2'}

        '''    
        key_to_name = {}
        name_to_keys = {}


        for d in self.constructs._constructs.values():
            name_to_keys = {}
        
            for key, construct in d.items():
                name = construct.identity(default='key%'+key)                    
                name_to_keys.setdefault(name, []).append(key)
                key_to_name[key] = name
    
            for name, keys in name_to_keys.items():
                if len(keys) <= 1:
                    continue
                
                for key in keys:
                    key_to_name[key] = '{0}{{{1}}}'.format(
                        name,
                        re.findall('\d+$', key)[0])
        #--- End: for
        
        return key_to_name
    #--- End: def
    
    def _unique_domain_axis_identities(self):
        '''Return unique domain axis construct names.

.. versionadded:: 1.7.0

**Examples:**

>>> f._unique_domain_axis_identities()
{'domainaxis0': 'latitude(5)',
 'domainaxis1': 'longitude(8)',
 'domainaxis2': 'time(1)'}

        '''
        key_to_name = {}
        name_to_keys = {}

        for key, value in self.domain_axes.items():
            name_size = (self.constructs.domain_axis_identity(key), value.get_size(''))
            name_to_keys.setdefault(name_size, []).append(key)
            key_to_name[key] = name_size

        for (name, size), keys in name_to_keys.items():
            if len(keys) == 1:
                key_to_name[keys[0]] = '{0}({1})'.format(name, size)
            else:
                for key in keys:                    
                    key_to_name[key] = '{0}{{{1}}}({2})'.format(name,
                                                                re.findall('\d+$', key)[0],
                                                                size)
        #--- End: for
        
        return key_to_name
    #--- End: def

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def coordinate_references(self):
        '''Return coordinate reference constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `Constructs`
        The  constructs and their construct keys.
    `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.


**Examples:**

>>> f.coordinate_references
Constructs:
{}

>>> f.coordinate_references
Constructs:
{'coordinatereference0': <CoordinateReference: atmosphere_hybrid_height_coordinate>,
 'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>}

        '''
        return self.constructs.filter_by_type('coordinate_reference')
    #--- End: def

    @property
    def domain_axes(self):
        '''Return domain axis constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`

:Returns:

    `Constructs`
        The domain axis constructs and their construct keys.

**Examples:**

>>> f.domain_axes
Constructs:
{}

>>> f.domain_axes
Constructs:
{'domainaxis0': <DomainAxis: size(1)>,
 'domainaxis1': <DomainAxis: size(10)>,
 'domainaxis2': <DomainAxis: size(9)>,
 'domainaxis3': <DomainAxis: size(1)>}

        '''
        return self.constructs.filter_by_type('domain_axis')
    #--- End: def

    @property
    def auxiliary_coordinates(self):
        '''Return auxiliary coordinate constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`

:Returns:

    `Constructs`
        The auxiliary coordinate constructs and their construct keys.

**Examples:**

>>> f.auxiliary_coordinates
Constructs:
{}

>>> f.auxiliary_coordinates
Constructs:
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
 'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:Grid latitude name(10) >}

        '''
        return self.constructs.filter_by_type('auxiliary_coordinate')
    #--- End: def

    @property
    def dimension_coordinates(self):
        '''Return dimension coordinate constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`

:Returns:

    `Constructs`
        The dimension coordinate constructs and their construct keys.

**Examples:**

>>> f.dimension_coordinates
Constructs:
{}

>>> f.dimension_coordinates
Constructs:
{'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
 'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

        '''
        return self.constructs.filter_by_type('dimension_coordinate')
    #--- End: def
    
    @property
    def coordinates(self):
        '''Return dimension and auxiliary coordinate constructs.

.. versionadded:: 1.7.0

.. seealso:: `auxiliary_coordinates`, `constructs`,
             `dimension_coordinates`

:Returns:

    `Constructs`
        The auxiliary coordinate and dimension coordinate constructs
        and their construct keys.

**Examples:**

>>> f.coordinates
Constructs:
{}

>>> f.coordinates
Constructs:
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
 'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name=Grid latitude name(10) >,
 'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
 'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}

        '''
        out = self.dimension_coordinates
        out._update(self.auxiliary_coordinates)        
        return out
    #--- End: def

    @property
    def domain_ancillaries(self):
        '''Return domain ancillary constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`

:Returns:

    `Constructs`
        The domain ancillary constructs and their construct keys.

**Examples:**

>>> f.domain_ancillaries
Constructs:
{}

>>> f.domain_ancillaries
Constructs:
{'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
 'domainancillary1': <DomainAncillary: ncvar%b(1) >,
 'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>}

        '''
        return self.constructs.filter_by_type('domain_ancillary')
    #--- End: def

    @property
    def cell_measures(self):
        '''Return cell measure constructs.

.. versionadded:: 1.7.0

.. seealso:: `constructs`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `Constructs`
        The cell measure constructs and their construct keys.

**Examples:**

>>> f.cell_measures
Constructs:
{}

>>> f.cell_measures
Constructs:
{'cellmeasure0': <CellMeasure: measure%area(9, 10) km2>}

        '''
        return self.constructs.filter_by_type('cell_measure')
    #--- End: def

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def construct(self, identity, default=ValueError()):
        '''Select a metadata construct by its identity.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `Constructs.filter_by_identity`,
             `Constructs.value`

:Parameters:

    identity: optional

        Select constructs that have the given identity. If exactly one
        construct is selected then it is returned, otherwise an
        exception is raised.

        The identity is specified by a string (e.g. ``'latitude'``,
        ``'long_name=time'``, etc.); or a compiled regular expression
        (e.g. ``re.compile('^atmosphere')``), for which all constructs
        whose identities match (via `re.search`) are selected.

        Each construct has a number of identities, and is selected if
        any of them match any of those provided. A construct's
        identities are those returned by its `!identities` method. In
        the following example, the construct ``c`` has four
        identities:

           >>> c.identities()
           ['time', 'long_name=Time', 'foo=bar', 'ncvar%T']

        In addition, each construct also has an identity based its
        construct key (e.g. ``'key%dimensioncoordinate2'``)

        Note that the identifiers of metadata constructs in the output
        of a `print` or `!dump` call are always one of its identities,
        and so may always be used as the *identity* argument.

    default: optional
        Return the value of the *default* parameter if the property
        has not been set. If set to an `Exception` instance then it
        will be raised instead.

:Returns:

        The selected construct.

**Examples:**

>>> print(f.constructs)
Constructs:
{'cellmethod0': <CellMethod: area: mean>,
 'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>,
 'dimensioncoordinate1': <DimensionCoordinate: longitude(8) degrees_east>,
 'dimensioncoordinate2': <DimensionCoordinate: long_name=time(1) days since 2018-12-01 >,
 'domainaxis0': <DomainAxis: size(5)>,
 'domainaxis1': <DomainAxis: size(8)>,
 'domainaxis2': <DomainAxis: size(1)>}

Select the construct that has the "standard_name" property of 'latitude':

>>> f.construct('latitude')
<DimensionCoordinate: latitude(5) degrees_north>

Select the cell method construct that has a "method" of 'mean':

>>> f.construct('method:mean')
<CellMethod: area: mean>

Attempt to select the construct whose "standard_name" start with the
letter 'l':

>>> import re
>>> f.construct(re.compile('^l'))
ValueError: Can't return 2 constructs
>>> f.construct(re.compile('^l'), default='no construct')
'no construct'

        '''
        c = self.constructs.filter_by_identity(identity)
        if len(c) == 1:
            return c.value()

        if not c:
            return self._default(default, "Can't return zero constructs")

        return self._default(default, "Can't return {0} constructs".format(len(c)))
    #--- End: def
        
#--- End: class
