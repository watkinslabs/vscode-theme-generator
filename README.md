# VS Code Theme Generator

A powerful Python module for generating VS Code themes with AI enhancement, automated screenshots, and VSIX packaging.

[View Theme Gallery](THEME_GALLERY.md)


## Features

- 🎨 **Theme Generation** - Create beautiful VS Code themes from YAML definitions
- 🤖 **AI Enhancement** - Optimize colors and descriptions using AI
- 📸 **Automatic Screenshots** - Generate preview screenshots for your themes
- 📦 **VSIX Packaging** - Build ready-to-install extension packages
- ✅ **Validation** - Ensure themes meet VS Code standards
- 🔧 **CLI Tool** - Easy-to-use command line interface
- 🎯 **Templates** - Start quickly with built-in theme templates

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/vscode_theme_generator.git
cd vscode_theme_generator

# Install in development mode
pip install -e .

# Or install from PyPI (when published)
pip install vscode-theme-generator
```

## Quick Start

### 1. Create a New Theme

```bash
# Create a new theme from template
vscode-theme-gen create my-awesome-theme

# Create with options
vscode-theme-gen create cyber-theme --template minimal --description "A cyberpunk inspired theme"
```

### 2. Edit Your Theme

Edit the generated theme file in `themes/my-awesome-theme.yaml`:

```yaml
theme:
  name: "my-awesome-theme"
  display_name: "My Awesome Theme"
  description: "A beautiful theme for VS Code"
  
  colors:
    editor.background: "#1e1e1e"
    editor.foreground: "#d4d4d4"
    # ... add more colors
    
  token_colors:
    - name: "Comments"
      scope: ["comment"]
      settings:
        foreground: "#6A9955"
        fontStyle: "italic"
    # ... add more token colors
```

### 3. Build Your Theme

```bash
# Build all themes
vscode-theme-gen build

# Build specific theme
vscode-theme-gen build my-awesome-theme

# Build without AI enhancement
vscode-theme-gen build --no-ai

# Build without screenshots
vscode-theme-gen build --no-screenshots
```

### 4. Install and Test

The built theme will be in `build/my-awesome-theme/`. You can:

1. **Install the VSIX:**
   ```bash
   code --install-extension build/my-awesome-theme-1.0.0.vsix
   ```

2. **Or test locally:**
   - Open the theme folder in VS Code
   - Press `F5` to launch a new VS Code window with your theme

## Configuration

Configure the generator using `config.yaml`:

```yaml
generator:
  output_dir: ./build
  themes_dir: ./themes
  
ai:
  enabled: true
  model: "gpt-4"
  temperature: 0.7
  
build:
  create_vsix: true
  generate_screenshots: true
  
# ... see config.yaml for all options
```

## CLI Commands

### Build Themes
```bash
vscode-theme-gen build [theme_name] [options]

Options:
  --no-ai              Skip AI enhancement
  --no-screenshots     Skip screenshot generation
  --no-package         Skip VSIX creation
  --output DIR         Output directory
  --force              Overwrite existing files
```

### Create New Theme
```bash
vscode-theme-gen create <name> [options]

Options:
  --template TYPE      Template to use (default, minimal, full)
  --display-name NAME  Display name for the theme
  --description TEXT   Theme description
```

### List Themes
```bash
vscode-theme-gen list [options]

Options:
  --detailed          Show detailed information
```

### Validate Themes
```bash
vscode-theme-gen validate [theme_name] [options]

Options:
  --fix              Attempt to fix validation errors
```

### Generate Screenshots
```bash
vscode-theme-gen screenshot <theme_name> [options]

Options:
  --code-file FILE    Custom code file for screenshot
  --language LANG     Language for code sample
```

### Package Theme
```bash
vscode-theme-gen package <theme_name> [options]

Options:
  --output FILE       Output VSIX file path
```

### Clean Build Artifacts
```bash
vscode-theme-gen clean [options]

Options:
  --all              Remove all generated files
  --build            Remove only build directory
  --screenshots      Remove only screenshots
```

## Theme Definition Format

### Basic Structure

```yaml
theme:
  name: "theme-name"              # Internal name (lowercase, hyphens)
  display_name: "Theme Name"      # Display name in VS Code
  description: "Description"      # Short description
  version: "1.0.0"               # Semantic version
  type: "dark"                   # dark or light
  
  author:
    name: "Your Name"
    email: "email@example.com"
    
  colors:
    # VS Code UI colors
    editor.background: "#1e1e1e"
    editor.foreground: "#d4d4d4"
    # ... more colors
    
  token_colors:
    # Syntax highlighting
    - name: "Comment"
      scope: ["comment"]
      settings:
        foreground: "#6A9955"
        fontStyle: "italic"
    # ... more tokens
```

### AI Enhancement Options

```yaml
ai_enhance:
  optimize_colors: true      # Optimize color contrast
  enhance_description: true  # Improve theme description
  generate_variants: false   # Generate theme variants
  contrast_check: true       # Check WCAG compliance
```

## Integration with watkinslabs

This module integrates with:
- [ai_manager](https://github.com/watkinslabs/ai_manager) - For AI enhancement
- [config_manager](https://github.com/watkinslabs/config_manager) - For configuration management

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/vscode_theme_generator.git
cd vscode_theme_generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vscode_theme_generator

# Run specific test file
pytest tests/test_builder.py
```

### Code Style

```bash
# Format code
black vscode_theme_generator tests

# Sort imports
isort vscode_theme_generator tests

# Check code style
flake8 vscode_theme_generator tests

# Type checking
mypy vscode_theme_generator
```

## Examples

See the `examples/` directory for sample theme definitions:
- `tron.yaml` - TRON-inspired theme
- `matrix.yaml` - Matrix digital rain theme
- `cyberpunk.yaml` - Cyberpunk 2077 inspired theme

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- VS Code team for the excellent extension API
- All contributors and theme designers
- watkinslabs for AI and configuration management tools

## Support

- 📧 Email: support@example.com
- 💬 Discord: [Join our server](#)
- 🐛 Issues: [GitHub Issues](https://github.com/watkinslabs/vscode_theme_generator/issues)

---

Made with ❤️ by the VS Code Theme Generator team