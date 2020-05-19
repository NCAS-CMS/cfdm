from builtins import super
from past.builtins import basestring

from . import abstract
from . import mixin

from . import Constructs


class Field(mixin.ConstructAccess, abstract.PropertiesData):
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
    coordinate reference and domain ancillary constructs. All of the
    constructs contained by the field construct are optional.

    The field construct also has optional properties to describe
    aspects of the data that are independent of the domain. These
    correspond to some netCDF attributes of variables (e.g. units,
    long_name and standard_name), and some netCDF global file
    attributes (e.g. history and institution).

    .. versionadded:: 1.7.0

    '''
    # ----------------------------------------------------------------
    # Define the base of the identity keys for each construct type
    # ----------------------------------------------------------------
    _construct_key_base = {'auxiliary_coordinate': 'auxiliarycoordinate',
                           'cell_measure'        : 'cellmeasure',
                           'cell_method'         : 'cellmethod',
                           'coordinate_reference': 'coordinatereference',
                           'dimension_coordinate': 'dimensioncoordinate',
                           'domain_ancillary'    : 'domainancillary',
                           'domain_axis'         : 'domainaxis',
                           'field_ancillary'     : 'fieldancillary',
    }

    def __new__(cls, *args, **kwargs):
        '''This must be overridden in subclasses.

        '''
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        return instance

    def __init__(self, properties={}, source=None, copy=True,
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
        super().__init__(properties=properties, source=source,
                         copy=copy, _use_data=False)

        if source is not None:
            # Initialise constructs and the data from the source
            # parameter
            try:
                constructs = source.constructs
            except AttributeError:
                constructs = None

            try:
                data = source.get_data(default=None)
            except AttributeError:
                data = None

            try:
                data_axes = source.get_data_axes(default=None)
            except AttributeError:
                data_axes = None

            if constructs is not None and (copy or not _use_data):
                constructs = constructs.copy(data=_use_data)
        else:
            constructs = None
            data       = None
            data_axes  = None

        if constructs is None:
            constructs = self._Constructs(**self._construct_key_base)

        self._set_component('constructs', constructs, copy=False)

        if data is not None and _use_data:
            self.set_data(data, data_axes, copy=copy)
        elif data_axes is not None:
            self.set_data_axes(data_axes)

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def construct_type(self):
        '''Return a description of the construct type.

    .. versionadded:: 1.7.0

    :Returns:

        `str`
            The construct type.

    **Examples:**

    >>> f.construct_type
    'field'

        '''
        return 'field'

    @property
    def constructs(self):
        '''Return the metdata constructs.

    .. versionadded:: 1.7.0

    :Returns:

        `Constructs`
            The constructs.

    **Examples:**

    >>> print(f.constructs)
    Constructs:
    {'cellmethod0': <CellMethod: area: mean>,
     'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>,
     'dimensioncoordinate1': <DimensionCoordinate: longitude(8) degrees_east>,
     'dimensioncoordinate2': <DimensionCoordinate: time(1) days since 2018-12-01 >,
     'domainaxis0': <DomainAxis: size(5)>,
     'domainaxis1': <DomainAxis: size(8)>,
     'domainaxis2': <DomainAxis: size(1)>}

        '''
        return self._get_component('constructs')

    @property
    def domain(self):
        '''Return the domain.

    ``f.domain`` is equivalent to ``f.get_domain()``

    .. versionadded:: 1.7.0

    .. seealso:: `get_domain`

    :Returns:

        `Domain`
            The domain.

    **Examples:**

    >>> d0 = f.domain
    >>> d1 = f.get_domain()
    >>> d0.equals(d1)
    True

        '''
        return self.get_domain()

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def del_data_axes(self, key=None, default=ValueError()):
        '''Remove the keys of the domain axis constructs spanned by the data
    of the field or of a metadata construct.

    .. versionadded:: 1.7.0

    .. seealso:: `get_data_axes`, `has_data_axes`, `set_data_axes`

    :Parameters:

        key: `str`, optional
            Specify a metadata construct, instead of the field
            construct.

            *Parameter example:*
              ``key='auxiliarycoordinate0'``

        default: optional
            Return the value of the *default* parameter if the data
            axes have not been set. If set to an `Exception` instance
            then it will be raised instead.

    :Returns:

        `tuple`
            The removed keys of the domain axis constructs spanned by
            the data.

    **Examples:**

    >>> f.del_data_axes()
    ('domainaxis0', 'domainaxis1')

    >>> f.del_data_axes(key='dimensioncoordinate2')
    ('domainaxis1',)

    >>> f.has_data_axes()
    False
    >>> f.has_data_axes(default='no axes')
    'no axes'

        '''
        if key is not None:
            return super().del_data_axes(key, default=default)

        try:
            return self._del_component('data_axes')
        except ValueError:
            return self._default(default,
              "{!r} has no data axes".format(self.__class__.__name__))

    def get_domain(self):
        '''Return the domain.

    .. versionadded:: 1.7.0

    .. seealso:: `domain`

    :Returns:

        `Domain`
             The domain.

    **Examples:**

    >>> d = f.get_domain()

        '''
        return self._Domain.fromconstructs(self.constructs)

    def get_data_axes(self, key=None, default=ValueError()):
        '''Return the keys of the domain axis constructs spanned by the data
    of the field or of a metadata construct.

    .. versionadded:: 1.7.0

    .. seealso:: `del_data_axes`, `get_data`, `set_data_axes`

    :Parameters:

        key: `str`, optional
            Specify a metadata construct, instead of the field
            construct.

            *Parameter example:*
              ``key='auxiliarycoordinate0'``

        default: optional
            Return the value of the *default* parameter if the data
            axes have not been set. If set to an `Exception` instance
            then it will be raised instead.

    :Returns:

        `tuple`
            The keys of the domain axis constructs spanned by the
            data.

    **Examples:**

    >>> f.get_data_axes()
    ('domainaxis0', 'domainaxis1')

    >>> f.get_data_axes('dimensioncoordinate2')
    ('domainaxis1',)

    >>> f.has_data_axes()
    False
    >>> f.get_data_axes(default='no axes')
    'no axes'

        '''
        if key is not None:
            return super().get_data_axes(key, default=default)

        try:
            return self._get_component('data_axes')
        except ValueError:
            return self._default(default,
              "{!r} has no data axes".format(self.__class__.__name__))

    def has_data_axes(self, key=None):
        '''Whether the domain axis constructs spanned by the data of the field
    or of a metadata construct have been set.

    .. versionadded:: 1.7.0

    .. seealso:: `del_data_axes`, `get_data_axes`, `set_data_axes`

    :Parameters:

        key: `str`, optional
            Specify a metadata construct, instead of the field
            construct.

            *Parameter example:*
              ``key='domainancillary1'``

    :Returns:

        `bool`
            True if domain axis constructs that span the data been
            set, otherwise False.

    **Examples:**

    >>> f.has_data_axes()
    True

    >>> f.has_data_axes(key='auxiliarycoordinate2')
    False

        '''
        axes = self.get_data_axes(key, default=None)
        if axes is None:
            return False

        return True

    def del_construct(self, key, default=ValueError()):
        '''Remove a metadata construct.

    If a domain axis construct is selected for removal then it can't
    be spanned by any data arrays of the field nor metadata
    constructs, nor be referenced by any cell method
    constructs. However, a domain ancillary construct may be removed
    even if it is referenced by coordinate reference construct.

    .. versionadded:: 1.7.0

    .. seealso:: `get_construct`, `constructs`, `has_construct`,
                 `set_construct`

    :Parameters:

        key: `str`
            The construct identifier of the metadata construct to be
            removed.

            *Parameter example:*
              ``key='auxiliarycoordinate0'``

        default: optional
            Return the value of the *default* parameter if the data
            axes have not been set. If set to an `Exception` instance
            then it will be raised instead.

    :Returns:

            The removed metadata construct.

    **Examples:**


    >>> f.del_construct('auxiliarycoordinate2')
    <AuxiliaryCoordinate: latitude(111, 106) degrees_north>
    >>> f.del_construct('auxiliarycoordinate2')
    ValueError: Can't get remove non-existent construct
    >>> f.del_construct('auxiliarycoordinate2', default=False)
    False

        '''
        if key in self.domain_axes and key in self.get_data_axes(default=()):
            raise ValueError(
                "Can't remove domain axis {!r} that is spanned by the data of the field construct".format(
                    key))

        return super().del_construct(key, default=default)

    def set_data(self, data, axes=None, copy=True):
        '''Set the data of the field construct.

    The units, calendar and fill value properties of the data object
    are removed prior to insertion.

    .. versionadded:: 1.7.0

    .. seealso:: `del_data`, `get_data`, `has_data`, `set_data_axes`

    :Parameters:

        data: `Data`
            The data to be inserted.

        axes: (sequence of) `str`, or `None`
            The identifiers of the domain axes spanned by the data
            array. If `None` then the data axes are not set.

            The axes may also be set afterwards with the
            `set_data_axes` method.

            *Parameter example:*
              ``axes=['domainaxis2']``

            *Parameter example:*
              ``axes='domainaxis2'``

            *Parameter example:*
              ``axes=['domainaxis2', 'domainaxis1']``

            *Parameter example:*
              ``axes=None``

        copy: `bool`, optional
            If False then do not copy the data prior to insertion. By
            default the data are copied.

    :Returns:

        `None`

    **Examples:**

    Set the domain axis constructs spanned by the data of the field
    construct:

    >>> d
    <Data(10, 9): [[23.6, ..., 76.8]]>
    >>> f.set_data(d, axes=['domainaxis0', 'domainaxis1'])
    >>> f.set_data(d)

        '''
        if axes is None:
            existing_axes = self.get_data_axes(default=None)
            if existing_axes is not None:
                self.set_data_axes(axes=existing_axes, _shape=data.shape)
        else:
            self.set_data_axes(axes=axes, _shape=data.shape)

        super().set_data(data, copy=copy)

    def set_data_axes(self, axes, key=None, _shape=None):
        '''Set the domain axis constructs spanned by the data of the field or
    of a metadata construct.

    .. versionadded:: 1.7.0

    .. seealso:: `del_data_axes`, `get_data`, `get_data_axes`,
                 `has_data_axes`

    :Parameters:

         axes: sequence of `str`
            The identifiers of the domain axis constructs spanned by
            the data of the field or of a metadata construct.

            *Parameter example:*
              ``axes='domainaxis1'``

            *Parameter example:*
              ``axes=['domainaxis1']``

            *Parameter example:*
              ``axes=['domainaxis1', 'domainaxis0']``

         key: `str`, optional
            Specify a metadata construct, instead of the field
            construct.

            *Parameter example:*
              ``key='domainancillary1'``

    :Returns:

        `None`

    **Examples:**

    Set the domain axis constructs spanned by the data of the field
    construct:

    >>> f.set_data_axes(['domainaxis0', 'domainaxis1'])

    Set the domain axis constructs spanned by the data of a metadata
    construct:

    >>> f.set_data_axes(['domainaxis1'], key='dimensioncoordinate1')

        '''
        if isinstance(axes, basestring):
            axes = (axes,)

        if key is not None:
            return super().set_data_axes(axes=axes, key=key)

        if _shape is None:
            data = self.get_data(None)
            if data is not None:
                _shape = data.shape
        # --- End: if

        if _shape is not None:
            domain_axes = self.constructs.filter_by_type('domain_axis')
            axes_shape = []
            for axis in axes:
                if axis not in domain_axes:
                    raise ValueError(
                        "Can't set field construct data axes: Domain axis {!r} doesn't exist".format(
                            axis))

                axes_shape.append(domain_axes[axis].get_size())

            if _shape != tuple(axes_shape):
                raise ValueError(
                    "Can't set field construct data axes: Data array shape of {!r} does not match the shape of the given domain axes {}: {}".format(
                        _shape, tuple(axes), tuple(axes_shape)))
        # --- End: if

        axes = tuple(axes)
        self._set_component('data_axes', axes, copy=False)

        self.constructs._field_data_axes = axes

# --- End: class
