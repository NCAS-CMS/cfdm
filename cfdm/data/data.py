import logging
import math
import operator
from itertools import product, zip_longest
from math import prod
from numbers import Integral
from os.path import commonprefix

import dask.array as da
import numpy as np
from dask.base import collections_to_expr, is_dask_collection, tokenize
from dask.optimization import cull
from netCDF4 import default_fillvals
from scipy.sparse import issparse

from .. import core
from ..constants import masked
from ..decorators import (
    _inplace_enabled,
    _inplace_enabled_define_and_cleanup,
    _manage_log_level_via_verbosity,
)
from ..functions import (
    _DEPRECATION_ERROR_KWARGS,
    _numpy_allclose,
    is_log_level_info,
    parse_indices,
)
from ..mixin.container import Container
from ..mixin.files import Files
from ..mixin.netcdf import NetCDFAggregation, NetCDFChunks
from ..units import Units
from .abstract import Array
from .creation import to_dask
from .dask_utils import (
    cfdm_filled,
    cfdm_harden_mask,
    cfdm_soften_mask,
    cfdm_to_memory,
    cfdm_where,
)
from .utils import (
    allclose,
    chunk_indices,
    chunk_positions,
    collapse,
    convert_to_datetime,
    convert_to_reftime,
    first_non_missing_value,
    generate_axis_identifiers,
    is_numeric_dtype,
    new_axis_identifier,
)

logger = logging.getLogger(__name__)


class Data(Container, NetCDFAggregation, NetCDFChunks, Files, core.Data):
    """An N-dimensional data array with units and masked values.

    * Contains an N-dimensional, indexable and broadcastable array with
      many similarities to a `numpy` array.

    * Contains the units of the array elements.

    * Supports masked arrays, regardless of whether or not it was
      initialised with a masked array.

    * Stores and operates on data arrays which are larger than the
      available memory.

    **Indexing**

    A data array is indexable in a similar way to a numpy array:

    >>> d.shape
    (12, 19, 73, 96)
    >>> d[...].shape
    (12, 19, 73, 96)
    >>> d[slice(0, 9), 10:0:-2, :, :].shape
    (9, 5, 73, 96)

    There are three extensions to the numpy indexing functionality:

    * Size 1 dimensions are never removed by indexing.

      An integer index i takes the i-th element but does not reduce the
      rank of the output array by one:

      >>> d.shape
      (12, 19, 73, 96)
      >>> d[0, ...].shape
      (1, 19, 73, 96)
      >>> d[:, 3, slice(10, 0, -2), 95].shape
      (12, 1, 5, 1)

      Size 1 dimensions may be removed with the `squeeze` method.

    * The indices for each axis work independently.

      When more than one dimension's slice is a 1-d Boolean sequence or
      1-d sequence of integers, then these indices work independently
      along each dimension (similar to the way vector subscripts work in
      Fortran), rather than by their elements:

      >>> d.shape
      (12, 19, 73, 96)
      >>> d[0, :, [0, 1], [0, 13, 27]].shape
      (1, 19, 2, 3)

    * Boolean indices may be any object which exposes the numpy array
      interface.

      >>> d.shape
      (12, 19, 73, 96)
      >>> d[..., d[0, 0, 0] > d[0, 0, 0].min()]

    """

    # Constants used to specify which components should be cleared
    # when a new dask array is set. See `_clear_after_dask_update` for
    # details.
    #
    # These must constants must have values 2**N (N>=1), except for
    # `_NONE` which must be 0, and `_ALL` which must be the sum of
    # other constants. It is therefore convenient to define these
    # constants in binary.
    _NONE = 0b000
    _ARRAY = 0b001
    _CACHE = 0b010
    _CFA = 0b100
    _ALL = 0b111

    # The default mask hardness
    _DEFAULT_HARDMASK = True

    def __new__(cls, *args, **kwargs):
        """Store component classes."""
        instance = super().__new__(cls)
        instance._Units_class = Units
        return instance

    def __init__(
        self,
        array=None,
        units=None,
        calendar=None,
        fill_value=None,
        hardmask=True,
        chunks="auto",
        dt=False,
        source=None,
        copy=True,
        dtype=None,
        mask=None,
        mask_value=None,
        to_memory=False,
        init_options=None,
        _use_array=True,
    ):
        """**Initialisation**

        :Parameters:

            array: optional
                The array of values. May be a scalar or array-like
                object, including another `Data` instance, anything
                with a `!to_dask_array` method, `numpy` array, `dask`
                array, `xarray` array, `{{package}}.Array` subclass, `list`,
                `tuple`, scalar.

                *Parameter example:*
                  ``array=34.6``

                *Parameter example:*
                  ``array=[[1, 2], [3, 4]]``

                *Parameter example:*
                  ``array=numpy.ma.arange(10).reshape(2, 1, 5)``

            units: `str` or `Units`, optional
                The physical units of the data. if a `Units` object is
                provided then this an also set the calendar.

                The units (without the calendar) may also be set after
                initialisation with the `set_units` method.

                *Parameter example:*
                  ``units='km hr-1'``

                *Parameter example:*
                  ``units='days since 2018-12-01'``

            calendar: `str`, optional
                The calendar for reference time units.

                The calendar may also be set after initialisation with the
                `set_calendar` method.

                *Parameter example:*
                  ``calendar='360_day'``

            fill_value: optional
                The fill value of the data. By default, or if set to
                `None`, the `numpy` fill value appropriate to the array's
                data-type will be used (see
                `numpy.ma.default_fill_value`).

                The fill value may also be set after initialisation with
                the `set_fill_value` method.

                *Parameter example:*
                  ``fill_value=-999.``

            dtype: data-type, optional
                The desired data-type for the data. By default the
                data-type will be inferred form the *array*
                parameter.

                The data-type may also be set after initialisation with
                the `dtype` attribute.

                *Parameter example:*
                    ``dtype=float``

                *Parameter example:*
                    ``dtype='float32'``

                *Parameter example:*
                    ``dtype=numpy.dtype('i2')``

                .. versionadded:: 3.0.4

            mask: optional
                Apply this mask to the data given by the *array*
                parameter. By default, or if *mask* is `None`, no mask
                is applied. May be any scalar or array-like object
                (such as a `list`, `numpy` array or `Data` instance)
                that is broadcastable to the shape of *array*. Masking
                will be carried out where the mask elements evaluate
                to `True`.

                This mask will applied in addition to any mask already
                defined by the *array* parameter.

            mask_value: scalar array_like
                Mask *array* where it is equal to *mask_value*, using
                numerically tolerant floating point equality.

                .. versionadded:: (cfdm) 1.11.0.0

            hardmask: `bool`, optional
                If True (the default) then the mask is hard. If False
                then the mask is soft.

            dt: `bool`, optional
                If True then strings (such as ``'1990-12-01 12:00'``)
                given by the *array* parameter are re-interpreted as
                date-time objects. By default they are not.

            {{init source: optional}}

            {{init copy: `bool`, optional}}

            {{chunks: `int`, `tuple`, `dict` or `str`, optional}}

                .. versionadded:: (cfdm) 1.11.2.0

            to_memory: `bool`, optional
                If True then ensure that the original data are in
                memory, rather than on disk.

                If the original data are on disk, then reading data
                into memory during initialisation will slow down the
                initialisation process, but can considerably improve
                downstream performance by avoiding the need for
                independent reads for every dask chunk, each time the
                data are computed.

                In general, setting *to_memory* to True is not the same
                as calling the `persist` of the newly created `Data`
                object, which also decompresses data compressed by
                convention and computes any data type, mask and
                date-time modifications.

                If the input *array* is a `dask.array.Array` object
                then *to_memory* is ignored.

                .. versionadded:: (cfdm) 1.11.2.0

            init_options: `dict`, optional
                Provide optional keyword arguments to methods and
                functions called during the initialisation process. A
                dictionary key identifies a method or function. The
                corresponding value is another dictionary whose
                key/value pairs are the keyword parameter names and
                values to be applied.

                Supported keys are:

                * ``'from_array'``: Provide keyword arguments to
                  the `dask.array.from_array` function. This is used
                  when initialising data that is not already a dask
                  array and is not compressed by convention.

                * ``'first_non_missing_value'``: Provide keyword
                  arguments to the
                  `cfdm.data.utils.first_non_missing_value`
                  function. This is used when the input array contains
                  date-time strings or objects, and may affect
                  performance.

                 *Parameter example:*
                   ``{'from_array': {'inline_array': True}}``

        **Examples**

        >>> d = {{package}}.Data(5)
        >>> d = {{package}}.Data([1,2,3], units='K')
        >>> import numpy
        >>> d = {{package}}.Data(numpy.arange(10).reshape(2,5),
        ...             units='m/s', fill_value=-999)
        >>> d = {{package}}.Data('fly')
        >>> d = {{package}}.Data(tuple('fly'))

        """
        if source is None and isinstance(array, self.__class__):
            source = array

        if init_options is None:
            init_options = {}

        if source is not None:
            try:
                array = source._get_Array(None)
            except AttributeError:
                array = None

            super().__init__(
                source=source, _use_array=_use_array and array is not None
            )
            if _use_array:
                try:
                    array = source.to_dask_array(
                        _force_mask_hardness=False, _force_to_memory=False
                    )
                except (AttributeError, TypeError):
                    try:
                        array = source.to_dask_array()
                    except AttributeError:
                        pass
                    else:
                        self._set_dask(
                            array,
                            copy=copy,
                            clear=self._NONE,
                            in_memory=getattr(source, "__in_memory__", None),
                        )
                else:
                    self._set_dask(
                        array,
                        copy=copy,
                        clear=self._NONE,
                        in_memory=getattr(source, "__in_memory__", None),
                    )
            else:
                self._del_dask(None, clear=self._NONE)

            # Units
            try:
                self._Units = source.Units
            except (ValueError, AttributeError):
                self._Units = self._Units_class(
                    self.get_units(None), self.get_calendar(None)
                )

            # Axis identifiers
            try:
                self._axes = source._axes
            except (ValueError, AttributeError):
                try:
                    self._axes = generate_axis_identifiers(source.ndim)
                except AttributeError:
                    pass

            # Cached elements
            try:
                self._set_cached_elements(source._get_cached_elements())
            except AttributeError:
                pass

            # Mask hardness
            self.hardmask = getattr(source, "hardmask", self._DEFAULT_HARDMASK)

            # Indexing flags
            self.__keepdims_indexing__ = getattr(
                source, "__keepdims_indexing__", True
            )
            self.__orthogonal_indexing__ = getattr(
                source, "__orthogonal_indexing__", True
            )

            # Deterministic name
            try:
                deterministic = source.has_deterministic_name()
            except AttributeError:
                deterministic = False

            self._custom["has_deterministic_name"] = bool(deterministic)

            return

        super().__init__(
            array=array,
            fill_value=fill_value,
            _use_array=False,
        )

        # Set the units
        units = self._Units_class(units, calendar=calendar)
        self._Units = units

        # Set the mask hardness
        self.hardmask = hardmask

        if array is None:
            # No data has been set
            return

        # Is the array a sparse array?
        sparse_array = issparse(array)

        # Is the array data in memory?
        if sparse_array or isinstance(array, (np.ndarray, list, tuple)):
            in_memory = True
        else:
            in_memory = getattr(array, "__in_memory__", None)

        try:
            ndim = array.ndim
        except AttributeError:
            ndim = np.ndim(array)

        # Create the _axes attribute: an ordered sequence of unique
        # names (within this instance) for each array axis.
        self._axes = generate_axis_identifiers(ndim)

        if not _use_array:
            return

        # Still here? Then create a dask array and store it.

        # Find out if the input data is compressed by convention
        try:
            compressed = array.get_compression_type()
        except AttributeError:
            compressed = ""

        if compressed and init_options.get("from_array"):
            raise ValueError(
                "Can't define 'from_array' initialisation options "
                "for compressed input arrays"
            )

        # Bring data into memory (compressed data is not decompressed)
        if to_memory:
            try:
                array = array.to_memory()
            except AttributeError:
                pass

        # Deterministic name
        self._custom["has_deterministic_name"] = not is_dask_collection(array)

        if self._is_abstract_Array_subclass(array):
            # Save the input array in case it's useful later. For
            # compressed input arrays this will contain extra
            # information, such as a count or index variable.
            self._set_Array(array)

        # Cast the input data as a dask array
        kwargs = init_options.get("from_array", {})
        if "chunks" in kwargs:
            raise TypeError(
                "Can't define 'chunks' in the 'from_array' initialisation "
                "options. Use the 'chunks' parameter instead."
            )

        dx = to_dask(array, chunks, **kwargs)

        # Find out if we have an array of date-time objects
        if units.isreftime:
            dt = True

        first_value = None
        if not dt and dx.dtype.kind == "O":
            kwargs = init_options.get("first_non_missing_value", {})
            first_value = first_non_missing_value(dx, **kwargs)

            if first_value is not None:
                dt = hasattr(first_value, "timetuple")

        # Convert string or object date-times to floating point
        # reference times
        if dt and dx.dtype.kind in "USO":
            dx, units = convert_to_reftime(dx, units, first_value)
            # Reset the units
            self._Units = units

        # Store the dask array
        self._set_dask(dx, clear=self._NONE, in_memory=in_memory)

        # Override the data type
        if dtype is not None:
            self.dtype = dtype

        # Apply a mask
        if mask is not None:
            if sparse_array:
                raise ValueError("Can't mask a sparse array")

            self.masked_where(mask, inplace=True)

        # Apply masked values
        if mask_value is not None:
            if sparse_array:
                raise ValueError("Can't mask a sparse array")

            self.masked_values(mask_value, inplace=True)

    def __bool__(self):
        """Truth value testing and the built-in operation `bool`

        x.__bool__() <==> bool(x)

        **Performance**

        `__bool__` causes all delayed operations to be computed.

        **Examples**

        >>> bool({{package}}.Data(1.5))
        True
        >>> bool({{package}}.Data([[False]]))
        False

        """
        size = self.size
        if size != 1:
            raise ValueError(
                f"The truth value of a {self.__class__.__name__} with {size} "
                "elements is ambiguous. Use d.any() or d.all()"
            )

        return bool(self.to_dask_array())

    def __float__(self):
        """Called to implement the built-in function `float`

        x.__float__() <==> float(x)

        **Performance**

        `__float__` causes all delayed operations to be executed,
        unless the dask array size is already known to be greater than
        1.

        """
        if self.size != 1:
            raise TypeError(
                "only length-1 arrays can be converted to "
                f"Python scalars. Got {self}"
            )

        return float(self.array[(0,) * self.ndim])

    def __format__(self, format_spec):
        """Interpret format specifiers for size 1 arrays.

        **Examples**

        >>> d = {{package}}.Data(9, 'metres')
        >>> f"{d}"
        '9 metres'
        >>> f"{d!s}"
        '9 metres'
        >>> f"{d!r}"
        '<{{repr}}Data(): 9 metres>'
        >>> f"{d:.3f}"
        '9.000'

        >>> d = {{package}}.Data([[9]], 'metres')
        >>> f"{d}"
        '[[9]] metres'
        >>> f"{d!s}"
        '[[9]] metres'
        >>> f"{d!r}"
        '<{{repr}}Data(1, 1): [[9]] metres>'
        >>> f"{d:.3f}"
        '9.000'

        >>> d = {{package}}.Data([9, 10], 'metres')
        >>> f"{d}"
        >>> '[9, 10] metres'
        >>> f"{d!s}"
        >>> '[9, 10] metres'
        >>> f"{d!r}"
        '<{{repr}}Data(2): [9, 10] metres>'
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
            f"Can't format Data array of size {n} (greater than 1) with "
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
          the same behaviour as indexing on a `netCDF4.Variable` object.

        **Performance**

        If the shape of the data is unknown then it is calculated
        immediately by executing all delayed operations.

        .. seealso:: `__keepdims_indexing__`,
                     `__orthogonal_indexing__`, `__setitem__`

        :Returns:

            `Data`
                The subspace of the data.

        **Examples**

        >>> import numpy
        >>> d = {{package}}.Data(numpy.arange(100, 190).reshape(1, 10, 9))
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
        if indices is Ellipsis:
            return self.copy()

        original_indices = indices
        original_shape = self.shape
        keepdims = self.__keepdims_indexing__

        indices = parse_indices(
            original_shape, original_indices, keepdims=keepdims
        )

        new = self.copy()
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )

        # ------------------------------------------------------------
        # Subspace the dask array
        # ------------------------------------------------------------
        if self.__orthogonal_indexing__:
            # Apply 'orthogonal indexing': indices that are 1-d arrays
            # or lists subspace along each dimension
            # independently. This behaviour is similar to Fortran, but
            # different to dask.
            axes_with_list_indices = [
                i
                for i, x in enumerate(indices)
                if isinstance(x, list) or getattr(x, "shape", False)
            ]
            n_axes_with_list_indices = len(axes_with_list_indices)

            if n_axes_with_list_indices < 2:
                # At most one axis has a list/1-d array index so do a
                # normal dask subspace
                dx = dx[tuple(indices)]
            else:
                # At least two axes have list/1-d array indices so we
                # can't do a normal dask subspace

                # Subspace axes which have list/1-d array indices
                for axis in axes_with_list_indices:
                    dx = da.take(dx, indices[axis], axis=axis)

                if n_axes_with_list_indices < len(indices):
                    # Subspace axes which don't have list/1-d array
                    # indices. (Do this after subspacing axes which do
                    # have list/1-d array indices, in case
                    # __keepdims_indexing__ is False.)
                    slice_indices = [
                        slice(None) if i in axes_with_list_indices else x
                        for i, x in enumerate(indices)
                    ]
                    dx = dx[tuple(slice_indices)]
        else:
            raise NotImplementedError(
                "Non-orthogonal indexing has not yet been implemented"
            )

        # ------------------------------------------------------------
        # Set the subspaced dask array
        # ------------------------------------------------------------
        new._set_dask(dx, clear=self._ALL ^ self._CFA, in_memory=None)

        if 0 in new.shape:
            raise IndexError(
                f"Index [{original_indices}] selects no elements from "
                f"data with shape {original_shape}"
            )

        # ------------------------------------------------------------
        # Get the axis identifiers for the subspace
        # ------------------------------------------------------------
        if not keepdims:
            new_axes = [
                axis
                for axis, x in zip(self._axes, indices)
                if not isinstance(x, Integral) and getattr(x, "shape", True)
            ]
            new._axes = new_axes

        # Update the dataset chunking strategy
        chunksizes = new.nc_dataset_chunksizes()
        if (
            chunksizes
            and isinstance(chunksizes, tuple)
            and new.shape != original_shape
        ):
            if keepdims:
                new.nc_set_dataset_chunksizes(chunksizes)
            else:
                new.nc_clear_dataset_chunksizes()

        return new

    def __int__(self):
        """Called to implement the built-in function `int`

        x.__int__() <==> int(x)

        **Performance**

        `__int__` causes all delayed operations to be executed, unless
        the dask array size is already known to be greater than 1.

        """
        if self.size != 1:
            raise TypeError(
                "only length-1 arrays can be converted to "
                f"Python scalars. Got {self}"
            )

        return int(self.array[(0,) * self.ndim])

    def __iter__(self):
        """Called when an iterator is required.

        x.__iter__() <==> iter(x)

        **Performance**

        If the shape of the data is unknown then it is calculated
        immediately by executing all delayed operations.

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3], 'metres')
        >>> for e in d:
        ...     print(repr(e))
        ...
        <{{repr}}Data(1): [1] metres>
        <{{repr}}Data(1): [2] metres>
        <{{repr}}Data(1): [3] metres>

        >>> d = {{package}}.Data([[1, 2], [3, 4]], 'metres')
        >>> for e in d:
        ...     print(repr(e))
        ...
        <{{repr}}Data: [1, 2] metres>
        <{{repr}}Data: [3, 4] metres>

        >>> d = {{package}}.Data(99, 'metres')
        >>> for e in d:
        ...     print(repr(e))
        ...
        Traceback (most recent call last):
            ...
        TypeError: iteration over a 0-d Data

        """
        try:
            n = len(self)
        except TypeError:
            raise TypeError(f"iteration over a 0-d {self.__class__.__name__}")

        if self.__keepdims_indexing__:
            for i in range(n):
                out = self[i]
                out.reshape(out.shape[1:], inplace=True)
                yield out
        else:
            for i in range(n):
                yield self[i]

    def __len__(self):
        """Called to implement the built-in function `len`.

        x.__len__() <==> len(x)

        **Performance**

        If the shape of the data is unknown then it is calculated
        immediately by executing all delayed operations.

        **Examples**

        >>> len({{package}}.Data([1, 2, 3]))
        3
        >>> len({{package}}.Data([[1, 2, 3]]))
        1
        >>> len({{package}}.Data([[1, 2, 3], [4, 5, 6]]))
        2
        >>> len({{package}}.Data(1))
        Traceback (most recent call last):
            ...
        TypeError: len() of unsized object

        """
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        if math.isnan(dx.size):
            logger.debug("Computing data len: Performance may be degraded")
            dx.compute_chunk_sizes()

        return len(dx)

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

        return f"<{self.__class__.__name__}{shape}: {self}>"

    def __setitem__(self, indices, value):
        """Implement indexed assignment.

        x.__setitem__(indices, y) <==> x[indices]=y

        Assignment to data array elements defined by indices.

        Elements of a data array may be changed by assigning values to
        a subspace. See `__getitem__` for details on how to define
        subspace of the data array.

        **Missing data**

        The treatment of missing data elements during assignment to a
        subspace depends on the value of the `hardmask` attribute. If
        it is True then masked elements will not be unmasked,
        otherwise masked elements may be set to any value.

        In either case, unmasked elements may be set, (including
        missing data).

        Unmasked elements may be set to missing data by assignment to
        the `{{package}}.masked` constant or by assignment to a value
        which contains masked elements.

        **Performance**

        If the shape of the data is unknown then it is calculated
        immediately by executing all delayed operations.

        If indices for two or more dimensions are lists or 1-d arrays
        of Booleans or integers, and any of these are dask
        collections, then these dask collections will be
        computed immediately.

        .. seealso:: `__getitem__`, `__keedims_indexing__`,
                     `__orthogonal_indexing__`, `{{package}}.masked`,
                     `hardmask`

        """
        original_shape = self.shape

        indices = parse_indices(
            original_shape,
            indices,
            keepdims=self.__keepdims_indexing__,
        )

        axes_with_list_indices = [
            i
            for i, x in enumerate(indices)
            if isinstance(x, list) or getattr(x, "shape", False)
        ]

        # When there are two or more 1-d array indices of Booleans or
        # integers, convert them to slices, if possible.
        #
        # Note: If any of these 1-d arrays is a dask collection, then
        #       this will be computed.
        if len(axes_with_list_indices) > 1:
            for i, index in enumerate(indices):
                if not (
                    isinstance(index, list) or getattr(index, "shape", False)
                ):
                    # Not a 1-d array
                    continue

                index = np.array(index)

                size = original_shape[i]
                if index.dtype == bool:
                    # Convert True values to integers
                    index = np.arange(size)[index]
                else:
                    # Make sure all integer values are non-negative
                    index = np.where(index < 0, index + size, index)

                if size == 1:
                    start = index[0]
                    index = slice(start, start + 1)
                else:
                    steps = index[1:] - index[:-1]
                    step = steps[0]
                    if step and not (steps - step).any():
                        # Array has a regular step, and so can be
                        # converted to a slice.
                        if step > 0:
                            start, stop = index[0], index[-1] + 1
                        elif step < 0:
                            start, stop = index[0], index[-1] - 1

                        if stop < 0:
                            stop = None

                        index = slice(start, stop, step)

                indices[i] = index

        dx = self.to_dask_array(
            _force_mask_hardness=True, _force_to_memory=True
        )

        # Do the assignment
        self._set_subspace(dx, indices, value)
        self._set_dask(dx, clear=self._ALL ^ self._CFA, in_memory=True)

        return

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
            first = "??"

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
                        np.ma.array(first, mask=mask[0]), units, calendar
                    ).datetime_array
                except Exception:
                    first = "??"

            out = f"{open_brackets}{first}{close_brackets}"
        else:
            try:
                last = self.last_element()
            except Exception:
                last = "??"

            if isreftime:
                if last is np.ma.masked:
                    last = 0
                    mask[-1] = True

                # Convert reference times to date-times
                try:
                    first, last = type(self)(
                        np.ma.array([first, last], mask=(mask[0], mask[-1])),
                        units,
                        calendar,
                    ).datetime_array
                except Exception:
                    first, last = ("??", "??")

            if size > 3:
                out = f"{open_brackets}{first}, ..., {last}{close_brackets}"
            elif shape[-1:] == (3,):
                try:
                    middle = self.second_element()
                except Exception:
                    last = "??"

                if isreftime:
                    # Convert reference time to date-time
                    if middle is np.ma.masked:
                        middle = 0
                        mask[1] = True

                    try:
                        middle = type(self)(
                            np.ma.array(middle, mask=mask[1]),
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

    def __eq__(self, other):
        """The rich comparison operator ``==``

        x.__eq__(y) <==> x==y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__eq__")

    def __ne__(self, other):
        """The rich comparison operator ``!=``

        x.__ne__(y) <==> x!=y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__ne__")

    def __ge__(self, other):
        """The rich comparison operator ``>=``

        x.__ge__(y) <==> x>=y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__ge__")

    def __gt__(self, other):
        """The rich comparison operator ``>``

        x.__gt__(y) <==> x>y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__gt__")

    def __le__(self, other):
        """The rich comparison operator ``<=``

        x.__le__(y) <==> x<=y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__le__")

    def __lt__(self, other):
        """The rich comparison operator ``<``

        x.__lt__(y) <==> x<y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__lt__")

    def __and__(self, other):
        """The binary bitwise operation ``&``

        x.__and__(y) <==> x&y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__and__")

    def __iand__(self, other):
        """The augmented bitwise assignment ``&=``

        x.__iand__(y) <==> x&=y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__iand__")

    def __rand__(self, other):
        """The binary bitwise operation ``&`` with reflected operands.

        x.__rand__(y) <==> y&x

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__rand__")

    def __or__(self, other):
        """The binary bitwise operation ``|``

        x.__or__(y) <==> x|y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__or__")

    def __ior__(self, other):
        """The augmented bitwise assignment ``|=``

        x.__ior__(y) <==> x|=y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__ior__")

    def __ror__(self, other):
        """The binary bitwise operation ``|`` with reflected operands.

        x.__ror__(y) <==> y|x

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__ror__")

    def __xor__(self, other):
        """The binary bitwise operation ``^``

        x.__xor__(y) <==> x^y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__xor__")

    def __ixor__(self, other):
        """The augmented bitwise assignment ``^=``

        x.__ixor__(y) <==> x^=y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, other, "__ixor__")

    def __rxor__(self, other):
        """The binary bitwise operation ``^`` with reflected operands.

        x.__rxor__(y) <==> y^x

        """
        return self._binary_operation(self, other, "__rxor__")

    def __lshift__(self, y):
        """The binary bitwise operation ``<<``

        x.__lshift__(y) <==> x<<y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, y, "__lshift__")

    def __ilshift__(self, y):
        """The augmented bitwise assignment ``<<=``

        x.__ilshift__(y) <==> x<<=y

        """
        return self._binary_operation(self, y, "__ilshift__")

    def __rlshift__(self, y):
        """The binary bitwise operation ``<<`` with reflected operands.

        x.__rlshift__(y) <==> y<<x

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, y, "__rlshift__")

    def __rshift__(self, y):
        """The binary bitwise operation ``>>``

        x.__lshift__(y) <==> x>>y

        """
        return self._binary_operation(self, y, "__rshift__")

    def __irshift__(self, y):
        """The augmented bitwise assignment ``>>=``

        x.__irshift__(y) <==> x>>=y

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, y, "__irshift__")

    def __rrshift__(self, y):
        """The binary bitwise operation ``>>`` with reflected operands.

        x.__rrshift__(y) <==> y>>x

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._binary_operation(self, y, "__rrshift__")

    def __abs__(self):
        """The unary arithmetic operation ``abs``

        x.__abs__() <==> abs(x)

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._unary_operation("__abs__")

    def __neg__(self):
        """The unary arithmetic operation ``-``

        x.__neg__() <==> -x

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._unary_operation("__neg__")

    def __invert__(self):
        """The unary bitwise operation ``~``

        x.__invert__() <==> ~x

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._unary_operation("__invert__")

    def __pos__(self):
        """The unary arithmetic operation ``+``

        x.__pos__() <==> +x

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._unary_operation("__pos__")

    def __array__(self, dtype=None, copy=None):
        """The numpy array interface.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            dtype: optional
                Typecode or data-type to which the array is cast.

            copy: `None` or `bool`
                Included to match the v2 `numpy.ndarray.__array__`
                API, but ignored. The returned numpy array is always
                independent.

                .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3])
        >>> a = numpy.array(d)
        >>> print(type(a))
        <class 'numpy.ndarray'>
        >>> a[0] = -99
        >>> d
        <{{repr}}Data(3): [1, 2, 3]>
        >>> b = numpy.array(d, float)
        >>> print(b)
        [1. 2. 3.]

        """
        array = self.array
        if dtype is None:
            return array

        return array.astype(dtype, copy=False)

    def __data__(self):
        """Returns a new reference to self.

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self

    @property
    def __in_memory__(self):
        """The in-memory status of chunk data.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `bool` or `None`
                Whether or not the chunk data at the head of the Dask
                graph is in memory. If `None` then it is not known
                whether or not this is the case.

        """
        return self._get_component("__in_memory__", None)

    @property
    def __keepdims_indexing__(self):
        """Flag to indicate if axes indexed with integers are kept.

        If set to True (the default) then providing a single integer
        as a single-axis index does *not* reduce the number of array
        dimensions by 1. This behaviour is different to `numpy`.

        If set to False then providing a single integer as a
        single-axis index reduces the number of array dimensions by
        1. This behaviour is the same as `numpy`.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `__orthogonal_indexing__`, `__getitem__`,
                     `__setitem__`

        **Examples**

        >>> d = {{package}}.Data([[1, 2, 3], [4, 5, 6]])
        >>> d.__keepdims_indexing__
        True
        >>> e = d[0]
        >>> e.shape
        (1, 3)
        >>> print(e.array)
        [[1 2 3]]

        >>> d.__keepdims_indexing__
        True
        >>> e = d[:, 1]
        >>> e.shape
        (2, 1)
        >>> print(e.array)
        [[2]
         [5]]

        >>> d.__keepdims_indexing__
        True
        >>> e = d[0, 1]
        >>> e.shape
        (1, 1)
        >>> print(e.array)
        [[2]]

        >>> d.__keepdims_indexing__ = False
        >>> e = d[0]
        >>> e.shape
        (3,)
        >>> print(e.array)
        [1 2 3]

        >>> d.__keepdims_indexing__
        False
        >>> e = d[:, 1]
        >>> e.shape
        (2,)
        >>> print(e.array)
        [2 5]

        >>> d.__keepdims_indexing__
        False
        >>> e = d[0, 1]
        >>> e.shape
        ()
        >>> print(e.array)
        2

        """
        return self._get_component("__keepdims_indexing__", True)

    @__keepdims_indexing__.setter
    def __keepdims_indexing__(self, value):
        self._set_component("__keepdims_indexing__", bool(value), copy=False)

    @property
    def __orthogonal_indexing__(self):
        """Flag to indicate that orthogonal indexing is supported.

        True, indicates that 'orthogonal indexing' is applied. This
        means that when indices are 1-d arrays or lists then they
        subspace along each dimension independently. This behaviour is
        similar to Fortran, but different to `numpy`.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `__keepdims_indexing__`, `__getitem__`,
                     `__setitem__`,
                     `netCDF4.Variable.__orthogonal_indexing__`

        **Examples**

        >>> d = {{package}}.Data([[1, 2, 3],
        ...              [4, 5, 6]])
        >>> e = d[[0], [0, 2]]
        >>> e.shape
        (1, 2)
        >>> print(e.array)
        [[1 3]]
        >>> e = d[[0, 1], [0, 2]]
        >>> e.shape
        (2, 2)
        >>> print(e.array)
        [[1 3]
         [4 6]]

        """
        return True

    @__orthogonal_indexing__.setter
    def __orthogonal_indexing__(self, value):
        self._set_component("__orthogonal_indexing__", bool(value), copy=False)

    @property
    def _Units(self):
        """Storage for the units in a `{{package}}.Units` object.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `Units`

        """
        return self._get_component("Units")

    @_Units.setter
    def _Units(self, value):
        self._set_component("Units", value, copy=False)

    @_Units.deleter
    def _Units(self):
        self._set_component("Units", self._Units_class(None), copy=False)

    @property
    def _axes(self):
        """Storage for the axis identifiers.

        Contains a `tuple` of identifiers, one for each array axis.

        .. versionadded:: (cfdm) 1.11.2.0

        """
        return self._get_component("axes")

    @_axes.setter
    def _axes(self, value):
        self._set_component("axes", tuple(value), copy=False)

    @classmethod
    def _binary_operation(cls, data, other, method):
        """Binary arithmetic and comparison operations.

        It is called by the binary (i.e. two operands) arithmetic and
        comparison methods, such as `__sub__`, `__imul__`, `__rdiv__`,
        `__lt__`, etc.

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

        >>> d = {{package}}.Data([0, 1, 2, 3])
        >>> e = {{package}}.Data([1, 1, 3, 4])

        >>> f = d._binary_operation(e, '__lt__')
        >>> print(f.array)
        [ True False  True  True]

        """
        # Note: This method is a classmethod to allow its
        #       functionality to be used with a LHS operand that is
        #       not 'self'. This is not currently needed here, but
        #       could be useful in subclasses which overload this
        #       method, yet still want to access the parent method
        #       functionality via `super`. For instance, cf-python's
        #       `cf.Data._binary_operation` sometimes needs to apply
        #       the binary operation to a modified copy of its 'self'.
        inplace = method[2] == "i"

        # ------------------------------------------------------------
        # Ensure other is an independent Data object, for example
        # so that combination with downstream cf.Query objects works.
        # ------------------------------------------------------------
        if not isinstance(other, cls):
            if other is None:
                # Can't sensibly initialise a Data object from `None`
                other = np.array(None, dtype=object)

            other = cls(other)

        # Cast as dask arrays
        dx0 = data.to_dask_array()
        dx1 = other.to_dask_array()

        original_shape = data.shape
        original_ndim = data.ndim

        if inplace:
            # Find non-in-place equivalent operator (remove 'i')
            equiv_method = method[:2] + method[3:]
            # Need to add check in here to ensure that the operation is not
            # trying to cast in a way which is invalid. For example, doing
            # [an int array] ** float value = [a float array] is fine, but
            # doing this in-place would try to chance an int array into a
            # float one, which isn't valid casting. Therefore we need to
            # catch cases where __i<op>__ isn't possible even if __<op>__
            # is due to datatype consistency rules.
            result = getattr(dx0, equiv_method)(dx1)
        else:
            result = getattr(dx0, method)(dx1)

        if result is NotImplemented:
            raise TypeError(
                f"Unsupported operands for {method}: {data!r} and {other!r}"
            )

        # Set axes when other has more dimensions than self
        axes = None
        if not original_ndim:
            axes = other._axes
        else:
            diff = dx1.ndim - original_ndim
            if diff > 0:
                axes = list(data._axes)
                for _ in range(diff):
                    axes.insert(0, new_axis_identifier(tuple(axes)))

        if inplace:
            d = data
        else:
            d = data.copy()

        d._set_dask(result, clear=cls._ALL, in_memory=True)

        if axes is not None:
            d._axes = axes

        # Update the dataset chunking strategy
        if (
            isinstance(data.nc_dataset_chunksizes(), tuple)
            and d.shape != original_shape
        ):
            d.nc_clear_dataset_chunksizes()

        # Update the deterministic status
        d._update_deterministic(other)

        return d

    def _clear_after_dask_update(self, clear=None):
        """Remove components invalidated by updating the `dask` array.

        Removes or modifies components that can't be guaranteed to be
        consistent with an updated `dask` array. See the *clear*
        parameter for details.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `_del_Array`, `_del_cached_elements`,
                     `nc_del_aggregation_write_status`, `_set_dask`

        :Parameters:

            clear: `int` or `None`, optional
                Specify which components to remove, determined by
                sequentially combining an integer value of *clear*
                with the relevant class-level constants (such as
                ``Data._ARRAY``), using the bitwise AND (&)
                operator. If ``clear & <class-level constant>`` is
                True then the corresponding component is cleared. The
                default value of `None` is equivalent to *clear* being
                set to ``Data._ALL``.

                The bitwise OR (^) operator can be used to retain a
                component (or components) but remove all others. For
                instance, if *clear* is ``Data._ALL ^
                Data._CACHE`` then all components except the
                cached array values will be removed.

        :Returns:

            `int`
                The integer value of *clear*.

        """
        if clear is None:
            # Clear all components
            clear = self._ALL

        if not clear:
            return clear

        if clear & self._ARRAY:
            # Delete a source array
            self._del_Array(None)

        if clear & self._CACHE:
            # Delete cached element values
            self._del_cached_elements()

        if clear & self._CFA:
            # Set the aggregation write status to False (under certain
            # circumstances)
            self._del_nc_aggregation_write_status()

        return clear

    @classmethod
    def _concatenate_conform_units(cls, data1, units0, relaxed_units, copy):
        """Check and conform the units of data prior to concatenation.

        This is a helper function for `concatenate` that may be easily
        overridden in subclasses, to allow for customisation of the
        concatenation process.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `concatenate`

        :Parameters:

            data1: `Data`
                Data with units.

            units0: `Units`
                The units to conform *data1* to.

            {{relaxed_units: `bool`, optional}}

            copy: `bool`
                If False then modify *data1* in-place. Otherwise a
                copy of it is modified.

        :Returns:

            `Data`
                Returns *data1*, possibly modified so that it conforms
                to *units0*. If *copy* is False and *data1* is
                modified, then it is done so in-place.

        """
        # Check and conform, if necessary, the units of all inputs
        units1 = data1.Units
        if (
            relaxed_units
            and not units0.isvalid
            and not units1.isvalid
            and units0.__dict__ == units1.__dict__
        ):
            # Allow identical invalid units to be equal
            pass
        elif not units0.equals(units1):
            raise ValueError(
                "Can't concatenate: All the input arrays must have "
                f"equal units. Got {units0!r} and {units1!r}"
            )

        return data1

    @classmethod
    def _concatenate_post_process(
        cls, concatenated_data, axis, conformed_data
    ):
        """Post-process concatenated data.

        This is a helper function for `concatenate` that may be easily
        overridden in subclasses, to allow for customisation of the
        concatenation process.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `concatenate`

        :Parameters:

            concatenated_data: `Data`
                The concatenated data array.

            axis: `int`
                The axis of concatenation.

            conformed_data: sequence of `Data`
                The ordered sequence of data arrays that were
                concatenated.

        :Returns:

            `Data`
                Returns *concatenated_data*, possibly modified
                in-place.

        """
        # ------------------------------------------------------------
        # Set the aggregation 'aggregated_data' terms
        # ------------------------------------------------------------
        if concatenated_data.nc_get_aggregation_write_status():
            # Set the netCDF aggregated_data terms, giving precedence
            # to those towards the left hand side of the input
            # list. If any input Data object has no aggregated_data
            # terms, then nor will the concatenated data.
            aggregated_data = {}
            for d in conformed_data[::-1]:
                value = d.nc_get_aggregated_data()
                if not value:
                    aggregated_data = {}
                    break

                aggregated_data.update(value)

            concatenated_data.nc_set_aggregated_data(aggregated_data)

        # ------------------------------------------------------------
        # Update the deterministic status of the concatenated data
        # ------------------------------------------------------------
        deterministic = True
        for d in conformed_data:
            if not d.has_deterministic_name():
                deterministic = False
                break

        concatenated_data._update_deterministic(deterministic)

        return concatenated_data

    def _del_cached_elements(self):
        """Delete any cached element values.

        Updates the data in-place to remove the cached element values.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `_get_cached_elements`, `_set_cached_elements`

        :Returns:

            `None`

        """
        self._del_component("cached_elements", None)

    def _del_nc_aggregation_write_status(self):
        """Set the aggregation write status to False.

        Updates the data in-place to set the aggregation write status
        to `False`, but only if the fragment type is not ``'value'``.

        A necessary (but not sufficient) condition for writing the
        data as CF-netCDF aggregated data is that the write status is
        True.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `nc_del_aggregation_write_status`,
                     `nc_get_aggregation_fragment_type`

        :Returns:

            `None`

        """
        if self.nc_get_aggregation_fragment_type() != "unique_value":
            self.nc_del_aggregation_write_status()

    def _del_dask(self, default=ValueError(), clear=None):
        """Remove the dask array.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `to_dask_array`, `_clear_after_dask_update`,
                     `_set_dask`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                dask array axes has not been set. If set to an
                `Exception` instance then it will be raised instead.

            clear: `int` or None`, optional
                Specify which components should be removed. The
                default value of `None` is equivalent to *clear* being
                set to ``Data._ALL``, which results in all
                components being removed. See
                `_clear_after_dask_update` for details. If there is no
                Dask array then no components are removed, regardless
                of the value of *clear*.

        :Returns:

            `dask.array.Array`
                The removed dask array.

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3])
        >>> dx = d._del_dask()
        >>> d._del_dask("No dask array")
        'No dask array'
        >>> d._del_dask()
        Traceback (most recent call last):
            ...
        ValueError: 'Data' has no dask array
        >>> d._del_dask(RuntimeError('No dask array'))
        Traceback (most recent call last):
            ...
        RuntimeError: No dask array

        """
        out = self._del_component("dask", None)
        if out is None:
            return self._default(
                default, f"{self.__class__.__name__!r} has no dask array"
            )

        self._clear_after_dask_update(clear)
        return out

    def _get_cached_elements(self):
        """Return the cache of selected element values.

        .. warning:: Never change the returned dictionary in-place.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `_del_cached_elements`, `_set_cached_elements`

        :Returns:

            `dict`
                The cached element values, where the keys are the
                element positions within the dask array and the values
                are the cached values for each position.

        **Examples**

        >>> d._get_cached_elements()
        {}

        >>> d._get_cached_elements()
        {0: 273.15, 1: 274.56, -1: 269.95}

        """
        return self._get_component("cached_elements", {})

    def _is_abstract_Array_subclass(self, array):
        """Whether or not an array is a type of Array.

        :Parameters:

            array:

        :Returns:

            `bool`

        """
        return isinstance(array, Array)

    def _item(self, index):
        """Return an element of the data as a scalar.

        It is assumed, but not checked, that the given index selects
        exactly one element.

        :Parameters:

            index:

        :Returns:

                The selected element of the data.

        **Examples**

        >>> d = {{package}}.Data([[1, 2, 3]], 'km')
        >>> d._item((0, -1))
        array(3)
        >>> d[0, 1] = {{package}}.masked
        >>> d._item((slice(None), slice(1, 2)))
        masked

        """
        array = self[index].array.squeeze()
        if np.ma.is_masked(array):
            array = np.ma.masked

        return array

    def _modify_dask_graph(
        self, method, args=(), kwargs=None, exceptions=(AttributeError,)
    ):
        """Modify the Dask graph.

        The value of each node of the Dask graph is replaced with the
        result of calling its *method* method. If attempting to call
        the method results in any of the exceptions given by
        *exceptions*, then that node is unmodified. If attempting to
        call the method results in an exception not given by
        *exceptions*, then that exception is raised.

        The `Data` object is modified in-place, but the embedded
        Dask graph is not.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            method: `str`
                The name of the callable method which returns a new
                graph node value.

            args: `tuple`, optional
                Positional arguments for the *method*. No arguments
                (the default) are specified by an empty `tuple`.

            kwargs: `dict` or `None`, optional
                Keyword arguments for the *method*. No keyword
                arguments (the default) is specified by an empty
                `dict` or `None`.

            exceptions: `tuple` of `Exception`, optional
                Do not change graph node values if calling its
                *method* results in any of the specified exceptions.

        :Returns:

            `None`

        """
        if kwargs is None:
            kwargs = {}

        updated = False

        dsk = self.todict(
            _force_mask_hardness=False,
            _force_to_memory=False,
        )
        for key, a in dsk.items():
            try:
                dsk[key] = getattr(a, method)(*args, **kwargs)
            except exceptions:
                # This graph node could not be modified
                pass
            else:
                # This graph node was successfully modified
                updated = True

        if updated:
            # The Dask graph was modified, so recast the dictionary
            # representation as a Dask array.
            dx = self.to_dask_array(
                _force_mask_hardness=False, _force_to_memory=False
            )
            dx = da.Array(dsk, dx.name, dx.chunks, dx.dtype, dx._meta)
            self._set_dask(dx, clear=self._NONE, in_memory=None)

            # Update the deterministic status
            self._update_deterministic(False)

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

    def _set_cached_elements(self, elements):
        """Cache selected element values.

        Updates the `Data` instance in-place to store the given
        element values.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `_del_cached_elements`, `_get_cached_elements`

        :Parameters:

            elements: `dict`
               Zero or more element values to be cached, each keyed by
               a unique identifier to allow unambiguous retrieval.
               Existing cached elements not specified by *elements*
               will not be removed.

        :Returns:

            `None`

        **Examples**

        >>> d._set_cached_elements({0: 273.15})

        """
        if not elements:
            return

        # Parse the new elements
        elements = elements.copy()
        for i, x in elements.items():
            if np.ma.is_masked(x):
                x = np.ma.masked
            else:
                x = np.squeeze(x)

            elements[i] = x

        cache = self._get_component("cached_elements", None)
        if cache:
            cache = cache.copy()
            cache.update(elements)
        else:
            cache = elements.copy()

        self._set_component("cached_elements", cache, copy=False)

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

    def _set_dask(self, dx, copy=False, clear=None, in_memory=None):
        """Set the dask array.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `to_dask_array`, `_clear_after_dask_update`,
                     `_del_dask`

        :Parameters:

            dx: `dask.array.Array`
                The array to be inserted.

            copy: `bool`, optional
                If True then copy *array* before setting it. By
                default it is not copied.

            clear: `int` or `None`, optional
                Specify which components should be removed. The
                default value of `None` is equivalent to *clear* being
                set to ``Data._ALL``, which results in all
                components being removed. See
                `_clear_after_dask_update` for details.

            in_memory: `None` or `bool`, optional
                If `None` then do not update the `__in_memory__`
                attribute. Otherwise set `__in_memory_` to
                *in_memory*. For clarity, it is recommended to provide
                a value for *in_memory*, even when that value is the
                default.

        :Returns:

            `None`

        """
        if dx is NotImplemented:
            logger.warning(
                "WARNING: NotImplemented has been set in the place of a "
                "dask array."
                "\n\n"
                "This could occur if any sort of exception is raised "
                "by a function that is run on chunks (via, for "
                "instance, da.map_blocks or "
                "dask.array.core.elemwise). Such a function could get "
                "run at definition time in order to ascertain "
                "suitability (such as data type casting, "
                "broadcasting, etc.). Note that the exception may be "
                "difficult to diagnose, as dask will have silently "
                "trapped it and returned NotImplemented (see , for "
                "instance, dask.array.core.elemwise). Print "
                "statements in a local copy of dask are possibly the "
                "way to go if the cause of the error is not obvious."
            )

        if copy:
            dx = dx.copy()

        self._set_component("dask", dx, copy=False)
        if in_memory is not None:
            self._set_component("__in_memory__", bool(in_memory), copy=False)

        self._clear_after_dask_update(clear)

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
                    for start, stop in zip_longest(*args):
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

            if prod(np.shape(value)) == 1:
                # 'value' is logically scalar => simply assign it to
                # all index combinations.
                for i in product(*indices1):
                    try:
                        array[i] = value
                    except NotImplementedError:
                        # Assume that this error was raised because
                        # 'i' contains multiple size 1 lists, which
                        # are not implemented by Dask => Replace the
                        # size 1 lists with integers.
                        i = [
                            x[0] if isinstance(x, list) and len(x) == 1 else x
                            for x in i
                        ]
                        array[tuple(i)] = value

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

                for i, j in zip(product(*indices1), product(*indices2)):
                    try:
                        array[i] = value[j]
                    except NotImplementedError:
                        # Assume that this error was raised because
                        # 'i' contains multiple size 1 lists, which
                        # are not implemented by Dask => Replace the
                        # size 1 lists with integers.
                        i = [
                            x[0] if isinstance(x, list) and len(x) == 1 else x
                            for x in i
                        ]
                        array[tuple(i)] = value[j]

    def _unary_operation(self, operation):
        """Implement unary arithmetic operations.

        It is called by the unary arithmetic methods, such as
        __abs__().

        .. seealso:: `_binary_operation`

        :Parameters:

            operation: `str`
                The unary arithmetic method name (such as "__invert__").

        :Returns:

            `Data`
                A new Data array.

        **Examples**

        >>> d = {{package}}.Data([[1, 2, -3, -4, -5]])

        >>> e = d._unary_operation('__abs__')
        >>> print(e.array)
        [[1 2 3 4 5]]

        >>> e = d.__abs__()
        >>> print(e.array)
        [[1 2 3 4 5]]

        >>> e = abs(d)
        >>> print(e.array)
        [[1 2 3 4 5]]

        """
        out = self.copy(array=False)

        dx = self.to_dask_array(
            _force_mask_hardness=True, _force_to_memory=True
        )
        dx = getattr(operator, operation)(dx)

        out._set_dask(dx, in_memory=True)

        return out

    def _update_deterministic(self, other):
        """Update the deterministic name status in-place.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `get_deterministic_name`,
                     `has_deterministic_name`

        :Parameters:

            other: `bool` or `Data`
                If `False`, `Data` with a False deterministic name
                status, or a Dask collection then set the
                deterministic name status to `False`.

                If `True`, `Data` with a True deterministic name
                status, or not a Dask collection then do not change
                the deterministic name status.

        :Returns:

            `None`

        """
        if other is True:
            return

        if other is False:
            self._custom["has_deterministic_name"] = False
            return

        custom = self._custom
        if custom["has_deterministic_name"]:
            try:
                deterministic = other._custom.get(
                    "has_deterministic_name", False
                )
            except AttributeError:
                custom["has_deterministic_name"] = not is_dask_collection(
                    other
                )
            else:
                if not deterministic:
                    custom["has_deterministic_name"] = False

    @property
    def array(self):
        """A numpy array copy of the data.

        In-place changes to the returned numpy array do not affect the
        underlying dask array.

        The returned numpy array has the same mask hardness and fill
        values as the data.

        Compare with `compute`.

        **Performance**

        `array` causes all delayed operations to be computed. The
        returned `numpy` array is a deep copy of that returned by
        created `compute`.

        .. seealso:: `datetime_array`, `compute`, `persist`

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3.0], 'km')
        >>> a = d.array
        >>> isinstance(a, numpy.ndarray)
        True
        >>> print(a)
        [ 1.  2.  3.]
        >>> d[0] = -99
        >>> print(a[0])
        1.0
        >>> a[0] = 88
        >>> print(d[0])
        -99.0 km

        >>> d = {{package}}.Data('2000-12-1', units='days since 1999-12-1')
        >>> print(d.array)
        366
        >>> print(d.datetime_array)
        2000-12-01 00:00:00

        """
        a = self.compute().copy()
        if issparse(a):
            a = a.toarray()
        elif not isinstance(a, np.ndarray):
            a = np.asanyarray(a)

        ndim = a.ndim
        shape = a.shape
        size = a.size
        if not size:
            return a

        ndim = a.ndim
        shape = a.shape

        # Set cached elements
        items = [0, -1]
        indices = [(slice(0, 1, 1),) * ndim, (slice(-1, None, 1),) * ndim]
        if ndim == 2 and shape[-1] == 2:
            items.extend((1, -2))
            indices.extend(
                (np.unravel_index(1, shape), np.unravel_index(size - 2, shape))
            )
        elif size == 3:
            items.append(1)
            indices.append(np.unravel_index(1, a.shape))

        cache = {i: a[index] for i, index in zip(items, indices)}
        self._set_cached_elements(cache)

        return a

    @property
    def chunks(self):
        """The `dask` chunk sizes for each dimension.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `chunksize`, `npartitions`, `numblocks`,
                     `rechunk`

        **Examples**

        >>> d = {{package}}.Data.empty((6, 5), chunks=(2, 4))
        >>> d.chunks
        ((2, 2, 2), (4, 1))
        >>> d.numblocks
        (3, 2)
        >>> d.npartitions
        6

        """
        return self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        ).chunks

    @property
    def chunksize(self):
        """The largest `dask` chunk size for each dimension.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `chunks`, `npartitions`, `numblocks`, `rechunk`

        **Examples**

        >>> d = {{package}}.Data.empty((6, 5), chunks=(2, 4))
         >>> d.chunks
        ((2, 2, 2), (4, 1))
        >>> d.chunksize
        (2, 4)
        >>> d.numblocks
        (3, 2)
        >>> d.npartitions
        6

        """
        return self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        ).chunksize

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
            raise ValueError("Not compressed: can't get compressed array")

        return ca.compressed_array

    @property
    def dask_compressed_array(self):
        """Returns a dask array of the compressed data.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `dask.array.Array`
                The compressed data.

        **Examples**

        >>> a = d.dask_compressed_array

        """
        ca = self.source(None)

        if ca is None or not ca.get_compression_type():
            raise ValueError("not compressed: can't get compressed dask array")

        return ca.to_dask_array()

    @property
    def data(self):
        """The data as an object identity.

        **Examples**

        >>> d = {{package}}.Data([1, 2], 'm')
        >>> d.data is d
        True

        """
        return self

    @property
    def datetime_array(self):
        """An independent numpy array of date-time objects.

        Only applicable to data arrays with reference time units.

        If the calendar has not been set then the CF default calendar will
        be used and the units will be updated accordingly.

        The data-type of the data array is unchanged.

        .. seealso:: `array`, `compute`, `persist`

        **Performance**

        `datetime_array` causes all delayed operations to be computed.

        **Examples**

        """
        units = self.Units

        if not units.isreftime:
            raise ValueError(
                f"Can't create date-time array from units {self._Units!r}"
            )

        calendar = getattr(units, "calendar", None)
        if calendar == "none":
            raise ValueError(
                f"Can't create date-time array from units {self._Units!r} "
                "because calendar is 'none'"
            )

        units1, reftime = units.units.split(" since ")

        # Convert months and years to days, because cftime won't work
        # otherwise.
        #
        # UDUNITS defines a year to be the interval between two
        # successive passages of the sun through vernal equinox, and a
        # month to be exactly 1/12 of that interval.
        year_length = 365.242198781

        dx = self.to_dask_array(_force_mask_hardness=False)
        if units1 in ("month", "months"):
            dx = dx * (year_length / 12)
            units = self._Units_class(f"days since {reftime}", calendar)
        elif units1 in ("year", "years", "yr"):
            dx = dx * year_length
            units = self._Units_class(f"days since {reftime}", calendar)

        dx = convert_to_datetime(dx, units)

        a = dx.compute()

        if np.ma.isMA(a):
            if self.hardmask:
                a.harden_mask()
            else:
                a.soften_mask()

            a.set_fill_value(self.get_fill_value(None))

        return a

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
    def dtype(self):
        """The `numpy` data-type of the data.

        Always returned as a `numpy` data-type instance, but may be set
        as any object that converts to a `numpy` data-type.

        **Examples**

        >>> d = {{package}}.Data([1, 2.5, 3.9])
        >>> d.dtype
        dtype('float64')
        >>> print(d.array)
        [1.  2.5 3.9]
        >>> d.dtype = int
        >>> d.dtype
        dtype('int64')
        >>> print(d.array)
        [1 2 3]
        >>> d.dtype = 'float32'
        >>> print(d.array)
        [1. 2. 3.]
        >>> import numpy as np
        >>> d.dtype = np.dtype('int32')
        >>> d.dtype
        dtype('int32')
        >>> print(d.array)
        [1 2 3]

        """
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        return dx.dtype

    @dtype.setter
    def dtype(self, value):
        # Only change the data type if it's different to that of the
        # dask array
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=True
        )
        if dx.dtype != value:
            cache = self._get_cached_elements().copy()

            dx = dx.astype(value)
            self._set_dask(dx, in_memory=True)

            if cache:
                # Re-instate cached elements, cast to the new dtype.
                cache1 = {}
                for i, a in cache.items():
                    if a is not np.ma.masked:
                        a = np.asanyarray(a, dtype=value)

                    cache1[i] = a

                self._set_cached_elements(cache1)

    @property
    def fill_value(self):
        """The data array missing data value.

        If set to `None` then the default `numpy` fill value
        appropriate to the data array's data-type will be used.

        Deleting this attribute is equivalent to setting it to `None`,
        so this attribute is guaranteed to always exist.

        .. versionadded:: (cfdm) 1.11.2.0

        **Examples**

        >>> d.fill_value = 9999.0
        >>> d.fill_value
        9999.0
        >>> del d.fill_value
        >>> d.fill_value
        None

        """
        return self.get_fill_value(None)

    @fill_value.setter
    def fill_value(self, value):
        self.set_fill_value(value)

    @fill_value.deleter
    def fill_value(self):
        self.del_fill_value(None)

    @property
    def hardmask(self):
        """Hardness of the mask.

        If the `hardmask` attribute is `True`, i.e. there is a hard
        mask, then unmasking an entry will silently not occur. This is
        the default, and prevents overwriting the mask.

        If the `hardmask` attribute is `False`, i.e. there is a soft
        mask, then masked entries may be overwritten with non-missing
        values.

        .. note:: Setting the `hardmask` attribute does not
                  immediately change the mask hardness, rather its
                  value indicates to other methods (such as `where`,
                  `transpose`, etc.) whether or not the mask needs
                  hardening or softening prior to an operation being
                  defined, and those methods will reset the mask
                  hardness if required.

                  By contrast, the `harden_mask` and `soften_mask`
                  methods immediately reset the mask hardness of the
                  underlying `dask` array, and also set the value of
                  the `hardmask` attribute.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `harden_mask`, `soften_mask`, `to_dask_array`,
                     `__setitem__`

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3])
        >>> d.hardmask
        True
        >>> d[0] = {{package}}.masked
        >>> print(d.array)
        [-- 2 3]
        >>> d[...] = 999
        >>> print(d.array)
        [-- 999 999]
        >>> d.hardmask = False
        >>> d.hardmask
        False
        >>> d[...] = -1
        >>> print(d.array)
        [-1 -1 -1]

        """
        return self._get_component("hardmask", self._DEFAULT_HARDMASK)

    @hardmask.setter
    def hardmask(self, value):
        self._set_component("hardmask", bool(value), copy=False)

    @property
    def mask(self):
        """The Boolean missing data mask of the data array.

        The Boolean mask has True where the data array has missing data
        and False otherwise.

        .. seealso:: `masked_values`, `masked_where`

        :Returns:

            `Data`

        **Examples**

        >>> d.shape
        (12, 73, 96)
        >>> m = d.mask
        >>> m.dtype
        dtype('bool')
        >>> m.shape
        (12, 73, 96)

        """
        mask_data_obj = self.copy(array=False)

        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=True
        )
        mask = da.ma.getmaskarray(dx)

        mask_data_obj._set_dask(mask, in_memory=True)
        mask_data_obj._Units = self._Units_class(None)
        mask_data_obj.hardmask = self._DEFAULT_HARDMASK

        return mask_data_obj

    @property
    def nbytes(self):
        """Total number of bytes consumed by the elements of the array.

        Does not include bytes consumed by the array mask

        **Performance**

        If the number of bytes is unknown then it is calculated
        immediately by executing all delayed operations.

        **Examples**

        >>> d = {{package}}.Data([[1, 1.5, 2]])
        >>> d.dtype
        dtype('float64')
        >>> d.size, d.dtype.itemsize
        (3, 8)
        >>> d.nbytes
        24
        >>> d[0] = {{package}}.masked
        >>> print(d.array)
        [[-- 1.5 2.0]]
        >>> d.nbytes
        24

        """
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        if math.isnan(dx.size):
            logger.debug("Computing data nbytes: Performance may be degraded")
            dx.compute_chunk_sizes()

        return dx.nbytes

    @property
    def ndim(self):
        """Number of dimensions in the data array.

        **Examples**

        >>> d = {{package}}.Data([[1, 2, 3], [4, 5, 6]])
        >>> d.ndim
        2

        >>> d = {{package}}.Data([[1, 2, 3]])
        >>> d.ndim
        2

        >>> d = {{package}}.Data([[3]])
        >>> d.ndim
        2

        >>> d = {{package}}.Data([3])
        >>> d.ndim
        1

        >>> d = {{package}}.Data(3)
        >>> d.ndim
        0

        """
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        return dx.ndim

    @property
    def npartitions(self):
        """The total number of chunks.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `chunks`, `chunksize`, `numblocks`, `rechunk`

        **Examples**

        >>> d = {{package}}.Data.empty((6, 5), chunks=(2, 4))
        >>> d.chunks
        ((2, 2, 2), (4, 1))
        >>> d.chunksize
        (2, 4)
        >>> d.numblocks
        (3, 2)
        >>> d.npartitions
        6

        """
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        return dx.npartitions

    @property
    def numblocks(self):
        """The number of chunks along each dimension.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `chunks`, `chunksize`, `npartitions`, `rechunk`

        **Examples**

        >>> d = {{package}}.Data.empty((6, 5), chunks=(2, 4))
        >>> d.chunks
        ((2, 2, 2), (4, 1))
        >>> d.chunksize
        (2, 4)
        >>> d.numblocks
        (3, 2)
        >>> d.npartitions
        6

        """
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        return dx.numblocks

    @property
    def shape(self):
        """Tuple of the data array's dimension sizes.

        **Performance**

        If the shape of the data is unknown then it is calculated
        immediately by executing all delayed operations.

        **Examples**

        >>> d = {{package}}.Data([[1, 2, 3], [4, 5, 6]])
        >>> d.shape
        (2, 3)

        >>> d = {{package}}.Data([[1, 2, 3]])
        >>> d.shape
        (1, 3)

        >>> d = {{package}}.Data([[3]])
        >>> d.shape
        (1, 1)

        >>> d = {{package}}.Data(3)
        >>> d.shape
        ()

        """
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        if math.isnan(dx.size):
            logger.debug("Computing data shape: Performance may be degraded")
            dx.compute_chunk_sizes()

        return dx.shape

    @property
    def size(self):
        """Number of elements in the data array.

        **Performance**

        If the size of the data is unknown then it is calculated
        immediately by executing all delayed operations.

        **Examples**

        >>> d = {{package}}.Data([[1, 2, 3], [4, 5, 6]])
        >>> d.size
        6

        >>> d = {{package}}.Data([[1, 2, 3]])
        >>> d.size
        3

        >>> d = {{package}}.Data([[3]])
        >>> d.size
        1

        >>> d = {{package}}.Data([3])
        >>> d.size
        1

        >>> d = {{package}}.Data(3)
        >>> d.size
        1

        """
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        size = dx.size
        if math.isnan(size):
            logger.debug("Computing data size: Performance may be degraded")
            dx.compute_chunk_sizes()
            size = dx.size

        return size

    @property
    def sparse_array(self):
        """Return an independent `scipy` sparse array of the data.

        In-place changes to the returned sparse array do not affect
        the underlying dask array.

        An `AttributeError` is raised if a sparse array representation
        is not available.

        **Performance**

        `sparse_array` causes all delayed operations to be
        computed. The returned sparse array is a deep copy of that
        returned by created `compute`.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `array`

        :Returns:

                An independent `scipy` sparse array of the data.

        **Examples**

        >>> from scipy.sparse import issparse
        >>> issparse(d.sparse_array)
        True

        """
        array = self.compute()
        if issparse(array):
            return array.copy()

        raise AttributeError(
            f"The array is of type {type(array)}, and a sparse array "
            "representation of the data is not available."
        )

    @property
    def Units(self):
        """The `Units` object containing the units of the data array.

        .. versionadded:: (cfdm) 1.11.2.0

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3], units='m')
        >>> d.Units
        <Units: m>
        >>> d.Units = {{package}}.Units('kilometres')
        >>> d.Units
        <Units: kilometres>
        >>> d.Units = {{package}}.Units('km')
        >>> d.Units
        <Units: km>

        """
        return self._Units

    @Units.setter
    def Units(self, value):
        self._Units = value

    @Units.deleter
    def Units(self):
        del self._Units

    def all(self, axis=None, keepdims=True, split_every=None):
        """Test whether all data array elements evaluate to True.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `any`

        :Parameters:

            axis: (sequence of) `int`, optional
                Axis or axes along which a logical AND reduction is
                performed. The default (`None`) is to perform a
                logical AND over all the dimensions of the input
                array. *axis* may be negative, in which case it counts
                from the last to the first axis.

            {{collapse keepdims: `bool`, optional}}

            {{split_every: `int` or `dict`, optional}}

        :Returns:

            `Data`
                Whether or not all data array elements evaluate to True.

        **Examples**

        >>> d = {{package}}.Data([[1, 2], [3, 4]])
        >>> d.all()
        <{{repr}}Data(1, 1): [[True]]>
        >>> d.all(keepdims=False)
        <{{repr}}Data(1, 1): True>
        >>> d.all(axis=0)
        <{{repr}}Data(1, 2): [[True, True]]>
        >>> d.all(axis=1)
        <{{repr}}Data(2, 1): [[True, True]]>
        >>> d.all(axis=())
        <{{repr}}Data(2, 2): [[True, ..., True]]>

        >>> d[0] = {{package}}.masked
        >>> d[1, 0] = 0
        >>> print(d.array)
        [[-- --]
         [0 4]]
        >>> d.all(axis=0)
        <{{repr}}Data(1, 2): [[False, True]]>
        >>> d.all(axis=1)
        <{{repr}}Data(2, 1): [[--, False]]>

        >>> d[...] = {{package}}.masked
        >>> d.all()
        <{{repr}}Data(1, 1): [[--]]>
        >>> bool(d.all())
        True
        >>> bool(d.all(keepdims=False))
        False

        """
        d = self.copy(array=False)
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=True
        )
        dx = da.all(dx, axis=axis, keepdims=keepdims, split_every=split_every)
        d._set_dask(dx, in_memory=True)
        d.hardmask = self._DEFAULT_HARDMASK
        d._Units = self._Units_class(None)
        return d

    def any(self, axis=None, keepdims=True, split_every=None):
        """Test whether any data array elements evaluate to True.

        .. seealso:: `all`

        :Parameters:

            axis: (sequence of) `int`, optional
                Axis or axes along which a logical OR reduction is
                performed. The default (`None`) is to perform a
                logical OR over all the dimensions of the input
                array. *axis* may be negative, in which case it counts
                from the last to the first axis.

            {{collapse keepdims: `bool`, optional}}

            {{split_every: `int` or `dict`, optional}}

        :Returns:

            `Data`
                Whether or any data array elements evaluate to True.

        **Examples**

        >>> d = {{package}}.Data([[0, 2], [0, 4]])
        >>> d.any()
        <{{repr}}Data(1, 1): [[True]]>
        >>> d.any(keepdims=False)
        <{{repr}}Data(1, 1): True>
        >>> d.any(axis=0)
        <{{repr}}Data(1, 2): [[False, True]]>
        >>> d.any(axis=1)
        <{{repr}}Data(2, 1): [[True, True]]>
        >>> d.any(axis=())
        <{{repr}}Data(2, 2): [[False, ..., True]]>

        >>> d[0] = {{package}}.masked
        >>> print(d.array)
        [[-- --]
         [0 4]]
        >>> d.any(axis=0)
        <{{repr}}Data(1, 2): [[False, True]]>
        >>> d.any(axis=1)
        <{{repr}}Data(2, 1): [[--, True]]>

        >>> d[...] = {{package}}.masked
        >>> d.any()
        <{{repr}}Data(1, 1): [[--]]>
        >>> bool(d.any())
        False
        >>> bool(d.any(keepdims=False))
        False

        """
        d = self.copy(array=False)
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=True
        )
        dx = da.any(dx, axis=axis, keepdims=keepdims, split_every=split_every)
        d._set_dask(dx, in_memory=True)
        d.hardmask = self._DEFAULT_HARDMASK
        d._Units = self._Units_class(None)
        return d

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

        .. seealso:: `get_fill_value`, `hardmask`, `mask`

        :Parameters:

            fill_values: `bool` or sequence of scalars, optional
                Specify values that will be set to missing data. Data
                elements exactly equal to any of the values are set to
                missing data.

                If True then the value returned by the
                `get_fill_value` method, if such a value exists, is
                used.

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
                A scalar specifying the minimum valid value. Data
                elements strictly less than this number will be set to
                missing data.

            valid_max: number, optional
                A scalar specifying the maximum valid value. Data
                elements strictly greater than this number will be set
                to missing data.

            valid_range: (number, number), optional
                A vector of two numbers specifying the minimum and
                maximum valid values, equivalent to specifying values
                for both *valid_min* and *valid_max* parameters. The
                *valid_range* parameter must not be set if either
                *valid_min* or *valid_max* is defined.

                *Parameter example:*
                  ``valid_range=[-999, 10000]`` is equivalent to setting
                  ``valid_min=-999, valid_max=10000``

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The data with masked values. If the operation was in-place
                then `None` is returned.

        **Examples**

        >>> import numpy
        >>> d = {{package}}.Data(numpy.arange(12).reshape(3, 4), 'm')
        >>> d[1, 1] = {{package}}.masked
        >>> print(d.array)
        [[0 1 2 3]
         [4 -- 6 7]
         [8 9 10 11]]
        >>> print(d.apply_masking().array)
        [[0 1 2 3]
         [4 -- 6 7]
         [8 9 10 11]]
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
        [[0 1 2 3]
         [4 -- 6 --]
         [8 9 10 11]]
        >>> print(d.apply_masking(fill_values=True,
        ...                       valid_range=[2, 8]).array)
        [[-- -- 2 3]
         [4 -- 6 --]
         [8 -- -- --]]

        """
        # Parse valid_range
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

        # Parse fill_values
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
                iter(fill_values)
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

        d = _inplace_enabled_define_and_cleanup(self)

        dx = self.to_dask_array(
            _force_mask_hardness=True, _force_to_memory=True
        )

        mask = None
        if fill_values:
            mask = dx == fill_values[0]

            for fill_value in fill_values[1:]:
                mask |= dx == fill_value

        if valid_min is not None:
            if mask is None:
                mask = dx < valid_min
            else:
                mask |= dx < valid_min

        if valid_max is not None:
            if mask is None:
                mask = dx > valid_max
            else:
                mask |= dx > valid_max

        if mask is not None:
            dx = da.ma.masked_where(mask, dx)
            CFA = self._CFA
        else:
            CFA = self._NONE

        d._set_dask(dx, clear=self._ALL ^ CFA, in_memory=True)

        return d

    @classmethod
    def asdata(cls, d, dtype=None, copy=False):
        """Convert the input to a `Data` object.

        If the input *d* has the Data interface (i.e. it has a
        `__data__` method), then the output of this method is used as
        the returned `Data` object. Otherwise, `Data(d)` is returned.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            d: data-like
                Input data in any form that can be converted to a
                `Data` object. This includes `Data` and `Field`
                objects, and objects with the Data interface, numpy
                arrays and any object which may be converted to a
                numpy array.

            dtype: data-type, optional
                By default, the data-type is inferred from the input
                data.

            copy: `bool`, optional
                If True and *d* has the Data interface, then a copy of
                `d.__data__()` is returned.

        :Returns:

            `Data`
                `Data` interpretation of *d*. No copy is performed on
                the input if it is already a `Data` object with
                matching dtype and *copy* is False.

        **Examples**

        >>> d = {{package}}.Data([1, 2])
        >>> {{package}}.Data.asdata(d) is d
        True
        >>> d.asdata(d) is d
        True

        >>> {{package}}.Data.asdata([1, 2])
        <{{repr}}Data: [1, 2]>

        >>> {{package}}.Data.asdata(numpy.array([1, 2]))
        <{{repr}}Data: [1, 2]>

        """
        data = getattr(d, "__data__", None)
        if data is None:
            # d does not have a Data interface
            data = cls(d)
            if dtype is not None:
                data.dtype = dtype

            return data

        # d does have a Data interface
        data = data()
        if copy:
            data = data.copy()
            if dtype is not None and np.dtype(dtype) != data.dtype:
                data.dtype = dtype
        elif dtype is not None and np.dtype(dtype) != data.dtype:
            data = data.copy()
            data.dtype = dtype

        return data

    def chunk_indices(self):
        """Return indices of the data that define each dask chunk.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `chunks`, `chunk_positions`

        :Returns:

            `itertools.product`
                An iterator over tuples of indices of the data array.

        **Examples**

        >>> d = {{package}}.Data(np.arange(405).reshape(3, 9, 15),
        ...     chunks=((1, 2), (9,), (4, 5, 6)))
        >>> d.npartitions
        6
        >>> for index in d.chunk_indices():
        ...     print(index)
        ...
        (slice(0, 1, None), slice(0, 9, None), slice(0, 4, None))
        (slice(0, 1, None), slice(0, 9, None), slice(4, 9, None))
        (slice(0, 1, None), slice(0, 9, None), slice(9, 15, None))
        (slice(1, 3, None), slice(0, 9, None), slice(0, 4, None))
        (slice(1, 3, None), slice(0, 9, None), slice(4, 9, None))
        (slice(1, 3, None), slice(0, 9, None), slice(9, 15, None))

        """
        return chunk_indices(self.chunks)

    def chunk_positions(self):
        """Find the position of each chunk.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `chunks`, `chunk_indices`

        :Parameters:

            chunks: `tuple`

                The chunk sizes along each dimension, as output by
                `dask.array.Array.chunks`.

        **Examples**

        >>> d = {{package}}.Data(np.arange(405).reshape(3, 9, 15),
        ...     chunks=((1, 2), (9,), (4, 5, 6)))
        >>> d.npartitions
        6
        >>> for position in d.chunk_positions():
        ...     print(position)
        ...
        (0, 0, 0)
        (0, 0, 1)
        (0, 0, 2)
        (1, 0, 0)
        (1, 0, 1)
        (1, 0, 2)

        """
        return chunk_positions(self.chunks)

    @_inplace_enabled(default=False)
    def compressed(self, inplace=False):
        """Return all non-masked values in a one dimensional data array.

        Not to be confused with compression by convention (see the
        `uncompress` method).

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `flatten`

        :Parameters:

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The non-masked values, or `None` if the operation was
                in-place.

        **Examples**

        >>> d = {{package}}.{class}}(numpy.arange(12).reshape(3, 4), 'm')
        >>> print(d.array)
        [[ 0  1  2  3]
         [ 4  5  6  7]
         [ 8  9 10 11]]
        >>> print(d.compressed().array)
        [ 0  1  2  3  4  5  6  7  8  9 10 11]
        >>> d[1, 1] = {{package}}.masked
        >>> d[2, 3] = {{package}}.masked
        >>> print(d.array)
        [[0  1  2  3]
         [4 --  6  7]
         [8  9 10 --]]
        >>> print(d.compressed().array)
        [ 0  1  2  3  4  6  7  8  9 10]

        >>> d = {{package}}.{class}}(9)
        >>> print(d.compressed().array)
        [9]

        """
        d = _inplace_enabled_define_and_cleanup(self)

        dx = d.to_dask_array(_force_mask_hardness=True, _force_to_memory=True)
        dx = da.blockwise(
            np.ma.compressed,
            "i",
            dx.ravel(),
            "i",
            adjust_chunks={"i": lambda n: np.nan},
            dtype=dx.dtype,
            meta=np.array((), dtype=dx.dtype),
        )

        d._set_dask(dx, clear=self._ALL, in_memory=True)
        return d

    def compute(self, _force_to_memory=True):
        """A view of the computed data.

        In-place changes to the returned array *might* affect the
        underlying Dask array, depending on how the that Dask array
        has been defined.

        The returned array has the same mask hardness and fill value
        as the data.

        Compare with `array`.

        **Performance**

        `compute` causes all delayed operations to be computed.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `persist`, `array`, `datetime_array`,
                     `sparse_array`

        :Parameters:

            _force_to_memory: `bool`, optional
                If True (the default) then force the data resulting
                from computing the returned Dask graph to be in
                memory. If False then the data resulting from
                computing the Dask graph may or may not be in memory,
                depending on the nature of the stack

        :Returns:

                An in-memory view of the data

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3.0], 'km')
        >>> d.compute()
        array([1., 2., 3.])

        >>> from scipy.sparse import csr_array
        >>> d = {{package}}.Data(csr_array((2, 3)))
        >>> d.compute()
        <2x3 sparse array of type '<class 'numpy.float64'>'
                with 0 stored elements in Compressed Sparse Row format>
        >>> d.array
        array([[0., 0., 0.],
               [0., 0., 0.]])
        >>> d.compute().toarray()
        array([[0., 0., 0.],
               [0., 0., 0.]])

        >>> f = {{package}}.example_field(0)
        >>> {{package}}.write(f, 'file.nc')
        >>> f = {{package}}.read('file.nc')[0]
        >>> print(f.data.compute())
        [[0.007 0.034 0.003 0.014 0.018 0.037 0.024 0.029]
         [0.023 0.036 0.045 0.062 0.046 0.073 0.006 0.066]
         [0.11  0.131 0.124 0.146 0.087 0.103 0.057 0.011]
         [0.029 0.059 0.039 0.07  0.058 0.072 0.009 0.017]
         [0.006 0.036 0.019 0.035 0.018 0.037 0.034 0.013]]
        >>> f.data.compute(_force_to_memory=False)
        <{{repr}}NetCDF4Array(5, 8): file.nc, q(5, 8)>

        """
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=_force_to_memory
        )
        a = dx.compute()

        if np.ma.isMA(a) and a is not np.ma.masked:
            if self.hardmask:
                a.harden_mask()
            else:
                a.soften_mask()

            a.set_fill_value(self.get_fill_value(None))

        return a

    @classmethod
    def concatenate(
        cls, data, axis=0, cull_graph=False, relaxed_units=False, copy=True
    ):
        """Join a sequence of data arrays together.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `cull_graph`

        :Parameters:

            data: sequence of `Data`
                The data arrays to be concatenated. Concatenation is
                carried out in the order given. Each data array must
                have equivalent units and the same shape, except in
                the concatenation axis. Note that scalar arrays are
                treated as if they were one dimensional.

            axis: `int`, optional
                The axis along which the arrays will be joined. The
                default is 0. Note that scalar arrays are treated as
                if they were one dimensional.

            {{cull_graph: `bool`, optional}}

            {{relaxed_units: `bool`, optional}}

            copy: `bool`, optional
                If True (the default) then make copies of the data, if
                required, prior to the concatenation, thereby ensuring
                that the input data arrays are not changed by the
                concatenation process. If False then some or all input
                data arrays might be changed in-place, but the
                concatenation process will be faster.

        :Returns:

            `Data`
                The concatenated data.

        **Examples**

        >>> d = {{package}}.Data([[1, 2], [3, 4]])
        >>> e = {{package}}.Data([[5.0, 6.0]])
        >>> f = {{package}}.Data.concatenate((d, e))
        >>> print(f.array)
        [[ 1.     2.   ]
         [ 3.     4.   ]
         [ 5.     6.   ]]
        >>> f.equals({{package}}.Data.concatenate((d, e), axis=-2))
        True

        >>> e = {{package}}.Data([[5.0], [6.0]])
        >>> f = {{package}}.Data.concatenate((d, e), axis=1)
        >>> print(f.array)
        [[ 1.     2.     5.]
         [ 3.     4.     6.]]

        >>> d = {{package}}.Data(1)
        >>> e = {{package}}.Data(50.0)
        >>> f = {{package}}.Data.concatenate((d, e))
        >>> print(f.array)
        [ 1.    50.]

        """
        if isinstance(data, cls):
            raise ValueError("Must provide a sequence of Data objects")

        data = tuple(data)
        n_data = len(data)
        if not n_data:
            raise ValueError(
                "Can't concatenate: Must provide at least one Data object"
            )

        if cull_graph:
            # Remove unnecessary components from the graph, which may
            # improve performance, and because complicated task graphs
            # can sometimes confuse da.concatenate.
            for d in data:
                d.cull_graph()

        data0 = data[0]
        units0 = data0.Units
        data0_cached_elements = data0._get_cached_elements()

        if copy:
            data0 = data0.copy()

        if not data0.ndim:
            data0.insert_dimension(inplace=True)

        if n_data == 1:
            return data0

        conformed_data = [data0]
        for data1 in data[1:]:
            # Turn any scalar array into a 1-d array
            copied = False
            if not data1.ndim:
                if copy:
                    data1 = data1.copy()
                    copied = True

                data1.insert_dimension(inplace=True)

            # Check and conform the units of data1 with respect to
            # those of data0
            data1 = cls._concatenate_conform_units(
                data1, units0, relaxed_units, copy and not copied
            )

            conformed_data.append(data1)

        # Get data as dask arrays and apply concatenation operation
        dxs = [
            d.to_dask_array(_force_mask_hardness=False, _force_to_memory=False)
            for d in conformed_data
        ]
        dx = da.concatenate(dxs, axis=axis)

        # ------------------------------------------------------------
        # Set the aggregation write status
        # ------------------------------------------------------------
        #
        # Assume at first that all input data instances have True
        # status, but then ..
        CFA = cls._CFA
        for d in conformed_data:
            if not d.nc_get_aggregation_write_status():
                # 1) The status must be False when any input data
                #    object has False status.
                CFA = cls._NONE
                break

        if CFA != cls._NONE:
            non_concat_axis_chunks0 = list(data[0].chunks)
            non_concat_axis_chunks0.pop(axis)
            for d in conformed_data[1:]:
                non_concat_axis_chunks = list(d.chunks)
                non_concat_axis_chunks.pop(axis)
                if non_concat_axis_chunks != non_concat_axis_chunks0:
                    # 2) The status must be False when any two input
                    #    data objects have different Dask chunk
                    #    patterns for the non-concatenated axes.
                    CFA = cls._NONE
                    break

        # ------------------------------------------------------------
        # Set the aggregation fragment type
        # ------------------------------------------------------------
        if CFA != cls._NONE:
            fragment_type0 = data[0].nc_get_aggregation_fragment_type()
            for d in conformed_data[1:]:
                fragment_type1 = d.nc_get_aggregation_fragment_type()
                if fragment_type1 != fragment_type0 and "location" in (
                    fragment_type1,
                    fragment_type0,
                ):
                    # 3) The status must be False when any two input
                    #    Data objects have different fragment types,
                    #    onew of which is 'location'.
                    data0._nc_del_aggregation_fragment_type()
                    CFA = cls._NONE
                    break

        # ------------------------------------------------------------
        # Set the __in_memory__ status
        # ------------------------------------------------------------
        in_memory = data[0].__in_memory__
        for d in conformed_data[1:]:
            if d.__in_memory__ != in_memory:
                # If and only if any two input Data objects have
                # different __in_memory__ values, then set
                # in_memory=False for the concatenation.
                in_memory = False
                break

        # ------------------------------------------------------------
        # Set the concatenated dask array
        # ------------------------------------------------------------
        data0._set_dask(dx, clear=cls._ALL ^ CFA, in_memory=in_memory)

        #        # ------------------------------------------------------------
        #        # Set the aggregation 'aggregated_data' terms
        #        # ------------------------------------------------------------
        #        if data0.nc_get_aggregation_write_status():
        #            # Set the netCDF aggregated_data terms, giving precedence
        #            # to those towards the left hand side of the input
        #            # list. If any input Data object has no aggregated_data
        #            # terms, then nor will the concatenated data.
        #            aggregated_data = {}
        #            for d in conformed_data[::-1]:
        #                value = d.nc_get_aggregated_data()
        #                if not value:
        #                    aggregated_data = {}
        #                    break
        #
        #                aggregated_data.update(value)
        #
        #            data0.nc_set_aggregated_data(aggregated_data)
        #
        # ------------------------------------------------------------
        # Re-set appropriate cached elements (after '_set_dask' has
        # just cleared them from data0)
        # ------------------------------------------------------------
        cached_elements = {}
        i = 0
        element = data0_cached_elements.get(i)
        if element is not None:
            cached_elements[i] = element

        i = -1
        element = conformed_data[i]._get_cached_elements().get(i)
        if element is not None:
            cached_elements[i] = element

        if cached_elements:
            data0._set_cached_elements(cached_elements)

        # ------------------------------------------------------------
        # Apply extra post-processing to the concatenated data
        # ------------------------------------------------------------
        data0 = cls._concatenate_post_process(data0, axis, conformed_data)

        # Return the concatenated data
        return data0

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

        >>> d = {{package}}.Data([[0.0, 45.0], [45.0, 90.0]],
        ...                           units='degrees_east')
        >>> print(d.creation_commands())
        data = {{package}}.Data([[0.0, 45.0], [45.0, 90.0]], units='degrees_east', dtype='f8')

        >>> d = {{package}}.Data(['alpha', 'beta', 'gamma', 'delta'],
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
                name="mask", namespace=namespace0, indent=indent, string=True
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

    @_inplace_enabled(default=True)
    def cull_graph(self, inplace=True):
        """Remove unnecessary tasks from the dask graph in-place.

        **Performance**

        An unnecessary task is one which does not contribute to the
        computed result. Such tasks are always automatically removed
        (culled) at compute time, but removing them beforehand might
        improve performance by reducing the amount of work done in
        later steps.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `dask.optimization.cull`

        :Parameters:

            {{inplace: `bool`, optional}}

                .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `None`

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3, 4, 5], chunks=3)
        >>> d = d[:2]
        >>> dict(d.to_dask_array().dask)
        {('array-729a27a557981dd627b6c07e8ef93250', 0): array([1, 2, 3]),
         ('array-729a27a557981dd627b6c07e8ef93250', 1): array([4, 5]),
         ('getitem-9890f07ccf98df4ab5231fbd87792f74',
          0): <Task ('getitem-9890f07ccf98df4ab5231fbd87792f74', 0) getitem(...)>,
         ('cfdm_harden_mask-d28b364730f9d5b38cfbd835b29a403c',
          0): <Task ('cfdm_harden_mask-d28b364730f9d5b38cfbd835b29a403c', 0) cfdm_harden_mask(...)>}
        >>> d.cull_graph()
        {('getitem-9890f07ccf98df4ab5231fbd87792f74',
          0): <Task ('getitem-9890f07ccf98df4ab5231fbd87792f74', 0) getitem(...)>,
         ('array-729a27a557981dd627b6c07e8ef93250', 0): array([1, 2, 3]),
         ('cfdm_harden_mask-d28b364730f9d5b38cfbd835b29a403c',
          0): <Task ('cfdm_harden_mask-d28b364730f9d5b38cfbd835b29a403c', 0) cfdm_harden_mask(...)>}

        """
        d = _inplace_enabled_define_and_cleanup(self)

        dx = d.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        dsk, _ = cull(dx.dask, dx.__dask_keys__())
        dx = da.Array(dsk, name=dx.name, chunks=dx.chunks, dtype=dx.dtype)
        d._set_dask(dx, clear=d._NONE, in_memory=None)

        return d

    def del_calendar(self, default=ValueError()):
        """Delete the calendar.

        .. seealso:: `get_calendar`, `has_calendar`, `set_calendar`,
                     `del_units`, `Units`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                calendar has not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

            `str`
                The value of the deleted calendar.

        **Examples**

        >>> d = {{package}}.Data(1, "days since 2000-1-1", calendar="noleap")
        >>> d.del_calendar()
        'noleap'
        >>> print(d.del_calendar())
        None

        >>> d = {{package}}.Data(1, "days since 2000-1-1")
        >>> print(d.del_calendar())
        None

        >>> d = {{package}}.Data(1, "m")
        Traceback (most recent call last):
            ...
        ValueError: Units <Units: m> have no calendar

        """
        units = self.Units
        if not units.isreftime:
            return self._default(default, f"Units {units!r} have no calendar")

        calendar = getattr(units, "calendar", None)
        if calendar is None:
            return self._default(
                default, f"{self.__class__.__name__} has no calendar"
            )

        self._Units = self._Units_class(self.get_units(None), None)
        return calendar

    def del_units(self, default=ValueError()):
        """Delete the units.

        .. seealso:: `get_units`, `has_units`, `set_units`,
                     `del_calendar`, `Units`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                units has not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

            `str`
                The value of the deleted units.

        **Examples**

        >>> d = {{package}}.Data(1, "m")
        >>> d.del_units()
        'm'
        >>> d.Units
        <Units: >
        >>> d.del_units()
        Traceback (most recent call last):
            ...
        ValueError: Data has no units

        >>> d = {{package}}.Data(1, "days since 2000-1-1", calendar="noleap")
        >>> d.del_units()
        'days since 2000-1-1'
        >>> d.Units
        <Units: noleap>

        """
        u = self.Units
        units = getattr(u, "units", None)
        calendar = getattr(u, "calendar", None)
        self._Units = self._Units_class(None, calendar)

        if units is not None:
            return units

        return self._default(
            default, f"{self.__class__.__name__} has no units"
        )

    @classmethod
    def empty(
        cls,
        shape,
        dtype=None,
        units=None,
        calendar=None,
        chunks="auto",
    ):
        """Return a new array, without initialising entries.

        :Parameters:

            shape: `int` or `tuple` of `int`
                The shape of the new array. e.g. ``(2, 3)`` or ``2``.

            dtype: data-type
                The desired output data-type for the array, e.g.
                `numpy.int8`. The default is `numpy.float64`.

            units: `str` or `Units`
                The units for the new data array.

            calendar: `str`, optional
                The calendar for reference time units.

            {{chunks: `int`, `tuple`, `dict` or `str`, optional}}

                .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `Data`
                Array of uninitialised (arbitrary) data of the given
                shape and dtype.

        **Examples**

        >>> d = {{package}}.Data.empty((2, 2))
        >>> print(d.array)
        [[ -9.74499359e+001  6.69583040e-309],
         [  2.13182611e-314  3.06959433e-309]]         #uninitialised

        >>> d = {{package}}.Data.empty((2,), dtype=bool)
        >>> print(d.array)
        [ False  True]                                 #uninitialised

        """
        dx = da.empty(shape, dtype=dtype, chunks=chunks)
        return cls(dx, units=units, calendar=calendar)

    @_manage_log_level_via_verbosity
    def equals(
        self,
        other,
        rtol=None,
        atol=None,
        ignore_fill_value=False,
        ignore_data_type=False,
        ignore_type=False,
        verbose=None,
        traceback=False,
        ignore_compression=False,
        _check_values=True,
    ):
        """True if two data arrays are logically equal, False otherwise.

        {{equals tolerance}}

        :Parameters:

            other:
                The object to compare for equality.

            {{rtol: number, optional}}

            {{atol: number, optional}}

            ignore_fill_value: `bool`, optional
                If True then data arrays with different fill values are
                considered equal. By default they are considered unequal.

            {{ignore_data_type: `bool`, optional}}

            {{ignore_type: `bool`, optional}}

            {{verbose: `int` or `str` or `None`, optional}}

            {{ignore_compression: `bool`, optional}}

        :Returns:

            `bool`
                Whether or not the two instances are equal.

        **Examples**

        >>> d.equals(d)
        True
        >>> d.equals(d + 1)
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

        self_dx = self.to_dask_array(_force_mask_hardness=False)
        other_dx = other.to_dask_array(_force_mask_hardness=False)

        # Check that each instance has the same data type
        self_is_numeric = is_numeric_dtype(self_dx)
        other_is_numeric = is_numeric_dtype(other_dx)
        if (
            not ignore_data_type
            and (self_is_numeric or other_is_numeric)
            and self.dtype != other.dtype
        ):
            logger.info(
                f"{self.__class__.__name__}: Different data types: "
                f"{self.dtype} != {other.dtype}"
            )  # pragma: no cover
            return False

        # Check that each instance has the same units.
        self_Units = self.Units
        other_Units = other.Units
        if self_Units != other_Units:
            if is_log_level_info(logger):
                logger.info(
                    f"{self.__class__.__name__}: Different Units "
                    f"({self_Units!r}, {other_Units!r})"
                )

            return False

        # Return now if we have been asked to not check the array
        # values
        if not _check_values:
            return True

        # ------------------------------------------------------------
        # Check that each instance has equal array values
        # ------------------------------------------------------------
        if rtol is None:
            rtol = self._rtol
        else:
            rtol = float(rtol)

        if atol is None:
            atol = self._atol
        else:
            atol = float(atol)

        # Return False if there are different cached elements. This
        # provides a possible short circuit for that case that two
        # arrays are not equal (but not in the case that they are).
        cache0 = self._get_cached_elements()
        if cache0:
            cache1 = other._get_cached_elements()
            if cache1 and sorted(cache0) == sorted(cache1):
                for key, value0 in cache0.items():
                    value1 = cache1[key]
                    if value0 is np.ma.masked or value1 is np.ma.masked:
                        # Don't test on masked values - this logic is
                        # determined elsewhere.
                        continue

                    if not _numpy_allclose(
                        value0, value1, rtol=rtol, atol=atol
                    ):
                        if is_log_level_info(logger):
                            logger.info(
                                f"{self.__class__.__name__}: Different array "
                                f"values (atol={atol}, rtol={rtol})"
                            )

                        return False

        # Now check that corresponding elements are equal within a tolerance.
        # We assume that all inputs are masked arrays. Note we compare the
        # data first as this may return False due to different dtype without
        # having to wait until the compute call.
        if self_is_numeric and other_is_numeric:
            data_comparison = allclose(
                self_dx,
                other_dx,
                masked_equal=True,
                rtol=rtol,
                atol=atol,
            )
        elif not self_is_numeric and not other_is_numeric:
            # If the array (say d) is fully masked, then the output of
            # np.all(d == d) and therefore da.all(d == d) will be a
            # np.ma.masked object which has dtype('float64'), and not
            # a Boolean, causing issues later. To ensure data_comparison
            # is Boolean, we must do an early compute to check if it is
            # a masked object and if so, force the desired result (True).
            #
            # This early compute won't degrade performance because it
            # would be performed towards result.compute() below anyway.
            data_comparison = da.all(self_dx == other_dx).compute()
            if data_comparison is np.ma.masked:
                data_comparison = True

        else:  # one is numeric and other isn't => not equal (incompat. dtype)
            if is_log_level_info(logger):
                logger.info(
                    f"{self.__class__.__name__}: Different data types:"
                    f"{self_dx.dtype} != {other_dx.dtype}"
                )

            return False

        mask_comparison = da.all(
            da.equal(da.ma.getmaskarray(self_dx), da.ma.getmaskarray(other_dx))
        )

        # Apply a (dask) logical 'and' to confirm if both the mask and the
        # data are equal for the pair of masked arrays:
        result = da.logical_and(data_comparison, mask_comparison)
        if not result.compute():
            if is_log_level_info(logger):
                logger.info(
                    f"{self.__class__.__name__}: Different array values ("
                    f"atol={atol}, rtol={rtol})"
                )

            return False
        else:
            return True

    def file_directories(self, normalise=False):
        """The directories of files containing parts of the data.

        Returns the locations of any files referenced by the data.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `get_filenames`, `replace_directory`

        :Returns:

            `set`
                The unique set of file directories as absolute paths.

        **Examples**

        >>> d.file_directories()
        {'https:///data/1', 'file:///data2'}

        """
        out = []
        append = out.append
        for key, a in self.todict(
            _force_mask_hardness=False, _force_to_memory=False
        ).items():
            try:
                append(a.file_directory(normalise=normalise))
            except AttributeError:
                # This graph element doesn't contain a file name
                pass

        return set(out)

    @_inplace_enabled(default=False)
    def filled(self, fill_value=None, inplace=False):
        """Replace masked elements with a fill value.

        .. versionadded:: (cfdm) 1.8.7.0

        :Parameters:

            fill_value: scalar, optional
                The fill value. By default the fill returned by
                `get_fill_value` is used, or if this is not set then
                the netCDF default fill value for the data type is
                used, as defined by `netCDF.default_fillvals`.

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The filled data, or `None` if the operation was in-place.

        **Examples**

        >>> d = {{package}}.Data([[1, 2, 3]])
        >>> print(d.filled().array)
        [[1 2 3]]
        >>> d[0, 0] = {{package}}.masked
        >>> print(d.filled().array)
        [-9223372036854775806                    2                    3]
        >>> d.set_fill_value(-99)
        >>> print(d.filled().array)
        [[-99   2   3]]

        """
        d = _inplace_enabled_define_and_cleanup(self)

        if fill_value is None:
            fill_value = d.get_fill_value(None)
            if fill_value is None:  # still...
                fill_value = default_fillvals.get(d.dtype.str[1:])
                if fill_value is None and d.dtype.kind in ("SU"):
                    fill_value = default_fillvals.get("S1", None)

                if fill_value is None:
                    raise ValueError(
                        "Can't determine fill value for "
                        f"data type {d.dtype.str!r}"
                    )

        dx = d.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        dx = dx.map_blocks(cfdm_filled, fill_value=fill_value, dtype=d.dtype)
        d._set_dask(dx, clear=self._ALL, in_memory=True)

        return d

    def first_element(self):
        """Return the first element of the data as a scalar.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `last_element`, `second_element`

        **Performance**

        If possible, a cached value is returned. Otherwise the delayed
        operations needed to compute the element are executed, and
        cached for subsequent calls.

        :Returns:

                The first element of the data.

        **Examples**

        >>> d = {{package}}.Data(9.0)
        >>> x = d.first_element()
        >>> print(x, type(x))
        9.0 <class 'float'>

        >>> d = {{package}}.Data([[1, 2], [3, 4]])
        >>> x = d.first_element()
        >>> print(x, type(x))
        1 <class 'int'>
        >>> d[0, 0] = {{package}}.masked
        >>> y = d.first_element()
        >>> print(y, type(y))
        -- <class 'numpy.ma.core.MaskedConstant'>

        >>> d = {{package}}.Data(['foo', 'bar'])
        >>> x = d.first_element()
        >>> print(x, type(x))
        foo <class 'str'>

        """
        try:
            return self._get_cached_elements()[0]
        except KeyError:
            item = self._item((slice(0, 1, 1),) * self.ndim)
            self._set_cached_elements({0: item})
            return self._get_cached_elements()[0]

    @_inplace_enabled(default=False)
    def flatten(self, axes=None, inplace=False):
        """Flatten specified axes of the data.

        Any subset of the axes may be flattened.

        The shape of the data may change, but the size will not.

        The flattening is executed in row-major (C-style) order. For
        example, the array ``[[1, 2], [3, 4]]`` would be flattened across
        both dimensions to ``[1 2 3 4]``.

        .. versionadded:: (cfdm) 1.7.11

        .. seealso:: `compressed`, `insert_dimension`, `squeeze`,
                     `transpose`

        :Parameters:

            axes: (sequence of) `int`
                Select the axes to be flattened. By default all axes
                are flattened. Each axis is identified by its positive
                or negative integer position. No axes are flattened if
                *axes* is an empty sequence.

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The flattened data, or `None` if the operation was
                in-place.

        **Examples**

        >>> import numpy as np
        >>> d = {{package}}.Data(np.arange(24).reshape(1, 2, 3, 4))
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

        ndim = d.ndim
        if not ndim:
            if axes or axes == 0:
                raise ValueError(
                    "Can't flatten: Can't remove axes from "
                    f"scalar {self.__class__.__name__}"
                )

            return d

        if axes is None:
            axes = list(range(ndim))
        else:
            axes = sorted(d._parse_axes(axes))

        if len(axes) <= 1:
            return d

        original_shape = self.shape

        # It is important that the first axis in the list is the
        # left-most flattened axis.
        #
        # E.g. if the shape is (10, 20, 30, 40, 50, 60) and the axes
        #      to be flattened are [2, 4], then the data must be
        #      transposed with order [0, 1, 2, 4, 3, 5]
        order = [i for i in range(ndim) if i not in axes]
        order[axes[0] : axes[0]] = axes
        d.transpose(order, inplace=True)

        # Find the flattened shape.
        #
        # E.g. if the *transposed* shape is (10, 20, 30, 50, 40, 60)
        #      and *transposed* axes [2, 3] are to be flattened then
        #      the new shape will be (10, 20, 1500, 40, 60)
        new_shape = [n for i, n in enumerate(original_shape) if i not in axes]
        new_shape.insert(axes[0], prod([original_shape[i] for i in axes]))

        dx = d.to_dask_array(_force_mask_hardness=True, _force_to_memory=True)
        dx = dx.reshape(new_shape)
        d._set_dask(dx, clear=self._ALL, in_memory=True)

        # Update the axis names
        data_axes0 = d._axes
        data_axes = [
            axis for i, axis in enumerate(data_axes0) if i not in axes
        ]
        data_axes.insert(axes[0], new_axis_identifier(data_axes0))
        d._axes = data_axes

        # Update the dataset chunking strategy
        if (
            isinstance(d.nc_dataset_chunksizes(), tuple)
            and d.shape != original_shape
        ):
            d.nc_clear_dataset_chunksizes()

        return d

    @classmethod
    def full(
        cls,
        shape,
        fill_value,
        dtype=None,
        units=None,
        calendar=None,
        chunks="auto",
    ):
        """Return new data filled with a fill value.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `empty`, `ones`, `zeros`

        :Parameters:

            shape: `int` or `tuple` of `int`
                The shape of the new array. e.g. ``(2, 3)`` or ``2``.

            fill_value: scalar
                The fill value.

            dtype: data-type
                The desired data-type for the array. The default, `None`,
                means ``np.array(fill_value).dtype``.

            units: `str` or `Units`
                The units for the new data array.

            calendar: `str`, optional
                The calendar for reference time units.

            {{chunks: `int`, `tuple`, `dict` or `str`, optional}}

        :Returns:

            `Data`
                Array of *fill_value* with the given shape and data
                type.

        **Examples**

        >>> d = {{package}}.Data.full((2, 3), -99)
        >>> print(d.array)
        [[-99 -99 -99]
         [-99 -99 -99]]

        >>> d = {{package}}.Data.full(2, 0.0)
        >>> print(d.array)
        [0. 0.]

        >>> d = {{package}}.Data.full((2,), 0, dtype=bool)
        >>> print(d.array)
        [False False]

        """
        if dtype is None:
            # Need to explicitly set the default because dtype is not
            # a named keyword of da.full
            dtype = getattr(fill_value, "dtype", None)
            if dtype is None:
                dtype = np.array(fill_value).dtype

        dx = da.full(shape, fill_value, dtype=dtype, chunks=chunks)
        return cls(dx, units=units, calendar=calendar)

    def get_calendar(self, default=ValueError()):
        """Return the calendar.

        .. seealso:: `del_calendar`, `set_calendar`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                calendar has not been set. If set to an `Exception`
                instance then it will be raised instead.

        :Returns:

                The calendar.

        **Examples**

        >>> d.set_calendar('julian')
        >>> d.get_calendar
        'metres'
        >>> d.del_calendar()
        >>> d.get_calendar()
        ValueError: Can't get non-existent calendar
        >>> print(d.get_calendar(None))
        None

        """
        try:
            return self.Units.calendar
        except (ValueError, AttributeError):
            return super().get_calendar(default=default)

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
                f"{self.__class__.__name__!r} has no compressed dimension",
            )

    def get_data(self, default=ValueError(), _units=None, _fill_value=None):
        """Returns the data.

        .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `Data`

        """
        return self

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

    def get_deterministic_name(self):
        """Get the deterministic name for the data.

        If there is a deterministic name then, **in some sense**, the
        data may be assumed to be equal to that of another `Data`
        object with the same deterministic name. This measure of
        equality is different to that applied by the `equals` method
        in that:

        * Numerical tolerance is not accounted for.
        * NaN and inf values are considered equal.

        .. warning:: Two `Data` objects that are considered equal by
                     their `equals` methods could have different
                     deterministic names, and two `Data` objects that
                     are considered unequal by their `equals` methods
                     could have the same deterministic names.

        **Performance**

        Ascertaining a measure of equality via deterministic names
        does not require the Dask array to be computed so is, in
        general, much faster than using the `equals` method.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `has_deterministic_name`

        :Returns:

            `str`
                The deterministic name.

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3], 'm')
        >>> d.has_deterministic_name()
        True
        >>> d.get_deterministic_name()
        '6380dd3674fbf10d30561484b084e9b3'
        >>> d1 = {{package}}.Data([1, 2, 3], 'metre')
        >>> d1.get_deterministic_name()
        '6380dd3674fbf10d30561484b084e9b3'
        >>> d1.get_deterministic_name() == d.get_deterministic_name()
        True
        >>> d1.equals(d)
        True

        >>> e = d + 1 - 1
        >>> e.get_deterministic_name()
        '0b83ada62d4b014bae83c3de1c1d3a80'
        >>> e.get_deterministic_name() == d.get_deterministic_name()
        False
        >>> e.equals(d)
        True

        """
        if not self.has_deterministic_name():
            raise ValueError()

        units = self._Units

        return tokenize(
            self.to_dask_array(
                _force_mask_hardness=False, _force_to_memory=False
            ).name,
            units.formatted(definition=True, names=True),
            units._canonical_calendar,
        )

    def get_filenames(self, normalise=False, per_chunk=False):
        """The names of files containing parts of the data array.

        Returns the names of any files that may be required to deliver
        the computed data array.

        .. seealso:: `replace_filenames, `replace_directory`

        :Parameters:

            {{normalise: `bool`, optional}}

                .. versionadded:: (cfdm) 1.12.0.0

            per_chunk: `bool`, optional
                Return a `numpy` array that provides the file name
                that contributes to each Dask chunk. This array will
                have the same shape as the Dask chunks (as returned by
                the `numblocks` attribute).

                .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `set`
                The file names. If no files are required to compute
                the data then an empty `set` is returned.

        **Examples**

        >>> d = {{package}}.Data.empty((5, 8), 1, chunks=4)
        >>> d.get_filenames()
        set()

        >>> f = {{package}}.example_field(0)
        >>> {{package}}.write(f, "file.nc")
        >>> d = {{package}}.read("file.nc", dask_chunks'128 B')[0].data
        >>> d.get_filenames()
        {'file.nc'}

        >>> d.numblocks
        (2, 2)
        >>> filenames = d.get_filenames(per_chunk=True)
        >>> filenames.shape
        (2, 2)
        >>> print(filenames)
        [['file.nc' 'file.nc']
         ['file.nc' 'file.nc']]

        """
        if per_chunk:
            # --------------------------------------------------------
            # Return the filenames in a numpy array
            # --------------------------------------------------------

            # Maximum number of characters in any file name
            n_char = 1

            filenames = {}
            for index, position in zip(
                self.chunk_indices(), self.chunk_positions()
            ):
                for a in (
                    self[index]
                    .todict(_force_mask_hardness=False, _force_to_memory=False)
                    .values()
                ):
                    try:
                        filename = a.get_filename(
                            normalise=normalise, default=None
                        )
                    except AttributeError:
                        pass
                    else:
                        if filename:
                            if position in filenames:
                                raise ValueError(
                                    "Can't return 'per_chunk' file names: "
                                    f"The Dask chunk in position {position} "
                                    f"(defined by {index!r}) has multiple "
                                    "file locations"
                                )

                            filenames[position] = filename
                            n_char = max(n_char, len(filename))

            array = np.ma.masked_all(
                self.numblocks,
                dtype=f"U{n_char}",
            )
            array.set_fill_value("")

            for position, filename in filenames.items():
                array[position] = filename

            return array

        # ------------------------------------------------------------
        # Return the filenames in a set
        # ------------------------------------------------------------
        out = []
        append = out.append
        for a in self.todict(
            _force_mask_hardness=False, _force_to_memory=False
        ).values():
            try:
                append(a.get_filename(normalise=normalise))
            except AttributeError:
                pass

        return set(out)

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
                dimension. A key identifies a subsampled dimension by
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

    def get_units(self, default=ValueError()):
        """Return the units.

        .. seealso:: `del_units`, `set_units`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the units
                have not been set. If set to an `Exception` instance then
                it will be raised instead.

        :Returns:

                The units.

        **Examples**

        >>> d.set_units('metres')
        >>> d.get_units()
        'metres'
        >>> d.del_units()
        >>> d.get_units()
        ValueError: Can't get non-existent units
        >>> print(d.get_units(None))
        None

        """
        try:
            return self.Units.units
        except (ValueError, AttributeError):
            return super().get_units(default=default)

    def harden_mask(self):
        """Force the mask to hard.

        Whether the mask of a masked array is hard or soft is
        determined by its `hardmask` property. `harden_mask` sets
        `hardmask` to `True`.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `hardmask`, `soften_mask`

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3], hardmask=False)
        >>> d.hardmask
        False
        >>> d.harden_mask()
        >>> d.hardmask
        True

        >>> d = {{package}}.Data([1, 2, 3], mask=[False, True, False])
        >>> d.hardmask
        True
        >>> d[1] = 999
        >>> print(d.array)
        [1 -- 3]

        """
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        dx = dx.map_blocks(cfdm_harden_mask, dtype=dx.dtype)
        self._set_dask(dx, clear=self._NONE, in_memory=True)
        self.hardmask = True

    def has_calendar(self):
        """Whether a calendar has been set.

        .. seealso:: `del_calendar`, `get_calendar`, `set_calendar`,
                     `has_units`, `Units`

        :Returns:

            `bool`
                `True` if the calendar has been set, otherwise
                `False`.

        **Examples**

        >>> d = {{package}}.Data(1, "days since 2000-1-1", calendar="noleap")
        >>> d.has_calendar()
        True

        >>> d = {{package}}.Data(1, calendar="noleap")
        >>> d.has_calendar()
        True

        >>> d = {{package}}.Data(1, "days since 2000-1-1")
        >>> d.has_calendar()
        False

        >>> d = {{package}}.Data(1, "m")
        >>> d.has_calendar()
        False

        """
        return hasattr(self.Units, "calendar")

    def has_deterministic_name(self):
        """Whether there is a deterministic name for the data.

        See `get_deterministic_name` for details.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `get_deterministic_name`

        :Returns:

            `bool`
                Whether or not there is a deterministic name.

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3], 'm')
        >>> d.has_deterministic_name()
        True

        """
        return self._custom.get("has_deterministic_name", False)

    def has_units(self):
        """Whether units have been set.

        .. seealso:: `del_units`, `get_units`, `set_units`,
                     `has_calendar`, `Units`

        :Returns:

            `bool`
                `True` if units have been set, otherwise `False`.

        **Examples**

        >>> d = {{package}}.Data(1, "")
        >>> d.has_units()
        True

        >>> d = {{package}}.Data(1, "m")
        >>> d.has_units()
        True

        >>> d = {{package}}.Data(1)
        >>> d.has_units()
        False

        >>> d = {{package}}.Data(1, calendar='noleap')
        >>> d.has_units()
        False

        """
        return hasattr(self.Units, "units")

    @_inplace_enabled(default=False)
    def insert_dimension(self, position=0, inplace=False):
        """Expand the shape of the data array in place.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `flatten`, `squeeze`, `transpose`

        :Parameters:

            position: `int`, optional
                Specify the position that the new axis will have in the data
                array axes. By default the new axis has position 0, the
                slowest varying position.

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The new data with expanded data axes, or `None` if
                the operation was in-place.

        **Examples**

        >>> d.shape
        (19, 73, 96)
        >>> d.insert_dimension(0).shape
        (1, 96, 73, 19)
        >>> d.insert_dimension(3).shape
        (19, 73, 96, 1)
        >>> d.insert_dimension(-1, inplace=True)
        >>> d.shape
        (19, 73, 1, 96)

        """
        d = _inplace_enabled_define_and_cleanup(self)

        # Parse position
        if not isinstance(position, int):
            raise ValueError("Position parameter must be an integer")

        original_ndim = self.ndim

        if -original_ndim - 1 <= position < 0:
            position += original_ndim + 1
        elif not 0 <= position <= original_ndim:
            raise ValueError(
                f"Can't insert dimension: Invalid position {position!r}"
            )

        #        new_shape = list(d.shape)
        #        new_shape.insert(position, 1)

        dx = d.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        index = [slice(None)] * dx.ndim
        index.insert(position, np.newaxis)
        dx = dx[tuple(index)]

        # Inserting a dimension doesn't affect the cached elements or
        # the CFA write status
        d._set_dask(
            dx, clear=self._ALL ^ self._CACHE ^ self._CFA, in_memory=None
        )

        # Expand _axes
        axis = new_axis_identifier(d._axes)
        data_axes = list(d._axes)
        data_axes.insert(position, axis)
        d._axes = data_axes

        # Update the dataset chunking strategy
        chunksizes = d.nc_dataset_chunksizes()
        if chunksizes and isinstance(chunksizes, tuple):
            chunksizes = list(chunksizes)
            chunksizes.insert(position, 1)
            d.nc_set_dataset_chunksizes(chunksizes)

        return d

    def last_element(self):
        """Return the last element of the data as a scalar.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `first_element`, `second_element`

        **Performance**

        If possible, a cached value is returned. Otherwise the delayed
        operations needed to compute the element are executed, and
        cached for subsequent calls.

        :Returns:

                The last element of the data.

        **Examples**

        >>> d = {{package}}.Data(9.0)
        >>> x = d.last_element()
        >>> print(x, type(x))
        9.0 <class 'float'>

        >>> d = {{package}}.Data([[1, 2], [3, 4]])
        >>> x = d.last_element()
        >>> print(x, type(x))
        4 <class 'int'>
        >>> d[-1, -1] = {{package}}.masked
        >>> y = d.last_element()
        >>> print(y, type(y))
        -- <class 'numpy.ma.core.MaskedConstant'>

        >>> d = {{package}}.Data(['foo', 'bar'])
        >>> x = d.last_element()
        >>> print(x, type(x))
        bar <class 'str'>

        """
        try:
            return self._get_cached_elements()[-1]
        except KeyError:
            item = self._item((slice(-1, None, 1),) * self.ndim)
            self._set_cached_elements({-1: item})
            return self._get_cached_elements()[-1]

    @_inplace_enabled(default=False)
    def masked_values(self, value, rtol=None, atol=None, inplace=False):
        """Mask using floating point equality.

        Masks the data where elements are approximately equal to the
        given value. For integer types, exact equality is used.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `mask`, `masked_where`

        :Parameters:

            value: number
                Masking value.

            {{rtol: number, optional}}

            {{atol: number, optional}}

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The result of masking the data where approximately
                equal to *value*, or `None` if the operation was
                in-place.

        **Examples**

        >>> d = {{package}}.Data([1, 1.1, 2, 1.1, 3])
        >>> e = d.masked_values(1.1)
        >>> print(e.array)
        [1.0 -- 2.0 -- 3.0]

        """
        d = _inplace_enabled_define_and_cleanup(self)

        if rtol is None:
            rtol = self._rtol
        else:
            rtol = float(rtol)

        if atol is None:
            atol = self._atol
        else:
            atol = float(atol)

        dx = d.to_dask_array(_force_mask_hardness=True, _force_to_memory=True)
        dx = da.ma.masked_values(dx, value, rtol=rtol, atol=atol)
        d._set_dask(dx, clear=self._ALL, in_memory=True)

        return d

    @_inplace_enabled(default=False)
    def masked_where(self, condition, inplace=False):
        """Mask the data where a condition is met.

        **Performance**

        `masked_where` causes all delayed operations to be executed.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `mask`, `masked_values`

        :Parameters:

            condition: array_like
                The masking condition. The data is masked where
                *condition* is True. Any masked values already in the
                data are also masked in the result.

            {{inplace: `bool`, optional}}

        :Returns:

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The result of masking the data, or `None` if the
                operation was in-place.

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3, 4, 5])
        >>> e = d.masked_where([0, 1, 0, 1, 0])
        >>> print(e.array)
        [1 -- 3 -- 5]

        """
        d = _inplace_enabled_define_and_cleanup(self)

        array = cfdm_where(d.array, condition, masked, None, d.hardmask)
        dx = da.from_array(array, chunks=d.chunks)
        d._set_dask(dx, clear=self._ALL, in_memory=True)

        # Update the deterministic status
        d._update_deterministic(condition)

        # Update the deterministic status
        d._update_deterministic(condition)

        return d

    @_inplace_enabled(default=False)
    def max(
        self,
        axes=None,
        squeeze=False,
        split_every=None,
        inplace=False,
    ):
        """Calculate maximum values.

        Calculates the maximum value or the maximum values along axes.

        See
        https://ncas-cms.github.io/cf-python/analysis.html#collapse-methods
        for mathematical definitions.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `min`, `sum`

        :Parameters:

            {{collapse axes: (sequence of) `int`, optional}}

            {{collapse squeeze: `bool`, optional}}

            {{split_every: `int` or `dict`, optional}}

                .. versionadded:: (cfdm) 1.11.2.0

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The collapsed data, or `None` if the operation was
                in-place.

        **Examples**

        >>> a = np.ma.arange(12).reshape(4, 3)
        >>> d = {{package}}.Data(a, 'K')
        >>> d[1, 1] = {{package}}.masked
        >>> print(d.array)
        [[0 1 2]
         [3 -- 5]
         [6 7 8]
         [9 10 11]]
        >>> d.max()
        <{{repr}}Data(1, 1): [[11]] K>

        """
        d = _inplace_enabled_define_and_cleanup(self)
        d = collapse(
            da.max,
            d,
            axis=axes,
            keepdims=not squeeze,
            split_every=split_every,
        )
        return d

    @_inplace_enabled(default=False)
    def min(self, axes=None, squeeze=False, split_every=None, inplace=False):
        """Calculate minimum values.

        Calculates the minimum value or the minimum values along axes.

        See
        https://ncas-cms.github.io/cf-python/analysis.html#collapse-methods
        for mathematical definitions.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `max`, `sum`

        :Parameters:

            {{collapse axes: (sequence of) `int`, optional}}

            {{collapse squeeze: `bool`, optional}}

            {{split_every: `int` or `dict`, optional}}

                .. versionadded:: (cfdm) 1.11.2.0

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The collapsed data, or `None` if the operation was
                in-place.

        **Examples**

        >>> a = np.ma.arange(12).reshape(4, 3)
        >>> d = {{package}}.Data(a, 'K')
        >>> d[1, 1] = {{package}}.masked
        >>> print(d.array)
        [[0 1 2]
         [3 -- 5]
         [6 7 8]
         [9 10 11]]
        >>> d.min()
        <{{repr}}Data(1, 1): [[0]] K>

        """
        d = _inplace_enabled_define_and_cleanup(self)
        d = collapse(
            da.min,
            d,
            axis=axes,
            keepdims=not squeeze,
            split_every=split_every,
        )
        return d

    @classmethod
    def ones(cls, shape, dtype=None, units=None, calendar=None, chunks="auto"):
        """Returns a new array filled with ones of set shape and type.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `empty`, `full`, `zeros`

        :Parameters:

            shape: `int` or `tuple` of `int`
                The shape of the new array. e.g. ``(2, 3)`` or ``2``.

            dtype: data-type
                The desired data-type for the array, e.g.
                `numpy.int8`. The default is `numpy.float64`.

            units: `str` or `Units`
                The units for the new data array.

            calendar: `str`, optional
                The calendar for reference time units.

            {{chunks: `int`, `tuple`, `dict` or `str`, optional}}

        :Returns:

            `Data`
                Array of ones with the given shape and data type.

        **Examples**

        >>> d = {{package}}.Data.ones((2, 3))
        >>> print(d.array)
        [[1. 1. 1.]
         [1. 1. 1.]]

        >>> d = {{package}}.Data.ones((2,), dtype=bool)
        >>> print(d.array)
        [ True  True]

        """
        dx = da.ones(shape, dtype=dtype, chunks=chunks)
        return cls(dx, units=units, calendar=calendar)

    @_inplace_enabled(default=False)
    def pad_missing(self, axis, pad_width=None, to_size=None, inplace=False):
        """Pad an axis with missing data.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            axis: `int`
                Select the axis for which the padding is to be
                applied.

                *Parameter example:*
                  Pad second axis: ``axis=1``.

                *Parameter example:*
                  Pad the last axis: ``axis=-1``.

            {{pad_width: sequence of `int`, optional}}

            {{to_size: `int`, optional}}

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The padded data, or `None` if the operation was
                in-place.

        **Examples**

        >>> d = {{package}}.Data(np.arange(6).reshape(2, 3))
        >>> print(d.array)
        [[0 1 2]
         [3 4 5]]
        >>> e = d.pad_missing(1, (1, 2))
        >>> print(e.array)
        [[-- 0 1 2 -- --]
         [-- 3 4 5 -- --]]
        >>> f = e.pad_missing(0, (0, 1))
        >>> print(f.array)
        [[--  0  1  2 -- --]
         [--  3  4  5 -- --]
         [-- -- -- -- -- --]]

        >>> g = d.pad_missing(1, to_size=5)
        >>> print(g.array)
        [[0 1 2 -- --]
         [3 4 5 -- --]]

        """
        if not 0 <= axis < self.ndim:
            raise ValueError(
                f"'axis' must be a valid dimension position. Got {axis}"
            )

        if to_size is not None:
            # Set pad_width from to_size
            if pad_width is not None:
                raise ValueError("Can't set both 'pad_width' and 'to_size'")

            pad_width = (0, to_size - self.shape[axis])
        elif pad_width is None:
            raise ValueError("Must set either 'pad_width' or 'to_size'")

        pad_width = np.asarray(pad_width)
        if pad_width.shape != (2,) or not pad_width.dtype.kind == "i":
            raise ValueError(
                "'pad_width' must be a sequence of two integers. "
                f"Got: {pad_width}"
            )

        pad_width = tuple(pad_width)
        if any(n < 0 for n in pad_width):
            if to_size is not None:
                raise ValueError(
                    f"'to_size' ({to_size}) must not be smaller than the "
                    f"original axis size ({self.shape[axis]})"
                )

            raise ValueError(
                f"Can't set a negative number of pad values. Got: {pad_width}"
            )

        d = _inplace_enabled_define_and_cleanup(self)

        dx = d.to_dask_array(_force_mask_hardness=True, _force_to_memory=True)
        mask0 = da.ma.getmaskarray(dx)

        pad = [(0, 0)] * dx.ndim
        pad[axis] = pad_width

        # Pad the data with zero. This will lose the original mask.
        dx = da.pad(dx, pad, mode="constant", constant_values=0)

        # Pad the mask with True
        mask = da.pad(mask0, pad, mode="constant", constant_values=True)

        # Set the mask
        dx = da.ma.masked_where(mask, dx)

        d._set_dask(dx, in_memory=True)
        return d

    @_inplace_enabled(default=False)
    def persist(self, inplace=False):
        """Persist data into memory.

        {{persist description}}

        Compare with `compute` and `array`.

        **Performance**

        `persist` causes delayed operations to be computed.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `compute`, `array`, `datetime_array`,
                     `dask.array.Array.persist`

        :Parameters:

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The persisted data. If the operation was in-place then
                `None` is returned.

        **Examples**

        >>> e = d.persist()

        """
        d = _inplace_enabled_define_and_cleanup(self)
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=True
        )
        dx = dx.persist()
        d._set_dask(
            dx, clear=self._ALL ^ self._ARRAY ^ self._CACHE, in_memory=True
        )
        return d

    @_inplace_enabled(default=False)
    def rechunk(
        self,
        chunks="auto",
        threshold=None,
        block_size_limit=None,
        balance=False,
        inplace=False,
    ):
        """Change the chunk structure of the data.

        **Performance**

        Rechunking can sometimes be expensive and incur a lot of
        communication overheads.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `chunks`, `chunksize`, `dask.array.rechunk`

        :Parameters:

            {{chunks: `int`, `tuple`, `dict` or `str`, optional}}

            {{threshold: `int`, optional}}

            {{block_size_limit: `int`, optional}}

            {{balance: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The rechunked data, or `None` if the operation was
                in-place.

        **Examples**

        >>> x = {{package}}.Data.empty((1000, 1000), chunks=(100, 100))

        Specify uniform chunk sizes with a tuple

        >>> y = x.rechunk((1000, 10))

        Or chunk only specific dimensions with a dictionary

        >>> y = x.rechunk({0: 1000})

        Use the value ``-1`` to specify that you want a single chunk
        along a dimension or the value ``'auto'`` to specify that dask
        can freely rechunk a dimension to attain blocks of a uniform
        block size.

        >>> y = x.rechunk({0: -1, 1: 'auto'}, block_size_limit=1e8)

        If a chunk size does not divide the dimension then rechunk
        will leave any unevenness to the last chunk.

        >>> x.rechunk(chunks=(400, -1)).chunks
        ((400, 400, 200), (1000,))

        However if you want more balanced chunks, and don't mind
        `dask` choosing a different chunksize for you then you can use
        the ``balance=True`` option.

        >>> x.rechunk(chunks=(400, -1), balance=True).chunks
        ((500, 500), (1000,))

        """
        d = _inplace_enabled_define_and_cleanup(self)

        dx = d.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        dx = dx.rechunk(chunks, threshold, block_size_limit, balance)
        d._set_dask(
            dx,
            clear=self._ALL ^ self._ARRAY ^ self._CACHE ^ self._CFA,
            in_memory=None,
        )

        return d

    def replace_directory(
        self,
        old=None,
        new=None,
        normalise=False,
        common=False,
    ):
        """Replace file directories in-place.

        Modifies the names of files that are required to deliver
        the computed data array.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `file_directories`, `get_filenames`

        :Parameters:

            {{replace old: `str` or `None`, optional}}

            {{replace new: `str` or `None`, optional}}

            {{replace normalise: `bool`, optional}}

            common: `bool`, optional
                If True the base directory structure that is common to
                all files with *new*.

        :Returns:

            `None`

        **Examples**

        >>> d.get_filenames()
        {'/data/file1.nc', '/home/file2.nc'}
        >>> d.replace_directory('/data', '/new/data/path/')
        >>> d.get_filenames()
        {'/new/data/path/file1.nc', '/home/file2.nc'}
        >>> d.replace_directory('/new/data, '/archive/location')
        >>> d.get_filenames()
        {'/archive/location/path/file1.nc', '/home/file2.nc'}
        >>> d.replace_directory('/home')
        >>> d.get_filenames()
        {'/archive/location/path/file1.nc', 'file2.nc'}

        """
        if not old and not new and not normalise and not common:
            return

        if common:
            if old is not None:
                raise ValueError(
                    "When 'common' is True, 'old' must be None "
                    "(because 'old' is going to be determined "
                    "automatically)"
                )

            old = commonprefix(
                tuple(self.file_directories(normalise=normalise))
            )

        self._modify_dask_graph(
            "replace_directory",
            (),
            {"old": old, "new": new, "normalise": normalise},
        )

    def replace_filenames(self, filenames):
        """Replace file locations in-place.

        A fragment is a part of the data array that is stored in a
        file.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `get_filenames`

        :Parameters:

             filenames: array_like
                 The replacement file names. It must either have the
                 same shape as the Dask chunks (as returned by the
                 `numblocks` attribute), or may also include an extra
                 trailing dimension for different file location
                 versions. Any output from the `get_filenames` method
                 with ``per_chunk=True`` is guaranteed to have an
                 acceptable shape.

        :Returns:

            `None`

        """
        filenames = np.ma.filled(filenames, "")
        if self.numblocks != filenames.shape:
            raise ValueError(
                f"'filenames' shape {filenames.shape} must be the same "
                f"as the Dask chunks shape {self.numblocks}"
            )

        dsk = self.todict(_force_mask_hardness=False, _force_to_memory=False)

        updated_keys = {}
        for index, position in zip(
            self.chunk_indices(), self.chunk_positions()
        ):
            filename = filenames[position]
            if not filename:
                # Don't replace the filename(s) for this chunk
                continue

            chunk_updated = False
            for key, a in (
                self[index]
                .todict(_force_mask_hardness=False, _force_to_memory=False)
                .items()
            ):
                try:
                    dsk[key] = a.replace_filename(filename)
                except AttributeError:
                    pass
                else:
                    if chunk_updated:
                        raise ValueError(
                            f"The Dask chunk in position {position} "
                            f"(defined by data index {index!r}) references multiple "
                            "file locations"
                        )

                    if key in updated_keys:
                        raise ValueError(
                            f"The Dask chunk in position {position} "
                            f"(defined by data index {index!r}) references a file "
                            "location that has already been replaced within "
                            "the Dask chunk in position "
                            f"{updated_keys[key][0]!r} (defined by "
                            f"{updated_keys[key][1]!r})"
                        )

                    chunk_updated = True
                    updated_keys[key] = (position, index)

        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        dx = da.Array(dsk, dx.name, dx.chunks, dx.dtype, dx._meta)
        self._set_dask(dx, clear=self._NONE, in_memory=None)

        # Update the deterministic status
        self._update_deterministic(False)

    @_inplace_enabled(default=False)
    def reshape(self, *shape, merge_chunks=True, limit=None, inplace=False):
        """Change the shape of the data without changing its values.

        It assumes that the array is stored in row-major order, and
        only allows for reshapings that collapse or merge dimensions
        like ``(1, 2, 3, 4) -> (1, 6, 4)`` or ``(64,) -> (4, 4, 4)``.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            shape: `tuple` of `int`, or any number of `int`
                The new shape for the data, which should be compatible
                with the original shape. If an integer, then the
                result will be a 1-d array of that length. One shape
                dimension can be -1, in which case the value is
                inferred from the length of the array and remaining
                dimensions.

            merge_chunks: `bool`
                When True (the default) merge chunks using the logic
                in `dask.array.rechunk` when communication is
                necessary given the input array chunking and the
                output shape. When False, the input array will be
                rechunked to a chunksize of 1, which can create very
                many tasks. See `dask.array.reshape` for details.

            limit: int, optional
                The maximum block size to target in bytes. If no limit
                is provided, it defaults to a size in bytes defined by
                the `{{package}}.chunksize` function.

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                 The reshaped data, or `None` if the operation was
                 in-place.

        **Examples**

        >>> d = {{package}}.Data(np.arange(12))
        >>> print(d.array)
        [ 0  1  2  3  4  5  6  7  8  9 10 11]
        >>> print(d.reshape(3, 4).array)
        [[ 0  1  2  3]
         [ 4  5  6  7]
         [ 8  9 10 11]]
        >>> print(d.reshape((4, 3)).array)
        [[ 0  1  2]
         [ 3  4  5]
         [ 6  7  8]
         [ 9 10 11]]
        >>> print(d.reshape(-1, 6).array)
        [[ 0  1  2  3  4  5]
         [ 6  7  8  9 10 11]]
        >>>  print(d.reshape(1, 1, 2, 6).array)
        [[[[ 0  1  2  3  4  5]
           [ 6  7  8  9 10 11]]]]
        >>> print(d.reshape(1, 1, -1).array)
        [[[[ 0  1  2  3  4  5  6  7  8  9 10 11]]]]

        """
        d = _inplace_enabled_define_and_cleanup(self)

        original_shape = self.shape
        original_ndim = len(original_shape)

        dx = d.to_dask_array(_force_mask_hardness=False)
        dx = dx.reshape(*shape, merge_chunks=merge_chunks, limit=limit)
        d._set_dask(dx, in_memory=True)

        # Set axis names for the reshaped data
        if dx.ndim != original_ndim:
            d._axes = generate_axis_identifiers(dx.ndim)

        # Update the dataset chunking strategy
        if (
            isinstance(d.nc_dataset_chunksizes(), tuple)
            and d.shape != original_shape
        ):
            d.nc_clear_dataset_chunksizes()

        return d

    def second_element(self):
        """Return the second element of the data as a scalar.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `first_element`, `last_element`

        **Performance**

        If possible, a cached value is returned. Otherwise the delayed
        operations needed to compute the element are executed, and
        cached for subsequent calls.

        :Returns:

                The second element of the data.

        **Examples**

        >>> d = {{package}}.Data([[1, 2], [3, 4]])
        >>> x = d.second_element()
        >>> print(x, type(x))
        2 <class 'int'>
        >>> d[0, 1] = {{package}}.masked
        >>> y = d.second_element()
        >>> print(y, type(y))
        -- <class 'numpy.ma.core.MaskedConstant'>

        >>> d = {{package}}.Data(['foo', 'bar'])
        >>> x = d.second_element()
        >>> print(x, type(x))
        bar <class 'str'>

        """
        try:
            return self._get_cached_elements()[1]
        except KeyError:
            item = self._item(np.unravel_index(1, self.shape))
            self._set_cached_elements({1: item})
            return self._get_cached_elements()[1]

    def set_calendar(self, calendar):
        """Set the calendar.

        .. seealso:: `override_calendar`, `override_units`,
                     `del_calendar`, `get_calendar`

        :Parameters:

            value: `str`
                The new calendar.

        :Returns:

            `None`

        **Examples**

        >>> d.set_calendar('none')
        >>> d.get_calendar
        'none'
        >>> d.del_calendar()
        >>> d.get_calendar()
        ValueError: Can't get non-existent calendar
        >>> print(d.get_calendar(None))
        None

        """
        self.Units = self._Units_class(self.get_units(default=None), calendar)

    def set_units(self, value):
        """Set the units.

        .. seealso:: `override_units`, `del_units`, `get_units`,
                     `has_units`, `Units`

        :Parameters:

            value: `str`
                The new units.

        :Returns:

            `None`

        **Examples**

        >>> d.set_units('watt')
        >>> d.get_units()
        'watt'
        >>> d.del_units()
        >>> d.get_units()
        ValueError: Can't get non-existent units
        >>> print(d.get_units(None))
        None

        """
        self.Units = self._Units_class(value, self.get_calendar(default=None))

    def soften_mask(self):
        """Force the mask to soft.

        Whether the mask of a masked array is hard or soft is
        determined by its `hardmask` property. `soften_mask` sets
        `hardmask` to `False`.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `hardmask`, `harden_mask`

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3])
        >>> d.hardmask
        True
        >>> d.soften_mask()
        >>> d.hardmask
        False

        >>> d = {{package}}.Data([1, 2, 3], mask=[False, True, False], hardmask=False)
        >>> d.hardmask
        False
        >>> d[1] = 999
        >>> print(d.array)
        [  1 999   3]

        """
        dx = self.to_dask_array(
            _force_mask_hardness=False, _force_to_memory=False
        )
        dx = dx.map_blocks(cfdm_soften_mask, dtype=dx.dtype)
        self._set_dask(dx, clear=self._NONE, in_memory=True)
        self.hardmask = False

    @_inplace_enabled(default=False)
    def squeeze(self, axes=None, inplace=False):
        """Remove size 1 axes from the data array.

        By default all size 1 axes are removed, but particular axes
        may be selected with the keyword arguments.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `flatten`, `insert_dimension`, `transpose`

        :Parameters:

            axes: (sequence of) `int`, optional
                Select the axes. By default all size 1 axes are
                removed. Each axis is identified by its positive or
                negative integer position. No axes are removed if
                *axes* is an empty sequence.

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The squeezed data array.

        **Examples**

        >>> v.shape
        (1,)
        >>> v.squeeze()
        >>> v.shape
        ()

        >>> v.shape
        (1, 2, 1, 3, 1, 4, 1, 5, 1, 6, 1)
        >>> v.squeeze((0,))
        >>> v.shape
        (2, 1, 3, 1, 4, 1, 5, 1, 6, 1)
        >>> v.squeeze(1)
        >>> v.shape
        (2, 3, 1, 4, 1, 5, 1, 6, 1)
        >>> v.squeeze([2, 4])
        >>> v.shape
        (2, 3, 4, 5, 1, 6, 1)
        >>> v.squeeze([])
        >>> v.shape
        (2, 3, 4, 5, 1, 6, 1)
        >>> v.squeeze()
        >>> v.shape
        (2, 3, 4, 5, 6)

        """
        d = _inplace_enabled_define_and_cleanup(self)

        if not d.ndim:
            if axes or axes == 0:
                raise ValueError("Can't squeeze axes from scalar data")

            if inplace:
                d = None

            return d

        original_shape = self.shape

        if axes is None:
            iaxes = tuple([i for i, n in enumerate(original_shape) if n == 1])
        else:
            iaxes = d._parse_axes(axes)
            for i in iaxes:
                if original_shape[i] > 1:
                    raise ValueError(
                        f"Can't squeeze axis in position {i} from data with "
                        f"shape {original_shape}: Axis size is greater than 1"
                    )

        if not iaxes:
            # Short circuit for a null operation (to avoid adding a
            # null layer to the Dask graph).
            return d

        # Still here? Then the data array is not scalar and at least
        # one size 1 axis needs squeezing.
        dx = d.to_dask_array(_force_mask_hardness=False, _force_to_memory=True)
        dx = dx.squeeze(axis=iaxes)

        # Squeezing a dimension doesn't affect the cached elements
        d._set_dask(
            dx, clear=self._ALL ^ self._CACHE ^ self._CFA, in_memory=True
        )

        # Remove the squeezed axis names
        d._axes = [axis for i, axis in enumerate(d._axes) if i not in iaxes]

        # Update the dataset chunking strategy
        chunksizes = d.nc_dataset_chunksizes()
        if chunksizes and isinstance(chunksizes, tuple):
            chunksizes = [
                size for i, size in enumerate(chunksizes) if i not in iaxes
            ]
            d.nc_set_dataset_chunksizes(chunksizes)

        return d

    @_inplace_enabled(default=False)
    def sum(self, axes=None, squeeze=False, split_every=None, inplace=False):
        """Calculate sum values.

        Calculates the sum value or the sum values along axes.

        See
        https://ncas-cms.github.io/cf-python/analysis.html#collapse-methods
        for mathematical definitions.

        .. seealso:: `max`, `min`

        :Parameters:

            {{collapse axes: (sequence of) `int`, optional}}

            {{collapse squeeze: `bool`, optional}}

            {{split_every: `int` or `dict`, optional}}

                .. versionadded:: (cfdm) 1.11.2.0

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The collapsed data, or `None` if the operation was
                in-place.

        **Examples**

        >>> a = np.ma.arange(12).reshape(4, 3)
        >>> d = {{package}}.Data(a, 'K')
        >>> d[1, 1] = {{package}}.masked
        >>> print(d.array)
        [[0 1 2]
         [3 -- 5]
         [6 7 8]
         [9 10 11]]
        >>> d.sum()
        <{{repr}}Data(1, 1): [[62]] K>

        >>> w = np.linspace(1, 2, 3)
        >>> print(w)
        [1.  1.5 2. ]
        >>> d.sum(weights={{package}}.Data(w, 'm'))
        <{{repr}}Data(1, 1): [[97.0]] K>

        """
        d = _inplace_enabled_define_and_cleanup(self)
        d = collapse(
            da.sum,
            d,
            axis=axes,
            keepdims=not squeeze,
            split_every=split_every,
        )
        return d

    def to_dask_array(self, _force_mask_hardness=True, _force_to_memory=True):
        """Convert the data to a `dask` array.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            {{_force_mask_hardness: `bool`, optional}}

            {{_force_to_memory: `bool`, optional}}

        :Returns:

            `dask.array.Array`
                The dask array contained within the `Data`
                instance.

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3, 4], 'm')
        >>> dx = d.to_dask_array()
        >>> dx
        >>> dask.array<array, shape=(4,), dtype=int64, chunksize=(4,), chunktype=numpy.ndarray>
        >>> dask.array.asanyarray(d) is dx
        True

        >>> d.to_dask_array(_force_mask_hardness=True)
        dask.array<cfdm_harden_mask, shape=(4,), dtype=int64, chunksize=(4,), chunktype=numpy.ndarray>

        >>> d = {{package}}.Data([1, 2, 3, 4], 'm', hardmask=False)
        >>> d.to_dask_array(_force_mask_hardness=True)
        dask.array<cfdm_soften_mask, shape=(4,), dtype=int64, chunksize=(4,), chunktype=numpy.ndarray>

        """
        dx = self._get_component("dask", None)
        if dx is None:
            raise ValueError(f"{self.__class__.__name__} object has no data")

        if _force_mask_hardness:
            if self.hardmask:
                dx = dx.map_blocks(cfdm_harden_mask, dtype=dx.dtype)
            else:
                dx = dx.map_blocks(cfdm_soften_mask, dtype=dx.dtype)

            # Note: The mask hardness functions have their own calls
            #       to 'cfdm_to_memory', so we don't need to set
            #       another one.
        elif _force_to_memory and not self.__in_memory__:
            dx = dx.map_blocks(cfdm_to_memory, dtype=dx.dtype)

        return dx

    def todict(
        self,
        graph="cull",
        _force_mask_hardness=True,
        _force_to_memory=True,
        optimize_graph=None,
    ):
        """Return a dictionary of the dask graph key/value pairs.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `cull_graph`, `to_dask_array`

        :Parameters:

            graph: `str` or `None`
                Specify the treatment to apply to the graph (not
                in-place) before converting to a dictionary. Must be
                one of:

                * ``'cull'``

                  This is the default. Remove unnecessary tasks which
                  do not contribute to the computed result, equivalent
                  to applying `dask.optimization.cull` to the graph.

                * ``'optimise'``

                  Apply all possible graph optimisations. These will
                  include removal of unnecessary tasks (see ``'cull'``),
                  and is equivalent to applying `dask.optimize` to the
                  graph.

                * `None`

                  Do not apply any optimisations.

                .. versionadded:: (cfdm) 1.12.0.0

            {{_force_mask_hardness: `bool`, optional}}

            {{_force_to_memory: `bool`, optional}}

            optimize_graph: Deprecated at version 1.12.0.0
                Use the *graph* parameter instead. Note that
                ``graph='optimise'`` is equivalent to the deprecated
                ``optimize_graph=True``.

        :Returns:

            `dict`
                The dictionary of the dask graph's key/value pairs.

        **Examples**

        >>> d = {{package}}.Data([1, 2, 3, 4], chunks=2)
        >>> d.todict()
        {('array-58934a19a81f97038351581dea42e32f', 0): array([1, 2]),
         ('array-58934a19a81f97038351581dea42e32f', 1): array([3, 4]),
         ('cfdm_harden_mask-23375a35009f4d3ec84b767640370152',
          0): <Task ('cfdm_harden_mask-23375a35009f4d3ec84b767640370152', 0) cfdm_harden_mask(...)>,
         ('cfdm_harden_mask-23375a35009f4d3ec84b767640370152',
          1): <Task ('cfdm_harden_mask-23375a35009f4d3ec84b767640370152', 1) cfdm_harden_mask(...)>}

        >>> e = d[0]
        >>> e.todict(graph=None)
        {('array-58934a19a81f97038351581dea42e32f', 0): array([1, 2]),
         ('array-58934a19a81f97038351581dea42e32f', 1): array([3, 4]),
         ('getitem-4d1949dc1e18d336e215bc226cd7b109',
          0): <Task ('getitem-4d1949dc1e18d336e215bc226cd7b109', 0) getitem(...)>,
         ('cfdm_harden_mask-b57a3694b00d301421b9fc21db4cf24e',
          0): <Task ('cfdm_harden_mask-b57a3694b00d301421b9fc21db4cf24e', 0) cfdm_harden_mask(...)>}
        >>> e.todict(graph='cull')
        {('getitem-4d1949dc1e18d336e215bc226cd7b109',
          0): <Task ('getitem-4d1949dc1e18d336e215bc226cd7b109', 0) getitem(...)>,
         ('array-58934a19a81f97038351581dea42e32f', 0): array([1, 2]),
         ('cfdm_harden_mask-b57a3694b00d301421b9fc21db4cf24e',
          0): <Task ('cfdm_harden_mask-b57a3694b00d301421b9fc21db4cf24e', 0) cfdm_harden_mask(...)>}

        """
        # NOTE: The underlying Dask graph structure is liable to
        # change in the future, in which case this method could break
        # and need refactoring (e.g.
        # https://github.com/dask/dask/pull/11736#discussion_r1954752842).

        if optimize_graph is not None:
            _DEPRECATION_ERROR_KWARGS(
                self,
                "todict",
                {"optimize_graph": optimize_graph},
                message="Use keyword 'graph' instead.",
                version="1.12.0.0",
                removed_at="1.14.0",
            )  # pragma: no cover

        if graph == "cull":
            self.cull_graph()

        dx = self.to_dask_array(
            _force_mask_hardness=_force_mask_hardness,
            _force_to_memory=_force_to_memory,
        )

        optimise_graph = graph == "optimise"
        e = collections_to_expr((dx,), optimize_graph=optimise_graph)
        return e.dask

    def tolist(self):
        """Return the data as a scalar or (nested) list.

        Returns the data as an ``N``-levels deep nested list of Python
        scalars, where ``N`` is the number of data dimensions.

        If ``N`` is 0 then, since the depth of the nested list is 0,
        it will not be a list at all, but a simple Python scalar.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `array`, `datetime_array`

        :Returns:

            `list` or scalar
                The (nested) list of array elements, or a scalar if
                the data has 0 dimensions.

        **Examples**

        >>> d = {{package}}.Data(9)
        >>> d.tolist()
        9

        >>> d = {{package}}.Data([1, 2])
        >>> d.tolist()
        [1, 2]

        >>> d = {{package}}.Data(([[1, 2], [3, 4]]))
        >>> d.tolist()
        [[1, 2], [3, 4]]

        >>> d.equals({{package}}.Data(d.tolist()))
        True

        """
        return self.array.tolist()

    @_inplace_enabled(default=False)
    def transpose(self, axes=None, inplace=False):
        """Permute the axes of the data array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `flatten', `insert_dimension`, `squeeze`

        :Parameters:

            axes: (sequence of) `int`
                The new axis order of the data array. By default the
                order is reversed. Each axis of the new order is
                identified by its original positive or negative
                integer position.

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`

        **Examples**

        >>> d.shape
        (19, 73, 96)
        >>> d.transpose()
        >>> d.shape
        (96, 73, 19)
        >>> d.transpose([1, 0, 2])
        >>> d.shape
        (73, 96, 19)
        >>> d.transpose((-1, 0, 1))
        >>> d.shape
        (19, 73, 96)

        """
        d = _inplace_enabled_define_and_cleanup(self)

        ndim = d.ndim
        if axes is None:
            iaxes = tuple(range(ndim - 1, -1, -1))
        else:
            iaxes = d._parse_axes(axes)

        if iaxes == tuple(range(ndim)):
            # Short circuit for a null operation (to avoid adding a
            # null layer to the Dask graph).
            return d

        data_axes = d._axes
        d._axes = [data_axes[i] for i in iaxes]

        dx = d.to_dask_array(_force_mask_hardness=False, _force_to_memory=True)
        try:
            dx = da.transpose(dx, axes=iaxes)
        except ValueError:
            raise ValueError(
                f"Can't transpose: Axes don't match array: {axes}"
            )

        d._set_dask(dx, in_memory=True)

        # Update the dataset chunking strategy
        chunksizes = d.nc_dataset_chunksizes()
        if chunksizes and isinstance(chunksizes, tuple):
            chunksizes = [chunksizes[i] for i in iaxes]
            d.nc_set_dataset_chunksizes(chunksizes)

        return d

    @_inplace_enabled(default=False)
    def uncompress(self, inplace=False):
        """Uncompress the data.

        Only affects data that is compressed by convention, i.e.

          * Ragged arrays for discrete sampling geometries (DSG) and
            simple geometry cell definitions.

          * Compression by gathering.

          * Compression by coordinate subsampling.

        Data that is already uncompressed is returned
        unchanged. Whether the data is compressed or not does not
        alter its functionality nor external appearance, but may
        affect how the data are written to a dataset on disk.

        .. versionadded:: (cfdm) 1.7.3

        .. seealso:: `array`, `compressed_array`, `source`

        :Parameters:

            {{inplace: `bool`, optional}}

        :Returns:

            `Data` or `None`
                The uncompressed data, or `None` if the operation was
                in-place.

        **Examples**

        >>> d.get_compression_type()
        'ragged contiguous'
        >>> d.uncompress()
        >>> d.get_compression_type()
        ''

        """
        d = _inplace_enabled_define_and_cleanup(self)
        if d.get_compression_type():
            d._del_Array(None)

        return d

    @_inplace_enabled(default=False)
    def unique(self, inplace=False):
        """The unique elements of the data.

        Returns the sorted unique elements of the array.

        :Returns:

            `Data` or `None`
                The unique values in a 1-d array, or `None` if the
                operation was in-place.

        **Examples**

        >>> d = {{package}}.Data([[4, 2, 1], [1, 2, 3]], 'm')
        >>> print(d.array)
        [[4 2 1]
         [1 2 3]]
        >>> e = d.unique()
        >>> print(e.array)
        [1 2 3 4]
        >>> d[0, 0] = {{package}}.masked
        >>> print(d.array)
        [[-- 2 1]
         [1 2 3]]
        >>> e = d.unique()
        >>> print(e.array)
        [1 2 3 --]

        """
        d = _inplace_enabled_define_and_cleanup(self)

        original_shape = self.shape

        dx = d.to_dask_array(_force_mask_hardness=False, _force_to_memory=True)

        u = np.unique(dx.compute())
        dx = da.from_array(u, chunks="auto")
        d._set_dask(dx, in_memory=True)

        # Update the axis names
        d._axes = generate_axis_identifiers(dx.ndim)

        # Update the dataset chunking strategy
        if (
            isinstance(d.nc_dataset_chunksizes(), tuple)
            and d.shape != original_shape
        ):
            d.nc_clear_dataset_chunksizes()

        return d

    @classmethod
    def zeros(
        cls, shape, dtype=None, units=None, calendar=None, chunks="auto"
    ):
        """Returns a new array filled with zeros of set shape and type.

        .. versionadded:: (cfdm) 1.11.2.0

        .. seealso:: `empty`, `full`, `ones`

        :Parameters:

            shape: `int` or `tuple` of `int`
                The shape of the new array.

            dtype: data-type
                The data-type of the new array. By default the
                data-type is ``float``.

            units: `str` or `Units`
                The units for the new data array.

            calendar: `str`, optional
                The calendar for reference time units.

            {{chunks: `int`, `tuple`, `dict` or `str`, optional}}

        :Returns:

            `Data`
                Array of zeros with the given shape and data type.

        **Examples**

        >>> d = {{package}}.Data.zeros((2, 3))
        >>> print(d.array)
        [[0. 0. 0.]
         [0. 0. 0.]]

        >>> d = {{package}}.Data.zeros((2,), dtype=bool)
        >>> print(d.array)
        [False False]

        """
        dx = da.zeros(shape, dtype=dtype, chunks=chunks)
        return cls(dx, units=units, calendar=calendar)

    # ----------------------------------------------------------------
    # Aliases
    # ----------------------------------------------------------------
    @property
    def dtarray(self):
        """Alias for `datetime_array`"""
        return self.datetime_array
