from collections.abc import Iterable

from ...cfdmimplementation import implementation
from ...core import DocstringRewriteMeta
from ...docstring import _docstring_substitution_definitions


class ReadWrite(metaclass=DocstringRewriteMeta):
    """TODOCFA."""

    implementation = implementation()

    def __docstring_substitutions__(self):
        """Defines applicable docstring substitutions.

        Substitutons are considered applicable if they apply to this
        class as well as all of its subclasses.

        These are in addtion to, and take precendence over, docstring
        substitutions defined by the base classes of this class.

        See `_docstring_substitutions` for details.

        .. versionaddedd:: (cfdm) 1.12.0.0

        :Returns:

            `dict`
                The docstring substitutions that have been applied.

        """
        return _docstring_substitution_definitions

    def __docstring_package_depth__(self):
        """Returns the package depth for {{package}} substitutions.

        See `_docstring_package_depth` for details.

        .. versionaddedd:: (cfdm) 1.12.0.0

        """
        return 0

    @classmethod
    def _flat(cls, x):
        """Return an iterator over an arbitrarily nested sequence.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            x: scalar or arbitrarily nested sequence
                The arbitrarily nested sequence to be flattened. Note
                that if *x* is a string or a scalar then this is
                equivalent to passing a single element sequence
                containing *x*.

        :Returns:

            generator
                An iterator over the flattened sequence.

        **Examples**

        >>> list({{package}}.write._flat([1, (2, [3, 4])]))
        [1, 2, 3, 4]

        >>> list({{package}}.write._flat(['a', ['bc', ['def', 'ghij']]]))
        ['a', 'bc', 'def', 'ghij']

        >>> list({{package}}.write._flat(2004))
        [2004]

        """
        if not isinstance(x, Iterable) or isinstance(x, str):
            x = (x,)

        for a in x:
            if not isinstance(a, str) and isinstance(a, Iterable):
                for sub in cls._flat(a):
                    yield sub
            else:
                yield a
