import os
import pprint
import re

# Prefer using built-in urllib to extract XML from cf-convention.github.io repo
# over the 'github' module to use the GitHub API directly, because it avoids
# the need for another dependency to the CF Data Tools.
from urllib import request

# TO parse the XML - better than using manual regex parsing!
import xml.etree.ElementTree as ET

# I.e. the data at repo location:
# 'https://github.com/cf-convention/cf-convention.github.io/blob/main/Data/'
# 'cf-standard-names/current/src/cf-standard-name-table.xml' but use this
# form under 'https://raw.githubusercontent.com' for raw XML content only
STD_NAME_CURRENT_XML_URL = (
    "https://raw.githubusercontent.com/"
    "cf-convention/cf-convention.github.io/refs/heads/main/Data/"
    "cf-standard-names/current/src/cf-standard-name-table.xml"
)
SAVE_DIR = "snames_cache"

XML_STD_NAME_TAG_PATTERN = re.compile(r"<entry id=\"(.+)\">")


def extract_names_from_xml(snames_xml):
    """TODO."""
    root = ET.fromstring(snames_xml)
    # Want  all <entry id="..."> elements. Note the regex this corresponds
    # to, from SLB older code, is 're.compile(r"<entry id=\"(.+)\">")' but
    # using the ElementTree is a much more robust means to extract!
    all_snames = [
        entry.attrib["id"] for entry in root.findall(".//entry")
    ]

    return all_snames


def get_all_current_standard_names():
    """TODO."""
    ###print ("Retrieving XML from:", STD_NAME_CURRENT_XML_URL)
    with request.urlopen(STD_NAME_CURRENT_XML_URL) as response:
        all_snames_xml = response.read()

    all_snames = extract_names_from_xml(all_snames_xml)
    total = len(all_snames)

    return all_snames, total


def main():
    """TODO."""
    names, total = get_all_current_standard_names()

    pprint.pprint(names)
    print(f"Done with total of {len(names)} names parsed")


if __name__ == "__main__":
    main()
