from __future__ import print_function
from builtins import super

from . import mixin
from . import core


class DomainAxis(mixin.NetCDFDimension,
                 mixin.Container,
                 core.DomainAxis):
    '''A domain axis construct of the CF data model. 

A domain axis construct specifies the number of points along an
independent axis of the domain. It comprises a positive integer
representing the size of the axis. In CF-netCDF it is usually defined
either by a netCDF dimension or by a scalar coordinate variable, which
implies a domain axis of size one. The field construct's data array
spans the domain axis constructs of the domain, with the optional
exception of size one axes, because their presence makes no difference
to the order of the elements.

.. versionadded:: 1.7

    '''
    def __init__(self, size=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    size: `int`, optional
        The size of the domain axis.

        *Example:*
          ``size=192``

        The size may also be set after initialisation with the
        `set_size` method.

    source: optional
        Initialize the size from that of *source*.

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__(size=size, source=source, copy=copy)
        
        self._initialise_netcdf(source)
    #--- End: def
        
    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

.. versionadded:: 1.7

        '''
        return str(self.get_size(''))
    #--- End: def

    def equals(self, other, traceback=False, ignore_type=False):
        '''Whether two domain axis constructs are the same.

Equality is strict by default. This means that for two field domain
axis constructs to be considered equal::

* the axis sizes must be the same.

Any type of object may be tested but, in general, equality is only
possible with another domain axis construct, or a subclass of one. See
the *ignore_type* parameter.

NetCDF elements, such as netCDF variable and dimension names, do not
constitute part of the CF data model and so are not checked.

.. versionadded:: 1.7

:Parameters:

    other: 
        The object to compare for equality.

    traceback: `bool`, optional
        If True then print information about differences that lead to
        inequality.

    ignore_type: `bool`, optional
        Any type of object may be tested but, in general, equality is
        only possible with another domain axis construct, or a
        subclass of one. If *ignore_type* is True then then
        ``DomainAxis(source=other)`` is tested, rather than the
        ``other`` defined by the *other* parameter.

:Returns: 
  
    out: `bool`
        Whether the two domain axis constructs are equal.

**Examples:**

>>> d.equals(d)
True
>>> d.equals(d.copy())
True
>>> d.equals('not a domain axis')
False

>>> d = cfdm.DomainAxis(1)
>>> e = cfdm.DomainAxis(99)
>>> d.equals(e, traceback=True)
DomainAxis: Different axis sizes: 1 != 99
False

        '''
        pp = super()._equals_preprocess(other, traceback=traceback,
                                        ignore_type=ignore_type)
        if pp in (True, False):
            return pp
        
        other = pp

        # Check that each axis has the same size
        self_size  = self.get_size(None)
        other_size = other.get_size(None)
        if not self_size == other_size:
            if traceback:
                print("{0}: Different axis sizes: {1} != {2}".format(
			self.__class__.__name__, self_size, other_size))
            return False

        return True
    #--- End: def

    def name(self, default=None, ncvar=True, custom=None,
             all_names=False):
        '''TODO

By default the name is the first found of the following:

  3. If the *ncdim* parameter is True, the netCDF variable name (as
     returned by the `nc_get_variable` method), preceeded by the
     string ``'ncvar%'``.
  
  4. The value of the *default* parameter.

.. versionadded:: 1.7

:Parameters:

    default: optional
        If no name can be found then return the value of the *default*
        parameter. By default the default is `None`.

    ncvar: `bool`, optional

:Returns:

    out:
        The name.

**Examples**

>>> n = f.{+name}()
>>> n = f.{+name}(default='NO NAME')

        '''
        if all_names:
            out = []
            n = self.nc_get_dimension(None)
            if n is not None:
                out.append('ncdim%{0}'.format(n))
                
            if default is not None:
                out.append(default)

            return out
       
        n = self.nc_get_dimension(None)
        if n is not None:
            return 'ncdim%{0}'.format(n)
        
        return default
    #--- End: def

#--- End: class
