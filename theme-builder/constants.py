"""
Constants for VS Code Theme Generator
"""

from pathlib import Path

# Version information
VERSION = "0.1.0"
THEME_SCHEMA_VERSION = "1.0"

# Default directories
DEFAULT_OUTPUT_DIR = Path("./build")
DEFAULT_THEMES_DIR = Path("./themes")
DEFAULT_TEMPLATES_DIR = Path(__file__).parent / "templates"
DEFAULT_TEMP_DIR = Path("./temp")
DEFAULT_SCREENSHOTS_DIR = Path("./screenshots")

# File patterns
THEME_FILE_PATTERN = "*.yaml"
VSIX_FILE_PATTERN = "*.vsix"

# VS Code specific
VSCODE_ENGINES_VERSION = "^1.74.0"
VSCODE_CATEGORIES = ["Themes"]

# Color validation patterns
HEX_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"
HEX_COLOR_WITH_ALPHA_PATTERN = r"^#[0-9A-Fa-f]{8}$"

# Default theme structure
DEFAULT_THEME_STRUCTURE = {
    "theme": {
        "name": "",
        "display_name": "",
        "description": "",
        "version": "1.0.0",
        "author": {
            "name": "",
            "email": ""
        },
        "keywords": [],
        "colors": {},
        "token_colors": []
    }
}

# Required color keys for a valid theme
REQUIRED_COLOR_KEYS = [
    "editor.background",
    "editor.foreground",
    "activityBar.background",
    "activityBar.foreground",
    "sideBar.background",
    "sideBar.foreground",
    "statusBar.background",
    "statusBar.foreground"
]

# AI prompt templates
AI_PROMPTS = {
    "enhance_description": """
Enhance this VS Code theme description to be more engaging and descriptive.
Keep it concise but compelling.

Theme: {theme_name}
Current description: {description}

Provide an enhanced description that:
- Highlights the unique visual characteristics
- Mentions the target audience or use case
- Uses vivid but professional language
- Stays under 200 characters
""",
    
    "optimize_colors": """
Review these VS Code theme colors and suggest optimizations.

Current colors:
{colors}

Analyze for:
1. Contrast ratios (WCAG compliance)
2. Color harmony
3. Eye strain reduction
4. Consistency across UI elements

Provide specific hex color recommendations for any issues found.
""",
    
    "generate_token_colors": """
Based on these base colors, generate a complete set of token colors for syntax highlighting.

Base colors:
{base_colors}

Create token colors for:
- Comments
- Strings
- Keywords
- Functions
- Variables
- Constants
- Operators
- Types

Ensure the colors work well together and maintain good contrast.
"""
}

# Screenshot configuration
SCREENSHOT_CONFIG = {
    "window_size": (1920, 1080),
    "code_samples": {
        "python": """
#!/usr/bin/env python3
\"\"\"
Example Python code for theme preview
\"\"\"

import asyncio
from typing import List, Dict, Optional

class ThemePreview:
    def __init__(self, name: str, colors: Dict[str, str]):
        self.name = name
        self.colors = colors
        self._initialized = False
    
    async def render(self, samples: List[str]) -> None:
        \"\"\"Render theme preview with code samples\"\"\"
        for idx, sample in enumerate(samples):
            print(f"Rendering sample {idx + 1}...")
            await self._process_sample(sample)
    
    async def _process_sample(self, sample: str) -> Optional[str]:
        # Process each code sample
        try:
            result = await asyncio.sleep(0.1)
            return f"Processed: {sample}"
        except Exception as e:
            print(f"Error: {e}")
            return None

# Example usage
if __name__ == "__main__":
    theme = ThemePreview("My Theme", {"bg": "#000000"})
    asyncio.run(theme.render(["sample1", "sample2"]))
""",
        
        "javascript": """
// Example JavaScript code for theme preview

import React, { useState, useEffect } from 'react';
import { ThemeProvider } from './theme-context';

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
                console.error('Failed to load preview:', error);
            } finally {
                setLoading(false);
            }
        }
        
        loadPreview();
    }, [themeName]);
    
    return (
        <ThemeProvider value={{ colors }}>
            <div className="theme-preview">
                {loading ? (
                    <LoadingSpinner />
                ) : (
                    <PreviewPane data={preview} />
                )}
            </div>
        </ThemeProvider>
    );
};

export default ThemePreview;
""",
        
        "rust": """
// Example Rust code for theme preview

use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Theme {
    name: String,
    display_name: String,
    colors: HashMap<String, String>,
    token_colors: Vec<TokenColor>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenColor {
    name: String,
    scope: Vec<String>,
    settings: TokenSettings,
}

impl Theme {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            display_name: String::new(),
            colors: HashMap::new(),
            token_colors: Vec::new(),
        }
    }
    
    pub fn with_color(mut self, key: &str, value: &str) -> Self {
        self.colors.insert(key.to_string(), value.to_string());
        self
    }
    
    pub fn build(self) -> Result<Theme, ThemeError> {
        if self.colors.is_empty() {
            return Err(ThemeError::NoColors);
        }
        Ok(self)
    }
}

fn main() {
    let theme = Theme::new("rust-theme")
        .with_color("editor.background", "#1e1e1e")
        .with_color("editor.foreground", "#d4d4d4")
        .build()
        .expect("Failed to build theme");
    
    println!("Created theme: {:?}", theme);
}
"""
    }
}