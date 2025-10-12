# utils.py - Utility functions
import os
import re
import platform
import subprocess
from datetime import datetime, timezone
from typing import Optional, Tuple

# Define LOG constant (will be overridden by themes.py if available)
try:
    from themes import LOG
except ImportError:
    LOG = "movie_app.log"


def now_iso() -> str:
    """Return current timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()


def log(msg: str) -> None:
    """Write message to log file"""
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{now_iso()} - {msg}\n")
    except Exception as e:
        print(f"Log write failed: {msg} | Error: {e}")


def open_file(path: str) -> bool:
    """Open file with system default application"""
    try:
        if not os.path.exists(path):
            log(f"File not found: {path}")
            return False
        
        system = platform.system()
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.run(["open", path], check=True)
        else:
            subprocess.run(["xdg-open", path], check=True)
        
        log(f"Opened file: {path}")
        return True
    except Exception as e:
        log(f"Error opening file {path}: {e}")
        return False


def get_video_resolution(file_path: str) -> str:
    """Extract video resolution from filename"""
    if not file_path:
        return ""
    
    filename = os.path.basename(file_path).lower()
    patterns = [
        (r'2160p|4k|uhd', '4K'),
        (r'1440p', '1440p'),
        (r'1080p|fhd', '1080p'),
        (r'720p|hd', '720p'),
        (r'480p|sd', '480p'),
        (r'360p', '360p')
    ]
    
    for pattern, resolution in patterns:
        if re.search(pattern, filename):
            return resolution
    return ""


def extract_title_from_filename(filename: str) -> Tuple[str, Optional[str]]:
    """Extract movie title and year from filename"""
    if not filename:
        return ("", None)
    
    # Remove file extension
    name = os.path.splitext(filename)[0]
    
    # Remove quality indicators
    name = re.sub(
        r'\b(1080p|720p|480p|4k|uhd|hd|bluray|webrip|web-dl|dvdrip|brrip|hdtv|x264|x265|hevc)\b',
        '', name, flags=re.IGNORECASE
    )
    
    # Extract year
    year_match = re.search(r'[\[\(]?(\d{4})[\]\)]?', name)
    year = year_match.group(1) if year_match else None
    
    # Remove year from name
    if year:
        name = re.sub(r'[\[\(]?' + year + r'[\]\)]?', '', name)
    
    # Clean up separators
    name = re.sub(r'[._\-]+', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    
    # Capitalize words
    name = ' '.join(word.capitalize() for word in name.split())
    
    return (name, year)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '', filename)
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized


def format_runtime(minutes: int) -> str:
    """Format runtime in minutes to human-readable format"""
    if not minutes or minutes <= 0:
        return ""
    
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"


def validate_year(year: str) -> bool:
    """Validate if year is reasonable for a movie"""
    if not year or not year.isdigit():
        return False
    
    year_int = int(year)
    # Movies started around 1888, allow up to 5 years in future
    return 1888 <= year_int <= datetime.now().year + 5