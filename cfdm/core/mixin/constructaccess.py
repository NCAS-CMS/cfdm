from builtins import object
#from future.utils import with_metaclass

#import abc


#class ConstructAccess(with_metaclass(abc.ABCMeta, object)):
class ConstructAccess(object):
    '''Mixin class for accessing an embedded `Constructs` object.

.. versionadded:: 1.7.0

    '''   
    def data_constructs(self, copy=False):
        '''Return metadata constructs that support data arrays.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    `dict`
        Constructs are returned as values of a dictionary, keyed by
        their construct identifiers.

**Examples:**

>>> f.constructs()
TODO
>>> f.data_constructs()
TODO

        '''
        return self.constructs.data_constructs(copy=copy)
    #-- End: def
    
    def del_construct(self, key, default=ValueError()):
        '''Remove a metadata construct.

If a domain axis construct is selected for removal then it can't be
spanned by any metdata construct data, nor the field construct's
data; nor be referenced by any cell method constructs.

However, a domain ancillary construct may be removed even if it is
referenced by coordinate reference construct. In this case the
reference is replace with `None`.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `get_construct`, `has_construct`,
             `set_construct`

:Parameters:

    key: `str`, optional
        The key of the metadata construct to be removed.

        *Parameter example:*
          ``key='auxiliarycoordinate0'``
        
    default: optional
        Return the value of the *default* parameter if the construct
        can not be removed, or does not exist. If set to an
        `Exception` instance then it will be raised instead.

:Returns:

        The removed metadata construct.

**Examples:**

>>> f.del_construct('dimensioncoordinate1')
<DimensionCoordinate: grid_latitude(111) degrees>

        '''
        return self.constructs._del_construct(key, default=default)
    #--- End: def

    def get_construct(self, key, default=ValueError()):
        '''Return a metadata construct.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `del_construct`, `has_construct`,
             `set_construct`

:Parameters:

    key: `str`
        The key of the metadata construct.

        *Parameter example:*
          ``key='domainaxis1'``

    default: optional
        Return the value of the *default* parameter if the construct
        does not exist. If set to an `Exception` instance then it will
        be raised instead.

:Returns:

        The metadata construct.

**Examples:**

>>> f.constructs()
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degree_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degreeE>,
 'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name:greek_letters(10) >,
 'coordinatereference1': <CoordinateReference: rotated_latitude_longitude>,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
 'domainaxis1': <DomainAxis: 10>,
 'domainaxis2': <DomainAxis: 9>}
>>> f.get_construct('dimensioncoordinate1')
<DimensionCoordinate: grid_latitude(10) degrees>

        '''
        return self.constructs.filter_by_key(key).value(default=default)
    #--- End: def

    def domain_axis_name(self, axis):
        '''TODO WHY DO WE NED THIS HERE?

.. versionadded:: 1.7.0

        '''
        return self.constructs.domain_axis_name(axis)
    #--- End: def
    
    def set_construct(self, construct, key=None, axes=None,
                      copy=True):
        '''Set a metadata construct.

.. versionadded:: 1.7.0

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct_data_axes`

:Parameters:

    construct:
        The metadata construct to be inserted.

    key: `str`, optional
        The construct identifier to be used for the construct. If not
        set then a new, unique identifier is created automatically. If
        the identifier already exisits then the exisiting construct
        will be replaced.

        *Parameter example:*
          ``key='cellmeasure0'``

    axes: (sequence of) `str`, optional
        The construct identifiers of the domain axis constructs
        spanned by the data array. An exception is raised if used for
        a metadata construct that can not have a data array,
        i.e. domain axis, cell method and coordinate reference
        constructs.

        *Parameter example:*
          ``axes='domainaxis1'``
        
        *Parameter example:*
          ``axes=['domainaxis1']``
        
        *Parameter example:*
          ``axes=['domainaxis1', 'domainaxis0']``
        
    copy: `bool`, optional
        If True then return a copy of the unique selected
        construct. By default the construct is not copied.
        
:Returns:

     `str`
        The construct identifier for the construct.
    
**Examples:**

>>> key = f.set_construct(c)
>>> key = f.set_construct(c, copy=False)
>>> key = f.set_construct(c, axes='domainaxis2')
>>> key = f.set_construct(c, key='cellmeasure0')

        '''
        return self.constructs._set_construct(construct, key=key,
                                              axes=axes, copy=copy)
    #--- End: def

#    def set_construct_data_axes(self, key, axes):
#        '''Set the domain axis constructs spanned by a metadata construct data
#array.
#
#.. versionadded:: 1.7.0
#
#.. seealso:: `constructs`, `del_construct`, `get_construct`,
#             `set_construct`
#
#:Parameters:
#
#    key: `str`
#        The construct identifier of the metadata construct.
#
#        *Parameter example:*
#          ``key='dimensioncoordinate2'``
#
#     axes: (sequence of) `str`
#        The construct identifiers of the domain axis constructs
#        spanned by the data array.
#
#        The axes may also be set with the `set_construct` method.
#
#        *Parameter example:*
#          ``axes='domainaxis1'``
#
#        *Parameter example:*
#          ``axes=['domainaxis1']``
#
#        *Parameter example:*
#          ``axes=['domainaxis1', 'domainaxis0']``
#
#:Returns:
#
#    `None`
#
#**Examples:**
#
#>>> key = f.set_construct(c)
#>>> f.set_construct_data_axes(key, axes='domainaxis1')
#
#        '''
#        return self.constructs._set_construct_data_axes(key, axes)
#    #--- End: def

#--- End: class
