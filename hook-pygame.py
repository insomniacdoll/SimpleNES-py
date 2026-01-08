"""
PyInstaller hook for pygame
This ensures pygame and its dependencies are properly included in the executable
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

# Collect all pygame submodules
hiddenimports = collect_submodules('pygame')

# Collect pygame data files
datas = collect_data_files('pygame')

# Collect pygame dynamic libraries
binaries = collect_dynamic_libs('pygame')