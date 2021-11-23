import numpy as np

from .quadraticinterpolation import QuadraticInterpolation


class GeographicInterpolation(QuadraticInterpolation):
    """Mixin class for geographic interpolation formulas.

    See CF appendix J "Coordinate Interpolation Methods" for details.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

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

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

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

        cv = self._fmultiply(cr, vr)

        if ce is not None:
            cv = self._fplus(cv, self._fmultiply(ce, self._fminus(va, vb)))

        if ca is not None:
            cv = self._fplus(cv, self._fmultiply(ca, self._fcross(va, vb)))

        return cv

    def _fcross(self, va, vb):
        """Vector cross product.

        (x, y, z) = fcross(va, vb)
                  = (va.y*vb.z - va.z*vb.y,
                     va.z*vb.x - va.x*vb.z,
                     va.x*vb.y - va.y*vb.x)

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            va: `tuple` of array_like

            vb: `tuple` of array_like

        :Returns:

            `tuple`

        """
        (x, y, z) = (0, 1, 2)
        return (
            va[y] * vb[z] - va[z] * vb[y],
            va[z] * vb[x] - va[x] * vb[z],
            va[x] * vb[y] - va[y] * vb[x],
        )

    def _fll2v(self, lat, lon):
        """TODO.

        Conversion from geocentric (latitude, longitude) to
        three-dimensional cartesian vector (x, y, z)

        (x, y, z) = fll2v(lat, lon)
                  = (cos(lat)*cos(lon),
                     cos(lat)*sin(lon),
                     sin(lat))

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            lat: array_like

            lon: array_like

        :Returns:

            `tuple`

        """
        cos_lat = np.cos(lat)
        return (
            cos_lat * np.cos(lon),
            cos_lat * np.sin(lon),
            np.sin(lat),
        )

    def _fcv(self, va, vb, vp, s):
        """TODO

        cv = fcv(va, vb, vp(i), s(i)) = (fw(va.x, vb.x, vp(i).x, s(i)), fw(va.y, vb.y, vp(i).y, s(i)), fw(va.z, vb.z, vp(i).z, s(i))).

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        (x, y, z) = (0, 1, 2)
        return (
            self._fw(va[x], vb[x], vp(i)[x], s),
            self._fw(va[y], vb[y], vp(i)[y], s),
            self._fw(va[z], vb[z], vp(i)[z], s),        
        )
    
    def _fminus(self, va, vb):
        """Vector difference.

        (x, y, z) = fminus(va, vb)
                  = (va.x - vb.x,
                     va.y - vb.y,
                     va.z - vb.z)

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return tuple(a - b for a, b in zip(va, vb))

    def _fmultiply(self, r, v):
        """Vector multiplied by scalar.

        (x, y, z) = fmultiply(r, v)
                  = (r * v.x,
                     r * v.y,
                     r * v.z)

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

        .. versionaddedd:: (cfdm) 1.9.TODO.0

        :Parameters:

            r: scalar array_like

            v: `tuple` of array_like

        :Returns:

            `tuple`

        """
        return tuple(a * r for a in v)

    def _fplus(self, *vectors):
        """Vector sum.

        Two vectors:

        (x, y, z) = fplus(va, vb)
                  = (va.x + vb.x,
                     va.y + vb.y,
                     va.z + vb.z)

        Three vectors:

        (x, y, z) = fplus(va, vb, vc)
                  = (va.x + vb.x + vc.x,
                     va.y + vb.y + vc.y,
                     va.z + vb.z + vc.z)

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

           vectors:
               The vectors to be added, each defined by a `tuple` of
               array_like.

        :Returns:

            `tuple`

        """
        out = []
        for v in zip(*vectors):
            s = v[0]
            for a in v[1:]:
                s = s + a

            out.append(s)

        return tuple(out)

    def _fqll(
        self,
        lat_a,
        lon_a,
        lat_b,
        lon_b,
        lat_c,
        lon_c,
        subsampled_dimension,
        subarea_shape,
        subarea_index,
        first,
        s=None
    ):
        """Quadratic interpolation in latitude-longitude coordinates.

        llp.lat, llp.lon = fqll(lla, llb, cll, s)
                         = (fq(lla.lat, llb.lat, cll.lat, s),
                            fq(lla.lon, llb.lon, cll.lon, s))

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        lat = self._fq(
            lat_a,
            lat_b,
            lat_c,
            subsampled_dimension,
            subarea_index,
            subarea_shape,
            first,
            s=s,
            trim=False,
        )
        lon = self._fq(
            lon_a,
            lon_b,
            lon_c,
            subsampled_dimension,
            subarea_index,
            subarea_shape,
            first,
            s=s,
            trim=False,
        )

        return (lat, lon)

    def _fqv(
        self,
        va,
        vb,
        cv,
        subsampled_dimension,
        subarea_shape,
        subarea_index,
        first,
            s=None,
    ):
        """Reconstitute points in 3-d cartesian coordinates.

        vp,x, vp.y, vp.z = fqv(va, vb, cv)
                         = (fq(va.x, vb.x, cv.x),
                            fq(va.y, vb.y, cv.y),
                            fq(va.z, vb.z, cv.z))

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            va:
                The three-dimensionsal vector representation of the
                first tie point, as calculated by `_fll2v`.

            vb:
                The three-dimensionsal vector representation of the
                second tie point, as calculated by `_fll2v`.

            cv:
                The three-dimensional cartesian representation of the
                quadratic interpolation parameter ``w``, as calculated
                by `_fcea2cv`.

            subsampled_dimension: `int`
                The position of the subsampled dimension in the
                compressed data.

            subarea_shape: `tuple` of `int`
                The shape of the uncompressed interpolation subararea,
                including all tie points, but excluding a bounds
                dimension.

            subarea_index: `tuple` of `slice`
                The index of the interpolation subarea.

            first: `tuple` of `bool`
                For each dimension, True if the interpolation subarea
                is the first (in index space) of a new continuous
                area, otherwise False.

            s: array_like or `None`
                If `None` then the interpolation coeficient ``s`` is
                calculated for each uncompressed location. Otherwise
                the values are taken as specified.

        :Returns:

            `tuple`

        """
        (x, y, z) = (0, 1, 2)

        return tuple(
            self._fq(
                va[i],
                vb[i],
                cv[i],
                subsampled_dimension,
                subarea_shape,
                subarea_index,
                first,
                s=s,
                trim=False,
            )
            for i in (x, y, z)
        )

    def _fsqrt(self, t):
        """Square root.

        s = fsqrt(t)

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            t: array_like

        :Returns:

            The square root of the values.

        """
        return t ** 0.5

    def _fv2ll(self, v):
        """Convert cartesian to geocentric coordinates.

        Converts three-dimensionsal (x, y, x) cartesian coordinates to
        geocentric (latitude, longitude) coordinates.

        (lat, lon) = fv2ll(v)
                   = (atan2(v.y, v.x),
                      atan2(z, sqrt(v.x * v.x + v.y * v.y))

        See CF appendix J "Coordinate Interpolation Methods" for
        details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            v: `tuple` of array_like

        :Returns:

            `tuple` of arrays

        """
        (x, y, z) = (0, 1, 2)
        return (
            np.atan2(v[y], v[x]),
            np.atan2(v[z], (v[x] * v[x] + v[y] * v[y]) ** 0.5),
        )

    def _use_3d_cartesian(self, flags, subarea_index):
        """TODO

        See CF section 3.5 "Flags" and Appendix J "Coordinate
        Interpolation Methods" for details.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            flags: `InteprolationParameter`, or `None`
                The interpolation parameter
                "interpolation_subarea_flags". It is assumed that the
                parameter has the same number of dimensions in the
                same relative order as the tie points array. If `None`
                then an exception is raised.

            subarea_index: `tuple` of `slice`
                The index of the interpolation subarea.

        :Returns:

            An array for which zero values incidate where
            latitude-longitude interpolation is to be used, and
            non-zero values indicate where three-dimensional cartesian
            interpolation is to be used.

        """
        if flags is None:
            raise ValueError(
                "Can't uncompress subsampled coordinates with the "
                f"{self.get_interpolation_name()} method when the "
                "interpolation_subarea_flags interpolation parameter "
                "has not been defined"
            )

        use_3d_cartesian = "location_use_3d_cartesian"

        flag_values = flags.get_property("flag_values", None)
        flag_masks = flags.get_property("flag_masks", None)
        flag_meanings = flags.get_property("flag_meanings", None)

        if flag_meanings is None:
            raise ValueError(
                "Can't uncompress subsampled coordinates with the "
                f"{self.get_interpolation_name()} method when the "
                "interpolation_subarea_flags interpolation parameter "
                "does not have a flag_meanings property"
            )

        if use_3d_cartesian not in flag_meanings.split():
            raise ValueError(
                "Can't uncompress subsampled coordinates with the "
                f"{self.get_interpolation_name()} method when the "
                "interpolation_subarea_flags interpolation parameter "
                "does not have 'location_use_3d_cartesian' in its "
                "flag_meanings property"
            )

        if flags_masks is not None:
            flag_masks = np.atleast_1d(flag_masks)
        elif flags_values is None:
            raise ValueError(
                "Can't uncompress subsampled coordinates with the "
                f"{self.get_interpolation_name()} method when the "
                "interpolation_subarea_flags interpolation parameter "
                "does not have a flag_values property and/or a "
                "flag_masks property"
            )

        flag_meanings = np.atleast_1d(flag_meanings)
        index = np.where(flag_meanings == use_3d_cartesian)[0]

        flags = flags[subarea_index].array

        if flag_values is not None:
            flag_values = np.atleast_1d(flag_values)
            flag_value = flag_values[index]
            if flags_masks is None:
                # flag_values but no flag_masks
                out = flags == flag_value
            else:
                # flag_values and flag_masks
                out = flags & (flag_mask[index] & flag_value)
        else:
            # flag_masks but no flag_values
            out = flags & flag_mask[index]

        return out

    def codependent_tie_points(self, *identities):
        """Get all codependent tie points.

        Returns the tie points from `source` as well as those returned
        by `get_dependent_tie_points`.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            identities:
                The identities of the codependent tie points, all
                except one of which must be keys of the dictionary
                returned by `get_dependent_tie_points`.

        :Returns:

            `list`
                The codependent tie points, in the order specified by
                the *identities* parameter.

        **Examples**

        >>> lat, lon = g.codependent_tie_points('latitude', 'longitude')

        """
        dependent_tie_points = self.get_dependent_tie_points(conform=True)
        if (
                len(identities) != len(dependent_tie_points) + 1
                or not set(identities).issubset(dependent_tie_points)
        ):
            raise ValueError(
                "Specified identities must comprise all except one of "
                f"{', '.join(map(str, dependent_tie_points))}. Got "
                f"{', '.join(map(str, identities))}"
            )
        
        out = []
        for identity in identities:
            tie_points = dependent_tie_points.get(identity)
            if tie_points is None:
                out.append(self.source())
            else:
                out.append(tie_points)

        return out
