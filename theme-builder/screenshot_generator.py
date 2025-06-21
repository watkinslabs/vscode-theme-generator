"""
Screenshot generator for VS Code themes
"""

import os
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

class ScreenshotGenerator:
    """Generates screenshots for VS Code themes"""
    
    def __init__(self, config):
        self.config = config
        self.screenshot_config = config.get('build.screenshot_config', SCREENSHOT_CONFIG)
        self.window_size = self.screenshot_config.get('window_size', (1920, 1080))
        
    def generate_screenshots(self, theme_name: str, theme_dir: Path) -> List[Path]:
        """Generate all screenshots for a theme"""
        screenshots = []
        
        # Check if we can use selenium for real VS Code screenshots
        if self._check_selenium_available():
            logger.info("Using Selenium for VS Code screenshots")
            screenshots = self._generate_vscode_screenshots(theme_name, theme_dir)
        else:
            logger.info("Using mock renderer for screenshots")
            screenshots = self._generate_mock_screenshots(theme_name, theme_dir)
            
        return screenshots
    
    def generate_single_screenshot(self, 
                                 theme_name: str, 
                                 theme_dir: Path,
                                 code_file: Optional[Path] = None,
                                 language: str = "python") -> Path:
        """Generate a single screenshot"""
        if self._check_selenium_available():
            return self._generate_vscode_screenshot_single(theme_name, theme_dir, code_file, language)
        else:
            return self._generate_mock_screenshot_single(theme_name, theme_dir, code_file, language)
    
    def _check_selenium_available(self) -> bool:
        """Check if Selenium and Chrome are available"""
        try:
            # Check if we can create a Chrome driver
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            driver = webdriver.Chrome(
                ChromeDriverManager().install(),
                options=options
            )
            driver.quit()
            return True
        except Exception as e:
            logger.warning(f"Selenium not available: {e}")
            return False
    
    def _generate_mock_screenshots(self, theme_name: str, theme_dir: Path) -> List[Path]:
        """Generate mock screenshots using PIL"""
        screenshots = []
        screenshots_dir = theme_dir / 'images'
        screenshots_dir.mkdir(exist_ok=True)
        
        # Load theme colors
        theme_file = theme_dir / 'themes' / f"{theme_name}-color-theme.json"
        if not theme_file.exists():
            logger.error(f"Theme file not found: {theme_file}")
            return screenshots
            
        with open(theme_file, 'r') as f:
            theme_data = json.load(f)
            
        colors = theme_data.get('colors', {})
        
        # Generate screenshots for different languages
        languages = self.screenshot_config.get('languages', ['python'])
        for idx, language in enumerate(languages):
            screenshot_path = screenshots_dir / f"screenshot{idx + 1}.png"
            self._create_mock_screenshot(colors, language, screenshot_path)
            screenshots.append(screenshot_path)
            logger.info(f"Generated mock screenshot: {screenshot_path}")
            
        return screenshots
    
    def _create_mock_screenshot(self, colors: dict, language: str, output_path: Path):
        """Create a mock VS Code screenshot"""
        width, height = self.window_size
        
        # Create image with editor background
        bg_color = colors.get('editor.background', '#1e1e1e')
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Try to load a font
        try:
            font = ImageFont.truetype("Consolas", 14)
            title_font = ImageFont.truetype("Arial", 12)
        except:
            font = ImageFont.load_default()
            title_font = font
            
        # Draw VS Code UI elements
        # Activity bar
        activity_bar_bg = colors.get('activityBar.background', '#333333')
        activity_bar_fg = colors.get('activityBar.foreground', '#ffffff')
        draw.rectangle([0, 0, 50, height], fill=activity_bar_bg)
        
        # Sidebar
        sidebar_bg = colors.get('sideBar.background', '#252526')
        sidebar_fg = colors.get('sideBar.foreground', '#cccccc')
        draw.rectangle([50, 0, 300, height], fill=sidebar_bg)
        
        # Title bar
        titlebar_bg = colors.get('titleBar.activeBackground', '#3c3c3c')
        titlebar_fg = colors.get('titleBar.activeForeground', '#ffffff')
        draw.rectangle([0, 0, width, 30], fill=titlebar_bg)
        draw.text((10, 8), f"VS Code - {language}.py", fill=titlebar_fg, font=title_font)
        
        # Status bar
        statusbar_bg = colors.get('statusBar.background', '#007acc')
        statusbar_fg = colors.get('statusBar.foreground', '#ffffff')
        draw.rectangle([0, height - 25, width, height], fill=statusbar_bg)
        draw.text((10, height - 20), f"{language} | UTF-8 | Ln 42, Col 17", fill=statusbar_fg, font=title_font)
        
        # Editor area
        editor_x = 300
        editor_y = 30
        editor_fg = colors.get('editor.foreground', '#d4d4d4')
        
        # Get code sample
        code_lines = self._get_code_sample(language).split('\n')
        
        # Draw line numbers
        line_number_fg = colors.get('editorLineNumber.foreground', '#858585')
        for i, line in enumerate(code_lines[:40]):  # Limit to 40 lines
            y_pos = editor_y + 10 + (i * 20)
            # Line number
            draw.text((editor_x + 10, y_pos), f"{i+1:3}", fill=line_number_fg, font=font)
            # Code
            draw.text((editor_x + 50, y_pos), line, fill=editor_fg, font=font)
            
        # Save image
        img.save(output_path, 'PNG')
    
    def _get_code_sample(self, language: str) -> str:
        """Get code sample for language"""
        samples = {
            'python': '''#!/usr/bin/env python3
"""VS Code Theme Preview - Python"""

import asyncio
from typing import List, Dict, Optional

class ThemeDemo:
    def __init__(self, name: str):
        self.name = name
        self.colors: Dict[str, str] = {}
        
    async def load_theme(self) -> None:
        """Load theme configuration"""
        # This is a comment
        config = await self._read_config()
        self.colors = config.get('colors', {})
        
    def apply_theme(self, editor) -> bool:
        """Apply theme to editor"""
        try:
            for key, value in self.colors.items():
                editor.set_color(key, value)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

# Usage example
if __name__ == "__main__":
    theme = ThemeDemo("My Theme")
    asyncio.run(theme.load_theme())
''',
            'javascript': '''// VS Code Theme Preview - JavaScript

import React, { useState, useEffect } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';

const ThemePreview = ({ themeName, colors }) => {
    const [loading, setLoading] = useState(true);
    const [preview, setPreview] = useState(null);
    
    useEffect(() => {
        // Load theme preview
        async function loadPreview() {
            try {
                const response = await fetch(`/api/themes/${themeName}`);
                const data = await response.json();
                setPreview(data);
            } catch (error) {
                console.error('Failed to load:', error);
            } finally {
                setLoading(false);
            }
        }
        
        loadPreview();
    }, [themeName]);
    
    return (
        <ThemeProvider value={{ colors }}>
            <div className="theme-preview">
                {loading ? <Spinner /> : <Preview data={preview} />}
            </div>
        </ThemeProvider>
    );
};

export default ThemePreview;
''',
            'rust': '''// VS Code Theme Preview - Rust

use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Theme {
    name: String,
    colors: HashMap<String, String>,
    token_colors: Vec<TokenColor>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenColor {
    scope: Vec<String>,
    settings: TokenSettings,
}

impl Theme {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            colors: HashMap::new(),
            token_colors: Vec::new(),
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
        
        return samples.get(language, samples['python'])
    
    def _generate_vscode_screenshots(self, theme_name: str, theme_dir: Path) -> List[Path]:
        """Generate real VS Code screenshots using Selenium"""
        # This would require VS Code to be installed and accessible
        # For now, fall back to mock screenshots
        logger.warning("Real VS Code screenshots not implemented yet")
        return self._generate_mock_screenshots(theme_name, theme_dir)
    
    def _generate_mock_screenshot_single(self,
                                       theme_name: str,
                                       theme_dir: Path,
                                       code_file: Optional[Path],
                                       language: str) -> Path:
        """Generate a single mock screenshot"""
        screenshots_dir = theme_dir / 'images'
        screenshots_dir.mkdir(exist_ok=True)
        
        # Load theme
        theme_file = theme_dir / 'themes' / f"{theme_name}-color-theme.json"
        with open(theme_file, 'r') as f:
            theme_data = json.load(f)
            
        colors = theme_data.get('colors', {})
        
        # Generate screenshot
        screenshot_path = screenshots_dir / f"screenshot_{language}.png"
        
        # Use custom code if provided
        if code_file and code_file.exists():
            code_content = code_file.read_text()
            # Create custom screenshot with provided code
            self._create_mock_screenshot_with_code(colors, code_content, language, screenshot_path)
        else:
            self._create_mock_screenshot(colors, language, screenshot_path)
            
        return screenshot_path
    
    def _create_mock_screenshot_with_code(self, colors: dict, code: str, language: str, output_path: Path):
        """Create mock screenshot with custom code"""
        # Similar to _create_mock_screenshot but uses provided code
        width, height = self.window_size
        
        img = Image.new('RGB', (width, height), colors.get('editor.background', '#1e1e1e'))
        draw = ImageDraw.Draw(img)
        
        # Draw UI elements (same as before)
        # ... (simplified for brevity)
        
        # Draw the custom code
        editor_x = 300
        editor_y = 30
        editor_fg = colors.get('editor.foreground', '#d4d4d4')
        
        try:
            font = ImageFont.truetype("Consolas", 14)
        except:
            font = ImageFont.load_default()
            
        lines = code.split('\n')[:40]  # Limit lines
        for i, line in enumerate(lines):
            y_pos = editor_y + 10 + (i * 20)
            draw.text((editor_x + 50, y_pos), line, fill=editor_fg, font=font)
            
        img.save(output_path, 'PNG')
    
    def _generate_vscode_screenshot_single(self,
                                         theme_name: str,
                                         theme_dir: Path,
                                         code_file: Optional[Path],
                                         language: str) -> Path:
        """Generate a single VS Code screenshot using Selenium"""
        # Not implemented - fall back to mock
        return self._generate_mock_screenshot_single(theme_name, theme_dir, code_file, language)