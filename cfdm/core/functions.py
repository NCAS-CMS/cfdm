import os
import platform
import sys
from pickle import dumps, loads

from . import __cf_version__, __file__, __version__


def environment(display=True, paths=True):
    """Return the names, versions and paths of all dependencies.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        display: `bool`, optional
            If True (the default) then display the description of the
            environment as a string. If False the description is
            instead returned as a list.

        paths: `bool`, optional
            If True (the default) then output the locations of each
            package. If False the locations are not included.

    :Returns:

        `None` or `list`
            If *display* is True then the description of the
            environment is printed and `None` is returned. Otherwise
            the description is returned as in a `list`.

    **Examples**

    >>> cfdm.core.environment(paths=False)
    Platform: Linux-5.15.0-92-generic-x86_64-with-glibc2.35
    Python: 3.11.4
    packaging: 23.0
    numpy: 1.25.2
    cfdm.core: NEXTVERSION

    """
    import numpy as np
    import packaging

    dependency_version_paths_mapping = {
        "Platform": (platform.platform(), ""),
        "Python": (platform.python_version(), sys.executable),
        "packaging": (
            packaging.__version__,
            os.path.abspath(packaging.__file__),
        ),
        "numpy": (np.__version__, os.path.abspath(np.__file__)),
        "cfdm.core": (__version__, os.path.abspath(__file__)),
    }
    string = "{0}: {1!s}"
    if paths:  # include path information, else exclude, when unpacking tuple
        string += " {2!s}"
    out = [
        string.format(dep, *info)
        for dep, info in dependency_version_paths_mapping.items()
    ]

    if display:
        print("\n".join(out))  # pragma: no cover
    else:
        return out


def CF():
    """The version of the CF conventions.

    This indicates which version of the CF conventions are represented
    by this release of the cfdm.core package, and therefore the
    version can not be changed.

    .. versionadded:: (cfdm) 1.7.0

    :Returns:

        `str`
            The version of the CF conventions represented by this
            release of the cfdm.core package.

    **Examples**

    >>> cfdm.core.CF()
    '1.10'

    """
    return __cf_version__


def deepcopy(x):
    """Use pickle/unpickle to deep copy an object.

    For the types of inputs expected, pickle/unpickle should a) work and
    b) be "not slower, sometimes much faster" than `copy.deepcopy`.

    """
    return loads(dumps(x))
