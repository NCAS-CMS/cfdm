from __future__ import print_function
from builtins import (super, zip)
from past.builtins import basestring

import textwrap
from copy import deepcopy

from . import core


class Constructs(core.Constructs):
    '''A container for metadata constructs.

.. versionadded:: 1.7.0

    ''' 
       
    def __call__(self, *identities):
        '''Select metadata constructs by identity.

Calling a `Constructs` instance is an alias for `filter_by_identity`,
so see that method method for details.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_identity`

:Parameters:

    identities: optional
        See `filter_by_identity` for details.

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

>>> c('latitude')
Constructs:
{'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>}
>>> c.filter_by_identity('latitude')
Constructs:
{'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>}

 See `filter_by_identity` for more examples.

        '''
        return self.filter_by_identity(*identities)
    #--- End: def
    
    def __repr__(self):
        '''Called by the `repr` built-in function.

x.__repr__() <==> repr(x)

.. versionadded:: 1.7.0

        '''
        construct_types = ['{0}({1})'.format(c, len(v))
                           for c, v in sorted(self._constructs.items())
                           if len(v) and c not in self._ignore]    
        
        return '<{0}: {1}>'.format(self.__class__.__name__, ', '.join(construct_types))
    #--- End: def

    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

.. versionadded:: 1.7.0

        '''
        out = ['Constructs:']

        construct_types = [c
                           for c, v in sorted(self._constructs.items())
                           if len(v) and c not in self._ignore]    

        first = '{'
        for construct_type in construct_types:
            for key, value in sorted(self._constructs[construct_type].items()):
                if first:
                    out[0] = out[0] + '\n{{{!r}: {!r},'.format(key, value)
                    first = False
                else:
                    out.append('{!r}: {!r},'.format(key, value))
        #--- End: for
        
        if first:
            out[0] = out[0] + '\n{}'
        else:
            out[-1] = out[-1][:-1] + '}'

        return '\n '.join(out)
    #--- End: def

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _axes_to_constructs(self):
        '''Map domain axis constructs to the metadata constructs whose data
span them.

This is useful for ascertaining whether or not two `Constructs`
instances are equal.

.. versionadded:: 1.7.0

:Returns:

    `dict`

**Examples:**

>>> f.constructs._axes_to_constructs()
{('domainaxis0',): {'auxiliary_coordinate': {},
                    'cell_measure'        : {},
                    'dimension_coordinate': {'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >},
                    'domain_ancillary'    : {'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
                                             'domainancillary1': <DomainAncillary: ncvar%b(1) >},
                    'field_ancillary'     : {}},
 ('domainaxis1',): {'auxiliary_coordinate': {'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name=Grid latitude name(10) >},
                    'cell_measure'        : {},
                    'dimension_coordinate': {'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>},
                    'domain_ancillary'    : {},
                    'field_ancillary'     : {}},
 ('domainaxis1', 'domainaxis2'): {'auxiliary_coordinate': {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>},
                                  'cell_measure'        : {},
                                  'dimension_coordinate': {},
                                  'domain_ancillary'    : {'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>},
                                  'field_ancillary'     : {'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}},
 ('domainaxis2',): {'auxiliary_coordinate': {},
                    'cell_measure'        : {},
                    'dimension_coordinate': {'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>},
                    'domain_ancillary'    : {},
                    'field_ancillary'     : {}},
 ('domainaxis2', 'domainaxis1'): {'auxiliary_coordinate': {'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>},
                                  'cell_measure'        : {'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>},
                                  'dimension_coordinate': {},
                                  'domain_ancillary'    : {},
                                  'field_ancillary'     : {}},
 ('domainaxis3',): {'auxiliary_coordinate': {},
                    'cell_measure'        : {},
                    'dimension_coordinate': {'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >},
                    'domain_ancillary'    : {},
                    'field_ancillary'     : {}}}

        '''
        out = {}


        data_axes = self.data_axes()
        
        for axes in data_axes.values():
            d = {construct_type: {}
                 for construct_type in self._array_constructs
                 if construct_type not in self._ignore}

            out[axes] = d
        #--- End: for

        for cid, construct in self.filter_by_data().items():
            axes = data_axes.get(cid)
            construct_type = self._construct_type[cid]
            out[axes][construct_type][cid] = construct

        return out
    #--- End: def

    def _equals_cell_method(self, other, rtol=None, atol=None,
                            verbose=False, ignore_type=False,
                            axis1_to_axis0=None, key1_to_key0=None):
        '''

        '''
        cell_methods0 = self.filter_by_type('cell_method') #.ordered()
        cell_methods1 = other.filter_by_type('cell_method') #.ordered()

        if len(cell_methods0) != len(cell_methods1):
            if verbose:
                print(
"Verbose: Different numbers of cell methods: {0!r} != {1!r}".format(
    cell_methods0, cell_methods1))
            return False

        if not len(cell_methods0):
            return True    

        cell_methods0 = cell_methods0.ordered()
        cell_methods1 = cell_methods1.ordered()

        axis0_to_axis1 = {axis0: axis1
                          for axis0, axis1 in axis1_to_axis0.items()}

        for cm0, cm1 in zip(tuple(cell_methods0.values()),
                            tuple(cell_methods1.values())):
            # Check that there are the same number of axes
            axes0 = cm0.get_axes(())
            axes1 = list(cm1.get_axes(()))
            if len(axes0) != len(axes1):
                if verbose:
                    print(
"{0}: Different cell methods (mismatched axes):\n  {1}\n  {2}".format(
    cm0.__class__.__name__, ccell_methods0.ordered(), cell_methods1.ordered()))
                return False
    
            indices = []
            for axis0 in axes0:
                if axis0 is None:
                    return False
                for axis1 in axes1:
                    if axis0 in axis0_to_axis1 and axis1 in axis1_to_axis0:
                        if axis1 == axis0_to_axis1[axis0]:
                            # axis0 and axis1 are domain axis
                            # constructs that correspond to each other
                            axes1.remove(axis1)
                            indices.append(cm1.get_axes(()).index(axis1))
                            break
                    elif axis0 in axis0_to_axis1 or axis1 in axis1_to_axis0:
                        # Only one of axis0 and axis1 is a domain axis
                        # construct
                        if verbose:
                            print(
"{0}: Different cell methods (mismatched axes):\n  {1}\n  {2}".format(
    cm0.__class__.__name__, cell_methods0, cell_methods1))

                        return False
                    elif axis0 == axis1:
                        # axes0 and axis 1 are identical standard
                        # names
                        axes1.remove(axis1)
                        indices.append(cm1.get_axes(()).index(axis1))
                    elif axis1 is None:
                        # axis1 
                        if verbose:
                            print(
"{0}: Different cell methods (mismatched axes):\n  {1}\n  {2}".format(
    cm0.__class__.__name__, cell_methods0, cell_methods1))
                        return False
            #--- End: for

            if len(cm1.get_axes(())) != len(indices):
                if verbose:
                    print("{0}: Different cell methods:\n  {1}\n  {2}".format(
                        cm0.__class__.__name__, cell_methods0, cell_methods1))
                return False

            cm1 = cm1.sorted(indices=indices)
            cm1.set_axes(axes0)

            if not cm0.equals(cm1, atol=atol, rtol=rtol,
                              verbose=verbose,
                              ignore_type=ignore_type):
                if verbose:
                    print(
"Verbose: Different cell methods: {0!r}, {1!r}".format(
    cell_methods0, cell_methods1))
                return False                
        #--- End: for

        return True
    #--- End: def

    def _equals_coordinate_reference(self, other, rtol=None,
                                     atol=None, verbose=False,
                                     ignore_type=False,
                                     axis1_to_axis0=None,
                                     key1_to_key0=None):
        '''
        '''
        refs0 = dict(self.filter_by_type('coordinate_reference'))
        refs1 = dict(other.filter_by_type('coordinate_reference'))

        if len(refs0) != len(refs1):
            if verbose:
                print("{0}: Different numbers of {1} constructs: {2} != {3}".format(
                    self.__class__.__name__, 'coordinate reference',
                    len(refs0), len(refs1)))
                return False

        if refs0:
            for ref0 in refs0.values():
                found_match = False
                for key1, ref1 in tuple(refs1.items()):
                    if not ref0.equals(ref1, rtol=rtol, atol=atol,
                                       verbose=False,
                                       ignore_type=ignore_type):
                        continue

                    # Coordinates
                    coordinates0 = ref0.coordinates()
                    coordinates1 = set()
                    for value in ref1.coordinates():
                        coordinates1.add(key1_to_key0.get(value, value))
                        
                    if coordinates0 != coordinates1:
                        continue
    
                    # Domain ancillary-valued coordinate conversion terms
                    terms0 = ref0.coordinate_conversion.domain_ancillaries()

                    terms1 = {term: key1_to_key0.get(key, key)
                              for term, key in ref1.coordinate_conversion.domain_ancillaries().items()}

                    if terms0 != terms1:
                        continue
    
                    found_match = True
                    del refs1[key1]                                       
                    break
                #--- End: for
    
                if not found_match:
                    if verbose:
                        print("{0}: No match for {1!r})".format(
                            self.__class__.__name__, ref0))
                    return False
            #--- End: for
        #--- End: if

        return True
    #--- End: def

    def _equals_domain_axis(self, other, rtol=None, atol=None,
                            verbose=False, ignore_type=False,
                            axis1_to_axis0=None, key1_to_key0=None):
        '''
        '''
        self_sizes  = [d.get_size()
                       for d in self.filter_by_type('domain_axis').values()]
        other_sizes = [d.get_size()
                       for d in other.filter_by_type('domain_axis').values()]
      
        if sorted(self_sizes) != sorted(other_sizes):
            # There is not a 1-1 correspondence between axis sizes
            if verbose:
                print("{0}: Different domain axis sizes: {1} != {2}".format(
                    self.__class__.__name__,
                    sorted(self_sizes), sorted(other_sizes)))
            return False

        return True
    #--- End: def
    
    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self, data=True):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.7.0

:Parameters:

    data: `bool`, optional
        If False then do not copy data contained in the metadata
        constructs. By default such data are copied.

:Returns:

        The deep copy.

**Examples:**

>>> g = f.copy()
>>> g = f.copy(data=False)

        '''
        out = super().copy(data=data)

        prefiltered = getattr(self, '_prefiltered', None)
        if prefiltered is not None:
            out._prefiltered = prefiltered.copy(data=data)
            out._filters_applied = self._filters_applied
            
        return out
    #--- End: def

#    def domain_axis_key(self, identity, default=ValueError()):
#        '''Return the key of domain axis construct that is spanned by a unique 1-d
#coordinate construct.
#
#:Parameters:
#
#    identity:
#        Select the domain axis construct that is spanned by the unique
#        1-d coordinate construct that has the given identity.
#
#        An identity is specified by a string (e.g. ``'latitude'``,
#        ``'long_name=time'``, etc.); or a compiled regular expression
#        (e.g. ``re.compile('^atmosphere')``), for which all constructs
#        whose identities match (via `re.search`) are selected.
#
#        Each construct has a number of identities that are returned by
#        its `!identities` method. In addition, each construct also has
#        an identity based its construct key
#        (e.g. ``'key%dimensioncoordinate2'``).
#
#        Note that the identifiers of a metadata construct in the
#        output of a `print` or `!dump` call are always one of its
#        identities, and so may always be used as an *identity*
#        argument.
#
#    default: optional
#        Return the value of the *default* parameter if a domain axis
#        construct can not be found. If set to an `Exception` instance
#        then it will be raised instead.
#
#:Returns:
#
#    `DomainAxis`
#        The domain axis constructs that is spanned by the sevlected
#        coordinate construct.
#
#**Examples:**
#
#>>> c.ilter_by_type('dimension_coordinate', 'auxiliary_coordinates')
#Constructs:
#{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
# 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
# 'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name=Grid latitude name(10) >,
# 'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
# 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
# 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
# 'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >}
#>>> c.domain_axis('grid_latitude'))
#<DomainAxis: size(10)>
#>>> c.domain_axis(re.compile('^tim'))
#<DomainAxis: size(1)>
#
#        '''
#        constructs_data_axes = self.data_axes()
#
#        c = self.filter_by_type('dimension_coordinate',
#                                'auxiliary_coordinates')
#        c = c.filter_by_naxes(1)
#        c = c.filter_by_identity(identity)
#        
#        if not len(c) :
#            return self._default(
#                default,
#                "No 1-d coordinate constructs have identity {!r}".format(identity))
#
#        if len(c) > 1:
#            return self._default(
#                default,
#                "Multiple 1-d coordinate constructs have identity {!r}".format(
#                    len(c),
#                    identity))
#
#        ckey, coord = dict(c).popitem()
#        axes = constructs_data_axes.get(ckey)
#        
#        if not axes:
#            return self._default(
#                default,
#                "{!r} has no domain axis contruct".format(coord))
#        
#        key = axes[0]
#        out = self.filter_by_type('domain_axis').get(key)
#        if not out:
#            return self._default(
#                default,
#                "Domain axis construct with key {!r} does not exist".format(
#                    key))
#        
#        return key
#    #--- End: def

    def domain_axis_identity(self, key):
        '''Return the canonical identity for an domain axis construct.

The identity is the first found of the following:

1. The canonical identity of a dimension coordinate contruct that span
   the domain axis construct.
2. The identity of a one-dimensional auxiliary coordinate construct
   that spans the domain axis construct. This will either be the value
   of a "standard_name", "cf_role" (preceeded by ``'cf_role='``) or
   "axis" (preceeded by ``'axis='``) property, as appropriate.
3. The netCDF dimension name, preceeded by 'ncdim%'.
4. The domain axis construct key, preceeded by 'key%'.

:Parameters:

    key: `str`
        The construct key for the domain axis construct.

        *Parameter example:*
          ``key='domainaxis2'``

:Returns:

    `str`
        The identity.

**Examples:**

>>> c.domain_axis_identity('domainaxis1')
'longitude'
>>> c.domain_axis_identity('domainaxis2')
'axis=Y'
>>> c.domain_axis_identity('domainaxis3')
'cf_role=timeseries_id'
>>> c.domain_axis_identity('domainaxis4')
'key%domainaxis4')

        '''
        domain_axes = self.filter_by_type('domain_axis')
        
        if key not in domain_axes:
            raise ValueError(
                'No domain axis construct with key {!r}'.format(key))

        constructs_data_axes = self.data_axes()

        # Try to get the identity from an dimension coordinate
        identity = ''
        for dkey, dim in self.filter_by_type('dimension_coordinate').items():
            if constructs_data_axes.get(dkey) == (key,):
                identity = dim.identity()
                if identity.startswith('ncvar%'):
                    identity = ''
                
                break
        #--- End: for
        if identity:
            return identity

        # Try to get the identity from an auxiliary coordinate
        identities = []
        for akey, aux in self.filter_by_type('auxiliary_coordinate').items():
            if constructs_data_axes.get(akey) == (key,):
                identity = aux.identity()
                if not identity.startswith('ncvar%'):
                    identities.append(identity)
        #--- End: for

        if len(identities) == 1:
            return identities[0]
        elif len(identities) > 1:
            cf_role = []
            axis = []
            for i in identities:
                if i.startswith('axis='):
                    axis.append(i)
                elif i.startswith('cf_role='):
                    cf_role.append(i)
            #--- End: for
            
            if len(cf_role) == 1:
                return cf_role[0]
            
            if len(axis) == 1:
                return axis[0]
        #--- End: if

        # Try to get the identity from an netCDF dimension name
        ncdim = domain_axes[key].nc_get_dimension(None)
        if ncdim is not None:
            return 'ncdim%{0}'.format(ncdim)

        # Get the identity from the domain axis construct key
        return 'key%{0}'.format(key)
    #--- End: def

    def equals(self, other, rtol=None, atol=None, verbose=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_compression=False, _ignore_type=False):
        '''Whether two `Constructs` instances are the same.

Two real numbers ``x`` and ``y`` are considered equal if
``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
differences) and ``rtol`` (the tolerance on relative differences) are
positive, typically very small numbers. See the *atol* and *rtol*
parameters.

If data arrays are compressed then the compression type and the
underlying compressed arrays must be the same, as well as the arrays
in their uncompressed forms. See the *ignore_compression* parameter.

Any type of object may be tested but equality is only possible with
another `Constructs` construct, or a subclass of one.

NetCDF elements, such as netCDF variable and dimension names, do not
constitute part of the CF data model and so are not checked on any
construct.

.. versionadded:: 1.7.0

:Parameters:

    other: 
        The object to compare for equality.

    atol: float, optional
        The tolerance on absolute differences between real
        numbers. The default value is set by the `cfdm.ATOL` function.
        
    rtol: float, optional
        The tolerance on relative differences between real
        numbers. The default value is set by the `cfdm.RTOL` function.

    ignore_fill_value: `bool`, optional
        If True then the "_FillValue" and "missing_value" properties
        are omitted from the comparison for the metadata constructs.

    verbose: `bool`, optional
        If True then print information about differences that lead to
        inequality.

    ignore_data_type: `bool`, optional
        If True then ignore the data types in all numerical
        comparisons. By default different numerical data types imply
        inequality, regardless of whether the elements are within the
        tolerance for equality.

    ignore_compression: `bool`, optional
        If True then any compression applied to underlying arrays is
        ignored and only uncompressed arrays are tested for
        equality. By default the compression type and, if applicable,
        the underlying compressed arrays must be the same, as well as
        the arrays in their uncompressed forms

:Returns: 
  
    `bool`
        Whether the two instances are equal.

**Examples:**

>>> x.equals(x)
True
>>> x.equals(x.copy())
True
>>> x.equals('something else')
False

        '''
        if self is other:
            return True
        
        # Check that each instance is the same type
        if  not isinstance(other, self.__class__):
            if verbose:
                print("{0}: Incompatible type: {1}".format(
                    self.__class__.__name__, other.__class__.__name__))
            return False
        
        axes0_to_axes1 = {}
        axis0_to_axis1 = {}
        axis1_to_axis0 = {}
        key1_to_key0   = {}
        
        # ------------------------------------------------------------
        # Domain axis constructs
        # ------------------------------------------------------------
        if not self._equals_domain_axis(other, rtol=rtol, atol=atol,
                                        verbose=verbose,
                                        ignore_type=_ignore_type,
                                        axis1_to_axis0=axis1_to_axis0,
                                        key1_to_key0=key1_to_key0):
            return False
        
        # ------------------------------------------------------------
        # Constructs with arrays
        # ------------------------------------------------------------
        log = []
        axes_to_constructs0 = self._axes_to_constructs()
        axes_to_constructs1 = other._axes_to_constructs()
        for axes0, constructs0 in axes_to_constructs0.items():
            matched_all_constructs_with_these_axes = False

             
            len_axes0 = len(axes0) 
            for axes1, constructs1 in tuple(axes_to_constructs1.items()):

                constructs1 = constructs1.copy()

                if len_axes0 != len(axes1):
                    # axes1 and axes0 contain different number of
                    # domain axes.
                    continue

                for construct_type in self._array_constructs:
#                    role_constructs0 = constructs0[construct_type]
#                    role_constructs1 = constructs1[construct_type].copy()
                    role_constructs0 = constructs0.get(construct_type, {})
                    role_constructs1 = constructs1.get(construct_type, {}).copy()
                    
                    if len(role_constructs0) != len(role_constructs1):
                        # There are the different numbers of
                        # constructs of this type
                        matched_all_constructs_with_these_axes = False
                        log.append("{0}: Different numbers of {1} constructs: {2} != {3}".format(
                            self.__class__.__name__, construct_type,
                            len(role_constructs0), len(role_constructs1)))
                        break
#                    elif not role_constructs0:
#                        break

                    # Check that there are matching pairs of equal
                    # constructs
                    matched_construct = True
                    for key0, item0 in role_constructs0.items():
                        matched_construct = False
                        for key1, item1 in tuple(role_constructs1.items()):
                            if item0.equals(item1,
                                            rtol=rtol, atol=atol,
                                            verbose=False,
                                            ignore_data_type=ignore_data_type,
                                            ignore_fill_value=ignore_fill_value,
                                            ignore_compression=ignore_compression,
                                            ignore_type=_ignore_type):
                                del role_constructs1[key1]
                                key1_to_key0[key1] = key0
                                matched_construct = True
                                break
                        #--- End: for

                        if not matched_construct:
                            log.append("{0}: Can't match {1!r}".format(
                                self.__class__.__name__, item0))
                            break
                    #--- End: for

                    if role_constructs1:
                        # At least one construct in other is not equal
                        # to a construct in self
                        break

                    # Still here? Then all constructs of this type
                    # that spanning these axes match
#                    del constructs1[construct_type]
                    constructs1.pop(construct_type, None)
                #--- End: for

                matched_all_constructs_with_these_axes = not constructs1
                if matched_all_constructs_with_these_axes:
                    del axes_to_constructs1[axes1]
                    break
            #--- End: for

            if not matched_all_constructs_with_these_axes:
                if verbose:
                    names = [self.domain_axis_identity(axis0) for axis0 in axes0]
                    print("{0}: Can't match constructs spanning axes {1}".format(
                        self.__class__.__name__, names))
                    if log:
                        print('\n'.join(log))
#                    print()
##                    print(axes_to_constructs0)
#                    print(self)
#                    print()
##                    print(axes_to_constructs1)
#                    print(other)
                return False

            # Map item axes in the two instances
            axes0_to_axes1[axes0] = axes1
        #--- End: for

        for axes0, axes1 in axes0_to_axes1.items():
            for axis0, axis1 in zip(axes0, axes1):
                if axis0 in axis0_to_axis1 and axis1 != axis0_to_axis1[axis0]:
                    if verbose:
                        print(
"{0}: Ambiguous axis mapping ({1} -> both {2} and {3})".format(
    self.__class__.__name__,
    self.domain_axis_identity(axes0), other.domain_axis_identity(axis1),
    other.domain_axis_identity(axis0_to_axis1[axis0])))
                    return False
                elif axis1 in axis1_to_axis0 and axis0 != axis1_to_axis0[axis1]:
                    if verbose:
                        print(
"{0}: Ambiguous axis mapping ({1} -> both {2} and {3})".format(
    self.__class__.__name__,
    self.domain_axis_identity(axis0), self.domain_axis_identity(axis1_to_axis0[axis0]),
    other.domain_axis_identity(axes1)))
                    return False

                axis0_to_axis1[axis0] = axis1
                axis1_to_axis0[axis1] = axis0
        #--- End: for

        # ------------------------------------------------------------
        # Constructs with no arrays
        # ------------------------------------------------------------
        for construct_type in self._non_array_constructs:
            if not getattr(self, '_equals_'+construct_type)(
                    other,
                    rtol=rtol, atol=atol, verbose=verbose,
                    ignore_type=_ignore_type,
                    axis1_to_axis0=axis1_to_axis0,
                    key1_to_key0=key1_to_key0):
                return False

        # ------------------------------------------------------------
        # Still here? Then the two objects are equal
        # ------------------------------------------------------------     
        return True
    #--- End: def

    def filter_by_axis(self, *mode, **axes):
        '''Select metadata constructs by axes spanned by their data.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_data`, `filter_by_key`, `filter_by_measure`,
             `filter_by_method`, `filter_by_identity`,
             `filter_by_naxes`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`,
             `filters_applied`, `inverse_filter`, `unfilter`

:Parameters:

    mode: optional
        Define the behaviour when multiple axes are provided.

        By default (or if the *modes* parameter is ``'and'``) a
        construct is selected if it matches all of the given axis
        requirements. If the *mode* parameter is ``'or'`` then a
        construct will be selected when at least one of the axis
        requirements is met. If the *mode* parameter is ``'exact'``
        then a construct will be selected when its data axes are
        exactly those defined by the axis requirements. If the mode
        parameters is ``'subset'`` then a construct will be selected
        when its data axes are a subset of those defined by the axis
        requirements.  If the mode parameters is ``'superset'`` then a
        construct will be selected when its data axes are a superset
        of those defined by the axis requirements.

    axes: optional
        Select constructs whose data does, or does not, span
        particular domain axis constructs.

        A domain axis construct is identified by a keyword parameter
        of the domain axis construct key (e.g. ``domainaxis1``). The
        value is a boolean indicating if a construct should be
        selected when its data does span the axis (`True`), or
        selected when its data does not span the axis (`False`).

        If no axes are provided then all constructs that have data,
        spanning any domain axes constructs, are selected.

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

Select constructs whose data spans the "domainaxis1" domain axis
construct:

>>> d = c.filter_by_axis(domainaxis1=True)

Select constructs whose data does not span the "domainaxis2" domain
axis construct:

>>> d = c.filter_by_axis(domainaxis2=False)

Select constructs whose data spans the "domainaxis1", but not the
"domainaxis2" domain axis constructs:

>>> d = c.filter_by_axis(domainaxis1=True, domainaxis2=False)

Select constructs whose data spans the "domainaxis1" or the
"domainaxis2" domain axis constructs:

>>> d = c.filter_by_axis('or', domainaxis1=True, domainaxis2=True)

        '''       
        out = self.shallow_copy()

        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + ({'filter_by_axis': (mode, axes)},)

        # Parse the mode parameter
        _and      = False
        _or       = False
        _exact    = False
        _subset   = False
        _superset = False
        if mode:
            if len(mode) > 1:
                raise ValueError("Can provide at most one mode value")
            
            mode = mode[0]
            if mode == 'or':
                _or = True
            elif mode == 'and':
                _and = True
            elif mode == 'exact':
                _exact = True
            elif mode == 'subset':
                _subset = True
            elif mode == 'superset':
                _superset = True
            else:
                raise ValueError(
                    "mode, if provided, must be one of 'and', 'or', 'exact', subset', 'superset'")
        else:
            # By default, mode is 'and'
            _and = True
            
        constructs_data_axes = self.data_axes()

        if _exact or _subset or _superset:
            axes_True = {axis: value for axis, value in axes.items() if value}
            if _exact and not axes_True:
                _exact = False
                _and   = True
        #--- End: if
        
        for cid in tuple(out):
            x = constructs_data_axes.get(cid)
            if x is None:
                # This construct does not have data axes
                out._pop(cid)
                continue

            ok = True
            if _exact:
                if set(x) != set(axes_True):
                    ok = False
            elif _subset:
                if not set(axes_True).issubset(x):
                    ok = False
            elif _superset:
                if not set(axes_True).issuperset(x):
                    ok = False
            else:
                for axis_key, value in axes.items():
                    if value:
                        ok = axis_key in x
                    else:
                        ok = axis_key not in x
                
                    if _or:
                        if ok:
                            break
                    elif not ok:
                        break
            #--- End: if

            if not ok:
                # This construct ..
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def filter_by_data(self):
        '''Select metadata constructs by whether they could contain data.

Selection is not based on whether they thay actually have data, rather
by whether the construct supports the inclusion of data. For example,
constructs selected by this method will all have `!get_data` method.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_key`, `filter_by_measure`,
             `filter_by_method`, `filter_by_identity`,
             `filter_by_naxes`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`,
             `filters_applied`, `inverse_filter`, `unfilter`

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

Select constructs that could contain data:

>>> d = c.filter_by_data()

        '''       
        out = self.shallow_copy()

        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + ({'filter_by_data': ()},)
        
        for cid in tuple(out):
            if out._construct_type[cid] not in self._array_constructs:
                # This construct can not have data
                out._pop(cid)
        #--- End: for
                
        return out
    #--- End: def

    def filter_by_identity(self, *identities):
        '''Select metadata constructs by identity.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_measure`, `filter_by_method`,
             `filter_by_naxes`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`,
             `filters_applied`, `inverse_filter`, `unfilter`

:Parameters:

    identities: optional

        Select constructs that have any of the given identities.

        An identity is specified by a string (e.g. ``'latitude'``,
        ``'long_name=time'``, etc.); or a compiled regular expression
        (e.g. ``re.compile('^atmosphere')``), for which all constructs
        whose identities match (via `re.search`) are selected.

        If no identities are provided then all constructs are selected.

        Each construct has a number of identities, and is selected if
        any of them match any of those provided. A construct's
        identities are those returned by its `!identities` method. In
        the following example, the construct ``c`` has four
        identities:

           >>> c.identities()
           ['time', 'long_name=Time', 'foo=bar', 'ncvar%T']

        In addition, each construct also has an identity based its
        construct key (e.g. ``'key%dimensioncoordinate2'``)

        Note that the identifiers of a metadata construct in the
        output of a `print` or `!dump` call are always one of its
        identities, and so may always be used as an *identities*
        argument.

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

Select constructs that have a "standard_name" property of 'latitude':

>>> d = c.filter_by_identity('latitude')

Select constructs that have a "long_name" property of 'Height':

>>> d = c.filter_by_identity('long_name=Height')

Select constructs that have a "standard_name" property of 'latitude'
or a "foo" property of 'bar':

>>> d = c.filter_by_identity('latitude', 'foo=bar')

Select constructs that have a netCDF variable name of 'time':

>>> d = c.filter_by_identity('ncvar%time')

        '''
        out = self.shallow_copy()
        
        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + ({'filter_by_identity': identities},)
        
        # Return all constructs if no identities have been provided
        if not identities:
            return out
        
        for cid, construct in tuple(out.items()):
            ok = False
            for value0 in identities:          
                for value1 in construct.identities() + ['key%'+cid]:
                    ok = self._matching_values(value0, construct, value1)
                    if ok:
                        break
                #--- End: for

                if ok:
                    break
            #--- End: for

            if not ok:
                # This construct does not match any of the identities
                out._pop(cid)
        #--- End: for

        return out
    #--- End: def

    def filter_by_key(self, *keys):
        '''Select metadata constructs by key.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_measure`,
             `filter_by_method`, `filter_by_identity`,
             `filter_by_naxes`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`,
             `filters_applied`, `inverse_filter`, `unfilter`

:Parameters:

    keys: optional
        Select constructs that have any of the given construct keys.

        A key is specified by a string (e.g. ``'fieldancillary0'``).

        If no keys are provided then all constructs are selected.

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

Select the construct with key 'domainancillary0':

>>> d = c.filter_by_key('domainancillary0')

Select the constructs with keys 'dimensioncoordinate1' or
'fieldancillary0':

>>> d = c.filter_by_key('dimensioncoordinate1', 'fieldancillary0')

        '''
        out = self.shallow_copy()

        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + ({'filter_by_key': keys},)
        
        if not keys:
            return out
        
        for cid in tuple(out):
            if cid not in keys:
                out._pop(cid)
        #--- End: for

        return out
    #--- End: def

    def filter_by_measure(self, *measures):
        '''Select cell measure constructs by measure.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_method`, `filter_by_identity`,
             `filter_by_naxes`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`,
             `filters_applied`, `inverse_filter`, `unfilter`

:Parameters:

    measures: optional
        Select cell measure constructs that have any of the given
        measure values.

        A measure is specified by a string (e.g. ``'area'``); or a
        compiled regular expression (e.g. ``re.compile('^a')``), for
        which all constructs whose measures match (via `re.search`)
        are selected.

        If no measures are provided then all cell measure constructs
        that have a measure property, with any value, are selected.

:Returns:

    `Constructs`
        The selected cell measure constructs and their construct
        keys.
        
**Examples:**

>>> print(t.constructs.filter_by_type('measure'))
Constructs:
{'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>,
 'cellmeasure1': <CellMeasure: measure:volume(3, 9, 10) m3>}

Select cell measure constructs that have a measure of 'area':

>>> print(c.filter_by_measure('area'))
Constructs:
{'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>}

Select cell measure constructs that have a measure of 'area' or
'volume':

>>> print(c.filter_by_measure('area', 'volume'))
Constructs:
{'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>,
 'cellmeasure1': <CellMeasure: measure:volume(3, 9, 10) m3>}

Select cell measure constructs that have a measure of start with the
letter "a" or "v":

>>> print(c.filter_by_measure(re.compile('^a|v')))
Constructs:
{'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>,
 'cellmeasure1': <CellMeasure: measure:volume(3, 9, 10) m3>}

Select cell measure constructs that have a measure of any value:

>>> print(c.filer_by_measure())
Constructs:
{'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>,
 'cellmeasure1': <CellMeasure: measure:volume(3, 9, 10) m3>}

        '''
        out = self.shallow_copy()

        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + ({'filter_by_measure': measures},)
        
        for cid, construct in tuple(out.items()):
            try:
                get_measure = construct.get_measure
            except AttributeError:
                # This construct doesn't have a "get_measure" method
                out._pop(cid)
                continue

            if not measures:
                if not construct.has_measure():
                    out._pop(cid)
                    
                continue

            ok = False
            for value0 in measures:
                value1 = construct.get_measure(None)
                ok = self._matching_values(value0, construct, value1)
                if ok:
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the measures
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def filter_by_method(self, *methods):
        '''Select cell method constructs by method.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_measure`, `filter_by_identity`,
             `filter_by_naxes`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`,
             `filters_applied`, `inverse_filter`, `unfilter`

:Parameters:

    methods: optional
        Select cell method constructs that have any of the given
        methods.

        A method is specified by a string (e.g. ``'mean'``); or a
        compiled regular expression (e.g. ``re.compile('^m')``), for
        which all constructs whose methods match (via `re.search`) are
        selected.

        If no methods are provided then all cell method constructs
        that have a method, with any value, are selected.

:Returns:

    `Constructs`
        The selected cell method constructs and their construct keys.

**Examples:**

>>> print(c.constructs.filter_by_type('cell_method'))
Constructs:
{'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1': <CellMethod: domainaxis3: maximum>}

Select cell method constructs that have a method of 'mean':

>>> print(c.filter_by_method('mean'))
Constructs:
{'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>}

Select cell method constructs that have a method of 'mean' or
'maximum':

>>> print(c.filter_by_method('mean', 'maximum'))
Constructs:
{'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1': <CellMethod: domainaxis3: maximum>}

Select cell method constructs that have a method that contain the letter 'x':

>>> import re
>>> print(c.filter_by_method(re.compile('x')))
Constructs:
{'cellmethod1': <CellMethod: domainaxis3: maximum>}

Select cell method constructs that have a method of any value:

>>> print(c.filter_by_method())
Constructs:
{'cellmethod0': <CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
 'cellmethod1': <CellMethod: domainaxis3: maximum>}

        '''
        out = self.shallow_copy()
        
        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + ({'filter_by_method': methods},)
        
        for cid, construct in tuple(out.items()):
            try:
                get_method = construct.get_method
            except AttributeError:
                # This construct doesn't have a "get_method" method
                out._pop(cid)
                continue

            if not methods:
                if not construct.has_method():
                    out._pop(cid)
                    
                continue
            
            ok = False
            for value0 in methods:
                value1 = get_method(None)
                ok = self._matching_values(value0, construct, value1)
                if ok:
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the methods
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def filter_by_naxes(self, *naxes):
        '''Select metadata constructs by the number of domain axis contructs
spanned by their data.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_measure`, `filter_by_method`,
             `filter_by_identity`, `filter_by_ncdim`,
             `filter_by_ncvar`, `filter_by_property`,
             `filter_by_type`, `filters_applied`, `inverse_filter`,
             `unfilter`

:Parameters:

    naxes: optional
        Select constructs whose data spans a particular number of
        domain axis constructs.

        A number of domain axis constructs is given by an `int`.

        If no numbers are provided then all constructs that have data,
        spanning any domain axes constructs, are selected.

:Returns:

    `Constructs`
        The selected domain axis constructs and their construct keys.

**Examples:**

Select constructs that contain data that spans two domain axis
constructs:

>>> d = c.filter_by_naxes(2)

Select constructs that contain data that spans one or two domain axis
constructs:

>>> d = c.filter_by_ncdim(1, 2)

        '''
        out = self.shallow_copy()
        
        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + ({'filter_by_naxes': naxes},)
            
        constructs_data_axes = self.data_axes()
        
        for key in tuple(out):
            x = constructs_data_axes.get(key)
            if x is None:
                # This construct does not have data axes
                out._pop(key)
                continue

            ok = True
            for n in naxes:
                if n == len(x):
                    ok = True
                    break

                ok = False

            if not ok:
                # This construct does not have the right number of axes
                out._pop(key)
        #--- End: for
        
        return out
    #--- End: def

    def filter_by_ncdim(self, *ncdims):
        '''Select domain axis constructs by netCDF dimension name.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_measure`, `filter_by_method`,
             `filter_by_naxes`, `filter_by_identity`,
             `filter_by_ncvar`, `filter_by_property`,
             `filter_by_type`, `filters_applied`, `inverse_filter`,
             `unfilter`

:Parameters:

    ncdims: optional
        Select domain axis constructs that have any of the given
        netCDF dimension names.

        A netCDF dimension name is specified by a string
        (e.g. ``'time'``); or a compiled regular expression
        (e.g. ``re.compile('^lat')``), for which all constructs whose
        netCDF dimension names match (via `re.search`) are selected.

        If no netCDF dimension names are provided then all domain axis
        constructs that have a netCDF dimension name, with any value,
        are selected.

:Returns:

    `Constructs`
        The selected domain axis constructs and their construct keys.

**Examples:**

Select the domain axis constructs with netCDF dimension name 'time':

>>> d = c.filter_by_ncdim('time')

Select the domain axis constructs with netCDF dimension name 'time' or
'lat':

>>> d = c.filter_by_ncdim('time', 'lat')

        '''
        out = self.shallow_copy()
        
        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + ({'filter_by_ncdim': ncdims},)
        
        for cid, construct in tuple(out.items()):
            try:
                nc_get_dimension = construct.nc_get_dimension
            except AttributeError:
                # This construct doesn't have a "nc_get_dimension"
                # method
                out._pop(cid)
                continue
            
            if not ncdims:
                if not construct.nc_has_dimension():
                    out._pop(cid)
                    
                continue
            
            ok = False
            for value0 in ncdims:
                value1 = nc_get_dimension(None)
                ok = self._matching_values(value0, construct, value1)
                if ok:
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the netCDF
                # dimension names
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def filter_by_ncvar(self, *ncvars):
        '''Select domain axis constructs by netCDF variable name.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_measure`, `filter_by_method`,
             `filter_by_naxes`, `filter_by_identity`,
             `filter_by_ncdim`, `filter_by_property`,
             `filter_by_type`, `filters_applied`, `inverse_filter`,
             `unfilter`

:Parameters:

    ncvars: optional
        Select constructs that have any of the given netCDF variable
        names.

        A netCDF variable name is specified by a string
        (e.g. ``'time'``); or a compiled regular expression
        (e.g. ``re.compile('^lat')``), for which all constructs whose
        netCDF variable names match (via `re.search`) are selected.

        If no netCDF variable names are provided then all domain axis
        constructs that have a netCDF variable name, with any value,
        are selected.

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

Select the constructs with netCDF variable name 'time':

>>> d = c.filter_by_ncvar('time')

Select the constructs with netCDF variable name 'time' or 'lat':

>>> d = c.filter_by_ncvar('time', 'lat')

        '''
        out = self.shallow_copy()
        
        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + ({'filter_by_ncvar': ncvars},)
        
        for cid, construct in tuple(out.items()):            
            try:
                nc_get_variable = construct.nc_get_variable
            except AttributeError:
                # This construct doesn't have a "nc_get_variable"
                # method
                out._pop(cid)
                continue

            if not ncvars:
                if not construct.nc_has_variable():
                    out._pop(cid)
                    
                continue

            ok = False
            for value0 in ncvars:
                value1 = nc_get_variable(None)
                ok = self._matching_values(value0, construct, value1)
                if ok:
                    break
            #--- End: for

            if not ok:
                # This construct does not match any of the netCDF
                # variable names
                out._pop(cid)
        #--- End: for
        
        return out
    #--- End: def

    def _matching_values(self, value0, construct, value1):
        if value1 is not None:                        
            try:
                result = value0.search(value1)
            except (AttributeError, TypeError):
                result = construct._equals(value1, value0)
                
            if result:
                # This construct matches this property
                return True

        return False
    
    def filter_by_property(self, *mode, **properties):
        '''Select metadata constructs by property.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_measure`, `filter_by_method`,
             `filter_by_naxes`, `filter_by_identity`,
             `filter_by_ncdim`, `filter_by_ncvar`, `filter_by_type`,
             `filters_applied`, `inverse_filter`, `unfilter`

:Parameters:
        
    mode: optional
        Define the behaviour when multiple properties are provided.

        By default (or if the *mode* parameter is ``'and'``) a
        construct is selected if it matches all of the given
        properties, but if the *mode* parameter is ``'or'`` then a
        construct will be selected when at least one of its properties
        matches.

    properties:  optional
        Select constructs that have properties with the given
        values.

        By default a construct is selected if it matches all of the
        given properties, but it may alternatively be selected when at
        least one of its properties matches (see the *mode* positional
        parameter).

        A property value is given by a keyword parameter of the
        property name. The value may be a scalar or vector
        (e.g. ``'latitude'``, ``4``, ``['foo', 'bar']``); or a
        compiled regular expression (e.g. ``re.compile('^ocean')``),
        for which all constructs whose methods match (via `re.search`)
        are selected.

        If no properties are provided then all constructs that have
        properties, with any values, are selected.

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**
g
Select constructs that have a "standard_name" of 'latitude':

>>> d = c.filter_by_property(standard_name='latitude')

Select constructs that have a "long_name" of 'height' *and* "units" of
'm':

>>> d = c.filter_by_property(long_name='height', units='m')

Select constructs that have a "long_name" of 'height' *or* a "foo" of
'bar':

>>> d = c.filter_by_property('or', long_name='height', foo='bar')

Select constructs that have a "standard_name" which contains start
with the string 'air':

>>> import re
>>> d = c.filter_by_property(standard_name=re.compile('^air'))

        '''
        out = self.shallow_copy()

        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + ({'filter_by_property': (mode, properties)},)
        
        _or = False
        if mode:
            if len(mode) > 1:
                raise ValueError("Can provide at most one positional argument")
            
            x = mode[0]
            if x == 'or':
                _or = True
            elif x != 'and':
                raise ValueError("Positional argument, if provided, must 'or' or 'and'")
        #--- End: if

        for cid, construct in tuple(out.items()):
            try:
                get_property = construct.get_property
            except AttributeError:
                # This construct doesn't have a "get_property" method
                out._pop(cid)
                continue

            if not properties:
                if not construct.properties():
                    out._pop(cid)
                    
                continue

            ok = True
            for name, value0 in properties.items():
                value1 = get_property(name, None)
                ok = self._matching_values(value0, construct, value1)

                if _or:
                    if ok:
                        break
                elif not ok:
                    break
            #--- End: for
            
            if not ok:
                # This construct does not match any of the sets of
                # properties
                out._pop(cid)
        #--- End: for

        return out
    #--- End: def

    def filter_by_type(self, *types):
        '''Select metadata constructs by type.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_measure`, `filter_by_method`,
             `filter_by_naxes`, `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_identity`, `filter_by_property`,
             `filters_applied`, `inverse_filter`, `unfilter`

:Parameters:

    types: optional 
        Select constructs that have are of any of the given types.

        A type is specified by one of the following strings:

          ==========================  ================================
          *type*                      Construct selected
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

        If no types are provided then all constructs are selected.

:Returns:

    `Constructs`
        The selected constructs and their construct keys.

**Examples:**

Select dimension coordinate constructs:

>>> d = c.filter_by_type('dimension_coordinate')

Select dimension coordinate and field ancillary constructs:

>>> d = c.filter_by_type('dimension_coordinate', 'field_ancillary')

        '''
        out = super().filter_by_type(*types)

        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + ({'filter_by_type': types},)
        
        return out        
    #--- End: def
    
    def filters_applied(self):
        '''A history of filters that have been applied.

The history is returned in a tuple. The last element of the tuple
describes the last filter applied. Each element is a single-entry
dictionary whose key is the name of the filter method that was used,
with a value that gives the arguments that were passed to the call of
that method. If no filters have been applied then the tuple is empty.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_measure`, `filter_by_method`,
             `filter_by_naxes`, `filter_by_identity`,
             `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`, `inverse_filter`,
             `unfilter`

:Returns:

    `tuple`
        The history of filters that have been applied, ordered from
        first to last. If no filters have been applied then the tuple
        is empty.


**Examples:**

>>> print(c)
{'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
 'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
 'coordinatereference1': <CoordinateReference: grid_mapping_name:rotated_latitude_longitude>,
 'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>,
 'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>,
 'domainaxis1': <DomainAxis: size(10)>,
 'domainaxis2': <DomainAxis: size(9)>}
>>> c.filters_applied()
()
>>> c = c.filter_by_type('dimension_coordinate', 'auxiliary_coordinate')
>>> c.filters_applied()
({'filter_by_type': ('dimension_coordinate', 'auxiliary_coordinate')},)
>>> c = c.filter_by_property(units='degrees')
>>> c.filters_applied()
({'filter_by_type': ('dimension_coordinate', 'auxiliary_coordinate')},
 {'filter_by_property': ((), {'units': 'degrees'})})
>>> c = c.filter_by_property('or', standard_name='grid_latitude', axis='Y')
>>> c.filters_applied()
({'filter_by_type': ('dimension_coordinate', 'auxiliary_coordinate')},
 {'filter_by_property': ((), {'units': 'degrees'})},
 {'filter_by_property': (('or',), {'axis': 'Y', 'standard_name': 'grid_latitude'})})
>>> print(c)
Constructs:
{'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>}

        '''
        filters = getattr(self, '_filters_applied', None)
        if filters is None:
            return ()

        return deepcopy(filters)
    #--- End: def

    def clear_filters_applied(self):
        '''Remove the history of filters that have been applied.

The removed history is returned in a tuple. The last element of the
tuple describes the last filter applied. Each element is a
single-entry dictionary whose key is the name of the filter method
that was used, with a value that gives the arguments that were passed
to the call of that method. If no filters have been applied then the
tuple is empty.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_measure`, `filter_by_method`,
             `filter_by_naxes`, `filter_by_identity`,
             `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`, `inverse_filter`,
             `unfilter`

:Returns:

    `tuple`
        The removed history of filters that have been applied, ordered
        from first to last. If no filters have been applied then the
        tuple is empty.


**Examples:**

>>> c.filters_applied()
({'filter_by_naxes': (3, 1)},
 {'filter_by_identity': ('grid_longitude',)})
>>> c.clear_filters_applied()
({'filter_by_naxes': (3, 1)},
 {'filter_by_identity': ('grid_longitude',)})
>>> c.filters_applied()
()

        '''
        out = self.filters_applied()
        self._filters_applied = None
        self._prefiltered = None
        return out
    #--- End: def

    def inverse_filter(self, depth=None):
        '''Return the inverse of previous filters.

By default, the inverse comprises all of the constructs that were
*not* selected by all previously applied filters. If no filters have
been applied, then this will result in empty `Constructs` instance
being returned.

If the *depth* parameter is set to *N* then the inverse is relative to
the constructs selected by the *N*\ -th most recently applied filter.

A history of the filters that have been applied is returned in a
`tuple` by the `filters_applied` method. The last element of the tuple
describes the last filter applied. If no filters have been applied
then the tuple is empty.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_measure`, `filter_by_method`,
             `filter_by_naxes`, `filter_by_identity`,
             `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`,
             `filters_applied`, `unfilter`

:Parameters:

     depth: `int`, optional
        If set to ``N`` then the inverse is relative to the constructs
        selected by the ``N``-th most recently applied filter. By
        default the inverse is relative to the constructs selected by
        all previously applied filters. ``N`` may be larger than the
        total number of filters applied, which results in the default
        bahaviour.

:Returns:

    `Constructs`
        The constructs, and their construct keys, that were not
        selected by the last filter applied. If no filtering has been
        applied, or the last filter was an inverse filter, then an
        empty `Constructs` instance is returned.

**Examples:**

>>> print(c)
Constructs:
{'cellmethod0': <CellMethod: area: mean>,
 'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>,
 'dimensioncoordinate1': <DimensionCoordinate: longitude(8) degrees_east>,
 'dimensioncoordinate2': <DimensionCoordinate: time(1) days since 2018-12-01 >,
 'domainaxis0': <DomainAxis: size(5)>,
 'domainaxis1': <DomainAxis: size(8)>,
 'domainaxis2': <DomainAxis: size(1)>}
>>> print(c.inverse_filter())
Constructs:
{}
>>> d = c.filter_by_type('dimension_coordinate', 'cell_method')
>>> print(d)
Constructs:
{'cellmethod0': <CellMethod: area: mean>,
 'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>,
 'dimensioncoordinate1': <DimensionCoordinate: longitude(8) degrees_east>,
 'dimensioncoordinate2': <DimensionCoordinate: time(1) days since 2018-12-01 >}
>>> print(d.inverse_filter())
Constructs:
{'domainaxis0': <DomainAxis: size(5)>,
 'domainaxis1': <DomainAxis: size(8)>,
 'domainaxis2': <DomainAxis: size(1)>}
>>> e = d.filter_by_method('mean')
>>> print(e)
Constructs:
{'cellmethod0': <CellMethod: area: mean>}
>>> print(e.inverse_filter(1))
Constructs:
{'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>,
 'dimensioncoordinate1': <DimensionCoordinate: longitude(8) degrees_east>,
 'dimensioncoordinate2': <DimensionCoordinate: time(1) days since 2018-12-01 >}
>>> print(e.inverse_filter())
Constructs:
{'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>,
 'dimensioncoordinate1': <DimensionCoordinate: longitude(8) degrees_east>,
 'dimensioncoordinate2': <DimensionCoordinate: time(1) days since 2018-12-01 >,
 'domainaxis0': <DomainAxis: size(5)>,
 'domainaxis1': <DomainAxis: size(8)>,
 'domainaxis2': <DomainAxis: size(1)>}
>>> print(e.inverse_filter(1).inverse_filter())
Constructs:
{'cellmethod0': <CellMethod: area: mean>,
 'domainaxis0': <DomainAxis: size(5)>,
 'domainaxis1': <DomainAxis: size(8)>,
 'domainaxis2': <DomainAxis: size(1)>}

        '''
        out = self.unfilter(depth=depth) 

        if depth:
            if 'inverse_filter' in self.filters_applied()[-1] :
                filters = out.filters_applied()
                d = 1
                while True:
                    if d > len(filters) or 'inverse_filter' not in filters[-d]:
                        break

                    d += 1

                if d > 1:
                    out = self.unfilter(depth=depth + d - 1)

                return out
        #--- End: if
        
        for key in self:
            out._pop(key)

        out._filters_applied = self.filters_applied() + ({'inverse_filter': ()},)

        out._prefiltered = self.shallow_copy()
        
        return out
    #--- End: def
    
    def shallow_copy(self, _ignore=None):
        '''Return a shallow copy.

``f.shallow_copy()`` is equivalent to ``copy.copy(f)``.

.. versionadded:: 1.7.0

:Returns:

        The shallow copy.

**Examples:**

>>> g = f.shallow_copy()

        '''
        out = super().shallow_copy(_ignore=_ignore)

        prefiltered = getattr(self, '_prefiltered', None)
        if prefiltered is not None:
            out._prefiltered = prefiltered.shallow_copy()
            out._filters_applied = self._filters_applied
           
        return out
    #--- End: def

    def unfilter(self, depth=None):
        '''Return the constructs that existed prior to previous filters.

By default, the unfiltered constructs are those that existed before
all previously applied filters.

If the *depth* parameter is set to *N* then the unfiltered constructs
are those that existed before the *N*\ -th most recently applied
filter.

A history of the filters that have been applied is returned in a
`tuple` by the `filters_applied` method. The last element of the tuple
describes the last filter applied. If no filters have been applied
then the tuple is empty.

.. versionadded:: 1.7.0

.. seealso:: `filter_by_axis`, `filter_by_data`, `filter_by_key`,
             `filter_by_measure`, `filter_by_method`,
             `filter_by_naxes`, `filter_by_identity`,
             `filter_by_ncdim`, `filter_by_ncvar`,
             `filter_by_property`, `filter_by_type`,
             `filters_applied`, `inverse_filter`

:Parameters:

     depth: `int`, optional
        If set to ``N`` then return the constructs selected by the
        ``N``-th most recently applied filter. By default the
        constructs from before all previously applied filters are
        returned. ``N`` may be larger than the total number of filters
        applied, which results in the default bahaviour.

:Returns:

    `Constructs`
        The constructs, and their construct keys, that existed before
        the last filter was applied. If no filters have been applied
        then all of the constructs are returned.

**Examples:**

>>> print(c)
Constructs:
{'cellmethod0': <CellMethod: area: mean>,
 'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>,
 'dimensioncoordinate1': <DimensionCoordinate: longitude(8) degrees_east>,
 'dimensioncoordinate2': <DimensionCoordinate: time(1) days since 2018-12-01 >,
 'domainaxis0': <DomainAxis: size(5)>,
 'domainaxis1': <DomainAxis: size(8)>,
 'domainaxis2': <DomainAxis: size(1)>}
>>> d = c.filter_by_type('dimension_coordinate', 'cell_method')
>>> print(d)
Constructs:
{'cellmethod0': <CellMethod: area: mean>,
 'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>,
 'dimensioncoordinate1': <DimensionCoordinate: longitude(8) degrees_east>,
 'dimensioncoordinate2': <DimensionCoordinate: time(1) days since 2018-12-01 >}
>>> d.unfilter().equals(c)
True
>>> e = d.filter_by_method('mean')
>>> print(e)
Constructs:
{'cellmethod0': <CellMethod: area: mean>}
>>> c.unfilter().equals(c)
True
>>> c.unfilter(0).equals(c)
True
>>> e.unfilter().equals(c)
True
>>> e.unfilter(1).equals(d)
True
>>> e.unfilter(2).equals(c)
True

If no filters have been applied then the unfiltered constructs are unchanged:

>>> c.filters_applied()
()
>>> c.unfilter().equals(c)
True

        '''
        out = self
        
        if depth is None:
            while True:
                prefiltered = getattr(out, '_prefiltered', None)
                if prefiltered is None:
                    break
                else:
                    out = prefiltered
        else:
            for _ in range(depth):
                prefiltered = getattr(out, '_prefiltered', None)
                if prefiltered is not None:
                    out = prefiltered
                else:
                    break
        #--- End: if
        
        return out.shallow_copy()
    #--- End: def
    
#--- End: class
