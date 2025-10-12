# themes.py - Theme and configuration management
import os
import json
from typing import Dict, Any

# Paths - Store everything in the same folder as the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = SCRIPT_DIR  # Same folder as main.py

# Create necessary subdirectories
POSTER_DIR = os.path.join(DB_DIR, "posters")
BACKUP_DIR = os.path.join(DB_DIR, "backups")

os.makedirs(POSTER_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# File paths
DB = os.path.join(DB_DIR, "movie_collection.db")
LOG = os.path.join(DB_DIR, "movie_app.log")
CONFIG_FILE = os.path.join(DB_DIR, "config.json")
CREDS_FILE = os.path.join(DB_DIR, "tmdb_api_key.txt")

# TMDB API Configuration
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_IMAGE_ORIGINAL = "https://image.tmdb.org/t/p/original"

# Default configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    "theme": "light",
    "window_size": "1400x850",
    "window_position": "center",
    "default_view": "list",
    "poster_quality": "high",
    "auto_backup": True,
    "backup_frequency_days": 7,
    "search_fuzzy": True,
    "auto_fetch_metadata": True,
    "default_sort": "title",
    "items_per_page": 50,
    "recent_searches": []
}

# Color schemes
LIGHT_THEME = {
    'bg': '#F3F3F3',
    'card_bg': '#FFFFFF',
    'accent': '#0067C0',
    'accent_hover': '#005A9E',
    'text': '#1F1F1F',
    'text_secondary': '#605E5C',
    'border': '#E1DFDD',
    'hover': '#F9F9F9',
    'button_bg': '#FAFAFA',
    'delete_btn': '#D13438',
    'delete_hover': '#A52A2A',
    'success': '#107C10',
    'success_hover': '#0E6B0E',
    'warning': '#F7630C',
    'info': '#0078D4'
}

DARK_THEME = {
    'bg': '#1E1E1E',
    'card_bg': '#2D2D2D',
    'accent': '#60CDFF',
    'accent_hover': '#4FB3E8',
    'text': '#FFFFFF',
    'text_secondary': '#C8C8C8',
    'border': '#3F3F3F',
    'hover': '#3A3A3A',
    'button_bg': '#2D2D2D',
    'delete_btn': '#E74856',
    'delete_hover': '#C93943',
    'success': '#6CCB5F',
    'success_hover': '#5AB64E',
    'warning': '#FCE100',
    'info': '#60CDFF'
}

# Global colors dictionary
COLORS = LIGHT_THEME.copy()

def set_theme(theme_name: str = "light") -> None:
    """Set the application theme"""
    global COLORS
    if theme_name == "dark":
        COLORS.update(DARK_THEME)
    else:
        COLORS.update(LIGHT_THEME)

def load_config() -> Dict[str, Any]:
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                return merged_config
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a single configuration value"""
    config = load_config()
    return config.get(key, default)

def set_config_value(key: str, value: Any) -> bool:
    """Set a single configuration value"""
    config = load_config()
    config[key] = value
    return save_config(config)
