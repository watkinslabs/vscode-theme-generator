#!/usr/bin/env python3
"""
VS Code Theme Generator CLI
"""

import argparse
import sys
import logging
import yaml
from pathlib import Path
from termcolor import colored
from tqdm import tqdm

from wl_config_manager import ConfigManager
from .builder import ThemeBuilder
from .constants import VERSION
from .utils import setup_logging, print_banner

def create_parser():
    """Create the argument parser"""
    parser = argparse.ArgumentParser(
        description='VS Code Theme Generator with AI Enhancement',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s build                    # Build all themes
  %(prog)s build tron               # Build specific theme
  %(prog)s build --no-ai            # Build without AI enhancement
  %(prog)s create my-theme          # Create new theme from template
  %(prog)s quickstart my-theme "A cool dark theme"  # Create and build immediately without AI
  %(prog)s list                     # List available themes
  %(prog)s validate tron            # Validate theme configuration
  %(prog)s icon tron                # Generate icon for theme
  %(prog)s clean                    # Clean build artifacts
        """
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version=f'%(prog)s {VERSION}'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('config.yaml'),
        help='Configuration file path (default: config.yaml)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Build command
    build_parser = subparsers.add_parser(
        'build', 
        help='Build theme(s)',
        description='Build one or more VS Code themes'
    )
    build_parser.add_argument(
        'theme',
        nargs='?',
        help='Theme name to build (builds all if not specified)'
    )
    build_parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Skip AI enhancement phase'
    )
    build_parser.add_argument(
        '--no-screenshots',
        action='store_true',
        help='Skip screenshot generation'
    )
    build_parser.add_argument(
        '--no-package',
        action='store_true',
        help='Skip VSIX package creation'
    )
    build_parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output directory (overrides config)'
    )
    build_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Overwrite existing files without prompting'
    )
    
    # Create command
    create_parser = subparsers.add_parser(
        'create', 
        help='Create new theme template',
        description='Create a new theme from a template'
    )
    create_parser.add_argument(
        'name',
        help='Theme name (use snake_case)'
    )
    create_parser.add_argument(
        '--template', '-t',
        default='default',
        choices=['default', 'minimal', 'full'],
        help='Template to use (default: default)'
    )
    create_parser.add_argument(
        '--display-name',
        help='Display name for the theme'
    )
    create_parser.add_argument(
        '--description',
        help='Theme description'
    )
    create_parser.add_argument(
        '--from-prompt', '-p',
        help='Generate theme from AI prompt (e.g., "dark theme with neon cyberpunk colors")'
    )
    
    # Quickstart command - NEW!
    quickstart_parser = subparsers.add_parser(
        'quickstart',
        help='Create and build theme quickly without AI',
        description='Create a new theme and immediately build it without AI enhancement'
    )
    quickstart_parser.add_argument(
        '--display-name',
        help='Display name for the theme'
    )
    quickstart_parser.add_argument(
        'name',
        help='Theme name (use snake_case)'
    )
    quickstart_parser.add_argument(
        'description',
        help='Theme description'
    )
    quickstart_parser.add_argument(
        '--template', '-t',
        default='default',
        choices=['default', 'minimal', 'full'],
        help='Template to use (default: default)'
    )
    quickstart_parser.add_argument(
        '--no-screenshots',
        action='store_true',
        help='Skip screenshot generation'
    )
    quickstart_parser.add_argument(
        '--no-icon',
        action='store_true',
        help='Skip icon generation'
    )
    quickstart_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Overwrite existing files without prompting'
    )
    quickstart_parser.add_argument(
        '--from-prompt', '-p',
        help='Generate theme from AI prompt (e.g., "dark theme with neon cyberpunk colors")'
    )
    
    # List command
    list_parser = subparsers.add_parser(
        'list', 
        help='List available themes',
        description='List all available theme configurations'
    )
    list_parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed information for each theme'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate theme configuration',
        description='Validate theme YAML configuration'
    )
    validate_parser.add_argument(
        'theme',
        nargs='?',
        help='Theme name to validate (validates all if not specified)'
    )
    validate_parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to fix validation errors'
    )
    
    # Clean command
    clean_parser = subparsers.add_parser(
        'clean', 
        help='Clean build artifacts',
        description='Remove generated files and build artifacts'
    )
    clean_parser.add_argument(
        '--all',
        action='store_true',
        help='Remove all generated files including themes directory'
    )
    clean_parser.add_argument(
        '--build',
        action='store_true',
        help='Remove only build directory'
    )
    clean_parser.add_argument(
        '--screenshots',
        action='store_true',
        help='Remove only screenshots'
    )
    
    # Package command
    package_parser = subparsers.add_parser(
        'package',
        help='Package existing theme',
        description='Package an existing theme directory into VSIX'
    )
    package_parser.add_argument(
        'theme',
        help='Theme directory to package'
    )
    package_parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output file path for VSIX'
    )
    
    # Screenshot command
    screenshot_parser = subparsers.add_parser(
        'screenshot',
        help='Generate theme screenshots',
        description='Generate screenshots for theme preview'
    )
    screenshot_parser.add_argument(
        'theme',
        help='Theme name to screenshot'
    )
    screenshot_parser.add_argument(
        '--code-file',
        type=Path,
        help='Custom code file to use for screenshot'
    )
    screenshot_parser.add_argument(
        '--language',
        choices=['python', 'javascript', 'rust', 'go', 'java'],
        default='python',
        help='Language for code sample'
    )
    screenshot_parser.add_argument(
        '--mock',
        action='store_true',
        help='Generate mock screenshot without opening VS Code'
    )
    
    # Icon command
    icon_parser = subparsers.add_parser(
        'icon',
        help='Generate theme icon',
        description='Generate icon for a theme'
    )
    icon_parser.add_argument(
        'theme',
        help='Theme name to generate icon for'
    )
    icon_parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output path for icon'
    )
    
    # Organize command
    organize_parser = subparsers.add_parser(
        'organize',
        help='Organize build artifacts',
        description='Copy build artifacts to proper locations'
    )
    organize_parser.add_argument(
        'theme',
        nargs='?',
        help='Theme name to organize (organizes all if not specified)'
    )
    
    return parser

def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.ERROR
        
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    # Show banner for interactive commands
    if not args.quiet and args.command in ['build', 'create', 'quickstart']:
        print_banner()
    
    # Show help if no command
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Load configuration
        config_path = args.config if hasattr(args, 'config') else Path('config.yaml')
        
        # For create and quickstart commands, we can work without config
        if args.command in ['create', 'quickstart'] and not config_path.exists():
            # Create minimal config in memory
            config = ConfigManager({
                'generator': {
                    'themes_dir': './themes',
                    'output_dir': './build'
                },
                'ai': {
                    'enabled': False  # Disable AI for quickstart
                }
            })
        else:
            if not config_path.exists():
                logger.error(f"Configuration file not found: {config_path}")
                print(colored(f"\n✗ Configuration file not found: {config_path}", "red"))
                print("\nCreate a config.yaml file or use --config to specify a different path")
                sys.exit(1)
                
            config = ConfigManager(str(config_path))
        
        # Initialize builder
        builder = ThemeBuilder(config)
        
        # Execute command
        if args.command == 'build':
            themes_built = builder.build(
                theme_name=args.theme,
                skip_ai=args.no_ai,
                skip_screenshots=args.no_screenshots,
                skip_package=args.no_package,
                output_dir=args.output,
                force=args.force
            )
            
            if themes_built:
                print(colored(f"\n✓ Successfully built {len(themes_built)} theme(s)", "green"))
            else:
                print(colored("\n✗ No themes were built", "red"))
                sys.exit(1)
                
        elif args.command == 'create':
            theme_path = builder.create_theme(
                name=args.name,
                template=args.template,
                display_name=args.display_name,
                description=args.description,
                from_prompt=args.from_prompt if hasattr(args, 'from_prompt') else None
            )
            
            print(colored(f"\n✓ Created theme template: {theme_path}", "green"))
            
            if hasattr(args, 'from_prompt') and args.from_prompt:
                print(colored("\n✓ AI generated theme based on your prompt!", "cyan"))
                print(f"\nThe theme was created with colors inspired by: '{args.from_prompt}'")
            
            print(f"\nNext steps:")
            print(f"  1. Edit {theme_path} to customize your theme")
            print(f"  2. Run 'vscode-theme-gen build {args.name}' to build")
            
        elif args.command == 'quickstart':
            # Quick create and build without AI
            print(colored(f"\n🚀 Quick starting theme: {args.name}", "cyan"))
            
            # Create theme
            display_name = args.display_name
            theme_path = builder.create_theme(
                name=args.name,
                template=args.template,
                display_name=display_name,
                description=args.description,
                from_prompt=args.from_prompt
            )
            
            print(colored(f"✓ Created theme: {theme_path}", "green"))
            
            # Immediately build it
            print(colored("\n🔨 Building theme...", "cyan"))
            
            # Determine what to skip
            skip_icon = args.no_icon if hasattr(args, 'no_icon') else False
            skip_screenshots = args.no_screenshots
            
            # Temporarily disable icon generation if requested
            if skip_icon:
                original_icon_setting = builder.config.get('build.generate_icon', True)
                builder.config.set('build.generate_icon', False)
            
            themes_built = builder.build(
                theme_name=args.name,
                skip_ai=True,  # Always skip AI for quickstart
                skip_screenshots=skip_screenshots,
                skip_package=False,  # Always create package
                force=args.force
            )
            
            # Restore icon setting
            if skip_icon:
                builder.config.set('build.generate_icon', original_icon_setting)
            
            if themes_built:
                print(colored(f"\n✅ Quick start complete!", "green", attrs=['bold']))
                print(f"\nYour theme '{args.name}' has been created and built!")
                print(f"\nArtifacts:")
                print(f"  • Theme definition: {theme_path}")
                print(f"  • Built files: {builder.output_dir / args.name}/")
                print(f"  • VSIX package: releases/{args.name}-*.vsix")
                if not skip_icon:
                    print(f"  • Icon: assets/builds/{args.name}_icon.png")
                if not skip_screenshots:
                    print(f"  • Screenshot: assets/builds/{args.name}.png")
                print(f"\nTo install in VS Code:")
                print(f"  code --install-extension releases/{args.name}-*.vsix")
            else:
                print(colored("\n✗ Quick start failed", "red"))
                sys.exit(1)
                
        elif args.command == 'list':
            themes = builder.list_themes(detailed=args.detailed)
            
            if not themes:
                print(colored("No themes found", "yellow"))
            else:
                print(colored(f"\nFound {len(themes)} theme(s):\n", "cyan"))
                for theme in themes:
                    if args.detailed:
                        print(f"  • {colored(theme['name'], 'white', attrs=['bold'])}")
                        print(f"    Display: {theme.get('display_name', 'N/A')}")
                        print(f"    Version: {theme.get('version', 'N/A')}")
                        print(f"    Description: {theme.get('description', 'N/A')}")
                        print()
                    else:
                        print(f"  • {theme['name']}")
                        
        elif args.command == 'validate':
            results = builder.validate_themes(
                theme_name=args.theme,
                fix=args.fix
            )
            
            all_valid = all(r['valid'] for r in results)
            
            for result in results:
                if result['valid']:
                    print(colored(f"✓ {result['name']}: Valid", "green"))
                else:
                    print(colored(f"✗ {result['name']}: Invalid", "red"))
                    for error in result['errors']:
                        print(f"    - {error}")
                        
            if not all_valid:
                sys.exit(1)
                
        elif args.command == 'clean':
            if args.all:
                builder.clean(all_files=True)
            elif args.build:
                builder.clean(build_only=True)
            elif args.screenshots:
                builder.clean(screenshots_only=True)
            else:
                builder.clean()
                
            print(colored("✓ Cleaned build artifacts", "green"))
            
        elif args.command == 'package':
            output_path = builder.package_theme(
                theme_name=args.theme,
                output_path=args.output
            )
            
            print(colored(f"✓ Created package: {output_path}", "green"))
            
        elif args.command == 'screenshot':
            # First check if theme is built
            theme_dir = builder.output_dir / args.theme
            
            if not theme_dir.exists():
                print(colored(f"✗ Theme '{args.theme}' not built yet!", "red"))
                print(f"\nYou need to build the theme first:")
                print(f"  vscode-theme-gen build {args.theme}")
                sys.exit(1)
            
            if args.mock:
                # Generate mock screenshot without opening VS Code
                print(colored("Mock screenshots are no longer supported", "yellow"))
                print("Please use real VS Code screenshots instead")
                sys.exit(1)
            else:
                # Check if VSIX exists for real screenshot
                vsix_files = list(theme_dir.glob("*.vsix"))
                if not vsix_files:
                    print(colored("✗ No VSIX found. Building package first...", "yellow"))
                    # Just package it
                    builder.package_theme(args.theme)
                
                # Normal flow - open VS Code and take real screenshot
                screenshot_path = builder.generate_screenshot(
                    theme_name=args.theme,
                    code_file=args.code_file,
                    language=args.language
                )
            
            if screenshot_path:
                print(colored(f"✓ Generated screenshot: {screenshot_path}", "green"))
            else:
                print(colored("✗ Failed to generate screenshot - VS Code required", "red"))
                sys.exit(1)
                
        elif args.command == 'icon':
            # Generate icon for theme
            theme_dir = builder.output_dir / args.theme
            
            if not theme_dir.exists():
                print(colored(f"✗ Theme '{args.theme}' not built yet!", "red"))
                print(f"\nBuild the theme first:")
                print(f"  vscode-theme-gen build {args.theme}")
                sys.exit(1)
            
            # Load theme data
            theme_file = builder.themes_dir / f"{args.theme}.yaml"
            if not theme_file.exists():
                theme_file = builder.themes_dir / f"{args.theme}.yml"
            
            if not theme_file.exists():
                print(colored(f"✗ Theme definition not found: {args.theme}", "red"))
                sys.exit(1)
            
            with open(theme_file, 'r') as f:
                theme_def = yaml.safe_load(f)
            
            theme_data = theme_def.get('theme', theme_def)
            
            # Generate icon
            from .icon_generator import IconGenerator
            icon_gen = IconGenerator(config)
            
            output_path = args.output or (theme_dir / 'images' / 'icon.png')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            icon_path = icon_gen.generate_icon(args.theme, theme_data, theme_dir)
            
            if icon_path:
                print(colored(f"✓ Generated icon: {icon_path}", "green"))
            else:
                print(colored("✗ Failed to generate icon", "red"))
                sys.exit(1)
                
        elif args.command == 'organize':
            if args.theme:
                # Organize single theme
                theme_dir = builder.output_dir / args.theme
                if theme_dir.exists():
                    builder._organize_build_artifacts(args.theme, theme_dir)
                    print(colored(f"✓ Organized artifacts for {args.theme}", "green"))
                else:
                    print(colored(f"✗ Theme not found: {args.theme}", "red"))
                    sys.exit(1)
            else:
                # Organize all themes
                builder.organize_all_artifacts()
                print(colored("✓ Organized all theme artifacts", "green"))
            
    except KeyboardInterrupt:
        print(colored("\n\nOperation cancelled by user", "yellow"))
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        print(colored(f"\n✗ Error: {e}", "red"))
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()