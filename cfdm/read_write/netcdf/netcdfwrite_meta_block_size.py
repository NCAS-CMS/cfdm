import logging
from math import ceil, prod

import numpy as np

from ...functions import is_log_level_debug

logger = logging.getLogger(__name__)


def _calculate_chunk_metadata(shape, contiguous, chunksizes):
    """Calculates the HDF5 B-tree metadata for a data aray.

    Accounts for data chunks.

    .. versionadded: (cfdm) 1.13.3.0

    :Parameters:

        shape: `tuple` of `int`
            The shape of the data array.

        contiguous: `bool` or sequence of `int`
            True if the data array is contiguous.

        chunksizes: `None` or sequence of `int`
            The shape of the data array chunks. Ignored if the data
            array is contiguous (in which case it may be `None`).

    :Returns:

        `int`
            The HDF5 B-tree metadata size for the data aray.

    """
    if contiguous or chunksizes is None:
        # Contiguous datasets have no chunk index
        return 32

    rank = len(shape)

    # Total Number of Chunks
    num_chunks = prod([ceil(n / c) for n, c in zip(shape, chunksizes)])

    # Maximum memory size of a single B-Tree Node for this rank
    entry_size = 16 + (8 * rank)
    node_size_bytes = 24 + (32 * entry_size) + (33 * 8)

    # Simulate the B-Tree allocation to find total nodes
    current_level_nodes = ceil(num_chunks / 32.0)
    total_nodes = current_level_nodes

    while current_level_nodes > 1:
        current_level_nodes = ceil(current_level_nodes / 32.0)
        total_nodes += current_level_nodes

    return total_nodes * node_size_bytes


class NetCDFMetaBlockSize:
    """Mixin class for calculating the HDF5 metadata block size.

    .. versionadded: (cfdm) 1.13.3.0

    """

    def _calculate_meta_block_size(self):
        """Estimate the HDF5 metadata block size for the dataset.

        .. versionadded: (cfdm) 1.13.3.0

        :Returns:

            `int`
                The HDF5 metadata block size, in bytes.

        """
        g = self.write_vars

        # Space for group metadata (there is always the root group,
        # whose creation is not stored in g["write_operations"], so
        # this starts non-zero)
        meta_block_groups = 2048
        # Space for attributes
        meta_block_attributes = 0
        # Space for data chunk metdata
        meta_block_chunk_metadata = 0
        # Space for dimension metdata
        meta_block_dimensions = 0

        # Count the number of varibales in the dataset
        n_variables = 0

        for method, kwargs in g["write_operations"]:
            match method:
                case "_set_attributes_work":
                    for name, value in kwargs["attributes"].items():
                        # Meta block space for an attribute
                        size = 51 + len(name.encode("utf-8"))
                        try:
                            size += len(value.encode("utf-8"))
                        except AttributeError:
                            size += np.asanyarray(value).nbytes

                        meta_block_attributes += size

                case "_createVariable_work":
                    n_variables += 1

                    # Meta block space for a variable
                    size = (
                        80
                        + len(kwargs["varname"].encode("utf-8"))
                        + 8 * len(kwargs.get("dimensions", ()))
                    )
                    size += _calculate_chunk_metadata(
                        kwargs.get("shape", ()),
                        kwargs.get("contiguous", True),
                        kwargs.get("chunksizes"),
                    )

                    meta_block_chunk_metadata += size

                case "_createDimension_work":
                    # Meta block space for a dimension
                    ncdim = kwargs["ncdim"]
                    n_referencing_vars = sum(
                        1
                        for m, k in g["write_operations"]
                        if m == "_createVariable_work"
                        and ncdim in k.get("dimensions", ())
                    )
                    size = 224 + 16 * n_referencing_vars
                    meta_block_dimensions += size

                case "_createGroup_work":
                    # Meta block space for a group
                    size = 2048 + 40 + len(kwargs["group_name"])
                    meta_block_groups += size

        # Meta block space for the netCDF overhead (e.g._Netcdf4Dimid
        # attributes)
        meta_block_netcdf_overhead = 4096 + 512 * n_variables

        meta_block_size = (
            meta_block_groups
            + meta_block_attributes
            + meta_block_chunk_metadata
            + meta_block_dimensions
            + meta_block_netcdf_overhead
        )

        # We multiply the minimum by an amount greater than 1 to
        # account for HDF5's dynamic, non-linear memory allocation
        # behaviours.
        hdf5_expansion_factor = g["hdf5_expansion_factor"]
        meta_block_size *= hdf5_expansion_factor

        # Round the meta block size up to a multiple of the OS
        # page size
        os_page_size = 4096
        meta_block_size = ceil(meta_block_size / os_page_size) * os_page_size

        if is_log_level_debug(logger):
            logger.debug(
                f"meta_block_attributes       = {meta_block_attributes}\n"
                f"meta_block_chunk_metadata   = {meta_block_chunk_metadata}\n"
                f"meta_block_dimensions       = {meta_block_dimensions}\n"
                f"meta_block_groups           = {meta_block_groups}\n"
                f"meta_block_netCDF_overhead  = {meta_block_netcdf_overhead}\n"
                f"hdf5_expansion_factor       = {hdf5_expansion_factor}\n"
                f"Total meta_block_size = {meta_block_size}"
            )  # pragma: no cover

        # Leave this here for convenient debugging!
        # print(
        #     f"meta_block_attributes       = {meta_block_attributes}\n"
        #     f"meta_block_chunk_metadata   = {meta_block_chunk_metadata}\n"
        #     f"meta_block_dimensions       = {meta_block_dimensions}\n"
        #     f"meta_block_groups           = {meta_block_groups}\n"
        #     f"meta_block_netCDF_overhead  = {meta_block_netcdf_overhead}\n"
        #     f"hdf5_expansion_factor       = {hdf5_expansion_factor}\n"
        #     f"Total meta_block_size = {meta_block_size}"
        # )

        return meta_block_size
