import numpy as np

from .quadraticinterpolation import QuadraticInterpolation


x, y, z = (0, 1, 2)


class QuadraticGeographicInterpolation(QuadraticInterpolation):
    """Mixin class for quadratic geographic interpolation formulas.

    See CF appendix J "Coordinate Interpolation Methods".

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def _fcea2cv(self, va, vb, ce, ca):
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
            k = k - ce * ce

        if ca is not None:
            k = k - ca * ca

        cr = self._fsqrt(k) - self._fsqrt(rsqr)

        cv = self._fmultiply(cr, vr)

        if ce is not None:
            cv = self._fplus(cv, self._fmultiply(ce, self._fminus(va, vb)))

        if ca is not None:
            cv = self._fplus(cv, self._fmultiply(ca, self._fcross(va, vb)))

        return cv

    def _fcll(
        self, lat_a, lon_a, lat_b, lon_b, lat_ab, lon_ab, subsampled_dimension
    ):
        """TODO.

        cll = fcll(lla, llb, llab)
            = (fw(lla.lat, llb.lat, llab.lat, 0.5),
               fw(lla.lon, llb.lon, llab.lon, 0.5))

        where

        llab = fv2ll(fqv(va, vb, cv, 0.5))

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            {{subsampled_dimension: `int`}}
        
        :Returns:

            `numpy.ndarray`

        """
        return (
            self._fw(lat_a, lat_b, lat_ab, subsampled_dimension, s_i=0.5),
            self._fw(lon_a, lon_b, lon_ab, subsampled_dimension, s_i=0.5),
        )

    def _fcross(self, va, vb):
        """Vector cross product.

        (x, y, z) = fcross(va, vb)
                  = (va.y*vb.z - va.z*vb.y,
                     va.z*vb.x - va.x*vb.z,
                     va.x*vb.y - va.y*vb.x)

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            va: `tuple` of array_like

            vb: `tuple` of array_like

        :Returns:

            `tuple`

        """
        return (
            va[y] * vb[z] - va[z] * vb[y],
            va[z] * vb[x] - va[x] * vb[z],
            va[x] * vb[y] - va[y] * vb[x],
        )

    def _fcv(self, va, vb, vp_i, subsampled_dimension, s_i):
        """Three-dimensionsal cartesian interpolation coefficients.

        cv = fcv(va, vb, vp(i), s(i))
           = (fw(va.x, vb.x, vp(i).x, s(i)),
              fw(va.y, vb.y, vp(i).y, s(i)),
              fw(va.z, vb.z, vp(i).z, s(i)))

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            va, vb: `tuple` of array_like
                The tie point vector representations of the tie point
                latitude-longitude representations

            vp_i: `tuple` of array_like
                The tie point vector representations from the tie
                point latitude-longitude representations

            {{subsampled_dimension: `int`}}

            {{s_i: array_like}}

        :Returns:

            `tuple`

        """
        return tuple(
            self._fw(va[i], vb[i], vp_i[i], subsampled_dimension, s_i)
            for i in (x, y, z)
        )

    def _fcv2cea(self, va, vb, cv):
        """Parametric representation interpolation coefficients.

        cea = (ce, ca)
            = fcv2cea(va, vb, cv)
            = (fdot(cv, fminus(va, vb)) / gsqr,
               fdot(cv, fcross(va, vb)) / (rsqr*gsqr))

        where

        rsqr = fdot(vr, vr)
        gsqr = fdot(vg, vg)

        and where

        vr = fmultiply(0.5, fplus(va, vb))
        vg = fminus(va, vb)

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            va, vb: `tuple` of array_like
                The tie point vector representations of the tie point
                latitude-longitude representations.

            cv: array_like
                The three-dimensional cartesian interpolation
                parmaeters.

        :Returns:

            `tuple`

        """
        vr = self._fmultiply(0.5, self._fplus(va, vb))
        vg = self._fminus(va, vb)
        rsqr = self._fdot(vr, vr)
        gsqr = self._fdot(vg, vg)

        return (
            self._fdot(cv, self._fminus(va, vb)) / gsqr,
            self._fdot(cv, self._fcross(va, vb)) / (rsqr * gsqr),
        )

    def _fll2v(self, lat, lon):
        """TODO.

        Conversion from geocentric (latitude, longitude) to
        three-dimensional cartesian vector (x, y, z)

        (x, y, z) = fll2v(lat, lon)
                  = (cos(lat)*cos(lon),
                     cos(lat)*sin(lon),
                     sin(lat))

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

    def _fminus(self, va, vb):
        """Vector difference.

        (x, y, z) = fminus(va, vb)
                  = (va.x - vb.x,
                     va.y - vb.y,
                     va.z - vb.z)

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return tuple(a - b for a, b in zip(va, vb))

    def _fmultiply(self, r, v):
        """Vector multiplied by scalar.

        (x, y, z) = fmultiply(r, v)
                  = (r * v.x,
                     r * v.y,
                     r * v.z)

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
        s=None,
    ):
        """Quadratic interpolation in latitude-longitude coordinates.

        llp.lat, llp.lon = fqll(lla, llb, cll, s)
                         = (fq(lla.lat, llb.lat, cll.lat, s),
                            fq(lla.lon, llb.lon, cll.lon, s))

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:
        
            {{subsampled_dimension: `int`}}
        
            {{s: array_like, optional}}

        """
        lat = self._fq(
            lat_a,
            lat_b,
            lat_c,
            subsampled_dimension,
            s=s,
        )
        lon = self._fq(
            lon_a,
            lon_b,
            lon_c,
            subsampled_dimension,
            s=s,
        )

        return (lat, lon)

    def _fqv(self, va, vb, cv, subsampled_dimension, s=None):
        """Reconstitute points in 3-d cartesian coordinates.

        vp.x, vp.y, vp.z = fqv(va, vb, cv, s)
                         = (fq(va.x, vb.x, cv.x, s),
                            fq(va.y, vb.y, cv.y, s),
                            fq(va.z, vb.z, cv.z, s))

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            va:
                The three-dimensionsal vector representation of the
                first tie point, as calculated by `_flv`.

            vb:
                The three-dimensionsal vector representation of the
                second tie point, as calculated by `_fll2v`.

            cv:
                The three-dimensional cartesian representation of the
                quadratic interpolation parameter ``w``, as calculated
                by `_fcea2cv`.

            {{subsampled_dimension: `int`}}
        
            {{s: array_like, optional}}

        :Returns:

            `tuple`

        """
        return tuple(
            self._fq(va[i], vb[i], cv[i], subsampled_dimension, s=s)
            for i in (x, y, z)
        )

    def _fsqrt(self, t):
        """Square root.

        s = fsqrt(t)

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

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            v: `tuple` of array_like

        :Returns:

            `tuple` of arrays

        """
        return (
            np.atan2(v[y], v[x]),
            np.atan2(v[z], (v[x] * v[x] + v[y] * v[y]) ** 0.5),
        )
