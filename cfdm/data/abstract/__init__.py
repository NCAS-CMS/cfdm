import time
s = time.time()
print('0 data/abstract/__init__')

from .array import Array

print('  5 data/abstract/__init__', time.time()-s); s = time.time()
from .compressedarray import CompressedArray
print('  6 data/abstract/__init__', time.time()-s); s = time.time()
from .filearray import FileArray
print('  7 data/abstract/__init__', time.time()-s); s = time.time()
from .mesharray import MeshArray
print('  8 data/abstract/__init__', time.time()-s); s = time.time()
from .raggedarray import RaggedArray

print('  9 data/abstract/__init__', time.time()-s)
