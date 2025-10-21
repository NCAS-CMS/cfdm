import time
s = time.time()
print('0 data/mixin/__init__')
from .arraymixin import ArrayMixin
print('  7 data/mixin/__init__', time.time()-s); s = time.time()
from .compressedarraymixin import CompressedArrayMixin
print('  8 data/mixin/__init__', time.time()-s); s = time.time()
from .indexmixin import IndexMixin

print('  9 data/mixin/__init__', time.time()-s); s = time.time()
