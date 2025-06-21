"""
Icon generator for VS Code themes
"""

import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image
import shutil

logger = logging.getLogger(__name__)


class IconGenerator:
    """Generates icons for VS Code themes using AI"""

    def __init__(self, config):
        self.config = config
        self.icon_size = (128, 128)  # VS Code marketplace icon size

        # Check if AI is enabled
        self.ai_enabled = config.get('ai.enabled', True)
        if self.ai_enabled:
            try:
                from wl_ai_manager import AIManager
                ai_manager_config = config.get('ai_manager', {})
                if ai_manager_config:
                    self.ai_manager = AIManager(ai_manager_config)
                else:
                    logger.warning("No ai_manager configuration found")
                    self.ai_manager = None
            except Exception as e:
                logger.error(f"Failed to initialize AI Manager: {e}")
                self.ai_manager = None
        else:
            self.ai_manager = None

    def generate_icon(self, theme_name: str, theme_data: Dict[str, Any], output_dir: Path) -> Optional[Path]:
        """Generate icon for theme"""
        logger.info(f"Generating icon for theme: {theme_name}")

        # Create images directory if it doesn't exist
        images_dir = output_dir / 'images'
        images_dir.mkdir(exist_ok=True)

        # FIXED: Always save as icon.png in the images directory
        icon_path = images_dir / 'icon.png'

        # Try AI generation first if available
        if self.ai_manager and self.ai_enabled:
            try:
                success = self._generate_ai_icon(theme_name, theme_data, icon_path)
                if success:
                    logger.info(f"AI-generated icon saved to: {icon_path}")
                    return icon_path
            except Exception as e:
                logger.warning(f"AI icon generation failed: {e}")
                logger.info("Falling back to procedural generation")

        # Fallback to procedural generation
        self._generate_procedural_icon(theme_name, theme_data, icon_path)
        logger.info(f"Procedural icon saved to: {icon_path}")
        return icon_path

    def _generate_ai_icon(self, theme_name: str, theme_data: Dict[str, Any], output_path: Path) -> bool:
        """Generate icon using AI based on theme description"""
        if not self.ai_manager:
            return False

        # Get theme description
        description = theme_data.get('description', theme_name)

        # Create prompt file if needed
        prompts_dir = Path(self.config.get('ai_manager.prompt_folder', './prompts'))
        prompts_dir.mkdir(exist_ok=True)

        # Prepare prompt data
        prompt_data = {
            'theme_description': description
        }

        try:
            logger.info(f"Generating AI icon for theme: {description}")

            # Get the formatted prompt
            prompt = self.ai_manager.prompt_template('icon', prompt_data, flatten=True, user_only=True)

            # Generate a temporary filename first
            temp_filename = f"icon_{theme_name}_{int(time.time())}"
            
            # Generate the icon to a temporary location
            result = self.ai_manager.generate_image(
                prompt=prompt,
                file_name=temp_filename,
                folder=str(output_path.parent),  # Generate in images directory
                width=512,
                height=512,
                file_type='png'
            )

            if result and Path(result).exists():
                # Move/rename to final location
                temp_path = Path(result)
                if temp_path != output_path:
                    shutil.move(str(temp_path), str(output_path))
                logger.info(f"AI generated icon saved to: {output_path}")
                return True
            else:
                logger.warning("AI image generation returned no result")
                return False

        except Exception as e:
            logger.error(f"Error generating AI icon: {e}")
            return False

    def _resize_icon(self, source_path: Path, output_path: Path):
        """Resize icon to VS Code standard size"""
        try:
            with Image.open(source_path) as img:
                # Convert to RGBA if not already
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                # Resize with high quality
                resized = img.resize(self.icon_size, Image.Resampling.LANCZOS)

                # Save the resized icon
                resized.save(output_path, 'PNG')

                logger.info(f"Resized icon from {img.size} to {self.icon_size}")
        except Exception as e:
            logger.error(f"Failed to resize icon: {e}")
            # If resize fails, just copy the original
            shutil.copy2(source_path, output_path)

    def _generate_procedural_icon(self, theme_name: str, theme_data: Dict[str, Any], output_path: Path):
        """Generate a procedural icon based on theme colors"""
        from PIL import Image, ImageDraw, ImageFont

        # Get theme colors
        colors = theme_data.get('colors', {})

        # Extract key colors
        bg_color = colors.get('editor.background', '#1e1e1e')
        fg_color = colors.get('editor.foreground', '#d4d4d4')
        accent_color = colors.get('activityBar.background', '#333333')
        badge_color = colors.get('activityBarBadge.background', '#007acc')

        # Create image with transparent background
        img = Image.new('RGBA', self.icon_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw a simple geometric design based on theme
        # Background circle
        margin = 10
        draw.ellipse([margin, margin, self.icon_size[0] - margin, self.icon_size[1] - margin],
                    fill=bg_color)

        # Inner design - create a code-editor inspired icon
        # Draw "code" lines
        line_height = 8
        line_margin = 30
        y_start = 35

        # Simulate code with colored rectangles
        code_colors = [
            badge_color,  # keyword
            fg_color,     # text
            accent_color, # comment
            fg_color,     # text
        ]

        for i in range(6):
            y = y_start + i * (line_height + 4)

            # Vary line lengths for code-like appearance
            line_lengths = [40, 60, 50, 70, 45, 55]
            line_length = line_lengths[i % len(line_lengths)]

            # Draw the "code" line
            color = code_colors[i % len(code_colors)]
            draw.rectangle([line_margin, y, line_margin + line_length, y + line_height],
                          fill=color)

        # Add a small accent - like a cursor
        cursor_x = line_margin + 25
        cursor_y = y_start + 2 * (line_height + 4)
        draw.rectangle([cursor_x, cursor_y, cursor_x + 2, cursor_y + line_height + 2],
                      fill=badge_color)

        # Add theme initial in corner
        try:
            font = ImageFont.truetype("DejaVuSans-Bold", 24)
        except:
            font = ImageFont.load_default()

        initial = theme_name[0].upper()
        draw.text((self.icon_size[0] - 35, self.icon_size[1] - 35), initial,
                 fill=fg_color, font=font)

        # Save the icon
        img.save(output_path, 'PNG')

    def generate_icon_batch(self, themes: list, output_base_dir: Path, delay_between_icons: int = 2) -> Dict[str, Any]:
        """Generate icons for multiple themes with rate limiting"""
        results = {
            'success': True,
            'generated': 0,
            'failed': 0,
            'failed_themes': [],
            'generated_icons': []
        }

        for idx, (theme_name, theme_data) in enumerate(themes):
            logger.info(f"\nGenerating icon {idx + 1}/{len(themes)}: {theme_name}")

            try:
                theme_output_dir = output_base_dir / theme_name
                icon_path = self.generate_icon(theme_name, theme_data, theme_output_dir)

                if icon_path and icon_path.exists():
                    results['generated'] += 1
                    results['generated_icons'].append({
                        'theme': theme_name,
                        'path': str(icon_path)
                    })
                else:
                    results['failed'] += 1
                    results['failed_themes'].append(theme_name)

                # Delay between AI requests to avoid rate limiting
                if self.ai_manager and idx < len(themes) - 1:
                    logger.info(f"Waiting {delay_between_icons} seconds before next icon...")
                    time.sleep(delay_between_icons)

            except Exception as e:
                logger.error(f"Failed to generate icon for {theme_name}: {e}")
                results['failed'] += 1
                results['failed_themes'].append(theme_name)

        return results