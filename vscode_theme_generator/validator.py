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
        logger.info("=== Starting theme validation ===")
        is_valid, errors = self.validate_with_errors(theme_def)
        
        if is_valid:
            logger.info("✓ Theme validation PASSED")
        else:
            logger.error(f"✗ Theme validation FAILED with {len(errors)} errors")
            for error in errors:
                logger.error(f"  - {error}")
        
        return is_valid
        
    def validate_with_errors(self, theme_def: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate theme and return errors"""
        self.errors = []
        
        logger.debug(f"Validating theme definition with keys: {list(theme_def.keys())}")
        
        # Check theme structure
        if 'theme' not in theme_def:
            logger.debug("No 'theme' key found, treating entire dict as theme data")
            theme_data = theme_def
        else:
            logger.debug("Found 'theme' key, extracting theme data")
            theme_data = theme_def['theme']
            
        logger.debug(f"Theme data keys: {list(theme_data.keys())}")
        
        # Validate required fields
        logger.info(">>> Validating required fields...")
        self._validate_required_fields(theme_data)
        
        # Validate colors
        if 'colors' in theme_data:
            logger.info(f">>> Validating colors ({len(theme_data['colors'])} colors)...")
            self._validate_colors(theme_data['colors'])
        else:
            logger.warning("No 'colors' section found in theme data")
            
        # Validate token colors
        if 'token_colors' in theme_data:
            logger.info(f">>> Validating token colors ({len(theme_data['token_colors'])} tokens)...")
            self._validate_token_colors(theme_data['token_colors'])
        else:
            logger.debug("No 'token_colors' section found (this is optional)")
            
        # Validate metadata
        logger.info(">>> Validating metadata...")
        self._validate_metadata(theme_data)
        
        logger.info(f"=== Validation complete: {len(self.errors)} errors found ===")
        
        return len(self.errors) == 0, self.errors
        
    def fix_theme(self, theme_def: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to fix common issues in theme definition"""
        logger.info("=== Attempting to fix theme issues ===")
        
        if 'theme' not in theme_def:
            logger.debug("Wrapping theme data in 'theme' key")
            theme_data = theme_def
            fixed_def = {'theme': theme_data}
        else:
            theme_data = theme_def['theme']
            fixed_def = theme_def.copy()
            
        # Fix missing required fields
        if 'name' not in theme_data:
            logger.info("Adding missing 'name' field")
            theme_data['name'] = 'unnamed_theme'
            
        if 'display_name' not in theme_data:
            logger.info("Adding missing 'display_name' field")
            theme_data['display_name'] = theme_data['name'].replace('_', ' ').title()
            
        if 'description' not in theme_data:
            logger.info("Adding missing 'description' field")
            theme_data['description'] = 'A custom VS Code theme'
            
        if 'version' not in theme_data:
            logger.info("Adding missing 'version' field")
            theme_data['version'] = '1.0.0'
            
        # Fix colors
        if 'colors' in theme_data:
            logger.info("Fixing color issues...")
            theme_data['colors'] = self._fix_colors(theme_data['colors'])
        else:
            logger.info("No colors found, adding minimal required colors")
            theme_data['colors'] = self._get_minimal_required_colors()
            
        # Fix token colors
        if 'token_colors' in theme_data:
            logger.info("Fixing token color issues...")
            theme_data['token_colors'] = self._fix_token_colors(theme_data['token_colors'])
            
        logger.info("=== Theme fixing complete ===")
        
        return fixed_def
        
    def _validate_required_fields(self, theme_data: Dict[str, Any]):
        """Validate required theme fields"""
        required_fields = ['name', 'colors']
        
        logger.debug(f"Checking for required fields: {required_fields}")
        
        for field in required_fields:
            if field not in theme_data:
                error = f"Missing required field: {field}"
                logger.error(f"  ✗ {error}")
                self.errors.append(error)
            else:
                logger.debug(f"  ✓ Found required field: {field}")
                
        # Validate name format
        if 'name' in theme_data:
            name = theme_data['name']
            logger.debug(f"Validating theme name: '{name}'")
            
            if not re.match(r'^[a-z0-9\-_]+$', name):
                error = f"Invalid theme name format: {name}. Use only lowercase letters, numbers, hyphens, and underscores."
                logger.error(f"  ✗ {error}")
                self.errors.append(error)
            else:
                logger.debug(f"  ✓ Theme name format is valid")
                
    def _validate_colors(self, colors: Dict[str, str]):
        """Validate color definitions"""
        logger.debug(f"Validating {len(colors)} color definitions")
        
        # Check for required colors
        missing_colors = []
        for key in REQUIRED_COLOR_KEYS:
            if key not in colors:
                missing_colors.append(key)
                logger.debug(f"  ✗ Missing required color: {key}")
            else:
                logger.debug(f"  ✓ Found required color: {key} = {colors[key]}")
                
        if missing_colors:
            error = f"Missing required colors: {', '.join(missing_colors)}"
            logger.error(error)
            self.errors.append(error)
            
        # Validate color format
        invalid_colors = []
        for key, value in colors.items():
            if not isinstance(value, str):
                error = f"Color value for '{key}' must be a string (got {type(value).__name__})"
                logger.error(f"  ✗ {error}")
                self.errors.append(error)
                continue
                
            if not validate_hex_color(value):
                error = f"Invalid color format for '{key}': {value}"
                logger.error(f"  ✗ {error}")
                self.errors.append(error)
                invalid_colors.append(key)
            else:
                logger.debug(f"  ✓ Valid color: {key} = {value}")
                
        if invalid_colors:
            logger.warning(f"Found {len(invalid_colors)} invalid color formats")
                
    def _validate_token_colors(self, token_colors: List[Dict[str, Any]]):
        """Validate token color definitions"""
        if not isinstance(token_colors, list):
            error = f"token_colors must be a list (got {type(token_colors).__name__})"
            logger.error(error)
            self.errors.append(error)
            return
            
        logger.debug(f"Validating {len(token_colors)} token color definitions")
        
        for idx, token in enumerate(token_colors):
            logger.debug(f"  Validating token {idx}...")
            
            if not isinstance(token, dict):
                error = f"Token color at index {idx} must be a dictionary"
                logger.error(f"    ✗ {error}")
                self.errors.append(error)
                continue
                
            # Check required fields
            if 'scope' not in token:
                error = f"Token color at index {idx} missing 'scope'"
                logger.error(f"    ✗ {error}")
                self.errors.append(error)
            else:
                scope = token['scope']
                if isinstance(scope, str):
                    logger.debug(f"    ✓ Scope (string): {scope}")
                elif isinstance(scope, list):
                    logger.debug(f"    ✓ Scope (list): {', '.join(scope)}")
                else:
                    logger.error(f"    ✗ Invalid scope type: {type(scope).__name__}")
                
            if 'settings' not in token:
                error = f"Token color at index {idx} missing 'settings'"
                logger.error(f"    ✗ {error}")
                self.errors.append(error)
            else:
                settings = token['settings']
                if not isinstance(settings, dict):
                    error = f"Token color settings at index {idx} must be a dictionary"
                    logger.error(f"    ✗ {error}")
                    self.errors.append(error)
                elif 'foreground' in settings:
                    fg = settings['foreground']
                    if not validate_hex_color(fg):
                        error = f"Invalid foreground color at index {idx}: {fg}"
                        logger.error(f"    ✗ {error}")
                        self.errors.append(error)
                    else:
                        logger.debug(f"    ✓ Valid foreground: {fg}")
                        
            if 'name' in token:
                logger.debug(f"    Token name: {token['name']}")
                        
    def _validate_metadata(self, theme_data: Dict[str, Any]):
        """Validate theme metadata"""
        # Validate version format
        if 'version' in theme_data:
            version = theme_data['version']
            logger.debug(f"Validating version: {version}")
            
            if not re.match(r'^\d+\.\d+\.\d+$', version):
                error = f"Invalid version format: {version}. Use semantic versioning (e.g., 1.0.0)"
                logger.error(f"  ✗ {error}")
                self.errors.append(error)
            else:
                logger.debug(f"  ✓ Valid version format")
                
        # Validate author
        if 'author' in theme_data:
            author = theme_data['author']
            logger.debug(f"Validating author: {type(author).__name__}")
            
            if isinstance(author, dict):
                if 'email' in author and author['email']:
                    email = author['email']
                    logger.debug(f"  Validating email: {email}")
                    
                    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                        error = f"Invalid email format: {email}"
                        logger.error(f"    ✗ {error}")
                        self.errors.append(error)
                    else:
                        logger.debug(f"    ✓ Valid email format")
                        
    def _fix_colors(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Fix color issues"""
        fixed_colors = {}
        fixes_made = []
        
        logger.debug(f"Attempting to fix {len(colors)} colors")
        
        for key, value in colors.items():
            if isinstance(value, str):
                # Try to fix color format
                if value.startswith('#'):
                    # Ensure proper hex format
                    hex_part = value[1:].upper()
                    if len(hex_part) == 3:
                        # Convert 3-char to 6-char hex
                        hex_part = ''.join([c*2 for c in hex_part])
                        fixed_colors[key] = f"#{hex_part}"
                        fixes_made.append(f"{key}: {value} → #{hex_part}")
                    elif len(hex_part) in [6, 8]:
                        fixed_colors[key] = f"#{hex_part}"
                        if value != f"#{hex_part}":
                            fixes_made.append(f"{key}: {value} → #{hex_part}")
                    else:
                        # Invalid length, skip
                        logger.warning(f"Cannot fix invalid color '{key}': {value} (invalid length: {len(hex_part)})")
                        continue
                else:
                    # Try to parse as hex without #
                    if re.match(r'^[0-9A-Fa-f]{6}$', value):
                        fixed_colors[key] = f"#{value.upper()}"
                        fixes_made.append(f"{key}: {value} → #{value.upper()}")
                    else:
                        logger.warning(f"Cannot fix invalid color '{key}': {value}")
            else:
                logger.warning(f"Skipping non-string color '{key}': {value} ({type(value).__name__})")
                
        # Add missing required colors with defaults
        for key in REQUIRED_COLOR_KEYS:
            if key not in fixed_colors:
                default_color = self._get_default_color_for_key(key)
                fixed_colors[key] = default_color
                fixes_made.append(f"{key}: (missing) → {default_color}")
                
        if fixes_made:
            logger.info(f"Fixed {len(fixes_made)} color issues:")
            for fix in fixes_made[:10]:  # Show first 10
                logger.info(f"  {fix}")
            if len(fixes_made) > 10:
                logger.info(f"  ... and {len(fixes_made) - 10} more")
                
        return fixed_colors
        
    def _fix_token_colors(self, token_colors: Any) -> List[Dict[str, Any]]:
        """Fix token color issues"""
        if not isinstance(token_colors, list):
            logger.warning(f"Token colors is not a list ({type(token_colors).__name__}), returning empty list")
            return []
            
        fixed_tokens = []
        fixes_made = 0
        
        for idx, token in enumerate(token_colors):
            if not isinstance(token, dict):
                logger.debug(f"Skipping non-dict token at index {idx}")
                continue
                
            fixed_token = {}
            
            # Ensure scope
            if 'scope' in token:
                scope = token['scope']
                if isinstance(scope, str):
                    fixed_token['scope'] = [scope]
                    logger.debug(f"Converted string scope to list at index {idx}")
                elif isinstance(scope, list):
                    fixed_token['scope'] = scope
                else:
                    logger.debug(f"Skipping token {idx} with invalid scope type")
                    continue
            else:
                logger.debug(f"Skipping token {idx} without scope")
                continue
                
            # Ensure settings
            if 'settings' in token and isinstance(token['settings'], dict):
                settings = {}
                
                # Fix foreground color
                if 'foreground' in token['settings']:
                    fg = token['settings']['foreground']
                    if isinstance(fg, str) and validate_hex_color(fg):
                        settings['foreground'] = fg
                    else:
                        logger.debug(f"Skipping invalid foreground color at index {idx}: {fg}")
                        
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
                fixes_made += 1
                
        logger.info(f"Fixed token colors: {len(token_colors)} → {len(fixed_tokens)} valid tokens")
        
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