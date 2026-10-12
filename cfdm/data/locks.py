from contextlib import nullcontext
from threading import Lock

no_lock = nullcontext()
netcdf_lock = Lock()
