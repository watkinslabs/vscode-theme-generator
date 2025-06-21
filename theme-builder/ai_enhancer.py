"""
AI Enhancement module for theme optimization
"""

import json
import logging
from typing import Dict, Any, List, Tuple
from wl_ai_manager import AIManager

from .constants import AI_PROMPTS
from .color_utils import (
    validate_hex_color,
    calculate_contrast_ratio,
    adjust_brightness,
    get_complementary_color,
    get_brightness,
    blend_colors,
    saturate_color
)

logger = logging.getLogger(__name__)

class AIEnhancer:
    """Enhances themes using AI for better colors and descriptions"""
    
    def __init__(self, config):
        self.config = config
        self.theme_ai_config = config.get('ai', {})
        
        # Initialize AI Manager if enabled
        if self.theme_ai_config.get('enabled', True):
            # Get the ai_manager configuration section
            ai_manager_config = config.get('ai_manager', {})
            if ai_manager_config:
                try:
                    self.ai_manager = AIManager(ai_manager_config)
                except Exception as e:
                    logger.error(f"Failed to initialize AI Manager: {e}")
                    self.ai_manager = None
            else:
                logger.warning("No ai_manager configuration found in config")
                self.ai_manager = None
        else:
            self.ai_manager = None
            
    def enhance_theme(self, theme_def: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a theme definition with AI"""
        if not self.ai_manager:
            logger.info("AI enhancement disabled")
            return theme_def
            
        theme_data = theme_def.get('theme', theme_def)
        ai_settings = theme_data.get('ai_enhance', {})
        
        # Enhance description
        if ai_settings.get('enhance_description', True):
            theme_data['description'] = self._enhance_description(
                theme_data.get('name', ''),
                theme_data.get('description', '')
            )
            
        # Optimize colors
        if ai_settings.get('optimize_colors', True):
            theme_data['colors'] = self._optimize_colors(theme_data.get('colors', {}))
            
        # Generate missing token colors
        if ai_settings.get('generate_token_colors', True) and not theme_data.get('token_colors'):
            theme_data['token_colors'] = self._generate_token_colors(theme_data.get('colors', {}))
            
        # Check contrast ratios
        if ai_settings.get('contrast_check', True):
            theme_data['colors'] = self._check_and_fix_contrast(theme_data.get('colors', {}))
            
        # Generate color variants
        if ai_settings.get('generate_variants', False):
            variants = self._generate_color_variants(theme_data)
            # Store variants in theme metadata
            theme_data['variants'] = variants
            
        return {'theme': theme_data}
    
    def _enhance_description(self, theme_name: str, current_description: str) -> str:
        """Use AI to enhance theme description"""
        try:
            # Create prompt file if needed
            prompts_dir = Path(self.config.get('ai_manager.prompt_folder', './prompts'))
            prompts_dir.mkdir(exist_ok=True)
            
            # Use naming convention: enhance_theme_description.user.txt
            prompt_file = prompts_dir / 'enhance_theme_description.user.txt'
            if not prompt_file.exists():
                prompt_content = """Enhance this VS Code theme description to be more engaging and descriptive.
Keep it concise but compelling, under 200 characters.

Theme: {{ theme_name }}
Current description: {{ description }}

Provide an enhanced description that:
- Highlights the unique visual characteristics
- Mentions the target audience or use case
- Uses vivid but professional language
- Stays under 200 characters"""
                prompt_file.write_text(prompt_content)
            
            # Data for templating
            prompt_data = {
                'theme_name': theme_name,
                'description': current_description
            }
            
            # Call with 'enhance_theme_description'
            response = self.ai_manager.chat('enhance_theme_description', prompt_data)
            enhanced_description = response.strip() if response else current_description
            
            # Ensure it's not too long
            if len(enhanced_description) > 200:
                enhanced_description = enhanced_description[:197] + "..."
                
            logger.info(f"Enhanced description: {enhanced_description}")
            return enhanced_description
            
        except Exception as e:
            logger.error(f"Failed to enhance description: {e}")
            return current_description
    
    def _optimize_colors(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Use AI to optimize theme colors"""
        try:
            # Format colors for AI
            colors_json = json.dumps(colors, indent=2)
            
            prompt = self.theme_ai_config.get('prompts', {}).get(
                'optimize_colors',
                AI_PROMPTS['optimize_colors']
            ).format(colors=colors_json)
            
            response = self.ai_manager.chat(prompt)
            
            # Parse AI suggestions
            optimized_colors = self._parse_color_suggestions(response, colors)
            
            logger.info(f"Optimized {len(optimized_colors)} colors")
            return optimized_colors
            
        except Exception as e:
            logger.error(f"Failed to optimize colors: {e}")
            return colors
    
    def _generate_token_colors(self, base_colors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate token colors based on theme colors"""
        try:
            # Get key colors for generation
            key_colors = {
                'background': base_colors.get('editor.background', '#1e1e1e'),
                'foreground': base_colors.get('editor.foreground', '#d4d4d4'),
                'accent': base_colors.get('activityBar.background', '#007acc'),
            }
            
            prompt = self.theme_ai_config.get('prompts', {}).get(
                'generate_token_colors',
                AI_PROMPTS['generate_token_colors']
            ).format(
                base_colors=json.dumps(key_colors, indent=2)
            )
            
            response = self.ai_manager.chat(prompt)
            token_colors = self._parse_token_colors(response)
            
            logger.info(f"Generated {len(token_colors)} token colors")
            return token_colors
            
        except Exception as e:
            logger.error(f"Failed to generate token colors: {e}")
            return self._get_fallback_token_colors(base_colors)
    
    def _check_and_fix_contrast(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Check and fix contrast ratios for accessibility"""
        fixed_colors = colors.copy()
        
        # Key color pairs to check
        contrast_pairs = [
            ('editor.background', 'editor.foreground', 7.0),  # WCAG AAA
            ('activityBar.background', 'activityBar.foreground', 4.5),  # WCAG AA
            ('sideBar.background', 'sideBar.foreground', 4.5),
            ('statusBar.background', 'statusBar.foreground', 4.5),
            ('terminal.background', 'terminal.foreground', 7.0),
            ('button.background', 'button.foreground', 4.5),
            ('input.background', 'input.foreground', 4.5),
            ('dropdown.background', 'dropdown.foreground', 4.5),
            ('list.activeSelectionBackground', 'list.activeSelectionForeground', 4.5),
        ]
        
        for bg_key, fg_key, min_ratio in contrast_pairs:
            if bg_key in colors and fg_key in colors:
                bg_color = colors[bg_key]
                fg_color = colors[fg_key]
                
                # Validate colors
                if not validate_hex_color(bg_color) or not validate_hex_color(fg_color):
                    continue
                
                ratio = calculate_contrast_ratio(bg_color, fg_color)
                
                if ratio < min_ratio:
                    logger.warning(f"Low contrast ratio {ratio:.2f} for {bg_key}/{fg_key}")
                    
                    # Try to fix by adjusting foreground brightness
                    fixed_fg = self._adjust_for_contrast(bg_color, fg_color, min_ratio)
                    if fixed_fg and fixed_fg != fg_color:
                        fixed_colors[fg_key] = fixed_fg
                        logger.info(f"Fixed contrast for {fg_key}: {fg_color} -> {fixed_fg}")
                        
        return fixed_colors
    
    def _adjust_for_contrast(self, bg_color: str, fg_color: str, target_ratio: float) -> str:
        """Adjust foreground color to meet contrast ratio"""
        # Try brightening and darkening
        for adjustment in range(10, 100, 10):
            # Try brighter
            brighter = adjust_brightness(fg_color, adjustment)
            if calculate_contrast_ratio(bg_color, brighter) >= target_ratio:
                return brighter
                
            # Try darker
            darker = adjust_brightness(fg_color, -adjustment)
            if calculate_contrast_ratio(bg_color, darker) >= target_ratio:
                return darker
                
        # If we can't fix it, return original
        return fg_color
    
    def _generate_color_variants(self, theme_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Generate color variants (light/dark/high-contrast)"""
        base_colors = theme_data.get('colors', {})
        variants = {}
        
        # Generate light variant if theme is dark
        if self._is_dark_theme(base_colors):
            variants['light'] = self._generate_light_variant(base_colors)
            
        # Generate high contrast variant
        variants['high-contrast'] = self._generate_high_contrast_variant(base_colors)
        
        return variants
    
    def _is_dark_theme(self, colors: Dict[str, str]) -> bool:
        """Check if theme is dark based on background color"""
        bg_color = colors.get('editor.background', '#ffffff')
        # Simple check: dark if background brightness < 50%
        return get_brightness(bg_color) < 0.5
    
    def _generate_light_variant(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Generate light variant from dark theme"""
        light_colors = {}
        
        for key, color in colors.items():
            if not validate_hex_color(color):
                light_colors[key] = color
                continue
                
            brightness = get_brightness(color)
            
            if 'background' in key:
                # Light backgrounds
                if brightness < 0.2:
                    light_colors[key] = '#ffffff'
                elif brightness < 0.5:
                    light_colors[key] = adjust_brightness(color, 80)
                else:
                    light_colors[key] = adjust_brightness(color, 40)
                    
            elif 'foreground' in key:
                # Dark foregrounds
                if brightness > 0.8:
                    light_colors[key] = '#000000'
                elif brightness > 0.5:
                    light_colors[key] = adjust_brightness(color, -80)
                else:
                    light_colors[key] = adjust_brightness(color, -40)
                    
            else:
                # Adjust other colors based on brightness
                if brightness < 0.5:
                    light_colors[key] = adjust_brightness(color, 40)
                else:
                    light_colors[key] = adjust_brightness(color, -40)
                    
        return light_colors
    
    def _generate_high_contrast_variant(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Generate high contrast variant"""
        hc_colors = colors.copy()
        
        # Maximize contrast for key pairs
        if 'editor.background' in colors:
            bg = colors['editor.background']
            # Make background pure black or white
            if get_brightness(bg) < 0.5:
                hc_colors['editor.background'] = '#000000'
                hc_colors['editor.foreground'] = '#ffffff'
                hc_colors['sideBar.background'] = '#000000'
                hc_colors['activityBar.background'] = '#000000'
                hc_colors['statusBar.background'] = '#000000'
                hc_colors['terminal.background'] = '#000000'
            else:
                hc_colors['editor.background'] = '#ffffff'
                hc_colors['editor.foreground'] = '#000000'
                hc_colors['sideBar.background'] = '#ffffff'
                hc_colors['activityBar.background'] = '#ffffff'
                hc_colors['statusBar.background'] = '#ffffff'
                hc_colors['terminal.background'] = '#ffffff'
                
        # Increase saturation for accent colors
        accent_keys = ['activityBarBadge.background', 'button.background', 
                       'progressBar.background', 'selection.background']
        for key in accent_keys:
            if key in hc_colors:
                hc_colors[key] = saturate_color(hc_colors[key], 0.5)
                
        return hc_colors
    
    def _parse_color_suggestions(self, ai_response: str, original_colors: Dict[str, str]) -> Dict[str, str]:
        """Parse AI color suggestions from response"""
        optimized = original_colors.copy()
        
        # Look for hex color patterns in response
        import re
        lines = ai_response.split('\n')
        
        for line in lines:
            # Look for patterns like "editor.background: #123456"
            match = re.search(r'([a-zA-Z.]+):\s*(#[0-9A-Fa-f]{6,8})', line)
            if match:
                key = match.group(1)
                color = match.group(2)
                
                if key in original_colors and validate_hex_color(color):
                    optimized[key] = color
                    logger.debug(f"AI suggested {key}: {color}")
                    
        return optimized
    
    def _parse_token_colors(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse token colors from AI response"""
        token_colors = []
        
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\[[\s\S]*\]', ai_response)
        
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, list):
                    # Validate structure
                    for item in parsed:
                        if isinstance(item, dict) and 'scope' in item and 'settings' in item:
                            token_colors.append(item)
                    return token_colors
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from AI response")
                
        # Fallback to manual parsing
        # Look for token color patterns
        current_token = None
        for line in ai_response.split('\n'):
            # Look for name
            name_match = re.search(r'name:\s*"([^"]+)"', line)
            if name_match:
                if current_token:
                    token_colors.append(current_token)
                current_token = {'name': name_match.group(1)}
                
            # Look for scope
            scope_match = re.search(r'scope:\s*\[([^\]]+)\]', line)
            if scope_match and current_token:
                scopes = [s.strip().strip('"') for s in scope_match.group(1).split(',')]
                current_token['scope'] = scopes
                
            # Look for foreground color
            fg_match = re.search(r'foreground:\s*(#[0-9A-Fa-f]{6})', line)
            if fg_match and current_token:
                if 'settings' not in current_token:
                    current_token['settings'] = {}
                current_token['settings']['foreground'] = fg_match.group(1)
                
        # Add last token
        if current_token and 'scope' in current_token and 'settings' in current_token:
            token_colors.append(current_token)
            
        # If parsing failed, return fallback
        if not token_colors:
            return self._get_fallback_token_colors({})
            
        return token_colors
    
    def _get_fallback_token_colors(self, base_colors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get fallback token colors if AI generation fails"""
        bg = base_colors.get('editor.background', '#1e1e1e')
        fg = base_colors.get('editor.foreground', '#d4d4d4')
        
        # Generate colors based on background
        is_dark = get_brightness(bg) < 0.5
        
        if is_dark:
            return [
                {
                    "name": "Comment",
                    "scope": ["comment", "punctuation.definition.comment"],
                    "settings": {"foreground": "#6A9955", "fontStyle": "italic"}
                },
                {
                    "name": "String",
                    "scope": ["string", "string.quoted"],
                    "settings": {"foreground": "#ce9178"}
                },
                {
                    "name": "Number",
                    "scope": ["constant.numeric"],
                    "settings": {"foreground": "#b5cea8"}
                },
                {
                    "name": "Keyword",
                    "scope": ["keyword", "keyword.control"],
                    "settings": {"foreground": "#569cd6"}
                },
                {
                    "name": "Storage",
                    "scope": ["storage", "storage.type", "storage.modifier"],
                    "settings": {"foreground": "#569cd6"}
                },
                {
                    "name": "Function",
                    "scope": ["entity.name.function", "support.function"],
                    "settings": {"foreground": "#dcdcaa"}
                },
                {
                    "name": "Variable",
                    "scope": ["variable", "variable.other"],
                    "settings": {"foreground": "#9cdcfe"}
                },
                {
                    "name": "Class",
                    "scope": ["entity.name.class", "entity.name.type.class", "support.class"],
                    "settings": {"foreground": "#4ec9b0"}
                },
                {
                    "name": "Interface",
                    "scope": ["entity.name.type.interface"],
                    "settings": {"foreground": "#4ec9b0"}
                },
                {
                    "name": "Type",
                    "scope": ["entity.name.type", "support.type"],
                    "settings": {"foreground": "#4ec9b0"}
                },
                {
                    "name": "Constant",
                    "scope": ["constant", "constant.language", "support.constant"],
                    "settings": {"foreground": "#569cd6"}
                },
                {
                    "name": "Tag",
                    "scope": ["entity.name.tag", "meta.tag"],
                    "settings": {"foreground": "#569cd6"}
                },
                {
                    "name": "Attribute",
                    "scope": ["entity.other.attribute-name"],
                    "settings": {"foreground": "#9cdcfe"}
                },
                {
                    "name": "Invalid",
                    "scope": ["invalid", "invalid.illegal"],
                    "settings": {"foreground": "#f44747"}
                },
                {
                    "name": "Invalid Deprecated",
                    "scope": ["invalid.deprecated"],
                    "settings": {"foreground": "#f44747", "fontStyle": "strikethrough"}
                }
            ]
        else:
            # Light theme colors
            return [
                {
                    "name": "Comment",
                    "scope": ["comment", "punctuation.definition.comment"],
                    "settings": {"foreground": "#008000", "fontStyle": "italic"}
                },
                {
                    "name": "String",
                    "scope": ["string", "string.quoted"],
                    "settings": {"foreground": "#a31515"}
                },
                {
                    "name": "Number",
                    "scope": ["constant.numeric"],
                    "settings": {"foreground": "#09885a"}
                },
                {
                    "name": "Keyword",
                    "scope": ["keyword", "keyword.control"],
                    "settings": {"foreground": "#0000ff"}
                },
                {
                    "name": "Storage",
                    "scope": ["storage", "storage.type", "storage.modifier"],
                    "settings": {"foreground": "#0000ff"}
                },
                {
                    "name": "Function",
                    "scope": ["entity.name.function", "support.function"],
                    "settings": {"foreground": "#795e26"}
                },
                {
                    "name": "Variable",
                    "scope": ["variable", "variable.other"],
                    "settings": {"foreground": "#001080"}
                },
                {
                    "name": "Class",
                    "scope": ["entity.name.class", "entity.name.type.class", "support.class"],
                    "settings": {"foreground": "#267f99"}
                },
                {
                    "name": "Interface",
                    "scope": ["entity.name.type.interface"],
                    "settings": {"foreground": "#267f99"}
                },
                {
                    "name": "Type",
                    "scope": ["entity.name.type", "support.type"],
                    "settings": {"foreground": "#267f99"}
                },
                {
                    "name": "Constant",
                    "scope": ["constant", "constant.language", "support.constant"],
                    "settings": {"foreground": "#0000ff"}
                },
                {
                    "name": "Tag",
                    "scope": ["entity.name.tag", "meta.tag"],
                    "settings": {"foreground": "#800000"}
                },
                {
                    "name": "Attribute",
                    "scope": ["entity.other.attribute-name"],
                    "settings": {"foreground": "#ff0000"}
                },
                {
                    "name": "Invalid",
                    "scope": ["invalid", "invalid.illegal"],
                    "settings": {"foreground": "#cd3131"}
                },
                {
                    "name": "Invalid Deprecated",
                    "scope": ["invalid.deprecated"],
                    "settings": {"foreground": "#cd3131", "fontStyle": "strikethrough"}
                }
            ]