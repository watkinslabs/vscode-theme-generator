"""
VSIX packager for VS Code themes
"""

import os
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class Packager:
    """Handles VSIX packaging for VS Code extensions"""
    
    def __init__(self, config):
        self.config = config
        
    def create_vsix(self, theme_dir: Path, output_path: Optional[Path] = None) -> Path:
        """Create VSIX package from theme directory"""
        # Check if vsce is installed
        if not self._check_vsce_installed():
            logger.warning("vsce not found. Installing...")
            self._install_vsce()
            
        # Validate theme directory
        if not self._validate_theme_directory(theme_dir):
            raise ValueError(f"Invalid theme directory: {theme_dir}")
            
        # Determine output path
        if not output_path:
            package_json = json.loads((theme_dir / 'package.json').read_text())
            name = package_json.get('name', 'theme')
            version = package_json.get('version', '1.0.0')
            output_path = theme_dir.parent / f"{name}-{version}.vsix"
            
        # Create VSIX
        logger.info(f"Creating VSIX package: {output_path}")
        
        try:
            # Run vsce package command
            result = subprocess.run(
                ['vsce', 'package', '--out', str(output_path)],
                cwd=theme_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"vsce package failed: {result.stderr}")
                raise RuntimeError(f"Failed to create VSIX: {result.stderr}")
                
            logger.info(f"Successfully created VSIX: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating VSIX: {e}")
            raise
            
    def _check_vsce_installed(self) -> bool:
        """Check if vsce is installed"""
        try:
            result = subprocess.run(
                ['vsce', '--version'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
            
    def _install_vsce(self):
        """Install vsce using npm"""
        try:
            logger.info("Installing vsce...")
            result = subprocess.run(
                ['npm', 'install', '-g', '@vscode/vsce'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to install vsce: {result.stderr}")
                
            logger.info("vsce installed successfully")
            
        except FileNotFoundError:
            raise RuntimeError("npm not found. Please install Node.js and npm first.")
            
    def _validate_theme_directory(self, theme_dir: Path) -> bool:
        """Validate that directory has required files for VS Code extension"""
        required_files = ['package.json', 'README.md']
        required_dirs = ['themes']
        
        for file_name in required_files:
            if not (theme_dir / file_name).exists():
                logger.error(f"Missing required file: {file_name}")
                return False
                
        for dir_name in required_dirs:
            if not (theme_dir / dir_name).is_dir():
                logger.error(f"Missing required directory: {dir_name}")
                return False
                
        # Validate package.json
        try:
            package_json = json.loads((theme_dir / 'package.json').read_text())
            
            # Check required fields
            required_fields = ['name', 'version', 'engines', 'contributes']
            for field in required_fields:
                if field not in package_json:
                    logger.error(f"Missing required field in package.json: {field}")
                    return False
                    
            # Check theme contribution
            themes = package_json.get('contributes', {}).get('themes', [])
            if not themes:
                logger.error("No themes defined in package.json")
                return False
                
        except Exception as e:
            logger.error(f"Invalid package.json: {e}")
            return False
            
        return True
    
    def create_installable_package(self, theme_dir: Path, output_dir: Path) -> Path:
        """Create a distributable package with installer script"""
        theme_name = theme_dir.name
        package_dir = output_dir / f"{theme_name}-package"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy theme files
        theme_dest = package_dir / theme_name
        if theme_dest.exists():
            shutil.rmtree(theme_dest)
        shutil.copytree(theme_dir, theme_dest)
        
        # Create VSIX
        vsix_path = self.create_vsix(theme_dir, package_dir / f"{theme_name}.vsix")
        
        # Create install script for different platforms
        self._create_install_scripts(package_dir, theme_name)
        
        # Create README for package
        self._create_package_readme(package_dir, theme_name)
        
        # Create zip archive
        archive_path = output_dir / f"{theme_name}-package.zip"
        shutil.make_archive(
            str(archive_path.with_suffix('')),
            'zip',
            package_dir
        )
        
        # Clean up temp directory
        shutil.rmtree(package_dir)
        
        logger.info(f"Created installable package: {archive_path}")
        return archive_path
    
    def _create_install_scripts(self, package_dir: Path, theme_name: str):
        """Create platform-specific install scripts"""
        # Windows batch script
        windows_script = f"""@echo off
echo Installing {theme_name} VS Code Theme...
code --install-extension {theme_name}.vsix
if %errorlevel% neq 0 (
    echo Failed to install theme. Make sure VS Code is installed and in PATH.
    pause
    exit /b 1
)
echo Theme installed successfully!
echo Restart VS Code and select the theme from Preferences > Color Theme
pause
"""
        (package_dir / 'install.bat').write_text(windows_script)
        
        # Unix shell script
        unix_script = f"""#!/bin/bash
echo "Installing {theme_name} VS Code Theme..."
code --install-extension {theme_name}.vsix
if [ $? -ne 0 ]; then
    echo "Failed to install theme. Make sure VS Code is installed and in PATH."
    exit 1
fi
echo "Theme installed successfully!"
echo "Restart VS Code and select the theme from Preferences > Color Theme"
"""
        install_sh = package_dir / 'install.sh'
        install_sh.write_text(unix_script)
        install_sh.chmod(0o755)
        
    def _create_package_readme(self, package_dir: Path, theme_name: str):
        """Create README for the package"""
        readme_content = f"""# {theme_name} VS Code Theme Package

## Installation

### Option 1: Automatic Installation

**Windows:**
1. Double-click `install.bat`

**macOS/Linux:**
1. Open Terminal in this directory
2. Run: `./install.sh`

### Option 2: Manual Installation

1. Open VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
3. Type "Install from VSIX"
4. Select the `{theme_name}.vsix` file from this directory

### Option 3: Command Line

```bash
code --install-extension {theme_name}.vsix
```

## Activating the Theme

1. Open VS Code
2. Press `Ctrl+K Ctrl+T` (or `Cmd+K Cmd+T` on macOS)
3. Select "{theme_name}" from the list

## Troubleshooting

If installation fails:
- Make sure VS Code is installed
- Ensure VS Code is in your system PATH
- Try running VS Code as administrator (Windows)

## Uninstalling

To uninstall the theme:
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "{theme_name}"
4. Click Uninstall
"""
        (package_dir / 'README.md').write_text(readme_content)