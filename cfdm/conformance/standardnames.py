import datetime
import logging
import os
import pickle
import xml.etree.ElementTree as ET
from functools import lru_cache

# Prefer using built-in urllib to extract XML from cf-convention.github.io repo
# over the 'github' module to use the GitHub API directly, because it avoids
# the need for another dependency to the CF Data Tools.
from urllib import request

logger = logging.getLogger(__name__)


# This is the data at the repo location:
# 'github.com/cf-convention/cf-convention.github.io/blob/main/Data/'
# 'cf-standard-names/current/src/cf-standard-name-table.xml' but use this
# form under 'https://raw.githubusercontent.com/' for raw XML content only.
# Note: the raw XML is also made available at:
# 'cfconventions.org/Data/cf-standard-names/current/src/cf-standard-name-'
# 'table.xml', but that is less reliable (hit in the past by domain issues).
_STD_NAME_CURRENT_XML_URL = (
    "https://raw.githubusercontent.com/"
    "cf-convention/cf-convention.github.io/refs/heads/main/Data/"
    "cf-standard-names/current/src/cf-standard-name-table.xml"
)
DEFAULT_TIMEOUT_SECONDS = 5

# Cache config.
CACHE_DIR = ".cf"
CACHE_PICKLE_FILENAME_NOALIASES = "standard_names.pickle"
CACHE_PICKLE_FILENAME_WITHALIASES = "standard_names_with_aliases.pickle"
CACHE_FORMAT_VERSION = 1
CACHE_MAX_AGE_DAYS = 30


class StandardNameTableUnavailableError(Exception):
    """Raise when the standard names table cannot be accessed."""

    def __init__(self, reason=None):
        """**Initialisation**"""
        message = (
            "Unable to retrieve the CF standard name table. Skipping "
            "validation of any encoded (computed)_standard_names."
        )
        if reason is not None:
            message += f" Reason: {reason}"

        super().__init__(message)


def _extract_names_from_xml(snames_xml, include_aliases):
    """Extract all names from a valid Standard Name Table XML document.

    Whether or not to include registered aliases is dependent on the value
    of the `include_aliases` flag.

    .. versionadded:: 1.13.2.0

     :Parameters:

         snames_xml: `bytes`
             Bytes representing an XML file of any
             valid Standard Name Table XML document, or mocked-up
             equivalent form. 'entry id' items are extracted, along
             with 'alias id' items if requested.

         include_aliases: `bool`
             If `True`, include standard names that are aliases
             rather than strict entries of the input table. By
             default this is `False` so that aliases are excluded.

     :Returns:

         `frozenset`
             A set of all CF Conventions standard names in the
             given version of the table, including aliases if
             requested.

    """
    root = ET.fromstring(snames_xml)
    # Want all <entry id="..."> elements. Note the regex this corresponds
    # to, from SLB older code, is 're.compile(r"<entry id=\"(.+)\">")' but
    # using the ElementTree is a much more robust means to extract
    all_standard_names = {
        entry.attrib["id"] for entry in root.findall(".//entry")
    }
    if include_aliases:
        all_standard_names.update(
            entry.attrib["id"] for entry in root.findall(".//alias")
        )

    # Set is more performant than a list for membership testing, so convert.
    # Use a frozen set form so users can't edit it (by mistake or otherwise!).
    return frozenset(all_standard_names)


def _extract_table_version_from_xml(snames_xml):
    """Extract table version from a valid Standard Name Table XML document.

    .. versionadded:: NEXTVERSION

     :Parameters:

         snames_xml: `bytes`
             Bytes representing an XML file of any
             valid Standard Name Table XML document, or mocked-up
             equivalent form. 'version_number' is extracted.

     :Returns:

         `str`
             The version of the standard names table of the XML document.

    """
    root = ET.fromstring(snames_xml)
    return root.findtext("version_number")


def _get_cache_file_path(include_aliases=False):
    """Return the filesystem path to the standard names pickle cache file.

    .. versionadded:: NEXTVERSION

     :Parameters:

         include_aliases: `bool`, optional
             If `True`, return the path of the file which caches
             standard names inclusive of standard name aliases, else
             and by default return the path for the cache file which
             does not include aliases.

     :Returns:

         `str`
             The filesystem path to the cache file.

    """
    cache_dir = os.path.join(
        os.path.expanduser("~"),
        CACHE_DIR,
    )

    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    if include_aliases:
        filename = CACHE_PICKLE_FILENAME_WITHALIASES
    else:
        filename = CACHE_PICKLE_FILENAME_NOALIASES

    return os.path.join(cache_dir, filename)


def _cache_standard_names_to_dotfile(
    standard_names,
    table_version,
    include_aliases=False,
):
    """Create a pickle cache of the frozenset of fetched standard names.

    .. versionadded:: NEXTVERSION

     :Parameters:

         standard_names: `frozenset`
             The set of all CF Conventions standard names in the
             given version of the table, including aliases if
             requested, to save to a new cache file.

         table_version: `str`
             The version of the standard names table of the XML
             document, to register as metadata for the cache file.

         include_aliases: `bool`, optional
             Set to `True` if the file will cache standard names
             inclusive of standard name aliases, else and by
             default the cache file name is chosen to reflect
             that it does not include aliases.

     :Returns:

         `str`
             The filesystem path to the newly-created cache file.

    """
    cache_file = _get_cache_file_path(include_aliases=include_aliases)

    # Include some metadata with the frozen set of names, to allow us to detect if
    # the dotfile is stale or of an old version
    cache = {
        "cache_format_version": CACHE_FORMAT_VERSION,
        "standard_names": standard_names,
        "include_aliases": include_aliases,
        "table_version": table_version,
        "cached_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    with open(cache_file, "wb") as f:
        pickle.dump(cache, f, protocol=pickle.HIGHEST_PROTOCOL)

    logger.info(
        f"Cached set of fetched standard names to dotfile at {cache_file}"
    )  # pragma: no cover

    return cache_file


def _load_standard_names_from_dotfile(include_aliases=False):
    """Attempt to load and open a pickled dotfile cache of standard names.

    .. versionadded:: NEXTVERSION

     :Parameters:

         include_aliases: `bool`, optional
             If `True`, try to load and open the file which caches
             standard names inclusive of standard name aliases, else
             and by default load and open the path for the cache file
             which does not include aliases.

     :Returns:

         `frozenset` or `None`
             The set of all CF Conventions standard names taken from
             the pickled dotfile cache or `None` if a valid cache
             file could not be opened.

    """
    cache_file = _get_cache_file_path(include_aliases=include_aliases)

    try:
        with open(cache_file, "rb") as f:
            cache = pickle.load(f)
    except (
        IOError,
        EOFError,
        pickle.UnpicklingError,
    ):
        return

    if cache.get("cache_format_version") != CACHE_FORMAT_VERSION:
        return

    if cache.get("include_aliases") != include_aliases:
        return

    cached_at = datetime.datetime.fromisoformat(cache["cached_at"])

    age = datetime.datetime.now(datetime.timezone.utc) - cached_at

    if age > datetime.timedelta(days=CACHE_MAX_AGE_DAYS):
        logger.info("Ignoring stale CF standard name cache.")
        return

    logger.info(
        f"Loaded set of fetched standard names from dotfile at {cache_file}"
    )  # pragma: no cover

    return cache["standard_names"]


@lru_cache
def get_all_current_standard_names(include_aliases=False):
    """Get list of all CF Standard Names from the current table.

    Entries are always returned from the current table. By default aliases
    are not included in the output but can also be included by setting the
    `include_aliases` flag to `True`.

    Relies on access to the XML which encodes the table of names from the
    canonical location stored under the repository
    `github.com/cf-convention/cf-convention.github.io/`, and
    raises the exception `StandardNameTableUnavailableError` if it is
    not accessible until timeout.

    .. versionadded:: 1.13.2.0

     :Parameters:

         include_aliases: `bool`, optional
             If `True`, include standard names that are aliases
             rather than strict entries of the current table. By
             default this is `False` so that aliases are excluded.

     :Returns:

         `frozenset`
             A set of all CF Conventions standard names in the
             current version of the table, including aliases if
             requested.

    """
    logger.info(
        "Retrieving XML for set of current standard names from: ",
        _STD_NAME_CURRENT_XML_URL,
    )  # pragma: no cover

    # First attempt to get a cached version from a pickle of the frozenset
    # of names that may have been fetched and stored at an earlier time
    pickled_names = _load_standard_names_from_dotfile(
        include_aliases=include_aliases
    )
    if pickled_names:
        return pickled_names

    try:
        with request.urlopen(
            _STD_NAME_CURRENT_XML_URL,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        ) as response:
            all_snames_xml = response.read()

        logger.debug(
            f"Successfully retrieved list of {len(all_snames_xml)} "
            "standard names"
        )  # pragma: no cover
    except (
        # urllib failures surface as OSError subclasses e.g. error.URLError
        OSError,
        TimeoutError,
    ) as exc:
        logger.warning(
            "Unable to retrieve CF standard names so skipping validation "
            f"against standard name table. Reason: {exc}",
        )
        # Note that lru_cache doesn't cache exceptions, so best return this here
        # but it can be caught later to prevent erroring for bypassing validation
        raise StandardNameTableUnavailableError from exc

    # Be careful even with parsing since there's a small chance the XML could be bad
    try:
        names_set = _extract_names_from_xml(
            all_snames_xml,
            include_aliases=include_aliases,
        )
    except ET.ParseError as exc:
        raise StandardNameTableUnavailableError(
            "Downloaded CF standard name table is not valid XML and cannot be parsed."
        ) from exc

    # Successfully extracted set of all current names. Cache to dotfile for future use.
    table_version = _extract_table_version_from_xml(all_snames_xml)
    _cache_standard_names_to_dotfile(
        names_set,
        table_version,
        include_aliases=include_aliases,
    )

    return names_set
