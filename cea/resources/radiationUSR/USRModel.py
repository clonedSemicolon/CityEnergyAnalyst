import os
import sys
import shlex
import subprocess
from typing import Optional, Tuple

__author__ = "Xiaoyu Wang"
__copyright__ = ["Copyright 2025, Architecture and Building Systems - ETH Zurich"], \
                ["Copyright 2025, College of Architecture and Urban Planning (CAUP) - Tongji University"]
__credits__ = ["Xiaoyu Wang"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = [""]
__email__ = ["cea@arch.ethz.ch", "wanglittlerain@163.com"]
__status__ = "Production"


# Define the list of required USR executables (without extension)
REQUIRED_USR_BINARIES = [
    "radiation",
]

REQUIRED_LIBS = []  # Add necessary library files if required


class USR:
    """
    A class to execute the USR model workflow. It can run one or more of the following stages:
      1. mesh-generation.exe (or Linux equivalent) to generate mesh files.
      2. radiation.exe (or Linux equivalent) to compute radiation values.
      3. write-radiation-results.exe (or Linux equivalent) to output the radiation results.

    The outputs are handled internally by the executables.
    """

    def __init__(self, usr_exe_dir: str, usr_lib_dir: Optional[str] = None):
        """
        Initialize the USRModel.
        :param usr_exe_dir: Directory where the USR executables are located.
        :param usr_lib_dir: Optional directory for USR libraries (if needed by the executables).
        """
        self.usr_exe_dir = usr_exe_dir
        self.usr_lib_dir = usr_lib_dir
        self.is_windows = sys.platform == "win32"

    @staticmethod
    def run_cmd(cmd: str, exe_dir: str, lib_dir: Optional[str] = None) -> str:
        """
        Run a command using subprocess with the given executable directory and environment settings.

        :param cmd: Command string to execute.
        :param exe_dir: Directory where the executable is located.
        :param lib_dir: Optional directory for libraries.
        :return: The standard output of the command.
        """
        print(f"Running command: {cmd}")
        # Set up environment variables
        env = os.environ.copy()
        if lib_dir:
            env["USR_LIB"] = lib_dir

        # Split the command into arguments
        parts = shlex.split(cmd)
        # On Windows, prepend the executable directory to the executable name
        if sys.platform == "win32":
            parts[0] = os.path.join(exe_dir, parts[0])
        process = subprocess.run(parts, capture_output=True, env=env, cwd=exe_dir)
        output = process.stdout.decode("utf-8")
        print(output)

        if process.returncode != 0:
            error_output = process.stderr.decode("utf-8")
            print(error_output)
            raise subprocess.CalledProcessError(process.returncode, cmd)
        return output

    def run_mesh_generation(self, json_file: str):
        """
        Execute the mesh-generation executable with a JSON input file.

        :param json_file: The full path to the JSON file to be used as input.
        """
        exe_name = "mesh-generation.exe" if self.is_windows else "mesh-generation"
        # Command includes the json file argument
        cmd = f'"{exe_name}" "{json_file}"'
        return self.run_cmd(cmd, self.usr_exe_dir, self.usr_lib_dir)

    def run_radiation(self, json_file: str):
        """
        Execute the radiation executable with a JSON input file.

        :param json_file: The full path to the JSON file to be used as input.
        """
        exe_name = "radiation.exe" if self.is_windows else "radiation"
        # Command includes the json file argument
        cmd = f'"{exe_name}" "{json_file}"'
        return self.run_cmd(cmd, self.usr_exe_dir, self.usr_lib_dir)


def check_usr_exe_directory(path_hint: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Check the directory for required USR executables and return the path to the binaries (and optionally the libraries).
    If the required executables are not found, a ValueError is raised.
    """
    print("Platform:", sys.platform)

    def contains_binaries(path: str) -> bool:
        """Check if the required binaries exist in the given path."""
        try:
            files = set(os.listdir(path))
        except OSError:
            return False

        for binary in REQUIRED_USR_BINARIES:
            expected = binary + (".exe" if sys.platform == "win32" else "")
            if expected not in files:
                print(f"Expected binary '{expected}' not found in {path}. Found: {files}")
                return False
        return True

    def contains_libs(path: str) -> bool:
        """Check if the required library files exist in the given path."""
        try:
            libs = set(os.listdir(path))
        except OSError:
            return False
        return all(lib in libs for lib in REQUIRED_LIBS)

    # List of directories to check
    folders_to_check = []
    if path_hint:
        folders_to_check.append(path_hint)

    # Add predefined binary directories
    base_path = os.path.join(os.path.dirname(__file__), "bin")
    win32_path = os.path.join(base_path, "win32")
    linux_path = os.path.join(base_path, "linux")

    folders_to_check.extend([win32_path, linux_path])

    # Normalize paths
    folders_to_check = [os.path.abspath(os.path.normpath(p)) for p in folders_to_check]
    lib_path = None

    print("Folders to check:", folders_to_check)
    for possible_path in folders_to_check:
        if not os.path.isdir(possible_path):
            print(f"{possible_path} is not a directory.")
            continue

        if contains_binaries(possible_path):
            if sys.platform == "win32":
                _lib_path = os.path.abspath(os.path.normpath(os.path.join(possible_path, "..", "lib")))
                if contains_libs(_lib_path):
                    lib_path = _lib_path
                elif contains_libs(possible_path):
                    lib_path = possible_path
            print(f"Found USR executables in: {possible_path}")
            return possible_path, lib_path
        else:
            # Check 'bin' subdirectory if the main directory doesn't contain the binaries
            sub_bin = os.path.join(possible_path, "bin")
            if os.path.isdir(sub_bin) and contains_binaries(sub_bin):
                if sys.platform == "win32":
                    _lib_path = os.path.abspath(os.path.normpath(os.path.join(sub_bin, "..", "lib")))
                    if contains_libs(_lib_path):
                        lib_path = _lib_path
                    elif contains_libs(sub_bin):
                        lib_path = sub_bin
                print(f"Found USR executables in subfolder: {sub_bin}")
                return sub_bin, lib_path

    raise ValueError("Could not find USR executables - checked these paths: {}".format(", ".join(folders_to_check)))







