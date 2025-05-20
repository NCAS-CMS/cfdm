"""General functions useful for `Data` functionality."""

from functools import lru_cache, partial
from itertools import product

import cftime
import dask.array as da
import numpy as np
from dask.core import flatten

from ..units import Units

_default_calendar = "standard"


def allclose(x, y, masked_equal=True, rtol=None, atol=None):
    """An effective dask.array.ma.allclose method.

    True if two dask arrays are element-wise equal within a tolerance.

    Equivalent to allclose except that masked values are treated as
    equal (default) or unequal, depending on the masked_equal
    argument.

    Define an effective da.ma.allclose method here because one is
    currently missing in the Dask codebase.

    Note that all default arguments are the same as those provided to
    the corresponding NumPy method (see the `numpy.ma.allclose` API
    reference).

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        x: a dask array to compare with y

        y: a dask array to compare with x

        masked_equal: `bool`, optional
            Whether masked values in a and b are considered equal
            (True) or not (False). They are considered equal by
            default.

        {{rtol: number, optional}}

        {{atol: number, optional}}

    :Returns:

        `bool`
            A Boolean value indicating whether or not the two dask
            arrays are element-wise equal to the given *rtol* and
            *atol* tolerance.

    """
    if rtol is None or atol is None:
        raise ValueError(
            "Must provide numeric values for the rtol and atol keywords"
        )

    # Must pass rtol=rtol, atol=atol in as kwargs to allclose, rather than it
    # using those in local scope from the outer function arguments, because
    # Dask's internal algorithms require these to be set as parameters.
    def allclose(a_blocks, b_blocks, rtol=rtol, atol=atol):
        """Run `ma.allclose` across multiple blocks over two arrays."""
        result = True
        # Handle scalars, including 0-d arrays, for which a_blocks and
        # b_blocks will have the corresponding type and hence not be iterable.
        # With this approach, we avoid inspecting sizes or lengths, and for
        # the 0-d array blocks the following iteration can be used unchanged
        # and will only execute once with block sizes as desired of:
        # (np.array(<int size>),)[0] = array(<int size>). Note
        # can't check against more general case of collections.abc.Iterable
        # because a 0-d array is also iterable, but in practice always a list.
        if not isinstance(a_blocks, list):
            a_blocks = (a_blocks,)
        if not isinstance(b_blocks, list):
            b_blocks = (b_blocks,)

        # Note: If a_blocks or b_blocks has more than one chunk in
        #       more than one dimension they will comprise a nested
        #       sequence of sequences, that needs to be flattened so
        #       that we can safely iterate through the actual numpy
        #       array elements.

        for a, b in zip(flatten(a_blocks), flatten(b_blocks)):
            result &= np.ma.allclose(
                a, b, masked_equal=masked_equal, rtol=rtol, atol=atol
            )

        return result

    axes = tuple(range(x.ndim))
    return da.blockwise(
        allclose, "", x, axes, y, axes, dtype=bool, rtol=rtol, atol=atol
    )


def collapse(
    func,
    d,
    axis=None,
    keepdims=True,
    split_every=None,
):
    """Collapse data in-place using a given funcion.

     .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        func: callable
            The function that collapses the underlying `dask` array of
            *d*. Must have the minimum signature (parameters and
            default values) ``func(dx, axis=None, keepdims=False,
            mtol=None, split_every=None)``, where ``dx`` is a the dask
            array contained in *d*.

        d: `Data`
            The data to be collapsed.

        axis: (sequence of) int, optional
            The axes to be collapsed. By default all axes are
            collapsed, resulting in output with size 1. Each axis is
            identified by its integer position. If *axes* is an empty
            sequence then the collapse is applied to each scalar
            element and the reuslt has the same shape as the input
            data.

        keepdims: `bool`, optional
            By default, the axes which are collapsed are left in the
            result as dimensions with size one, so that the result
            will broadcast correctly against the input array. If set
            to False then collapsed axes are removed from the data.

        split_every: `int` or `dict`, optional
            Determines the depth of the recursive aggregation. See
            `dask.array.reduction` for details.

    :Returns:

        `Data`
            The collapsed data.

    """
    dx = d.to_dask_array()
    original_shape = dx.shape

    # Parse the axes. By default flattened input is used.
    if axis is None:
        iaxes = tuple(range(dx.ndim))
    else:
        try:
            iaxes = d._parse_axes(axis)
        except ValueError as error:
            raise ValueError(f"Can't min data: {error}")

    dx = func(dx, axis=iaxes, keepdims=keepdims, split_every=split_every)
    d._set_dask(dx)

    # Remove collapsed axis identifiers
    if iaxes and not keepdims:
        d._axes = [axis for i, axis in enumerate(d._axes) if i not in iaxes]

    # Update the dataset chunking strategy
    chunksizes = d.nc_dataset_chunksizes()
    if (
        chunksizes
        and isinstance(chunksizes, tuple)
        and dx.shape != original_shape
    ):
        if not keepdims:
            chunksizes = [
                size for i, size in enumerate(chunksizes) if i not in iaxes
            ]

        d.nc_set_dataset_chunksizes(chunksizes)

    return d


def is_numeric_dtype(array):
    """True if the given array is of a numeric or boolean data type.

    .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            array: numpy-like array

        :Returns:

            `bool`
                Whether or not the array holds numeric elements.

    **Examples**

    >>> a = np.array([0, 1, 2])
    >>> cfdm.data.utils.is_numeric_dtype(a)
    True
    >>> a = np.array([False, True, True])
    >>> cfdm.data.utils.is_numeric_dtype(a)
    True
    >>> a = np.array(["a", "b", "c"], dtype="S1")
    >>> cfdm.data.utils.is_numeric_dtype(a)
    False
    >>> a = np.ma.array([10.0, 2.0, 3.0], mask=[1, 0, 0])
    >>> cfdm.data.utils.is_numeric_dtype(a)
    True
    >>> a = np.array(10)
    >>> cfdm.data.utils.is_numeric_dtype(a)
    True
    >>> a = np.empty(1, dtype=object)
    >>> cfdm.data.utils.is_numeric_dtype(a)
    False

    """
    dtype = array.dtype

    # This checks if the dtype is either a standard "numeric" type
    # (i.e. int types, floating point types or complex floating point
    # types) or Boolean, which are effectively a restricted int type
    # (0 or 1). We determine the former by seeing if it sits under the
    # 'np.number' top-level dtype in the NumPy dtype hierarchy; see
    # the 'Hierarchy of type objects' figure diagram under:
    # https://numpy.org/doc/stable/reference/arrays.scalars.html#scalars
    return np.issubdtype(dtype, np.number) or np.issubdtype(dtype, np.bool_)


def convert_to_datetime(a, units):
    """Convert a dask array of numbers to one of date-time objects.

    .. versionadded:: (cfdm) 1.11.2.0

    .. seealso `convert_to_reftime`

    :Parameters:

        a: `dask.array.Array`
            The input numeric reference time values.

        units: `Units`
            The reference time units that define the output
            date-time objects.

    :Returns:

        `dask.array.Array`
            A new dask array containing date-time objects.

    **Examples**

    >>> import dask.array as da
    >>> d = da.from_array(2.5)
    >>> e = cfdm.data.utils.convert_to_datetime(d, cfdm.Units("days since 2000-12-01"))
    >>> print(e.compute())
    2000-12-03 12:00:00

    """
    return a.map_blocks(
        partial(rt2dt, units_in=units),
        dtype=object,
        meta=np.array((), dtype=object),
    )


def convert_to_reftime(a, units=None, first_value=None):
    """Convert date-times to floating point reference times.

    .. versionadded:: (cfdm) 1.11.2.0

    .. seealso `convert_to_datetime`

    :Parameters:

        a: `dask.array.Array`
            An array of string or object date-times

        units: `Units`, optional
            Specify the units for the output reference time values. By
            default the units are inferred from the first non-missing
            value in the array, or set to ``<Units: days since
            1970-01-01 gregorian>`` if all values are missing.

        first_value: optional
            If set, then assumed to be equal to the first non-missing
            value of the array, thereby removing the need to find it
            by inspection of *a*, which may be expensive. By default
            the first non-missing value is found from *a*.

    :Returns:

        (`dask.array.Array`, `Units`)
            The reference times, and their units.

    >>> import dask.array as da
    >>> d = da.from_array(2.5)
    >>> e = cfdm.data.utils.convert_to_datetime(d, Units("days since 2000-12-01"))

    >>> f, u = cfdm.data.utils.convert_to_reftime(e)
    >>> f.compute()
    0.5
    >>> u
    <Units: days since 2000-12-3 standard>

    >>> f, u = cfdm.data.utils.convert_to_reftime(e, Units("days since 1999-12-01"))
    >>> f.compute()
    368.5
    >>> u
    <Units: days since 1999-12-01 standard>

    """
    kind = a.dtype.kind
    if kind in "US":
        # Convert date-time strings to reference time floats
        if not units:
            first_value = first_non_missing_value(a, cached=first_value)
            if first_value is not None:
                YMD = str(first_value).partition("T")[0]
            else:
                YMD = "1970-01-01"

            units = Units(
                "days since " + YMD,
                getattr(units, "calendar", _default_calendar),
            )

        a = a.map_blocks(
            partial(st2rt, units_in=units, units_out=units), dtype=float
        )

    elif kind == "O":
        # Convert date-time objects to reference time floats
        first_value = first_non_missing_value(a, cached=first_value)
        if first_value is not None:
            x = first_value
        else:
            x = cftime.DatetimeGregorian(1970, 1, 1)

        x_since = "days since " + "-".join(map(str, (x.year, x.month, x.day)))
        x_calendar = getattr(x, "calendar", "standard")

        d_calendar = getattr(units, "calendar", None)
        d_units = getattr(units, "units", None)

        if x_calendar != "":
            if not units:
                d_calendar = x_calendar
            elif not units.equivalent(Units(x_since, x_calendar)):
                raise ValueError(
                    "Incompatible units: "
                    f"{units!r}, {Units(x_since, x_calendar)!r}"
                )

        if not units:
            # Set the units to something that is (hopefully) close to
            # all of the datetimes, in an attempt to reduce errors
            # arising from the conversion to reference times
            units = Units(x_since, calendar=d_calendar)
        else:
            units = Units(d_units, calendar=d_calendar)

        # Convert the date-time objects to reference times
        a = a.map_blocks(dt2rt, units_out=units, dtype=float)

    if not units.isreftime:
        raise ValueError(
            f"Can't create a reference time array with units {units!r}"
        )

    return a, units


def first_non_missing_value(a, cached=None, method="index"):
    """Return the first non-missing value of a dask array.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        a: `dask.array.Array`
            The array to be inspected.

        cached: scalar, optional
            If set to a value other than `None`, then return without
            inspecting the array. This allows a previously found first
            value to be used instead of a potentially costly array
            access.

        method: `str`, optional
            Select the method used to find the first non-missing
            value.

            The default ``'index'`` method evaulates sequentially the
            elements of the flattened array and returns when the first
            non-missing value is found.

            The ``'mask'`` method finds the first non-missing value of
            the flattened array as that which has the same location as
            the first `False` element of the flattened array mask.

            It is considered likely that the ``'index'`` method is
            fastest for data for which the first element is not
            missing, but this may not always be the case.

    :Returns:

            If set, then *cached* is returned. Otherwise returns the
            first non-missing value of *a*, or `None` if there isn't
            one.

    **Examples**

    >>> import dask.array as da
    >>> d = da.arange(8).reshape(2, 4)
    >>> print(d.compute())
    [[0 1 2 3]
     [4 5 6 7]]
    >>> cfdm.data.utils.first_non_missing_value(d)
    0
    >>> cfdm.data.utils.first_non_missing_value(d, cached=99)
    99
    >>> d[0, 0] = cfdm.masked
    >>> cfdm.data.utils.first_non_missing_value(d)
    1
    >>> d[0, :] = cfdm.masked
    >>> cfdm.data.utils.first_non_missing_value(d)
    4
    >>> cfdm.data.utils.first_non_missing_value(d, cached=99)
    99
    >>> d[...] = cfdm.masked
    >>> print(cfdm.data.utils.first_non_missing_value(d))
    None
    >>> print(cfdm.data.utils.first_non_missing_value(d, cached=99))
    99

    """
    if cached is not None:
        return cached

    if method == "index":
        shape = a.shape
        for i in range(a.size):
            index = np.unravel_index(i, shape)
            x = a[index].compute()
            if not (x is np.ma.masked or np.ma.getmask(x)):
                try:
                    return x.item()
                except AttributeError:
                    return x

        return

    if method == "mask":
        mask = da.ma.getmaskarray(a)
        if not a.ndim:
            # Scalar data
            if mask:
                return

            a = a.compute()
            try:
                return a.item()
            except AttributeError:
                return a

        x = a[da.unravel_index(mask.argmin(), a.shape)].compute()
        if x is np.ma.masked:
            return

        try:
            return x.item()
        except AttributeError:
            return x

    raise ValueError(f"Unknown value of 'method': {method!r}")


@lru_cache(maxsize=32)
def generate_axis_identifiers(n):
    """Return new axis identifiers for a given number of axes.

    The names are arbitrary and have no semantic meaning.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        n: `int`
            Generate this number of axis identifiers.

    :Returns:

        `list`
            The new axis identifiers.

    **Examples**

    >>> cfdm.data.creation.generate_axis_identifiers(0)
    []
    >>> cfdm.data.creation.generate_axis_identifiers(1)
    ['dim0']
    >>> cfdm.data.creation.generate_axis_identifiers(3)
    ['dim0', 'dim1', 'dim2']

    """
    return [f"dim{i}" for i in range(n)]


@lru_cache(maxsize=32)
def new_axis_identifier(existing_axes=(), basename="dim"):
    """Return a new, unique axis identifier.

    The name is arbitrary and has no semantic meaning.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        existing_axes: sequence of `str`, optional
            Any existing axis names that are not to be duplicated.

        basename: `str`, optional
            The root of the new axis identifier. The new axis
            identifier will be this root followed by an integer.

    :Returns:

        `str`
            The new axis idenfifier.

    **Examples**

    >>> cfdm.data.utils.new_axis_identifier()
    'dim0'
    >>> cfdm.data.utils.new_axis_identifier(['dim0'])
    'dim1'
    >>> cfdm.data.utils.new_axis_identifier(['dim3'])
    'dim1'
     >>> cfdm.data.utils.new_axis_identifier(['dim1'])
    'dim2'
    >>> cfdm.data.utils.new_axis_identifier(['dim1', 'dim0'])
    'dim2'
    >>> cfdm.data.utils.new_axis_identifier(['dim3', 'dim4'])
    'dim2'
    >>> cfdm.data.utils.new_axis_identifier(['dim2', 'dim0'])
    'dim3'
    >>> cfdm.data.utils.new_axis_identifier(['dim3', 'dim4', 'dim0'])
    'dim5'
    >>> cfdm.data.utils.new_axis_identifier(basename='axis')
    'axis0'
    >>> cfdm.data.utils.new_axis_identifier(basename='axis')
    'axis0'
    >>> cfdm.data.utils.new_axis_identifier(['dim0'], basename='axis')
    'axis1'
    >>> cfdm.data.utils.new_axis_identifier(['dim0', 'dim1'], basename='axis')
    'axis2'

    """
    n = len(existing_axes)
    axis = f"{basename}{n}"
    while axis in existing_axes:
        n += 1
        axis = f"{basename}{n}"

    return axis


def chunk_indices(chunks):
    """Return indices that define each dask chunk.

    .. versionadded:: (cfdm) 1.12.0.0

    .. seealso:: `chunks`

    :Parameters:

        chunks: `tuple`
            The chunk sizes along each dimension, as output by
            `dask.array.Array.chunks`.

    :Returns:

        `itertools.product`
            An iterator over tuples of indices of the data array.

    **Examples**

    >>> chunks = ((1, 2), (9,), (4, 5, 6)))
    >>> for index in cfdm.data.utils.chunk_indices():
    ...     print(index)
    ...
    (slice(0, 1, None), slice(0, 9, None), slice(0, 4, None))
    (slice(0, 1, None), slice(0, 9, None), slice(4, 9, None))
    (slice(0, 1, None), slice(0, 9, None), slice(9, 15, None))
    (slice(1, 3, None), slice(0, 9, None), slice(0, 4, None))
    (slice(1, 3, None), slice(0, 9, None), slice(4, 9, None))
    (slice(1, 3, None), slice(0, 9, None), slice(9, 15, None))

    """
    from dask.utils import cached_cumsum

    cumdims = [cached_cumsum(bds, initial_zero=True) for bds in chunks]
    indices = [
        [slice(s, s + dim) for s, dim in zip(starts, shapes)]
        for starts, shapes in zip(cumdims, chunks)
    ]
    return product(*indices)


def chunk_positions(chunks):
    """Find the position of each chunk.

    .. versionadded:: (cfdm) 1.11.2.0

    .. seealso:: `chunk_indices`, `chunk_locations`, `chunk_shapes`

    :Parameters:

        chunks: `tuple`
            The chunk sizes along each dimension, as output by
            `dask.array.Array.chunks`.

    **Examples**

    >>> chunks = ((1, 2), (9,), (4, 5, 6))
    >>> for position in cfdm.data.utils.chunk_positions(chunks):
    ...     print(position)
    ...
    (0, 0, 0)
    (0, 0, 1)
    (0, 0, 2)
    (1, 0, 0)
    (1, 0, 1)
    (1, 0, 2)

    """
    return product(*(range(len(bds)) for bds in chunks))


def chunk_shapes(chunks):
    """Find the shape of each chunk.

    .. versionadded:: (cfdm) 1.11.2.0

    .. seealso:: `chunk_indices`, `chunk_locations`, `chunk_positions`

    :Parameters:

        chunks: `tuple`
            The chunk sizes along each dimension, as output by
            `dask.array.Array.chunks`.

    **Examples**

    >>> chunks = ((1, 2), (9,), (4, 5, 6))
    >>> for shape in cfdm.data.utils.chunk_shapes(chunks):
    ...     print(shape)
    ...
    (1, 9, 4)
    (1, 9, 5)
    (1, 9, 6)
    (2, 9, 4)
    (2, 9, 5)
    (2, 9, 6)

    """
    return product(*chunks)


def chunk_locations(chunks):
    """Find the shape of each chunk.

    .. versionadded:: (cfdm) 1.11.2.0

    .. seealso:: `chunk_indices`, `chunk_positions`, `chunk_shapes`

    :Parameters:

        chunks: `tuple`
            The chunk sizes along each dimension, as output by
            `dask.array.Array.chunks`.

    **Examples**

    >>> chunks = ((1, 2), (9,), (4, 5, 6))
    >>> for location in cfdm.data.utils.chunk_locations(chunks):
    ...     print(location)
    ...
    ((0, 1), (0, 9), (0, 4))
    ((0, 1), (0, 9), (4, 9))
    ((0, 1), (0, 9), (9, 15))
    ((1, 3), (0, 9), (0, 4))
    ((1, 3), (0, 9), (4, 9))
    ((1, 3), (0, 9), (9, 15))

    """
    from dask.utils import cached_cumsum

    cumdims = [cached_cumsum(bds, initial_zero=True) for bds in chunks]
    locations = [
        [(s, s + dim) for s, dim in zip(starts, shapes)]
        for starts, shapes in zip(cumdims, chunks)
    ]
    return product(*locations)


def normalize_chunks(chunks, shape=None, dtype=None):
    """Normalize chunks to tuple of tuples.

    The shape may contain sizes of ``nan``. This could occur when the
    underlying data is compressed in a way which makes the shape
    impossible to infer without actually uncompressing the data.

    If *shape* contains no ``nan`` sizes then this function is
    identical to `dask.array.core.normalize_chunks`. If it does, then
    the output chunks for each such axis will be ``(nan,)``.

    .. versionadded (cfdm) 1.11.2.0

    :Parameters:

        chunks: tuple, int, dict, or string
            The chunks to be normalized. See
            `dask.array.core.normalize_chunks` for details.

        shape: `tuple`
            The shape of the data.

        dtype: data-type
            The data-type for the data.

    :Returns:

        `tuple`
            The normalized chunks.

    """
    from math import isnan, nan

    from dask.array.core import normalize_chunks

    if not any(map(isnan, shape)):
        return normalize_chunks(chunks, shape=shape, dtype=dtype)

    out = [
        (
            (nan,)
            if isnan(size)
            else normalize_chunks(chunk, shape=(size,), dtype=dtype)[0]
        )
        for chunk, size in zip(chunks, shape)
    ]
    return tuple(out)


def dt2rt(array, units_out):
    """Return numeric time values from datetime objects.

    .. versionadded:: (cfdm) 1.11.2.0

    .. seealso:: `rt2dt`

    :Parameters:

        array: numpy array-like of date-time objects
            The datetime objects must be in UTC with no time-zone
            offset.

        units_out: `Units`
            The units of the numeric time values. If there is a
            time-zone offset in *units_out*, it will be applied to the
            returned numeric values.

    :Returns:

        `numpy.ndarray`
            An array of numbers with the same shape as *array*.

    **Examples**

    >>> print(
    ...   cfdm.data.utils.dt2rt(
    ...     np.ma.array([0, cftime.DatetimeGregorian(2001, 11, 16, 12)], mask=[True, False]),
    ...     units_out=cfdm.Units('days since 2000-01-01')
    ...   )
    ... )
    [-- 685.5]

    """
    isscalar = not np.ndim(array)

    array = cftime.date2num(
        array, units=units_out.units, calendar=units_out._utime.calendar
    )

    if isscalar:
        if array is np.ma.masked:
            array = np.ma.masked_all(())
        else:
            array = np.asanyarray(array)

    return array


def rt2dt(array, units_in):
    """Convert reference times to date-time objects.

    .. versionadded:: (cfdm) 1.11.2.0

    The returned array is always independent.

    .. seealso:: `dt2rt`

    :Parameters:

        array: numpy array-like

        units_in: `Units`

    :Returns:

        `numpy.ndarray`
            An array of `cftime.datetime` objects with the same shape
            as *array*.

    **Examples**

    >>> print(
    ...   cfdm.data.utils.rt2dt(
    ...     np.ma.array([0, 685.5], mask=[True, False]),
    ...     units_in=cfdm.Units('days since 2000-01-01')
    ...   )
    ... )
    [--
     cftime.DatetimeGregorian(2001, 11, 16, 12, 0, 0, 0, has_year_zero=False)]

    """
    if not np.ndim(array) and np.ma.is_masked(array):
        # num2date has issues with scalar masked arrays with a True
        # mask
        return np.ma.masked_all((), dtype=object)

    units = units_in.units
    calendar = getattr(units_in, "calendar", "standard")

    if np.ma.isMA(array):
        # Note: We're going to apply `cftime.num2date` to a non-masked
        #       array and reset the mask afterwards, because numpy
        #       currently (numpy==2.2.3) has a bug that produces a
        #       RuntimeWarning: "numpy/ma/core.py:502: RuntimeWarning:
        #       invalid value encountered in cast fill_value =
        #       np.asarray(fill_value, dtype=ndtype)". See
        #       https://github.com/numpy/numpy/issues/28255 for more
        #       details.
        mask = array.mask
        array = np.array(array)
    else:
        mask = None

    array = cftime.num2date(
        array, units, calendar, only_use_cftime_datetimes=True
    )

    if not isinstance(array, np.ndarray):
        array = np.array(array, dtype=object)

    if mask is not None:
        array = np.ma.array(array, mask=mask)

    return array


def st2datetime(date_string, calendar=None):
    """Parse an ISO 8601 date-time string into a `cftime` object.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        date_string: `str`

    :Returns:

        `cftime.datetime`

    """
    if date_string.count("-") != 2:
        raise ValueError(
            "Input date-time string must contain at least a year, a month "
            "and a day"
        )

    x = cftime._parse_date(date_string)
    if len(x) == 7:
        year, month, day, hour, minute, second, utc_offset = x
        microsecond = 0
    else:
        year, month, day, hour, minute, second, microsecond, utc_offset = x

    if utc_offset:
        raise ValueError("Can't specify a time offset from UTC")

    return cftime.datetime(
        year, month, day, hour, minute, second, microsecond, calendar=calendar
    )


def st2dt(array, units_in=None):
    """The returned array is always independent.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        array: numpy array-like

        units_in: `Units`, optional

    :Returns:

        `numpy.ndarray`
            An array of `cftime.datetime` objects with the same shape
            as *array*.

    **Examples**

    """
    func = partial(st2datetime, calendar=units_in._calendar)
    return np.vectorize(func, otypes=[object])(array)


def st2rt(array, units_in, units_out):
    """The returned array is always independent.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        array: numpy array-like of ISO 8601 date-time strings

        units_in: `Units` or `None`

        units_out: `Units`

    :Returns:

        `numpy.ndarray`
            An array of floats with the same shape as *array*.

    """
    array = st2dt(array, units_in)
    return dt2rt(array, units_out)
