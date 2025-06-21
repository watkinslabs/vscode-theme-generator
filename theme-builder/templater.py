"""
Template engine for generating VS Code theme files
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .constants import DEFAULT_TEMPLATES_DIR, VSCODE_ENGINES_VERSION

logger = logging.getLogger(__name__)

class Templater:
    """Handles template rendering for theme files"""
    
    def __init__(self, config):
        self.config = config
        
        # Setup Jinja2 environment
        template_dir = Path(config.get('templates.directory', DEFAULT_TEMPLATES_DIR))
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['jsonify'] = lambda x: json.dumps(x, indent=2)
        self.env.filters['jsonify_compact'] = lambda x: json.dumps(x)
        
    def generate_theme_files(self, theme_def: Dict[str, Any], output_dir: Path):
        """Generate all theme files from templates"""
        theme_data = theme_def.get('theme', theme_def)
        
        # Ensure required directories exist
        (output_dir / "themes").mkdir(parents=True, exist_ok=True)
        (output_dir / ".vscode").mkdir(exist_ok=True)
        
        # Generate each file
        self._generate_package_json(theme_data, output_dir)
        self._generate_theme_json(theme_data, output_dir)
        self._generate_readme(theme_data, output_dir)
        self._generate_changelog(theme_data, output_dir)
        self._generate_license(theme_data, output_dir)
        self._generate_vscode_launch(theme_data, output_dir)
        self._generate_quickstart(theme_data, output_dir)
        
    def _generate_package_json(self, theme_data: Dict[str, Any], output_dir: Path):
        """Generate package.json"""
        template = self.env.get_template('package.json.j2')
        
        # Prepare context
        context = {
            'name': theme_data['name'].replace('_', '-'),
            'display_name': theme_data.get('display_name', theme_data['name']),
            'description': theme_data.get('description', 'A custom VS Code theme'),
            'version': theme_data.get('version', '1.0.0'),
            'publisher': theme_data.get('publisher', 'unknown'),
            'author': theme_data.get('author', {
                'name': 'Unknown',
                'email': 'unknown@example.com'
            }),
            'keywords': theme_data.get('keywords', ['theme', 'color-theme']),
            'engines_version': VSCODE_ENGINES_VERSION,
            'repository': theme_data.get('repository', ''),
            'icon': 'images/icon.png' if (output_dir / 'images' / 'icon.png').exists() else '',
            'theme_file': f"{theme_data['name']}-color-theme.json"
        }
        
        # Render and save
        content = template.render(**context)
        package_path = output_dir / 'package.json'
        package_path.write_text(content)
        logger.debug(f"Generated: {package_path}")
        
    def _generate_theme_json(self, theme_data: Dict[str, Any], output_dir: Path):
        """Generate the actual theme JSON file"""
        template = self.env.get_template('theme.json.j2')
        
        # Prepare context
        context = {
            'name': theme_data.get('display_name', theme_data['name']),
            'type': theme_data.get('type', 'dark'),
            'colors': theme_data.get('colors', {}),
            'token_colors': theme_data.get('token_colors', [])
        }
        
        # Render and save
        content = template.render(**context)
        theme_path = output_dir / 'themes' / f"{theme_data['name']}-color-theme.json"
        theme_path.write_text(content)
        logger.debug(f"Generated: {theme_path}")
        
    def _generate_readme(self, theme_data: Dict[str, Any], output_dir: Path):
        """Generate README.md"""
        template = self.env.get_template('README.md.j2')
        
        # Prepare context
        context = {
            'display_name': theme_data.get('display_name', theme_data['name']),
            'description': theme_data.get('description', 'A custom VS Code theme'),
            'author': theme_data.get('author', {}),
            'features': theme_data.get('features', []),
            'screenshots': self._get_screenshots(output_dir),
            'installation': theme_data.get('installation', {}),
            'repository': theme_data.get('repository', ''),
            'license': theme_data.get('license', 'MIT'),
        }
        
        # Render and save
        content = template.render(**context)
        readme_path = output_dir / 'README.md'
        readme_path.write_text(content)
        logger.debug(f"Generated: {readme_path}")
        
    def _generate_changelog(self, theme_data: Dict[str, Any], output_dir: Path):
        """Generate CHANGELOG.md"""
        template = self.env.get_template('CHANGELOG.md.j2')
        
        # Prepare context
        context = {
            'version': theme_data.get('version', '1.0.0'),
            'name': theme_data['name'],
            'changes': theme_data.get('changelog', [])
        }
        
        # Render and save
        content = template.render(**context)
        changelog_path = output_dir / 'CHANGELOG.md'
        changelog_path.write_text(content)
        logger.debug(f"Generated: {changelog_path}")
        
    def _generate_license(self, theme_data: Dict[str, Any], output_dir: Path):
        """Generate LICENSE file"""
        template = self.env.get_template('LICENSE.j2')
        
        # Prepare context
        context = {
            'year': theme_data.get('year', '2024'),
            'author': theme_data.get('author', {}).get('name', 'Unknown'),
            'license_type': theme_data.get('license', 'MIT')
        }
        
        # Render and save
        content = template.render(**context)
        license_path = output_dir / 'LICENSE'
        license_path.write_text(content)
        logger.debug(f"Generated: {license_path}")
        
    def _generate_vscode_launch(self, theme_data: Dict[str, Any], output_dir: Path):
        """Generate .vscode/launch.json for testing"""
        launch_config = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Extension",
                    "type": "extensionHost",
                    "request": "launch",
                    "args": [
                        "--extensionDevelopmentPath=${workspaceFolder}"
                    ]
                }
            ]
        }
        
        launch_path = output_dir / '.vscode' / 'launch.json'
        launch_path.write_text(json.dumps(launch_config, indent=2))
        logger.debug(f"Generated: {launch_path}")
        
    def _generate_quickstart(self, theme_data: Dict[str, Any], output_dir: Path):
        """Generate vsc-extension-quickstart.md"""
        template = self.env.get_template('quickstart.md.j2')
        
        # Prepare context
        context = {
            'name': theme_data['name'],
            'display_name': theme_data.get('display_name', theme_data['name'])
        }
        
        # Render and save
        content = template.render(**context)
        quickstart_path = output_dir / 'vsc-extension-quickstart.md'
        quickstart_path.write_text(content)
        logger.debug(f"Generated: {quickstart_path}")
        
    def _get_screenshots(self, output_dir: Path) -> list:
        """Get list of screenshot files"""
        screenshots = []
        images_dir = output_dir / 'images'
        
        if images_dir.exists():
            for img_file in images_dir.glob('screenshot*.png'):
                screenshots.append({
                    'path': f'images/{img_file.name}',
                    'caption': f'Theme Preview {len(screenshots) + 1}'
                })
                
        return screenshots