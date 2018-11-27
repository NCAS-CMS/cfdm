from builtins import (object, str)
from past.builtins import basestring

from collections import OrderedDict


class Constructs(object):
    '''TODO

    '''
    
    def __init__(self, 
                 auxiliary_coordinate=None,                
                 dimension_coordinate=None,         
                 domain_ancillary=None,         
                 field_ancillary=None,         
                 cell_measure=None,
                 coordinate_reference=None,
                 domain_axis=None,
                 cell_method=None,
                 source=None,
                 copy=True,
                 _use_data=True,
                 _view=False,
                 _ignore=()):
        '''TODO
        '''
        self._ignore = tuple(set(_ignore))
    
        if source is not None:
            if _view:
                self._key_base             = source._key_base
                self._array_constructs     = source._array_constructs
                self._non_array_constructs = source._non_array_constructs
                self._ordered_constructs   = source._ordered_constructs
                self._construct_axes       = source._construct_axes
                self._construct_type       = source._construct_type
                self._constructs           = source._constructs
                return
            
            self._key_base             = source._key_base.copy()
            self._array_constructs     = source._array_constructs.copy()
            self._non_array_constructs = source._non_array_constructs.copy()
            self._ordered_constructs   = source._ordered_constructs.copy()
            self._construct_axes       = source._construct_axes.copy()           
            self._construct_type       = source._construct_type.copy()
            self._constructs           = source._constructs.copy()

            for construct_type in self._ignore:
                self._key_base.pop(construct_type, None)
                self._array_constructs.discard(construct_type)
                self._non_array_constructs.discard(construct_type)
                self._ordered_constructs.discard(construct_type)
            
            d = {}            
            for construct_type in source._array_constructs:
                if construct_type in self._ignore:
                    for cid in source._constructs[construct_type]:
                        self._construct_axes.pop(cid, None)
                        self._construct_type.pop(cid, None)
                    continue
                
                if copy:
                    new_v = {}
                    for cid, construct in source._constructs[construct_type].items():
                        new_v[cid] = construct.copy(data=_use_data)
                else:
                    new_v = source._constructs[construct_type].copy()
                    
                d[construct_type] = new_v
            #--- End: for
            
            for construct_type in source._non_array_constructs:
                if construct_type in self._ignore:
                    for cid in source._constructs[construct_type]:
                        self._construct_type.pop(cid, None)
                    continue
                
                if copy:
                    new_v = {}
                    for cid, construct in source._constructs[construct_type].items():
                        new_v[cid] = construct.copy()
                else:
                    new_v = source._constructs[construct_type].copy()

                d[construct_type] = new_v
            #--- End: for
        
            self._constructs = d

            self._ignore = ()
            
            return
        #--- End: if
        
        self._key_base = {}

        self._array_constructs     = set()
        self._non_array_constructs = set()
        self._ordered_constructs   = set()

        self._construct_axes = {}

        # The construct type for each key. For example:
        # {'domainaxis1':'domain_axis', 'aux3':'auxiliary_coordinate'}
        self._construct_type = {}
        
        self._constructs     = {}
        
        if auxiliary_coordinate:
            self._key_base['auxiliary_coordinate'] = auxiliary_coordinate
            self._array_constructs.add('auxiliary_coordinate')
            
        if dimension_coordinate:
            self._key_base['dimension_coordinate'] = dimension_coordinate
            self._array_constructs.add('dimension_coordinate')
            
        if domain_ancillary:
            self._key_base['domain_ancillary'] = domain_ancillary
            self._array_constructs.add('domain_ancillary')
            
        if field_ancillary:
            self._key_base['field_ancillary'] = field_ancillary
            self._array_constructs.add('field_ancillary')

        if cell_measure:
            self._key_base['cell_measure'] = cell_measure
            self._array_constructs.add('cell_measure')

        if domain_axis:
            self._key_base['domain_axis'] = domain_axis
            self._non_array_constructs.add('domain_axis')

        if coordinate_reference:
            self._key_base['coordinate_reference'] = coordinate_reference
            self._non_array_constructs.add('coordinate_reference')

        if cell_method:
            self._key_base['cell_method'] = cell_method
            self._non_array_constructs.add('cell_method')
            self._ordered_constructs.add('cell_method')

        for x in self._array_constructs:
            self._constructs[x] = {}
        
        for x in self._non_array_constructs:
            self._constructs[x] = {}
        
        for x in self._ordered_constructs:
            self._constructs[x] = OrderedDict()
    #--- End: def

    def __call__(self):
        '''TODO
        '''
        return self.constructs()
    #--- End: def
    
    def __deepcopy__(self, memo):
        '''Called by the :py:obj:`copy.deepcopy` standard library function.

.. versionadded:: 1.7

        '''
        return self.copy()
    #--- End: def

    def __repr__(self):
        '''x.__repr__() <==> repr(x)

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        return 'TODO'
    #--- End: def
    
    def construct_type(self, cid):
        '''TODO
        '''
        x = self._construct_type.get(cid)
        if x in self._ignore:
            return
        
        return x
    #--- End: def

    def _construct_type_description(self, construct_type):
        '''TODO
        '''
        return construct_type.replace('_', ' ')
    #--- End: def

    def _set_construct_axes(self, cid, axes):
        '''TODO
        '''
        self._construct_axes[cid] = tuple(axes)
    #--- End: def

    def construct_types(self):
        '''TODO
        '''
        out =  self._construct_type.copy()
        if self._ignore:
            for x in self._ignore:
                del out[x]

        return out
    #--- End: def

    def array_constructs(self, axes=None, copy=False):
        '''TODO
        '''
        out = {}

        if not self._ignore:
            for construct_type in self._array_constructs:
                out.update(self._constructs[construct_type])
        else:
            ignore = self._ignore
            for construct_type in self._array_constructs:
                if construct_type not in ignore:
                    out.update(self._constructs[construct_type])

        if axes:
            spans_axes = set(axes)
            construct_axes = self.construct_axes()
            for cid, construct in list(out.items()):
                x = construct_axes[cid]
                if not spans_axes.intersection(x):
                    del out[cid]
        #--- End: def

        return out
    #--- End: def
    
    def non_array_constructs(self):
        '''TODO
        '''
        out = {}        
        if not self._ignore:
            for construct_type in self._non_array_constructs:
                out.update(self._constructs[construct_type])
        else:
            ignore = self._ignore
            for construct_type in self._non_array_constructs:
                if construct_type not in ignore:
                    out.update(self._constructs[construct_type])

        return out
    #--- End: def

    def _check_construct_type(self, construct_type):
        '''TODO
        '''
        if construct_type is None:
            return None

        x = self._key_base
        if self._ignore:
            x = set(x).difference(self._ignore)
        
        if construct_type not in x:
            raise ValueError(
                "Invalid construct type {!r}. Must be one of {}".format(
                    construct_type, sorted(x)))

        return construct_type    
    #--- End: def
        
    def constructs(self, construct_type=None, copy=False):
        '''Return metadata constructs

Constructs are returned as values of a dictionary, keyed by their
construct identifiers.

.. versionadded:: 1.7

.. seealso:: `del_construct`, `get_construct`, `set_construct`

:Parameters:

    construct_type: (sequence of) `str`, optional
        Select constructs of the given type, or types. Valid types
        are:

          ==========================  ================================
          *construct_type*            Constructs
          ==========================  ================================
          ``'domain_ancillary'``      Domain ancillary constructs
          ``'dimension_coordinate'``  Dimension coordinate constructs
          ``'domain_axis'``           Domain axis constructs
          ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
          ``'cell_measure'``          Cell measure constructs
          ``'coordinate_reference'``  Coordinate reference constructs
          ``'cell_method'``           Cell method constructs
          ``'field_ancillary'``       Field ancillary constructs
          ==========================  ================================

        *Example:*
          ``construct_type='dimension_coordinate'``

        *Example:*
          ``construct_type=['auxiliary_coordinate']``

        *Example:*
          ``construct_type=['domain_ancillary', 'cell_method']``

        Note that a domain never contains cell method nor field
        ancillary constructs.

    copy: `bool`, optional
        If True then return copies of the constructs. By default the
        constructs are not copied.

:Returns:

    out: `dict`

**Examples:**

>>> f.constructs()
TODO

        '''
        if construct_type is not None:
            if isinstance(construct_type, basestring):
                construct_type = (construct_type,)
        #--- End: if
        
#        construct_type = self._check_construct_type(construct_type)

        if construct_type is not None:
            if construct_type == ('cell_method',):
                out = self._constructs[construct_type[0]].copy()
            else:                
                out = {}
                
            for ct in construct_type:
                ct = self._check_construct_type(ct)
                out.update(self._constructs[ct])
            
#            out = self._constructs[construct_type].copy()
        else:
            out = {}
            ignore = self._ignore
            for key, value in self._constructs.items():
                if key not in ignore:
                    out.update(value)
        #--- End: if

        if copy:
            for key, construct in list(out.items()):
                out[key] = construct.copy()
        #--- End: if

        return out
    #--- End: def
    
    def construct_axes(self, cid=None):
        '''TODO

:Parameters:

    cid: `str`, optional

    axes: sequence of `str`, optional

    default: optional

:Returns:

    out: `dict` or `tuple` or *default*

**Examples**

>>> x = f.construct_axes()
>>> f.variable_axes()
{'aux0': ('dim1', 'dim0'),
 'aux1': ('dim0',),
 'aux2': ('dim0',),
 'aux3': ('dim0',),
 'aux4': ('dim0',),
 'aux5': ('dim0',)}
>>> f._axes(key='aux0')
('dim1', 'dim0')
>>> print c.item_axes(key='aux0', new_axes=['dim0', 'dim1'])
None
>>> f._axes(key='aux0')
('dim0', 'dim1')

'''
        if cid is None:
            # Return all of the constructs' axes
            if not self._ignore:
                return self._construct_axes.copy()
            else:
                ignore = self._ignore
                out = {}
                for construct_type, keys in self._constructs.items():
                    if construct_type not in ignore:
                        for key in keys:
                            _ = self._construct_axes.get(key)
                            if _ is not None:
                                out[key] = _
                #--- End: for
                return out
        #--- End: if
        
        # Return a particular construct's axes
        if self._ignore and self.construct_type(cid) is None:
            cid = None

        return self._construct_axes.get(cid)
    #--- End: def


#    def _check_construct_type_of_key(self, key):
#        '''
#        '''
#        construct_type = self.construct_type(key)
#        if construct_type is not None:
#            self._check_construct_type(construct_type, key=key)
#
#        return construct_type

    def set_construct_axes(self, cid, axes):
        '''TODO

.. versionadded:: 1.7
        '''
        if self.construct_type(cid) is None:
            raise ValueError(
                "Can't set axes for non-existent construct identifier: {}".format(cid))

        self._set_construct_axes(cid, axes)
    #--- End: def

    def copy(self, data=True):
        '''Return a deep copy.

``c.copy()`` is equivalent to ``copy.deepcopy(c)``.

:Returns:

    out: `Constructs`
        The copy.

**Examples**

>>> d = c.copy()

        '''
        return type(self)(source=self, copy=True, _view=False,
                          _use_data=data, _ignore=self._ignore)
    #--- End: def

    def axes_to_constructs(self):
        '''TODO

:Returns:

    out: `dict`

**Examples**

>>> print c.axes_to_constructs()
{('domainaxis1',): {
        'auxiliary_coordinate': {'auxiliary_coordinate2': <AuxiliaryCoordinate: greek_letters(10) >},
        'field_ancillary'     : {'fieldancillary2': <FieldAncillary: ncvar%ancillary_data_2(10) >},
        'domain_ancillary'    : {}, 
        'cell_measure'        : {}, 
        'dimension_coordinate': {'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>}
        },
('domainaxis1', 'domainaxis2'): {
        'auxiliary_coordinate': {'auxiliary_coordinate0': <AuxiliaryCoordinate: latitude(10, 9) degree_N>},
        'field_ancillary'     : {'fieldancillary0': <FieldAncillary: ncvar%ancillary_data(10, 9) >},
        'domain_ancillary'    : {'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>},
        'cell_measure'        : {},
        'dimension_coordinate': {}
        },
('domainaxis2', 'domainaxis1'): {
        'auxiliary_coordinate': {'auxiliary_coordinate1': <AuxiliaryCoordinate: longitude(9, 10) degreeE>},
        'field_ancillary'     : {},
        'domain_ancillary'    : {},
        'cell_measure'        : {'cell_measure0': <CellMeasure: area(9, 10) km2>},
        'dimension_coordinate': {}
        },
('domainaxis0',): {
        'auxiliary_coordinate': {},
        'field_ancillary'     : {},
        'domain_ancillary'    : {'domainancillary1': <DomainAncillary: ncvar%b(1) >, 'domainancillary0': <DomainAncillary: ncvar%a(1) m>},
        'cell_measure'        : {},
        'dimension_coordinate': {'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >}
        },
('domainaxis2',): {
        'auxiliary_coordinate': {},
        'field_ancillary'     : {'fieldancillary1': <FieldAncillary: ncvar%ancillary_data_1(9) >},
        'domain_ancillary'    : {},
        'cell_measure'        : {},
        'dimension_coordinate': {'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>}
        }
}

'''
        out = {}

        for axes in list(self.construct_axes().values()):
            d = {}
            for construct_type in self._array_constructs:
                d[construct_type] = {}  #ARRAY CONSTRUCTS SHOULD CONTAIN GENERIC NAME, NOT KEY BASE .....

            out[axes] = d
        #--- End: for

        for key, construct in self.array_constructs().items():
            axes = self.construct_axes(key)
            construct_type = self._construct_type[key]
            out[axes][construct_type][key] = construct

        return out
    #--- End: def

#    def domain_axes(self, copy=False):
#        '''TODO
#
#:Parameters:
#
#    copy: 
#
#**Examples**
#
#>>> d = f.domain_axes()
#>>> d
#{'domainaxis1': <DomainAxis: 106>,
# 'domainaxis0': <DomainAxis: 111>}
#>>> d['domainaxis0'].set_size(73)
#>>> f.domain_axes()
#{'domainaxis1': <DomainAxis: 106>,
# 'domainaxis0': <DomainAxis: 73>}
#
#>>> d['domainaxis0'].set_size(73)
#>>> f.domain_axes()
#{'domainaxis1': <DomainAxis: 106>,
# 'domainaxis0': <DomainAxis: 73>}
#
#>>> d = f.domain_axes(copy=True)
#>>> d
#{'domainaxis1': <DomainAxis: 106>,
# 'domainaxis0': <DomainAxis: 73>}
#>>> d['domainaxis0'].set_size(111)
#>>> f.domain_axes()
#{'domainaxis1': <DomainAxis: 106>,
# 'domainaxis0': <DomainAxis: 73>}
#
#     
#        '''
#        return self.constructs(construct_type='domain_axis', copy=copy)
#    #--- End: def
    
    def get_construct(self, cid):
        '''Return a metadata construct.

Parameters:	

    cid: `str`

:Returns:	

    out:

**Examples**

>>> f.constructs()
>>> f.get_construct('dimensioncoordinate1')
<>
>>> f.get_construct('dimensioncoordinate99', 'Not set')
'Not set'

        '''
        construct_type = self.construct_type(cid)
        if construct_type is None:
            if default:
                return default[0]
            raise ValueError("Can't get construct!!!!!!")
            
        d = self._constructs.get(construct_type)
        if d is None:
            d = {}
            
        try:            
            return d[cid]
        except KeyError:
#            if default:
#                return default[0]
            raise ValueError("Can't get construct!!!!!!")
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
        try:
            self.get_construct(cid)
        except ValueError:
            return False
        else:
            return True        
    #--- End: def

    def set_construct(self, construct, cid=None,
                      axes=None, #extra_axes=0, #replace=True,
                      copy=True):
        '''Set a construct.

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

        '''
#    extra_axes: `int`, optional
#        The number of extra, trailing data array axes that do **not**
#        correspond to a domain axis specified by the *axes*
#        parameter. For example, a coordinate bounds data array may has
#        one or two extra axes. By default it assumed that there are no
#        extra axes.
#
#          *Example:*
#             ``extra_axes=1``

        construct_type = construct.construct_type
        construct_type = self._check_construct_type(construct_type)
                                                
        if cid is None:
            # Create a new construct identifier
            cid = self.new_identifier(construct_type)
#        elif not replace and cid in self._constructs[construct_type]:
#            raise ValueError(
#"Can't set {} construct: Identifier {!r} already exists".format(
#    self._construct_type_description(construct_type), cid))
    
        if construct_type in self._array_constructs:
            #---------------------------------------------------------
            # The construct could have a data array
            #---------------------------------------------------------
            if axes is None:
                raise ValueError(
"Can't set {} construct: Must specify the domain axes for the data array".format(
    self._construct_type_description(construct_type)))

            domain_axes = self.constructs(construct_type='domain_axis')

            axes_shape = []
            for axis in axes:
                if axis not in domain_axes:
                    raise ValueError(                    
"Can't set {!r}: Domain axis {!r} does not exist".format(
    construct, axis))

                axes_shape.append(domain_axes[axis].get_size())
            #--- End: for
            axes_shape = tuple(axes_shape)
            extra_axes=0        
            if (construct.has_data() and 
                construct.data.shape[:construct.data.ndim - extra_axes] != axes_shape):
                raise ValueError(
                    "Can't set {!r}: Data array shape of {!r} does not match the shape required by domain axes {}: {}".format(
    construct, construct.data.shape, tuple(axes), axes_shape))

            self._set_construct_axes(cid, axes)

        elif axes is not None:
            raise ValueError(
"Can't set {!r}: Can't provide domain axis constructs for {} construct".format(
    construct, self._construct_type_description(construct_type)))
        #--- End: if

        # Record the construct type
        self._construct_type[cid] = construct_type

        if copy:
            # Create a deep copy of the construct
            construct = construct.copy()

        # Insert (a copy of) the construct
        self._constructs[construct_type][cid] = construct

        # Return the identifier of the construct
        return cid
    #--- End: def

    def new_identifier(self, construct_type):
        '''Return a new, unique identifier for a construct.

.. versionadded:: 1.7

:Parameters:

    construct_type: `str`

:Returns:

    out: `str`
        The new identifier.

**Examples**

>>> d.items().keys()
['aux2', 'aux0', 'dim1', 'ref2']
>>> d.new_identifier('aux')
'aux3'
>>> d.new_identifier('ref')
'ref1'

>>> d.items().keys()
[]
>>> d.new_identifier('dim')
'dim0'

>>> d.axes()
{'dim0', 'dim4'}
>>> d.new_identifier('axis')
'dim2'

>>> d.axes()
{}
>>> d.new_identifier('axis')
'dim0'

        '''
        keys = self._constructs[construct_type]

        key_base = self._key_base[construct_type]
        key = '{0}{1}'.format(key_base, len(keys))
        while key in keys:
            n += 1
            key = '{0}{1}'.format(key_base, n)

        return key
    #--- End: def

    def del_construct(self, cid):        
        '''Remove a construct.

:Parameters:

   cid: `str`, optional
        The identifier of the construct.

        *Example:*
          ``cid='auxiliarycoordinate0'``
  
:Returns:

    out:
        The removed construct, or `None` if the given key did not
        exist.

**Examples**

>>> x = f.del_construct('auxiliarycoordinate2')
        '''
        self._construct_axes.pop(cid, None)

        construct_type = self._construct_type.pop(cid, None)
        if construct_type is None:
            return

        return self._constructs[construct_type].pop(cid, None)
    #--- End: def

    def replace(self, cid, construct, axes=None, copy=True):
        '''TODO

.. note:: No checks on the axes are done!!!!!
'''
        construct_type = self.construct_types().get(cid)
        if construct_type is None:
            raise ValueError("Can't replace non-existent construct {!r}".format(cid))

        if axes is not None and construct_type in self._array_constructs:        
            self._set_construct_axes(cid, axes)

        if copy:
            construct = construct.copy()
            
        self._constructs[construct_type][cid] = construct
    #--- End: def
    
    def view(self, ignore=()):
        '''TODO
        '''
        return type(self)(source=self, _view=True, _ignore=ignore)
    #--- End: def
    
#--- End: class
