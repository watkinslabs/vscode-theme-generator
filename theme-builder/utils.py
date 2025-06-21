"""
Utility functions for VS Code theme generator
"""

import logging
import sys
from pathlib import Path
from termcolor import colored
from datetime import datetime

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"theme_generator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Set levels for specific loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                VS Code Theme Generator                   ║
║                    Version 0.1.0                         ║
║                                                          ║
║         Create beautiful themes with AI enhancement      ║
╚══════════════════════════════════════════════════════════╝
"""
    print(colored(banner, 'cyan'))

def confirm_action(prompt: str, default: bool = False) -> bool:
    """Ask user for confirmation"""
    default_str = "[Y/n]" if default else "[y/N]"
    response = input(f"{prompt} {default_str}: ").strip().lower()
    
    if not response:
        return default
        
    return response in ['y', 'yes']

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def sanitize_name(name: str) -> str:
    """Sanitize name for file/directory naming"""
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    
    # Remove invalid characters
    import re
    name = re.sub(r'[^a-zA-Z0-9_\-]', '', name)
    
    # Convert to lowercase
    name = name.lower()
    
    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = f"theme_{name}"
        
    return name

def load_yaml_file(file_path: Path) -> dict:
    """Load YAML file with error handling"""
    import yaml
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {file_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error reading {file_path}: {e}")

def save_yaml_file(data: dict, file_path: Path):
    """Save data to YAML file"""
    import yaml
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except Exception as e:
        raise ValueError(f"Error writing {file_path}: {e}")

def create_backup(file_path: Path) -> Path:
    """Create backup of a file"""
    if not file_path.exists():
        return None
        
    backup_dir = file_path.parent / '.backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
    
    import shutil
    shutil.copy2(file_path, backup_path)
    
    return backup_path

def get_project_info() -> dict:
    """Get project information from git or defaults"""
    info = {
        'author': 'Unknown',
        'email': 'unknown@example.com',
        'repository': ''
    }
    
    try:
        import subprocess
        
        # Try to get git user info
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            info['author'] = result.stdout.strip()
            
        result = subprocess.run(
            ['git', 'config', 'user.email'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            info['email'] = result.stdout.strip()
            
        # Try to get remote URL
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Convert SSH to HTTPS
            if url.startswith('git@github.com:'):
                url = url.replace('git@github.com:', 'https://github.com/')
            if url.endswith('.git'):
                url = url[:-4]
            info['repository'] = url
            
    except:
        pass
        
    return info

def merge_dicts(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries"""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
            
    return result