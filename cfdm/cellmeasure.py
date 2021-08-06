import logging

from . import core, mixin
from .decorators import _manage_log_level_via_verbosity

logger = logging.getLogger(__name__)


class CellMeasure(
    mixin.NetCDFVariable,
    mixin.NetCDFExternal,
    mixin.PropertiesData,
    core.CellMeasure,
):
    """A cell measure construct of the CF data model.

    A cell measure construct provides information that is needed about
    the size or shape of the cells and that depends on a subset of the
    domain axis constructs. Cell measure constructs have to be used
    when the size or shape of the cells cannot be deduced from the
    dimension or auxiliary coordinate constructs without special
    knowledge that a generic application cannot be expected to have.

    The cell measure construct consists of a numeric array of the
    metric data which spans a subset of the domain axis constructs,
    and properties to describe the data. The cell measure construct
    specifies a "measure" to indicate which metric of the space it
    supplies, e.g. cell horizontal areas, and must have a units
    property consistent with the measure, e.g. square metres. It is
    assumed that the metric does not depend on axes of the domain
    which are not spanned by the array, along which the values are
    implicitly propagated. CF-netCDF cell measure variables correspond
    to cell measure constructs.

    **NetCDF interface**

    {{netCDF variable}}

    {{netCDF global attributes}}

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        measure=None,
        properties=None,
        data=None,
        source=None,
        copy=True,
        _use_data=True,
    ):
        """**Initialisation**

        :Parameters:

            measure: `str`, optional
                Set the measure that indicates which metric given by
                the data array. Ignored if the *source* parameter is
                set.

                The measure may also be set after initialisation with
                the `set_measure` method.

                *Parameter example:*
                  ``measure='area'``

            {{init properties: `dict`, optional}}

               *Parameter example:*
                 ``properties={'standard_name': 'cell_area'}``

            {{init data: data_like, optional}}

            source: optional
                Initialise the measure, properties and data from those
                of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(
            measure=measure,
            properties=properties,
            data=data,
            source=source,
            copy=copy,
            _use_data=_use_data,
        )

        self._initialise_netcdf(source)

    def creation_commands(
        self,
        representative_data=False,
        namespace=None,
        indent=0,
        string=True,
        name="c",
        data_name="data",
        header=True,
    ):
        """Returns the commands to create the cell measure construct.

        .. versionadded:: (cfdm) 1.8.7.0

        .. seealso:: `{{package}}.Data.creation_commands`,
                     `{{package}}.Field.creation_commands`

        :Parameters:

            {{representative_data: `bool`, optional}}

            {{namespace: `str`, optional}}

            {{indent: `int`, optional}}

            {{string: `bool`, optional}}

            {{name: `str`, optional}}

            {{data_name: `str`, optional}}

            {{header: `bool`, optional}}

        :Returns:

            {{returns creation_commands}}

        **Examples:**

        >>> x = {{package}}.CellMeasure(
        ...     measure='area',
        ...     properties={'units': 'm2'}
        ... )
        >>> x.set_data([100345.5, 123432.3, 101556.8])
        >>> print(x.creation_commands(header=False))
        c = {{package}}.CellMeasure()
        c.set_properties({'units': 'm2'})
        data = {{package}}.Data([100345.5, 123432.3, 101556.8], units='m2', dtype='f8')
        c.set_data(data)
        c.set_measure('area')

        """
        out = super().creation_commands(
            representative_data=representative_data,
            indent=0,
            namespace=namespace,
            string=False,
            name=name,
            data_name=data_name,
            header=header,
        )

        measure = self.get_measure(None)
        if measure is not None:
            out.append(f"{name}.set_measure({measure!r})")

        if string:
            indent = " " * indent
            out[0] = indent + out[0]
            out = ("\n" + indent).join(out)

        return out

    def dump(
        self,
        display=True,
        _omit_properties=None,
        _key=None,
        _level=0,
        _title=None,
        _axes=None,
        _axis_names=None,
    ):
        """A full description of the cell measure construct.

        Returns a description of all properties, including those of
        components, and provides selected values of all data arrays.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        if _title is None:
            name = self.identity(default=self.get_property("units", ""))
            _title = f"Cell Measure: {name}"

        if self.nc_get_external():
            if not (self.has_data() or self.properties()):
                ncvar = self.nc_get_variable(None)
                if ncvar is not None:
                    ncvar = f"ncvar%{ncvar}"
                else:
                    ncvar = ""

                _title += f" (external variable: {ncvar})"

        return super().dump(
            display=display,
            _key=_key,
            _omit_properties=_omit_properties,
            _level=_level,
            _title=_title,
            _axes=_axes,
            _axis_names=_axis_names,
        )

    @_manage_log_level_via_verbosity
    def equals(
        self,
        other,
        rtol=None,
        atol=None,
        verbose=None,
        ignore_data_type=False,
        ignore_fill_value=False,
        ignore_properties=(),
        ignore_compression=True,
        ignore_type=False,
    ):
        """Whether two cell measure constructs are the same.

        Equality is strict by default. This means that:

        * the same descriptive properties must be present, with the same
          values and data types, and vector-valued properties must also have
          same the size and be element-wise equal (see the *ignore_properties*
          and *ignore_data_type* parameters), and

        ..

        * if there are data arrays then they must have same shape and data
          type, the same missing data mask, and be element-wise equal (see the
          *ignore_data_type* parameter).

        {{equals tolerance}}

        {{equals compression}}

        Any type of object may be tested but, in general, equality is only
        possible with another cell measure construct, or a subclass of
        one. See the *ignore_type* parameter.

        {{equals netCDF}}

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            other:
                The object to compare for equality.

            {{atol: number, optional}}

            {{rtol: number, optional}}

            {{ignore_fill_value: `bool`, optional}}

            {{verbose: `int` or `str` or `None`, optional}}

            ignore_properties: sequence of `str`, optional
                The names of properties to omit from the comparison.

            {{ignore_data_type: `bool`, optional}}

            {{ignore_compression: `bool`, optional}}

            {{ignore_type: `bool`, optional}}

        :Returns:

            `bool`
                Whether the two cell measure constructs are equal.

        **Examples:**

        >>> c = {{package}}.CellMeasure()
        >>> c.set_properties({'units': 'm2'})
        >>> c.equals(c)
        True
        >>> c.equals(c.copy())
        True
        >>> c.equals('not a cell measure')
        False

        >>> m = c.copy()
        >>> m.set_property('units', 'km2')
        >>> c.equals(m)
        False
        >>> c.equals(m, verbose=3)
        False
        >>> # Logs: CellMeasure: Different 'units' property values: 'm2', 'km2'

        """
        if not super().equals(
            other,
            rtol=rtol,
            atol=atol,
            verbose=verbose,
            ignore_data_type=ignore_data_type,
            ignore_fill_value=ignore_fill_value,
            ignore_properties=ignore_properties,
            ignore_compression=ignore_compression,
            ignore_type=ignore_type,
        ):
            return False

        measure0 = self.get_measure(None)
        measure1 = other.get_measure(None)
        if measure0 != measure1:
            logger.info(
                f"{self.__class__.__name__}: Different measure "
                f"({measure0} != {measure1})"
            )
            return False

        return True

    def identity(self, default=""):
        """Return the canonical identity.

        By default the identity is the first found of the following:

        * The measure, preceded by ``'measure:'``.
        * The ``standard_name`` property.
        * The ``cf_role`` property, preceded by 'cf_role='.
        * The ``long_name`` property, preceded by 'long_name='.
        * The netCDF variable name, preceded by 'ncvar%'.
        * The value of the default parameter.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `identities`

        :Parameters:

            default: optional
                If no identity can be found then return the value of the
                default parameter.

        :Returns:

                The identity.

        **Examples:**

        >>> f = {{package}}.example_field(1)
        >>> c = f.get_construct('cellmeasure0')
        >>> c.get_measure()
        'area'

        >>> c.properties()
        {'units': 'km2'}
        >>> c.nc_get_variable()
        'cell_measure'
        >>> c.identity(default='no identity')
        'measure:area'

        >>> c.del_measure()
        'area'
        >>> c.identity()
        'ncvar%cell_measure'
        >>> c.nc_del_variable()
        'cell_measure'
        >>> c.identity()
        ''
        >>> c.identity(default='no identity')
        'no identity'

        """
        n = self.get_measure(None)
        if n is not None:
            return f"measure:{n}"

        n = self.get_property("standard_name", None)
        if n is not None:
            return n

        for prop in ("cf_role", "long_name"):
            n = self.get_property(prop, None)
            if n is not None:
                return f"{prop}={n}"

        n = self.nc_get_variable(None)
        if n is not None:
            return f"ncvar%{n}"

        return default

    def identities(self, generator=False, **kwargs):
        """Return all possible identities.

        The identities comprise:

        * The measure property, preceded by ``'measure:'``.
        * The ``standard_name`` property.
        * All properties, preceded by the property name and a colon,
          e.g. ``'long_name:Air temperature'``.
        * The netCDF variable name, preceded by ``'ncvar%'``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `identity`

        :Parameters:

            generator: `bool`, optional
                If True then return a generator for the identities,
                rather than a list.

                .. versionadded:: (cfdm) 1.8.9.0

            kwargs: optional
                Additional configuration parameters. Currently
                none. Unrecognised parameters are ignored.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `list` or generator
                The identities.

        **Examples:**

        >>> f = {{package}}.example_field(1)
        >>> c = f.get_construct('cellmeasure0')
        >>> c.get_measure()
        'area'

        >>> c.properties()
        {'units': 'km2'}
        >>> c.nc_get_variable()
        'cell_measure'
        >>> c.identities()
        ['measure:area', 'units=km2', 'ncvar%cell_measure']
        >>> for i in c.identities(generator=True):
        ...     print(i)
        ...
        measure:area
        units=km2
        ncvar%cell_measure

        """
        measure = self.get_measure(None)
        if measure is not None:
            pre = ((f"measure:{measure}",),)
            pre0 = kwargs.pop("pre", None)
            if pre0:
                pre = tuple(pre0) + pre

            kwargs["pre"] = pre

        return super().identities(generator=generator, **kwargs)
