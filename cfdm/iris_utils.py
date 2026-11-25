"""Utilities for conversion to and from iris."""


def from_iris(c):
    """Convert `iris` cubes to CF field constructs.

    `cfdm.from_iris` is an in-memory operation which does two things:
    it maps the `iris` cubes onto CF constructs; and it copies
    pointers to the arrays describing the actual data, from the `iris`
    dataset to the fields or domains. No actual data is copied.

    :Method:

    The conversion is a three-step process: `iris` cubes are mapped to
    an `ncdata.NcData` dataset-level container, which is mapped to an
    `xarray` dataset, which is mapped to CF fields. I.e. ``f =
    cfdm.from_iris(c)`` is exactly equivalent to::

    >>> from ncdata.iris import from_iris as ncdata_from_iris
    >>> from ncdata.xarray import to_xarray as ncdata_to_xarray
    >>> n = ncdata_from_iris(c)
    >>> ds = ncdata_to_xarray(n)
    >>> f = cfdm.from_xarray(ds)

    .. versionadded:: 1.13.4.0

    .. seealso:: `cfdm.to_iris`, `cfdm.to_xarray`, `cfdm.from_xarray`

    :Parameters:

        c: (sequence of) `iris.cube.Cube`
            The `iris.cube.Cube` objects to be converted.

    :Returns:

        sequence of `Field`
            The equivalent CF fields.

    :Examples:

    Create some field constructs, convert them to `iris` cubes, and
    convert the `iris` cubes back to field constructs.

    >>> f = cfdm.example_fields(0, 7)
    >>> f
    [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
     <Field: eastward_wind(time(3), air_pressure(1), grid_latitude(4), grid_longitude(5)) m s-1>]
    >>> c = cfdm.to_iris(f)
    >>> c
    [<iris 'Cube' of eastward_wind / (m s-1) (time: 3; air_pressure: 1; grid_latitude: 4; grid_longitude: 5)>,
    <iris 'Cube' of specific_humidity / (1) (latitude: 5; longitude: 8)>]
    >>> g = cfdm.from_iris(c)
    >>> g
    [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
     <Field: eastward_wind(time(3), air_pressure(1), grid_latitude(4), grid_longitude(5)) m s-1>]

    """
    try:
        import ncdata  # noqa: F401
    except ImportError as e:
        raise ImportError(
            f"{e}. Must install ncdata (https://pypi.org/project/ncdata) "
            "to allow conversions to and from iris cubes"
        )

    try:
        from ncdata.iris import from_iris
    except ImportError as e:
        raise ImportError(
            f"{e}. Must install scitools-iris "
            "(https://pypi.org/project/scitools-iris/) "
            "to allow conversions to and from iris cubes"
        )

    try:
        from ncdata.xarray import to_xarray
    except ImportError as e:
        raise ImportError(
            f"{e}. Must install xarray "
            "to allow conversions to and from iris cubes"
        )

    from cfdm import from_xarray

    n = from_iris(c)
    ds = to_xarray(n)
    return from_xarray(ds)


def to_iris(f):
    """Convert CF field constructs to `iris` cubes.

    `cfdm.to_iris` is an in-memory operation which does two things: it
    maps the CF constructs onto `iris` cubes; and it copies pointers
    to the arrays describing the actual data, from the fields to the
    `iris` cubes. No actual data is copied.

    :Method:

    The conversion is a three-step process: CF fields are mapped to an
    `xarray` dataset, which is mapped to an `ncdata.NcData`
    dataset-level container, which is mapped to `iris` cubes. I.e. ``c
    = cfdm.to_iris(f)`` is exactly equivalent to::

    >>> from ncdata.xarray import from_xarray as ncdata_from_xarray
    >>> from ncdata.iris import to_iris as ncdata_to_iris
    >>> ds = cfdm.to_xarray(f)
    >>> n = ncdata_from_xarray(ds)
    >>> c = ncdata_to_iris(n)

    .. versionadded:: 1.13.4.0

    .. seealso:: `cfdm.from_iris`, `cfdm.to_xarray`, `cfdm.from_xarray`

    :Parameters:

        f: (sequence of) `Field`
            The CF fields to be converted.

    :Returns:

        `iris.cube.CubeList`
            The equivalent `iris.cube.Cube` objects.

    :Examples:

    Create some field constructs, convert them to `iris` cubes, and
    convert the `iris` cubes back to field constructs.

    >>> f = cfdm.example_fields(0, 7)
    >>> f
    [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
     <Field: eastward_wind(time(3), air_pressure(1), grid_latitude(4), grid_longitude(5)) m s-1>]
    >>> c = cfdm.to_iris(f)
    >>> c
    [<iris 'Cube' of eastward_wind / (m s-1) (time: 3; air_pressure: 1; grid_latitude: 4; grid_longitude: 5)>,
    <iris 'Cube' of specific_humidity / (1) (latitude: 5; longitude: 8)>]
    >>> g = cfdm.from_iris(c)
    >>> g
    [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
     <Field: eastward_wind(time(3), air_pressure(1), grid_latitude(4), grid_longitude(5)) m s-1>]

    """
    try:
        import ncdata  # noqa: F401
    except ImportError as e:
        raise ImportError(
            f"{e}. Must install ncdata (https://pypi.org/project/ncdata) "
            "to allow conversions to and from iris cubes"
        )

    try:
        from ncdata.iris import to_iris
    except ImportError as e:
        raise ImportError(
            f"{e}. Must install scitools-iris "
            "(https://pypi.org/project/scitools-iris/) "
            "to allow conversions to and from iris cubes"
        )

    try:
        from ncdata.xarray import from_xarray
    except ImportError as e:
        raise ImportError(
            f"{e}. Must install xarray "
            "to allow conversions to and from iris cubes"
        )

    from cfdm import to_xarray

    ds = to_xarray(f)
    n = from_xarray(ds)
    return to_iris(n)
