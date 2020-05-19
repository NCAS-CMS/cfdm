from builtins import object
from future.utils import with_metaclass
import abc


class Implementation(with_metaclass(abc.ABCMeta, object)):
    '''Store an implementation of the CF data model.

    '''
    def __init__(self, cf_version=None, **kwargs):
        '''**Initialisation**

    :Parameters:

        kwargs:
            The concrete objects required to represent a Field.

        '''
        self._cf_version = cf_version
        self._class = kwargs.copy()
        for key, value in kwargs.items():
            if value is None:
                del self._class[key]

    def classes(self):
        '''Return all the classes of the implmeentation.

    :Returns:

        `dict`
            The class objects, keyed by their class name.

    **Examples:**

    >>> sorted(i.classes())
    ['AuxiliaryCoordinate',
     'Bounds',
     'CellMeasure',
     'CellMethod',
     'CoordinateConversion',
     'CoordinateReference',
     'Count',
     'Data',
     'Datum',
     'DimensionCoordinate',
     'DomainAncillary',
     'DomainAxis',
     'Field',
     'FieldAncillary',
     'GatheredArray',
     'Index',
     'InteriorRing',
     'List',
     'NetCDFArray',
     'NodeCountProperties',
     'PartNodeCountProperties',
     'RaggedContiguousArray',
     'RaggedIndexedArray',
     'RaggedIndexedContiguousArray']

        '''
        return self._class.copy()

    def copy(self):
        '''Copy

        '''
        return type(self)(cf_version=self.get_cf_version(),
                          **self._class)

    def get_class(self, name):
        '''Return a class of the implementation.

    :Parameters:

        name: `str`
            The name of the class.

            *Parameter example:*
              ``name='Field'``

    :Returns:

            The class object.

    **Examples:**

    >>> Field = i.get_class('Field')
    >>> f = Field()

        '''
        try:
            return self._class[name]
        except KeyError:
            raise ValueError(
                "Implementation does not have class {!r}".format(name))

    def get_cf_version(self):
        '''Return the CF version of the implementation.

    :Returns:

        `str`
            The version.

    **Examples:**

    >>> i.get_cf_version()
    '1.8'

        '''
        return self._cf_version

    def set_class(self, name, cls):
        '''Set a class of the implementation.

    :Parameters:

        name: `str`
            The name of the class.

            *Parameter example:*
              ``name='Field'``

        cls:
            The class object.

    :Returns:

        `None`

    **Examples:**

    >>> from . import Field
    >>> i.set_class('Field', Field)
    >>> field_class = i.get_class('Field')
    >>> f = field_class()

        '''
        self._class[name] = cls

# --- End: class
