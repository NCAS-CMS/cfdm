"""A data indexer that applies netCDF masking and unpacking.

Portions of this code were adapted from the `netCDF4` library, which
carries the MIT License:

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

import netCDF4
import numpy as np

_safecast = netCDF4.utils._safecast
_default_fillvals = netCDF4.default_fillvals

logger = logging.getLogger(__name__)


class NetCDFIndexer:
    """A data indexer that applies netCDF masking and unpacking.

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

    The relevant netCDF attributes that are considered:

      * For masking: ``missing_value``, ``valid_max``, ``valid_min``,
                     ``valid_range``, ``_FillValue``, ``_Unsigned``

      * For unpacking: ``add_offset``, ``scale_factor``, ``_Unsigned``

    .. versionadded:: (cfdm) NEXTVERSION

    **Examples**

    >>> import netCDF4
    >>> nc = netCDF4.Dataset('file.nc', 'r')
    >>> x = cfdm.NetCDFIndexer(nc.variables['x'])
    >>> x.shape
    (12, 64, 128)
    >>> print(x[0, 0:4, 0:3])
    [[236.5, 236.2, 236.0],
     [240.9, --   , 239.6],
     [243.4, 242.4, 241.3],
     [243.1, 241.7, 240.4]]

    >>> import h5netcdf
    >>> h5 = h5netcdf.File('file.nc', 'r')
    >>> x = cfdm.NetCDFIndexer(h5.variables['x'])
    >>> x.shape
    (12, 64, 128)
    >>> print(x[0, 0:4, 0:3])
    [[236.5, 236.2, 236.0],
     [240.9, --   , 239.6],
     [243.4, 242.4, 241.3],
     [243.1, 241.7, 240.4]]

    >>> import numpy as np
    >>> n = np.arange(7)
    >>> x = cfdm.NetCDFIndexer(n)
    >>> x.shape
    (9,)
    >>> print(x[...])
    [0 1 2 3 4 5 6]
    >>> x = cfdm.NetCDFIndexer(n, attributes={'_FillValue': 4})
    >>> print(x[...])
    [0 1 2 3 -- 5 6]
    >>> x = cfdm.NetCDFIndexer(n, mask=False, attributes={'_FillValue': 4})
    >>> print(x[...])
    [0 1 2 3 4 5 6]

    """

    def __init__(
        self,
        variable,
        mask=True,
        unpack=True,
        always_mask=False,
        attributes=None,
    ):
        """**Initialisation**

        :Parameters:

            variable: `netCDF4.Variable` or `h5netcdf.Variable` or `numpy.ndarray`
                The variable to be indexed. Any masking and unpacking
                that could be applied by applied by the *variable*
                itself is disabled, i.e. any masking and unpacking is
                always done by the `NetCDFIndexer` instance.

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
                determined netCDF conventions for the following
                attributes: ``add_offset``, ``scale_factor``, and
                ``_Unsigned``.

            always_mask: `bool`
                If False, the default, then an array returned by
                indexing which has no missing values is created as a
                regular numpy array. If True then an array returned by
                indexing is always a masked array, even if there are
                no missing values.

            attributes: `dict`, optional
                Provide the netCDF attributes of the *variable* as
                dictionary key/value pairs. If *attributes* is set
                then any netCDF attributes stored by *variable* itself
                are ignored. Only the attributes relevant to masking
                and unpacking are considered, and all other attributes
                are ignored.

        """
        self.variable = variable
        self.mask = mask
        self.unpack = unpack
        self.always_mask = always_mask
        self._attributes = attributes

    def __getitem__(self, index):
        """Return a subspace of the variable as a `numpy` array.

        v.__getitem__(index) <==> v[index]

        Indexing follows the rules defined by the variable.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        variable = self.variable
        unpack = self.unpack
        attributes = self.attributes()
        dtype = variable.dtype

        netCDF4_scale = False
        netCDF4_mask = False
        try:
            netCDF4_scale = variable.scale
        except AttributeError:
            pass
        else:
            netCDF4_mask = variable.mask
            # Prevent netCDF4 from doing any masking and unpacking
            variable.set_auto_maskandscale(False)

        # Index the variable
        data = variable[index]

        # Convert str, char, and object data to byte strings
        if isinstance(data, str):
            data = np.array(data, dtype="S")
        elif data.dtype.kind in "OSU":
            kind = data.dtype.kind
            if kind == "S":
                data = netCDF4.chartostring(data)

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

        if self.mask:
            data = self._mask(data, dtype, attributes, dtype_unsigned_int)

        if unpack:
            data = self._unpack(data, attributes)

        if data.dtype.kind == "S":
            data = data.astype("U", copy=False)

        # Reset a netCDF4 variables's scale and mask behaviour
        if netCDF4_scale:
            variable.set_auto_scale(True)

        if netCDF4_mask:
            variable.set_auto_mask(True)

        return data

    @property
    def shape(self):
        """Tuple of the data dimension sizes.

        .. versionadded:: (cfdm) NEXTVERSION

        """
        return self.variable.shape

    def _check_safecast(self, attname, dtype, attributes):
        """Check an attribute's data type.

        Checks to see that variable attribute exists and can be safely
        cast to variable data type.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameter:

            attname: `str`
                The attribute name.

            dtype: `numpy.dtype`
                The variable data type.

            attributes: `dict`
                The variable attributes.

        :Returns:

            `bool`, value
                Whether or not the attribute data type is consistent
                with the variable data type, and the attribute value.

        """
        if attname in attributes:
            attvalue = attributes[attname]
            att = np.array(attvalue)
        else:
            return False, None

        is_safe = True
        try:
            atta = np.array(att, dtype)
        except ValueError:
            is_safe = False
        else:
            is_safe = _safecast(att, atta)

        if not is_safe:
            logger.info(
                f"Mask attribute {attname!r} not used since it can't "
                f"be safely cast to variable data type {dtype!r}"
            )  # pragma: no cover

        return is_safe, attvalue

    def _default_FillValue(self, dtype):
        """Return the default ``_FillValue`` for the given data type.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `netCDF4.default_fillvals`

        :Parameter:

            dtype: `numpy.dtype`
                The variable's data type

        :Returns:

                The default ``_FillValue``.

        """
        if dtype.kind in "OS":
            return _default_fillvals["S1"]
        else:
            return _default_fillvals[dtype.str[1:]]

    def _mask(self, data, dtype, attributes, dtype_unsigned_int):
        """Mask the data.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameter:

            data: `numpy.ndarray`
                The unmasked and unpacked data indexed from the
                variable.

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
                mask = data < validmin
                if totalmask is None:
                    totalmask = mask
                else:
                    totalmask += mask

            if validmax is not None:
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
                data, mask=totalmask, fill_value=fill_value
            )
            if not data.ndim:
                # Return a scalar numpy masked constant not a 0-d
                # masked array, so that data == np.ma.masked.
                data = data[()]
        elif self.always_mask and not np.ma.isMA(data):
            # Return a masked array when there are no masked elements
            data = np.ma.masked_array(data)

        return data

    def _unpack(self, data, attributes):
        """Unpack the data..

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameter:

            data: `numpy.ndarray`
                The unmasked and unpacked data indexed from the
                variable.

            attributes: `dict`
                The variable attributes.

        :Returns:

            `nump.ndarray`
                The unpacked data.

        """
        scale_factor = attributes.get("scale_factor")
        add_offset = attributes.get("add_offset")
        try:
            if scale_factor is not None:
                float(scale_factor)
        except ValueError:
            logging.warn(
                "No unpacking done: 'scale_factor' attribute "
                f"{scale_factor!r} can't be converted to a float"
            )  # pragma: no cover
            return data

        try:
            if add_offset is not None:
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
                else:
                    data = data.astype(np.array(scale_factor).dtype)
            else:
                # scale_factor with no add_offset
                if scale_factor != 1.0:
                    data = data * scale_factor
                else:
                    data = data.astype(scale_factor.dtype)
        elif add_offset is not None:
            # add_offset with no scale_factor
            if add_offset != 0.0:
                data = data + add_offset
            else:
                data = data.astype(np.array(add_offset).dtype)

        return data

    def attributes(self):
        """Return the netCDF attributes of the variable.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `dict`
                The attributes.

        **Examples**

        >>> v.attributes()
        {'standard_name': 'air_temperature',
         'missing_value': -999.0}

        """
        if self._attributes is not None:
            return self._attributes.copy()

        variable = self.variable
        try:
            # h5netcdf
            return dict(variable.attrs)
        except AttributeError:
            try:
                # netCDF4
                return {
                    attr: variable.getncattr(attr)
                    for attr in variable.ncattrs()
                }
            except AttributeError:
                # numpy
                return {}
