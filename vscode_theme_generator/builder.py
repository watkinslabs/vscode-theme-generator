"""
Theme Builder - Main orchestration for theme generation
"""

import os
import shutil
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from tqdm import tqdm
from termcolor import colored
from datetime import datetime
from .templater import Templater
from .ai_enhancer import AIEnhancer
from .packager import Packager
from .validator import ThemeValidator
from .screenshot_generator import ScreenshotGenerator
from .icon_generator import IconGenerator
from .constants import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_THEMES_DIR,
    THEME_FILE_PATTERN,
    DEFAULT_THEME_STRUCTURE
)

logger = logging.getLogger(__name__)

class ThemeBuilder:
    """Main theme builder that orchestrates the build process"""

    def __init__(self, config):
        self.config = config

        # Setup directories
        self.themes_dir = Path(config.get('generator.themes_dir', DEFAULT_THEMES_DIR))
        self.output_dir = Path(config.get('generator.output_dir', DEFAULT_OUTPUT_DIR))
        self.temp_dir = Path(config.get('generator.temp_dir', './temp'))

        # Initialize components lazily to avoid errors during create
        self._templater = None
        self._ai_enhancer = None
        self._packager = None
        self._validator = None
        self._screenshot_generator = None
        self._icon_generator = None

    @property
    def templater(self):
        if self._templater is None:
            self._templater = Templater(self.config)
        return self._templater

    @property
    def ai_enhancer(self):
        if self._ai_enhancer is None:
            self._ai_enhancer = AIEnhancer(self.config)
        return self._ai_enhancer

    @property
    def packager(self):
        if self._packager is None:
            self._packager = Packager(self.config)
        return self._packager

    @property
    def validator(self):
        if self._validator is None:
            self._validator = ThemeValidator()
        return self._validator

    @property
    def screenshot_generator(self):
        if self._screenshot_generator is None:
            self._screenshot_generator = ScreenshotGenerator(self.config)
        return self._screenshot_generator

    @property
    def icon_generator(self):
        if self._icon_generator is None:
            self._icon_generator = IconGenerator(self.config)
        return self._icon_generator

    def build(self,
              theme_name: Optional[str] = None,
              skip_ai: bool = False,
              skip_screenshots: bool = False,
              skip_package: bool = False,
              output_dir: Optional[Path] = None,
              force: bool = False) -> List[str]:
        """
        Build theme(s) with complete pipeline

        Returns list of successfully built theme names
        """
        logger.info(f"Starting build process...")

        # Override output directory if provided
        if output_dir:
            self.output_dir = output_dir

        # Get themes to build
        themes_to_build = self._get_themes_to_build(theme_name)
        if not themes_to_build:
            logger.warning("No themes found to build")
            return []

        built_themes = []

        # Build each theme
        with tqdm(total=len(themes_to_build), desc="Building themes") as pbar:
            for theme_path in themes_to_build:
                theme_name = theme_path.stem
                pbar.set_description(f"Building {theme_name}")

                try:
                    # Build individual theme
                    success = self._build_theme(
                        theme_path,
                        skip_ai=skip_ai,
                        skip_screenshots=skip_screenshots,
                        skip_package=skip_package,
                        force=force
                    )

                    if success:
                        built_themes.append(theme_name)
                        logger.info(f"Successfully built theme: {theme_name}")
                    else:
                        logger.error(f"Failed to build theme: {theme_name}")

                except Exception as e:
                    logger.error(f"Error building theme {theme_name}: {e}")

                pbar.update(1)

        return built_themes

    def _build_theme(self,
                     theme_path: Path,
                     skip_ai: bool = False,
                     skip_screenshots: bool = False,
                     skip_package: bool = False,
                     force: bool = False) -> bool:
        """Build a single theme"""
        theme_name = theme_path.stem
        logger.info(f"Building theme: {theme_name}")

        try:
            # 1. Load and validate theme definition
            with open(theme_path, 'r') as f:
                theme_def = yaml.safe_load(f)

            if not self.validator.validate(theme_def):
                logger.error(f"Theme validation failed: {theme_name}")
                return False

            # 2. Create output directory structure
            theme_output_dir = self.output_dir / theme_name
            #if theme_output_dir.exists() and not force:
            #    response = input(f"Theme {theme_name} already exists. Overwrite? [y/N]: ")
            #    if response.lower() != 'y':
            #        logger.info(f"Skipping theme: {theme_name}")
            #        return False

            self._create_theme_structure(theme_output_dir)

            # 3. AI Enhancement (if enabled)
            if not skip_ai and self.config.get('ai.enabled', True):
                logger.info(f"Enhancing theme with AI: {theme_name}")
                theme_def = self.ai_enhancer.enhance_theme(theme_def)

            # 4. Generate icon FIRST (if enabled) - BEFORE templating
            if self.config.get('build.generate_icon', True):
                logger.info(f"Generating icon: {theme_name}")
                try:
                    theme_data = theme_def.get('theme', theme_def)
                    icon_path = self.icon_generator.generate_icon(theme_name, theme_data, theme_output_dir)
                    if icon_path:
                        logger.info(f"Generated icon: {icon_path}")
                except Exception as e:
                    logger.warning(f"Failed to generate icon: {e}")
                    logger.info("Continuing without icon")

            # 5. Template files (package.json will now detect the icon)
            logger.info(f"Generating theme files: {theme_name}")
            self.templater.generate_theme_files(theme_def, theme_output_dir)

            # 6. Package as VSIX (needed for screenshots)
            if not skip_package and self.config.get('build.create_vsix', True):
                logger.info(f"Creating VSIX package: {theme_name}")
                vsix_path = self.packager.create_vsix(theme_output_dir)
                logger.info(f"Created VSIX: {vsix_path}")

            # 7. Generate screenshots AFTER packaging (if enabled)
            if not skip_screenshots and self.config.get('build.generate_screenshots', True):
                logger.info(f"Generating screenshots: {theme_name}")
                try:
                    screenshots = self.screenshot_generator.generate_single_screenshot(theme_name, theme_output_dir)

                    # Update README with actual screenshot paths only if we got screenshots
                    if screenshots:
                        self._update_readme_with_screenshots(theme_output_dir, screenshots)
                    else:
                        logger.info("No screenshots generated - VS Code required for screenshots")
                except Exception as e:
                    logger.warning(f"Failed to generate screenshots: {e}")
                    logger.info("Continuing without screenshots")

            self._organize_build_artifacts(theme_name, theme_output_dir)

            return True

        except Exception as e:
            logger.error(f"Failed to build theme {theme_name}: {e}")
            return False

    def _update_readme_with_screenshots(self, theme_dir: Path, screenshots: List[Path]):
        """Update README.md to reference actual screenshots"""
        readme_path = theme_dir / 'README.md'
        if readme_path.exists():
            content = readme_path.read_text()

            # Simple replacement - find the screenshots section and update
            # This is a bit hacky but works for now
            if '![Theme Preview](images/screenshot_python.png)' in content and screenshots:
                # Replace with actual screenshots
                screenshot_md = '\n\n'.join([
                    f"![Theme Preview {i+1}]({str(s.relative_to(theme_dir))})"
                    for i, s in enumerate(screenshots)
                ])
                content = content.replace(
                    '![Theme Preview](images/screenshot_python.png)',
                    screenshot_md
                )
                readme_path.write_text(content)

    def _create_theme_structure(self, theme_dir: Path):
        """Create the VS Code extension directory structure"""
        # Create directories
        (theme_dir / "themes").mkdir(parents=True, exist_ok=True)
        (theme_dir / "images").mkdir(exist_ok=True)

        # Create .vscode directory for launch config
        (theme_dir / ".vscode").mkdir(exist_ok=True)

    def _get_themes_to_build(self, theme_name: Optional[str] = None) -> List[Path]:
        """Get list of theme files to build"""
        if not self.themes_dir.exists():
            logger.error(f"Themes directory not found: {self.themes_dir}")
            return []

        if theme_name:
            # Build specific theme
            theme_path = self.themes_dir / f"{theme_name}.yaml"
            if not theme_path.exists():
                theme_path = self.themes_dir / f"{theme_name}.yml"

            if theme_path.exists():
                return [theme_path]
            else:
                logger.error(f"Theme not found: {theme_name}")
                return []
        else:
            # Build all themes
            yaml_files = list(self.themes_dir.glob("*.yaml"))
            yml_files = list(self.themes_dir.glob("*.yml"))
            return yaml_files + yml_files

    def create_theme(self,
                     name: str,
                     template: str = "default",
                     display_name: Optional[str] = None,
                     description: Optional[str] = None,
                     from_prompt: Optional[str] = None) -> Path:
        """Create a new theme from template"""
        logger.info(f"Creating new theme: {name}")

        # Ensure themes directory exists
        self.themes_dir.mkdir(parents=True, exist_ok=True)

        # If we have a prompt, use AI to generate the theme
        if from_prompt:
            logger.info(f"Generating theme from prompt: {from_prompt}")
            theme_def = self._generate_theme_from_prompt(name, from_prompt, display_name, description)
        else:
            # Create theme definition - note the structure!
            theme_def = {
                'theme': {  # This is the key that was missing!
                    'name': name,
                    'display_name': display_name or name.replace('_', ' ').title(),
                    'description': description or f"A custom VS Code theme",
                    'version': '1.0.0',
                    'author': {
                        'name': 'Your Name',
                        'email': 'your.email@example.com'
                    },
                    'colors': {},
                    'token_colors': []
                }
            }

            # Load template colors based on template type
            if template == "minimal":
                theme_def['theme']['colors'] = self._get_minimal_colors()
            elif template == "full":
                theme_def['theme']['colors'] = self._get_full_colors()
            else:
                theme_def['theme']['colors'] = self._get_default_colors()

            # Add default token colors
            theme_def['theme']['token_colors'] = self._get_default_token_colors()

        # Save theme file
        theme_path = self.themes_dir / f"{name}.yaml"
        with open(theme_path, 'w') as f:
            yaml.dump(theme_def, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created theme template: {theme_path}")
        return theme_path

    def _get_minimal_colors(self) -> Dict[str, str]:
        """Get minimal color set for a theme"""
        return {
            "editor.background": "#1e1e1e",
            "editor.foreground": "#d4d4d4",
            "activityBar.background": "#333333",
            "activityBar.foreground": "#ffffff",
            "sideBar.background": "#252526",
            "sideBar.foreground": "#cccccc",
            "statusBar.background": "#007acc",
            "statusBar.foreground": "#ffffff",
        }

    def _get_default_colors(self) -> Dict[str, str]:
        """Get default color set for a theme"""
        colors = self._get_minimal_colors()
        colors.update({
            "editor.lineHighlightBackground": "#2a2a2a",
            "editor.selectionBackground": "#264f78",
            "editorCursor.foreground": "#ffffff",
            "editorGroupHeader.tabsBackground": "#2d2d30",
            "tab.activeBackground": "#1e1e1e",
            "tab.activeForeground": "#ffffff",
            "tab.inactiveBackground": "#2d2d30",
            "tab.inactiveForeground": "#969696",
            "terminal.background": "#1e1e1e",
            "terminal.foreground": "#cccccc",
        })
        return colors

    def _get_full_colors(self) -> Dict[str, str]:
        """Get full color set for a theme - ALL VS Code color keys"""
        return {
            # Editor colors
            "editor.background": "#1e1e1e",
            "editor.foreground": "#d4d4d4",
            "editorLineNumber.foreground": "#858585",
            "editorLineNumber.activeForeground": "#c6c6c6",
            "editorCursor.foreground": "#aeafad",
            "editorCursor.background": "#000000",
            "editor.selectionBackground": "#264f78",
            "editor.selectionForeground": "#ffffff",
            "editor.inactiveSelectionBackground": "#3a3d41",
            "editor.selectionHighlightBackground": "#add6ff26",
            "editor.wordHighlightBackground": "#575757b8",
            "editor.wordHighlightStrongBackground": "#004972b8",
            "editor.findMatchBackground": "#515c6a",
            "editor.findMatchHighlightBackground": "#ea5c0055",
            "editor.findRangeHighlightBackground": "#3a3d4166",
            "editor.hoverHighlightBackground": "#264f7840",
            "editor.lineHighlightBackground": "#ffffff0A",
            "editor.lineHighlightBorder": "#282828",
            "editorLink.activeForeground": "#4e94ce",
            "editor.rangeHighlightBackground": "#ffffff0b",
            "editorWhitespace.foreground": "#e3e4e229",
            "editorIndentGuide.background": "#404040",
            "editorIndentGuide.activeBackground": "#707070",
            "editorRuler.foreground": "#5a5a5a",
            "editorCodeLens.foreground": "#999999",
            "editorBracketMatch.background": "#0064001a",
            "editorBracketMatch.border": "#888888",

            # Editor widget colors
            "editorWidget.background": "#252526",
            "editorWidget.foreground": "#cccccc",
            "editorWidget.border": "#454545",
            "editorSuggestWidget.background": "#252526",
            "editorSuggestWidget.border": "#454545",
            "editorSuggestWidget.foreground": "#d4d4d4",
            "editorSuggestWidget.highlightForeground": "#0097fb",
            "editorSuggestWidget.selectedBackground": "#062f4a",
            "editorHoverWidget.background": "#252526",
            "editorHoverWidget.border": "#454545",

            # Editor groups and tabs
            "editorGroup.border": "#444444",
            "editorGroupHeader.tabsBackground": "#2d2d30",
            "editorGroupHeader.tabsBorder": "#252526",
            "tab.activeBackground": "#1e1e1e",
            "tab.activeForeground": "#ffffff",
            "tab.border": "#252526",
            "tab.activeBorder": "#1e1e1e",
            "tab.unfocusedActiveBorder": "#1e1e1e",
            "tab.inactiveBackground": "#2d2d30",
            "tab.inactiveForeground": "#969696",
            "tab.unfocusedActiveForeground": "#cccccc",
            "tab.unfocusedInactiveForeground": "#969696",

            # Activity Bar
            "activityBar.background": "#333333",
            "activityBar.foreground": "#ffffff",
            "activityBar.inactiveForeground": "#ffffff66",
            "activityBar.border": "#333333",
            "activityBarBadge.background": "#007acc",
            "activityBarBadge.foreground": "#ffffff",
            "activityBar.activeBorder": "#ffffff",
            "activityBar.activeBackground": "#3c3c3c",

            # Sidebar
            "sideBar.background": "#252526",
            "sideBar.foreground": "#cccccc",
            "sideBar.border": "#333333",
            "sideBarTitle.foreground": "#bbbbbb",
            "sideBarSectionHeader.background": "#00000000",
            "sideBarSectionHeader.foreground": "#cccccc",
            "sideBarSectionHeader.border": "#33333300",

            # Lists and trees
            "list.activeSelectionBackground": "#094771",
            "list.activeSelectionForeground": "#ffffff",
            "list.inactiveSelectionBackground": "#37373d",
            "list.inactiveSelectionForeground": "#cccccc",
            "list.hoverBackground": "#2a2d2e",
            "list.hoverForeground": "#cccccc",
            "list.dropBackground": "#062f4a",
            "list.highlightForeground": "#0097fb",
            "listFilterWidget.background": "#653723",
            "listFilterWidget.outline": "#00000000",
            "listFilterWidget.noMatchesOutline": "#be1100",

            # Status Bar
            "statusBar.background": "#007acc",
            "statusBar.foreground": "#ffffff",
            "statusBar.border": "#007acc",
            "statusBar.debuggingBackground": "#cc6633",
            "statusBar.debuggingForeground": "#ffffff",
            "statusBar.debuggingBorder": "#cc6633",
            "statusBar.noFolderForeground": "#ffffff",
            "statusBar.noFolderBackground": "#68217a",
            "statusBar.noFolderBorder": "#68217a",
            "statusBarItem.hoverBackground": "#ffffff1f",
            "statusBarItem.activeBackground": "#ffffff2e",
            "statusBarItem.prominentBackground": "#00000080",
            "statusBarItem.prominentHoverBackground": "#0000004d",

            # Title Bar
            "titleBar.activeBackground": "#3c3c3c",
            "titleBar.activeForeground": "#cccccc",
            "titleBar.inactiveBackground": "#3c3c3c99",
            "titleBar.inactiveForeground": "#cccccc99",
            "titleBar.border": "#00000000",

            # Menus
            "menu.background": "#252526",
            "menu.foreground": "#cccccc",
            "menu.selectionBackground": "#094771",
            "menu.selectionForeground": "#ffffff",
            "menu.selectionBorder": "#00000000",
            "menu.separatorBackground": "#bbbbbb",
            "menu.border": "#00000085",
            "menubar.selectionBackground": "#ffffff1a",
            "menubar.selectionForeground": "#cccccc",
            "menubar.selectionBorder": "#00000000",

            # Buttons
            "button.background": "#0e639c",
            "button.foreground": "#ffffff",
            "button.hoverBackground": "#1177bb",
            "button.secondaryBackground": "#3a3a3a",
            "button.secondaryForeground": "#ffffff",
            "button.secondaryHoverBackground": "#45494e",

            # Inputs
            "input.background": "#3c3c3c",
            "input.border": "#00000000",
            "input.foreground": "#cccccc",
            "input.placeholderForeground": "#a6a6a6",
            "inputOption.activeBackground": "#007acc",
            "inputOption.activeBorder": "#007acc",
            "inputOption.activeForeground": "#ffffff",
            "inputValidation.errorBackground": "#5a1d1d",
            "inputValidation.errorBorder": "#be1100",
            "inputValidation.errorForeground": "#ffffff",
            "inputValidation.infoBackground": "#063b49",
            "inputValidation.infoBorder": "#007acc",
            "inputValidation.infoForeground": "#ffffff",
            "inputValidation.warningBackground": "#352a05",
            "inputValidation.warningBorder": "#b89500",
            "inputValidation.warningForeground": "#ffffff",

            # Scrollbar
            "scrollbar.shadow": "#000000",
            "scrollbarSlider.activeBackground": "#bfbfbf66",
            "scrollbarSlider.background": "#79797966",
            "scrollbarSlider.hoverBackground": "#646464b3",

            # Badge
            "badge.background": "#4d4d4d",
            "badge.foreground": "#ffffff",

            # Progress bar
            "progressBar.background": "#0e70c0",

            # Panel
            "panel.background": "#1e1e1e",
            "panel.border": "#80808059",
            "panel.dropBackground": "#164c7e",
            "panelTitle.activeBorder": "#007acc",
            "panelTitle.activeForeground": "#e7e7e7",
            "panelTitle.inactiveForeground": "#e7e7e799",

            # Terminal
            "terminal.background": "#1e1e1e",
            "terminal.foreground": "#cccccc",
            "terminal.ansiBlack": "#000000",
            "terminal.ansiRed": "#cd3131",
            "terminal.ansiGreen": "#0dbc79",
            "terminal.ansiYellow": "#e5e510",
            "terminal.ansiBlue": "#2472c8",
            "terminal.ansiMagenta": "#bc3fbc",
            "terminal.ansiCyan": "#11a8cd",
            "terminal.ansiWhite": "#e5e5e5",
            "terminal.ansiBrightBlack": "#666666",
            "terminal.ansiBrightRed": "#f14c4c",
            "terminal.ansiBrightGreen": "#23d18b",
            "terminal.ansiBrightYellow": "#f5f543",
            "terminal.ansiBrightBlue": "#3b8eea",
            "terminal.ansiBrightMagenta": "#d670d6",
            "terminal.ansiBrightCyan": "#29b8db",
            "terminal.ansiBrightWhite": "#e5e5e5",
            "terminal.selectionBackground": "#ffffff40",
            "terminalCursor.background": "#000000",
            "terminalCursor.foreground": "#ffffff",

            # Git decorations
            "gitDecoration.addedResourceForeground": "#81b88b",
            "gitDecoration.modifiedResourceForeground": "#e2c08d",
            "gitDecoration.deletedResourceForeground": "#c74e39",
            "gitDecoration.untrackedResourceForeground": "#73c991",
            "gitDecoration.ignoredResourceForeground": "#8c8c8c",
            "gitDecoration.conflictingResourceForeground": "#6c6cc4",
            "gitDecoration.submoduleResourceForeground": "#8db9e2",

            # Peek view
            "peekView.border": "#007acc",
            "peekViewEditor.background": "#001f33",
            "peekViewEditor.matchHighlightBackground": "#ff8f0099",
            "peekViewEditor.matchHighlightBorder": "#ee931e",
            "peekViewResult.background": "#252526",
            "peekViewResult.fileForeground": "#ffffff",
            "peekViewResult.lineForeground": "#bbbbbb",
            "peekViewResult.matchHighlightBackground": "#ea5c004d",
            "peekViewResult.selectionBackground": "#3399ff33",
            "peekViewResult.selectionForeground": "#ffffff",
            "peekViewTitle.background": "#1e1e1e",
            "peekViewTitleDescription.foreground": "#ccccccb3",
            "peekViewTitleLabel.foreground": "#ffffff",

            # Merge conflicts
            "merge.currentHeaderBackground": "#367366",
            "merge.currentContentBackground": "#27403B",
            "merge.incomingHeaderBackground": "#395F8F",
            "merge.incomingContentBackground": "#28384B",
            "merge.border": "#c3c3c3",
            "merge.commonHeaderBackground": "#383838",
            "merge.commonContentBackground": "#282828",

            # Notifications
            "notificationCenter.border": "#474747",
            "notificationCenterHeader.foreground": "#cccccc",
            "notificationCenterHeader.background": "#303031",
            "notificationToast.border": "#474747",
            "notifications.foreground": "#cccccc",
            "notifications.background": "#252526",
            "notifications.border": "#303031",
            "notificationLink.foreground": "#3794ff",

            # Extensions
            "extensionButton.prominentForeground": "#ffffff",
            "extensionButton.prominentBackground": "#327e36",
            "extensionButton.prominentHoverBackground": "#28632b",

            # Breadcrumbs
            "breadcrumb.foreground": "#cccccccc",
            "breadcrumb.background": "#1e1e1e",
            "breadcrumb.focusForeground": "#e0e0e0",
            "breadcrumb.activeSelectionForeground": "#e0e0e0",
            "breadcrumbPicker.background": "#252526",

            # Errors and warnings
            "editorError.foreground": "#f48771",
            "editorError.border": "#f4877100",
            "editorWarning.foreground": "#cca700",
            "editorWarning.border": "#cca70000",
            "editorInfo.foreground": "#75beff",
            "editorInfo.border": "#75beff00",
            "editorHint.foreground": "#eeeeeeb3",
            "editorGutter.background": "#1e1e1e",
            "editorGutter.modifiedBackground": "#0c7d9d",
            "editorGutter.addedBackground": "#587c0c",
            "editorGutter.deletedBackground": "#94151b",
        }

    def _get_default_token_colors(self) -> List[Dict[str, Any]]:
        """Get default token colors for syntax highlighting"""
        return [
            {
                "name": "Comment",
                "scope": ["comment", "punctuation.definition.comment"],
                "settings": {
                    "fontStyle": "italic",
                    "foreground": "#6A9955"
                }
            },
            {
                "name": "String",
                "scope": ["string"],
                "settings": {
                    "foreground": "#ce9178"
                }
            },
            {
                "name": "Keyword",
                "scope": ["keyword", "storage.type", "storage.modifier"],
                "settings": {
                    "foreground": "#569cd6"
                }
            },
            {
                "name": "Function",
                "scope": ["entity.name.function"],
                "settings": {
                    "foreground": "#dcdcaa"
                }
            },
            {
                "name": "Variable",
                "scope": ["variable"],
                "settings": {
                    "foreground": "#9cdcfe"
                }
            },
            {
                "name": "Number",
                "scope": ["constant.numeric"],
                "settings": {
                    "foreground": "#b5cea8"
                }
            }
        ]

    def list_themes(self, detailed: bool = False) -> List[Dict[str, Any]]:
        """List available themes"""
        themes = []

        for theme_path in self._get_themes_to_build():
            try:
                with open(theme_path, 'r') as f:
                    theme_def = yaml.safe_load(f)

                theme_info = {
                    'name': theme_path.stem,
                    'path': str(theme_path)
                }

                if detailed and 'theme' in theme_def:
                    theme_info.update({
                        'display_name': theme_def['theme'].get('display_name', ''),
                        'description': theme_def['theme'].get('description', ''),
                        'version': theme_def['theme'].get('version', ''),
                        'author': theme_def['theme'].get('author', {}).get('name', ''),
                    })

                themes.append(theme_info)

            except Exception as e:
                logger.error(f"Error reading theme {theme_path}: {e}")

        return themes

    def _generate_theme_from_prompt(self, name: str, prompt: str, display_name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Generate a complete theme from an AI prompt"""
        from wl_ai_manager import AIManager

        # Get AI manager config
        ai_manager_config = self.config.get('ai_manager', {})
        if not ai_manager_config:
            raise ValueError("AI Manager configuration not found. Please set up config.yaml with ai_manager section.")

        ai_manager = AIManager(ai_manager_config)

        # Create the prompt file for theme generation
        prompts_dir = Path(ai_manager_config.get('prompt_folder', './prompts'))
        prompts_dir.mkdir(exist_ok=True)

        # Write the prompt template file
        prompt_file = prompts_dir / 'generate_theme_colors.user.txt'
        prompt_content = """Based on this theme description: "{theme_description}"

Generate a color palette with these exact colors (as hex values):

1. primary_bg - main background color
2. primary_fg - main text color
3. secondary_bg - sidebar/panel background
4. secondary_fg - sidebar/panel text
5. accent1 - primary accent color (buttons, badges)
6. accent2 - secondary accent color (selections, highlights)
7. accent3 - tertiary accent color (links, info)
8. error - error/danger color
9. warning - warning color
10. success - success/added color
11. comment - comment color
12. string - string color
13. keyword - keyword color
14. function - function name color
15. variable - variable color
16. number - number color
17. type - type/class color
18. terminal_bg - terminal background
19. terminal_fg - terminal foreground
20. cursor - cursor color

Return ONLY a Python list of tuples like this:
[
    ("primary_bg", "#000000"),
    ("primary_fg", "#ffffff"),
    ... etc
]

Make sure all colors fit the theme: {theme_description}"""

        # Write the prompt file if it doesn't exist
        if not prompt_file.exists():
            prompt_file.write_text(prompt_content)
            logger.info(f"Created prompt file: {prompt_file}")

        # Data to template the prompt
        prompt_data = {
            'theme_description': prompt
        }

        try:
            print(prompt_data)
            # Call AI Manager with prompt file name and data
            response = ai_manager.chat('generate_theme_colors', prompt_data)

            if not response:
                raise ValueError("No response from AI")

            logger.info(f"AI Response: {response[:200]}...")

            # Parse the color tuples
            colors_dict = self._parse_color_tuples(response)

            if not colors_dict:
                raise ValueError("Could not parse colors from AI response")

            defaults = self.config.get('defaults', {})

            # Now use the FULL template and map our colors
            theme_def = {
                'theme': {
                    'name': name,
                    'display_name': display_name or self._generate_display_name(prompt),
                    'description': description or f"Theme inspired by: {prompt}"[:200],
                    'version': defaults.get('version', '1.0.0'),
                    'author': defaults.get('author', {
                        'name': 'Your Name',
                        'email': 'your.email@example.com'
                    }),
                    'repository': defaults.get('repository', ''),
                    'license': defaults.get('license', 'MIT'),
                    'publisher': defaults.get('publisher', 'unknown'),
                    'keywords': defaults.get('keywords', ['theme', 'color-theme']),
                    'colors': self._map_ai_colors_to_full_theme(colors_dict),
                    'token_colors': self._map_ai_colors_to_token_colors(colors_dict)
                }
            }
            return theme_def

        except Exception as e:
            logger.error(f"Failed to generate theme from prompt: {e}")
            defaults = self.config.get('defaults', {})
            # Fallback to a basic theme
            print(colored("\n⚠ AI generation failed, creating basic theme instead", "yellow"))
            return {
                'theme': {
                    'name': name,
                    'display_name': display_name or name.replace('_', ' ').title(),
                    'description': description or f"Theme inspired by: {prompt}",
                    'version': defaults.get('version', '1.0.0'),
                    'author': defaults.get('author', {
                        'name': 'Your Name',
                        'email': 'your.email@example.com'
                    }),
                    'repository': defaults.get('repository', ''),
                    'license': defaults.get('license', 'MIT'),
                    'publisher': defaults.get('publisher', 'unknown'),
                    'keywords': defaults.get('keywords', ['theme', 'color-theme']),
                    'colors': self._get_full_colors(),
                    'token_colors': self._get_default_token_colors()
                }
            }

    def _parse_color_tuples(self, response: str) -> Dict[str, str]:
        """Parse color tuples from AI response"""
        import re

        colors = {}

        # Try to find tuple patterns
        # Match patterns like ("name", "#hex") or ('name', '#hex')
        pattern = r'\(\s*["\'](\w+)["\']\s*,\s*["\']#?([0-9A-Fa-f]{6})["\']'
        matches = re.findall(pattern, response)

        for name, hex_value in matches:
            colors[name] = f"#{hex_value}"

        # If we didn't find enough colors, try simpler patterns
        if len(colors) < 10:
            # Try to find hex colors with labels
            pattern2 = r'(\w+)\s*[-:=]\s*#?([0-9A-Fa-f]{6})'
            matches2 = re.findall(pattern2, response)
            for name, hex_value in matches2:
                colors[name] = f"#{hex_value}"

        logger.info(f"Parsed {len(colors)} colors from AI response")
        return colors

    def _generate_display_name(self, prompt: str) -> str:
        """Generate a display name from the prompt"""
        # Simple heuristic - take first few words and title case
        words = prompt.split()[:3]
        return ' '.join(words).title() + " Theme"

    def _map_ai_colors_to_full_theme(self, ai_colors: Dict[str, str]) -> Dict[str, str]:
        """Map AI colors to full VS Code theme colors"""
        # Start with a full color template
        full_colors = self._get_full_colors()

        # Map AI colors to theme colors
        color_mappings = {
            # Editor
            'editor.background': ai_colors.get('primary_bg', '#1e1e1e'),
            'editor.foreground': ai_colors.get('primary_fg', '#d4d4d4'),
            'editorCursor.foreground': ai_colors.get('cursor', ai_colors.get('accent1', '#ffffff')),
            'editor.lineHighlightBackground': ai_colors.get('secondary_bg', '#2a2a2a') + '40',  # 40 = 25% opacity
            'editor.selectionBackground': ai_colors.get('accent2', '#264f78') + '80',  # 80 = 50% opacity

            # Activity Bar
            'activityBar.background': ai_colors.get('primary_bg', '#333333'),
            'activityBar.foreground': ai_colors.get('accent1', '#ffffff'),
            'activityBar.inactiveForeground': ai_colors.get('secondary_fg', '#ffffff') + '99',  # 60% opacity
            'activityBarBadge.background': ai_colors.get('accent1', '#007acc'),
            'activityBarBadge.foreground': ai_colors.get('primary_bg', '#ffffff'),

            # Side Bar
            'sideBar.background': ai_colors.get('secondary_bg', '#252526'),
            'sideBar.foreground': ai_colors.get('secondary_fg', '#cccccc'),
            'sideBarTitle.foreground': ai_colors.get('accent1', '#ffffff'),

            # Status Bar
            'statusBar.background': ai_colors.get('accent1', '#007acc'),
            'statusBar.foreground': ai_colors.get('primary_bg', '#ffffff'),
            'statusBar.debuggingBackground': ai_colors.get('warning', '#ff9900'),
            'statusBar.debuggingForeground': ai_colors.get('primary_bg', '#ffffff'),

            # Terminal
            'terminal.background': ai_colors.get('terminal_bg', ai_colors.get('primary_bg', '#1e1e1e')),
            'terminal.foreground': ai_colors.get('terminal_fg', ai_colors.get('primary_fg', '#cccccc')),
            'terminalCursor.foreground': ai_colors.get('cursor', ai_colors.get('accent1', '#ffffff')),

            # Buttons
            'button.background': ai_colors.get('accent1', '#0e639c'),
            'button.foreground': ai_colors.get('primary_bg', '#ffffff'),
            'button.hoverBackground': ai_colors.get('accent2', '#1177bb'),

            # Input
            'input.background': ai_colors.get('secondary_bg', '#3c3c3c'),
            'input.foreground': ai_colors.get('primary_fg', '#cccccc'),
            'input.border': ai_colors.get('accent2', '#007acc') + '80',

            # Lists
            'list.activeSelectionBackground': ai_colors.get('accent2', '#094771'),
            'list.activeSelectionForeground': ai_colors.get('primary_fg', '#ffffff'),
            'list.hoverBackground': ai_colors.get('secondary_bg', '#2a2a2a') + '80',

            # Errors, warnings, info
            'editorError.foreground': ai_colors.get('error', '#ff0000'),
            'editorWarning.foreground': ai_colors.get('warning', '#ffaa00'),
            'editorInfo.foreground': ai_colors.get('accent3', '#00aaff'),

            # Git colors
            'gitDecoration.addedResourceForeground': ai_colors.get('success', '#00ff00'),
            'gitDecoration.modifiedResourceForeground': ai_colors.get('warning', '#ffaa00'),
            'gitDecoration.deletedResourceForeground': ai_colors.get('error', '#ff0000'),
        }

        # Update full colors with our mappings
        full_colors.update(color_mappings)

        # Add more colors based on the base colors
        # Terminal ANSI colors
        full_colors.update({
            'terminal.ansiBlack': '#000000',
            'terminal.ansiRed': ai_colors.get('error', '#ff0000'),
            'terminal.ansiGreen': ai_colors.get('success', '#00ff00'),
            'terminal.ansiYellow': ai_colors.get('warning', '#ffff00'),
            'terminal.ansiBlue': ai_colors.get('accent3', '#0000ff'),
            'terminal.ansiMagenta': ai_colors.get('accent2', '#ff00ff'),
            'terminal.ansiCyan': ai_colors.get('accent3', '#00ffff'),
            'terminal.ansiWhite': ai_colors.get('primary_fg', '#ffffff'),
            'terminal.ansiBrightBlack': '#666666',
            'terminal.ansiBrightRed': ai_colors.get('error', '#ff6666'),
            'terminal.ansiBrightGreen': ai_colors.get('success', '#66ff66'),
            'terminal.ansiBrightYellow': ai_colors.get('warning', '#ffff66'),
            'terminal.ansiBrightBlue': ai_colors.get('accent3', '#6666ff'),
            'terminal.ansiBrightMagenta': ai_colors.get('accent2', '#ff66ff'),
            'terminal.ansiBrightCyan': ai_colors.get('accent3', '#66ffff'),
            'terminal.ansiBrightWhite': '#ffffff',
        })

        return full_colors

    def _map_ai_colors_to_token_colors(self, ai_colors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Map AI colors to token colors for syntax highlighting"""
        return [
            {
                "name": "Comment",
                "scope": ["comment", "punctuation.definition.comment"],
                "settings": {
                    "foreground": ai_colors.get('comment', '#6A9955'),
                    "fontStyle": "italic"
                }
            },
            {
                "name": "String",
                "scope": ["string", "string.quoted"],
                "settings": {
                    "foreground": ai_colors.get('string', '#ce9178')
                }
            },
            {
                "name": "Number",
                "scope": ["constant.numeric"],
                "settings": {
                    "foreground": ai_colors.get('number', '#b5cea8')
                }
            },
            {
                "name": "Keyword",
                "scope": ["keyword", "keyword.control", "storage.type", "storage.modifier"],
                "settings": {
                    "foreground": ai_colors.get('keyword', '#569cd6'),
                    "fontStyle": "bold"
                }
            },
            {
                "name": "Function",
                "scope": ["entity.name.function", "support.function"],
                "settings": {
                    "foreground": ai_colors.get('function', '#dcdcaa')
                }
            },
            {
                "name": "Variable",
                "scope": ["variable", "variable.other"],
                "settings": {
                    "foreground": ai_colors.get('variable', '#9cdcfe')
                }
            },
            {
                "name": "Type",
                "scope": ["entity.name.type", "entity.name.class", "support.type", "support.class"],
                "settings": {
                    "foreground": ai_colors.get('type', '#4ec9b0')
                }
            },
            {
                "name": "Constant",
                "scope": ["constant", "constant.language", "support.constant"],
                "settings": {
                    "foreground": ai_colors.get('keyword', '#569cd6')
                }
            },
            {
                "name": "Tag",
                "scope": ["entity.name.tag", "meta.tag"],
                "settings": {
                    "foreground": ai_colors.get('keyword', '#569cd6')
                }
            },
            {
                "name": "Attribute",
                "scope": ["entity.other.attribute-name"],
                "settings": {
                    "foreground": ai_colors.get('variable', '#9cdcfe')
                }
            },
            {
                "name": "Invalid",
                "scope": ["invalid", "invalid.illegal"],
                "settings": {
                    "foreground": ai_colors.get('error', '#f44747')
                }
            }
        ]

    def validate_themes(self, theme_name: Optional[str] = None, fix: bool = False) -> List[Dict[str, Any]]:
        """Validate theme configurations"""
        themes_to_validate = self._get_themes_to_build(theme_name)
        results = []

        for theme_path in themes_to_validate:
            try:
                with open(theme_path, 'r') as f:
                    theme_def = yaml.safe_load(f)

                is_valid, errors = self.validator.validate_with_errors(theme_def)

                result = {
                    'name': theme_path.stem,
                    'valid': is_valid,
                    'errors': errors
                }

                if fix and not is_valid:
                    fixed_theme = self.validator.fix_theme(theme_def)
                    with open(theme_path, 'w') as f:
                        yaml.dump(fixed_theme, f, default_flow_style=False, sort_keys=False)
                    result['fixed'] = True

                results.append(result)

            except Exception as e:
                results.append({
                    'name': theme_path.stem,
                    'valid': False,
                    'errors': [str(e)]
                })

        return results

    def clean(self, all_files: bool = False, build_only: bool = False, screenshots_only: bool = False):
        """Clean build artifacts"""
        if all_files:
            # Clean everything
            dirs_to_clean = [
                self.output_dir,
                self.temp_dir,
                Path('./screenshots'),
                Path(self.config.get('generator.assets_dir', './assets/builds')),
                Path(self.config.get('generator.releases_dir', './releases'))
            ]
        elif build_only:
            dirs_to_clean = [self.output_dir]
        elif screenshots_only:
            dirs_to_clean = [Path('./screenshots')]
        else:
            # Default: clean build and temp
            dirs_to_clean = [self.output_dir, self.temp_dir]

        for dir_path in dirs_to_clean:
            if dir_path.exists():
                logger.info(f"Removing directory: {dir_path}")
                shutil.rmtree(dir_path)

    def package_theme(self, theme_name: str, output_path: Optional[Path] = None) -> Path:
        """Package an existing theme directory into VSIX"""
        theme_dir = self.output_dir / theme_name

        if not theme_dir.exists():
            raise ValueError(f"Theme directory not found: {theme_dir}")

        return self.packager.create_vsix(theme_dir, output_path)

    def generate_screenshot(self, theme_name: str, code_file: Optional[Path] = None, language: str = "python") -> Path:
        """Generate screenshot for a theme"""
        theme_dir = self.output_dir / theme_name

        if not theme_dir.exists():
            raise ValueError(f"Theme not built yet: {theme_name}")

        return self.screenshot_generator.generate_single_screenshot(
            theme_name,
            theme_dir,
            code_file=code_file,
            language=language
        )
    
    
    def _organize_build_artifacts(self, theme_name: str, theme_dir: Path) -> None:
        """Organize build artifacts into proper locations after build"""
        logger.info(f"Organizing build artifacts for {theme_name}")
        
        # Create releases directory if it doesn't exist
        releases_dir = Path(self.config.get('generator.releases_dir', './releases'))
        releases_dir.mkdir(parents=True, exist_ok=True)
        
        # Create assets/builds directory if needed
        assets_builds_dir = Path(self.config.get('generator.assets_dir', './assets/builds'))
        assets_builds_dir.mkdir(parents=True, exist_ok=True)
        
        # Get base URL for assets if configured
        assets_base_url = self.config.get('generator.assets_base_url', '')
        
        # 1. Copy VSIX file to releases directory with version
        vsix_files = list(theme_dir.glob("*.vsix"))
        version = None
        
        # Get version from package.json
        package_json_path = theme_dir / 'package.json'
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    version = package_data.get('version', '1.0.0')
            except Exception as e:
                logger.error(f"Failed to read version from package.json: {e}")
                version = '1.0.0'
        
        if vsix_files:
            vsix_source = vsix_files[0]
            # Include version in filename: theme_name-version.vsix
            vsix_dest = releases_dir / f"{theme_name}-{version}.vsix"
            
            shutil.copy2(vsix_source, vsix_dest)
            logger.info(f"✓ Copied VSIX: {vsix_source.name} → {vsix_dest}")
            
            # Also create a symlink to latest version for convenience
            latest_link = releases_dir / f"{theme_name}-latest.vsix"
            if latest_link.exists():
                latest_link.unlink()
            try:
                latest_link.symlink_to(vsix_dest.name)
                logger.info(f"✓ Created latest symlink: {latest_link.name} → {vsix_dest.name}")
            except Exception as e:
                # Symlinks might not work on Windows without admin
                logger.warning(f"Could not create symlink: {e}")
        else:
            logger.warning(f"No VSIX file found for {theme_name}")
        
        # 2. Copy icon to assets/builds/{theme_name}_icon.png
        icon_source = theme_dir / 'images' / 'icon.png'
        icon_updated = False
        if icon_source.exists():
            icon_dest = assets_builds_dir / f"{theme_name}_icon.png"
            shutil.copy2(icon_source, icon_dest)
            logger.info(f"✓ Copied icon: icon.png → {icon_dest}")
            icon_updated = True
        
        # 3. Copy main screenshot to assets/builds/{theme_name}.png
        screenshots_copied = 0
        images_dir = theme_dir / 'images'
        if images_dir.exists():
            # First, look for the main screenshot (screenshot.png or screenshot1.png)
            main_screenshot = None
            if (images_dir / 'screenshot.png').exists():
                main_screenshot = images_dir / 'screenshot.png'
            elif (images_dir / 'screenshot1.png').exists():
                main_screenshot = images_dir / 'screenshot1.png'
            
            if main_screenshot:
                main_dest = assets_builds_dir / f"{theme_name}.png"
                shutil.copy2(main_screenshot, main_dest)
                screenshots_copied += 1
                logger.info(f"✓ Copied main screenshot: {main_screenshot.name} → {main_dest}")
            
            # Copy any additional numbered screenshots
            for screenshot in images_dir.glob('screenshot[2-9].png'):
                num = screenshot.stem.replace('screenshot', '')
                screenshot_dest = assets_builds_dir / f"{theme_name}_screenshot{num}.png"
                shutil.copy2(screenshot, screenshot_dest)
                screenshots_copied += 1
                logger.info(f"✓ Copied screenshot: {screenshot.name} → {screenshot_dest}")
        
        if screenshots_copied == 0:
            logger.warning(f"No screenshots found for {theme_name}")
        
        # 4. Update package.json with new icon path if we have a base URL
        if icon_updated and assets_base_url:
            package_json_path = theme_dir / 'package.json'
            if package_json_path.exists():
                try:
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                    
                    # Update icon path to use the assets URL
                    package_data['icon'] = f"{assets_base_url}/{theme_name}_icon.png"
                    
                    # Write back the updated package.json
                    with open(package_json_path, 'w') as f:
                        json.dump(package_data, f, indent=2)
                    
                    logger.info(f"✓ Updated package.json icon URL: {package_data['icon']}")
                    
                    # If VSIX was already created, we need to recreate it with updated package.json
                    if vsix_files:
                        logger.info("Recreating VSIX with updated package.json...")
                        try:
                            # Delete old VSIX
                            vsix_files[0].unlink()
                            # Recreate VSIX
                            new_vsix = self.packager.create_vsix(theme_dir)
                            # Copy to releases again with version
                            shutil.copy2(new_vsix, releases_dir / f"{theme_name}-{version}.vsix")
                            logger.info(f"✓ Recreated VSIX with updated icon URL")
                        except Exception as e:
                            logger.error(f"Failed to recreate VSIX: {e}")
                    
                except Exception as e:
                    logger.error(f"Failed to update package.json: {e}")
        
        # 5. Create a manifest file for tracking
        manifest = {
            'theme_name': theme_name,
            'version': version,
            'build_date': datetime.now().isoformat(),
            'artifacts': {
                'vsix': str(releases_dir / f"{theme_name}-{version}.vsix") if vsix_files else None,
                'vsix_latest': str(releases_dir / f"{theme_name}-latest.vsix") if vsix_files else None,
                'icon': str(assets_builds_dir / f"{theme_name}_icon.png") if icon_updated else None,
                'main_screenshot': str(assets_builds_dir / f"{theme_name}.png") if screenshots_copied > 0 else None,
                'additional_screenshots': []
            },
            'urls': {
                'icon': f"{assets_base_url}/{theme_name}_icon.png" if assets_base_url and icon_updated else None,
                'screenshot': f"{assets_base_url}/{theme_name}.png" if assets_base_url and screenshots_copied > 0 else None
            }
        }
        
        # Add additional screenshot paths to manifest
        for i in range(2, 10):
            screenshot_path = assets_builds_dir / f"{theme_name}_screenshot{i}.png"
            if screenshot_path.exists():
                manifest['artifacts']['additional_screenshots'].append(str(screenshot_path))
        
        # Save manifest
        manifest_path = theme_dir / 'build_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"✓ Created build manifest: {manifest_path}")
        
        # Summary
        logger.info(f"\n=== Build Artifacts Summary for {theme_name} v{version} ===")
        logger.info(f"VSIX: {releases_dir / f'{theme_name}-{version}.vsix' if vsix_files else 'None'}")
        logger.info(f"Latest: {releases_dir / f'{theme_name}-latest.vsix' if vsix_files else 'None'}")
        logger.info(f"Icon: {assets_builds_dir / f'{theme_name}_icon.png' if icon_updated else 'None'}")
        logger.info(f"Main Screenshot: {assets_builds_dir / f'{theme_name}.png' if screenshots_copied > 0 else 'None'}")
        logger.info(f"Total Screenshots: {screenshots_copied}")
        if assets_base_url:
            logger.info(f"Icon URL: {assets_base_url}/{theme_name}_icon.png")
            logger.info(f"Screenshot URL: {assets_base_url}/{theme_name}.png")
        logger.info("=" * 50)
    
    def rebuild_package_json(self, theme_name: str, output_dir: Optional[Path] = None, rebuild_readme: bool = True) -> bool:
        """
        Rebuild package.json and optionally README.md for an existing theme
        
        Args:
            theme_name: Name of the theme
            output_dir: Output directory (defaults to self.output_dir / theme_name)
            rebuild_readme: Also rebuild README.md file
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Rebuilding package.json{' and README.md' if rebuild_readme else ''} for theme: {theme_name}")
        
        try:
            # Find theme file
            theme_path = self.themes_dir / f"{theme_name}.yaml"
            if not theme_path.exists():
                theme_path = self.themes_dir / f"{theme_name}.yml"
            
            if not theme_path.exists():
                logger.error(f"Theme definition not found: {theme_name}")
                return False
            
            # Load theme definition
            with open(theme_path, 'r') as f:
                theme_def = yaml.safe_load(f)
            
            # Determine output directory
            theme_output_dir = output_dir or (self.output_dir / theme_name)
            
            if not theme_output_dir.exists():
                logger.error(f"Theme output directory not found: {theme_output_dir}")
                return False
            
            # Check if icon exists (important for package.json generation)
            icon_path = theme_output_dir / 'images' / 'icon.png'
            if icon_path.exists():
                logger.info(f"Found existing icon at: {icon_path}")
            else:
                logger.info("No icon found")
            
            # Extract theme data
            theme_data = theme_def.get('theme', theme_def)
            
            # Apply any AI enhancements if they were previously applied
            # (This reads from the existing theme.json to preserve any AI-enhanced descriptions)
            theme_json_path = theme_output_dir / 'themes' / f"{theme_name}-color-theme.json"
            if theme_json_path.exists():
                try:
                    with open(theme_json_path, 'r') as f:
                        existing_theme = json.load(f)
                    
                    # Preserve the enhanced description if it exists
                    if 'name' in existing_theme and existing_theme['name'] != theme_data.get('display_name'):
                        logger.info("Preserving AI-enhanced display name from theme.json")
                        theme_data['display_name'] = existing_theme['name']
                except Exception as e:
                    logger.warning(f"Could not read existing theme.json: {e}")
            
            # Regenerate package.json
            self.templater._generate_package_json(theme_data, theme_output_dir)
            logger.info(f"Successfully rebuilt package.json for {theme_name}")
            
            # Regenerate README.md if requested
            if rebuild_readme:
                logger.info("Regenerating README.md...")
                self.templater._generate_readme(theme_data, theme_output_dir)
                logger.info(f"Successfully rebuilt README.md for {theme_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rebuild package.json: {e}")
            return False
    
    def rebuild_all_package_json(self, force: bool = False, rebuild_readme: bool = True) -> Dict[str, bool]:
        """
        Rebuild package.json and optionally README.md for all themes
        
        Args:
            force: Rebuild even if files haven't changed
            rebuild_readme: Also rebuild README.md files
            
        Returns:
            Dictionary of theme_name: success status
        """
        results = {}
        
        # Get all built themes
        if not self.output_dir.exists():
            logger.warning("Output directory doesn't exist")
            return results
        
        for theme_dir in self.output_dir.iterdir():
            if theme_dir.is_dir() and (theme_dir / 'package.json').exists():
                theme_name = theme_dir.name
                logger.info(f"Rebuilding files for: {theme_name}")
                
                success = self.rebuild_package_json(theme_name, rebuild_readme=rebuild_readme)
                results[theme_name] = success
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        files_rebuilt = "package.json" + (" and README.md" if rebuild_readme else "")
        logger.info(f"Rebuilt {files_rebuilt} files: {successful} successful, {failed} failed")
        
        return results