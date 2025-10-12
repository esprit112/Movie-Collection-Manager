# database.py - Database operations with all functions
import sqlite3
import os
import shutil
import glob
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any
from themes import DB, BACKUP_DIR
from utils import log, now_iso


def init_db() -> bool:
    """Initialize database with proper error handling"""
    try:
        if os.path.exists(DB):
            try:
                test_conn = sqlite3.connect(DB)
                test_conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                test_conn.close()
                log("Existing database verified successfully")
            except sqlite3.DatabaseError as e:
                log(f"Database corrupted: {e}. Creating backup and new database.")
                backup_path = os.path.join(BACKUP_DIR, f"corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                shutil.copy2(DB, backup_path)
                os.remove(DB)
                log(f"Corrupted database backed up to: {backup_path}")
        
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year TEXT,
                director TEXT,
                writers TEXT,
                cast TEXT,
                genre TEXT,
                rating TEXT,
                certificate TEXT,
                runtime TEXT,
                synopsis TEXT,
                poster_path TEXT,
                backdrop_path TEXT,
                file_path TEXT,
                resolution TEXT,
                watched INTEGER DEFAULT 0,
                personal_rating INTEGER DEFAULT 0,
                notes TEXT,
                date_added TEXT,
                last_watched TEXT,
                watch_count INTEGER DEFAULT 0,
                tmdb_id TEXT,
                imdb_id TEXT,
                tagline TEXT,
                original_title TEXT,
                budget INTEGER DEFAULT 0,
                revenue INTEGER DEFAULT 0,
                status TEXT,
                trailer_key TEXT,
                homepage TEXT,
                vote_count INTEGER DEFAULT 0,
                popularity REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON movies(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_year ON movies(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_genre ON movies(genre)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_watched ON movies(watched)")
        
        # Check for missing columns and add them
        cursor.execute("PRAGMA table_info(movies)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # List of columns that should exist
        required_columns = {
            'backdrop_path': 'TEXT',
            'tagline': 'TEXT',
            'original_title': 'TEXT',
            'budget': 'INTEGER DEFAULT 0',
            'revenue': 'INTEGER DEFAULT 0',
            'status': 'TEXT',
            'trailer_key': 'TEXT',
            'homepage': 'TEXT',
            'vote_count': 'INTEGER DEFAULT 0',
            'popularity': 'REAL DEFAULT 0'
        }
        
        # Add missing columns
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                log(f"Adding missing column: {column_name}")
                cursor.execute(f"ALTER TABLE movies ADD COLUMN {column_name} {column_type}")
                conn.commit()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backup_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_path TEXT,
                backup_date TEXT,
                movie_count INTEGER,
                file_size INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
        log("Database initialized successfully")
        return True
        
    except Exception as e:
        log(f"Database initialization error: {e}")
        return False


class Database:
    """Database handler class with context manager support"""
    
    def __init__(self):
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(DB)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            log(f"Database connection error: {e}")
            return False
    
    def close(self) -> None:
        """Close database connection"""
        if self.conn:
            try:
                self.conn.commit()
            except:
                pass
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def movie_exists(self, title: str, year: str = "") -> bool:
        """Check if movie already exists in database"""
        try:
            if year:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM movies WHERE LOWER(title) = LOWER(?) AND year = ?",
                    (title, year)
                )
            else:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM movies WHERE LOWER(title) = LOWER(?)",
                    (title,)
                )
            count = self.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            log(f"Error checking movie existence: {e}")
            return False
    
    def add_movie(self, movie_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Add a movie to the database
        Returns: (success, message)
        """
        try:
            # Check for duplicates
            if self.movie_exists(movie_data.get('title', ''), movie_data.get('year', '')):
                return False, "Movie already exists in collection"
            
            # Add timestamps
            if 'date_added' not in movie_data:
                movie_data['date_added'] = now_iso()
            
            # Get valid columns from database
            self.cursor.execute("PRAGMA table_info(movies)")
            valid_columns = set(column[1] for column in self.cursor.fetchall())
            
            # Filter movie_data to only include valid columns
            filtered_data = {k: v for k, v in movie_data.items() if k in valid_columns}
            
            if not filtered_data:
                return False, "No valid data to insert"
            
            columns = ', '.join(filtered_data.keys())
            placeholders = ', '.join(['?' for _ in filtered_data])
            values = tuple(filtered_data.values())
            
            query = f"INSERT INTO movies ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            log(f"Added movie: {movie_data.get('title', 'Unknown')}")
            return True, "Movie added successfully"
            
        except Exception as e:
            log(f"Error adding movie: {e}")
            self.conn.rollback()
            return False, str(e)
    
    def get_all_movies(self) -> List[Tuple]:
        """Get all movies from database"""
        try:
            self.cursor.execute("SELECT * FROM movies ORDER BY title ASC")
            movies = self.cursor.fetchall()
            log(f"Retrieved {len(movies)} movies from database")
            return movies
        except Exception as e:
            log(f"Error retrieving movies: {e}")
            return []
    
    def get_movie_by_id(self, movie_id: int) -> Optional[Tuple]:
        """Get a specific movie by ID"""
        try:
            self.cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
            return self.cursor.fetchone()
        except Exception as e:
            log(f"Error getting movie by ID: {e}")
            return None
    
    def search_movies(self, query: str) -> List[Tuple]:
        """Search movies by title, director, cast, or genre"""
        try:
            search_term = f"%{query}%"
            self.cursor.execute("""
                SELECT * FROM movies 
                WHERE title LIKE ? OR director LIKE ? OR cast LIKE ? OR genre LIKE ?
                ORDER BY title ASC
            """, (search_term, search_term, search_term, search_term))
            return self.cursor.fetchall()
        except Exception as e:
            log(f"Error searching movies: {e}")
            return []
    
    def update_movie(self, movie_id: int, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """Update movie fields"""
        try:
            updates['updated_at'] = now_iso()
            
            set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [movie_id]
            
            query = f"UPDATE movies SET {set_clause} WHERE id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            log(f"Updated movie ID: {movie_id}")
            return True, "Movie updated successfully"
            
        except Exception as e:
            log(f"Error updating movie: {e}")
            self.conn.rollback()
            return False, str(e)
    
    def delete_movie(self, movie_id: int) -> Tuple[bool, str]:
        """Delete a movie from database"""
        try:
            # Get poster path before deleting
            movie = self.get_movie_by_id(movie_id)
            if movie and len(movie) > 11:
                poster_path = movie[11]  # poster_path index
                if poster_path and os.path.exists(poster_path):
                    try:
                        os.remove(poster_path)
                        log(f"Deleted poster: {poster_path}")
                    except:
                        pass
            
            self.cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
            self.conn.commit()
            
            log(f"Deleted movie ID: {movie_id}")
            return True, "Movie deleted successfully"
            
        except Exception as e:
            log(f"Error deleting movie: {e}")
            self.conn.rollback()
            return False, str(e)
    
    def mark_as_watched(self, movie_id: int) -> bool:
        """Mark a movie as watched"""
        try:
            self.cursor.execute("""
                UPDATE movies 
                SET watched = 1, last_watched = ?, watch_count = watch_count + 1, updated_at = ?
                WHERE id = ?
            """, (now_iso(), now_iso(), movie_id))
            self.conn.commit()
            
            log(f"Marked movie ID {movie_id} as watched")
            return True
        except Exception as e:
            log(f"Error marking as watched: {e}")
            self.conn.rollback()
            return False
    
    def get_watched_movies(self) -> List[Tuple]:
        """Get all watched movies"""
        try:
            self.cursor.execute("SELECT * FROM movies WHERE watched = 1 ORDER BY last_watched DESC")
            return self.cursor.fetchall()
        except Exception as e:
            log(f"Error getting watched movies: {e}")
            return []
    
    def get_unwatched_movies(self) -> List[Tuple]:
        """Get all unwatched movies"""
        try:
            self.cursor.execute("SELECT * FROM movies WHERE watched = 0 ORDER BY date_added DESC")
            return self.cursor.fetchall()
        except Exception as e:
            log(f"Error getting unwatched movies: {e}")
            return []
    
    def get_movies_by_genre(self, genre: str) -> List[Tuple]:
        """Get movies by genre"""
        try:
            self.cursor.execute("SELECT * FROM movies WHERE genre LIKE ? ORDER BY title ASC", (f"%{genre}%",))
            return self.cursor.fetchall()
        except Exception as e:
            log(f"Error getting movies by genre: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            stats = {}
            
            self.cursor.execute("SELECT COUNT(*) FROM movies")
            stats['total_movies'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM movies WHERE watched = 1")
            stats['watched'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM movies WHERE watched = 0")
            stats['unwatched'] = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(DISTINCT genre) FROM movies WHERE genre IS NOT NULL AND genre != ''")
            stats['genres'] = self.cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            log(f"Error getting statistics: {e}")
            return {
                'total_movies': 0,
                'watched': 0,
                'unwatched': 0,
                'genres': 0
            }


def create_backup() -> Tuple[bool, str]:
    """Create database backup"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(BACKUP_DIR, f"movie_collection_backup_{timestamp}.db")
        
        # Copy database file
        shutil.copy2(DB, backup_path)
        
        # Get file size and movie count
        file_size = os.path.getsize(backup_path)
        
        with Database() as db:
            db.cursor.execute("SELECT COUNT(*) FROM movies")
            movie_count = db.cursor.fetchone()[0]
            
            # Record backup in history
            db.cursor.execute("""
                INSERT INTO backup_history (backup_path, backup_date, movie_count, file_size)
                VALUES (?, ?, ?, ?)
            """, (backup_path, now_iso(), movie_count, file_size))
            db.conn.commit()
        
        log(f"Backup created: {backup_path}")
        return True, backup_path
        
    except Exception as e:
        log(f"Backup error: {e}")
        return False, str(e)


def restore_backup(backup_path: str) -> Tuple[bool, str]:
    """Restore database from backup"""
    try:
        if not os.path.exists(backup_path):
            return False, "Backup file not found"
        
        # Create a backup of current database before restoring
        current_backup = os.path.join(BACKUP_DIR, f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        if os.path.exists(DB):
            shutil.copy2(DB, current_backup)
        
        # Restore from backup
        shutil.copy2(backup_path, DB)
        
        log(f"Database restored from: {backup_path}")
        return True, "Database restored successfully"
        
    except Exception as e:
        log(f"Restore error: {e}")
        return False, str(e)


def list_backups() -> List[str]:
    """List all available backup files"""
    try:
        # Find all .db files in backup directory
        backup_pattern = os.path.join(BACKUP_DIR, "*.db")
        backups = glob.glob(backup_pattern)
        
        # Sort by modification time (newest first)
        backups.sort(key=os.path.getmtime, reverse=True)
        
        log(f"Found {len(backups)} backup files")
        return backups
        
    except Exception as e:
        log(f"Error listing backups: {e}")
        return []