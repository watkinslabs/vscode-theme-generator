"""
Screenshot generator for VS Code themes
"""

import subprocess
import time
import platform
import shutil
import json
from pathlib import Path
from typing import Optional, List

import os
import subprocess
import platform
import shutil
import time
import json
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from .constants import SCREENSHOT_CONFIG

logger = logging.getLogger(__name__)

# In screenshot_generator.py, modify the class:

class ScreenshotGenerator:
    """Generates screenshots for VS Code themes"""

    def __init__(self, config):
        self.config = config
        self.screenshot_config = config.get('build.screenshot_config', SCREENSHOT_CONFIG)
        self.window_size = self.screenshot_config.get('window_size', (1920, 1080))

        # Check if we can use VS Code automation
        self.use_vscode_automation = self._check_vscode_available()
        if self.use_vscode_automation:
            self.vscode_generator = VSCodeAutomationScreenshotGenerator(config)

    def _check_vscode_available(self) -> bool:
        """Check if VS Code is installed and available"""
        try:
            result = subprocess.run(['code', '--version'], capture_output=True)
            return result.returncode == 0
        except:
            return False

    def generate_single_screenshot(self,
                                 theme_name: str,
                                 theme_dir: Path,
                                 code_file: Optional[Path] = None,
                                 language: str = "python") -> Path:
        """Generate a single screenshot"""

        if self.use_vscode_automation:
            print("Using VS Code automation for screenshot...")
            try:
                return self.vscode_generator.generate_single_screenshot(
                    theme_name, theme_dir, code_file, language
                )
            except Exception as e:
                print(f"VS Code automation failed: {e}")

        return None


    def _generate_vscode_screenshot_single(self,
                                         theme_name: str,
                                         theme_dir: Path,
                                         code_file: Optional[Path],
                                         language: str) -> Path:
        """Generate a single VS Code screenshot using Selenium"""
        # Not implemented - fall back to mock
        return self._generate_mock_screenshot_single(theme_name, theme_dir, code_file, language)


class VSCodeAutomationScreenshotGenerator:
    """Generate screenshots by automating actual VS Code"""

    def __init__(self, config):
        self.config = config
        self.system = platform.system()
        self.vscode_process = None  # Track the VS Code process we spawn


    def _check_vscode_installed(self) -> bool:
        """Check if VS Code is available"""
        try:
            result = subprocess.run(['code', '--version'], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _get_installed_extensions(self) -> List[str]:
        """Get list of installed VS Code extensions"""
        try:
            result = subprocess.run(
                ['code', '--list-extensions'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except:
            pass
        return []

    def _create_temp_code_file(self, language: str) -> Path:
        """Create a temporary code file with sample code"""
        temp_dir = Path("/tmp/vscode_theme_screenshots")
        temp_dir.mkdir(exist_ok=True)

        # Get sample code from SCREENSHOT_CONFIG or use defaults
        samples = self.config.get('build.screenshot_config.code_samples', {})

        default_samples = {
            'python': '''#!/usr/bin/env python3
"""VS Code Theme Preview - Python Sample"""

import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ThemeColors:
    """Theme color configuration"""
    background: str = "#1e1e1e"
    foreground: str = "#d4d4d4"
    accent: str = "#007acc"

    def validate(self) -> bool:
        """Validate color values"""
        for color in [self.background, self.foreground, self.accent]:
            if not color.startswith('#'):
                return False
        return True

async def process_theme(name: str, colors: ThemeColors) -> Dict[str, str]:
    """Process theme configuration"""
    if not colors.validate():
        raise ValueError(f"Invalid colors for theme: {name}")

    # Simulate async processing
    await asyncio.sleep(0.1)

    return {
        "name": name,
        "type": "dark" if colors.background < "#7f7f7f" else "light",
        "colors": {
            "editor.background": colors.background,
            "editor.foreground": colors.foreground,
        }
    }

# Example usage
if __name__ == "__main__":
    theme = ThemeColors()
    result = asyncio.run(process_theme("My Theme", theme))
    print(f"Generated theme: {result}")
''',
            'javascript': '''// VS Code Theme Preview - JavaScript Sample

import React, { useState, useEffect } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';

const ThemePreview = ({ themeName, colors }) => {
    const [loading, setLoading] = useState(true);
    const [preview, setPreview] = useState(null);

    useEffect(() => {
        async function loadPreview() {
            try {
                const response = await fetch(`/api/themes/${themeName}`);
                const data = await response.json();
                setPreview(data);
            } catch (error) {
                console.error('Failed:', error);
            } finally {
                setLoading(false);
            }
        }

        loadPreview();
    }, [themeName]);

    return (
        <div className="theme-preview">
            {loading ? <Loading /> : <Preview data={preview} />}
        </div>
    );
};

export default ThemePreview;
''',
            'rust': '''// VS Code Theme Preview - Rust Sample

use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Theme {
    name: String,
    colors: HashMap<String, String>,
}

impl Theme {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            colors: HashMap::new(),
        }
    }

    pub fn with_color(mut self, key: &str, value: &str) -> Self {
        self.colors.insert(key.to_string(), value.to_string());
        self
    }
}

fn main() {
    let theme = Theme::new("rust-theme")
        .with_color("editor.background", "#1e1e1e")
        .with_color("editor.foreground", "#d4d4d4");

    println!("Theme: {:?}", theme);
}
'''
        }

        code = samples.get(language, default_samples.get(language, default_samples['python']))
        file_ext = {'python': 'py', 'javascript': 'js', 'rust': 'rs'}.get(language, 'txt')

        code_file = temp_dir / f"sample.{file_ext}"
        code_file.write_text(code)

        return code_file

    def _take_screenshot(self, output_path: Path) -> bool:
        """Take screenshot based on OS"""
        try:
            if self.system == "Linux":
                return self._take_screenshot_linux(output_path)
            elif self.system == "Darwin":
                return self._take_screenshot_macos(output_path)
            elif self.system == "Windows":
                return self._take_screenshot_windows(output_path)
            else:
                print(f"Unsupported OS: {self.system}")
                return False
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return False

    def _take_screenshot_macos(self, output_path: Path) -> bool:
        """Take screenshot on macOS"""
        print("Click on the VS Code window to capture...")
        result = subprocess.run([
            'screencapture',
            '-i',  # Interactive
            '-w',  # Window mode
            str(output_path)
        ])
        return result.returncode == 0

    def _take_screenshot_windows(self, output_path: Path) -> bool:
        """Take screenshot on Windows"""
        # You could use pyautogui or other tools here
        print("Windows screenshot not implemented yet")
        return False

    def _focus_vscode_window(self):
        """Try to focus VS Code window using wmctrl or xdotool"""
        # Wait a bit for window to appear
        time.sleep(1)

        if shutil.which('wmctrl'):
            # List all windows to find the right VS Code instance
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                windows = result.stdout.strip().split('\n')
                # Find the most recent VS Code window (should be our temp project)
                for window in reversed(windows):
                    if 'Visual Studio Code' in window and 'vscode_theme_screenshots' in window:
                        window_id = window.split()[0]
                        subprocess.run(['wmctrl', '-i', '-a', window_id])
                        print(f"Focused VS Code window: {window_id}")
                        return

            # Fallback to any VS Code window
            subprocess.run(['wmctrl', '-a', 'Visual Studio Code'])

        elif shutil.which('xdotool'):
            # Use xdotool to find and focus VS Code window
            result = subprocess.run(
                ['xdotool', 'search', '--name', 'vscode_theme_screenshots'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout:
                window_id = result.stdout.strip().split('\n')[-1]  # Get most recent
                subprocess.run(['xdotool', 'windowactivate', window_id])
                print(f"Focused VS Code window: {window_id}")


    def _verify_theme_installation(self, theme_name: str) -> str:
        """Verify theme is installed and get its exact extension ID"""
        result = subprocess.run(
            ['code', '--list-extensions'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            extensions = result.stdout.strip().split('\n')
            print(f"Installed extensions: {extensions}")

            # Look for our theme
            for ext in extensions:
                if theme_name in ext.lower():
                    print(f"Found theme extension: {ext}")
                    return ext

        return theme_name

    def _create_project_structure(self, project_dir: Path):
        """Create a realistic project structure for screenshots"""
        # Create directories
        (project_dir / 'src').mkdir(exist_ok=True)
        (project_dir / 'tests').mkdir(exist_ok=True)
        (project_dir / 'docs').mkdir(exist_ok=True)

        # Create some files to show in the sidebar
        files = {
            'README.md': '''# My Awesome Project

This is a demo project showcasing the VS Code theme.

## Features
- Beautiful syntax highlighting
- Clear and readable UI
- Optimized for long coding sessions
''',
        'package.json': '''{
"name": "demo-project",
"version": "1.0.0",
"description": "Demo project for theme preview",
"main": "src/index.js",
"scripts": {
    "start": "node src/index.js",
    "test": "jest"
}
}
''',
        '.gitignore': '''node_modules/
dist/
*.log
.env
.DS_Store
''',
        'src/index.js': '''// Main application entry point
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(3000);
''',
        'src/utils.py': '''"""Utility functions"""

def process_data(data):
    """Process the data"""
    return [x * 2 for x in data]
''',
        'tests/test_main.py': '''import pytest

def test_example():
    assert True
'''
        }

        # Write all files
        for filename, content in files.items():
            file_path = project_dir / filename
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(content)

    def _take_screenshot_linux(self, output_path: Path) -> bool:
        """Take screenshot on Linux - capture specific window"""

        # First, let's find our VS Code window by title
        if shutil.which('xdotool'):
            print("Finding VS Code theme screenshot window...")

            # Search for our specific window
            result = subprocess.run(
                ['xdotool', 'search', '--name', 'VS Code Theme Screenshot'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout:
                window_id = result.stdout.strip().split('\n')[0]
                print(f"Found window ID: {window_id}")

                # Focus the window
                subprocess.run(['xdotool', 'windowactivate', window_id])
                time.sleep(0.5)  # Brief pause for focus

                # Take screenshot of this specific window
                if shutil.which('import'):
                    # Use ImageMagick import with specific window ID
                    print("Taking screenshot with ImageMagick...")
                    result = subprocess.run([
                        'import',
                        '-window', window_id,
                        str(output_path)
                    ])
                    return result.returncode == 0

                elif shutil.which('scrot'):
                    # Use scrot with focused window
                    print("Taking screenshot with scrot...")
                    result = subprocess.run([
                        'scrot',
                        '--focused',
                        '--delay', '0',  # No delay
                        str(output_path)
                    ])
                    return result.returncode == 0

        # Fallback to gnome-screenshot with interactive window selection
        if shutil.which('gnome-screenshot'):
            print("Using gnome-screenshot...")
            print("Please click on the VS Code window in the next 3 seconds...")

            result = subprocess.run([
                'gnome-screenshot',
                '-w',  # Window mode
                '--delay=3',  # 3 second delay to click the right window
                '-f', str(output_path)
            ])

            return result.returncode == 0

        print("No suitable screenshot tool found!")
        return False

    def _close_screenshot_window(self):
        """Close only the VS Code window we opened for screenshots"""
        if shutil.which('xdotool'):
            # Find our specific window by title
            result = subprocess.run(
                ['xdotool', 'search', '--name', 'VS Code Theme Screenshot'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout:
                window_id = result.stdout.strip().split('\n')[0]
                print(f"Closing window ID: {window_id}")
                # Close just this window
                subprocess.run(['xdotool', 'windowclose', window_id])
                return

        elif shutil.which('wmctrl'):
            # Use wmctrl to close specific window
            subprocess.run(['wmctrl', '-c', 'VS Code Theme Screenshot'])
            return

        # Fallback - but this might close all VS Code windows, so warn user
        print("Warning: Could not find specific window to close")
        print("You may need to close the VS Code screenshot window manually")


    # Replace the generate_single_screenshot method:
    def generate_single_screenshot(self, theme_name: str, theme_dir: Path,
                                code_file: Optional[Path] = None,
                                language: str = "python") -> Path:
        """Generate a screenshot using actual VS Code"""
        try:
            print("\n=== VS Code Screenshot Generation ===")

            # Check VS Code is installed
            if not self._check_vscode_installed():
                raise RuntimeError("VS Code is not installed or not in PATH")

            print("✓ VS Code found")

            # Find the VSIX file
            vsix_files = list(theme_dir.glob("*.vsix"))
            if not vsix_files:
                raise RuntimeError(f"No VSIX file found in {theme_dir}")
            vsix_path = vsix_files[0]
            print(f"✓ Found VSIX: {vsix_path.name}")

            # Install extension
            print(f"Installing theme extension...")
            subprocess.run(
                ['code', '--install-extension', str(vsix_path), '--force'],
                capture_output=True
            )

            # Create or use code file
            if not code_file:
                code_file = self._create_temp_code_file(language)
                print(f"✓ Created sample code file: {code_file}")

            # Open VS Code with the theme
            print(f"Opening VS Code with '{theme_name}' theme...")
            self._setup_and_open_vscode(code_file, theme_name)

            # Wait for VS Code to render
            print("Waiting 2 seconds for VS Code to render...")
            time.sleep(2)

            # Take screenshot
            screenshot_path = theme_dir / 'images' / f'screenshot.png'
            screenshot_path.parent.mkdir(exist_ok=True)

            print(f"Taking screenshot...")
            success = self._take_screenshot(screenshot_path)

            if success:
                print(f"✓ Screenshot saved to: {screenshot_path}")
            else:
                raise RuntimeError("Failed to take screenshot")

            # Close the VS Code process we opened
            print("Closing VS Code screenshot window...")
            self._close_vscode_process()

            return screenshot_path
            
        finally:
            # Always cleanup the VS Code process
            if self.vscode_process:
                self._close_vscode_process()

    # Replace the _setup_and_open_vscode method:
    def _setup_and_open_vscode(self, code_file: Path, theme_name: str):
        """Open VS Code with the theme applied"""
        # Create project structure
        project_dir = code_file.parent
        self._create_project_structure(project_dir)

        # Create workspace settings
        workspace_dir = project_dir / '.vscode'
        workspace_dir.mkdir(exist_ok=True)

        # Get theme label
        theme_dir = Path(self.config.get('generator.output_dir', './build')) / theme_name
        package_json_path = theme_dir / 'package.json'

        theme_label = theme_name
        if package_json_path.exists():
            import json
            with open(package_json_path) as f:
                package_data = json.load(f)
                themes = package_data.get('contributes', {}).get('themes', [])
                if themes:
                    theme_label = themes[0].get('label', theme_name)

        print(f"Using theme label: '{theme_label}'")

        settings = {
            "workbench.colorTheme": theme_label,
            "window.zoomLevel": 0,
            "editor.fontSize": 14,
            "editor.minimap.enabled": True,
            "workbench.activityBar.visible": True,
            "workbench.statusBar.visible": True,
            "workbench.sideBar.location": "left",
            "breadcrumbs.enabled": True,
            "window.menuBarVisibility": "compact",
            "workbench.startupEditor": "none",
            "editor.scrollBeyondLastLine": False,
            "editor.renderWhitespace": "none",
            "editor.lineNumbers": "on",
            "explorer.openEditors.visible": 0,
            "workbench.sideBar.visible": True,
            "workbench.panel.defaultLocation": "bottom",
            "workbench.panel.opensMaximized": "never",
            "window.title": f"VS Code Theme Screenshot - {theme_name}"
        }

        settings_file = workspace_dir / 'settings.json'
        settings_file.write_text(json.dumps(settings, indent=2))

        # Open VS Code and track the process
        cmd = [
            'code',
            '-n',  # New window
            str(project_dir)
        ]

        print(f"Opening VS Code...")
        # Use Popen to get the process object
        self.vscode_process = subprocess.Popen(cmd)

        # Give it a moment to open
        time.sleep(1)

        # Now open the file in that new window
        subprocess.run(['code', '--reuse-window', str(code_file)])

    # Add this new method to replace _close_screenshot_window:
    def _close_vscode_process(self):
        """Close the VS Code process we opened"""
        if self.vscode_process:
            try:
                # First try to terminate gracefully
                self.vscode_process.terminate()
                
                # Give it a moment to close
                try:
                    self.vscode_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # If it doesn't close, kill it
                    self.vscode_process.kill()
                    self.vscode_process.wait()
                
                print("VS Code process closed successfully")
            except Exception as e:
                print(f"Warning: Error closing VS Code process: {e}")
            finally:
                self.vscode_process = None
        else:
            print("No VS Code process to close")
