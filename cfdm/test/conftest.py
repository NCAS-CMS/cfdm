import subprocess
import sys
from pathlib import Path


def run_script(script_name):
    """Helper to run a python script in the same directory."""
    script_path = Path(__file__).parent / script_name
    if script_path.exists():
        print(f"\nRunning setup script: {script_name}...")
        subprocess.run([sys.executable, str(script_path)], check=False)
    else:
        print(f"\nWarning: Setup script {script_name} not found.")


def pytest_configure(config):
    """Runs ONCE before any tests are collected or executed."""
    # config.args contains the positional arguments passed to pytest
    # (e.g., ['cfdm/test/test_List.py'] or ['cfdm/test/'])

    # If config.args is empty, or if it ONLY contains the default test
    # directory, we assume the user wants the "full" run.
    is_specific_file_run = False

    for arg in config.args:
        # If any argument points directly to a specific Python test file,
        # we skip the heavy setup scripts.
        if arg.endswith(".py") and "test_" in arg:
            is_specific_file_run = True
            break

    if not is_specific_file_run:
        print("\n>>> Full test run detected. Running setup scripts...")
        run_script("create_test_files.py")
        run_script("setup_create_field.py")
    else:
        print(
            "\n>>> Specific test file targeted. Skipping heavy setup scripts."
        )
