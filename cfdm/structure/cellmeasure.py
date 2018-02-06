import abc

import abstract


# ====================================================================
#
# CellMeasure object
#
# ====================================================================

class CellMeasure(abstract.PropertiesData):
    '''A cell measure construct of the CF data model.

A cell measure construct provides information that is needed about the
size or shape of the cells and that depends on a subset of the domain
axis constructs. Cell measure constructs have to be used when the size
or shape of the cells cannot be deduced from the dimension or
auxiliary coordinate constructs without special knowledge that a
generic application cannot be expected to have. The cell measure
construct consists of a numeric array of the metric data which spans a
subset of the domain axis constructs, and properties to describe the
data (in the same sense as for the field construct). The properties
must contain a "measure" property, which indicates which metric of the
space it supplies e.g. cell horizontal areas, and a units property
consistent with the measure property e.g. square metres. It is assumed
that the metric does not depend on axes of the domain which are not
spanned by the array, along which the values are implicitly
propagated. CF-netCDF cell measure variables correspond to cell
measure constructs.

    '''   
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, measure=None, properties={}, data=None,
                 source=None, copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Initialize properties from the dictionary's key/value pairs.

    data: `Data`, optional
        Provide a data array.
        
    source: `{+Variable}`, optional
        Take the attributes, CF properties and data array from the
        source {+variable}. Any attributes, CF properties or data
        array specified with other parameters are set after
        initialisation from the source {+variable}.

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        super(CellMeasure, self).__init__(properties=properties,
                                          source=source, data=data,
                                          copy=copy, _use_data=_use_data)

        if source is not None:
            if measure is None:
                measure = source.get_measure(None)
        
        if measure is not None:
            self.set_measure(measure)
    #--- End: def

    def del_measure(self):
        '''
        '''
        return self._del_attribute('measure')
    #--- End: def

    def has_measure(self):
        '''
        '''
        return self._has_attribute('measure')
    #--- End: def

    def get_measure(self, *default):
        '''
        '''
        return self._get_attribute('measure', *default)
    #--- End: def

    def set_measure(self, measure):
        '''
        '''
        return self._set_attribute('measure', measure)
    #--- End: def

#--- End: class
