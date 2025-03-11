#!/usr/bin/env python3
"""Makes a standalone executable of the calibrate.py program, and copies it,
appropriately named for the OS, to the standalone_exec directory.
"""
import subprocess
import sys
import shutil
from pathlib import Path

subprocess.run("uv run pyinstaller -F calibrate.py", shell=True)

src_name, dest_name = {
    'win': ('calibrate.exe', 'calibrate-win.exe'),
    'dar': ('calibrate', 'calibrate-mac'),
    'lin': ('calibrate', 'calibrate-linux')
}[sys.platform[:3]]

src = Path("dist") / src_name
dest = Path("standalone-exec") / dest_name
dest_config = Path("standalone-exec") / "config.py"

shutil.copy(src, dest)
shutil.copy('config.py', dest_config)

