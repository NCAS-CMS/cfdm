"""A data indexer that applies netCDF masking and unpacking.

Portions of this code were adapted from the `netCDF4` library, which
carries the following MIT License:

Copyright 2008 Jeffrey Whitaker

https://opensource.org/license/mit

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

"""
import logging
from math import prod
from numbers import Integral

import numpy as np
from dask.array.slicing import normalize_index
from netCDF4 import chartostring, default_fillvals
from netCDF4.utils import _safecast

logger = logging.getLogger(__name__)


class netcdf_indexer:
    """A data indexer that also applies netCDF masking and unpacking.

    Indexing is orthogonal, meaning that the index for each dimension
    is applied independently, regardless of how that index was
    defined. For instance, the indices ``[[0, 1], [1, 3], 0]`` and
    ``[:2, 1:4:2, 0]`` will give identical results. Note that this
    behaviour is different to that of `numpy`.

    During indexing, masking and unpacking is applied according to the
    netCDF conventions, either or both of which may be disabled via
    initialisation options.

    In addition, string and character variables are always converted
    to unicode arrays, the latter with the last dimension
    concatenated.

    Masking and unpacking operations are defined by the conventions
    for netCDF attributes, which are either provided as part of the
    input *data* object, or given with the input *attributes*
    parameter.

    The relevant netCDF attributes that are considered are:

      * For masking: ``missing_value``, ``valid_max``, ``valid_min``,
                     ``valid_range``, ``_FillValue``, and
                     ``_Unsigned``. Note that if ``_FillValue`` is not
                     present then the netCDF default value for the
                     appropriate data type will be assumed, as defined
                     by `netCDF4.default_fillvals`.

      * For unpacking: ``add_offset``, ``scale_factor``, and
                       ``_Unsigned``

    .. versionadded:: (cfdm) NEXTVERSION

    **Examples**

    >>> import netCDF4
    >>> nc = netCDF4.Dataset('file.nc', 'r')
    >>> x = cfdm.netcdf_indexer(nc.variables['x'])
    >>> x.shape
    (12, 64, 128)
    >>> print(x[0, 0:4, 0:3])
    [[236.5, 236.2, 236.0],
     [240.9, --   , 239.6],
     [243.4, 242.4, 241.3],
     [243.1, 241.7, 240.4]]

    >>> import h5netcdf
    >>> h5 = h5netcdf.File('file.nc', 'r')
    >>> x = cfdm.netcdf_indexer(h5.variables['x'])
    >>> x.shape
    (12, 64, 128)
    >>> print(x[0, 0:4, 0:3])
    [[236.5, 236.2, 236.0],
     [240.9, --   , 239.6],
     [243.4, 242.4, 241.3],
     [243.1, 241.7, 240.4]]

    >>> import numpy as np
    >>> n = np.arange(7)
    >>> x = cfdm.netcdf_indexer(n)
    >>> x.shape
    (9,)
    >>> print(x[...])
    [0 1 2 3 4 5 6]
    >>> x = cfdm.netcdf_indexer(n, attributes={'_FillValue': 4})
    >>> print(x[...])
    [0 1 2 3 -- 5 6]
    >>> x = cfdm.netcdf_indexer(n, mask=False, attributes={'_FillValue': 4})
    >>> print(x[...])
    [0 1 2 3 4 5 6]
    >>> x = cfdm.netcdf_indexer(n, mask=False, attributes={'_FillValue': 4})
    >>> print(x[...])
    [0 1 2 3 4 5 6]

    """

    def __init__(
        self,
        variable,
        mask=True,
        unpack=True,
        always_masked_array=False,
        attributes=None,
        copy=False,
    ):
        """**Initialisation**

        :Parameters:

            variable:
                The variable to be indexed. May be any variable that
                has the same API as one of `numpy.ndarray`,
                `netCDF4.Variable` or `h5py.Variable` (which includes
                `h5netcdf.Variable`). Any masking and unpacking that
                could be applied by *variable* itself (e.g. by a
                `netCDF4.Variable` instance) is disabled, ensuring
                that any masking and unpacking is always done by the
                `netcdf_indexer` instance.

            mask: `bool`
                If True, the default, then an array returned by
                indexing is automatically masked. Masking is
                determined by the netCDF conventions for the following
                attributes: ``_FillValue``, ``missing_value``,
                ``_Unsigned``, ``valid_max``, ``valid_min``, and
                ``valid_range``.

            unpack: `bool`
                If True, the default, then an array returned by
                indexing is automatically unpacked. Unpacking is
                determined by the netCDF conventions for the following
                attributes: ``add_offset``, ``scale_factor``, and
                ``_Unsigned``.

            always_masked_array: `bool`
                If False, the default, then an array returned by
                indexing which has no missing values is created as a
                regular `numpy` array. If True then an array returned
                by indexing is always a masked `numpy` array, even if
                there are no missing values.

            attributes: `dict`, optional
                Provide netCDF attributes for the *variable* as a
                dictionary key/value pairs. Only the attributes
                relevant to masking and unpacking are considered, with
                all other attributes being ignored. If *attributes* is
                `None`, the default, then the netCDF attributes stored
                by *variable* itself (if any) are used. If
                *attributes* is not `None`, then any netCDF attributes
                stored by *variable* itself are ignored.

        """
        self.variable = variable
        self.mask = bool(mask)
        self.unpack = bool(unpack)
        self.always_masked_array = bool(always_masked_array)
        self._attributes = attributes
        self._copy = copy

    def __getitem__(self, index):
        """Return a subspace of the variable as a `numpy` array.

        v.__getitem__(index) <==> v[index]

        Indexing is orthogonal, meaning that the index for each
        dimension is applied independently, regardless of how that
        index was defined. For instance, the indices ``[[0, 1], [1,
        3], 0]`` and ``[:2, 1:4:2, 0]`` will give identical
        results. Note that this behaviour is different to that of
        `numpy`.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        variable = self.variable
        unpack = self.unpack
        attributes = self.attributes()
        dtype = variable.dtype

        # Prevent a netCDF4 variable from doing its own masking and
        # unpacking during the indexing
        netCDF4_scale = False
        netCDF4_mask = False
        try:
            netCDF4_scale = variable.scale
        except AttributeError:
            # Not a netCDF4 variable
            pass
        else:
            netCDF4_mask = variable.mask
            variable.set_auto_maskandscale(False)

        # ------------------------------------------------------------
        # Index the variable
        # ------------------------------------------------------------
        data = self._index(index)

        # Reset a netCDF4 variable's scale and mask behaviour
        if netCDF4_scale:
            variable.set_auto_scale(True)

        if netCDF4_mask:
            variable.set_auto_mask(True)

        # Convert str, char, and object data to byte strings
        if isinstance(data, str):
            data = np.array(data, dtype="S")
        elif data.dtype.kind in "OSU":
            kind = data.dtype.kind
            if kind == "S":
                data = chartostring(data)

            # Assume that object arrays are arrays of strings
            data = data.astype("S", copy=False)
            if kind == "O":
                dtype = data.dtype

        if dtype is str:
            dtype = data.dtype

        dtype_unsigned_int = None
        if unpack:
            is_unsigned_int = attributes.get("_Unsigned") in ("true", "True")
            if is_unsigned_int:
                data_dtype = data.dtype
                dtype_unsigned_int = (
                    f"{data_dtype.byteorder}u{data_dtype.itemsize}"
                )
                data = data.view(dtype_unsigned_int)

        # ------------------------------------------------------------
        # Mask the data
        # ------------------------------------------------------------
        if self.mask:
            data = self._mask(data, dtype, attributes, dtype_unsigned_int)

        # ------------------------------------------------------------
        # Unpack the data
        # ------------------------------------------------------------
        if unpack:
            data = self._unpack(data, attributes)

        # Make sure all strings are unicode
        if data.dtype.kind == "S":
            data = data.astype("U", copy=False)

        # ------------------------------------------------------------
        # Copy the data
        # ------------------------------------------------------------
        if self._copy:
            data = data.copy()

        return data

    def __orthogonal_indexing__(self):
        """Flag to indicate that orthogonal indexing is supported.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return True

    def _check_safecast(self, attr, dtype, attributes):
        """Check an attribute's data type.

        Checks to see that variable attribute exists and can be safely
        cast to variable's data type.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameter:

            attr: `str`
                The name of the attribute.

            dtype: `numpy.dtype`
                The variable data type.

            attributes: `dict`
                The variable attributes.

        :Returns:

            `bool`, value
                Whether or not the attribute data type is consistent
                with the variable data type, and the attribute value.

        """
        if attr in attributes:
            attvalue = attributes[attr]
            att = np.array(attvalue)
        else:
            return False, None

        try:
            atta = np.array(att, dtype)
        except ValueError:
            safe = False
        else:
            safe = _safecast(att, atta)

        if not safe:
            logger.info(
                f"Mask attribute {attr!r} not used since it can't "
                f"be safely cast to variable data type {dtype!r}"
            )  # pragma: no cover

        return safe, attvalue

    def _default_FillValue(self, dtype):
        """Return the default ``_FillValue`` for the given data type.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `netCDF4.default_fillvals`

        :Parameter:

            dtype: `numpy.dtype`
                The data type.

        :Returns:

                The default ``_FillValue``.

        """
        if dtype.kind in "OS":
            return default_fillvals["S1"]

        return default_fillvals[dtype.str[1:]]

    def _index(self, index):
        """Get a subspace of the variable with orthogonal indexing.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `__getitem__`

        :Parameter:

            index:
                The indices that define the subspace.

        :Returns:

            `numpy.ndarray`
                The subspace of the variable.

        """
        variable = self.variable
        index = normalize_index(index, variable.shape)

        # Find the positions of any list/1-d array indices (which by
        # now will contain only integers)
        axes_with_list_indices = [
            n
            for n, i in enumerate(index)
            if isinstance(i, list) or getattr(i, "shape", False)
        ]

        # Create an index that replaces integer indices with size 1
        # slices, so that their axes are not dropped yet (they will be
        # dealt with later).
        index0 = [
            slice(i, i + 1) if isinstance(i, Integral) else i for i in index
        ]

        data = variable
        if len(axes_with_list_indices) <= 1 or getattr(
            variable, "__orthogonal_indexing__", False
        ):
            # There is at most one list/1-d array index, and/or the
            # variable natively supports orthogonal indexing.
            #
            # Note: `netCDF4.Variable` supports orthogonal indexing;
            #       but `numpy.ndarray`, `h5netcdf.File` and
            #       `h5py.File` do not.
            data = data[tuple(index0)]
        else:
            # There are two or more list/1-d array index, and the
            # variable does not natively support orthogonal indexing.
            #
            # Emulate orthogonal indexing with a sequence of
            # subspaces, one for each list/1-d array index.

            # 1) Apply the slice indices at the time as the list/1-d
            #    array index that gives the smallest result.

            # Create an index that replaces each list/1-d array with
            # slice(None)
            index1 = [
                i if isinstance(i, slice) else slice(None) for i in index0
            ]

            # Find the position of the list/1-d array index that gives
            # the smallest result.
            shape1 = self.index_shape(index1, data.shape)
            size1 = prod(shape1)
            sizes = [
                len(index[i]) * size1 // shape1[i]
                for i in axes_with_list_indices
            ]
            n = axes_with_list_indices.pop(np.argmin(sizes))

            # Apply the subspace of slices and the chosen list/1-d
            # array index
            index1[n] = index[n]
            data = data[tuple(index1)]

            # 2) Apply the rest of the list/1-d array indices, in the
            #    order that gives the smallest result after each step.
            ndim = variable.ndim
            while axes_with_list_indices:
                shape1 = data.shape
                size1 = data.size
                sizes = [
                    len(index[i]) * size1 // shape1[i]
                    for i in axes_with_list_indices
                ]
                n = axes_with_list_indices.pop(np.argmin(sizes))

                # Apply the subspace of for the chosen list/1-d array
                # index
                index2 = [slice(None)] * ndim
                index2[n] = index[n]
                data = data[tuple(index2)]

        # Apply any integer indices that will drop axes
        index3 = [0 if isinstance(i, Integral) else slice(None) for i in index]
        if index3:
            data = data[tuple(index3)]

        return data

    def _mask(self, data, dtype, attributes, dtype_unsigned_int):
        """Mask the data.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameter:

            data: `numpy.ndarray`
                The unmasked and (possibly) packed data.

            dtype: `numpy.dtype`
                The data type of the variable (which may be different
                to that of *data*).

            attributes: `dict`
                The variable attributes.

            dtype_unsigned_int: `dtype` or `None`
                The data type when the data have been cast to unsigned
                integers, otherwise `None`.

        :Returns:

            `nump.ndarray`
                The masked data.

        """
        # The Boolean mask accounting for all methods of specification
        totalmask = None
        # The fill value for the returned numpy array
        fill_value = None

        safe_missval, missing_value = self._check_safecast(
            "missing_value", dtype, attributes
        )
        if safe_missval:
            # --------------------------------------------------------
            # Create mask from missing_value
            # --------------------------------------------------------
            mval = np.array(missing_value, dtype)
            if dtype_unsigned_int is not None:
                mval = mval.view(dtype_unsigned_int)

            if not mval.ndim:
                mval = (mval,)

            for m in mval:
                try:
                    mvalisnan = np.isnan(m)
                except TypeError:
                    # isnan fails on some dtypes
                    mvalisnan = False

                if mvalisnan:
                    mask = np.isnan(data)
                else:
                    mask = data == m

                if mask.any():
                    if totalmask is None:
                        totalmask = mask
                    else:
                        totalmask += mask

            if totalmask is not None:
                fill_value = mval[0]

        # Set mask=True for data == fill value
        safe_fillval, _FillValue = self._check_safecast(
            "_FillValue", dtype, attributes
        )
        if not safe_fillval:
            _FillValue = self._default_FillValue(dtype)
            safe_fillval = True

        if safe_fillval:
            # --------------------------------------------------------
            # Create mask from _FillValue
            # --------------------------------------------------------
            fval = np.array(_FillValue, dtype)
            if dtype_unsigned_int is not None:
                fval = fval.view(dtype_unsigned_int)

            if fval.ndim == 1:
                # _FillValue must be a scalar
                fval = fval[0]

            try:
                fvalisnan = np.isnan(fval)
            except Exception:
                # isnan fails on some dtypes
                fvalisnan = False

            if fvalisnan:
                mask = np.isnan(data)
            else:
                mask = data == fval

            if mask.any():
                if fill_value is None:
                    fill_value = fval

                if totalmask is None:
                    totalmask = mask
                else:
                    totalmask += mask

        # Set mask=True for data outside [valid_min, valid_max]
        #
        # If valid_range exists use that, otherwise look for
        # valid_min, valid_max. No special treatment of byte data as
        # described in the netCDF documentation.
        validmin = None
        validmax = None
        safe_validrange, valid_range = self._check_safecast(
            "valid_range", dtype, attributes
        )
        safe_validmin, valid_min = self._check_safecast(
            "valid_min", dtype, attributes
        )
        safe_validmax, valid_max = self._check_safecast(
            "valid_max", dtype, attributes
        )
        if safe_validrange and valid_range.size == 2:
            validmin = np.array(valid_range[0], dtype)
            validmax = np.array(valid_range[1], dtype)
        else:
            if safe_validmin:
                validmin = np.array(valid_min, dtype)

            if safe_validmax:
                validmax = np.array(valid_max, dtype)

        if dtype_unsigned_int is not None:
            if validmin is not None:
                validmin = validmin.view(dtype_unsigned_int)

            if validmax is not None:
                validmax = validmax.view(dtype_unsigned_int)

        if dtype.kind != "S":
            # --------------------------------------------------------
            # Create mask from valid_min. valid_max, valid_range
            # --------------------------------------------------------
            # Don't set validmin/validmax mask for character data
            #
            # Setting valid_min/valid_max to the _FillVaue is too
            # surprising for many users (despite the netcdf docs
            # attribute best practices suggesting clients should do
            # this).
            if validmin is not None:
                if validmin.ndim == 1:
                    # valid min must be a scalar
                    validmin = validmin[0]

                mask = data < validmin
                if totalmask is None:
                    totalmask = mask
                else:
                    totalmask += mask

            if validmax is not None:
                if validmax.ndim == 1:
                    # valid max must be a scalar
                    validmax = validmax[0]

                mask = data > validmax
                if totalmask is None:
                    totalmask = mask
                else:
                    totalmask += mask

        # ------------------------------------------------------------
        # Mask the data
        # ------------------------------------------------------------
        if totalmask is not None and totalmask.any():
            data = np.ma.masked_array(
                data, mask=totalmask, fill_value=fill_value, copy=False
            )
            if not data.ndim:
                # Return a scalar numpy masked constant not a 0-d
                # masked array, so that data == np.ma.masked.
                data = data[()]
        elif np.ma.isMA(data):
            if not (self.always_masked_array or np.ma.is_masked(data)):
                # Return a non-masked array
                data = np.array(data, copy=False)
        elif self.always_masked_array:
            # Return a masked array
            data = np.ma.masked_array(data, copy=False)

        return data

    def _unpack(self, data, attributes):
        """Unpack the data.

        If both the ``add_offset`` and ``scale_factor`` attributes
        have not been set then no unpacking is done and the data is
        returned unchanged.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameter:

            data: `numpy.ndarray`
                The masked and (possibly) packed data.

            attributes: `dict`
                The variable attributes.

        :Returns:

            `numpy.ndarray`
                The unpacked data.

        """
        scale_factor = attributes.get("scale_factor")
        add_offset = attributes.get("add_offset")

        try:
            if scale_factor is not None:
                scale_factor = np.array(scale_factor)
                if scale_factor.ndim == 1:
                    # scale_factor must be a scalar
                    scale_factor = scale_factor[0]

                float(scale_factor)
        except ValueError:
            logging.warn(
                "No unpacking done: 'scale_factor' attribute "
                f"{scale_factor!r} can't be converted to a float"
            )  # pragma: no cover
            return data

        try:
            if add_offset is not None:
                add_offset = np.array(add_offset)
                if add_offset.ndim == 1:
                    # add_offset must be a scalar
                    add_offset = add_offset[0]

                float(add_offset)
        except ValueError:
            logging.warn(
                "No unpacking done: 'add_offset' attribute "
                f"{add_offset!r} can't be converted to a float"
            )  # pragma: no cover
            return data

        if scale_factor is not None:
            if add_offset is not None:
                # scale_factor and add_offset
                if add_offset != 0.0 or scale_factor != 1.0:
                    data = data * scale_factor + add_offset
                    self._copy = False
                else:
                    data = data.astype(np.array(scale_factor).dtype)
            else:
                # scale_factor with no add_offset
                if scale_factor != 1.0:
                    data = data * scale_factor
                    self._copy = False
                else:
                    data = data.astype(scale_factor.dtype)
        elif add_offset is not None:
            # add_offset with no scale_factor
            if add_offset != 0.0:
                data = data + add_offset
                self._copy = False
            else:
                data = data.astype(np.array(add_offset).dtype)

        return data

    @property
    def dtype(self):
        """The data type of the array elements.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return self.variable.dtype

    @property
    def ndim(self):
        """Number of dimensions in the data array.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return self.variable.ndim

    @property
    def shape(self):
        """Tuple of the data dimension sizes.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return self.variable.shape

    @property
    def size(self):
        """Number of elements in the data array.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return self.variable.size

    def attributes(self):
        """Return the netCDF attributes for the data.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `dict`
                The attributes.

        **Examples**

        >>> v.attributes()
        {'standard_name': 'air_temperature',
         'missing_value': -999.0}

        """
        _attributes = self._attributes
        if _attributes is not None:
            return _attributes.copy()

        variable = self.variable
        try:
            # h5py API
            attrs = dict(variable.attrs)
        except AttributeError:
            try:
                # netCDF4 API
                attrs = {
                    attr: variable.getncattr(attr)
                    for attr in variable.ncattrs()
                }
            except AttributeError:
                # numpy API
                attrs = {}

        self._attributes = attrs
        return attrs

    @classmethod
    def index_shape(cls, index, shape):
        """Return the shape of the array subspace implied by indices.

        .. versionadded:: (cfdm) NEXTRELEASE

        :Parameters:

            indices: `tuple`
                The indices to be applied to an array with shape
                *shape*.

            shape: sequence of `ints`
                The shape of the array to be subspaced.

        :Returns:

            `list`
                The shape of the subspace defined by the *indices*.

        **Examples**

        >>> import numpy as np
        >>> n.indices_shape((slice(2, 5), 4), (10, 20))
        [3, 1]
        >>> n.indices_shape(([2, 3, 4], np.arange(1, 6)), (10, 20))
        [3, 5]

        >>> n.indices_shape((slice(None), [True, False, True]), (10, 3))
        [10, 2]

        >>> index0 = np.arange(5)
        >>> index0 = index0[index0 < 3]
        >>> n.indices_shape((index0, []), (10, 20))
        [3, 0]

        >>> n.indices_shape((slice(1, 5, 3), 3), (10, 20))
        [2, 1]
        >>> n.indices_shape((slice(5, 1, -2), 3), (10, 20))
        [2, 1]
        >>> n.indices_shape((slice(5, 1, 3), 3), (10, 20))
        [0, 1]
        >>> n.indices_shape((slice(1, 5, -3), 3), (10, 20))
        [0, 1]

        """
        implied_shape = []
        for ind, full_size in zip(index, shape):
            if isinstance(ind, slice):
                start, stop, step = ind.indices(full_size)
                if (stop - start) * step < 0:
                    # E.g. 5:1:3 or 1:5:-3
                    size = 0
                else:
                    size = abs((stop - start) / step)
                    int_size = round(size)
                    if size > int_size:
                        size = int_size + 1
                    else:
                        size = int_size
            elif isinstance(ind, np.ndarray):
                if ind.dtype == bool:
                    # Size is the number of True values in the array
                    size = int(ind.sum())
                else:
                    size = ind.size

                if not ind.ndim:
                    # Scalar array
                    continue
            elif isinstance(ind, list):
                if not ind:
                    size = 0
                else:
                    i = ind[0]
                    if isinstance(i, bool):
                        # List of bool: Size is the number of True
                        # values in the list
                        size = sum(ind)
                    else:
                        # List of int
                        size = len(ind)
            else:
                # Index is Integral
                continue

            implied_shape.append(size)

        return implied_shape
