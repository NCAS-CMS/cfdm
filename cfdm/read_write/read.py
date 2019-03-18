from __future__ import print_function
from past.builtins import basestring

import os

from . import implementation

from .netcdf import NetCDFRead


_implementation = implementation()

def read(filename, external=None, extra=None, verbose=False,
         warnings=False, _implementation=_implementation):
    '''Read field constructs from a dataset.

The dataset may be a netCDF file on disk or on an OPeNDAP server.

The returned field constructs are sorted by the netCDF variable names
of their corresponding data variables.

**Performance**

Descriptive properties are always read into memory, but lazy loading
is employed for all data arrays, which means that no data is read into
memory until the data is required for inspection or to modify the
array contents. This maximises the number of field constructs that may
be read within a session, and makes the read operation fast.

**NetCDF unlimited dimensions**

Domain axis constructs that correspond to NetCDF unlimited dimensions
may be accessed with the `~cfdm.Field.nc_unlimited_dimensions`
`~cfdm.Field.nc_set_unlimited_dimensions` and
`~cfdm.Field.nc_clear_unlimited_dimensions` methods of a field
construct.

**CF-compliance**

If the dataset is partially CF-compliant to the extent that it is not
possible to unambiguously map an element of the netCDF dataset to an
element of the CF data model, then a field construct is still
returned, but may be incomplete. This is so that datasets which are
partially conformant may nonetheless be modified in memory and written
to new datasets.

Such "structural" non-compliance would occur, for example, if the
"coordinates" attribute of a CF-netCDF data variable refers to another
variable that does not exist, or refers to a variable that spans a
netCDF dimension that does not apply to the data variable. Other types
of non-compliance are not checked, such whether or not controlled
vocabularies have been adhered to. The structural compliance of the
dataset may be checked with the `~cfdm.Field.dataset_compliance`
method of the field construct, as well as optionally displayed when
the dataset is read by setting the *warnings* parameter.

.. versionadded:: 1.7.0

.. seealso:: `cfdm.write`, `cfdm.Field.convert`,
             `cfdm.Field.nc_unlimited_dimensions`,
             `cfdm.Field.dataset_compliance`

:Parameters:

    filename: `str`
        The file name or OPenDAP URL of the dataset.

        Relative paths are allowed, and standard tilde and shell
        parameter expansions are applied to the string.

        *Parameter example:*
          The file ``file.nc`` in the user's home directory could be
          described by any of the following: ``'$HOME/file.nc'``,
          ``'${HOME}/file.nc'``, ``'~/file.nc'``,
          ``'~/tmp/../file.nc'``.
    
    external: (sequence of) `str`, optional
        Read external variables (i.e. variables which are named by
        attributes, but are not present, in the parent file given by
        the *filename* parameter) from the given external
        files. Ignored if the parent file does not contain a global
        "external_variables" attribute. Multiple external files may be
        provided, which are searched in random order for the required
        external variables.  
       
        If an external variable is not found in any external files, or
        is found in multiple external files, then the relevant
        metadata construct is still created, but without any metadata
        or data. In this case the construct's `!is_external` method
        will return `True`.

        *Parameter example:*
          ``external='cell_measure.nc'``

        *Parameter example:*
          ``external=['cell_measure.nc']``

        *Parameter example:*
          ``external=('cell_measure_A.nc', 'cell_measure_O.nc')``

    extra: (sequence of) `str`, optional
        Create extra, independent fields from netCDF variables that
        correspond to particular types metadata constructs. The
        *extra* parameter may be one, or a sequence, of:

          ==========================  ================================
          *extra*                     Metadata constructs
          ==========================  ================================
          ``'field_ancillary'``       Field ancillary constructs
          ``'domain_ancillary'``      Domain ancillary constructs
          ``'dimension_coordinate'``  Dimension coordinate constructs
          ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
          ``'cell_measure'``          Cell measure constructs
          ==========================  ================================

        *Parameter example:*
          To create fields from auxiliary coordinate constructs:
          ``extra='auxiliary_coordinate'`` or
          ``extra=['auxiliary_coordinate']``.

        *Parameter example:*
          To create fields from domain ancillary and cell measure
          constructs: ``extra=['domain_ancillary', 'cell_measure']``.

        An extra field construct created via the *extra* parameter
        will have a domain limited to that which can be inferred from
        the corresponding netCDF variable, but without the connections
        that are defined by the parent netCDF data variable. It is
        possible to create independent fields from metadata constructs
        that do incorporate as much of the parent field construct's
        domain as possible by using the `~cfdm.Field.convert` method
        of a returned field construct, instead of setting the *extra*
        parameter.

    verbose: `bool`, optional
        If True then print a description of how the contents of the
        netCDF file were parsed and mapped to CF data model
        constructs.

    warnings: `bool`, optional
        If True then print warnings when an output field construct is
        incomplete due to structural non-compliance of the dataset. By
        default such warnings are not displayed.
        
    _implementation: (subclass of) `CFDMImplementation`, optional
        Define the CF data model implementation that provides the
        returned field constructs.

:Returns:
    
    `list`
        The field constructs found in the dataset. The list may be
        empty.

**Examples:**

>>> x = cfdm.read('file.nc')
>>> print(type(x))
<type 'list'>

Read a file and create field constructs from CF-netCDF data variables
as well as from the netCDF variables that correspond to particular
types metadata constructs:

>>> f = cfdm.read('file.nc', extra='domain_ancillary')
>>> g = cfdm.read('file.nc', extra=['dimension_coordinate', 
...                                 'auxiliary_coordinate'])

Read a file that contains external variables:

>>> h = cfdm.read('parent.nc')
>>> i = cfdm.read('parent.nc', external='external.nc')
>>> j = cfdm.read('parent.nc', external=['external1.nc', 'external2.nc'])

    '''
    # Parse the field parameter
    if extra is None:
        extra = ()
    elif isinstance(extra, basestring):
        extra = (extra,)

    filename = os.path.expanduser(os.path.expandvars(filename))
    
    if os.path.isdir(filename):
        raise IOError("Can't read directory {}".format(filename))

    if not os.path.isfile(filename):
        raise IOError("Can't read non-existent file {}".format(filename))

    # ----------------------------------------------------------------
    # Read the fields in the file
    # ----------------------------------------------------------------
    return _read_a_file(filename, external=external, extra=extra,
                        verbose=verbose, warnings=warnings,
                        _implementation=_implementation)
#--- End: def

def _read_a_file(filename, external=(), extra=(), verbose=False,
                 warnings=False, _implementation=None):
    '''Read the contents of a single file into a field list.

:Parameters:

    filename: `str`
        The file name.
    
:Returns:

    `list`
        The fields in the file.

    '''
    # ----------------------------------------------------------------
    # Initialise a netCDF read object
    # ----------------------------------------------------------------
    netcdf = NetCDFRead(_implementation)

    # ----------------------------------------------------------------
    # Read the file into fields.
    # ----------------------------------------------------------------
    if netcdf.is_netcdf_file(filename):
        fields = netcdf.read(filename, external=external, extra=extra,
                             verbose=verbose, warnings=warnings)
    else:
        raise IOError("Can't determine format of file {}".format(filename))

    # ----------------------------------------------------------------
    # Return the fields
    # ----------------------------------------------------------------
    return fields
#--- End: def
