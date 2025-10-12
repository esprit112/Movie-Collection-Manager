# main.py - Movie Collection Manager with Cinema Theme
"""
Movie Collection Manager - PySide6 Application
A comprehensive movie collection manager with TMDB integration and cinematic styling

Requirements:
- PySide6
- requests
- See requirements.txt for full list

Run: python main.py
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QDialog, QFileDialog, QScrollArea, QFrame, QGridLayout,
    QHeaderView, QMenu, QMenuBar, QStatusBar
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QPixmap, QFont, QAction, QIcon

# Import cinema color scheme
from cinema_colors import (
    CINEMA,
    get_button_style,
    get_card_style,
    get_dialog_style,
    get_main_window_style,
    get_movie_card_style,
    get_status_bar_style
)

# Import other modules
try:
    from database import init_db, Database, create_backup, restore_backup, list_backups
    from tmdb_api import (
        load_api_key, save_api_key, test_api_key,
        search_movies, fetch_movie_details, download_image
    )
    from utils import log, sanitize_filename, extract_title_from_filename
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all required files are present:")
    print("  - cinema_colors.py")
    print("  - database.py")
    print("  - tmdb_api.py")
    print("  - utils.py")
    sys.exit(1)


class FetchMovieThread(QThread):
    """Background thread for fetching movie details from TMDB"""
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, tmdb_id: int):
        super().__init__()
        self.tmdb_id = tmdb_id
    
    def run(self):
        try:
            details = fetch_movie_details(self.tmdb_id)
            if details:
                self.finished.emit(details)
            else:
                self.error.emit("Failed to fetch movie details")
        except Exception as e:
            self.error.emit(str(e))


class AddMovieDialog(QDialog):
    """Dialog for searching and adding movies from TMDB"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎬 Add Movie")
        self.setModal(True)
        self.setMinimumSize(900, 600)
        
        self.search_results = []
        self.selected_movie = None
        
        self._setup_ui()
        self.setStyleSheet(get_dialog_style())
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Search TMDB for Movies")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {CINEMA['gold']}; padding: 10px;")
        layout.addWidget(title)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter movie title...")
        self.search_input.returnPressed.connect(self.search)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet(get_button_style(primary=True))
        search_btn.clicked.connect(self.search)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Title", "Year", "Rating", "Overview"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SingleSelection)
        self.results_table.doubleClicked.connect(self.add_selected)
        layout.addWidget(self.results_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        add_btn = QPushButton("Add Selected")
        add_btn.setStyleSheet(get_button_style(primary=True))
        add_btn.clicked.connect(self.add_selected)
        btn_layout.addWidget(add_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(get_button_style())
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Input Required", "Please enter a movie title to search.")
            return
        
        # Show loading
        self.results_table.setRowCount(0)
        self.results_table.setRowCount(1)
        self.results_table.setItem(0, 0, QTableWidgetItem("Searching TMDB..."))
        
        try:
            results = search_movies(query)
            
            self.results_table.setRowCount(0)
            
            if not results:
                QMessageBox.information(self, "No Results", f"No movies found for '{query}'")
                return
            
            self.search_results = results
            self.results_table.setRowCount(len(results))
            
            for i, movie in enumerate(results):
                self.results_table.setItem(i, 0, QTableWidgetItem(movie.get('title', 'Unknown')))
                self.results_table.setItem(i, 1, QTableWidgetItem(str(movie.get('year', ''))))
                self.results_table.setItem(i, 2, QTableWidgetItem(str(movie.get('rating', 'N/A'))))
                overview = movie.get('overview', 'No overview available')
                if len(overview) > 150:
                    overview = overview[:150] + "..."
                self.results_table.setItem(i, 3, QTableWidgetItem(overview))
            
        except Exception as e:
            self.results_table.setRowCount(0)
            QMessageBox.critical(self, "Error", f"Search failed:\n{str(e)}")
            log(f"Search error: {e}")
    
    def add_selected(self):
        selected_rows = self.results_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a movie to add.")
            return
        
        row = selected_rows[0].row()
        if row < len(self.search_results):
            self.selected_movie = self.search_results[row]
            self.accept()


class MovieCollectionManager(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 Movie Collection Manager")
        self.setMinimumSize(1400, 900)
        
        # Initialize data
        self.current_movies = []
        self.filtered_movies = []
        self.current_selection = None
        
        # Initialize database
        if not init_db():
            QMessageBox.critical(self, "Database Error", 
                               "Failed to initialize database.")
            sys.exit(1)
        
        # Check API key
        if not load_api_key():
            self.prompt_api_key()
        
        # Setup UI
        self._setup_ui()
        self._apply_styles()
        
        # Load movies
        self.load_movies()
        
        log("Application started successfully")
    
    def _setup_ui(self):
        """Setup the main user interface"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # Menu bar
        self._create_menu_bar()
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Action buttons
        actions = self._create_action_buttons()
        main_layout.addWidget(actions)
        
        # Movies grid
        self.movies_container = self._create_movies_grid()
        main_layout.addWidget(self.movies_container)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet(get_status_bar_style())
        self.update_status("Ready")
    
    def _create_menu_bar(self):
        """Create application menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        add_action = QAction("Add Movie", self)
        add_action.setShortcut("Ctrl+N")
        add_action.triggered.connect(self.show_add_dialog)
        file_menu.addAction(add_action)
        
        import_action = QAction("Import Movie Files", self)
        import_action.triggered.connect(self.import_files)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export to CSV", self)
        export_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        backup_action = QAction("Backup Database", self)
        backup_action.triggered.connect(self.backup_database)
        file_menu.addAction(backup_action)
        
        restore_action = QAction("Restore Database", self)
        restore_action.triggered.connect(self.restore_database)
        file_menu.addAction(restore_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menu_bar.addMenu("Tools")
        
        api_action = QAction("Configure TMDB API Key", self)
        api_action.triggered.connect(self.prompt_api_key)
        tools_menu.addAction(api_action)
        
        refresh_action = QAction("Refresh Collection", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.load_movies)
        tools_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _create_header(self):
        """Create header with title and search"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title = QLabel("🎬 My Movie Collection")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color: {CINEMA['gold']};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search collection...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self.filter_movies)
        header_layout.addWidget(self.search_input)
        
        return header_frame
    
    def _create_action_buttons(self):
        """Create action buttons"""
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setSpacing(10)
        
        # Add movie button
        add_btn = QPushButton("➕ Add Movie")
        add_btn.setStyleSheet(get_button_style(primary=True))
        add_btn.clicked.connect(self.show_add_dialog)
        btn_layout.addWidget(add_btn)
        
        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setStyleSheet(get_button_style(danger=True))
        self.delete_btn.clicked.connect(self.delete_movie)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)
        
        # Watched button
        self.watched_btn = QPushButton("✓ Mark Watched")
        self.watched_btn.setStyleSheet(get_button_style())
        self.watched_btn.clicked.connect(self.toggle_watched)
        self.watched_btn.setEnabled(False)
        btn_layout.addWidget(self.watched_btn)
        
        btn_layout.addStretch()
        
        # Stats label
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet(f"color: {CINEMA['text_dim']}; font-weight: 600; font-size: 13px;")
        btn_layout.addWidget(self.stats_label)
        
        return btn_frame
    
    def _create_movies_grid(self):
        """Create scrollable movies grid"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.grid_layout = QVBoxLayout(container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(container)
        return scroll
    
    def _apply_styles(self):
        """Apply cinema color scheme"""
        self.setStyleSheet(get_main_window_style())
    
    def prompt_api_key(self):
        """Prompt user to enter TMDB API key"""
        dialog = QDialog(self)
        dialog.setWindowTitle("TMDB API Key Required")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(get_dialog_style())
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel("🔑 TMDB API Key Required")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {CINEMA['gold']}; padding: 10px;")
        layout.addWidget(title)
        
        info = QLabel(
            "To use this app, you need a free TMDB API key.\n\n"
            "1. Visit: https://www.themoviedb.org/settings/api\n"
            "2. Create a free account\n"
            "3. Copy your API key and paste it below"
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {CINEMA['text']}; padding: 10px;")
        layout.addWidget(info)
        
        key_input = QLineEdit()
        key_input.setPlaceholderText("Enter your TMDB API key...")
        layout.addWidget(key_input)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("Save & Test")
        save_btn.setStyleSheet(get_button_style(primary=True))
        btn_layout.addWidget(save_btn)
        
        skip_btn = QPushButton("Skip")
        skip_btn.setStyleSheet(get_button_style())
        btn_layout.addWidget(skip_btn)
        
        layout.addLayout(btn_layout)
        
        def save_key():
            key = key_input.text().strip()
            if not key:
                QMessageBox.warning(dialog, "Required", "Please enter an API key.")
                return
            
            if save_api_key(key):
                valid, message = test_api_key()
                if valid:
                    QMessageBox.information(dialog, "✓ Success", "API key saved and validated!")
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Invalid Key", f"API key validation failed:\n{message}")
            else:
                QMessageBox.warning(dialog, "Error", "Failed to save API key")
        
        save_btn.clicked.connect(save_key)
        skip_btn.clicked.connect(dialog.reject)
        key_input.returnPressed.connect(save_key)
        
        dialog.exec()
    
    def load_movies(self):
        """Load all movies from database"""
        try:
            with Database() as db:
                self.current_movies = db.get_all_movies()
            
            self.filtered_movies = self.current_movies
            self.display_movies()
            self.update_status(f"Loaded {len(self.current_movies)} movies")
            
        except Exception as e:
            log(f"Error loading movies: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load movies:\n{str(e)}")
    
    def display_movies(self):
        """Display movies in grid layout"""
        # Clear existing widgets
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.filtered_movies:
            empty_label = QLabel("No movies found\n\nAdd movies to your collection to get started!")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setFont(QFont("Segoe UI", 16))
            empty_label.setStyleSheet(f"color: {CINEMA['text_muted']}; padding: 60px;")
            self.grid_layout.addWidget(empty_label)
            return
        
        # Create rows of movie cards
        movies_per_row = 6
        for i in range(0, len(self.filtered_movies), movies_per_row):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(15)
            
            for j in range(movies_per_row):
                if i + j < len(self.filtered_movies):
                    movie = self.filtered_movies[i + j]
                    card = self._create_movie_card(movie)
                    row_layout.addWidget(card)
            
            row_layout.addStretch()
            self.grid_layout.addLayout(row_layout)
        
        self.update_collection_stats()
    
    def _create_movie_card(self, movie: tuple):
        """Create a movie card widget"""
        card = QFrame()
        card.setFixedSize(180, 320)
        card.setStyleSheet(get_movie_card_style())
        card.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Poster - index 11 is poster_path in the database schema
        poster_label = QLabel()
        poster_label.setFixedSize(164, 245)
        poster_label.setAlignment(Qt.AlignCenter)
        poster_label.setStyleSheet(f"background-color: {CINEMA['bg_dark']}; border-radius: 4px;")
        
        # Get poster path from the correct index
        poster_path = movie[11] if len(movie) > 11 else None
        
        poster_loaded = False
        if poster_path and os.path.exists(poster_path):
            try:
                pixmap = QPixmap(poster_path)
                if not pixmap.isNull():
                    poster_label.setPixmap(pixmap.scaled(164, 245, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    poster_loaded = True
                    log(f"Loaded poster for {movie[1] if len(movie) > 1 else 'Unknown'}: {poster_path}")
            except Exception as e:
                log(f"Error loading poster {poster_path}: {e}")
        
        if not poster_loaded:
            # Show placeholder
            poster_label.setText("🎬")
            poster_label.setFont(QFont("Segoe UI", 32))
            poster_label.setStyleSheet(f"background-color: {CINEMA['bg_dark']}; color: {CINEMA['text_muted']}; border-radius: 4px;")
        
        layout.addWidget(poster_label)
        
        # Title
        title = movie[1] if len(movie) > 1 else "Unknown"
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title_label.setStyleSheet(f"color: {CINEMA['text']};")
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(35)
        layout.addWidget(title_label)
        
        # Year
        year = movie[2] if len(movie) > 2 else ""
        year_label = QLabel(str(year))
        year_label.setFont(QFont("Segoe UI", 9))
        year_label.setStyleSheet(f"color: {CINEMA['text_dim']};")
        layout.addWidget(year_label)
        
        # Store movie data in the card for access in click handler
        card.movie_data = movie
        
        # Make card clickable using mousePressEvent
        def mouse_press_handler(event):
            self.current_selection = movie
            self.delete_btn.setEnabled(True)
            self.watched_btn.setEnabled(True)
            self.show_movie_details(movie)
        
        card.mousePressEvent = mouse_press_handler
        
        return card
    
    def show_movie_details(self, movie: tuple):
        """Show detailed movie information with poster"""
        try:
            log(f"Opening details for movie: {movie[1] if len(movie) > 1 else 'Unknown'}")
            
            # Create custom dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Movie Details")
            dialog.setMinimumSize(700, 600)
            dialog.setStyleSheet(get_dialog_style())
            
            layout = QHBoxLayout(dialog)
            layout.setSpacing(20)
            
            # Left side - Poster
            poster_container = QWidget()
            poster_layout = QVBoxLayout(poster_container)
            poster_layout.setAlignment(Qt.AlignTop)
            
            poster_label = QLabel()
            poster_label.setFixedSize(300, 450)
            poster_label.setAlignment(Qt.AlignCenter)
            poster_label.setStyleSheet(f"background-color: {CINEMA['bg_dark']}; border-radius: 8px; border: 2px solid {CINEMA['border']};")
            
            # Load poster - index 11 is poster_path
            poster_path = movie[11] if len(movie) > 11 else None
            poster_loaded = False
            
            if poster_path and os.path.exists(poster_path):
                try:
                    pixmap = QPixmap(poster_path)
                    if not pixmap.isNull():
                        poster_label.setPixmap(pixmap.scaled(300, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        poster_loaded = True
                except Exception as e:
                    log(f"Error loading poster in details: {e}")
            
            if not poster_loaded:
                poster_label.setText("🎬\nNo Poster")
                poster_label.setFont(QFont("Segoe UI", 24))
                poster_label.setStyleSheet(f"background-color: {CINEMA['bg_dark']}; color: {CINEMA['text_muted']}; border-radius: 8px; border: 2px solid {CINEMA['border']};")
            
            poster_layout.addWidget(poster_label)
            layout.addWidget(poster_container)
            
            # Right side - Details
            details_container = QWidget()
            details_layout = QVBoxLayout(details_container)
            details_layout.setAlignment(Qt.AlignTop)
            details_layout.setSpacing(15)
            
            # Extract movie data
            title = movie[1] if len(movie) > 1 else "Unknown"
            year = movie[2] if len(movie) > 2 else ""
            director = movie[3] if len(movie) > 3 else "Unknown"
            writers = movie[4] if len(movie) > 4 else "Unknown"
            cast = movie[5] if len(movie) > 5 else "Unknown"
            genre = movie[6] if len(movie) > 6 else "Unknown"
            rating = movie[7] if len(movie) > 7 else "N/A"
            certificate = movie[8] if len(movie) > 8 else "N/A"
            runtime = movie[9] if len(movie) > 9 else "N/A"
            synopsis = movie[10] if len(movie) > 10 else "No synopsis available"
            watched = movie[15] if len(movie) > 15 else 0
            
            # New fields
            tagline = movie[23] if len(movie) > 23 and movie[23] else ""
            original_title = movie[24] if len(movie) > 24 and movie[24] else ""
            budget = movie[25] if len(movie) > 25 and movie[25] else 0
            revenue = movie[26] if len(movie) > 26 and movie[26] else 0
            status = movie[27] if len(movie) > 27 and movie[27] else ""
            trailer_key = movie[28] if len(movie) > 28 and movie[28] else ""
            homepage = movie[29] if len(movie) > 29 and movie[29] else ""
            vote_count = movie[30] if len(movie) > 30 and movie[30] else 0
            popularity = movie[31] if len(movie) > 31 and movie[31] else 0
            
            # Ensure numeric types
            try:
                budget = int(budget) if budget else 0
            except (ValueError, TypeError):
                budget = 0
            
            try:
                revenue = int(revenue) if revenue else 0
            except (ValueError, TypeError):
                revenue = 0
            
            try:
                vote_count = int(vote_count) if vote_count else 0
            except (ValueError, TypeError):
                vote_count = 0
            
            try:
                popularity = float(popularity) if popularity else 0
            except (ValueError, TypeError):
                popularity = 0
            
            # Title and Year
            title_label = QLabel(f"{title} ({year})")
            title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
            title_label.setStyleSheet(f"color: {CINEMA['gold']}; padding: 5px;")
            title_label.setWordWrap(True)
            details_layout.addWidget(title_label)
            
            # Tagline (if available)
            if tagline:
                tagline_label = QLabel(f'"{tagline}"')
                tagline_font = QFont("Segoe UI", 11)
                tagline_font.setItalic(True)
                tagline_label.setFont(tagline_font)
                tagline_label.setStyleSheet(f"color: {CINEMA['text_dim']}; padding: 5px;")
                tagline_label.setWordWrap(True)
                details_layout.addWidget(tagline_label)
            
            # Create scrollable area for details
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setSpacing(10)
            scroll_layout.setAlignment(Qt.AlignTop)
            
            # Helper function to add detail row
            def add_detail(label_text, value_text, make_link=False, link_url=""):
                row = QHBoxLayout()
                label = QLabel(f"<b>{label_text}:</b>")
                label.setStyleSheet(f"color: {CINEMA['text']}; font-size: 13px;")
                label.setMinimumWidth(120)
                
                if make_link and link_url:
                    value = QLabel(f'<a href="{link_url}" style="color: {CINEMA["gold"]};">{value_text}</a>')
                    value.setOpenExternalLinks(True)
                else:
                    value = QLabel(str(value_text))
                
                value.setStyleSheet(f"color: {CINEMA['text_dim']}; font-size: 13px;")
                value.setWordWrap(True)
                
                row.addWidget(label)
                row.addWidget(value, 1)
                scroll_layout.addLayout(row)
            
            # Basic Information Section
            section_label = QLabel("📋 Basic Information")
            section_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
            section_label.setStyleSheet(f"color: {CINEMA['gold']}; margin-top: 10px; margin-bottom: 5px;")
            scroll_layout.addWidget(section_label)
            
            # Original Title (if different from title)
            if original_title and original_title != title:
                add_detail("🌍 Original Title", original_title)
            
            add_detail("Director", director)
            add_detail("Writers", writers)
            add_detail("Cast", cast)
            add_detail("Genre", genre)
            add_detail("Rating", f"{rating}/10" if rating != "N/A" else "N/A")
            add_detail("Certificate", certificate)
            add_detail("Runtime", f"{runtime} min" if runtime != "N/A" else "N/A")
            add_detail("Status", status if status else "Released")
            add_detail("Watched", "✓ Yes" if watched else "✗ Not yet")
            
            # Statistics Section
            if vote_count or popularity:
                section_label = QLabel("⭐ Statistics")
                section_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
                section_label.setStyleSheet(f"color: {CINEMA['gold']}; margin-top: 15px; margin-bottom: 5px;")
                scroll_layout.addWidget(section_label)
                
                if vote_count and vote_count > 0:
                    formatted_votes = f"{vote_count:,}"
                    add_detail("Vote Count", f"{formatted_votes} votes")
                if popularity and popularity > 0:
                    add_detail("Popularity", f"{popularity:.1f}")
            
            # Financial Section
            if budget or revenue:
                section_label = QLabel("💰 Box Office")
                section_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
                section_label.setStyleSheet(f"color: {CINEMA['gold']}; margin-top: 15px; margin-bottom: 5px;")
                scroll_layout.addWidget(section_label)
                
                if budget and budget > 0:
                    formatted_budget = f"${budget:,}"
                    add_detail("Budget", formatted_budget)
                if revenue and revenue > 0:
                    formatted_revenue = f"${revenue:,}"
                    add_detail("Revenue", formatted_revenue)
                    if budget and budget > 0:
                        profit = revenue - budget
                        profit_pct = (profit / budget * 100) if budget > 0 else 0
                        formatted_profit = f"${profit:,}"
                        profit_text = f"{formatted_profit} ({profit_pct:+.1f}%)"
                        add_detail("Profit", profit_text)
            
            # Links Section
            if trailer_key or homepage:
                section_label = QLabel("🔗 Links")
                section_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
                section_label.setStyleSheet(f"color: {CINEMA['gold']}; margin-top: 15px; margin-bottom: 5px;")
                scroll_layout.addWidget(section_label)
                
                if trailer_key:
                    youtube_url = f"https://www.youtube.com/watch?v={trailer_key}"
                    add_detail("📺 Trailer", "Watch on YouTube", make_link=True, link_url=youtube_url)
                if homepage:
                    add_detail("🌐 Homepage", "Visit Official Website", make_link=True, link_url=homepage)
            
            # Synopsis Section
            section_label = QLabel("📖 Synopsis")
            section_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
            section_label.setStyleSheet(f"color: {CINEMA['gold']}; margin-top: 15px; margin-bottom: 5px;")
            scroll_layout.addWidget(section_label)
            
            synopsis_text = QLabel(synopsis)
            synopsis_text.setStyleSheet(f"color: {CINEMA['text_dim']}; font-size: 12px; padding: 10px; background-color: {CINEMA['bg_dark']}; border-radius: 4px;")
            synopsis_text.setWordWrap(True)
            scroll_layout.addWidget(synopsis_text)
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_content)
            details_layout.addWidget(scroll)
            
            # Buttons
            btn_layout = QHBoxLayout()
            
            # Re-fetch button
            refetch_btn = QPushButton("🔄 Re-fetch from TMDB")
            refetch_btn.setStyleSheet(get_button_style(primary=True))
            refetch_btn.clicked.connect(lambda: self.refetch_movie_data(movie, dialog))
            btn_layout.addWidget(refetch_btn)
            
            btn_layout.addStretch()
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.setStyleSheet(get_button_style())
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)
            
            details_layout.addLayout(btn_layout)
            
            layout.addWidget(details_container, 1)
            
            log("Movie details dialog created successfully")
            dialog.exec()
            
        except Exception as e:
            log(f"Error showing movie details: {e}")
            import traceback
            log(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to show movie details:\n{str(e)}")
    
    def refetch_movie_data(self, old_movie: tuple, details_dialog: QDialog):
        """Re-fetch movie data from TMDB"""
        movie_id = old_movie[0]
        old_title = old_movie[1] if len(old_movie) > 1 else ""
        
        # Close the details dialog
        details_dialog.close()
        
        # Show search dialog
        search_dialog = QDialog(self)
        search_dialog.setWindowTitle("🔄 Re-fetch Movie Data")
        search_dialog.setModal(True)
        search_dialog.setMinimumSize(900, 600)
        search_dialog.setStyleSheet(get_dialog_style())
        
        layout = QVBoxLayout(search_dialog)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(f"Re-fetch data for: {old_title}")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {CINEMA['gold']}; padding: 10px;")
        layout.addWidget(title)
        
        info = QLabel("Search for the correct movie on TMDB and select it to update the data.")
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {CINEMA['text_dim']}; padding: 5px;")
        layout.addWidget(info)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText("Enter movie title to search...")
        search_input.setText(old_title)
        search_layout.addWidget(search_input)
        
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet(get_button_style(primary=True))
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Results table
        results_table = QTableWidget()
        results_table.setColumnCount(4)
        results_table.setHorizontalHeaderLabels(["Title", "Year", "Rating", "Overview"])
        results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        results_table.setSelectionBehavior(QTableWidget.SelectRows)
        results_table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(results_table)
        
        # Store search results
        search_results = []
        
        def do_search():
            nonlocal search_results
            query = search_input.text().strip()
            if not query:
                QMessageBox.warning(search_dialog, "Input Required", "Please enter a movie title to search.")
                return
            
            results_table.setRowCount(0)
            results_table.setRowCount(1)
            results_table.setItem(0, 0, QTableWidgetItem("Searching TMDB..."))
            
            try:
                results = search_movies(query)
                
                results_table.setRowCount(0)
                
                if not results:
                    QMessageBox.information(search_dialog, "No Results", f"No movies found for '{query}'")
                    return
                
                search_results = results
                results_table.setRowCount(len(results))
                
                for i, movie in enumerate(results):
                    results_table.setItem(i, 0, QTableWidgetItem(movie.get('title', 'Unknown')))
                    results_table.setItem(i, 1, QTableWidgetItem(str(movie.get('year', ''))))
                    results_table.setItem(i, 2, QTableWidgetItem(str(movie.get('rating', 'N/A'))))
                    overview = movie.get('overview', 'No overview available')
                    if len(overview) > 150:
                        overview = overview[:150] + "..."
                    results_table.setItem(i, 3, QTableWidgetItem(overview))
                
            except Exception as e:
                results_table.setRowCount(0)
                QMessageBox.critical(search_dialog, "Error", f"Search failed:\n{str(e)}")
                log(f"Re-fetch search error: {e}")
        
        def update_movie():
            selected_rows = results_table.selectionModel().selectedRows()
            
            if not selected_rows:
                QMessageBox.warning(search_dialog, "No Selection", "Please select a movie to update.")
                return
            
            row = selected_rows[0].row()
            if row >= len(search_results):
                return
            
            selected_movie = search_results[row]
            tmdb_id = selected_movie.get('tmdb_id')
            
            if not tmdb_id:
                QMessageBox.warning(search_dialog, "Error", "Invalid movie data")
                return
            
            reply = QMessageBox.question(
                search_dialog,
                "⚠️ Confirm Update",
                f"Update '{old_title}' with data from:\n\n"
                f"{selected_movie.get('title')} ({selected_movie.get('year')})?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            search_dialog.close()
            
            # Show progress
            progress = QMessageBox(self)
            progress.setWindowTitle("Updating Movie")
            progress.setText("Fetching updated movie details from TMDB...")
            progress.setStandardButtons(QMessageBox.NoButton)
            progress.setStyleSheet(get_dialog_style())
            progress.show()
            
            # Fetch full details in background
            self.refetch_thread = FetchMovieThread(tmdb_id)
            self.refetch_thread.finished.connect(
                lambda details: self.on_refetch_complete(details, progress, movie_id, old_movie)
            )
            self.refetch_thread.error.connect(lambda error: self.on_fetch_error(error, progress))
            self.refetch_thread.start()
        
        search_btn.clicked.connect(do_search)
        search_input.returnPressed.connect(do_search)
        results_table.doubleClicked.connect(update_movie)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        update_btn = QPushButton("Update Selected")
        update_btn.setStyleSheet(get_button_style(primary=True))
        update_btn.clicked.connect(update_movie)
        btn_layout.addWidget(update_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(get_button_style())
        cancel_btn.clicked.connect(search_dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Auto-search on open
        QTimer.singleShot(100, do_search)
        
        search_dialog.exec()
    
    def on_refetch_complete(self, details: dict, progress: QMessageBox, movie_id: int, old_movie: tuple):
        """Handle successful movie re-fetch"""
        try:
            progress.close()
            progress.deleteLater()
        except:
            pass
        
        try:
            # Download poster and backdrop images
            tmdb_id = details.get('tmdb_id')
            
            if tmdb_id:
                # Download poster
                poster_path = details.get('poster_path', '')
                if poster_path:
                    log(f"Downloading updated poster for TMDB ID {tmdb_id}: {poster_path}")
                    local_poster = download_image(poster_path, int(tmdb_id), is_backdrop=False)
                    if local_poster:
                        details['poster_path'] = local_poster
                        log(f"Updated poster saved to: {local_poster}")
                    else:
                        details['poster_path'] = ''
                else:
                    details['poster_path'] = ''
                
                # Download backdrop
                backdrop_path = details.get('backdrop_path', '')
                if backdrop_path:
                    log(f"Downloading updated backdrop for TMDB ID {tmdb_id}: {backdrop_path}")
                    local_backdrop = download_image(backdrop_path, int(tmdb_id), is_backdrop=True)
                    if local_backdrop:
                        details['backdrop_path'] = local_backdrop
                        log(f"Updated backdrop saved to: {local_backdrop}")
                    else:
                        details['backdrop_path'] = ''
                else:
                    details['backdrop_path'] = ''
            
            # Delete old poster if it exists and is different
            old_poster = old_movie[11] if len(old_movie) > 11 else None
            new_poster = details.get('poster_path', '')
            if old_poster and old_poster != new_poster and os.path.exists(old_poster):
                try:
                    os.remove(old_poster)
                    log(f"Deleted old poster: {old_poster}")
                except:
                    pass
            
            # Update movie in database
            with Database() as db:
                success, message = db.update_movie(movie_id, details)
                
                if success:
                    QMessageBox.information(self, "✓ Success", "Movie data updated successfully!")
                    self.load_movies()
                else:
                    QMessageBox.warning(self, "Error", f"Failed to update movie:\n{message}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error updating movie:\n{str(e)}")
            log(f"Error updating movie: {e}")
    
    def filter_movies(self):
        """Filter movies based on search input"""
        query = self.search_input.text().lower().strip()
        
        if not query:
            self.filtered_movies = self.current_movies
        else:
            self.filtered_movies = [
                movie for movie in self.current_movies
                if query in (movie[1] if len(movie) > 1 else "").lower() or
                   query in str(movie[2] if len(movie) > 2 else "").lower()
            ]
        
        self.display_movies()
    
    def show_add_dialog(self):
        """Show add movie dialog"""
        dialog = AddMovieDialog(self)
        
        if dialog.exec() == QDialog.Accepted and dialog.selected_movie:
            self.add_movie_from_tmdb(dialog.selected_movie)
    
    def add_movie_from_tmdb(self, movie_data: dict):
        """Add movie from TMDB search result"""
        tmdb_id = movie_data.get('tmdb_id')
        if not tmdb_id:
            QMessageBox.warning(self, "Error", "Invalid movie data")
            return
        
        # Show progress
        progress = QMessageBox(self)
        progress.setWindowTitle("Fetching Details")
        progress.setText("Fetching movie details from TMDB...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.setStyleSheet(get_dialog_style())
        progress.show()
        
        # Fetch full details in background
        self.fetch_thread = FetchMovieThread(tmdb_id)
        self.fetch_thread.finished.connect(lambda details: self.on_fetch_complete(details, progress))
        self.fetch_thread.error.connect(lambda error: self.on_fetch_error(error, progress))
        self.fetch_thread.start()
    
    def on_fetch_complete(self, details: dict, progress: QMessageBox):
        """Handle successful movie fetch"""
        try:
            progress.close()
            progress.deleteLater()
        except:
            pass
        
        try:
            # Download poster and backdrop images
            tmdb_id = details.get('tmdb_id')
            
            if tmdb_id:
                # Download poster
                poster_path = details.get('poster_path', '')
                if poster_path:
                    log(f"Downloading poster for TMDB ID {tmdb_id}: {poster_path}")
                    local_poster = download_image(poster_path, int(tmdb_id), is_backdrop=False)
                    if local_poster:
                        details['poster_path'] = local_poster
                        log(f"Poster saved to: {local_poster}")
                    else:
                        log("Failed to download poster")
                        details['poster_path'] = ''
                else:
                    details['poster_path'] = ''
                
                # Download backdrop
                backdrop_path = details.get('backdrop_path', '')
                if backdrop_path:
                    log(f"Downloading backdrop for TMDB ID {tmdb_id}: {backdrop_path}")
                    local_backdrop = download_image(backdrop_path, int(tmdb_id), is_backdrop=True)
                    if local_backdrop:
                        details['backdrop_path'] = local_backdrop
                        log(f"Backdrop saved to: {local_backdrop}")
                    else:
                        details['backdrop_path'] = ''
                else:
                    details['backdrop_path'] = ''
            
            # Add to database
            with Database() as db:
                success, message = db.add_movie(details)
                
                if success:
                    QMessageBox.information(self, "✓ Success", "Movie added to collection!")
                    self.load_movies()
                else:
                    QMessageBox.warning(self, "Error", f"Failed to add movie:\n{message}")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error adding movie:\n{str(e)}")
            log(f"Error adding movie: {e}")
    
    def on_fetch_error(self, error: str, progress: QMessageBox):
        """Handle movie fetch error"""
        try:
            progress.close()
            progress.deleteLater()
        except:
            pass
        QMessageBox.critical(self, "Error", f"Failed to fetch movie details:\n{error}")
    
    def delete_movie(self):
        """Delete selected movie"""
        if not self.current_selection:
            return
        
        movie_id = self.current_selection[0]
        title = self.current_selection[1] if len(self.current_selection) > 1 else "Unknown"
        year = self.current_selection[2] if len(self.current_selection) > 2 else ""
        
        reply = QMessageBox.question(
            self, "⚠️ Confirm Delete",
            f"Are you sure you want to delete:\n\n{title} ({year})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with Database() as db:
                    success, message = db.delete_movie(movie_id)
                    
                    if success:
                        QMessageBox.information(self, "✓ Success", "Movie deleted successfully!")
                        self.load_movies()
                        self.delete_btn.setEnabled(False)
                        self.watched_btn.setEnabled(False)
                    else:
                        QMessageBox.warning(self, "Error", f"Failed to delete movie:\n{message}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete movie:\n{str(e)}")
    
    def toggle_watched(self):
        """Toggle watched status of selected movie"""
        if not self.current_selection:
            return
        
        movie_id = self.current_selection[0]
        
        try:
            with Database() as db:
                if db.mark_as_watched(movie_id):
                    QMessageBox.information(self, "✓ Success", "Movie marked as watched!")
                    self.load_movies()
                else:
                    QMessageBox.warning(self, "Error", "Failed to update watched status")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update:\n{str(e)}")
    
    def import_files(self):
        """Import movie files from disk"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Movie Files",
            "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.m4v);;All Files (*.*)"
        )
        
        if not file_paths:
            return
        
        QMessageBox.information(
            self, "Import", 
            f"Import functionality for {len(file_paths)} files will be implemented.\n\n"
            "This will extract titles from filenames and search TMDB."
        )
    
    def export_csv(self):
        """Export collection to CSV"""
        if not self.current_movies:
            QMessageBox.information(self, "Export", "No movies to export!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Collection",
            f"movie_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        
        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Title', 'Year', 'Director', 'Genre', 'Rating', 'Runtime'])
                    
                    for movie in self.current_movies:
                        writer.writerow([
                            movie[1] if len(movie) > 1 else '',
                            movie[2] if len(movie) > 2 else '',
                            movie[3] if len(movie) > 3 else '',
                            movie[6] if len(movie) > 6 else '',
                            movie[7] if len(movie) > 7 else '',
                            movie[9] if len(movie) > 9 else ''
                        ])
                
                QMessageBox.information(self, "✓ Success", f"Exported {len(self.current_movies)} movies to:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export:\n{str(e)}")
                log(f"Export error: {e}")
    
    def backup_database(self):
        """Create database backup"""
        try:
            success, backup_path = create_backup()
            if success:
                QMessageBox.information(
                    self, "✓ Backup Created",
                    f"Database backed up successfully to:\n{backup_path}"
                )
            else:
                QMessageBox.warning(self, "Error", f"Failed to create backup:\n{backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backup failed:\n{str(e)}")
            log(f"Backup error: {e}")
    
    def restore_database(self):
        """Restore database from backup"""
        backups = list_backups()
        
        if not backups:
            QMessageBox.information(self, "No Backups", "No backup files found.")
            return
        
        # Create selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Restore Database")
        dialog.setModal(True)
        dialog.setMinimumWidth(600)
        dialog.setStyleSheet(get_dialog_style())
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel("📦 Select Backup to Restore")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {CINEMA['gold']}; padding: 10px;")
        layout.addWidget(title)
        
        warning = QLabel(
            "⚠️ Warning: This will replace your current database.\n"
            "Make sure to create a backup of your current data first!"
        )
        warning.setStyleSheet(f"color: {CINEMA['red']}; padding: 10px;")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Backup list
        backup_table = QTableWidget()
        backup_table.setColumnCount(2)
        backup_table.setHorizontalHeaderLabels(["Backup File", "Date"])
        backup_table.setRowCount(len(backups))
        backup_table.setSelectionBehavior(QTableWidget.SelectRows)
        backup_table.setSelectionMode(QTableWidget.SingleSelection)
        
        for i, backup in enumerate(backups):
            backup_table.setItem(i, 0, QTableWidgetItem(os.path.basename(backup)))
            backup_table.setItem(i, 1, QTableWidgetItem(
                datetime.fromtimestamp(os.path.getmtime(backup)).strftime('%Y-%m-%d %H:%M:%S')
            ))
        
        backup_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(backup_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        restore_btn = QPushButton("Restore Selected")
        restore_btn.setStyleSheet(get_button_style(primary=True))
        btn_layout.addWidget(restore_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(get_button_style())
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        def do_restore():
            selected = backup_table.selectionModel().selectedRows()
            if not selected:
                QMessageBox.warning(dialog, "No Selection", "Please select a backup to restore.")
                return
            
            row = selected[0].row()
            backup_file = backups[row]
            
            reply = QMessageBox.question(
                dialog, "⚠️ Confirm Restore",
                f"Are you sure you want to restore from:\n{os.path.basename(backup_file)}\n\n"
                "This will replace your current database!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success, message = restore_backup(backup_file)
                if success:
                    QMessageBox.information(dialog, "✓ Success", message)
                    dialog.accept()
                    self.load_movies()
                else:
                    QMessageBox.critical(dialog, "Error", message)
        
        restore_btn.clicked.connect(do_restore)
        
        dialog.exec()
    
    def update_collection_stats(self):
        """Update collection statistics"""
        total = len(self.current_movies)
        watched = sum(1 for movie in self.current_movies if len(movie) > 15 and movie[15])
        
        self.stats_label.setText(f"📊 Total: {total} | Watched: {watched} | Unwatched: {total - watched}")
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_bar.showMessage(message)
        log(message)
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""
        <div style='text-align: center;'>
            <h2 style='color: {CINEMA['gold']};'>🎬 Movie Collection Manager</h2>
            <p style='color: {CINEMA['text']};'><b>Version 4.0</b></p>
            <p style='color: {CINEMA['text_dim']};'>
                A comprehensive movie management application<br>
                with TMDB integration and cinematic styling.
            </p>
            <hr style='border-color: {CINEMA['border']};'>
            <p style='color: {CINEMA['text_dim']};'>
                <b>Built with:</b> Python • PySide6 • TMDB API<br>
                <b>Theme:</b> Cinema Dark Mode
            </p>
        </div>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About")
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_text)
        msg.setStyleSheet(get_dialog_style())
        msg.exec()
    
    def closeEvent(self, event):
        """Handle application close"""
        log("Application closing")
        event.accept()


def main():
    """Main application entry point"""
    # Check for required dependencies
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("Error: PySide6 not found")
        print("Install with: pip install PySide6")
        sys.exit(1)
    
    try:
        import requests
    except ImportError:
        print("Error: requests library not found")
        print("Install with: pip install requests")
        sys.exit(1)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Movie Collection Manager")
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MovieCollectionManager()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()