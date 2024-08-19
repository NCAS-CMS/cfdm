"""Configuration for the `Data` class."""

# The Units object
from cfunits import Units  # noqa: F401

_DEFAULT_CHUNKS = "auto"
_DEFAULT_HARDMASK = True

# Contstants used to specify which `Data` components should be cleared
# when a new Dask array is set. See `Data._clear_after_dask_update`
# for details. These must be powers to 2, except for _ALL, which must
# be 2**N - 1
_NONE = 0  # =   0b0000000000
_ARRAY = 1  # =  0b0000000001
_CACHE = 2  # =  0b0000000010
_CFA = 4  # =    0b0000000100
_ALL = 1023  # = 0b1111111111
