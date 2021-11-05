import numpy as np

from .abstract import CompressedArray
from .mixin import (
    GeographicInterpolation,
    QuadraticInterpolation,
    SubsampledArray,
)


class SubsampledQuadraticLatitudeLongitudeArray(
    GeographicInterpolation,
    QuadraticInterpolation,
    SubsampledArray,
    CompressedArray,
):
    """A subsampled array with quadratic_latitude_longitude
    interpolation.

    The information needed to uncompress the data is stored in a tie
    point index variable that defines the relationship between the
    indices of the subsampled dimension and the indices of the
    corresponding interpolated dimension.

    **Cell boundaries**

    If the subsampled array represents cell boundaries, then the
    *shape*, *ndim* and *size* parameters that describe the
    uncompressed array will include the required trailing size 2
    dimension.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        interpolation_description=None,
        computational_precision=None,
        tie_point_indices={},
        interpolation_parameters={},
        parameter_dimensions={},
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: `Data`
                The tie points array.

            shape: `tuple`
                The uncompressed array dimension sizes.

            size: `int`
                Number of elements in the uncompressed array.

            ndim: `int`
                The number of uncompressed array dimensions.

            compressed_axes: sequence of `int`
                The position of the compressed axis in the tie points
                array.

                *Parameter example:*
                  ``compressed_axes=[1]``

            tie_point_indices: `dict`, optional
                TODO

            tie_point_indices: `dict`
                The tie point index variable for each subsampled
                dimension. A key indentifies a subsampled dimension by
                its integer position in the compressed array, and its
                value is a `TiePointIndex` variable.

                *Parameter example:*
                  ``tie_point_indices={1: cfdm.TiePointIndex(data=[0, 16])}``

            computational_precision: `str`, optional
                The floating-point arithmetic precision used during
                the preparation and validation of the compressed
                coordinates.

                *Parameter example:*
                  ``computational_precision='64'``

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            size=size,
            ndim=ndim,
            compression_type="subsampled",
            interpolation_name="quadratic_latitude_longitude",
            computational_precision=computational_precision,
            tie_point_indices=tie_point_indices.copy(),
            interpolation_parameters=interpolation_parameters.copy(),
            parameter_dimensions=parameter_dimensions.copy(),
            compressed_dimensions=tuple(tie_point_indices),
            one_to_one=True,
        )

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        # If the first or last element is requested then we don't need
        # to interpolate
        try:
            return self._first_or_last_index(indices)
        except IndexError:
            pass

        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        lat = self.get_latitude(None)
        if lat is not None:
            lon = self
        else:
            lat = self
            lon = self.get_longitude(None)            
            if lon is None:            
                raise ValueError(
                    "Can't subspace: quadratic_latitude_longitude "
                    "interpolation of longitudes requires corresponding "
                    "latitudes, and vice versa."
            )
       
        (d0,) = tuple(self.compressed_dimensions())

        tie_points = self._get_compressed_Array()

        parameters = self.get_interpolation_parameters(conform=True)
        ce = parameters.get("ce")
        ca = parameters.get("ca")
        flags = parameters.get("interpolation_subarea_flags")

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=np.dtype(float))

        # Interpolate the tie points for each interpolation subarea
        for u_indices, tp_indices, subarea_size, first, subarea_index in zip(
            *self._interpolation_subareas()
        ):
            lat_a = lat._select_tie_points(tie_points, tp_indices, {d0: 0})
            lon_a = lon._select_tie_points(tie_points, tp_indices, {d0: 0})
            lat_b = lat._select_tie_points(tie_points, tp_indices, {d0: 1})
            lon_b = lon._select_tie_points(tie_points, tp_indices, {d0: 1})

            lat_p, lon_p = self._quadratic_latitude_longitude_interpolation(
                lat_a,
                lon_a,
                lat_b,
                lon_b,
                ce,
                ca,
                flags,
                d0,
                first,
                subarea_index,
            )

            if is_latitude:
                u = lat_p
            else:
                u = lon_p

            self._set_interpolated_values(uarray, u, u_indices, (d0,))

        self._s.cache_clear()

        self.del_latitude_or_longitude()

        return self.get_subspace(uarray, indices, copy=True)

    def _fcea2cv(self, va, vb, ce, ca, subarea_index):
        """TODO.
 
        cv = fcea2cv(va, vb, ce, ca)
           = fplus(fmultiply(ce, fminus(va, vb)),
                   fmultiply(ca, fcross(va, vb)),
                   fmultiply(cr, vr))

        where

        vr = fmultiply(0.5, fplus(va, vb))
        rsqr = fdot(vr, vr)
        cr = fsqrt(1 - ce*ce - ca*ca) - fsqrt(rsqr)

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        vr = self._fmultiply(0.5, self._fplus(va, vb))
        rsqr = self._fdot(vr, vr)

        k = 1
        if ce is not None:
            ce = ce[subarea_index]
            k = k - ce * ce

        if ca is not None:
            ca = ca[subarea_index]
            k = k - ca * ca

        cr = self._fsqrt(k) - self._fsqrt(rsqr)

        out = self._fmultiply(cr, vr)

        if ce is not None:
            out = self._fmultiply(ce, self._fminus(va, vb))

        if ca is not None:
            out = self._fmultiply(ca, self._fcross(va, vb))

        return out

    def _fcll(self, lat_a, lon_a, lat_b, lon_b, va, vb, cv):
        """TODO.

        cll = fcll(lla, llb, llab)
            = (fw(lla.lat, llb.lat, llab.lat, 0.5),
               fw(lla.lon, llb.lon, llab.lon, 0.5))

        where

        llab = fv2ll(fqv(va, vb, cv, 0.5))

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        (lat_ab, lon_ab) = self._fv2ll(self._fqv(va, vb, cv, 0.5))
        return (
            self._fw(lat_a, lat_b, lat_ab, 0.5),
            self._fw(lon_a, lon_b, lon_ab, 0.5),
        )

    def _fqll(
        self,
        lat_a,
        lon_a,
        lat_b,
        lon_b,
        lat_c,
        lon_c,
        subsampled_dimension,
        first,
        subarea_index,
    ):
        """Quadratic interpolation in latitude-longitude coordinates.

        llp(i) = (llp(i).lat, llp(i).lon)
               = fqll(lla, llb, cll, s(i))
               = (fq(lla.lat, llb.lat, cll.lat, s(i)),
                  fq(lla.lon, llb.lon, cll.lon, s(i)))

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        d0 = subsampled_dimension

        lat = self._fq(
            lat_a, lat_b, lat_c, d0, first, subarea_index, trim=False
        )
        lon = self._fq(
            lon_a, lon_b, lon_c, d0, first, subarea_index, trim=False
        )

        return (lat, lon)

    def _fqv(self, va, vb, cv, subsampled_dimension, first, subarea_index):
        """TODO.

        vp(i) = fqv(va, vb, cv, s(i))
              = (fq(va.x, vb.x, cv.x, s(i)),
                 fq(va.y, vb.y, cv.y, s(i)),
                 fq(va.z, vb.z, cv.z, s(i)))

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        (x, y, z) = (0, 1, 2)
        d0 = subsampled_dimension

        return (
            self._fq(
                va[x], vb[x], cv[x], d0, first, subarea_index, trim=False
            ),
            self._fq(
                va[y], vb[y], cv[y], d0, first, subarea_index, trim=False
            ),
            self._fq(
                va[z], vb[z], cv[z], d0, first, subarea_index, trim=False
            ),
        )

    def _quadratic_latitude_longitude_interpolation(
        self,
        lat_a,
        lon_a,
        lat_b,
        lon_b,
        ce,
        ca,
        flags,
        subsampled_dimension,
        subarea_index,
        first,
        trim=True,
    ):
        """Quadratic interpolation of geographic coordinates.

        A one-dimensional quadratic method for interpolation of the
        geographic coordinates latitude and longitude, typically used
        for remote sensing products with geographic coordinates on the
        reference ellipsoid. See CF appendix J for details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_quadratic_interpolation`, `_trim`

        :Parameters:

            lat_a, lon_a: array_like
                The latitudes and longitudes of the first tie point in
                index space space.

            lat_b, lon_b: array_like
                The latitudes and longitudes of the second tie point
                in index space.

            ce: `InterpolationParameter` or `None`
                The interpolation coefficient "ce". If `None` then the
                "ce" is assumed to be zero.

            ca: `InterpolationParameter` or `None`
                The interpolation coefficient "ca". If `None` then the
                "ca" is assumed to be zero.

            flags: `InterpolationParameter` or `None`
                The interpolation coefficient
                "interpolation_subarea_flags". If `None` then the
                "interpolation_subarea_flags" is assumed to be zero. TODO.

            subsampled_dimension: `int`
                The position of the subsampled dimension in the
                compressed data.

            subarea_index: `tuple` of `slice`
                The index of the interpolation subarea along the
                interpolation subarea dimension.

            first: `tuple` of `bool`
                For each dimension, True if the interpolation subarea
                is the first (in index space) of a new continuous
                area, otherwise False.

            trim: `bool`, optional
                For the interpolated dimension, remove the first point
                of the interpolation subarea when it is not the first
                (in index space) of a continuous area, and when the
                compressed data are not bounds tie points.

        :Returns:

            `numpy.ndarray`

        """
        va = self._fll2v(lat_a, lon_a)
        vb = self._fll2v(lat_b, lon_b)
        cv = self._fcea2cv(va, vb, ce, ca, subarea_index)

        if flags is not None and flags[subarea_index]:
            # Use interpolation in three-dimensional cartesian
            # coordinates
            lat_p, lon_p = (None, None)
        else:
            # Use interpolation in latitude-longitude coordinates
            lat_c, lon_c = self._fcll(
                lat_a,
                lon_a,
                lat_b,
                lon_b,
                va,
                vb,
                cv,
                subsampled_dimension,
                first,
                subarea_index,
            )
            lat_p, lon_p = self._fqll(
                lat_a,
                lon_a,
                lat_b,
                lon_b,
                lat_c,
                lon_c,
                subsampled_dimension,
                first,
                subarea_index,
            )

        if trim:
            lat_p = self._trim(lat_p, (subsampled_dimension,), first)
            lon_p = self._trim(lon_p, (subsampled_dimension,), first)

        return (lat_p, lon_p)
