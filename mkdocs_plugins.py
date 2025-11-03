"""
MkDocs custom plugins registration.
This file allows us to register custom plugins without packaging.
"""
import sys
from pathlib import Path

# Add tools directory to path so we can import our plugin
tools_dir = Path(__file__).parent / "tools"
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

from escape_macros_plugin import EscapeMacrosInCodePlugin

__all__ = ['EscapeMacrosInCodePlugin']

