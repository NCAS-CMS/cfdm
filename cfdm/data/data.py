import itertools
import logging

import netCDF4
import numpy
import numpy as np

from .. import core
from ..constants import masked as cfdm_masked
from ..decorators import (
    _inplace_enabled,
    _inplace_enabled_define_and_cleanup,
    _manage_log_level_via_verbosity,
)
from ..functions import abspath
from ..mixin.container import Container
from ..mixin.files import Files
from ..mixin.netcdf import NetCDFHDF5
from . import NumpyArray, abstract

logger = logging.getLogger(__name__)


class Data(Container, NetCDFHDF5, Files, core.Data):
    """An orthogonal multidimensional array with masking and units.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        array=None,
        units=None,
        calendar=None,
        fill_value=None,
        source=None,
        copy=True,
        dtype=None,
        mask=None,
        _use_array=True,
        **kwargs,
    ):
        """**Initialisation**

        :Parameters:

            array: data_like, optional
                The array of values.

                {{data_like}}

                Ignored if the *source* parameter is set.

                *Parameter example:*
                  ``array=[34.6]``

                *Parameter example:*
                  ``array=[[1, 2], [3, 4]]``

                *Parameter example:*
                  ``array=numpy.ma.arange(10).reshape(2, 1, 5)``

            units: `str`, optional
                The physical units of the data. Ignored if the *source*
                parameter is set.

                The units may also be set after initialisation with the
                `set_units` method.

                *Parameter example:*
                  ``units='km hr-1'``

                *Parameter example:*
                  ``units='days since 2018-12-01'``

            calendar: `str`, optional
                The calendar for reference time units. Ignored if the
                *source* parameter is set.

                The calendar may also be set after initialisation with the
                `set_calendar` method.

                *Parameter example:*
                  ``calendar='360_day'``

            fill_value: optional
                The fill value of the data. By default, or if set to
                `None`, the `numpy` fill value appropriate to the array's
                data type will be used (see
                `numpy.ma.default_fill_value`). Ignored if the *source*
                parameter is set.

                The fill value may also be set after initialisation with
                the `set_fill_value` method.

                *Parameter example:*
                  ``fill_value=-999.``

            dtype: data-type, optional
                The desired data-type for the data. By default the
                data-type will be inferred form the *array* parameter.

                The data-type may also be set after initialisation
                with the `dtype` attribute.

                *Parameter example:*
                    ``dtype=float``

                *Parameter example:*
                    ``dtype='float32'``

                *Parameter example:*
                    ``dtype=numpy.dtype('i2')``

            mask: data_like, optional
                Apply this mask to the data given by the *array*
                parameter. By default, or if *mask* is `None`, no mask
                is applied. May be any data_like object that
                broadcasts to *array*. Masking will be carried out
                where mask elements evaluate to `True`.

                {{data_like}}

                This mask will applied in addition to any mask already
                defined by the *array* parameter.

            source: optional
                Initialise the array, units, calendar and fill value
                from those of *source*.

                {{init source}}

            {{deep copy}}

            kwargs: ignored
                Not used. Present to facilitate subclassing.

        """
        if dtype is not None:
            if isinstance(array, abstract.Array):
                array = array.array
            elif not isinstance(array, numpy.ndarray):
                array = numpy.asanyarray(array)

            array = array.astype(dtype)
            array = NumpyArray(array)

        if mask is not None:
            if isinstance(array, abstract.Array):
                array = array.array
            elif not isinstance(array, numpy.ndarray):
                array = numpy.asanyarray(array)

            array = numpy.ma.array(array, mask=mask)
            array = NumpyArray(array)

        super().__init__(
            array=array,
            units=units,
            calendar=calendar,
            fill_value=fill_value,
            source=source,
            copy=copy,
            _use_array=_use_array,
        )

        # Initialise the netCDF components
        self._initialise_netcdf(source)
        self._initialise_original_filenames(source)

    def __array__(self, *dtype):
        """The numpy array interface.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            dtype: optional
                Typecode or data-type to which the array is cast.

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples**


        >>> d = {{package}}.{{class}}([1, 2, 3])
        >>> a = numpy.array(d)
        >>> print(type(a))
        <class 'numpy.ndarray'>
        >>> a[0] = -99
        >>> d
        <{{repr}}{{class}}(3): [1, 2, 3]>
        >>> b = numpy.array(d, float)
        >>> print(b)
        [1. 2. 3.]

        """
        array = self.array
        if not dtype:
            return array
        else:
            return array.astype(dtype[0], copy=False)

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        """
        try:
            shape = self.shape
        except AttributeError:
            shape = ""
        else:
            shape = str(shape)
            shape = shape.replace(",)", ")")

        return f"<{ self.__class__.__name__}{shape}: {self}>"

    def __format__(self, format_spec):
        """Interpret format specifiers for size 1 arrays.

        **Examples**

        >>> d = {{package}}.{{class}}(9, 'metres')
        >>> f"{d}"
        '9 metres'
        >>> f"{d!s}"
        '9 metres'
        >>> f"{d!r}"
        '<{{repr}}{{class}}(): 9 metres>'
        >>> f"{d:.3f}"
        '9.000'

        >>> d = {{package}}.{{class}}([[9]], 'metres')
        >>> f"{d}"
        '[[9]] metres'
        >>> f"{d!s}"
        '[[9]] metres'
        >>> f"{d!r}"
        '<{{repr}}{{class}}(1, 1): [[9]] metres>'
        >>> f"{d:.3f}"
        '9.000'

        >>> d = {{package}}.{{class}}([9, 10], 'metres')
        >>> f"{d}"
        >>> '[9, 10] metres'
        >>> f"{d!s}"
        >>> '[9, 10] metres'
        >>> f"{d!r}"
        '<{{repr}}{{class}}(2): [9, 10] metres>'
        >>> f"{d:.3f}"
        Traceback (most recent call last):
            ...
        ValueError: Can't format Data array of size 2 with format code .3f

        """
        if not format_spec:
            return super().__format__("")

        n = self.size
        if n == 1:
            return "{x:{f}}".format(x=self.first_element(), f=format_spec)

        raise ValueError(
            f"Can't format Data array of size {n} with "
            f"format code {format_spec}"
        )

    def __getitem__(self, indices):
        """Return a subspace of the data defined by indices.

        d.__getitem__(indices) <==> d[indices]

        Indexing follows rules that are very similar to the numpy indexing
        rules, the only differences being:

        * An integer index i takes the i-th element but does not reduce
          the rank by one.

        * When two or more dimensions' indices are sequences of integers
          then these indices work independently along each dimension
          (similar to the way vector subscripts work in Fortran). This is
          the same behaviour as indexing on a Variable object of the
          netCDF4 package.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `__setitem__`, `_parse_indices`

        :Returns:

            `{{class}}`
                The subspace of the data.

        **Examples**


        >>> d = {{package}}.{{class}}(numpy.arange(100, 190).reshape(1, 10, 9))
        >>> d.shape
        (1, 10, 9)
        >>> d[:, :, 1].shape
        (1, 10, 1)
        >>> d[:, 0].shape
        (1, 1, 9)
        >>> d[..., 6:3:-1, 3:6].shape
        (1, 3, 3)
        >>> d[0, [2, 9], [4, 8]].shape
        (1, 2, 2)
        >>> d[0, :, -2].shape
        (1, 10, 1)

        """
        indices = self._parse_indices(indices)

        array = self._get_Array(None)
        if array is None:
            raise ValueError("No array!!")

        array = array[tuple(indices)]

        out = self.copy(array=False)
        out._set_Array(array, copy=False)

        if out.shape != self.shape:
            # Delete hdf5 chunksizes
            out.nc_clear_hdf5_chunksizes()

        return out

    def __and__(self, other):
        """The binary bitwise operation ``&``

        x.__and__(y) <==> x&y

        """
        return self._binary_operation(other, "__and__")

    def __eq__(self, other):
        """The rich comparison operator ``==``

        x.__eq__(y) <==> x==y

        """
        return self._binary_operation(other, "__eq__")

    def __int__(self):
        """Called by the `int` built-in function.

        x.__int__() <==> int(x)

        """
        if self.size != 1:
            raise TypeError(
                "only length-1 arrays can be converted to "
                f"Python scalars. Got {self}"
            )

        return int(self.array)

    def __iter__(self):
        """Called when an iterator is required.

        x.__iter__() <==> iter(x)

        **Examples**

        >>> d = {{package}}.{{class}}([1, 2, 3], 'metres')
        >>> for e in d:
        ...    print(repr(e))
        ...
        1
        2
        3

        >>> d = {{package}}.{{class}}([[1, 2], [4, 5]], 'metres')
        >>> for e in d:
        ...    print(repr(e))
        ...
        <{{repr}}Data(2): [1, 2] metres>
        <{{repr}}Data(2): [4, 5] metres>

        >>> d = {{package}}.{{class}}(34, 'metres')
        >>> for e in d:
        ...     print(repr(e))
        Traceback (most recent call last):
            ...
        TypeError: Iteration over 0-d Data

        """
        ndim = self.ndim

        if not ndim:
            raise TypeError(f"Iteration over 0-d {self.__class__.__name__}")

        if ndim == 1:
            i = iter(self.array)
            while 1:
                try:
                    yield next(i)
                except StopIteration:
                    return
        else:
            # ndim > 1
            for n in range(self.shape[0]):
                out = self[n, ...]
                out.squeeze(0, inplace=True)
                yield out

    def __setitem__(self, indices, value):
        """Assign to data elements defined by indices.

        d.__setitem__(indices, x) <==> d[indices]=x

        Indexing follows rules that are very similar to the numpy indexing
        rules, the only differences being:

        * An integer index i takes the i-th element but does not reduce
          the rank by one.

        * When two or more dimensions' indices are sequences of integers
          then these indices work independently along each dimension
          (similar to the way vector subscripts work in Fortran). This is
          the same behaviour as indexing on a Variable object of the
          netCDF4 package.

        **Broadcasting**

        The value, or values, being assigned must be broadcastable to the
        shape defined by the indices, using the numpy broadcasting rules.

        **Missing data**

        Data array elements may be set to missing values by assigning them
        to `masked`. Missing values may be unmasked by assigning them to
        any other value.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `__getitem__`, `_parse_indices`

        :Returns:

            `None`

        **Examples**


        >>> d = {{package}}.{{class}}(numpy.arange(100, 190).reshape(1, 10, 9))
        >>> d.shape
        (1, 10, 9)
        >>> d[:, :, 1] = -10
        >>> d[:, 0] = range(9)
        >>> d[..., 6:3:-1, 3:6] = numpy.arange(-18, -9).reshape(3, 3)
        >>> d[0, [2, 9], [4, 8]] = {{package}}.{{class}}([[-2, -3]])
        >>> d[0, :, -2] = {{package}}.masked

        """
        indices = self._parse_indices(indices)

        array = self.array

        if value is cfdm_masked or numpy.ma.isMA(value):
            # The data is not masked but the assignment is masking
            # elements, so turn the non-masked array into a masked
            # one.
            array = array.view(numpy.ma.MaskedArray)

        self._set_subspace(array, indices, numpy.asanyarray(value))

        self._set_Array(array, copy=False)

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        """
        units = self.get_units(None)
        calendar = self.get_calendar(None)

        isreftime = False
        if units is not None:
            if isinstance(units, str):
                isreftime = "since" in units
            else:
                units = "??"

        try:
            first = self.first_element()
        except Exception:
            out = ""
            if units and not isreftime:
                out += f" {units}"
            if calendar:
                out += f" {calendar}"

            return out

        size = self.size
        shape = self.shape
        ndim = self.ndim
        open_brackets = "[" * ndim
        close_brackets = "]" * ndim

        mask = [False, False, False]

        if isreftime and first is np.ma.masked:
            first = 0
            mask[0] = True

        if size == 1:
            if isreftime:
                # Convert reference time to date-time
                try:
                    first = type(self)(
                        numpy.ma.array(first, mask=mask[0]), units, calendar
                    ).datetime_array
                except (ValueError, OverflowError):
                    first = "??"

            out = f"{open_brackets}{first}{close_brackets}"
        else:
            last = self.last_element()
            if isreftime:
                if last is numpy.ma.masked:
                    last = 0
                    mask[-1] = True

                # Convert reference times to date-times
                try:
                    first, last = type(self)(
                        numpy.ma.array(
                            [first, last], mask=(mask[0], mask[-1])
                        ),
                        units,
                        calendar,
                    ).datetime_array
                except (ValueError, OverflowError):
                    first, last = ("??", "??")

            if size > 3:
                out = f"{open_brackets}{first}, ..., {last}{close_brackets}"
            elif shape[-1:] == (3,):
                middle = self.second_element()
                if isreftime:
                    # Convert reference time to date-time
                    if middle is numpy.ma.masked:
                        middle = 0
                        mask[1] = True

                    try:
                        middle = type(self)(
                            numpy.ma.array(middle, mask=mask[1]),
                            units,
                            calendar,
                        ).datetime_array
                    except (ValueError, OverflowError):
                        middle = "??"

                out = (
                    f"{open_brackets}{first}, {middle}, {last}{close_brackets}"
                )
            elif size == 3:
                out = f"{open_brackets}{first}, ..., {last}{close_brackets}"
            else:
                out = f"{open_brackets}{first}, {last}{close_brackets}"

        if isreftime:
            if calendar:
                out += f" {calendar}"
        elif units:
            out += f" {units}"

        return out

    def _binary_operation(self, other, method):
        """Implement binary arithmetic and comparison operations.

        Implements binary arithmetic and comparison operations with
        the numpy broadcasting rules.

        It is called by the binary arithmetic and comparison methods,
        such as `__sub__`, `__imul__`, `__rdiv__`, `__lt__`, etc.

        .. seealso:: `_unary_operation`

        :Parameters:

            other:
                The object on the right hand side of the operator.

            method: `str`
                The binary arithmetic or comparison method name (such as
                ``'__imul__'`` or ``'__ge__'``).

        :Returns:

            `Data`
                A new data object, or if the operation was in place, the
                same data object.

        **Examples**

        >>> d = {{package}}.{{class}}([0, 1, 2, 3])
        >>> e = {{package}}.{{class}}([1, 1, 3, 4])
        >>> f = d._binary_operation(e, '__add__')
        >>> print(f.array)
        [1 2 5 7]
        >>> e = d._binary_operation(e, '__lt__')
        >>> print(e.array)
        [ True False  True  True]
        >>> d._binary_operation(2, '__imul__')
        >>> print(d.array)
        [0 2 4 6]

        """
        inplace = method[2] == "i"
        if inplace:
            d = self
        else:
            d = self.copy(array=False)

        array = np.asanyarray(getattr(self.array, method)(other))

        d._set_Array(array, copy=False)

        return d

    def _item(self, index):
        """Return an element of the data as a scalar.

        It is assumed, but not checked, that the given index selects
        exactly one element.

        :Parameters:

            index:

        :Returns:

                The selected element of the data.

        **Examples**

        >>> d = {{package}}.{{class}}([[1, 2, 3]], 'km')
        >>> x = d._item((0, -1))
        >>> print(x, type(x))
        3 <class 'int'>
        >>> x = d._item((0, 1))
        >>> print(x, type(x))
        2 <class 'int'>
        >>> d[0, 1] = {{package}}.masked
        >>> d._item((slice(None), slice(1, 2)))
        masked

        """
        array = self[index].array

        if not numpy.ma.isMA(array):
            return array.item()

        mask = array.mask
        if mask is numpy.ma.nomask or not mask.item():
            return array.item()

        return numpy.ma.masked

    def _original_filenames(self, define=None, update=None, clear=False):
        """Return the names of files that contain the original data.

        {{original filenames}}

        .. note:: The original filenames are **not** inherited by
                  parent constructs that contain the data.

        .. versionadded:: (cfdm) 1.10.0.1

        :Parameters:

            {{define: (sequence of) `str`, optional}}

            {{update: (sequence of) `str`, optional}}

            {{clear: `bool` optional}}

        :Returns:

            `set` or `None`
                {{Returns original filenames}}

                If the *define* or *update* parameter is set then
                `None` is returned.

        **Examples**

        >>> d = {{package}}.{{class}}(9)
        >>> d._original_filenames()
        ()
        >>> d._original_filenames(define="file1.nc")
        >>> d._original_filenames()
        ('/data/user/file1.nc',)
        >>> d._original_filenames(update=["file1.nc"])
        >>> d._original_filenames()
        ('/data/user/file1.nc',)
        >>> d._original_filenames(update="file2.nc")
        >>> d._original_filenames()
        ('/data/user/file1.nc', '/data/user/file2.nc')
        >>> d._original_filenames(define="file3.nc")
        >>> d._original_filenames()
        ('/data/user/file3.nc',)
        >>> d._original_filenames(clear=True)
        >>> d._original_filenames()
        ()

        >>> d = {{package}}.{{class}}(9, _filenames=["file1.nc", "file2.nc"])
        >>> d._original_filenames()
        ('/data/user/file1.nc', '/data/user/file2.nc',)

        """
        old = super()._original_filenames(
            define=define, update=update, clear=clear
        )

        if old is None:
            return

        # Find any compression ancillary data variables
        ancils = []
        compression = self.get_compression_type()
        if compression:
            if compression == "gathered":
                ancils.extend(self.get_list([]))
            elif compression == "subsampled":
                ancils.extend(self.get_tie_point_indices({}).values())
                ancils.extend(self.get_interpolation_parameters({}).values())
                ancils.extend(self.get_dependent_tie_points({}).values())
            else:
                if compression in (
                    "ragged contiguous",
                    "ragged indexed contiguous",
                ):
                    ancils.extend(self.get_count([]))

                if compression in (
                    "ragged indexed",
                    "ragged indexed contiguous",
                ):
                    ancils.extend(self.get_index([]))

            if ancils:
                # Include original file names from ancillary variables
                for a in ancils:
                    old.update(a._original_filenames(clear=clear))

        # Return the old file names
        return old

    def _parse_axes(self, axes):
        """Parses the data axes and returns valid non-duplicate axes.

        :Parameters:

            axes: (sequence of) `int`
                The axes of the data.

                {{axes int examples}}

        :Returns:

            `tuple`

        **Examples**

        >>> d._parse_axes(1)
        (1,)

        >>> e._parse_axes([0, 2])
        (0, 2)

        """
        if axes is None:
            return axes

        ndim = self.ndim

        if isinstance(axes, int):
            axes = (axes,)

        axes2 = []
        for axis in axes:
            if 0 <= axis < ndim:
                axes2.append(axis)
            elif -ndim <= axis < 0:
                axes2.append(axis + ndim)
            else:
                raise ValueError(f"Invalid axis: {axis!r}")

        # Check for duplicate axes
        n = len(axes2)
        if n > len(set(axes2)) >= 1:
            raise ValueError(f"Duplicate axis: {axes2}")

        return tuple(axes2)

    def _set_Array(self, array, copy=True):
        """Set the array.

        .. seealso:: `_set_CompressedArray`

        :Parameters:

            array: `numpy` array_like or `Array`, optional
                The array to be inserted.

        :Returns:

            `None`

        **Examples**

        >>> d._set_Array(a)

        """
        if not isinstance(array, abstract.Array):
            if not isinstance(array, numpy.ndarray):
                array = numpy.asanyarray(array)

            array = NumpyArray(array)

        super()._set_Array(array, copy=copy)

    def _set_CompressedArray(self, array, copy=True):
        """Set the compressed array.

        .. versionadded:: (cfdm) 1.7.11

        .. seealso:: `_set_Array`

        :Parameters:

            array: subclass of `CompressedArray`
                The compressed array to be inserted.

        :Returns:

            `None`

        **Examples**

        >>> d._set_CompressedArray(a)

        """
        self._set_Array(array, copy=copy)

    @classmethod
    def _set_subspace(cls, array, indices, value, orthogonal_indexing=True):
        """Assign to a subspace of an array.

        :Parameters:

            array: array_like
                The array to be assigned to. Must support
                `numpy`-style indexing. The array is changed in-place.

            indices: sequence
                The indices to be applied.

            value: array_like
                The value being assigned. Must support fancy indexing.

            orthogonal_indexing: `bool`, optional
                If True then apply 'orthogonal indexing', for which
                indices that are 1-d arrays or lists subspace along
                each dimension independently. This behaviour is
                similar to Fortran but different to, for instance,
                `numpy` or `dask`.

        :Returns:

            `None`

        **Examples**

        Note that ``a`` is redefined for each example, as it is
        changed in-place.

        >>> a = np.arange(40).reshape(5, 8)
        >>> {{package}}.Data._set_subspace(a, [[1, 4 ,3], [7, 6, 1]],
        ...                    np.array([[-1, -2, -3]]))
        >>> print(a)
        [[ 0  1  2  3  4  5  6  7]
         [ 8 -3 10 11 12 13 -2 -1]
         [16 17 18 19 20 21 22 23]
         [24 -3 26 27 28 29 -2 -1]
         [32 -3 34 35 36 37 -2 -1]]

        >>> a = np.arange(40).reshape(5, 8)
        >>> {{package}}.Data._set_subspace(a, [[1, 4 ,3], [7, 6, 1]],
        ...                    np.array([[-1, -2, -3]]),
        ...                    orthogonal_indexing=False)
        >>> print(a)
        [[ 0  1  2  3  4  5  6  7]
         [ 8  9 10 11 12 13 14 -1]
         [16 17 18 19 20 21 22 23]
         [24 -3 26 27 28 29 30 31]
         [32 33 34 35 36 37 -2 39]]

        >>> a = np.arange(40).reshape(5, 8)
        >>> value = np.linspace(-1, -9, 9).reshape(3, 3)
        >>> print(value)
        [[-1. -2. -3.]
         [-4. -5. -6.]
         [-7. -8. -9.]]
        >>> {{package}}.Data._set_subspace(a, [[4, 4 ,1], [7, 6, 1]], value)
        >>> print(a)
        [[ 0  1  2  3  4  5  6  7]
         [ 8 -9 10 11 12 13 -8 -7]
         [16 17 18 19 20 21 22 23]
         [24 25 26 27 28 29 30 31]
         [32 -6 34 35 36 37 -5 -4]]

        """
        if not orthogonal_indexing:
            # --------------------------------------------------------
            # Apply non-orthogonal indexing
            # --------------------------------------------------------
            array[tuple(indices)] = value
            return

        # ------------------------------------------------------------
        # Still here? Then apply orthogonal indexing
        # ------------------------------------------------------------
        axes_with_list_indices = [
            i
            for i, x in enumerate(indices)
            if isinstance(x, list) or getattr(x, "shape", False)
        ]

        if len(axes_with_list_indices) < 2:
            # At most one axis has a list-of-integers index so we can
            # do a normal assignment
            array[tuple(indices)] = value
        else:
            # At least two axes have list-of-integers indices so we
            # can't do a normal assignment.
            #
            # The brute-force approach would be to do a separate
            # assignment to each set of elements of 'array' that are
            # defined by every possible combination of the integers
            # defined by the two index lists.
            #
            # For example, if the input 'indices' are ([1, 2, 4, 5],
            # slice(0:10), [8, 9]) then the brute-force approach would
            # be to do 4*2=8 separate assignments of 10 elements each.
            #
            # This can be reduced by a factor of ~2 per axis that has
            # list indices if we convert it to a sequence of "size 2"
            # slices (with a "size 1" slice at the end if there are an
            # odd number of list elements).
            #
            # In the above example, the input list index [1, 2, 4, 5]
            # can be mapped to two slices: slice(1,3,1), slice(4,6,1);
            # the input list index [8, 9] is mapped to slice(8,10,1)
            # and only 2 separate assignments of 40 elements each are
            # needed.
            indices1 = indices[:]
            for i, (x, size) in enumerate(zip(indices, array.shape)):
                if i in axes_with_list_indices:
                    # This index is a list (or similar) of integers
                    if not isinstance(x, list):
                        x = np.asanyarray(x).tolist()

                    y = []
                    args = [iter(x)] * 2
                    for start, stop in itertools.zip_longest(*args):
                        if start < 0:
                            start += size

                        if stop is None:
                            y.append(slice(start, start + 1))
                            break

                        if stop < 0:
                            stop += size

                        step = stop - start
                        if not step:
                            # (*) There is a repeated index in
                            #     positions 2N and 2N+1 (N>=0). Store
                            #     this as a single-element list
                            #     instead of a "size 2" slice, mainly
                            #     as an indicator that a special index
                            #     to 'value' might need to be
                            #     created. See below, where this
                            #     comment is referenced.
                            #
                            #     For example, the input list index
                            #     [1, 4, 4, 4, 6, 2, 7] will be mapped
                            #     to slice(1,5,3), [4], slice(6,1,-4),
                            #     slice(7,8,1)
                            y.append([start])
                        else:
                            if step > 0:
                                stop += 1
                            else:
                                stop -= 1

                            y.append(slice(start, stop, step))

                    indices1[i] = y
                else:
                    indices1[i] = (x,)

            if value.size == 1:
                # 'value' is logically scalar => simply assign it to
                # all index combinations.
                for i in itertools.product(*indices1):
                    array[i] = value
            else:
                # 'value' has two or more elements => for each index
                # combination for 'array' assign the corresponding
                # part of 'value'.
                indices2 = []
                ndim_difference = array.ndim - value.ndim
                for i2, size in enumerate(value.shape):
                    i1 = i2 + ndim_difference
                    if i1 not in axes_with_list_indices:
                        # The input 'indices[i1]' is a slice
                        indices2.append((slice(None),))
                        continue

                    index1 = indices1[i1]
                    if size == 1:
                        indices2.append((slice(None),) * len(index1))
                    else:
                        y = []
                        start = 0
                        for index in index1:
                            stop = start + 2
                            if isinstance(index, list):
                                # Two consecutive elements of 'value'
                                # are assigned to the same integer
                                # index of 'array'.
                                #
                                # See the (*) comment above.
                                start += 1

                            y.append(slice(start, stop))
                            start = stop

                        indices2.append(y)

                for i, j in zip(
                    itertools.product(*indices1), itertools.product(*indices2)
                ):
                    array[i] = value[j]

    @property
    def compressed_array(self):
        """Returns an independent numpy array of the compressed data.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_compressed_axes`, `get_compressed_dimension`,
                     `get_compression_type`

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the compressed data.

        **Examples**

        >>> a = d.compressed_array

        """
        ca = self._get_Array(None)
        if ca is None or not ca.get_compression_type():
            raise ValueError("not compressed: can't get compressed array")

        return ca.compressed_array

    @property
    def data(self):
        """The data as an object identity.

        **Examples**

        >>> d.data is d
        True

        """
        return self

    @property
    def datetime_array(self):
        """Returns an independent numpy array of datetimes.

        Specifically, returns an independent numpy array containing
        the date-time objects corresponding to times since a reference
        date.

        Only applicable for reference time units.

        If the calendar has not been set then the CF default calendar of
        'standard' (i.e. the mixed Gregorian/Julian calendar as defined by
        Udunits) will be used.

        Conversions are carried out with the `netCDF4.num2date` function.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `array`, `datetime_as_string`

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the date-time objects.

        **Examples**

        >>> d = {{package}}.{{class}}([31, 62, 90], units='days since 2018-12-01')
        >>> a = d.datetime_array
        >>> print(a)
        [cftime.DatetimeGregorian(2019, 1, 1, 0, 0, 0, 0)
         cftime.DatetimeGregorian(2019, 2, 1, 0, 0, 0, 0)
         cftime.DatetimeGregorian(2019, 3, 1, 0, 0, 0, 0)]
        >>> print(a[1])
        2019-02-01 00:00:00

        >>> d = {{package}}.{{class}}(
        ...     [31, 62, 90], units='days since 2018-12-01', calendar='360_day')
        >>> a = d.datetime_array
        >>> print(a)
        [cftime.Datetime360Day(2019, 1, 2, 0, 0, 0, 0)
         cftime.Datetime360Day(2019, 2, 3, 0, 0, 0, 0)
         cftime.Datetime360Day(2019, 3, 1, 0, 0, 0, 0)]
        >>> print(a[1])
        2019-02-03 00:00:00

        """
        array = self.array

        mask = None
        if numpy.ma.isMA(array):
            # num2date has issues if the mask is nomask
            mask = array.mask
            if mask is numpy.ma.nomask or not numpy.ma.is_masked(array):
                mask = None
                array = array.view(numpy.ndarray)

        if mask is not None and not array.ndim:
            # Fix until num2date copes with scalar aarrays containing
            # missing data
            return array

        array = netCDF4.num2date(
            array,
            units=self.get_units(None),
            calendar=self.get_calendar("standard"),
            only_use_cftime_datetimes=True,
        )

        if mask is None:
            # There is no missing data
            array = numpy.array(array, dtype=object)
        else:
            # There is missing data
            array = numpy.ma.masked_where(mask, array)
            if not numpy.ndim(array):
                array = numpy.ma.masked_all((), dtype=object)

        return array

    @property
    def datetime_as_string(self):
        """Returns an independent numpy array with datetimes as strings.

        Specifically, returns an independent numpy array containing
        string representations of times since a reference date.

        Only applicable for reference time units.

        If the calendar has not been set then the CF default calendar of
        "standard" (i.e. the mixed Gregorian/Julian calendar as defined by
        Udunits) will be used.

        Conversions are carried out with the `netCDF4.num2date` function.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `array`, `datetime_array`

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the date-time strings.

        **Examples**

        >>> d = {{package}}.{{class}}([31, 62, 90], units='days since 2018-12-01')
        >>> print(d.datetime_as_string)
        ['2019-01-01 00:00:00' '2019-02-01 00:00:00' '2019-03-01 00:00:00']

        >>> d = {{package}}.{{class}}(
        ...     [31, 62, 90], units='days since 2018-12-01', calendar='360_day')
        >>> print(d.datetime_as_string)
        ['2019-01-02 00:00:00' '2019-02-03 00:00:00' '2019-03-01 00:00:00']

        """
        return self.datetime_array.astype(str)

    @property
    def mask(self):
        """The Boolean missing data mask of the data array.

        The Boolean mask has True where the data array has missing data
        and False otherwise.

        :Returns:

            `{{class}}`
                The Boolean mask as data.

        **Examples**

        >>> d = {{package}}.{{class}}(numpy.ma.array(
        ...     [[280.0,   -99,   -99,   -99],
        ...      [281.0, 279.0, 278.0, 279.5]],
        ...     mask=[[0, 1, 1, 1], [0, 0, 0, 0]]
        ... ))
        >>> d
        <{{repr}}Data(2, 4): [[280.0, ..., 279.5]]>
        >>> print(d.array)
        [[280.0    --    --    --]
         [281.0 279.0 278.0 279.5]]
        >>> d.mask
        <{{repr}}Data(2, 4): [[False, ..., False]]>
        >>> print(d.mask.array)
        [[False  True  True  True]
         [False False False False]]

        """
        return type(self)(numpy.ma.getmaskarray(self.array))

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def any(self):
        """Test whether any data array elements evaluate to True.

        Performs a logical or over the data array and returns the
        result. Masked values are considered as False during computation.

        :Returns:

            `bool`
                `True` if any data array elements evaluate to True,
                otherwise `False`.

        **Examples**

        >>> d = {{package}}.{{class}}([[0, 0, 0]])
        >>> d.any()
        False
        >>> d[0, 0] = {{package}}.masked
        >>> print(d.array)
        [[-- 0 0]]
        >>> d.any()
        False
        >>> d[0, 1] = 3
        >>> print(d.array)
        [[-- 3 0]]
        >>> d.any()
        True
        >>> d[...] = {{package}}.masked
        >>> print(d.array)
        [[-- -- --]]
        >>> d.any()
        False

        """
        masked = self.array.any()
        if masked is numpy.ma.masked:
            masked = False

        return masked

    @_inplace_enabled(default=False)
    def apply_masking(
        self,
        fill_values=None,
        valid_min=None,
        valid_max=None,
        valid_range=None,
        inplace=False,
    ):
        """Apply masking.

        Masking is applied according to the values of the keyword
        parameters.

        Elements that are already masked remain so.

        .. versionadded:: (cfdm) 1.8.2

        .. seealso:: `get_fill_value`, `mask`

        :Parameters:

            fill_values: `bool` or sequence of scalars, optional
                Specify values that will be set to missing data. Data
                elements exactly equal to any of the values are set to
                missing data.

                If True then the value returned by the `get_fill_value`
                method, if such a value exists, is used.

                Zero or more values may be provided in a sequence of
                scalars.

                *Parameter example:*
                  Specify a fill value of 999: ``fill_values=[999]``

                *Parameter example:*
                  Specify fill values of 999 and -1.0e30:
                  ``fill_values=[999, -1.0e30]``

                *Parameter example:*
                  Use the fill value already set for the data:
                  ``fill_values=True``

                *Parameter example:*
                  Use no fill values: ``fill_values=False`` or
                  ``fill_value=[]``

            valid_min: number, optional
                A scalar specifying the minimum valid value. Data elements
                strictly less than this number will be set to missing
                data.

            valid_max: number, optional
                A scalar specifying the maximum valid value. Data elements
                strictly greater than this number will be set to missing
                data.

            valid_range: (number, number), optional
                A vector of two numbers specifying the minimum and maximum
                valid values, equivalent to specifying values for both
                *valid_min* and *valid_max* parameters. The *valid_range*
                parameter must not be set if either *valid_min* or
                *valid_max* is defined.

                *Parameter example:*
                  ``valid_range=[-999, 10000]`` is equivalent to setting
                  ``valid_min=-999, valid_max=10000``

            inplace: `bool`, optional
                If True then do the operation in-place and return `None`.

        :Returns:

            `{{class}}` or `None`
                The data with masked values. If the operation was in-place
                then `None` is returned.

        **Examples**


        >>> d = {{package}}.{{class}}(numpy.arange(12).reshape(3, 4), 'm')
        >>> d[1, 1] = {{package}}.masked
        >>> print(d.array)
        [[0  1  2  3]
         [4 --  6  7]
         [8  9 10 11]]

        >>> print(d.apply_masking().array)
        [[0  1  2  3]
         [4 --  6  7]
         [8  9 10 11]]
        >>> print(d.apply_masking(fill_values=[0]).array)
        [[-- 1 2 3]
         [4 -- 6 7]
         [8 9 10 11]]
        >>> print(d.apply_masking(fill_values=[0, 11]).array)
        [[-- 1 2 3]
         [4 -- 6 7]
         [8 9 10 --]]

        >>> print(d.apply_masking(valid_min=3).array)
        [[-- -- -- 3]
         [4 -- 6 7]
         [8 9 10 11]]
        >>> print(d.apply_masking(valid_max=6).array)
        [[0 1 2 3]
         [4 -- 6 --]
         [-- -- -- --]]
        >>> print(d.apply_masking(valid_range=[2, 8]).array)
        [[-- -- 2 3]
         [4 -- 6 7]
         [8 -- -- --]]

        >>> d.set_fill_value(7)
        >>> print(d.apply_masking(fill_values=True).array)
        [[0  1  2  3]
         [4 --  6 --]
         [8  9 10 11]]
        >>> print(d.apply_masking(fill_values=True,
        ...                       valid_range=[2, 8]).array)
        [[-- -- 2 3]
         [4 -- 6 --]
         [8 -- -- --]]

        """
        if valid_range is not None:
            if valid_min is not None or valid_max is not None:
                raise ValueError(
                    "Can't set 'valid_range' parameter with either the "
                    "'valid_min' nor 'valid_max' parameters"
                )

            try:
                if len(valid_range) != 2:
                    raise ValueError(
                        "'valid_range' parameter must be a vector of "
                        "two elements"
                    )
            except TypeError:
                raise ValueError(
                    "'valid_range' parameter must be a vector of "
                    "two elements"
                )

            valid_min, valid_max = valid_range

        d = _inplace_enabled_define_and_cleanup(self)

        if fill_values is None:
            fill_values = False

        if isinstance(fill_values, bool):
            if fill_values:
                fill_value = self.get_fill_value(None)
                if fill_value is not None:
                    fill_values = (fill_value,)
                else:
                    fill_values = ()
            else:
                fill_values = ()
        else:
            try:
                _ = iter(fill_values)
            except TypeError:
                raise TypeError(
                    "'fill_values' parameter must be a sequence or "
                    f"of type bool. Got type {type(fill_values)}"
                )
            else:
                if isinstance(fill_values, str):
                    raise TypeError(
                        "'fill_values' parameter must be a sequence or "
                        f"of type bool. Got type {type(fill_values)}"
                    )

        mask = None

        if fill_values:
            array = self.array
            mask = array == fill_values[0]

            for fill_value in fill_values[1:]:
                mask |= array == fill_value

        if valid_min is not None:
            if mask is None:
                array = self.array
                mask = array < valid_min
            else:
                mask |= array < valid_min

        if valid_max is not None:
            if mask is None:
                array = self.array
                mask = array > valid_max
            else:
                mask |= array > valid_max

        if mask is not None:
            array = numpy.ma.where(mask, cfdm_masked, array)
            d._set_Array(array, copy=False)

        return d

    def copy(self, array=True):
        """Return a deep copy.

        ``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

        :Parameters:

            array: `bool`, optional
                If True (the default) then copy the array, else it
                is not copied.

        :Returns:

            `{{class}}`
                The deep copy.

        **Examples**

        >>> e = d.copy()
        >>> e = d.copy(array=False)

        """
        return super().copy(array=array)

    def creation_commands(
        self, name="data", namespace=None, indent=0, string=True
    ):
        """Return the commands that would create the data object.

        .. versionadded:: (cfdm) 1.8.7.0

        :Parameters:

            name: `str` or `None`, optional
                Set the variable name of `Data` object that the commands
                create.

            {{namespace: `str`, optional}}

            {{indent: `int`, optional}}

            {{string: `bool`, optional}}

        :Returns:

            {{returns creation_commands}}

        **Examples**

        >>> d = {{package}}.{{class}}([[0.0, 45.0], [45.0, 90.0]],
        ...                           units='degrees_east')
        >>> print(d.creation_commands())
        data = {{package}}.{{class}}([[0.0, 45.0], [45.0, 90.0]], units='degrees_east', dtype='f8')

        >>> d = {{package}}.{{class}}(['alpha', 'beta', 'gamma', 'delta'],
        ...                           mask = [1, 0, 0, 0])
        >>> d.creation_commands(name='d', namespace='', string=False)
        ["d = Data(['', 'beta', 'gamma', 'delta'], dtype='U5', mask=Data([True, False, False, False], dtype='b1'))"]

        """
        namespace0 = namespace
        if namespace is None:
            namespace = self._package() + "."
        elif namespace and not namespace.endswith("."):
            namespace += "."

        mask = self.mask
        if mask.any():
            if name == "mask":
                raise ValueError(
                    "When the data is masked, the 'name' parameter "
                    "can not have the value 'mask'"
                )
            masked = True
            array = self.filled().array.tolist()
        else:
            masked = False
            array = self.array.tolist()

        units = self.get_units(None)
        if units is None:
            units = ""
        else:
            units = f", units={units!r}"

        calendar = self.get_calendar(None)
        if calendar is None:
            calendar = ""
        else:
            calendar = f", calendar={calendar!r}"

        fill_value = self.get_fill_value(None)
        if fill_value is None:
            fill_value = ""
        else:
            fill_value = f", fill_value={fill_value}"

        dtype = self.dtype.descr[0][1][1:]

        if masked:
            mask = mask.creation_commands(
                name="mask", namespace=namespace0, indent=0, string=True
            )
            mask = mask.replace("mask = ", "mask=", 1)
            mask = f", {mask}"
        else:
            mask = ""

        if name is None:
            name = ""
        else:
            name = name + " = "

        out = []
        out.append(
            f"{name}{namespace}{self.__class__.__name__}({array}{units}"
            f"{calendar}, dtype={dtype!r}{mask}{fill_value})"
        )

        if string:
            indent = " " * indent
            out[0] = indent + out[0]
            out = ("\n" + indent).join(out)

        return out

    @_inplace_enabled(default=False)
    def filled(self, fill_value=None, inplace=False):
        """Replace masked elements with the fill value.

        .. versionadded:: (cfdm) 1.8.7.0

        :Parameters:

            fill_value: scalar, optional
                The fill value. By default the fill returned by
                `get_fill_value` is used, or if this is not set then the
                netCDF default fill value for the data type is used (as
                defined by `netCDF.fillvals`).

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The filled data, or `None` if the operation was in-place.

        **Examples**

        >>> d = {{package}}.{{class}}([[1, 2, 3]])
        >>> print(d.filled().array)
        [[1 2 3]]
        >>> d[0, 0] = {{package}}.masked
        >>> print(d.filled().array)
        [[-9223372036854775806                    2                    3]]
        >>> d.set_fill_value(-99)
        >>> print(d.filled().array)
        [[-99   2   3]]
        >>> print(d.filled(1e10).array)
        [[10000000000           2           3]]

        """
        d = _inplace_enabled_define_and_cleanup(self)

        if fill_value is None:
            fill_value = d.get_fill_value(None)
            if fill_value is None:
                default_fillvals = netCDF4.default_fillvals
                fill_value = default_fillvals.get(d.dtype.str[1:], None)
                if fill_value is None and d.dtype.kind in ("SU"):
                    fill_value = default_fillvals.get("S1", None)

                if fill_value is None:  # should not be None by this stage
                    raise ValueError(
                        "Can't determine fill value for "
                        f"data type {d.dtype.str!r}"
                    )  # pragma: no cover

        array = self.array

        if numpy.ma.isMA(array):
            array = array.filled(fill_value)

        d._set_Array(array, copy=False)

        return d

    @_inplace_enabled(default=False)
    def insert_dimension(self, position=0, inplace=False):
        """Expand the shape of the data array.

        Inserts a new size 1 axis, corresponding to a given position in
        the data array shape.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `flatten`, `squeeze`, `transpose`

        :Parameters:

            position: `int`, optional
                Specify the position that the new axis will have in the
                data array. By default the new axis has position 0, the
                slowest varying position. Negative integers counting from
                the last position are allowed.

                *Parameter example:*
                  ``position=2``

                *Parameter example:*
                  ``position=-1``

            inplace: `bool`, optional
                If True then do the operation in-place and return `None`.

        :Returns:

            `{{class}}` or `None`
                The data with expanded axes. If the operation was in-place
                then `None` is returned.

        **Examples**

        >>> d.shape
        (19, 73, 96)
        >>> d.insert_dimension('domainaxis3').shape
        (1, 96, 73, 19)
        >>> d.insert_dimension('domainaxis3', position=3).shape
        (19, 73, 96, 1)
        >>> d.insert_dimension('domainaxis3', position=-1, inplace=True)
        >>> d.shape
        (19, 73, 1, 96)

        """
        d = _inplace_enabled_define_and_cleanup(self)

        # Parse position
        ndim = d.ndim
        if -ndim - 1 <= position < 0:
            position += ndim + 1
        elif not 0 <= position <= ndim:
            raise ValueError(
                f"Can't insert dimension: Invalid position: {position!r}"
            )

        array = numpy.expand_dims(self.array, position)

        d._set_Array(array, copy=False)

        # Delete hdf5 chunksizes
        d.nc_clear_hdf5_chunksizes()

        return d

    def get_count(self, default=ValueError()):
        """Return the count variable for a compressed array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_index`, `get_list`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if a count
                variable has not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

                The count variable.

        **Examples**

        >>> c = d.get_count()

        """
        try:
            return self._get_Array().get_count()
        except (AttributeError, ValueError):
            return self._default(
                default, f"{self.__class__.__name__!r} has no count variable"
            )

    def get_dependent_tie_points(self, default=ValueError()):
        """Return the list variable for a compressed array.

        .. versionadded:: (cfdm) 1.10.0.1

        .. seealso:: `get_tie_point_indices`,
                     `get_interpolation_parameters`, `get_index`,
                     `get_list`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if no
                dependent tie point index variables have been set. If
                set to an `Exception` instance then it will be raised
                instead.

        :Returns:

            `dict`
                The dependent tie point arrays needed by the
                interpolation method, keyed by the dependent tie point
                identities. Each key is a dependent tie point
                identity, whose value is a `Data` variable.

        **Examples**

        >>> l = d.get_dependent_tie_points()

        """
        try:
            return self._get_Array().get_dependent_tie_points()
        except (AttributeError, ValueError):
            return self._default(
                default,
                f"{self.__class__.__name__!r} has no dependent "
                "tie point index variables",
            )

    def get_index(self, default=ValueError()):
        """Return the index variable for a compressed array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_count`, `get_list`

        :Parameters:

            default: optional
                Return *default* if index variable has not been set.

            default: optional
                Return the value of the *default* parameter if an index
                variable has not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

                The index variable.

        **Examples**

        >>> i = d.get_index()

        """
        try:
            return self._get_Array().get_index()
        except (AttributeError, ValueError):
            return self._default(
                default, f"{self.__class__.__name__!r} has no index variable"
            )

    def get_interpolation_parameters(self, default=ValueError()):
        """Return the list variable for a compressed array.

        .. versionadded:: (cfdm) 1.10.0.1

        .. seealso:: `get_dependent_tie_points`,
                     `get_tie_point_indices`, `get_index`,
                     `get_list`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if no
                interpolation parameters have been set. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `dict`
                Interpolation parameters required by the subsampling
                interpolation method. Each key is an interpolation
                parameter term name, whose value is an
                `InterpolationParameter` variable.

                Interpolation parameter term names for the
                standardised interpolation methods are defined in CF
                Appendix J "Coordinate Interpolation Methods".

        **Examples**

        >>> l = d.get_interpolation_parameters()

        """
        try:
            return self._get_Array().get_interpolation_parameters()
        except (AttributeError, ValueError):
            return self._default(
                default,
                f"{self.__class__.__name__!r} has no subsampling "
                "interpolation parameters",
            )

    def get_list(self, default=ValueError()):
        """Return the list variable for a compressed array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_count`, `get_index`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if an index
                variable has not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

                The list variable.

        **Examples**

        >>> l = d.get_list()

        """
        try:
            return self._get_Array().get_list()
        except (AttributeError, ValueError):
            return self._default(
                default, f"{self.__class__.__name__!r} has no list variable"
            )

    def get_tie_point_indices(self, default=ValueError()):
        """Return the list variable for a compressed array.

        .. versionadded:: (cfdm) 1.10.0.1

        .. seealso:: `get_dependent_tie_points`,
                     `get_interpolation_parameters`,
                     `get_index`, `get_list`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if no tie
                point index variables have been set. If set to an
                `Exception` instance then it will be raised instead.

        :Returns:

            `dict`
                The tie point index variable for each subsampled
                dimension. A key indentifies a subsampled dimension by
                its integer position in the compressed array, and its
                value is a `TiePointIndex` variable.

        **Examples**

        >>> l = d.get_tie_point_indices()

        """
        try:
            return self._get_Array().get_tie_point_indices()
        except (AttributeError, ValueError):
            return self._default(
                default,
                f"{self.__class__.__name__!r} has no "
                "tie point index variables",
            )

    def get_compressed_dimension(self, default=ValueError()):
        """Returns the compressed dimension's array position.

        That is, returns the position of the compressed dimension
        in the compressed array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `compressed_array`, `get_compressed_axes`,
                     `get_compression_type`

        :Parameters:

            default: optional
                Return the value of the *default* parameter there is no
                compressed dimension. If set to an `Exception` instance
                then it will be raised instead.

        :Returns:

            `int`
                The position of the compressed dimension in the compressed
                array.

        **Examples**

        >>> d.get_compressed_dimension()
        2

        """
        try:
            return self._get_Array().get_compressed_dimension()
        except (AttributeError, ValueError):
            return self._default(
                default,
                f"{ self.__class__.__name__!r} has no compressed dimension",
            )

    def _parse_indices(self, indices):
        """Parse indices of the data and return valid indices in a list.

        :Parameters:

            indices: `tuple` (not a `list`!)

        :Returns:

            `list`

        **Examples**


        >>> d = {{package}}.{{class}}(numpy.arange(100, 190).reshape(1, 10, 9))
        >>> d._parse_indices((slice(None, None, None), 1, 2))
        [slice(None, None, None), slice(1, 2, 1), slice(2, 3, 1)]
        >>> d._parse_indices((1,))
        [slice(1, 2, 1), slice(None, None, None), slice(None, None, None)]

        """
        shape = self.shape

        parsed_indices = []

        if not isinstance(indices, tuple):
            indices = (indices,)

        # Initialise the list of parsed indices as the input indices
        # with any Ellipsis objects expanded
        length = len(indices)
        n = len(shape)
        ndim = n
        for index in indices:
            if index is Ellipsis:
                m = n - length + 1
                parsed_indices.extend([slice(None)] * m)
                n -= m
            else:
                parsed_indices.append(index)
                n -= 1

            length -= 1

        len_parsed_indices = len(parsed_indices)

        if ndim and len_parsed_indices > ndim:
            raise IndexError(
                f"Invalid indices for data with shape {shape}: "
                f"{parsed_indices}"
            )

        if len_parsed_indices < ndim:
            parsed_indices.extend([slice(None)] * (ndim - len_parsed_indices))

        if not ndim and parsed_indices:
            raise IndexError(
                "Scalar data can only be indexed with () or Ellipsis"
            )

        for i, (index, size) in enumerate(zip(parsed_indices, shape)):
            if isinstance(index, slice):
                continue

            if isinstance(index, int):
                # E.g. 43 -> slice(43, 44, 1)
                if index < 0:
                    index += size

                index = slice(index, index + 1, 1)
            else:
                if getattr(getattr(index, "dtype", None), "kind", None) == "b":
                    # E.g. index is [True, False, True] -> [0, 2]
                    #
                    # Convert Booleans to non-negative integers. We're
                    # assuming that anything with a dtype attribute also
                    # has a size attribute.
                    if index.size != size:
                        raise IndexError(
                            "Invalid indices for data "
                            f"with shape {shape}: {parsed_indices}"
                        )

                    index = numpy.where(index)[0]

                if not numpy.ndim(index):
                    if index < 0:
                        index += size

                    index = slice(index, index + 1, 1)
                else:
                    len_index = len(index)
                    if len_index == 1:
                        # E.g. [3] -> slice(3, 4, 1)
                        index = index[0]
                        if index < 0:
                            index += size

                        index = slice(index, index + 1, 1)
                    else:
                        # E.g. [1, 3, 4] -> [1, 3, 4]
                        pass

            parsed_indices[i] = index

        return parsed_indices

    def maximum(self, axes=None):
        """Return the maximum of an array or the maximum along axes.

        Missing data array elements are omitted from the calculation.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `minimum`

        :Parameters:

            axes: (sequence of) `int`, optional
                The axes over which to take the maximum. By default the
                maximum over all axes is returned.

                {{axes int examples}}

        :Returns:

            `{{class}}`
                Maximum of the data along the specified axes.

        **Examples**


        >>> d = {{package}}.{{class}}(numpy.arange(24).reshape(1, 2, 3, 4))
        >>> d
        <{{repr}}Data(1, 2, 3, 4): [[[[0, ..., 23]]]]>
        >>> print(d.array)
        [[[[ 0  1  2  3]
           [ 4  5  6  7]
           [ 8  9 10 11]]
          [[12 13 14 15]
           [16 17 18 19]
           [20 21 22 23]]]]
        >>> e = d.max()
        >>> e
        <{{repr}}Data(1, 1, 1, 1): [[[[23]]]]>
        >>> print(e.array)
        [[[[23]]]]
        >>> e = d.max(2)
        >>> e
        <{{repr}}Data(1, 2, 1, 4): [[[[8, ..., 23]]]]>
        >>> print(e.array)
        [[[[ 8  9 10 11]]
          [[20 21 22 23]]]]
        >>> e = d.max([-2, -1])
        >>> e
        <{{repr}}Data(1, 2, 1, 1): [[[[11, 23]]]]>
        >>> print(e.array)
        [[[[11]]
          [[23]]]]

        """
        # Parse the axes. By default flattened input is used.
        try:
            axes = self._parse_axes(axes)
        except ValueError as error:
            raise ValueError(f"Can't find maximum of data: {error}")

        array = self.array
        array = numpy.amax(array, axis=axes, keepdims=True)

        out = self.copy(array=False)
        out._set_Array(array, copy=False)

        if out.shape != self.shape:
            # Delete hdf5 chunksizes
            out.nc_clear_hdf5_chunksizes()

        return out

    def minimum(self, axes=None):
        """Return the minimum of an array or minimum along axes.

        Missing data array elements are omitted from the calculation.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `maximum`

        :Parameters:

            axes: (sequence of) `int`, optional
                The axes over which to take the minimum. By default the
                minimum over all axes is returned.

                {{axes int examples}}

        :Returns:

            `{{class}}`
                Minimum of the data along the specified axes.

        **Examples**


        >>> d = {{package}}.{{class}}(numpy.arange(24).reshape(1, 2, 3, 4))
        >>> d
        <{{repr}}Data(1, 2, 3, 4): [[[[0, ..., 23]]]]>
        >>> print(d.array)
        [[[[ 0  1  2  3]
           [ 4  5  6  7]
           [ 8  9 10 11]]
          [[12 13 14 15]
           [16 17 18 19]
           [20 21 22 23]]]]
        >>> e = d.min()
        >>> e
        <{{repr}}Data(1, 1, 1, 1): [[[[0]]]]>
        >>> print(e.array)
        [[[[0]]]]
        >>> e = d.min(2)
        >>> e
        <{{repr}}Data(1, 2, 1, 4): [[[[0, ..., 15]]]]>
        >>> print(e.array)
        [[[[ 0  1  2  3]]
          [[12 13 14 15]]]]
        >>> e = d.min([-2, -1])
        >>> e
        <{{repr}}Data(1, 2, 1, 1): [[[[0, 12]]]]>
        >>> print(e.array)
        [[[[ 0]]
          [[12]]]]

        """
        # Parse the axes. By default flattened input is used.
        try:
            axes = self._parse_axes(axes)
        except ValueError as error:
            raise ValueError(f"Can't find minimum of data: {error}")

        array = self.array
        array = numpy.amin(array, axis=axes, keepdims=True)

        out = self.copy(array=False)
        out._set_Array(array, copy=False)

        if out.shape != self.shape:
            # Delete hdf5 chunksizes
            out.nc_clear_hdf5_chunksizes()

        return out

    @_inplace_enabled(default=False)
    def squeeze(self, axes=None, inplace=False):
        """Remove size 1 axes from the data.

        By default all size 1 axes are removed, but particular axes may be
        selected with the keyword arguments.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `flatten`, `insert_dimension`, `transpose`

        :Parameters:

            axes: (sequence of) `int`, optional
                The positions of the size one axes to be removed. By
                default all size one axes are removed.

                {{axes int examples}}

            inplace: `bool`, optional
                If True then do the operation in-place and return `None`.

        :Returns:

            `Data` or `None`
                The data with removed data axes. If the operation was
                in-place then `None` is returned.

        **Examples**

        >>> d.shape
        (1, 73, 1, 96)
        >>> f.squeeze().shape
        (73, 96)
        >>> d.squeeze(0).shape
        (73, 1, 96)
        >>> d.squeeze([-3, 2]).shape
        (73, 96)
        >>> d.squeeze(2, inplace=True)
        >>> d.shape
        (1, 73, 96)

        """
        d = _inplace_enabled_define_and_cleanup(self)

        try:
            axes = d._parse_axes(axes)
        except ValueError as error:
            raise ValueError(f"Can't squeeze data: {error}")

        shape = d.shape

        if axes is None:
            axes = tuple([i for i, n in enumerate(shape) if n == 1])
        else:
            # Check the squeeze axes
            for i in axes:
                if shape[i] > 1:
                    raise ValueError(
                        "Can't squeeze data: "
                        f"Can't remove axis of size {shape[i]}"
                    )

        if not axes:
            return d

        array = self.array
        array = numpy.squeeze(array, axes)

        d._set_Array(array, copy=False)

        # Delete hdf5 chunksizes
        d.nc_clear_hdf5_chunksizes()

        return d

    def sum(self, axes=None):
        """Return the sum of an array or the sum along axes.

        Missing data array elements are omitted from the calculation.

        .. seealso:: `max`, `min`

        :Parameters:

            axes: (sequence of) `int`, optional
                The axes over which to calculate the sum. By default the
                sum over all axes is returned.

                {{axes int examples}}

        :Returns:

            `{{class}}`
                The sum of the data along the specified axes.

        **Examples**


        >>> d = {{package}}.{{class}}(numpy.arange(24).reshape(1, 2, 3, 4))
        >>> d
        <{{repr}}Data(1, 2, 3, 4): [[[[0, ..., 23]]]]>
        >>> print(d.array)
        [[[[ 0  1  2  3]
           [ 4  5  6  7]
           [ 8  9 10 11]]
          [[12 13 14 15]
           [16 17 18 19]
           [20 21 22 23]]]]
        >>> e = d.sum()
        >>> e
        <{{repr}}Data(1, 1, 1, 1): [[[[276]]]]>
        >>> print(e.array)
        [[[[276]]]]
        >>> e = d.sum(2)
        >>> e
        <{{repr}}Data(1, 2, 1, 4): [[[[12, ..., 57]]]]>
        >>> print(e.array)
        [[[[12 15 18 21]]
          [[48 51 54 57]]]]
        >>> e = d.sum([-2, -1])
        >>> e
        <{{repr}}Data(1, 2, 1, 1): [[[[66, 210]]]]>
        >>> print(e.array)
        [[[[ 66]]
          [[210]]]]

        """
        # Parse the axes. By default flattened input is used.
        try:
            axes = self._parse_axes(axes)
        except ValueError as error:
            raise ValueError(f"Can't sum data: {error}")
        array = self.array
        array = numpy.sum(array, axis=axes, keepdims=True)

        d = self.copy(array=False)
        d._set_Array(array, copy=False)

        if d.shape != self.shape:
            # Delete hdf5 chunksizes
            d.nc_clear_hdf5_chunksizes()

        return d

    @_inplace_enabled(default=False)
    def transpose(self, axes=None, inplace=False):
        """Permute the axes of the data array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `flatten`, `insert_dimension`, `squeeze`

        :Parameters:

            axes: (sequence of) `int`
                The new axis order. By default the order is reversed.

                {{axes int examples}}

            inplace: `bool`, optional
                If True then do the operation in-place and return `None`.

        :Returns:

            `{{class}}` or `None`
                The data with permuted data axes. If the operation was
                in-place then `None` is returned.

        **Examples**

        >>> d.shape
        (19, 73, 96)
        >>> d.transpose().shape
        (96, 73, 19)
        >>> d.transpose([1, 0, 2]).shape
        (73, 19, 96)
        >>> d.transpose([-1, 0, 1], inplace=True)
        >>> d.shape
        (96, 19, 73)

        """
        d = _inplace_enabled_define_and_cleanup(self)

        ndim = d.ndim

        # Parse the axes. By default, reverse the order of the axes.
        try:
            axes = d._parse_axes(axes)
        except ValueError as error:
            raise ValueError(f"Can't transpose data: {error}")

        if axes is None:
            if ndim <= 1:
                return d

            axes = tuple(range(ndim - 1, -1, -1))
        elif len(axes) != ndim:
            raise ValueError(
                f"Can't transpose data: Axes don't match array: {axes}"
            )

        # Return unchanged if axes are in the same order as the data
        if axes == tuple(range(ndim)):
            return d

        array = self.array
        array = numpy.transpose(array, axes=axes)

        d._set_Array(array, copy=False)

        return d

    def get_compressed_axes(self):
        """Returns the dimensions that are compressed in the array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `compressed_array`, `get_compressed_dimension`,
                     `get_compression_type`

        :Returns:

            `list`
                The dimensions of the data that are compressed to a single
                dimension in the underlying array. If the data are not
                compressed then an empty list is returned.

        **Examples**

        >>> d.shape
        (2, 3, 4, 5, 6)
        >>> d.compressed_array.shape
        (2, 14, 6)
        >>> d.get_compressed_axes()
        [1, 2, 3]

        >>> d.get_compression_type()
        ''
        >>> d.get_compressed_axes()
        []

        """
        ca = self._get_Array(None)

        if ca is None:
            return []

        return ca.get_compressed_axes()

    def get_compression_type(self):
        """Returns the type of compression applied to the array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `compressed_array`, `compression_axes`,
                     `get_compressed_dimension`

        :Returns:

            `str`
                The compression type. An empty string means that no
                compression has been applied.

        **Examples**

        >>> d.get_compression_type()
        ''

        >>> d.get_compression_type()
        'gathered'

        >>> d.get_compression_type()
        'ragged contiguous'

        """
        ma = self._get_Array(None)
        if ma is None:
            return ""

        return ma.get_compression_type()

    @classmethod
    def empty(cls, shape, dtype=None, units=None, calendar=None):
        """Create a new data array without initialising the elements.

        Note that the mask of the returned empty data is hard.

        .. seealso:: `full`, `ones`, `zeros`

        :Parameters:

            shape: `int` or `tuple` of `int`
                The shape of the new array.

            dtype: `numpy.dtype` or any object convertible to `numpy.dtype`
                The data-type of the new array. By default the
                data-type is ``float``.

            units: `str` or `Units`
                The units for the empty data array.

            calendar: `str`, optional
                The calendar for reference time units.

        :Returns:

            `{{class}}`

        **Examples**

        >>> d = {{package}}.{{class}}.empty((96, 73))

        """
        return cls(
            numpy.empty(shape=shape, dtype=dtype),
            units=units,
            calendar=calendar,
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
        ignore_compression=True,
        ignore_type=False,
        _check_values=True,
    ):
        """Whether two data arrays are the same.

        Equality is strict by default. This means that for data arrays to
        be considered equal:

        * the units and calendar must be the same,

        ..

        * the fill value must be the same (see the *ignore_fill_value*
          parameter), and

        ..

        * the arrays must have same shape and data type, the same missing
          data mask, and be element-wise equal (see the *ignore_data_type*
          parameter).

        {{equals tolerance}}

        Any compression is ignored by default, with only the arrays in
        their uncompressed forms being compared. See the
        *ignore_compression* parameter.

        Any type of object may be tested but, in general, equality is only
        possible with another cell measure construct, or a subclass of
        one. See the *ignore_type* parameter.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            other:
                The object to compare for equality.

            {{atol: number, optional}}

            {{rtol: number, optional}}

            ignore_fill_value: `bool`, optional
                If True then the fill value is omitted from the
                comparison.

            {{ignore_data_type: `bool`, optional}}

            {{ignore_compression: `bool`, optional}}

            {{ignore_type: `bool`, optional}}

            {{verbose: `int` or `str` or `None`, optional}}

        :Returns:

            `bool`
                Whether the two data arrays are equal.

        **Examples**

        >>> d.equals(d)
        True
        >>> d.equals(d.copy())
        True
        >>> d.equals('not a data array')
        False

        """
        pp = super()._equals_preprocess(
            other, verbose=verbose, ignore_type=ignore_type
        )

        if pp is True or pp is False:
            return pp

        other = pp

        # Check that each instance has the same shape
        if self.shape != other.shape:
            logger.info(
                f"{self.__class__.__name__}: Different shapes: "
                f"{self.shape} != {other.shape}"
            )  # pragma: no cover
            return False

        # Check that each instance has the same fill value
        if not ignore_fill_value and self.get_fill_value(
            None
        ) != other.get_fill_value(None):
            logger.info(
                f"{self.__class__.__name__}: Different fill value: "
                f"{self.get_fill_value(None)} != {other.get_fill_value(None)}"
            )  # pragma: no cover
            return False

        # Check that each instance has the same data type
        if not ignore_data_type and self.dtype != other.dtype:
            logger.info(
                f"{self.__class__.__name__}: Different data types: "
                f"{self.dtype} != {other.dtype}"
            )  # pragma: no cover
            return False

        # Return now if we have been asked to not check the array
        # values
        if not _check_values:
            return True

        # Check that each instance has the same units
        for attr in ("units", "calendar"):
            x = getattr(self, "get_" + attr)(None)
            y = getattr(other, "get_" + attr)(None)
            if x != y:
                logger.info(
                    f"{self.__class__.__name__}: Different {attr}: "
                    f"{x!r} != {y!r}"
                )  # pragma: no cover
                return False

        if not ignore_compression:
            # --------------------------------------------------------
            # Check for equal compression types
            # --------------------------------------------------------
            compression_type = self.get_compression_type()
            if compression_type != other.get_compression_type():
                logger.info(
                    f"{self.__class__.__name__}: Different compression types: "
                    f"{compression_type} != {other.get_compression_type()}"
                )  # pragma: no cover

                return False

            # --------------------------------------------------------
            # Check for equal compressed array values
            # --------------------------------------------------------
            if compression_type:
                if not self._equals(
                    self.compressed_array,
                    other.compressed_array,
                    rtol=rtol,
                    atol=atol,
                ):
                    logger.info(
                        f"{self.__class__.__name__}: Different compressed "
                        "array values"
                    )  # pragma: no cover
                    return False

        # ------------------------------------------------------------
        # Check for equal (uncompressed) array values
        # ------------------------------------------------------------
        if not self._equals(
            self.array,
            other.array,
            ignore_data_type=ignore_data_type,
            rtol=rtol,
            atol=atol,
        ):
            logger.info(
                f"{self.__class__.__name__}: Different array values "
                f"(atol={atol}, rtol={rtol})"
            )  # pragma: no cover

            return False

        # ------------------------------------------------------------
        # Still here? Then the two data arrays are equal.
        # ------------------------------------------------------------
        return True

    def get_filenames(self):
        """Return the name of the file containing the data array.

        .. seealso:: `original_filenames`

        :Returns:

            `set`
                The file name in normalised, absolute form. If the
                data is are memory then an empty `set` is returned.

        **Examples**

        >>> f = {{package}}.example_field(0)
        >>> {{package}}.write(f, 'temp_file.nc')
        >>> g = {{package}}.read('temp_file.nc')[0]
        >>> d = g.data
        >>> d.get_filenames()
        {'/data/user/temp_file.nc'}
        >>> d[...] = -99
        >>> d.get_filenames()
        set()

        """
        source = self.source(None)
        if source is None:
            return set()

        try:
            filename = source.get_filename()
        except AttributeError:
            return set()
        else:
            return set((abspath(filename),))

    def first_element(self):
        """Return the first element of the data as a scalar.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `last_element`, `second_element`

        :Returns:

                The first element of the data.

        **Examples**

        >>> d = {{package}}.{{class}}(9.0)
        >>> x = d.first_element()
        >>> print(x, type(x))
        9.0 <class 'float'>

        >>> d = {{package}}.{{class}}([[1, 2], [3, 4]])
        >>> x = d.first_element()
        >>> print(x, type(x))
        1 <class 'int'>
        >>> d[0, 0] = {{package}}.masked
        >>> y = d.first_element()
        >>> print(y, type(y))
        -- <class 'numpy.ma.core.MaskedConstant'>

        >>> d = {{package}}.{{class}}(['foo', 'bar'])
        >>> x = d.first_element()
        >>> print(x, type(x))
        foo <class 'str'>

        """
        return self._item((slice(0, 1, 1),) * self.ndim)

    @_inplace_enabled(default=False)
    def flatten(self, axes=None, inplace=False):
        """Flatten axes of the data.

        Any subset of the axes may be flattened.

        The shape of the data may change, but the size will not.

        The flattening is executed in row-major (C-style) order. For
        example, the array ``[[1, 2], [3, 4]]`` would be flattened across
        both dimensions to ``[1 2 3 4]``.

        .. versionadded:: (cfdm) 1.7.11

        .. seealso:: `insert_dimension`, `squeeze`, `transpose`

        :Parameters:

            axes: (sequence of) `int`, optional
                Select the axes. By default all axes are flattened. No
                axes are flattened if *axes* is an empty sequence.

                {{axes int examples}}

            inplace: `bool`, optional
                If True then do the operation in-place and return `None`.

        :Returns:

            `Data` or `None`
                The flattened data, or `None` if the operation was
                in-place.

        **Examples**


        >>> d = {{package}}.{{class}}(numpy.arange(24).reshape(1, 2, 3, 4))
        >>> d
        <{{repr}}Data(1, 2, 3, 4): [[[[0, ..., 23]]]]>
        >>> print(d.array)
        [[[[ 0  1  2  3]
           [ 4  5  6  7]
           [ 8  9 10 11]]
          [[12 13 14 15]
           [16 17 18 19]
           [20 21 22 23]]]]

        >>> e = d.flatten()
        >>> e
        <{{repr}}Data(24): [0, ..., 23]>
        >>> print(e.array)
        [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23]

        >>> e = d.flatten([])
        >>> e
        <{{repr}}Data(1, 2, 3, 4): [[[[0, ..., 23]]]]>

        >>> e = d.flatten([1, 3])
        >>> e
        <{{repr}}Data(1, 8, 3): [[[0, ..., 23]]]>
        >>> print(e.array)
        [[[ 0  4  8]
          [ 1  5  9]
          [ 2  6 10]
          [ 3  7 11]
          [12 16 20]
          [13 17 21]
          [14 18 22]
          [15 19 23]]]

        >>> d.flatten([0, -1], inplace=True)
        >>> d
        <{{repr}}Data(4, 2, 3): [[[0, ..., 23]]]>
        >>> print(d.array)
        [[[ 0  4  8]
          [12 16 20]]
         [[ 1  5  9]
          [13 17 21]]
         [[ 2  6 10]
          [14 18 22]]
         [[ 3  7 11]
          [15 19 23]]]

        """
        d = _inplace_enabled_define_and_cleanup(self)

        try:
            axes = d._parse_axes(axes)
        except ValueError as error:
            raise ValueError(f"Can't flatten data: {error}")

        ndim = d.ndim

        if ndim <= 1:
            return d

        if axes is None:
            # By default flatten all axes
            axes = tuple(range(ndim))
        else:
            if len(axes) <= 1:
                return d

            # Note that it is important that the first axis in the
            # list is the left-most flattened axis
            axes = sorted(axes)

        # Save the shape before we transpose
        shape = list(d.shape)

        order = [i for i in range(ndim) if i not in axes]
        order[axes[0] : axes[0]] = axes

        d.transpose(order, inplace=True)

        new_shape = [n for i, n in enumerate(shape) if i not in axes]
        new_shape.insert(axes[0], numpy.prod([shape[i] for i in axes]))

        array = d.array.reshape(new_shape)

        out = type(self)(
            array,
            units=d.get_units(None),
            calendar=d.get_calendar(None),
            fill_value=d.get_fill_value(None),
        )

        if inplace:
            d.__dict__ = out.__dict__

        return out

    def last_element(self):
        """Return the last element of the data as a scalar.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `first_element`, `second_element`

        :Returns:

                The last element of the data.

        **Examples**

        >>> d = {{package}}.{{class}}(9.0)
        >>> x = d.last_element()
        >>> print(x, type(x))
        9.0 <class 'float'>

        >>> d = {{package}}.{{class}}([[1, 2], [3, 4]])
        >>> x = d.last_element()
        >>> print(x, type(x))
        4 <class 'int'>
        >>> d[-1, -1] = {{package}}.masked
        >>> y = d.last_element()
        >>> print(y, type(y))
        -- <class 'numpy.ma.core.MaskedConstant'>

        >>> d = {{package}}.{{class}}(['foo', 'bar'])
        >>> x = d.last_element()
        >>> print(x, type(x))
        bar <class 'str'>

        """
        return self._item((slice(-1, None, 1),) * self.ndim)

    def second_element(self):
        """Return the second element of the data as a scalar.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `first_element`, `last_element`

        :Returns:

                The second element of the data.

        **Examples**

        >>> d = {{package}}.{{class}}([[1, 2], [3, 4]])
        >>> x = d.second_element()
        >>> print(x, type(x))
        2 <class 'int'>
        >>> d[0, 1] = {{package}}.masked
        >>> y = d.second_element()
        >>> print(y, type(y))
        -- <class 'numpy.ma.core.MaskedConstant'>

        >>> d = {{package}}.{{class}}(['foo', 'bar'])
        >>> x = d.second_element()
        >>> print(x, type(x))
        bar <class 'str'>

        """
        return self._item(
            (slice(0, 1, 1),) * (self.ndim - 1) + (slice(1, 2, 1),)
        )

    @_inplace_enabled(default=False)
    def to_memory(self, inplace=False):
        """Bring data on disk into memory.

        There is no change to data that is already in memory.

        :Parameters:

            inplace: `bool`, optional
                If True then do the operation in-place and return `None`.

        :Returns:

            `{{class}}` or `None`
                A copy of the data in memory, or `None` if the
                operation was in-place.

        **Examples**

        >>> f = {{package}}.example_field(4)
        >>> f.data
        <{{repr}}Data(3, 26, 4): [[[290.0, ..., --]]] K>
        >>> f.data.to_memory()

        """
        d = _inplace_enabled_define_and_cleanup(self)
        d._set_Array(self.source().to_memory())
        return d

    @_inplace_enabled(default=False)
    def uncompress(self, inplace=False):
        """Uncompress the underlying array.

        .. versionadded:: (cfdm) 1.7.3

        .. seealso:: `array`, `compressed_array`, `source`

        :Parameters:

            inplace: `bool`, optional
                If True then do the operation in-place and return `None`.

        :Returns:

            `{{class}}` or `None`
                The uncompressed data, or `None` if the operation was
                in-place.

        **Examples**

        >>> d.get_compression_type()
        'ragged contiguous'
        >>> d.source()
        <RaggedContiguousArray(4, 9): >
        >>> d.uncompress(inpalce=True)
        >>> d.get_compression_type()
        ''
        >>> d.source()
        <NumpyArray(4, 9): >

        """
        d = _inplace_enabled_define_and_cleanup(self)

        if d.get_compression_type():
            d._set_Array(d.array, copy=False)

        return d

    def unique(self):
        """The unique elements of the data.

        The unique elements are sorted into a one dimensional array. with
        no missing values.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `{{class}}`
                The unique elements.

        **Examples**

        >>> d = {{package}}.{{class}}([[4, 2, 1], [1, 2, 3]], 'metre')
        >>> d.unique()
        <{{repr}}Data(4): [1, ..., 4] metre>
        >>> d[1, -1] = {{package}}.masked
        >>> d.unique()
        <{{repr}}Data(3): [1, 2, 4] metre>

        """
        array = self.array
        array = numpy.unique(array)

        if numpy.ma.is_masked(array):
            array = array.compressed()

        d = self.copy(array=False)
        d._set_Array(array, copy=False)

        if d.shape != self.shape:
            # Delete hdf5 chunksizes
            d.nc_clear_hdf5_chunksizes()

        return d

    # ----------------------------------------------------------------
    # Aliases
    # ----------------------------------------------------------------
    def max(self, axes=None):
        """Alias for `maximum`."""
        return self.maximum(axes=axes)

    def min(self, axes=None):
        """Alias for `minimum`."""
        return self.minimum(axes=axes)
