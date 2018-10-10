from __future__ import print_function
from past.builtins import basestring

import os

from .. import __version__

from .. import (AuxiliaryCoordinate,
                CellMethod,
                CellMeasure,
                CoordinateReference,
                DimensionCoordinate,
                DomainAncillary,
                DomainAxis,
                Field,
                FieldAncillary,
                Bounds,
                Count,
                List,
                Index,
                CoordinateConversion,
                Datum)
#from ..auxiliarycoordinate import AuxiliaryCoordinate
#from ..cellmethod          import CellMethod
#from ..cellmeasure         import CellMeasure
#from ..coordinatereference import CoordinateReference
#from ..dimensioncoordinate import DimensionCoordinate
#from ..domainancillary     import DomainAncillary
#from ..domainaxis          import DomainAxis
#from ..field               import Field
#from ..fieldancillary      import FieldAncillary
#
#from ..bounds               import Bounds
#from ..count                 import Count
#from ..list                 import List
#from ..index                 import Index
#from ..coordinateconversion import CoordinateConversion
#from ..datum                import Datum

from ..data import (Data,
                    GatheredArray,
                    NetCDFArray,
                    RaggedContiguousArray,
                    RaggedIndexedArray,
                    RaggedIndexedContiguousArray)

from . import CFDMImplementation

from .netcdf import NetCDFRead

implementation = CFDMImplementation(version = __version__,

                                    AuxiliaryCoordinate = AuxiliaryCoordinate,
                                    CellMeasure         = CellMeasure,
                                    CellMethod          = CellMethod,
                                    CoordinateReference = CoordinateReference,
                                    DimensionCoordinate = DimensionCoordinate,
                                    DomainAncillary     = DomainAncillary,
                                    DomainAxis          = DomainAxis,
                                    Field               = Field,
                                    FieldAncillary      = FieldAncillary,
                                    
                                    Bounds = Bounds,
                                    List   = List,
                                    Index=Index,
                                    Count=Count,
                                    
                                    CoordinateConversion = CoordinateConversion,
                                    Datum                = Datum,
                                    
                                    Data                         = Data,
                                    GatheredArray                = GatheredArray,
                                    NetCDFArray                  = NetCDFArray,
                                    RaggedContiguousArray        = RaggedContiguousArray,
                                    RaggedIndexedArray           = RaggedIndexedArray,
                                    RaggedIndexedContiguousArray = RaggedIndexedContiguousArray,
                                    )

#netcdf = NetCDFRead(implementation)
# um = UMRead(implementation)

def read(filename, external_files=(), verbose=False,
         ignore_read_error=False, uncompress=True, field=None,
         _debug=False, _implementation=implementation):
    '''Read fields from netCDF files.

Files may be on disk or on a OPeNDAP server.

Any amount of netCDF files may be read.

.. versionadded:: 1.6

.. seealso:: `write`

:Examples 1:

>>> f = cfdm.read('file.nc')

:Parameters:

    filename: `str`
        A string giving the file name or OPenDAP URL from which to
        read fields. Various type of expansion are applied to the file
        name:
        
          ====================  ======================================
          Expansion             Description
          ====================  ======================================
          Tilde                 An initial component of ``~`` or
                                ``~user`` is replaced by that *user*'s
                                home directory.
           
          Environment variable  Substrings of the form ``$name`` or
                                ``${name}`` are replaced by the value
                                of environment variable *name*.
          ====================  ======================================

          *Example:*
            If the environment variable ``MYSELF`` has been set to
            ``david``, then ``'~$MYSELF/data.nc'`` is equivalent to
            ``'~david/data.nc'``.
  
    verbose: `bool`, optional
        If True then print information to stdout.
    
    ignore_read_error: `bool`, optional
        If True then ignore any file which raises an IOError whilst
        being read, as would be the case for an empty file, unknown
        file format, etc. By default the IOError is raised.
    
    field: (sequence of) `str`, optional
        Create independent fields from field components. The *field*
        parameter may be one, or a sequence, of:

          ======================  ====================================
          *field*                 Field components
          ======================  ====================================
          ``'field_ancillary'``   Field ancillary objects
          ``'domain_ancillary'``  Domain ancillary objects
          ``'dimension'``         Dimension coordinate objects
          ``'auxiliary'``         Auxiliary coordinate objects
          ``'measure'``           Cell measure objects
          ``'all'``               All of the above
          ======================  ====================================

            *Example:*
              To create fields from auxiliary coordinate objects:
              ``field='auxiliary'`` or ``field=['auxiliary']``.

            *Example:*
              To create fields from domain ancillary and cell measure
              objects: ``field=['domain_ancillary', 'measure']``.

:Returns:
    
    out: `list`
        A list of the fields found in the input file(s). The list may
        be empty.

:Examples 2:

>>> f = cf.read('file*.nc')
>>> f
[<CF Field: pmsl(30, 24)>,
 <CF Field: z-squared(17, 30, 24)>,
 <CF Field: temperature(17, 30, 24)>,
 <CF Field: temperature_wind(17, 29, 24)>]

>>> cf.read('file*.nc')[0:2]
[<CF Field: pmsl(30, 24)>,
 <CF Field: z-squared(17, 30, 24)>]

>>> cf.read('file*.nc')[-1]
<CF Field: temperature_wind(17, 29, 24)>

>>> cf.read('file*.nc', select='units:K)
[<CF Field: temperature(17, 30, 24)>,
 <CF Field: temperature_wind(17, 29, 24)>]

>>> cf.read('file*.nc', select='ncvar%ta')
<CF Field: temperature(17, 30, 24)>

>>> cf.read('file*.nc', select={'standard_name': '.*pmsl*', 'units':['K', 'Pa']})
<CF Field: pmsl(30, 24)>

>>> cf.read('file*.nc', select={'units':['K', 'Pa']})
[<CF Field: pmsl(30, 24)>,
 <CF Field: temperature(17, 30, 24)>,
 <CF Field: temperature_wind(17, 29, 24)>]

    '''
    # Parse the field parameter
    if field is None:
        field = ()
    elif isinstance(field, basestring):
        field = (field,)

    filename = os.path.expanduser(os.path.expandvars(filename))
    
    if os.path.isdir(filename):
        raise IOError("Can't read directory {}".format(filename))

    if not os.path.isfile(filename):
        raise IOError("Can't read non-existent file {}".format(filename))

    # ----------------------------------------------------------------
    # Read the fields in the file
    # ----------------------------------------------------------------
    fields = _read_a_file(filename,
                          external_files=external_files,
                          ignore_read_error=ignore_read_error,
                          verbose=verbose,
                          field=field,
                          uncompress=uncompress,
                          _debug=_debug,
                          _implementation=_implementation)
    
    if verbose:
        print("Read {0} field{1} from file {2}".format( 
            len(fields), _plural(field_counter), filename))
   
    return fields
#--- End: def

def _plural(n):
    '''Return a suffix which reflects a word's plural.

    '''
    return 's' if n !=1 else ''

def _read_a_file(filename,
                 external_files=(),
                 ignore_read_error=False,
                 verbose=False,
                 field=(),
                 uncompress=True,
                 _debug=False,
                 _implementation=None):
    '''

Read the contents of a single file into a field list.

:Parameters:

    filename: `str`
        The file name.

    ignore_read_error: `bool`, optional
        If True then return an empty field list if reading the file
        produces an IOError, as would be the case for an empty file,
        unknown file format, etc. By default the IOError is raised.
    
    verbose: `bool`, optional
        If True then print information to stdout.
    
:Returns:

    out: `list`
        The fields in the file.

'''
    # ----------------------------------------------------------------
    # Initialise the netCDF read object
    # ----------------------------------------------------------------
    netcdf = NetCDFRead(_implementation)

    # ----------------------------------------------------------------
    # Read the file into fields.
    # ----------------------------------------------------------------
    if netcdf.is_netcdf_file(filename):
        fields = netcdf.read(filename, field=field, verbose=verbose,
                             uncompress=uncompress, _debug=_debug)
    else:
        raise IOError("Can't determine format of file {}".format(filename))

    # ----------------------------------------------------------------
    # Return the fields
    # ----------------------------------------------------------------
    return fields
#--- End: def
