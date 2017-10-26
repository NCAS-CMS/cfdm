import glob
import os

from .functions import flat

from .auxiliarycoordinate import AuxiliaryCoordinate
from .cellmethod          import CellMethod
from .cellmeasure         import CellMeasure
from .coordinatereference import CoordinateReference
from .dimensioncoordinate import DimensionCoordinate
from .domainancillary     import DomainAncillary
from .domainaxis          import DomainAxis
from .field               import Field
from .fieldancillary      import FieldAncillary

from .bounds    import Bounds
#from .fieldlist import FieldList
from .units     import Units
from .netcdf2   import NetCDF

from .data.data  import Data
from .data.array import NetCDFArray


netcdf = NetCDF(mode='read',
                AuxiliaryCoordinate = AuxiliaryCoordinate,
                CellMeasure         = CellMeasure,
                CellMethod          = CellMethod,
                CoordinateReference = CoordinateReference,
                DimensionCoordinate = DimensionCoordinate,
                DomainAncillary     = DomainAncillary,
                DomainAxis          = DomainAxis,
                Field               = Field,
                FieldAncillary      = FieldAncillary,
                
                Bounds    = Bounds,
                Data      = Data,
#                FieldList = FieldList,
                Units     = Units,        
                
                NetCDFArray = NetCDFArray)

def read(files, verbose=False, ignore_read_error=False, squeeze=False,
         unsqueeze=False, uncompress=True, field=None, _debug=False):
    '''Read fields from netCDF files.

Files may be on disk or on a OPeNDAP server.

Any amount of netCDF files may be read.

.. seealso:: `write`

:Examples 1:

>>> f = read('file.nc')

:Parameters:

    files: (arbitrarily nested sequence of) `str`

        A string or arbitrarily nested sequence of strings giving the
        file names or OPenDAP URLs from which to read fields. Various
        type of expansion are applied to the file names:
        
          ====================  ======================================
          Expansion             Description
          ====================  ======================================
          Tilde                 An initial component of ``~`` or
                                ``~user`` is replaced by that *user*'s
                                home directory.
           
          Environment variable  Substrings of the form ``$name`` or
                                ``${name}`` are replaced by the value
                                of environment variable *name*.

          Pathname              A string containing UNIX file name
                                metacharacters as understood by the
                                :py:obj:`glob` module is replaced by
                                the list of matching file names. This
                                type of expansion is ignored for
                                OPenDAP URLs.
          ====================  ======================================
    
        Where more than one type of expansion is used in the same
        string, they are applied in the order given in the above
        table.

          Example: If the environment variable *MYSELF* has been set
          to the "david", then ``'~$MYSELF/*.nc'`` is equivalent to
          ``'~david/*.nc'``, which will read all netCDF files in the
          user david's home directory.
  
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

        .. versionadded:: 1.0.4

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
    if squeeze and unsqueeze:
        raise ValueError("The squeeze and unsqueeze parameters can not both be True")

    # Initialize the output list of fields
    field_list = [] #FieldList()

    # Parse the field parameter
    if field is None:
        field = ()
    elif isinstance(field, basestring):
        field = (field,)

    # Count the number of fields (in all files) and the number of
    # files
    field_counter = -1
    file_counter  = 0

    for file_glob in flat(files):

        # Expand variables
        file_glob = os.path.expanduser(os.path.expandvars(file_glob))

        if file_glob.startswith('http://'):
            # Do not glob a URL
            files2 = (file_glob,)
        else:
            # Glob files on disk
            files2 = glob.glob(file_glob)
            
            if not files2 and not ignore_read_error:
                open(file_glob, 'rb')
                
            for x in files2:
                if os.path.isdir(x):
                    raise IOError("Can't read directory {}".format(x))
        #--- End: if

        for filename in files2:
            if verbose:
                print 'File: {0}'.format(filename)
                
            # --------------------------------------------------------
            # Read the file into fields
            # --------------------------------------------------------
            fields = _read_a_file(filename,
                                  ignore_read_error=ignore_read_error,
                                  verbose=verbose,
                                  field=field,
                                  uncompress=uncompress,
                                  _debug=_debug)

            # --------------------------------------------------------
            # Add this file's fields to those already read from other
            # files
            # --------------------------------------------------------
            field_list.extend(fields)
   
            field_counter = len(field_list)
            file_counter += 1
        #--- End: for            
    #--- End: for     
            
    # ----------------------------------------------------------------
    # Squeeze or unsqueeze size one dimensions from the data arrays
    # ----------------------------------------------------------------
    if squeeze:
        for f in field_list:
            f.squeeze(copy=False) 
    elif unsqueeze:
        for f in field_list:
            f.unsqueeze(copy=False)
            
    # Print some informative messages
    if verbose:
        print("Read {0} field{1} from {2} file{3}".format( 
            field_counter, _plural(field_counter),
            file_counter , _plural(file_counter)))
    #--- End: if
   
    return field_list
#--- End: def

def _plural(n):
    '''Return a suffix which reflects a word's plural.

    '''
    return 's' if n !=1 else ''

def _read_a_file(filename,
                 ignore_read_error=False,
                 verbose=False,
                 field=(),
                 uncompress=True,
                 _debug=False):
    '''

Read the contents of a single file into a field list.

:Parameters:

    filename: `str`
        The file name.

    aggregate_options: `dict`, optional
        The keys and values of this dictionary may be passed as
        keyword parameters to an external call of the aggregate
        function.

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
    # Check the file type
    ftype = file_type(filename)        
    
    # ----------------------------------------------------------------
    # Still here? Read the file into fields.
    # ----------------------------------------------------------------
    fields = netcdf.read(filename, field=field, verbose=verbose,
                         uncompress=uncompress, _debug=_debug)
        
    # ----------------------------------------------------------------
    # Return the fields
    # ----------------------------------------------------------------
    return fields
#--- End: def

def file_type(filename):
    '''

:Parameters:

    filename: `str`
        The file name.

:Returns:

    out: `str`
        The format type of the file.

:Examples:

>>> filetype = file_type(filename)

'''
    if netcdf.is_netcdf_file(filename):
        return 'netCDF'

    # Still here?
    raise IOError("Can't determine format of file {}".format(filename))
#--- End: def
