# tmdb_api.py - TMDB API operations with poster downloading
import requests
import os
from typing import List, Dict, Optional, Tuple
from themes import TMDB_BASE_URL, TMDB_IMAGE_BASE, TMDB_IMAGE_ORIGINAL, POSTER_DIR, CREDS_FILE
from utils import log, sanitize_filename

TMDB_API_KEY: Optional[str] = None


def load_api_key() -> bool:
    """Load TMDB API key from file"""
    global TMDB_API_KEY
    
    if os.path.exists(CREDS_FILE):
        try:
            with open(CREDS_FILE, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                if key and len(key) > 10:
                    TMDB_API_KEY = key
                    log("TMDB API key loaded successfully")
                    return True
        except Exception as e:
            log(f"Error reading API key: {e}")
    
    return False


def save_api_key(key: str) -> bool:
    """Save TMDB API key to file"""
    global TMDB_API_KEY
    
    try:
        key = key.strip()
        if not key or len(key) < 10:
            return False
        
        with open(CREDS_FILE, 'w', encoding='utf-8') as f:
            f.write(key)
        
        TMDB_API_KEY = key
        log("TMDB API key saved successfully")
        return True
        
    except Exception as e:
        log(f"Error saving API key: {e}")
        return False


def test_api_key() -> Tuple[bool, str]:
    """Test if API key is valid"""
    if not TMDB_API_KEY:
        return False, "No API key configured"
    
    try:
        url = f"{TMDB_BASE_URL}/configuration"
        response = requests.get(url, params={'api_key': TMDB_API_KEY}, timeout=10)
        
        if response.status_code == 200:
            return True, "API key is valid"
        elif response.status_code == 401:
            return False, "Invalid API key"
        else:
            return False, f"API error: {response.status_code}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def search_movies(query: str, year: Optional[str] = None) -> List[Dict]:
    """
    Search for movies on TMDB
    Returns list of movie dictionaries
    """
    if not TMDB_API_KEY:
        log("No API key available for search")
        return []
    
    try:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            'api_key': TMDB_API_KEY,
            'query': query,
            'language': 'en-US',
            'page': 1,
            'include_adult': False
        }
        
        if year:
            params['year'] = year
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for movie in data.get('results', [])[:20]:
            results.append({
                'tmdb_id': movie.get('id'),
                'title': movie.get('title', 'Unknown'),
                'original_title': movie.get('original_title', ''),
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                'overview': movie.get('overview', ''),
                'poster_path': movie.get('poster_path', ''),
                'backdrop_path': movie.get('backdrop_path', ''),
                'rating': round(movie.get('vote_average', 0), 1),
                'vote_count': movie.get('vote_count', 0),
                'popularity': movie.get('popularity', 0),
                'genre_ids': movie.get('genre_ids', [])
            })
        
        log(f"TMDB search for '{query}' returned {len(results)} results")
        return results
        
    except requests.exceptions.RequestException as e:
        log(f"TMDB search network error: {e}")
        return []
    except Exception as e:
        log(f"TMDB search error: {e}")
        return []


def fetch_movie_details(tmdb_id: int) -> Dict:
    """
    Fetch detailed movie information from TMDB
    Returns dictionary with movie details (poster paths are still TMDB paths, not local)
    """
    if not TMDB_API_KEY:
        log("No API key available for details fetch")
        return {}
    
    try:
        url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US',
            'append_to_response': 'credits,release_dates,videos'
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Extract credits
        credits = data.get('credits', {})
        cast_list = credits.get('cast', [])[:5]
        crew_list = credits.get('crew', [])
        
        # Get director
        director = ''
        for person in crew_list:
            if person.get('job') == 'Director':
                director = person.get('name', '')
                break
        
        # Get writers
        writers = []
        for person in crew_list:
            if person.get('job') in ['Writer', 'Screenplay', 'Story']:
                writers.append(person.get('name', ''))
        writers_str = ', '.join(writers[:3]) if writers else ''
        
        # Get cast
        cast_str = ', '.join([person.get('name', '') for person in cast_list])
        
        # Get genres
        genres = data.get('genres', [])
        genre_str = ', '.join([g.get('name', '') for g in genres])
        
        # Get runtime
        runtime = data.get('runtime', 0)
        runtime_str = str(runtime) if runtime else ''
        
        # Get certification (age rating)
        certificate = ''
        release_dates = data.get('release_dates', {}).get('results', [])
        for country in release_dates:
            if country.get('iso_3166_1') == 'US':
                for release in country.get('release_dates', []):
                    cert = release.get('certification', '')
                    if cert:
                        certificate = cert
                        break
                break
        
        # Get trailer
        trailer_key = ''
        videos = data.get('videos', {}).get('results', [])
        for video in videos:
            if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
                trailer_key = video.get('key', '')
                break
        
        # Get IMDb ID
        imdb_id = data.get('imdb_id', '')
        
        result = {
            'tmdb_id': str(tmdb_id),
            'imdb_id': imdb_id,
            'title': data.get('title', ''),
            'original_title': data.get('original_title', ''),
            'year': data.get('release_date', '')[:4] if data.get('release_date') else '',
            'director': director,
            'writers': writers_str,
            'cast': cast_str,
            'genre': genre_str,
            'rating': str(round(data.get('vote_average', 0), 1)),
            'certificate': certificate,
            'runtime': runtime_str,
            'synopsis': data.get('overview', ''),
            'poster_path': data.get('poster_path', ''),  # TMDB path, not local
            'backdrop_path': data.get('backdrop_path', ''),  # TMDB path, not local
            'tagline': data.get('tagline', ''),
            'budget': data.get('budget', 0),
            'revenue': data.get('revenue', 0),
            'status': data.get('status', ''),
            'trailer_key': trailer_key,
            'homepage': data.get('homepage', ''),
            'vote_count': data.get('vote_count', 0),
            'popularity': data.get('popularity', 0)
        }
        
        log(f"Fetched details for TMDB ID: {tmdb_id} - {result.get('title', 'Unknown')}")
        return result
        
    except requests.exceptions.RequestException as e:
        log(f"TMDB details fetch network error: {e}")
        return {}
    except Exception as e:
        log(f"TMDB details fetch error: {e}")
        return {}


def download_image(image_path: str, tmdb_id: int, is_backdrop: bool = False, high_quality: bool = True) -> str:
    """
    Download movie poster or backdrop from TMDB
    
    Args:
        image_path: TMDB image path (e.g., "/abc123.jpg")
        tmdb_id: TMDB movie ID
        is_backdrop: True for backdrop, False for poster
        high_quality: True for original quality, False for w500
    
    Returns:
        Local file path or empty string on failure
    """
    if not image_path:
        log("No image path provided")
        return ""
    
    try:
        # Ensure POSTER_DIR exists
        os.makedirs(POSTER_DIR, exist_ok=True)
        
        # Choose image quality
        base_url = TMDB_IMAGE_ORIGINAL if high_quality else TMDB_IMAGE_BASE
        url = f"{base_url}{image_path}"
        
        # Create filename
        suffix = "_backdrop" if is_backdrop else ""
        safe_id = sanitize_filename(str(tmdb_id))
        local_path = os.path.join(POSTER_DIR, f"tmdb_{safe_id}{suffix}.jpg")
        
        # Check if file already exists
        if os.path.exists(local_path):
            log(f"Image already exists: {local_path}")
            return local_path
        
        # Download image
        log(f"Downloading image from: {url}")
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        
        # Save to file
        with open(local_path, "wb") as f:
            f.write(response.content)
        
        log(f"Successfully downloaded image to: {local_path}")
        return local_path
        
    except requests.exceptions.RequestException as e:
        log(f"Image download network error for {image_path}: {e}")
        return ""
    except Exception as e:
        log(f"Image download error for {image_path}: {e}")
        return ""


def get_popular_movies(page: int = 1) -> List[Dict]:
    """Get popular movies from TMDB"""
    if not TMDB_API_KEY:
        return []
    
    try:
        url = f"{TMDB_BASE_URL}/movie/popular"
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US',
            'page': page
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for movie in data.get('results', []):
            results.append({
                'tmdb_id': movie.get('id'),
                'title': movie.get('title', 'Unknown'),
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                'overview': movie.get('overview', ''),
                'poster_path': movie.get('poster_path', ''),
                'rating': round(movie.get('vote_average', 0), 1)
            })
        
        return results
        
    except Exception as e:
        log(f"Error fetching popular movies: {e}")
        return []