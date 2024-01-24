import logging

import h5netcdf
import netCDF4
import numpy as np

from . import abstract
from .mixin import FileArrayMixin, NetCDFFileMixin

_safecast = netCDF4.utils._safecast
default_fillvals = netCDF4.default_fillvals

logger = logging.getLogger(__name__)


class HDFArray(NetCDFFileMixin, FileArrayMixin, abstract.Array):
    """An underlying array stored in an HDF file.

    .. versionadded:: (cfdm) TODOHDF

    """

    def __init__(
        self,
        filename=None,
        address=None,
        dtype=None,
        shape=None,
        mask=True,
        units=False,
        calendar=False,
        missing_values=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            filename: (sequence of) `str`, optional
                The name of the file(s) containing the array.

            address: (sequence of) `str`, optional
                The identity of the variable in each file defined by
                *filename*. Must be a netCDF variable name.

            dtype: `numpy.dtype`
                The data type of the array in the file. May be `None`
                if the numpy data-type is not known (which can be the
                case for string types, for example).

            shape: `tuple`
                The array dimension sizes in the file.

            size: `int`
                Number of elements in the array in the file.

            ndim: `int`
                The number of array dimensions in the file.

            mask: `bool`
                If True (the default) then mask by convention when
                reading data from disk.

                A netCDF array is masked depending on the values of any of
                the netCDF variable attributes ``valid_min``,
                ``valid_max``, ``valid_range``, ``_FillValue`` and
                ``missing_value``.

            units: `str` or `None`, optional
                The units of the variable. Set to `None` to indicate
                that there are no units. If unset then the units will
                be set during the first `__getitem__` call.

            calendar: `str` or `None`, optional
                The calendar of the variable. By default, or if set to
                `None`, then the CF default calendar is assumed, if
                applicable. If unset then the calendar will be set
                during the first `__getitem__` call.

            missing_values: `dict`, optional
                The missing value indicators defined by the variable
                attributes. See `get_missing_values` for details.

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(source=source, copy=copy)

        if source is not None:
            try:
                shape = source._get_component("shape", None)
            except AttributeError:
                shape = None

            try:
                filename = source._get_component("filename", None)
            except AttributeError:
                filename = None

            try:
                address = source._get_component("address", None)
            except AttributeError:
                address = None

            try:
                dtype = source._get_component("dtype", None)
            except AttributeError:
                dtype = None

            try:
                mask = source._get_component("mask", True)
            except AttributeError:
                mask = True

            try:
                units = source._get_component("units", False)
            except AttributeError:
                units = False

            try:
                calendar = source._get_component("calendar", False)
            except AttributeError:
                calendar = False

            try:
                missing_values = source._get_component("missing_values", None)
            except AttributeError:
                missing_values = None

        if shape is not None:
            self._set_component("shape", shape, copy=False)

        if filename is not None:
            if isinstance(filename, str):
                filename = (filename,)
            else:
                filename = tuple(filename)

            self._set_component("filename", filename, copy=False)

        if address is not None:
            if isinstance(address, (str, int)):
                address = (address,)
            else:
                address = tuple(address)

            self._set_component("address", address, copy=False)

        if missing_values is not None:
            self._set_component(
                "missing_values", missing_values.copy(), copy=False
            )

        self._set_component("dtype", dtype, copy=False)
        self._set_component("mask", mask, copy=False)
        self._set_component("units", units, copy=False)
        self._set_component("calendar", calendar, copy=False)

        # By default, close the file after data array access
        self._set_component("close", True, copy=False)

    def __getitem__(self, indices):
        """Returns a subspace of the array as a numpy array.

        x.__getitem__(indices) <==> x[indices]

        The indices that define the subspace must be either `Ellipsis` or
        a sequence that contains an index for each dimension. In the
        latter case, each dimension's index must either be a `slice`
        object or a sequence of two or more integers.

        Indexing is similar to numpy indexing. The only difference to
        numpy indexing (given the restrictions on the type of indices
        allowed) is:

          * When two or more dimension's indices are sequences of integers
            then these indices work independently along each dimension
            (similar to the way vector subscripts work in Fortran).

        .. versionadded:: (cfdm) 1.7.0

        """
        dataset, address = self.open()
        dataset0 = dataset

        mask = self.get_mask()
        groups, address = self.get_groups(address)

        if groups:
            dataset = self._uuu(dataset, groups)

        # Get the variable by netCDF name
        variable = dataset.variables[address]
        self.variable = variable
        array = variable[indices]

        if mask:
            self.scale = True
            self.always_mask = False
            self._isvlen = variable.dtype == np.dtype("O")
            if not self._isvlen:
                array = self._mask(array)
                array = self._scale(array)

        # Set the units, if they haven't been set already.
        self._set_units(variable)

        self.close(dataset0)
        del dataset, dataset0
        del self.variable

        string_type = isinstance(array, str)
        if string_type:
            # --------------------------------------------------------
            # A netCDF string type scalar variable comes out as Python
            # str object, so convert it to a numpy array.
            # --------------------------------------------------------
            array = np.array(array, dtype=f"U{len(array)}")

        if not self.ndim:
            # Hmm netCDF4 has a thing for making scalar size 1, 1d
            array = array.squeeze()

        array = self._process_string_and_char(array)
        return array

    def _check_safecast(self, attname):
        """ToDOHDF.

        Check to see that variable attribute exists can can be safely
        cast to variable data type.

        """
        attrs = self.variable.attrs
        if attname in attrs:
            attvalue = attrs[attname]
            att = np.array(attvalue)
            setattr(self, attname, attvalue)
        else:
            return False

        is_safe = True
        try:
            atta = np.array(att, self.dtype)
        except ValueError:
            is_safe = False
        else:
            is_safe = _safecast(att, atta)

        if not is_safe:
            logger.warn(
                f"WARNING: {attname} not used since it cannot "
                "be safely cast to variable data type"
            )  # pragma: no cover

        return is_safe

    def _mask(self, data):
        """TODOHDF."""
        # Private function for creating a masked array, masking
        # missing_values and/or _FillValues.

        attrs = self.variable.attrs
        is_unsigned = attrs.get("_Unsigned", False) in ("true", "True")
        is_unsigned_int = is_unsigned and data.dtype.kind == "i"

        dtype = data.dtype
        if self.scale and is_unsigned_int:
            # Only do this if autoscale option is on.
            dtype_unsigned_int = f"{dtype.byteorder}u{dtype.itemsize}"
            data = data.view(dtype_unsigned_int)

        totalmask = np.zeros(data.shape, np.bool_)
        fill_value = None
        safe_missval = self._check_safecast("missing_value")
        if safe_missval:
            mval = np.array(self.missing_value, self.dtype)
            if self.scale and is_unsigned_int:
                mval = mval.view(dtype_unsigned_int)

            # create mask from missing values.
            mvalmask = np.zeros(data.shape, np.bool_)
            if mval.shape == ():  # mval a scalar.
                mval = (mval,)  # make into iterable.

            for m in mval:
                # is scalar missing value a NaN?
                try:
                    mvalisnan = np.isnan(m)
                except TypeError:
                    # isnan fails on some dtypes
                    mvalisnan = False

                if mvalisnan:
                    mvalmask += np.isnan(data)
                else:
                    mvalmask += data == m

            if mvalmask.any():
                # Set fill_value for masked array to missing_value (or
                # 1st element if missing_value is a vector).
                fill_value = mval[0]
                totalmask += mvalmask

        # set mask=True for data == fill value
        safe_fillval = self._check_safecast("_FillValue")
        if safe_fillval:
            fval = np.array(self._FillValue, self.dtype)
            if self.scale and is_unsigned_int:
                fval = fval.view(dtype_unsigned_int)

            # is _FillValue a NaN?
            try:
                fvalisnan = np.isnan(fval)
            except Exception:
                # isnan fails on some dtypes
                fvalisnan = False

            if fvalisnan:
                mask = np.isnan(data)
            elif (data == fval).any():
                mask = data == fval
            else:
                mask = None

            if mask is not None:
                if fill_value is None:
                    fill_value = fval

                totalmask += mask
        else:
            # Don't return masked array if variable filling is disabled.
            no_fill = 0
            #                with nogil:
            #                    ierr = nc_inq_var_fill(self._grpid,self._varid,&no_fill,NULL)
            #                _ensure_nc_success(ierr)

            # if no_fill is not 1, and not a byte variable, then use
            # default fill value.  from
            # http://www.unidata.ucar.edu/software/netcdf/docs/netcdf-c/Fill-Values.html#Fill-Values
            # "If you need a fill value for a byte variable, it is
            # recommended that you explicitly define an appropriate
            # _FillValue attribute, as generic utilities such as
            # ncdump will not assume a default fill value for byte
            # variables."  Explained here too:
            # http://www.unidata.ucar.edu/software/netcdf/docs/known_problems.html#ncdump_ubyte_fill
            # "There should be no default fill values when reading any
            # byte type, signed or unsigned, because the byte ranges
            # are too small to assume one of the values should appear
            # as a missing value unless a _FillValue attribute is set
            # explicitly."  (do this only for non-vlens, since vlens
            # don't have a default _FillValue)
            if not self._isvlen and (
                no_fill != 1 or dtype.str[1:] not in ("u1", "i1")
            ):
                fillval = np.array(default_fillvals[dtype.str[1:]], dtype)
                has_fillval = data == fillval
                # if data is an array scalar, has_fillval will be a
                # boolean.  in that case convert to an array.
                #                if type(has_fillval) == bool:
                if isinstance(has_fillval, bool):
                    has_fillval = np.asarray(has_fillval)

                if has_fillval.any():
                    if fill_value is None:
                        fill_value = fillval

                    mask = data == fillval
                    totalmask += mask

        # Set mask=True for data outside valid_min, valid_max.
        validmin = None
        validmax = None
        # If valid_range exists use that, otherwise look for
        # valid_min, valid_max. No special treatment of byte data as
        # described at
        # http://www.unidata.ucar.edu/software/netcdf/docs/attribute_conventions.html).
        safe_validrange = self._check_safecast("valid_range")
        safe_validmin = self._check_safecast("valid_min")
        safe_validmax = self._check_safecast("valid_max")
        if safe_validrange and self.valid_range.size == 2:
            validmin = np.array(self.valid_range[0], self.dtype)
            validmax = np.array(self.valid_range[1], self.dtype)
        else:
            if safe_validmin:
                validmin = np.array(self.valid_min, self.dtype)

            if safe_validmax:
                validmax = np.array(self.valid_max, self.dtype)

        if validmin is not None and self.scale and is_unsigned_int:
            validmin = validmin.view(dtype_unsigned_int)

        if validmax is not None and self.scale and is_unsigned_int:
            validmax = validmax.view(dtype_unsigned_int)

        # http://www.unidata.ucar.edu/software/netcdf/docs/attribute_conventions.html).
        # "If the data type is byte and _FillValue is not explicitly
        # defined, then the valid range should include all possible
        # values.  Otherwise, the valid range should exclude the
        # _FillValue (whether defined explicitly or by default) as
        # follows. If the _FillValue is positive then it defines a
        # valid maximum, otherwise it defines a valid minimum."
        if safe_fillval:
            fval = np.array(self._FillValue, dtype)
        else:
            k = dtype.str[1:]
            if k in ("u1", "i1"):
                fval = None
            else:
                fval = np.array(default_fillvals[k], dtype)

        if self.dtype.kind != "S":
            # Don't set mask for character data

            # Setting valid_min/valid_max to the _FillVaue is too
            # surprising for many users (despite the netcdf docs
            # attribute best practices suggesting clients should do
            # this).
            if validmin is not None:
                totalmask += data < validmin

            if validmax is not None:
                totalmask += data > validmax

        if fill_value is None and fval is not None:
            fill_value = fval

        # If all else fails, use default _FillValue as fill_value for
        # masked array.
        if fill_value is None:
            fill_value = default_fillvals[dtype.str[1:]]

        # Create masked array with computed mask
        masked_values = bool(totalmask.any())
        if masked_values:
            data = np.ma.masked_array(
                data, mask=totalmask, fill_value=fill_value
            )
        else:
            # Always return masked array, if no values masked.
            data = np.ma.masked_array(data)

        # Scalar array with mask=True should be converted to
        # np.ma.MaskedConstant to be consistent with slicing
        # behavior of masked arrays.
        if data.shape == () and data.mask.all():
            # Return a scalar numpy masked constant not a 0-d masked
            # array, so that data == np.ma.masked.
            data = data[()]

        elif not self.always_mask and not masked_values:
            # Return a regular numpy array if requested and there are
            # no missing values
            data = np.array(data, copy=False)

        return data

    def _scale(self, data):
        """TODOHDF."""
        # If variable has scale_factor and add_offset attributes,
        # apply them.
        attrs = self.variable.attrs
        scale_factor = attrs.get("scale_factor")
        add_offset = attrs.get("add_offset")
        try:
            if scale_factor is not None:
                float(scale_factor)

            if add_offset is not None:
                float(add_offset)
        except ValueError:
            logging.warn(
                "invalid scale_factor or add_offset attribute, "
                "no unpacking done..."
            )
            return data

        if scale_factor is not None and add_offset is not None:
            if add_offset != 0.0 or scale_factor != 1.0:
                data = data * scale_factor + add_offset
            else:
                data = data.astype(scale_factor.dtype)
        elif scale_factor is not None and scale_factor != 1.0:
            # If variable has only scale_factor attribute, rescale.
            data = data * scale_factor
        elif add_offset is not None and add_offset != 0.0:
            # If variable has only add_offset attribute, add offset.
            data = data + add_offset

        return data

    #    def _get_attr(self, var, attr):
    #        """TODOHDF.
    #
    #        .. versionadded:: (cfdm) HDFVER
    #
    #        :Parameters:
    #
    #        """
    #        return var.attrs[attr]

    def close(self, dataset):
        """Close the dataset containing the data.

        .. versionadded:: (cfdm) HDFVER

        :Parameters:

            dataset: `h5netcdf.File`
                The netCDF dataset to be be closed.

        :Returns:

            `None`

        """
        if self._get_component("close"):
            dataset.close()

    def get_groups(self, address):
        """The netCDF4 group structure of a netCDF variable.

        .. versionadded:: (cfdm) 1.8.6.0

        :Parameters:

            address: `str` or `int`
                The netCDF variable name, or integer varid, from which
                to get the groups.

                .. versionadded:: (cfdm) 1.10.1.0

        :Returns:

            (`list`, `str`) or (`list`, `int`)
                The group structure and the name within the group. If
                *address* is a varid then an empty list and the varid
                are returned.

        **Examples**

        >>> n.get_groups('tas')
        ([], 'tas')

        >>> n.get_groups('/tas')
        ([], 'tas')

        >>> n.get_groups('/data/model/tas')
        (['data', 'model'], 'tas')

        >>> n.get_groups(9)
        ([], 9)

        """
        try:
            if "/" not in address:
                return [], address
        except TypeError:
            return [], address

        out = address.split("/")[1:]
        return out[:-1], out[-1]

    def open(self, **kwargs):
        """Return a dataset file object and address.

        When multiple files have been provided an attempt is made to
        open each one, in the order stored, and a file object is
        returned from the first file that exists.

        :Returns:

            (`h5netcdf.File`, `str`)
                The open file object, and the address of the data
                within the file.

        """
        return super().open(
            h5netcdf.File, mode="r", decode_vlen_strings=True, **kwargs
        )
