"""
Theme validator for ensuring valid theme configurations
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional

from .constants import REQUIRED_COLOR_KEYS, HEX_COLOR_PATTERN
from .color_utils import validate_hex_color

logger = logging.getLogger(__name__)

class ThemeValidator:
    """Validates theme configurations"""
    
    def __init__(self):
        self.errors = []
        
    def validate(self, theme_def: Dict[str, Any]) -> bool:
        """Validate theme definition"""
        is_valid, _ = self.validate_with_errors(theme_def)
        return is_valid
        
    def validate_with_errors(self, theme_def: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate theme and return errors"""
        self.errors = []
        
        # Check theme structure
        if 'theme' not in theme_def:
            theme_data = theme_def
        else:
            theme_data = theme_def['theme']
            
        # Validate required fields
        self._validate_required_fields(theme_data)
        
        # Validate colors
        if 'colors' in theme_data:
            self._validate_colors(theme_data['colors'])
            
        # Validate token colors
        if 'token_colors' in theme_data:
            self._validate_token_colors(theme_data['token_colors'])
            
        # Validate metadata
        self._validate_metadata(theme_data)
        
        return len(self.errors) == 0, self.errors
        
    def fix_theme(self, theme_def: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to fix common issues in theme definition"""
        if 'theme' not in theme_def:
            theme_data = theme_def
            fixed_def = {'theme': theme_data}
        else:
            theme_data = theme_def['theme']
            fixed_def = theme_def.copy()
            
        # Fix missing required fields
        if 'name' not in theme_data:
            theme_data['name'] = 'unnamed_theme'
            
        if 'display_name' not in theme_data:
            theme_data['display_name'] = theme_data['name'].replace('_', ' ').title()
            
        if 'description' not in theme_data:
            theme_data['description'] = 'A custom VS Code theme'
            
        if 'version' not in theme_data:
            theme_data['version'] = '1.0.0'
            
        # Fix colors
        if 'colors' in theme_data:
            theme_data['colors'] = self._fix_colors(theme_data['colors'])
        else:
            theme_data['colors'] = self._get_minimal_required_colors()
            
        # Fix token colors
        if 'token_colors' in theme_data:
            theme_data['token_colors'] = self._fix_token_colors(theme_data['token_colors'])
            
        return fixed_def
        
    def _validate_required_fields(self, theme_data: Dict[str, Any]):
        """Validate required theme fields"""
        required_fields = ['name', 'colors']
        
        for field in required_fields:
            if field not in theme_data:
                self.errors.append(f"Missing required field: {field}")
                
        # Validate name format
        if 'name' in theme_data:
            name = theme_data['name']
            if not re.match(r'^[a-z0-9\-_]+$', name):
                self.errors.append(f"Invalid theme name format: {name}. Use only lowercase letters, numbers, hyphens, and underscores.")
                
    def _validate_colors(self, colors: Dict[str, str]):
        """Validate color definitions"""
        # Check for required colors
        missing_colors = []
        for key in REQUIRED_COLOR_KEYS:
            if key not in colors:
                missing_colors.append(key)
                
        if missing_colors:
            self.errors.append(f"Missing required colors: {', '.join(missing_colors)}")
            
        # Validate color format
        for key, value in colors.items():
            if not isinstance(value, str):
                self.errors.append(f"Color value for '{key}' must be a string")
                continue
                
            if not validate_hex_color(value):
                self.errors.append(f"Invalid color format for '{key}': {value}")
                
    def _validate_token_colors(self, token_colors: List[Dict[str, Any]]):
        """Validate token color definitions"""
        if not isinstance(token_colors, list):
            self.errors.append("token_colors must be a list")
            return
            
        for idx, token in enumerate(token_colors):
            if not isinstance(token, dict):
                self.errors.append(f"Token color at index {idx} must be a dictionary")
                continue
                
            # Check required fields
            if 'scope' not in token:
                self.errors.append(f"Token color at index {idx} missing 'scope'")
                
            if 'settings' not in token:
                self.errors.append(f"Token color at index {idx} missing 'settings'")
            else:
                settings = token['settings']
                if not isinstance(settings, dict):
                    self.errors.append(f"Token color settings at index {idx} must be a dictionary")
                elif 'foreground' in settings:
                    if not validate_hex_color(settings['foreground']):
                        self.errors.append(f"Invalid foreground color at index {idx}: {settings['foreground']}")
                        
    def _validate_metadata(self, theme_data: Dict[str, Any]):
        """Validate theme metadata"""
        # Validate version format
        if 'version' in theme_data:
            version = theme_data['version']
            if not re.match(r'^\d+\.\d+\.\d+$', version):
                self.errors.append(f"Invalid version format: {version}. Use semantic versioning (e.g., 1.0.0)")
                
        # Validate author
        if 'author' in theme_data:
            author = theme_data['author']
            if isinstance(author, dict):
                if 'email' in author and author['email']:
                    email = author['email']
                    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                        self.errors.append(f"Invalid email format: {email}")
                        
    def _fix_colors(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Fix color issues"""
        fixed_colors = {}
        
        for key, value in colors.items():
            if isinstance(value, str):
                # Try to fix color format
                if value.startswith('#'):
                    # Ensure proper hex format
                    hex_part = value[1:].upper()
                    if len(hex_part) == 3:
                        # Convert 3-char to 6-char hex
                        hex_part = ''.join([c*2 for c in hex_part])
                    elif len(hex_part) not in [6, 8]:
                        # Invalid length, skip
                        logger.warning(f"Cannot fix invalid color '{key}': {value}")
                        continue
                        
                    fixed_colors[key] = f"#{hex_part}"
                else:
                    # Try to parse as hex without #
                    if re.match(r'^[0-9A-Fa-f]{6}$', value):
                        fixed_colors[key] = f"#{value.upper()}"
                    else:
                        logger.warning(f"Cannot fix invalid color '{key}': {value}")
            else:
                logger.warning(f"Skipping non-string color '{key}': {value}")
                
        # Add missing required colors with defaults
        for key in REQUIRED_COLOR_KEYS:
            if key not in fixed_colors:
                fixed_colors[key] = self._get_default_color_for_key(key)
                
        return fixed_colors
        
    def _fix_token_colors(self, token_colors: Any) -> List[Dict[str, Any]]:
        """Fix token color issues"""
        if not isinstance(token_colors, list):
            return []
            
        fixed_tokens = []
        
        for token in token_colors:
            if not isinstance(token, dict):
                continue
                
            fixed_token = {}
            
            # Ensure scope
            if 'scope' in token:
                scope = token['scope']
                if isinstance(scope, str):
                    fixed_token['scope'] = [scope]
                elif isinstance(scope, list):
                    fixed_token['scope'] = scope
                else:
                    continue
            else:
                continue
                
            # Ensure settings
            if 'settings' in token and isinstance(token['settings'], dict):
                settings = {}
                
                # Fix foreground color
                if 'foreground' in token['settings']:
                    fg = token['settings']['foreground']
                    if isinstance(fg, str) and validate_hex_color(fg):
                        settings['foreground'] = fg
                        
                # Copy other settings
                for key in ['fontStyle', 'background']:
                    if key in token['settings']:
                        settings[key] = token['settings'][key]
                        
                if settings:
                    fixed_token['settings'] = settings
                    
            # Copy name if present
            if 'name' in token:
                fixed_token['name'] = token['name']
                
            if 'scope' in fixed_token and 'settings' in fixed_token:
                fixed_tokens.append(fixed_token)
                
        return fixed_tokens
        
    def _get_minimal_required_colors(self) -> Dict[str, str]:
        """Get minimal set of required colors"""
        return {
            "editor.background": "#1e1e1e",
            "editor.foreground": "#d4d4d4",
            "activityBar.background": "#333333",
            "activityBar.foreground": "#ffffff",
            "sideBar.background": "#252526",
            "sideBar.foreground": "#cccccc",
            "statusBar.background": "#007acc",
            "statusBar.foreground": "#ffffff"
        }
        
    def _get_default_color_for_key(self, key: str) -> str:
        """Get default color for a specific key"""
        defaults = self._get_minimal_required_colors()
        
        if key in defaults:
            return defaults[key]
            
        # Generate based on key type
        if 'background' in key:
            return "#1e1e1e"
        elif 'foreground' in key:
            return "#d4d4d4"
        else:
            return "#808080"