from builtins import super

from . import abstract
#from future.utils import with_metaclass


class CellMeasure(abstract.PropertiesData):
#    class CellMeasure(with_metaclass(abc.ABCMeta, abstract.PropertiesData)):
    '''A cell measure construct of the CF data model.

A cell measure construct provides information that is needed about the
size or shape of the cells and that depends on a subset of the domain
axis constructs. Cell measure constructs have to be used when the size
or shape of the cells cannot be deduced from the dimension or
auxiliary coordinate constructs without special knowledge that a
generic application cannot be expected to have.

The cell measure construct consists of a numeric array of the metric
data which spans a subset of the domain axis constructs, and
properties to describe the data. The cell measure construct specifies
a "measure" to indicate which metric of the space it supplies,
e.g. cell horizontal areas, and must have a units property consistent
with the measure, e.g. square metres. It is assumed that the metric
does not depend on axes of the domain which are not spanned by the
array, along which the values are implicitly propagated. CF-netCDF
cell measure variables correspond to cell measure constructs.

    '''
    def __init__(self, measure=None, properties=None, data=None,
                 source=None, copy=True, _use_data=True):
        '''**Initialisation**

:Parameters:

    measure: `str`, optional
        Set the measure that indicates which metric given by the data
        array. Ignored if the *source* parameter is set.

          *Example:*
             ``measure='area'``
        
        The measure may also be set after initialisation with the
        `set_measure` method.

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

          *Example:*
             ``properties={'units': 'metres 2'}``
        
        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.

    data: `Data`, optional
        Set the data array. Ignored if the *source* parameter is set.
        
        The data array also may be set after initialisation with the
        `set_data` method.

    source: optional
        Initialise the *measure*, *properties* and *data* parameters
        (if present) from *source*, which will be a `CellMeasure`
        object, or a subclass of one of its parent classes.

          *Example:*
            >>> d = CellMeasure(source=c)

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization By default parameters are deep copied.

**Examples**

>>> c = CellMeasure(measure='area'
...                 properties={'units': 'km 2'},
...                 data=d)

        '''
        super().__init__(properties=properties, source=source,
                         data=data, copy=copy, _use_data=_use_data)

        if source is not None:
            try:
                measure = source.get_measure(None)
            except AttributeError:
                measure = None
        #--- End: if
                
        if measure is not None:
            self.set_measure(measure)
    #--- End: def
    
    @property
    def construct_type(self):
        '''Return a description of the construct type.
        
.. versionadded:: 1.7
        
:Returns:

    out: `str`
        The construct type.

        '''
        return 'cell_measure'
    #--- End: def
        
    def del_measure(self, *default):
        '''Remove the measure.

.. versionadded:: 1.7

.. seealso:: `get_measure`, `has_measure`, `properties`, `set_measure`

:Parameters:

    default: optional
        Return *default* if the property has not been set.

:Returns:

     out:
        The removed measure. If unset then *default* is returned, if
        provided.

**Examples**

TODO

        '''
        return self._del_component('measure')
    #--- End: def

    def has_measure(self):
        '''TODO
        '''
        return self._has_component('measure')
    #--- End: def

    def get_measure(self, *default):
        '''TODO
        '''
        return self._get_component('measure', *default)
    #--- End: def

    def set_measure(self, measure, copy=True):
        '''TODO
        '''
        return self._set_component('measure', measure, copy=copy)
    #--- End: def

#--- End: class
