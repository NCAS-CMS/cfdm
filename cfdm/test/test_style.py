import datetime
import os
import pycodestyle
import unittest

import cfdm


class styleTest(unittest.TestCase):
    """Test PEP8 compliance on all Python '.py' files in the 'cf' directory."""
    def setUp(self):
        self.cfdm_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(self.cfdm_dir)

    def test_pep8_compliance(self):
        pep8_check = pycodestyle.StyleGuide()

        # Directories to skip in the recursive walk of the directory:
        skip_dirs = (
            '__pycache__',
        )
        # These are pycodestyle errors and warnings to explicitly ignore. For
        # descriptions for each code see:
        # https://pep8.readthedocs.io/en/latest/intro.html#error-codes
        pep8_check.options.ignore += (  # ignored because...
            'W605',  # ...false positives on regex and LaTeX expressions
            'E272',  # ...>1 spaces to align keywords in long import listings
            'E402',  # ...justified lower module imports in {.., core}/__init__
            'E501',  # ...docstring examples include output lines >79 chars
            'E722',  # ...lots of "bare except" cases need to be addressed
        )

        # Find all Python source code ('.py') files in the 'cf' directory,
        # including all unskipped sub-directories within e.g. test directory:
        python_files = []
        for root_dir, dirs, filelist in os.walk('..'):  # '..' to test/ == cfdm/
            if os.path.basename(root_dir) in skip_dirs:
                continue
            python_files += [
                os.path.join(root_dir, fname) for fname in filelist
                if fname.endswith('.py')
            ]

        pep8_issues = pep8_check.check_files(python_files).total_errors
        self.assertEqual(
            pep8_issues, 0,
            'Detected {!s} PEP8 errors or warnings:'.format(pep8_issues)
        )


# --- End: class


if __name__ == "__main__":
    print('Run date:', datetime.datetime.now())
    cfdm.environment(display=False)
    print('')
    unittest.main(verbosity=2)
