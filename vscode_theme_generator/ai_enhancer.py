"""
AI Enhancement module for theme optimization
"""

import json
import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path
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
        
        logger.info("=== AI Enhancer Initialization ===")
        # Don't try to JSON serialize the config object directly
        logger.info(f"AI Enabled: {self.theme_ai_config.get('enabled', True)}")

        # Initialize AI Manager if enabled
        if self.theme_ai_config.get('enabled', True):
            # Get the ai_manager configuration section
            ai_manager_config = config.get('ai_manager', {})
            logger.info(f"AI Manager Config Found: {bool(ai_manager_config)}")
            
            if ai_manager_config:
                try:
                    self.ai_manager = AIManager(ai_manager_config)
                    logger.info("✓ AI Manager initialized successfully")
                except Exception as e:
                    logger.error(f"✗ Failed to initialize AI Manager: {e}")
                    self.ai_manager = None
            else:
                logger.warning("✗ No ai_manager configuration found in config")
                self.ai_manager = None
        else:
            logger.info("AI enhancement disabled by configuration")
            self.ai_manager = None

    def enhance_theme(self, theme_def: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a theme definition with AI"""
        logger.info("=== Starting Theme Enhancement ===")
        logger.info(f"Original theme_def keys: {list(theme_def.keys())}")
        
        if not self.ai_manager:
            logger.info("AI enhancement disabled - returning original theme")
            return theme_def

        theme_data = theme_def.get('theme', theme_def)
        logger.info(f"Theme name: {theme_data.get('name', 'Unknown')}")
        logger.info(f"Theme data keys: {list(theme_data.keys())}")
        
        ai_settings = theme_data.get('ai_enhance', {})
        # Don't try to JSON serialize if it might contain non-serializable objects
        logger.info(f"AI Enhancement enabled: {ai_settings.get('enabled', True)}")
        
        # Track what we're enhancing
        enhancements_made = []

        # Enhance description
        if ai_settings.get('enhance_description', True):
            logger.info(">>> Enhancing description...")
            original_desc = theme_data.get('description', '')
            theme_data['description'] = self._enhance_description(
                theme_data.get('name', ''),
                original_desc
            )
            if theme_data['description'] != original_desc:
                enhancements_made.append('description')
                logger.info(f"✓ Description enhanced: '{original_desc}' -> '{theme_data['description']}'")

        # Optimize colors
        if ai_settings.get('optimize_colors', True):
            logger.info(">>> Optimizing colors...")
            original_colors = theme_data.get('colors', {}).copy()
            theme_data['colors'] = self._optimize_colors(original_colors)
            if theme_data['colors'] != original_colors:
                enhancements_made.append('colors')
                logger.info(f"✓ Colors optimized - {len(theme_data['colors'])} total colors")

        # Generate missing token colors
        if ai_settings.get('generate_token_colors', True) and not theme_data.get('token_colors'):
            logger.info(">>> Generating token colors...")
            theme_data['token_colors'] = self._generate_token_colors(theme_data.get('colors', {}))
            if theme_data['token_colors']:
                enhancements_made.append('token_colors')
                logger.info(f"✓ Generated {len(theme_data['token_colors'])} token colors")

        # Check contrast ratios
        if ai_settings.get('contrast_check', True):
            logger.info(">>> Checking contrast ratios...")
            original_colors = theme_data.get('colors', {}).copy()
            theme_data['colors'] = self._check_and_fix_contrast(original_colors)
            if theme_data['colors'] != original_colors:
                enhancements_made.append('contrast')
                logger.info("✓ Contrast ratios fixed")

        # Generate color variants
        if ai_settings.get('generate_variants', False):
            logger.info(">>> Generating color variants...")
            variants = self._generate_color_variants(theme_data)
            # Store variants in theme metadata
            theme_data['variants'] = variants
            if variants:
                enhancements_made.append('variants')
                logger.info(f"✓ Generated {len(variants)} color variants")

        logger.info(f"=== Enhancement Complete ===")
        logger.info(f"Enhancements made: {enhancements_made}")
        logger.info(f"Final theme_data keys: {list(theme_data.keys())}")
        
        # Make sure we return the enhanced theme in the right structure
        result = {'theme': theme_data}
        logger.info(f"Returning enhanced theme with structure: {list(result.keys())}")
        
        return result

    def _enhance_description(self, theme_name: str, current_description: str) -> str:
        """Use AI to enhance theme description"""
        logger.info(f"_enhance_description called with: name='{theme_name}', desc='{current_description}'")
        
        try:
            # Create prompt file if needed
            prompts_dir = Path(self.config.get('ai_manager.prompt_folder', './prompts'))
            prompts_dir.mkdir(exist_ok=True)

            # Use naming convention: enhance_theme_description.user.txt
            prompt_file = prompts_dir / 'enhance_theme_description.user.txt'
            if not prompt_file.exists():
                prompt_content = """Enhance this VS Code theme description to be more engaging and descriptive.
Keep it concise but compelling, under 200 characters.

Theme: {theme_name}
Current description: {description}

Provide an enhanced description that:
- Highlights the unique visual characteristics
- Mentions the target audience or use case
- Uses vivid but professional language
- Stays under 200 characters"""
                prompt_file.write_text(prompt_content)
                logger.info(f"Created prompt file: {prompt_file}")
                
            # Also create system prompt
            system_prompt_file = prompts_dir / 'enhance_theme_description.system.txt'
            if not system_prompt_file.exists():
                system_content = """You are a marketing copywriter specializing in developer tools. Create compelling, concise descriptions for VS Code themes."""
                system_prompt_file.write_text(system_content)
                logger.info(f"Created system prompt file: {system_prompt_file}")

            # Data for templating - NO SPACES in keys!
            prompt_data = {
                'theme_name': theme_name,
                'description': current_description
            }
            
            logger.info(f"Calling AI with theme_name='{theme_name}', description='{current_description}'")

            # Call with 'enhance_theme_description'
            response = self.ai_manager.chat('enhance_theme_description', prompt_data)
            
            logger.info(f"AI Response: {response}")
            
            enhanced_description = response.strip() if response else current_description

            # Ensure it's not too long
            if len(enhanced_description) > 200:
                enhanced_description = enhanced_description[:197] + "..."

            logger.info(f"Enhanced description result: '{enhanced_description}'")
            return enhanced_description

        except Exception as e:
            logger.error(f"Failed to enhance description: {e}", exc_info=True)
            return current_description

    def _optimize_colors(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Use AI to optimize theme colors"""
        logger.info(f"_optimize_colors called with {len(colors)} colors")
        
        try:
            # Create prompt file if needed
            prompts_dir = Path(self.config.get('ai_manager.prompt_folder', './prompts'))
            prompts_dir.mkdir(exist_ok=True)

            prompt_file = prompts_dir / 'optimize_theme_colors.user.txt'
            if not prompt_file.exists():
                prompt_content = """Review these VS Code theme colors and suggest optimizations.

Current colors:
{colors}

Analyze for:
1. Contrast ratios (WCAG compliance)
2. Color harmony
3. Eye strain reduction
4. Consistency across UI elements

Return a Python dictionary with any color changes needed. Example:
{
    "editor.background": "#1a1a1a",
    "editor.foreground": "#e0e0e0"
}

Only include colors that need to be changed."""
                prompt_file.write_text(prompt_content)
                logger.info(f"Created prompt file: {prompt_file}")
                
            # Also create system prompt
            system_prompt_file = prompts_dir / 'optimize_theme_colors.system.txt'
            if not system_prompt_file.exists():
                system_content = """You are a color theory and accessibility expert for VS Code themes. Analyze color schemes for contrast, harmony, and usability. Return only valid Python code."""
                system_prompt_file.write_text(system_content)
                logger.info(f"Created system prompt file: {system_prompt_file}")

            # Format colors for AI
            colors_json = json.dumps(colors, indent=2)
            prompt_data = {
                'colors': colors_json
            }
            
            logger.info(f"Calling AI to optimize colors...")
            logger.debug(f"Current colors sample: {list(colors.items())[:5]}")

            response = self.ai_manager.chat('optimize_theme_colors', prompt_data)
            
            if response:
                logger.info(f"AI color optimization response: {response[:500]}...")
            else:
                logger.warning("No response from AI for color optimization")
                return colors

            # Parse AI suggestions
            optimized_colors = self._parse_color_suggestions(response, colors)

            logger.info(f"Optimized {len(optimized_colors)} colors")
            changes = []
            for key in optimized_colors:
                if key in colors and optimized_colors[key] != colors[key]:
                    changes.append(f"{key}: {colors[key]} -> {optimized_colors[key]}")
            
            if changes:
                logger.info("Color changes made:")
                for change in changes[:10]:  # Show first 10 changes
                    logger.info(f"  {change}")
                if len(changes) > 10:
                    logger.info(f"  ... and {len(changes) - 10} more")
            
            return optimized_colors

        except Exception as e:
            logger.error(f"Failed to optimize colors: {e}", exc_info=True)
            return colors

    def _generate_token_colors(self, base_colors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate token colors based on theme colors"""
        logger.info("_generate_token_colors called")
        
        try:
            # Create prompt file if needed
            prompts_dir = Path(self.config.get('ai_manager.prompt_folder', './prompts'))
            prompts_dir.mkdir(exist_ok=True)

            prompt_file = prompts_dir / 'generate_token_colors.user.txt'
            if not prompt_file.exists():
                prompt_content = """Based on these base colors, generate token colors for syntax highlighting.

Base colors:
{base_colors}

Create a Python list of dictionaries for VS Code token colors. Example format:
[
    {
        "name": "Comment",
        "scope": ["comment", "punctuation.definition.comment"],
        "settings": {"foreground": "#6A9955", "fontStyle": "italic"}
    },
    {
        "name": "String", 
        "scope": ["string"],
        "settings": {"foreground": "#CE9178"}
    }
]

Include colors for: comments, strings, keywords, functions, variables, constants, types, numbers."""
                prompt_file.write_text(prompt_content)
                logger.info(f"Created prompt file: {prompt_file}")

            # Get key colors for generation
            key_colors = {
                'background': base_colors.get('editor.background', '#1e1e1e'),
                'foreground': base_colors.get('editor.foreground', '#d4d4d4'),
                'accent': base_colors.get('activityBar.background', '#007acc'),
            }
            
            prompt_data = {
                'base_colors': json.dumps(key_colors, indent=2)
            }
            
            logger.info(f"Generating token colors based on: {json.dumps(key_colors, indent=2)}")

            response = self.ai_manager.chat('generate_token_colors', prompt_data)
            
            logger.info(f"AI token colors response: {response[:500]}...")
            
            token_colors = self._parse_token_colors(response)

            logger.info(f"Generated {len(token_colors)} token colors")
            for tc in token_colors[:3]:  # Show first 3
                logger.debug(f"  Token: {tc.get('name', 'unnamed')} - {tc.get('scope', [])}")
            
            return token_colors

        except Exception as e:
            logger.error(f"Failed to generate token colors: {e}", exc_info=True)
            return self._get_fallback_token_colors(base_colors)

    def _check_and_fix_contrast(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Check and fix contrast ratios for accessibility"""
        logger.info("_check_and_fix_contrast called")
        
        fixed_colors = colors.copy()
        fixes_made = []

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
                    logger.warning(f"Low contrast ratio {ratio:.2f} for {bg_key}/{fg_key} (min: {min_ratio})")

                    # Try to fix by adjusting foreground brightness
                    fixed_fg = self._adjust_for_contrast(bg_color, fg_color, min_ratio)
                    if fixed_fg and fixed_fg != fg_color:
                        fixed_colors[fg_key] = fixed_fg
                        fixes_made.append(f"{fg_key}: {fg_color} -> {fixed_fg} (ratio: {ratio:.2f} -> {calculate_contrast_ratio(bg_color, fixed_fg):.2f})")

        if fixes_made:
            logger.info(f"Fixed {len(fixes_made)} contrast issues:")
            for fix in fixes_made:
                logger.info(f"  {fix}")
        else:
            logger.info("No contrast issues found")

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
        logger.info("_generate_color_variants called")
        
        base_colors = theme_data.get('colors', {})
        variants = {}

        # Generate light variant if theme is dark
        if self._is_dark_theme(base_colors):
            logger.info("Generating light variant...")
            variants['light'] = self._generate_light_variant(base_colors)

        # Generate high contrast variant
        logger.info("Generating high-contrast variant...")
        variants['high-contrast'] = self._generate_high_contrast_variant(base_colors)

        logger.info(f"Generated {len(variants)} variants")
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
        logger.info("_parse_color_suggestions called")
        
        optimized = original_colors.copy()

        # Try to extract dictionary from response
        import re
        import ast
        
        # Look for Python dictionary in response
        dict_match = re.search(r'\{[^}]*\}', ai_response, re.DOTALL)
        
        if dict_match:
            try:
                # Try to parse as Python dict
                dict_str = dict_match.group()
                logger.debug(f"Found potential dict: {dict_str[:200]}...")
                
                # Use ast.literal_eval for safe parsing
                parsed_dict = ast.literal_eval(dict_str)
                
                if isinstance(parsed_dict, dict):
                    for key, color in parsed_dict.items():
                        if key in original_colors and validate_hex_color(str(color)):
                            optimized[key] = str(color)
                            logger.debug(f"AI suggested {key}: {color}")
                            
            except (ValueError, SyntaxError) as e:
                logger.warning(f"Failed to parse dictionary from AI response: {e}")
                
                # Fallback: Look for hex color patterns in response
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
        logger.info("_parse_token_colors called")
        
        token_colors = []

        # Try to extract JSON/Python list from response
        import re
        import ast
        
        # Look for list pattern
        list_match = re.search(r'\[[\s\S]*\]', ai_response)

        if list_match:
            try:
                list_str = list_match.group()
                logger.debug(f"Found potential list: {list_str[:200]}...")
                
                # Try ast.literal_eval first (safer)
                parsed = ast.literal_eval(list_str)
                
                if isinstance(parsed, list):
                    # Validate structure
                    for item in parsed:
                        if isinstance(item, dict) and 'scope' in item and 'settings' in item:
                            # Ensure scope is a list
                            if isinstance(item['scope'], str):
                                item['scope'] = [item['scope']]
                            token_colors.append(item)
                            
                    logger.info(f"Successfully parsed {len(token_colors)} token colors")
                    return token_colors
                    
            except (ValueError, SyntaxError) as e:
                logger.warning(f"Failed to parse list with ast.literal_eval: {e}")
                
                # Try JSON parsing
                try:
                    parsed = json.loads(list_str)
                    if isinstance(parsed, list):
                        for item in parsed:
                            if isinstance(item, dict) and 'scope' in item and 'settings' in item:
                                token_colors.append(item)
                        return token_colors
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse JSON from AI response: {je}")

        # Fallback to manual parsing
        logger.warning("Falling back to manual token color parsing")
        
        # Look for token color patterns
        current_token = None
        for line in ai_response.split('\n'):
            # Look for name
            name_match = re.search(r'name["\']?\s*:\s*["\']([^"\']+)["\']', line)
            if name_match:
                if current_token and 'scope' in current_token and 'settings' in current_token:
                    token_colors.append(current_token)
                current_token = {'name': name_match.group(1)}

            # Look for scope
            scope_match = re.search(r'scope["\']?\s*:\s*\[([^\]]+)\]', line)
            if scope_match and current_token:
                scopes = [s.strip().strip('"\'') for s in scope_match.group(1).split(',')]
                current_token['scope'] = scopes

            # Look for foreground color
            fg_match = re.search(r'foreground["\']?\s*:\s*["\']?(#[0-9A-Fa-f]{6})["\']?', line)
            if fg_match and current_token:
                if 'settings' not in current_token:
                    current_token['settings'] = {}
                current_token['settings']['foreground'] = fg_match.group(1)

        # Add last token
        if current_token and 'scope' in current_token and 'settings' in current_token:
            token_colors.append(current_token)

        # If parsing failed, return fallback
        if not token_colors:
            logger.warning("Failed to parse token colors from AI, using fallback")
            return self._get_fallback_token_colors({})

        logger.info(f"Manually parsed {len(token_colors)} token colors")
        return token_colors

    def _get_fallback_token_colors(self, base_colors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get fallback token colors if AI generation fails"""
        logger.info("Using fallback token colors")
        
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