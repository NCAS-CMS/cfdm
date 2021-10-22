import numpy as np

from .quadraticinterpolation import QuadraticInterpolation


class GeographicInterpolation(QuadraticInterpolation):
    """Mixin class for geographic interpolation formulas.

    See CF appendix J for details.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def _fll2v(self, lat, lon):
        """TODO.

        Conversion from geocentric (latitude, longitude) to
        three-dimensional cartesian vector (x, y, z)

        (x, y, z) = fll2v(ll)
                  = (cos(ll.lat)*cos(ll.lon),
                     cos(ll.lat)*sin(ll.lon),
                     sin(ll.lat))

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        cos_lat = np.cos(lat)
        return (
            cos_lat * np.cos(lon),
            cos_lat * np.sin(lon),
            np.sin(lat),
        )

    def _fcross(self, va, vb):
        """Vector cross product.

        (x, y, z) = fcross(va, vb)
                  = (va.y*vb.z - va.z*vb.y,
                     va.z*vb.x - va.x*vb.z,
                     va.x*vb.y - va.y*vb.x)

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        (x, y, z) = (0, 1, 2)
        return (
            va[y] * vb[z] - va[z] * vb[y],
            va[z] * vb[x] - va[x] * vb[z],
            va[x] * vb[y] - va[y] * vb[x],
        )

    def _fmultiply(self, r, v):
        """Vector multiplied by scalar.

        (x, y, z) = fmultiply(r, v)
                  = (r * v.x,
                     r * v.y,
                     r * v.z)

        """
        return tuple(a * r for a in v)

    def _fminus(self, va, vb):
        """Vector difference.

        (x, y, z) = fminus(va, vb)
                  = (va.x - vb.x,
                     va.y - vb.y,
                     va.z - vb.z)

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return tuple(a - b for a, b in zip(va, vb))

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

        """
        out = []
        for v in zip(*vectors):
            s = v[0]
            for a in v[1:]:
                s = s + a

            out.append(s)

        return tuple(out)

    def _fsqrt(self, t):
        """Square root.

        s = fsqrt(t)

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            t: array_like

        """
        return t ** 0.5

    def _fv2ll(self, v):
        """Convert cartesian (x, y, z) to geocentric (latitude,
        longitude).

        Conversion from three-dimensional cartesian vector (x, y, z)
        to geocentric (latitude, longitude).

        (lat, lon) = fv2ll(v)
                   = (atan2(v.y, v.x),
                      atan2(z, sqrt(v.x * v.x + v.y * v.y))

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            v: 3-`tuple`

        """
        (x, y, z) = (0, 1, 2)
        return (
            np.atan2(v[y], v[x]),
            np.atan2(v[z], (v[x] * v[x] + v[y] * v[y]) ** 0.5),
        )

    def get_latitude_or_longitude(self):
        """TODO."""
        return self._get_component("latitude_or_longitude")

    def set_latitude_or_longitude(self, value):
        """TODO."""
        return self._set_component("latitude_or_longitude", value, copy=False)

    def del_latitude_or_longitude(self):
        """TODO."""
        return self._del_component("latitude_or_longitude", None)
