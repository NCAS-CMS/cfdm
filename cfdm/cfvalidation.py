import logging
import os
import pprint
import re

from functools import lru_cache

# Prefer using built-in urllib to extract XML from cf-convention.github.io repo
# over the 'github' module to use the GitHub API directly, because it avoids
# the need for another dependency to the CF Data Tools.
from urllib import request

# To parse the XML - better than using manual regex parsing!
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


# This is the data at the repo location:
# 'github.com/cf-convention/cf-convention.github.io/blob/main/Data/'
# 'cf-standard-names/current/src/cf-standard-name-table.xml' but use this
# form under 'https://raw.githubusercontent.com/' for raw XML content only.
# Note: the raw XML is also made available at:
# 'cfconventions.org/Data/cf-standard-names/current/src/cf-standard-name-'
# 'table.xml', is that a better location to grab from (may be more stable)?
STD_NAME_CURRENT_XML_URL = (
    "https://raw.githubusercontent.com/"
    "cf-convention/cf-convention.github.io/refs/heads/main/Data/"
    "cf-standard-names/current/src/cf-standard-name-table.xml"
)


def _extract_names_from_xml(snames_xml):
    """TODO."""
    root = ET.fromstring(snames_xml)
    # Want all <entry id="..."> elements. Note the regex this corresponds
    # to, from SLB older code, is 're.compile(r"<entry id=\"(.+)\">")' but
    # using the ElementTree is a much more robust means to extract
    all_standard_names = [
        entry.attrib["id"] for entry in root.findall(".//entry")
    ]

    return all_standard_names


@lru_cache
def get_all_current_standard_names():
    """TODO."""
    logger.info(
        "Retrieving XML for set of current standard names from: ",
        STD_NAME_CURRENT_XML_URL
    )  # pragma: no cover
    with request.urlopen(STD_NAME_CURRENT_XML_URL) as response:
        all_snames_xml = response.read()

    logger.debug(
        f"Successfully retrived set of {len(all_snames_xml)} standard names"
    )  # pragma: no cover

    return _extract_names_from_xml(all_snames_xml)
