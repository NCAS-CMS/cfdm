"""Check the class-coverage and method-coverage of the API reference.

All classes are extracted and checked for an entry in docs/source/class.rst

All non-private methods of all such classes are checked for having an
entry in their corresponding class's file in docs/source/class/

For example, all cfdm.Field methods that do not start with an
underscore are checked for having an entry in
docs/source/class/cfdm.Field.rst

If being used on the cfdm library, the classes listed in
docs/source/class_core.rst are also checked.

Call as:

   $ python check_api_coverage.py <docs/source/ directory path>

"""

import inspect
import os
import re
import sys

import cfdm as package

if len(sys.argv) == 2:
    source = sys.argv[1]
else:
    raise ValueError(
        "Must provide the 'source' directory as the "
        "only positional argument"
    )


if not source.endswith("source"):
    raise ValueError(f"Given directory {source} does not end with 'source'")

n_undocumented_classes = 0
n_undocumented_methods = 0
n_missing_files = 0

duplicate_method_entries = []

for core in ("", "_core"):
    if core:
        if package.__name__ != "cfdm":
            # Only check core methods on cfdm package
            continue

        package = getattr(package, "core")

    with open(os.path.join(source, "class" + core + ".rst")) as f:
        api_contents = f.read()

    class_names = [
        name
        for name, klass in inspect.getmembers(package, inspect.isclass)
        if klass.__module__.startswith(package.__name__ + ".")
        and not klass.__module__.startswith(package.__name__ + ".functions")
        # This just counts top-level read-write i.e. cfdm.read and .write
        and not klass.__module__.startswith(package.__name__ + ".read_write")
        and name != "netcdf_indexer"  # lone function
    ]

    for class_name in class_names:
        full_class_name = f"{package.__name__}.{class_name}"

        if full_class_name not in api_contents:
            print(
                f"Class {full_class_name} not in docs/source/class{core}.rst"
            )
            n_missing_files += 1
            n_undocumented_classes += 1
            continue

        klass = getattr(package, class_name)
        methods = [
            method for method in dir(klass) if not method.startswith("_")
        ]

        class_name = ".".join([package.__name__, class_name])

        rst_file = os.path.join(source, "class", full_class_name + ".rst")

        try:
            with open(rst_file) as f:
                rst_contents = f.read()

            for method in methods:
                method = ".".join([class_name, method])
                count = rst_contents.count(method)
                if count == 0:
                    n_undocumented_methods += 1
                    print(
                        f"Method {method} not in "
                        f"{os.path.join(source, 'class', rst_file)}"
                    )
                elif count > 1:
                    # The method appears more than once, but may be a
                    # sub-string of another method name, e.g. this gets caught:
                    #     [cfdm.List.]nc_set_variable
                    # due to the presence of this method:
                    #     [cfdm.List.]nc_set_variable_groups
                    # so we must account for that. Checking next character
                    # of duplicate(s) is something other than a newline or
                    # whitespace, seems robust and simplest.
                    end_loc = [
                        m.end(0) for m in re.finditer(method, rst_contents)
                    ]
                    chars = [rst_contents[c] for c in [e for e in end_loc]]

                    # Any character that isn't a newline or whitespace
                    # indicates another method which the method is a substring
                    # of and can be excluded. If there are still duplicates,
                    # we have genuine duplicate listing entries to report.
                    if chars.count("\n") + chars.count(" ") > 1:
                        duplicate_method_entries.append(method)
        except FileNotFoundError:
            n_missing_files += 1
            print(f"File {rst_file} does not exist  for existing class")

# Raise an exception to ensure a non-zero shell return code
if n_undocumented_methods:
    print("Found undocumented method(s)")

if n_missing_files:
    print("Found missing .rst file(s)")

if n_undocumented_methods or n_missing_files:
    raise ValueError(
        f"Found {n_undocumented_classes} undocumented classes, "
        f"{n_undocumented_methods} undocumented methods and "
        f"{n_missing_files} missing .rst files"
    )

if duplicate_method_entries:
    duplicate_method_entries.sort()
    entries = "\n".join(duplicate_method_entries)  # can't set \n in f-string!
    print(
        "WARNING: some methods are listed multiple times inside one class "
        "file/page. Decide if the duplicates are intended and if not remove "
        f"them. They are:\n{entries}\n"
    )

print("All non-private methods are documented")
