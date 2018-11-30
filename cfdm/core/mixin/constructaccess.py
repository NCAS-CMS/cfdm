from builtins import object
from future.utils import with_metaclass

import abc


class ConstructAccess(with_metaclass(abc.ABCMeta, object)):
    '''Mixin class for accessing an embedded `Constructs` object.

    '''   
    @abc.abstractmethod
    def _get_constructs(self, *default):
        '''Return the `Constructs` object

:Parameters:

    default: optional
        If set then return *default* if there is no `Constructs` object.

:Returns:

    out:
        The `Constructs` object. If unset then return *default* if provided.

**Examples:**

>>> c = f._get_constructs()
>>> c = f._get_constructs(None)

        '''
        raise NotImplementedError()
    #--- End: def
    
    def array_constructs(self, copy=False):
        return self._get_constructs().array_constructs(copy=copy)
 
    def construct_axes(self, cid=None):
        '''Return the domain axes spanned by metadata construct data arrays.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    cid: `str`
        The identifier of the construct.

:Returns:

    out: `tuple` or `None`

        The identifiers of the domain axes constructs spanned by data
        array of metadata constructs. If a metadata construct does not have a
        data array then `None` is returned.

**Examples:**

>>> f.construct_axes('auxiliarycoordinate0')
('domainaxis1', 'domainaxis0')
>>> print(f.construct_axes('auxiliarycoordinate99'))
None

        '''
        return self._get_constructs().construct_axes(cid=cid)
    #--- End: def
    
    def construct_type(self, cid):
        '''TODO
        '''                
        return self._get_constructs().construct_type(cid)
    #--- End: def
    
    def constructs(self, construct_type=None, copy=False):
        '''Return metadata constructs.

.. versionadded:: 1.7

.. seealso:: `construct_axes`

:Parameters:

    construct_type: TODO

    copy: `bool`, optional
        If `True` then deep copies of the constructs are returned.

:Returns:

    out: `dict`
        TODO

**Examples:**

TODO

        '''
        return self._get_constructs().constructs(construct_type=construct_type,
                                                 copy=copy)
    #--- End: def
    
    @abc.abstractmethod
    def del_construct(self, cid):
        '''Remove a construct.

.. versionadded:: 1.7

.. seealso:: `get_construct`, `constructs`

:Parameters:

    cid: `str`, optional
        The identifier of the construct.

        *Example:*
          ``cid='auxiliarycoordinate0'``
        
:Returns:

    out: 
        The removed construct.

**Examples:**

TODO

        '''
        raise NotImplementedError()
    #--- End: def

    def get_construct(self, cid):
        '''Return a metadata construct.

.. versionadded:: 1.7

:Parameters:

    cid: `str`
        TODO

:Returns:

    out:
        TODO

**Examples:**

>>> f.constructs()
>>> f.get_construct('dimensioncoordinate1')
<>
>>> f.get_construct('dimensioncoordinate99', 'Not set')
'Not set'
        '''
        return self._get_constructs().get_construct(cid)
    #--- End: def

    def get_construct_axes(self, cid, *default):
        '''Return the domain axes spanned by a metadata construct data array.

.. versionadded:: 1.7

.. seealso:: `construct_axes`, `get_construct`, `set_construct_axes`

:Parameters:

    cid: `str`
        The construct identifier of the metadata construct.

        *Example:*
          ``cid='domainancillary1'``

    default: optional
        Return *default* if the metadata construct does not have a
        data array, or no domain axes have been set.

:Returns:

    out:
        The identifiers of the domain axis constructs spanned by data
        array. If a metadata construct does not have a data array, or
        no domain axes have been set, then `None` is returned.

**Examples:**

>>> f.get_construct_axes('domainancillary2')
('domainaxis1', 'domainaxis0')
>>> da = f.get_construct('domainancillary2')
>>> data = da.del_data()
>>> print(f.get_construct_axes('domainancillary2', None))
None

>>> f.get_construct_axes('cellmethod0', 'no axes')
'no axes'

        '''
        axes = self.construct_axes().get(cid)
        if axes is None:
            if default:
                return default[0]

            raise ValueError("no axes.")

        return axes
    #--- End: def
    
    def has_construct(self, cid):
        '''Whether a construct exisits.

.. versionadded:: 1.7

:Parameters:

    cid: `str`
        TODO

:Returns:

    out: `bool`
        True if the construct exists, otherwise False.

**Examples:**

TODO
        '''
        return self._get_constructs().has_construct(cid)
    #--- End: def

    def domain_axis_name(self, axis):
        '''TODO WHY DO WE NED THIS HERE?
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: def
    
    def set_construct(self, construct, cid=None, axes=None,
                      copy=True):
        '''Set a metadata construct.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct_axes`

:Parameters:

    construct:
        The metadata construct to be inserted.

    axes: sequence of `str`, optional
        The construct identifiers of the domain axis constructs
        spanned by the data array. An exception is raised if used for
        a metadata construct that can not have a data array,
        i.e. domain axis, cell method and coordinate reference
        constructs.

        The axes may also be set afterwards with the
        `set_construct_axes` method.

        *Example:*
          ``axes=['domainaxis1']``
        
        *Example:*
          ``axes=['domainaxis1', 'domainaxis0']``
        
    cid: `str`, optional
        The construct identifier to be used for the construct. If not
        set then a new, unique identifier is created automatically. If
        the identifier already exisits then the exisiting construct
        will be replaced.

        *Example:*
          ``cid='cellmeasure0'``

    copy: `bool`, optional
        If True then return a copy of the unique selected
        construct. By default the construct is not copied.
        
:Returns:

     out: `str`
        The construct identifier for the construct.
    
**Examples:**

>>> cid = f.set_construct(c)
>>> cid = f.set_construct(c, copy=False)
>>> cid = f.set_construct(c, axes=['domainaxis2'])
>>> cid = f.set_construct(c, cid='cellmeasure0')

        '''
        return self._get_constructs().set_construct(construct, cid=cid,
                                                    axes=axes,
#                                                    extra_axes=extra_axes,
#                                                    replace=replace,
                                                    copy=copy)
    #--- End: def

    def set_construct_axes(self, cid, axes):
        '''Set the domain axis constructs spanned by a metadata construct data
array.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct`

:Parameters:

    cid: `str`
        The construct identifier of the metadata construct.

        *Example:*
          ``cid='dimensioncoordinate2'``

     axes: sequence of `str`
        The construct identifiers of the domain axis constructs
        spanned by the data array.

        The axes may also be set with the `set_construct` method.

        *Example:*
          ``axes=['domainaxis1']``

        *Example:*
          ``axes=['domainaxis1', 'domainaxis0']``

:Returns:

    `None`

**Examples:**

>>> cid = f.set_construct(c)
>>> f.set_construct_axes(cid, axes=['domainaxis1'])

        '''
        return self._get_constructs().set_construct_axes(cid, axes)
    #--- End: def

#--- End: class
