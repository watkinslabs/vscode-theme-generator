"""
VS Code Theme Generator

A comprehensive tool for generating VS Code themes with AI enhancement
"""

from .builder import ThemeBuilder
from .templater import Templater
from .ai_enhancer import AIEnhancer
from .packager import Packager
from .icon_generator import IconGenerator
from .constants import VERSION, THEME_SCHEMA_VERSION

__version__ = VERSION
__all__ = [
    "ThemeBuilder",
    "Templater",
    "AIEnhancer",
    "Packager",
    "IconGenerator",
    "VERSION",
    "THEME_SCHEMA_VERSION",
]