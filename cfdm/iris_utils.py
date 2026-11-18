"""Utitlities for conversion to and from iris."""


def from_iris(ds):
    """Convert `iris` cubes to CF field constructs.

    `cfdm.from_iris` is an entirely in-memory operation which does two
    things: it maps the `iris` cubes onto CF constructs; and it copies
    pointers to the arrays describing the actual data, from the
    `iris` dataset to the fields or domains. No actual data is
    copied.

    :Method:

    The conversion is a three-step process: `iris` cubes to an
    `ncdata.NcData` dataset-level container, to an `xarray` dataset,
    to CF fields. ``f = cfdm.from_iris(c)`` is exactly equivalent
    to::

    >>> from ncdata.iris import from_iris
    >>> from ncdata.xarray import to_xarray
    >>> n = from_iris(c)
    >>> ds = to_xarray(n)
    >>> f = cfdm.from_xarray(ds)

    .. versionadded:: NEXTVERSION

    .. seealso:: `cfdm.to_iris`, `cfdm.to_xarray`, `cfdm.from_xarray`

    :Parameters:

        ds: (sequence of) `iris.cube.Cube`
            The `iris.cube.Cube` objects to be converted.

    :Returns:

        sequence of `Field`
            The equivalent CF fields.

    :Examples:

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
            f"{e}. Must install iris "
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

    n = from_iris(ds)
    ds = to_xarray(n)
    return from_xarray(ds)


def to_iris(f):
    """Convert CF field constructs to `iris` cubes.

    `cfdm.to_iris` is an entirely in-memory operation which does two
    things: it maps the CF constructs onto `iris` cubes; and it copies
    pointers to the arrays describing the actual data, from the fields
    to the `iris` cubes. No actual data is copied.

    :Method:

    The conversion is a three-step process: CF fields to an `xarray`
    dataset, to an `ncdata.NcData` dataset-level container, to `iris`
    cubes. ``c = cfdm.to_iris(f)`` is exactly equivalent to::

    >>> from ncdata.xarray import from_xarray
    >>> from ncdata.iris import to_iris
    >>> ds = cfdm.to_xarray(f)
    >>> n = from_xarray(ds)
    >>> c = to_iris(n)

    .. versionadded:: NEXTVERSION

    .. seealso:: `cfdm.from_iris`, `cfdm.to_xarray`, `cfdm.from_xarray`

    :Parameters:

        f: (sequence of) `Field`
            The CF fields to be converted.

    :Returns:

        `iris.cube.CubeList`
            The equivalent `iris.cube.Cube` objects.

    :Examples:

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
            f"{e}. Must install iris "
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
