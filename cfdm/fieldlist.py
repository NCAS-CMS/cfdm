# ====================================================================
#
# FieldList object
#
# ====================================================================

class FieldList(list):
    '''An ordered sequence of fields.

Each element of a field list is a `cf.Field` object.

A field list supports the python list-like operations (such as
indexing and methods like `!append`).

>>> fl = cf.FieldList()
>>> len(fl)
0
>>> f
<CF Field: air_temperaturetime(12), latitude(73), longitude(96) K>
>>> fl = cf.FieldList(f)
>>> len(fl)
1
>>> fl = cf.FieldList([f, f])
>>> len(fl)
2
>>> fl = cf.FieldList(cf.FieldList([f] * 3))
>>> len(fl)

3
>>> len(fl + fl)
6

These methods provide functionality similar to that of a
:ref:`built-in list <python:tut-morelists>`. The main difference is
that when a field element needs to be assesed for equality its
`~cf.Field.equals` method is used, rather than the ``==`` operator.
    '''   

    def __init__(self, fields=None):
        '''
**Initialization**

:Parameters:

    fields: (sequence of) `cf.Field`, optional
         Create a new field list with these fields.

'''
        if fields is not None:
            if getattr(fields, 'isfield', False):
                self.append(fields)
            else:
                self.extend(fields)         
    #--- End: def

    def __repr__(self):
        '''Called by the :py:obj:`repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        
        out = [repr(f) for f in self]
        out = ',\n '.join(out)
        return '['+out+']'
    #--- End: def

    def __str__(self):
        '''Called by the :py:obj:`str` built-in function.

x.__str__() <==> str(x)

        '''
        return '\n'.join(str(f) for f in self)
    #--- End: def

    # ================================================================
    # Overloaded list methods
    # ================================================================    
    def __add__(self, x):
        '''Called to implement evaluation of f + x

f.__add__(x) <==> f + x

:Examples 1:

>>> h = f + g
>>> f += g

:Returns:

    out: `cf.FieldList`

        '''
        return type(self)(list.__add__(self, x))
    #--- End: def

    def __mul__(self, x):
        '''Called to implement evaluation of f * x

f.__mul__(x) <==> f * x

:Examples:

>>> h = f * 2
>>> f *= 2

:Returns:

    out: `cf.FieldList`

        '''
        return type(self)(list.__mul__(self, x))
    #--- End: def

    def __getslice__(self, i, j):
        '''Called to implement evaluation of f[i:j]

f.__getslice__(i, j) <==> f[i:j]

:Examples:

>>> g = f[0:1]
>>> g = f[1:-4]
>>> g = f[:1]
>>> g = f[1:]

:Returns:

    out: `cf.FieldList`

        '''
        return type(self)(list.__getslice__(self, i, j))
    #--- End: def

    def __getitem__(self, index):
        '''Called to implement evaluation of f[index]

f.__getitem_(index) <==> f[index]

:Examples:

>>> g = f[0]
>>> g = f[-1:-4:-1]
>>> g = f[2:2:2]

:Returns:

    out: `cf.Field` or `cf.FieldList`
        If *index* is an integer then a field is returned. If *index*
        is a slice then a field list is returned, which may be empty.

        '''
        out = list.__getitem__(self, index)

        if isinstance(out, list):
            return type(self)(out)

        return out
    #--- End: def

    __len__     = list.__len__
    __setitem__ = list.__setitem__    
    append      = list.append
    extend      = list.extend
    insert      = list.insert
    pop         = list.pop
    reverse     = list.reverse
    sort        = list.sort

    def __contains__(self, y):
        '''Called to implement membership test operators.

x.__contains__(y) <==> y in x

Each field in the field list is compared with the field's
`~cf.Field.equals` method, as aopposed to the ``==`` operator.

Note that ``y in fl`` is equivalent to ``any(f.equals(y) for f in fl)``.

        '''
        for f in self:
            if f.equals(y):
                return True
            
        return False
    #--- End: def

    def count(self, value):
        '''Return number of occurrences of value

Each field in the field list is compared with the field's
`~cf.Field.equals` method, as opposed to the ``==`` operator.

Note that ``fl.count(value)`` is equivalent to ``sum(f.equals(value)
for f in fl)``.

.. seealso:: `cf.Field.equals`, :py:obj:`list.count`

:Examples:

>>> f = cf.FieldList([a, b, c, a])
>>> f.count(a)
2
>>> f.count(b)
1
>>> f.count(a+1)
0

        '''
        return len([None for f in self if f.equals(value)])
    #--- End def

    def index(self, value, start=0, stop=None):
        '''Return first index of value.

Each field in the field list is compared with the field's
`~cf.Field.equals` method, as aopposed to the ``==`` operator.

It is an error if there is no such field.

.. seealso:: :py:obj:`list.index`

:Examples:

>>>

        '''      
        if start < 0:
            start = len(self) + start

        if stop is None:
            stop = len(self)
        elif stop < 0:
            stop = len(self) + stop

        for i, f in enumerate(self[start:stop]):
            if f.equals(x):
               return i + start
        #--- End: for

        raise ValueError(
            "{0!r} is not in {1}".format(x, self.__class__.__name__))
    #--- End: def

    def remove(self, value):
        '''Remove first occurrence of value.

Each field in the field list is compared with its `~cf.Field.equals`
method, as opposed to the ``==`` operator.

.. seealso:: :py:obj:`list.remove`

        '''
        for i, f in enumerate(self):
            if f.equals(value):
                del self[i]
                return

        raise ValueError(
            "{0}.remove(x): x not in {0}".format(self.__class__.__name__))
    #--- End: def

    def sort(self, cmp=None, key=None, reverse=False):
        '''Stable sort of the field list *IN PLACE*

By default the field list is sorted by the identities of its fields.

.. versionadded:: 1.0.4

.. seealso:: `reverse`, :py:obj:`sorted`

:Examples 1:

>>> fl.sort()

:Parameters:

    cmp: function, optional
        Specifies a custom comparison function of two arguments
        (iterable elements) which should return a negative, zero or
        positive number depending on whether the first argument is
        considered smaller than, equal to, or larger than the second
        argument. The default value is `None`.
        
          *Example:*
            ``cmp=lambda x,y: cmp(x.lower(), y.lower())``.

    key: function, optional
        Specify a function of one argument that is used to extract a
        comparison key from each list element. By default fiel list is
        sorted by field identity, i.e. the default value of *key* is
        ``lambda f: f.identity()``.

    reverse: `bool`, optional
        If set to True, then the list elements are sorted as if each
        comparison were reversed.

:Returns:

    `None`

:Examples 2:

>>> fl
[<CF Field: eastward_wind(time(3), air_pressure(5), grid_latitude(110), grid_longitude(106)) m s-1>,
 <CF Field: ocean_meridional_overturning_streamfunction(time(12), region(4), depth(40), latitude(180)) m3 s-1>,
 <CF Field: air_temperature(time(12), latitude(64), longitude(128)) K>,
 <CF Field: eastward_wind(time(3), air_pressure(5), grid_latitude(110), grid_longitude(106)) m s-1>]
>>> fl.sort()
>>> fl
[<CF Field: air_temperature(time(12), latitude(64), longitude(128)) K>,
 <CF Field: eastward_wind(time(3), air_pressure(5), grid_latitude(110), grid_longitude(106)) m s-1>,
 <CF Field: eastward_wind(time(3), air_pressure(5), grid_latitude(110), grid_longitude(106)) m s-1>,
 <CF Field: ocean_meridional_overturning_streamfunction(time(12), region(4), depth(40), latitude(180)) m3 s-1>]
>>> fl.sort(reverse=True)
>>> fl
[<CF Field: ocean_meridional_overturning_streamfunction(time(12), region(4), depth(40), latitude(180)) m3 s-1>,
 <CF Field: eastward_wind(time(3), air_pressure(5), grid_latitude(110), grid_longitude(106)) m s-1>,
 <CF Field: eastward_wind(time(3), air_pressure(5), grid_latitude(110), grid_longitude(106)) m s-1>,
 <CF Field: air_temperature(time(12), latitude(64), longitude(128)) K>]

>>> [f.datum(0) for f in fl]
[masked,
 -0.12850454449653625,
 -0.12850454449653625,
 236.51275634765625]
>>> fl.sort(key=lambda f: f.datum(0), reverse=True)
>>> [f.datum(0) for f in fl]
[masked,
 236.51275634765625,
 -0.12850454449653625,
 -0.12850454449653625]

>>> from operator import attrgetter
>>> [f.long_name for f in fl]
['Meridional Overturning Streamfunction',
 'U COMPNT OF WIND ON PRESSURE LEVELS',
 'U COMPNT OF WIND ON PRESSURE LEVELS',
 'air_temperature']
>>> fl.sort(cmp=lambda x,y: cmp(x.lower(), y.lower()), key=attrgetter('long_name'))
>>> [f.long_name for f in fl]
['air_temperature',
 'Meridional Overturning Streamfunction',
 'U COMPNT OF WIND ON PRESSURE LEVELS',
 'U COMPNT OF WIND ON PRESSURE LEVELS']

        '''
        return super(FieldList, self).sort(cmp, key, reverse)
    #--- End: def

    def __deepcopy__(self, memo):
        '''Called by the `copy.deepcopy` standard library function.

        '''
        return self.copy()
    #--- End: def

    def _parameters(self, d):
        del d['self']
        if 'kwargs' in d:
            d.update(d.pop('kwargs'))
        return d
    #--- End: def

    def copy(self, _omit_data=False, _only_data=False,
             _omit_special=None, _omit_properties=False,
             _omit_attributes=False):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

:Examples 1:

>>> g = f.copy()

:Returns:

    out: `cf.FieldList`
        The deep copy.

:Examples 2:

>>> g = f.copy()
>>> g is f
False
>>> f.equals(g)
True
>>> import copy
>>> h = copy.deepcopy(f)
>>> h is f
False
>>> f.equals(g)
True

        '''
        kwargs2 = self._parameters(locals())
        return type(self)([f.copy(**kwargs2) for f in self])
    #--- End: def
    
    def dump(self, display=True, _level=0, _title='Field', _q='-'):
        '''A full description of each field.

By default, the description is given without abbreviation with the
exception of data arrays (which are abbreviated to their first and
last values) and fields contained in coordinate references and
ancillary variables (which are given as one-line summaries).

:Examples 1:
        
>>> fl.dump()

:Parameters:

    display: `bool`, optional
        If False then return the descriptionfor each field as a
        string. By default the descriptions are printed.

          *Example:*
            ``fl.dump()`` is equivalent to ``for f in fl: print
            f.dump(display=False)``.

:Returns:

    out: `None` or `list`
        If *display* is True then the description is printed and
        `None` is returned. Otherwise a list of strings containing the
        description for each field is returned.

        '''   
        kwargs2 = self._parameters(locals())

        if display:
            for f in self:
                f.dump(**kwargs2)

            return
        else:
            return [f.dump(**kwargs2) for f in self]
    #--- End: def

    def equals(self, other, rtol=None, atol=None, ignore_fill_value=False,
               traceback=False, ignore=(), _set=False):
        '''True if two field lists are equal, False otherwise.

Two {+variable}s are equal if they have the same number of elements
and the field elements are equal pairwise, i.e. ``f.equals(g)`` is
equivalent to ``all(x.equals(y) for x, y in map(None, f, g))``.

Two fields are equal if ...

Note that a single element {+variable} may be equal to field, for
example ``f[0:1].equals(f[0])`` and ``f[0].equals(f[0:1])`` are always
True.

.. seealso:: `set_equals`, `cf.Field.equals`

:Examples 1:

>>> b = f.equals(g)

:Parameters:

    other: `object`
        The object to compare for equality.

    {+atol}

    {+rtol}

    ignore_fill_value: `bool`, optional
        If True then data arrays with different fill values are
        considered equal. By default they are considered unequal.

    traceback: `bool`, optional
        If True then print a traceback highlighting where the two
        {+variable}s differ.

    ignore: `tuple`, optional
        The names of CF properties to omit from the comparison. By
        default, the CF Conventions property is omitted.

:Returns: 
  
    out: `bool`
        Whether or not the two {+variable}s are equal.

:Examples 2:


.. seealso:: `cf.Field.equals`

:Examples 1:

>>> g = f.copy()
>>> g.equals(f)
True

        '''
        # Check for object identity
        if self is other:
            return True

        # Check that each instance is of the same type
        if not isinstance(other, self.__class__):
            if traceback:
                print("{0}: Different types: {0}, {1}".format(
			self.__class__.__name__,
			other.__class__.__name__))
	    return False
        #--- End: if

        # Check that there are equal numbers of fields
        len_self = len(self)
        if len_self != len(other): 
            if traceback:
                print("{}: Different numbers of elements: {}, {}".format(
		    self.__class__.__name__,
		    len_self,
		    len(other)))
            return False
        #--- End: if

        if len_self == 1:
            _set = False
            
	if not _set:
       	    # ----------------------------------------------------
    	    # Check the lists pair-wise
    	    # ----------------------------------------------------
    	    for i, (f, g) in enumerate(zip(self, other)):
    	        if not f.equals(g, rtol=rtol, atol=atol,
                                ignore_fill_value=ignore_fill_value,
    				ignore=ignore, traceback=traceback):
    	            if traceback:
    		        print("{}: Different element {}: {!r}, {!r}".format(
    			    self.__class__.__name__, i, f, g))
                    return False
        else:
    	    # ----------------------------------------------------
    	    # Check the lists set-wise
    	    # ----------------------------------------------------
    	    # Group the variables by identity
    	    self_identity = {}
            for f in self:
                self_identity.setdefault(f.identity(), []).append(f)

    	    other_identity = {}
            for f in other:
                other_identity.setdefault(f.identity(), []).append(f)

    	    # Check that there are the same identities
    	    if set(self_identity) != set(other_identity):
    	        if traceback:
    		    print("{}: Different sets of identities: {}, {}".format(
    			self.__class__.__name__,
    			set(self_identity),
    			set(other_identity)))
    	        return False
            #--- End: if

            # Check that there are the same number of variables
    	    # for each identity
            for identity, fl in self_identity.iteritems():
    	        gl = other_identity[identity]
    	        if len(fl) != len(gl):
    		    if traceback:
    		        print("{}: Different numbers of {!r} {}s: {}, {}".format(
    			    self.__class__.__name__,
    			    identity,
                            fl[0].__class__.__name__,
    			    len(fl),
                            len(gl)))
                    return False
            #--- End: for

    	    # For each identity, check that there are matching pairs
            # of equal fields.
            for identity, fl in self_identity.iteritems():
    	        gl = other_identity[identity]

                for f in fl:
    		    found_match = False
                    for i, g in enumerate(gl):
                        if f.equals(g, rtol=rtol, atol=atol,
                                    ignore_fill_value=ignore_fill_value,
    				    ignore=ignore, traceback=False):
                            found_match = True
    		    	    del gl[i]
                            break
                #--- End: for
                
    		if not found_match:
    		    if traceback:                        
    			print("{}: No {} equal to: {!r}".format(
    			    self.__class__.__name__,
    			    g.__class__.__name__,
    			    f))
                    return False
	    #--- End: if

        #--- End: if

        # ------------------------------------------------------------
    	# Still here? Then the field lists are equal
    	# ------------------------------------------------------------
        return True	    
    #--- End: def

    def select(self, description=None, items=None, rank=None, ndim=None,
               exact=False, match_and=True, inverse=False):
        '''Return the fields that satisfy the given conditions.

Different types of conditions may be set with the parameters:
         
=============  =======================================================
Parameter      What gets tested
=============  =======================================================
*description*  Field properties and attributes
             
*items*        Field domain items
         
*rank*         The number of field domain axes

*ndim*         The number of field data array axes
=============  =======================================================

By default, when multiple criteria are given the field matches if it
satisfies the conditions given by each one.

If no fields satisfy the conditions then an empty `cf.FieldList` is
returned.

Note that ``fl.select(**kwargs)`` is equivalent to ``FieldList(g for g
in f if g.match(**kwargs))``

.. seealso:: `cf.Field.items`, `cf.Field.match`

**Quick start examples**

There is great flexibility in the types of test which can be
specified, and as a result the documentation is very detailed in
places. These preliminary, simple examples show that the usage need
not always be complicated and may help with understanding the keyword
descriptions.

1. Select fields which contain air temperature data, as given
   determined by the `identity` method:

   >>> fl.select('air_temperature')

2. Select fields which contain air temperature data, as given determined
   by the `identity` method, or have a long name which contains the
   string "temp":

   >>> fl.select(['air_temperature', {'long_name': cf.eq('.*temp.*', regex=true)}])

3. Select fields which have at least one longitude grid cell point on
   the Greenwich meridian:

   >>> fl.select(items={'longitude': 0})

4. Select fields which have at least one latitude grid cell of less
   than 1 degree in size:

   >>> fl.select(items={'latitude': cf.cellsize(cf.lt(1, 'degree'))})

5. Select fields which have exactly 4 domain axes:

   >>> fl.select(rank=4)

6. Examples 1 to 4 may be combined to select fields which have exactly
   4 domain axes, contain air temperature data, has at least one
   longitude grid cell point on the Greenwich meridian and have at
   least one latitude grid cells with a size of less than 1 degree:

   >>> fl.select('air_temperature',
   ...           items={'longitude': 0,
   ...                  'latitude': cf.cellsize(cf.lt(1, 'degree'))},
   ...           rank=4)

7. Select fields which contain at least one Gregorian calendar monthly
   mean data array value:

   >>> f.lselect({'cell_methods': cf.CellMethods('time: mean')},
   ...           items={'time': cf.cellsize(cf.wi(28, 31, 'days'))})

Further examples are given within and after the description of the
arguments.

:Parameters:

    description: *optional*
        Set conditions on the field's CF property and attribute
        values. *description* may be one, or a sequence of:

          * `None` or an empty dictionary. Always matches the
            field. This is the default.

     ..

          * A string which identifies string-valued metadata of the
            field and a value to compare it against. The value may
            take one of the following forms:

              ==============  ======================================
              *description*   Interpretation
              ==============  ======================================
              Contains ``:``  Selects on the CF property specified
                              before the first ``:``

              Contains ``%``  Selects on the attribute specified
                              before the first ``%``              
              
              Anything else   Selects on identity as returned by the
                              `identity` method
              ==============  ======================================

            By default the part of the string to be compared with the
            item is treated as a regular expression understood by the
            :py:obj:`re` module and the field matches if its
            appropriate value matches the regular expression using the
            :py:obj:`re.match` method (i.e. if zero or more characters
            at the beginning of field's value match the regular
            expression pattern). See the *exact* parameter for
            details.
            
              *Example:*
                To select a field with `identity` beginning with "lat":
                ``description='lat'``.

              *Example:*
                To select a field with long name beginning with "air":
                ``description='long_name:air'``.

              *Example:*
                To select a field with netCDF variable name of exactly
                "tas": ``description='ncvar%tas$'``.

              *Example:*
                To select a field with `identity` which ends with the
                letter "z": ``description='.*z$'``.

              *Example:*
                To select a field with long name which starts with the
                string ".*a": ``description='long_name%\.\*a'``. 

        ..

          * A `cf.Query` object to be compared with field's identity,
            as returned by its `identity` method.

              *Example:*
                To select a field with `identity` of exactly
                "air_temperature" you could set
                ``description=cf.eq('air_temperature')`` (see `cf.eq`).

              *Example:*
                To select a field with `identity` ending with
                "temperature" you could set
                ``description=cf.eq('.*temperature$', exact=False)`` (see
                `cf.eq`).

     ..

          * A dictionary which identifies properties of the field with
            corresponding tests on their values. The field matches if
            **all** of the tests in the dictionary are passed.

            In general, each dictionary key is a CF property name with
            a corresponding value to be compared against the field's
            CF property value. 

            If the dictionary value is a string then by default it is
            treated as a regular expression understood by the
            :py:obj:`re` module and the field matches if its
            appropriate value matches the regular expression using the
            :py:obj:`re.match` method (i.e. if zero or more characters
            at the beginning of field's value match the regular
            expression pattern). See the *exact* parameter for
            details.
            
              *Example:*
                To select a field with standard name of exactly
                "air_temperature" and long name beginning with the
                letter "a": ``description={'standard_name':
                cf.eq('air_temperature'), 'long_name': 'a'}`` (see
                `cf.eq`).

            Some key/value pairs have a special interpretation:

              ==================  ====================================
              Special key         Value
              ==================  ====================================
              ``'units'``         The value must be a string and by
                                  default is evaluated for
                                  equivalence, rather than equality,
                                  with the field's `units` property,
                                  for example a value of ``'Pa'``
                                  will match units of Pascals or
                                  hectopascals, etc. See the *exact*
                                  parameter.
                            
              ``'calendar'``      The value must be a string and by
                                  default is evaluated for
                                  equivalence, rather than equality,
                                  with the field's `calendar`
                                  property, for example a value of
                                  ``'noleap'`` will match a calendar
                                  of noleap or 365_day. See the
                                  *exact* parameter.
                              
              ``'cell_methods'``  The value must be a `cf.CellMethods`
                                  object containing *N* cell methods
                                  and by default is evaluated for
                                  equivalence with the last *N* cell
                                  methods contained within the field's
                                  `cell_methods` property. See the
                                  *exact* parameter.

              `None`              The value is interpreted as for a
                                  string value of the *description*
                                  parameter. For example,
                                  ``description={None: 'air'}`` is
                                  equivalent to ``description='air'`` 
                                  and ``description={None:
                                  'ncvar%pressure'}`` is equivalent to
                                  ``description='ncvar%pressure'``.
              ==================  ====================================
            
              *Example:*
                To select a field with standard name starting with
                "air", units of temperature and a netCDF variable name
                beginning with "tas" you could set
                ``description={'standard_name': 'air', 'units': 'K',
                None: 'ncvar%tas'}``.

              *Example:*
                To select a field whose last two cell methods are
                equivalent to "time: minimum area: mean":
                ``description={'cell_methods': cf.Cellmethods('time:
                minimum area: mean')``. This would select a field
                which has, for example, cell methods of "height: mean
                time: minimum area: mean".

        If *description* is a sequence of any combination of the above then
        the field matches if it matches **at least one** element of
        the sequence:

          *Example:* 

            >>> f.select('air_temperature')
            <CF Field: air_temperature(latitude(73), longitude(96) K>
            >>> f.select({'units': 'hPa'})
            []
            >>> f.select(['air_temperature', {'units': 'hPa'])
            <CF Field: air_temperature(latitude(73), longitude(96) K>
              
        If the sequence is empty then the field always matches.
 
    items: `dict`, optional
        A dictionary which identifies domain items of the field
        (dimension coordinate, auxiliary coordinate, cell measure or
        coordinate reference objects) with corresponding tests on
        their elements. The field matches if **all** of the specified
        items exist and their tests are passed.

        Each dictionary key specifies an item to test as the one that
        would be returned by this call of the field's `item` method:
        ``f.item(key, exact=exact)`` (see `cf.Field.item`).

        The corresponding value is, in general, any object for which
        the item may be compared with for equality (``==``). The test
        is passed if the result evaluates to True, or if the result is
        an array of values then the test is passed if at least one
        element evaluates to true.

        If the value is `None` then the test is always passed,
        i.e. this case tests for item existence.

          *Example:*
             To select a field which has a latitude coordinate value of
             exactly 30: ``items={'latitude': 30}``.

          *Example:*
             To select a field whose longitude axis spans the Greenwich
             meridian: ``items={'longitude': cf.contain(0)}`` (see
             `cf.contain`).

          *Example:*
             To select a field which has a time coordinate value of
             2004-06-01: ``items={'time': cf.dt('2004-06-01')}`` (see
            `cf.dt`).

          *Example:*
             To select a field which has a height axis: ``items={'Z':
             None}``.

          *Example:*
             To select a field which has a time axis and depth
             coordinates greater then 1000 metres: ``items={'T': None,
             'depth': cf.gt(1000, 'm')}`` (see `cf.gt`).

          *Example:*
            To select a field with time coordinates after than 1989 and
            cell sizes of between 28 and 31 days: ``items={'time':
            cf.dtge(1990) & cf.cellsize(cf.wi(28, 31, 'days'))}`` (see
            `cf.dtge`, `cf.cellsize` and `cf.wi`).

    rank: *optional*
        Specify a condition on the number of axes in the field's
        domain. The field matches if its number of domain axes equals
        *rank*. A range of values may be selected if *rank* is a
        `cf.Query` object. Not to be confused with the *ndim*
        parameter (the number of data array axes may be fewer than the
        number of domain axes).

          *Example:*
            ``rank=2`` selects a field with exactly two domain axes
            and ``rank=cf.wi(3, 4)`` selects a field with three or
            four domain axes (see `cf.wi`).

    ndim: *optional*
        Specify a condition on the number of axes in the field's data
        array. The field matches if its number of data array axes
        equals *ndim*. A range of values may be selected if *ndim* is
        a `cf.Query` object. Not to be confused with the *rank*
        parameter (the number of domain axes may be greater than the
        number of data array axes).

          *Example:*
            ``ndim=2`` selects a field with exactly two data array
            axes and ``ndim=cf.le(2)`` selects a field with fewer than
            three data array axes (see `cf.le`).

    exact: `bool`, optional
        The *exact* parameter applies to the interpretation of string
        values of the *description* parameter and of keys of the *items*
        parameter. By default *exact* is False, which means that:

          * A string value is treated as a regular expression
            understood by the :py:obj:`re` module. 

          * Units and calendar values in a *description* dictionary are
            evaluated for equivalence rather then equality
            (e.g. "metre" is equivalent to "m" and to "km").

          * A cell methods value containing *N* cell methods in a
            *description* dictionary is evaluated for equivalence with the
            last *N* cell methods contained within the field's
            `cell_methods` property.

        ..

          *Example:*
            To select a field with a standard name which begins with
            "air" and any units of pressure:
            ``f.select({'standard_name': 'air', 'units': 'hPa'})``.

          *Example:*          
            ``f.select({'cell_methods': cf.CellMethods('time: mean
            (interval 1 hour)')})`` would select a field with cell
            methods of "area: mean time: mean (interval 60 minutes)".

        If *exact* is True then:

          * A string value is not treated as a regular expression.

          * Units and calendar values in a *description* dictionary are
            evaluated for exact equality rather than equivalence
            (e.g. "metre" is equal to "m", but not to "km").

          * A cell methods value in a *description* dictionary is evaluated
            for exact equality to the field's cell methods.
          
        ..

          *Example:*          
            To select a field with a standard name of exactly
            "air_pressure" and units of exactly hectopascals:
            ``f.select({'standard_name': 'air_pressure', 'units':
            'hPa'}, exact=True)``.

          *Example:*          
            To select a field with a cell methods of exactly "time:
            mean (interval 1 hour)": ``f.select({'cell_methods':
            cf.CellMethods('time: mean (interval 1 hour)')``.

        Note that `cf.Query` objects provide a mechanism for
        overriding the *exact* parameter for individual values.

          *Example:*
            ``f.select({'standard_name': cf.eq('air', exact=False),
            'units': 'hPa'}, exact=True)`` will select a field with a
            standard name which begins "air" but has units of exactly
            hectopascals (see `cf.eq`).
    
          *Example:*
            ``f.select({'standard_name': cf.eq('air_pressure'),
            'units': 'hPa'})`` will select a field with a standard name
            of exactly "air_pressure" but with units which equivalent
            to hectopascals (see `cf.eq`).


    match_and: `bool`, optional
        By default *match_and* is True and the field matches if it
        satisfies the conditions specified by each test parameter
        (*description*, *items*, *rank* and *ndim*).

        If *match_and* is False then the field will match if it
        satisfies at least one test parameter's condition.

          *Example:*
            To select a field with a standard name of "air_temperature"
            **and** 3 data array axes: ``f.select('air_temperature',
            ndim=3)``. To select a field with a standard name of
            "air_temperature" **or** 3 data array axes:
            ``f.select('air_temperature", ndim=3, match_and=False)``.
    
    inverse: `bool`, optional
        If True then return the field matches if it does **not**
        satisfy the given conditions.

          *Example:*
          
            >>> len(f.select('air', ndim=4, inverse=True)) == len(f) - len(f.select('air', ndim=4))
            True

:Returns:

    out: `cf.FieldList`
        A `cf.FieldList` of the matching fields.

:Examples:

Field identity starts with "air":

>>> fl.select('air')

Field identity ends contains the string "temperature":

>>> fl.select('.*temperature')

Field identity is exactly "air_temperature":

>>> fl.select('^air_temperature$')
>>> fl.select('air_temperature', exact=True)

Field has units of temperature:

>>> fl.select({'units': 'K'}):

Field has units of exactly Kelvin:

>>> fl.select({'units': 'K'}, exact=True)

Field identity which starts with "air" and has units of temperature:

>>> fl.select({None: 'air', 'units': 'K'})

Field identity starts with "air" and/or has units of temperature:

>>> fl.select(['air', {'units': 'K'}])

Field standard name starts with "air" and/or has units of exactly Kelvin:

>>> fl.select([{'standard_name': cf.eq('air', exact=False), {'units': 'K'}],
...           exact=True)

Field has height coordinate values greater than 63km:

>>> fl.select(items={'height': cf.gt(63, 'km')})

Field has a height coordinate object with some values greater than
63km and a north polar point on its horizontal grid:

>>> fl.select(items={'height': cf.gt(63, 'km'),
...                  'latitude': cf.eq(90, 'degrees')})

Field has some longitude cell sizes of 3.75:

>>> fl.select(items={'longitude': cf.cellsize(3.75)})

Field latitude cell sizes within a tropical region are all no greater
than 1 degree:

>>> fl.select(items={'latitude': (cf.wi(-30, 30, 'degrees') &
...                               cf.cellsize(cf.le(1, 'degrees')))})

Field contains monthly mean air pressure data and all vertical levels
within the bottom 100 metres of the atmosphere have a thickness of 20
metres or less:

>>> fl.select({None: '^air_pressure$', 'cell_methods': cf.CellMethods('time: mean')},
...           items={'height': cf.le(100, 'm') & cf.cellsize(cf.le(20, 'm')),
...                  'time': cf.cellsize(cf.wi(28, 31, 'days'))})

        '''
        kwargs2 = self._parameters(locals())
        return type(self)(f for f in self if f.match(**kwargs2))
    #--- End: def

#--- End: class
