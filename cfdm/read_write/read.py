from __future__ import print_function
from past.builtins import basestring

import os

#from .. import __version__

from .. import CF

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

from ..data import (Data,
                    GatheredArray,
                    NetCDFArray,
                    RaggedContiguousArray,
                    RaggedIndexedArray,
                    RaggedIndexedContiguousArray)

from . import CFDMImplementation

from .netcdf import NetCDFRead

implementation = CFDMImplementation(
    cf_version = CF(),
    
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

def read(filename, external_files=None, create_field=None,
         verbose=False, _implementation=implementation):
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

.. versionadded:: 1.7

.. seealso:: `cfdm.write`, `cfdm.Field.create_field`,
             `cfdm.Field.read_report`

:Parameters:

    filename: `str`
        The file name or OPenDAP URL of the dataset.

        Relative paths are allowed, and standard tilde and shell
        parameter expansions are applied to the string.

        *Example:*
          The file ``file.nc`` in the user's home directory could be
          described by any of the following: ``'$HOME/file.nc'``,
          ``'${HOME}/file.nc'``, ``'~/file.nc'``,
          ``'~/tmp/../file.nc'``.
    
    external_files: (sequence of) `str`, optional
        Read external variables (i.e. variables which are named by
        attributes, but are not present, in the parent file given by
        the *filename* parameter) from the given external
        files. Ignored if the parent file does not contain a global
        "external_variables" attribute. Multiple external files may be
        provided, which are searched in random order for the required
        external variables.  
       
        If an external variable is not found in any external files, or
        is found in multiple external files, then the relevent
        metadata construct is still created, but without any metadata
        or data. In this case the construct's `!is_external` method
        will return `True`.

        *Example:*
          ``external_files='cell_measure.nc'``

        *Example:*
          ``external_files=['cell_measure_A.nc', 'cell_measure_O.nc']``

    create_field: (sequence of) `str`, optional
        Create extra, independent fields from the particular types of
        metadata constructs. The *create_field* parameter may be one,
        or a sequence, of:

          ==========================  ================================
          *create_field*              Metadata constructs
          ==========================  ================================
          ``'field_ancillary'``       Field ancillary constructs
          ``'domain_ancillary'``      Domain ancillary constructs
          ``'dimension_coordinate'``  Dimension coordinate constructs
          ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
          ``'cell_measure'``          Cell measure constructs
          ==========================  ================================

        *Example:*
          To create fields from auxiliary coordinate constructs:
          ``create_field='auxiliary_coordinate'`` or
          ``create_field=['auxiliary_coordinate']``.

        *Example:*
          To create fields from domain ancillary and cell measure
          constructs: ``create_field=['domain_ancillary',
          'cell_measure']``.

        An extra field construct created via the *create_field*
        parameter will have a domain limited to that which can be
        inferred from the corresponding netCDF variable, but without
        the connections that are defined by the parent netCDF data
        variable. It is possible to create independent fields from
        metadata constructs that do incorporate as much of the parent
        field construct's domain as possible by using the
        `~cfdm.Field.create_field` method of a returned field
        construct, instead of setting the *create_field* parameter.

:Returns:
    
    out: `list`
        The field constructs found in the dataset. The list may be
        empty.

**Examples:**

TODO

    '''
    # Parse the field parameter
    if create_field is None:
        create_field = ()
    elif isinstance(create_field, basestring):
        create_field = (create_field,)

    filename = os.path.expanduser(os.path.expandvars(filename))
    
    if os.path.isdir(filename):
        raise IOError("Can't read directory {}".format(filename))

    if not os.path.isfile(filename):
        raise IOError("Can't read non-existent file {}".format(filename))

    # ----------------------------------------------------------------
    # Read the fields in the file
    # ----------------------------------------------------------------
    return _read_a_file(filename,
                        external_files=external_files,
                        create_field=create_field,
                        verbose=verbose,
                        _implementation=_implementation)
#--- End: def

def _read_a_file(filename,
                 external_files=(),
                 create_field=(),
                 verbose=False,
                 _implementation=None):
    '''Read the contents of a single file into a field list.

:Parameters:

    filename: `str`
        The file name.
    
:Returns:

    out: `list`
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
        fields = netcdf.read(filename, external_files=external_files,
                             create_field=create_field,
                             verbose=verbose)
    else:
        raise IOError("Can't determine format of file {}".format(filename))

    # ----------------------------------------------------------------
    # Return the fields
    # ----------------------------------------------------------------
    return fields
#--- End: def
